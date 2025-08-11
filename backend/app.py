import json
import sqlite3
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ai_formatter import craft_subject_and_body
from email_queue import email_queue

DB_PATH = "contacts.db"
HOST = "0.0.0.0"
PORT = 5000

MAIL_RECIPIENTS = [
    r.strip()
    for r in (os.getenv("MAIL_RECIPIENTS", "").split(","))
    if r.strip()
]


def initialize_database() -> None:
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()
    connection.close()


from rate_limit import build_default_rate_limiter


rate_limiter = build_default_rate_limiter()


class ContactRequestHandler(BaseHTTPRequestHandler):
    server_version = "ContactHTTP/1.0"

    def _set_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802 (BaseHTTPRequestHandler naming)
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return

        if self.path == "/api/contacts":
            try:
                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT id, name, email, message, created_at FROM contacts ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()
                connection.close()
                contacts = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "message": row[3],
                        "created_at": row[4],
                    }
                    for row in rows
                ]
                self._send_json({"contacts": contacts})
            except Exception as exc:  # pragma: no cover - generic failure path
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):  # noqa: N802
        if self.path == "/api/contact":
            try:
                # Rate limit by client IP
                ip = self.client_address[0]
                if not rate_limiter.allow(ip):
                    self._send_json({"error": "Too many requests"}, status=HTTPStatus.TOO_MANY_REQUESTS)
                    return

                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                try:
                    data = json.loads(raw_body.decode("utf-8"))
                except json.JSONDecodeError:
                    self._send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
                    return

                # Honeypot trap: reject if filled
                honeypot = (data.get("company") or "").strip()
                if honeypot:
                    self._send_json({"message": "Contact submitted successfully"}, status=HTTPStatus.CREATED)
                    return

                name = (data.get("name") or "").strip()
                email = (data.get("email") or "").strip()
                message = (data.get("message") or "").strip()

                if not (name and email and message):
                    self._send_json({"error": "All fields are required"}, status=HTTPStatus.BAD_REQUEST)
                    return

                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
                    (name, email, message),
                )
                connection.commit()
                connection.close()

                # AI craft subject/body and enqueue email (if recipients configured)
                try:
                    subject, body = craft_subject_and_body({
                        "name": name,
                        "email": email,
                        "message": message,
                    })
                    if MAIL_RECIPIENTS:
                        email_queue.enqueue(MAIL_RECIPIENTS, subject, body)
                except Exception as exc:
                    # Do not fail the API if email preparation fails
                    print(f"Email enqueue failed: {exc}")

                self._send_json({"message": "Contact submitted successfully"}, status=HTTPStatus.CREATED)
            except Exception as exc:  # pragma: no cover - generic failure path
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    initialize_database()
    email_queue.start()
    server = ThreadingHTTPServer((HOST, PORT), ContactRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        email_queue.stop()


if __name__ == "__main__":
    main()
