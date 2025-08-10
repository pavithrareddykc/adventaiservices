import json
import os
import signal
import subprocess
import time
import unittest
from urllib import request, error


BASE_URL = "http://localhost:5000"


def http_get(path: str):
    req = request.Request(f"{BASE_URL}{path}", method="GET")
    with request.urlopen(req, timeout=5) as resp:
        return resp.getcode(), resp.read().decode("utf-8")


def http_post(path: str, payload: dict):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)


