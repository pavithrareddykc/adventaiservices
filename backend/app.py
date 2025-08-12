"""Advent AI contact backend.

This module provides a small threaded HTTP server using only Python's standard
library. It exposes three endpoints:

- GET /health: Simple health check returning {"status": "ok"}
- POST /api/contact: Accepts JSON {name, email, message}; validates and stores
  a new contact message in a local SQLite database
- GET /api/contacts: Lists stored contact messages in reverse chronological
  order

The SQLite database file is created on first run. CORS headers are set to allow
simple integration from a static website.
"""

import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB_PATH = "contacts.db"
HOST = "0.0.0.0"
PORT = 5000


def initialize_database() -> None:
    """Create the SQLite database and the `contacts` table if they don't exist."""
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
    """HTTP handler that implements health and contact API endpoints.

    The handler also sets permissive CORS headers to support browser clients
    hosted on different origins.
    """
    server_version = "ContactHTTP/1.0"

    def _set_cors_headers(self) -> None:
        """Attach CORS headers to the current response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        """Serialize `payload` as JSON and write it to the response stream."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802 (BaseHTTPRequestHandler naming)
        """Respond to CORS preflight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        """Handle GET requests for `/health` and `/api/contacts`."""
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
        """Handle POST requests for `/api/contact` to insert a new contact."""
        if self.path == "/api/contact":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
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
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    """Entry point: initialize the database and start the HTTP server."""
    initialize_database()
    server = ThreadingHTTPServer((HOST, PORT), ContactRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
