"""Integration tests for the minimal contact backend.

These tests spin up the HTTP server (if not already running) and exercise
health, validation, insertion, and listing flows over real HTTP.
"""

import json
import os
import signal
import subprocess
import time
import unittest
from urllib import request, error


BASE_URL = "http://localhost:5000"


def http_get(path: str):
    """Perform a GET request to the running backend and return (status_code, body_str)."""
    req = request.Request(f"{BASE_URL}{path}", method="GET")
    with request.urlopen(req, timeout=5) as resp:
        return resp.getcode(), resp.read().decode("utf-8")


def http_post(path: str, payload: dict):
    """Perform a POST with a JSON body and return (status_code, body_str).

    On non-2xx responses, this function returns the HTTP error code and error
    body instead of raising.
    """
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as resp:
            return resp.getcode(), resp.read().decode("utf-8")
    except error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, body


class BackendIntegrationTests(unittest.TestCase):
    """End-to-end tests targeting the real HTTP interface of the backend server."""
    server_proc = None

    @classmethod
    def setUpClass(cls):
        # Check if server is already up; if not, start it
        try:
            code, _ = http_get("/health")
            if code == 200:
                return
        except Exception:
            pass

        cls.server_proc = subprocess.Popen(
            ["python3", "app.py"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # wait for health
        for _ in range(30):
            try:
                code, _ = http_get("/health")
                if code == 200:
                    return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError("Backend server did not become healthy in time")

    @classmethod
    def tearDownClass(cls):
        if cls.server_proc and cls.server_proc.poll() is None:
            try:
                cls.server_proc.terminate()
                time.sleep(0.5)
                if cls.server_proc.poll() is None:
                    cls.server_proc.kill()
            except Exception:
                pass

    def test_health(self):
        code, body = http_get("/health")
        self.assertEqual(code, 200)
        self.assertIn("\"status\": \"ok\"", body)

    def test_submit_contact_and_list(self):
        unique_msg = f"Hello from tests {int(time.time()*1000)}"
        payload = {"name": "CI Tester", "email": "ci@example.com", "message": unique_msg}
        code, body = http_post("/api/contact", payload)
        self.assertEqual(code, 201, msg=body)
        self.assertIn("Contact submitted successfully", body)

        code, body = http_get("/api/contacts")
        self.assertEqual(code, 200)
        self.assertIn(unique_msg, body)

    def test_validation(self):
        code, body = http_post("/api/contact", {"name": "", "email": "a@b.c", "message": ""})
        self.assertEqual(code, 400)
        self.assertIn("All fields are required", body)

    def test_storage_fields_exact_match(self):
        # Submit a payload with surrounding whitespace to verify trimming and exact storage
        unique_suffix = str(int(time.time() * 1000))
        raw_name = f"  Alice QA {unique_suffix}  "
        raw_email = f"  alice.qa+{unique_suffix}@example.com  "
        raw_message = f"  Hello storage check {unique_suffix}  "

        payload = {
            "name": raw_name,
            "email": raw_email,
            "message": raw_message,
        }

        code, body = http_post("/api/contact", payload)
        self.assertEqual(code, 201, msg=body)
        self.assertIn("Contact submitted successfully", body)

        code, body = http_get("/api/contacts")
        self.assertEqual(code, 200)

        data = json.loads(body)
        contacts = data.get("contacts", [])
        self.assertIsInstance(contacts, list)

        expected_name = raw_name.strip()
        expected_email = raw_email.strip()
        expected_message = raw_message.strip()

        # Find the inserted record by unique message
        match = None
        for c in contacts:
            if c.get("message") == expected_message:
                match = c
                break

        self.assertIsNotNone(match, msg=f"Did not find stored contact with message: {expected_message}")
        self.assertEqual(match.get("name"), expected_name)
        self.assertEqual(match.get("email"), expected_email)
        self.assertIn("id", match)
        self.assertIsInstance(match.get("id"), int)
        self.assertIn("created_at", match)
        self.assertIsInstance(match.get("created_at"), str)


if __name__ == "__main__":
    unittest.main(verbosity=2)


