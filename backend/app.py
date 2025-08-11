import json
import sqlite3
import os
import logging
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Configuration via environment variables with safe defaults
DB_PATH = os.getenv("DB_PATH", "contacts.db")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "65536"))  # 64 KiB
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "120"))
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"

# Basic structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("adventai.backend")


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


class ContactRequestHandler(BaseHTTPRequestHandler):
    server_version = "ContactHTTP/1.0"

    # Simple in-memory rate limit buckets: { ip: [timestamps_sec, ...] }
    rate_limit_buckets: dict[str, list[float]] = {}

    def _determine_client_ip(self) -> str:
        if TRUST_PROXY:
            forwarded = self.headers.get("X-Forwarded-For")
            if forwarded:
                # Use the first IP in the XFF list
                return forwarded.split(",")[0].strip()
        return self.client_address[0]

    def _set_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        # Default permissive for backwards compatibility
        if ALLOWED_ORIGIN == "*":
            allow_origin = "*"
        else:
            allow_origin = ALLOWED_ORIGIN if origin == ALLOWED_ORIGIN else "null"
        self.send_header("Access-Control-Allow-Origin", allow_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        # API responses are not cached by default
        self.send_header("Cache-Control", "no-store")
        # Basic security headers
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        try:
            logger.info(
                "access method=%s path=%s status=%s ip=%s length=%s",
                self.command,
                self.path,
                status,
                getattr(self, "client_address", ("-",))[0],
                len(body),
            )
        except Exception:
            pass

    def _rate_limit_check(self) -> bool:
        now = time.time()
        ip = self._determine_client_ip()
        window_start = now - 60.0
        bucket = self.rate_limit_buckets.setdefault(ip, [])
        # Drop old timestamps
        i = 0
        for i in range(len(bucket)):
            if bucket[i] >= window_start:
                break
        if i > 0:
            del bucket[:i]
        # Check allowance
        if len(bucket) >= REQUESTS_PER_MINUTE:
            return False
        bucket.append(now)
        return True

    def do_OPTIONS(self):  # noqa: N802 (BaseHTTPRequestHandler naming)
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return

        if self.path == "/api/contacts":
            if not self._rate_limit_check():
                self._send_json({"error": "Too Many Requests"}, status=HTTPStatus.TOO_MANY_REQUESTS)
                return
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
                logger.exception("Failed to list contacts")
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):  # noqa: N802
        if self.path == "/api/contact":
            if not self._rate_limit_check():
                self._send_json({"error": "Too Many Requests"}, status=HTTPStatus.TOO_MANY_REQUESTS)
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length > MAX_BODY_BYTES:
                    self._send_json({"error": "Payload Too Large"}, status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                    return
                raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
                try:
                    data = json.loads(raw_body.decode("utf-8"))
                except json.JSONDecodeError:
                    self._send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
                    return

                name = (data.get("name") or "").strip()
                email = (data.get("email") or "").strip()
                message = (data.get("message") or "").strip()

                if not (name and email and message):
                    self._send_json({"error": "All fields are required"}, status=HTTPStatus.BAD_REQUEST)
                    return

                # Additional validation: email format and length limits
                if len(name) > 200 or len(email) > 320 or len(message) > 4000:
                    self._send_json({"error": "Fields too long"}, status=HTTPStatus.BAD_REQUEST)
                    return

                # Very simple email validation
                if ("@" not in email) or (email.count("@") != 1) or ("." not in email.split("@", 1)[1]) or (" " in email):
                    self._send_json({"error": "Invalid email"}, status=HTTPStatus.BAD_REQUEST)
                    return

                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
                    (name, email, message),
                )
                connection.commit()
                connection.close()

                self._send_json({"message": "Contact submitted successfully"}, status=HTTPStatus.CREATED)
            except Exception as exc:  # pragma: no cover - generic failure path
                logger.exception("Failed to submit contact")
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    logger.info("Initializing database at %s", DB_PATH)
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), ContactRequestHandler)
    logger.info("Starting HTTP server on %s:%s", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down server")
        server.server_close()


if __name__ == "__main__":
    main()
