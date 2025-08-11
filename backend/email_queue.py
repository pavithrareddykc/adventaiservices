import threading
import time
from dataclasses import dataclass
from queue import Queue, Empty
from typing import List, Optional

import logging
from mailer import send_email, MailSendError
from audit import record_event


@dataclass
class EmailJob:
    recipients: List[str]
    subject: str
    body: str
    reply_to: Optional[str] = None
    from_override: Optional[str] = None
    attempts: int = 0


class EmailQueue:
    def __init__(self, max_retries: int = 5, base_backoff_seconds: float = 1.0):
        self._queue: Queue[EmailJob] = Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._max_retries = max_retries
        self._base_backoff_seconds = base_backoff_seconds

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, name="EmailQueueWorker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def enqueue(self, recipients: List[str], subject: str, body: str, *, reply_to: Optional[str] = None, from_override: Optional[str] = None) -> None:
        self._queue.put(EmailJob(recipients=recipients, subject=subject, body=body, reply_to=reply_to, from_override=from_override))

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                send_email(job.recipients, job.subject, job.body, reply_to=job.reply_to, from_override=job.from_override)
                record_event("email_sent", {"recipients": job.recipients, "subject": job.subject})
            except Exception as exc:  # broad except to ensure job handling
                job.attempts += 1
                if job.attempts <= self._max_retries:
                    # Exponential backoff with jitter
                    backoff = self._base_backoff_seconds * (2 ** (job.attempts - 1))
                    jitter = 0.1 * backoff
                    sleep_for = max(0.1, backoff + (jitter if job.attempts % 2 == 0 else -jitter))
                    logging.warning(
                        "email_send_failed",
                        extra={
                            "attempt": job.attempts,
                            "max_retries": self._max_retries,
                            "error": str(exc),
                            "retry_in_seconds": round(sleep_for, 2),
                        },
                    )
                    record_event("email_send_retry", {"attempt": job.attempts, "error": str(exc)})
                    time.sleep(sleep_for)
                    self._queue.put(job)
                else:
                    logging.error("email_send_permanent_failure", extra={"error": str(exc), "attempts": job.attempts})
                    record_event("email_send_failed", {"error": str(exc), "attempts": job.attempts})
            finally:
                self._queue.task_done()


# Singleton instance used by app
email_queue = EmailQueue()