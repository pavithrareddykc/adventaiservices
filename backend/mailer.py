import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable, Optional, List, Tuple
from urllib import request, error


class MailSendError(Exception):
    pass


def _partition_recipients(recipients: Iterable[str]) -> Tuple[List[str], List[str]]:
    emails: List[str] = []
    webhooks: List[str] = []
    for r in recipients:
        r = (r or "").strip()
        if not r:
            continue
        if r.lower().startswith("http://") or r.lower().startswith("https://"):
            webhooks.append(r)
        elif "@" in r and "/" not in r:
            emails.append(r)
        else:
            # Unknown type; treat as email to avoid surprises
            emails.append(r)
    return emails, webhooks


def _send_webhook(url: str, payload: dict, timeout: float = 2.0) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=timeout) as resp:
        # Consume response to avoid unclosed sockets
        resp.read()


def _send_via_smtp(sender: str, recipients: Iterable[str], subject: str, body_text: str, reply_to: Optional[str] = None, from_override: Optional[str] = None) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host:
        raise MailSendError("SMTP_HOST is not configured")

    message = MIMEMultipart()
    display_from = from_override or sender
    message["From"] = display_from
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.attach(MIMEText(body_text, "plain"))

    envelope_from = display_from  # use visible From as envelope from when overridden
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(envelope_from, list(recipients), message.as_string())


def send_email(recipients: Iterable[str], subject: str, body_text: str, reply_to: Optional[str] = None, from_override: Optional[str] = None) -> None:
    """
    Send to recipients which can be email addresses and/or webhook URLs (http/https).
    - Email recipients are sent via SMTP when configured; otherwise printed to stdout.
    - Webhook recipients receive a JSON POST with keys: subject, body, reply_to, from.
    MAIL_FROM is the default From unless ALLOW_SUBMITTER_AS_FROM is true and from_override provided.
    """
    sender = os.getenv("MAIL_FROM")
    if not sender and not from_override:
        raise MailSendError("MAIL_FROM is not configured")

    emails, webhooks = _partition_recipients(recipients)
    if not emails and not webhooks:
        raise MailSendError("No recipients specified")

    allow_override = os.getenv("ALLOW_SUBMITTER_AS_FROM", "false").lower() in {"1", "true", "yes"}
    effective_from_override = from_override if allow_override and from_override else None

    # Send emails via SMTP or stdout
    if emails:
        if os.getenv("SMTP_HOST"):
            _send_via_smtp(sender or effective_from_override or "", emails, subject, body_text, reply_to=reply_to, from_override=effective_from_override)
        else:
            print("=== EMAIL (dev fallback) ===")
            print(f"From: {effective_from_override or sender}")
            print(f"To: {', '.join(emails)}")
            if reply_to:
                print(f"Reply-To: {reply_to}")
            print(f"Subject: {subject}")
            print("")
            print(body_text)
            print("=== END EMAIL ===")

    # Send webhooks
    for url in webhooks:
        payload = {
            "subject": subject,
            "body": body_text,
            "reply_to": reply_to,
            "from": effective_from_override or sender,
        }
        try:
            _send_webhook(url, payload)
        except Exception as exc:
            # Bubble up to be retried by queue
            raise MailSendError(f"Webhook send failed to {url}: {exc}")