"""Regression tests for security response headers and cross-origin write protection."""
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch

from server import make_server


class SecurityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "NAGORA_DEMO_ONLY": "0",
            "RENDER": "false",
            "RENDER_EXTERNAL_URL": "",
            "NAGORA_ORIGIN": "",
        })
        self.env.start()
        self.server = make_server(Path(self.tmp.name) / "security.sqlite", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.env.stop()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        status = response.status
        response_headers = dict(response.getheaders())
        response.read()
        connection.close()
        return status, response_headers

    def test_security_headers_on_public_routes(self):
        for path in ("/", "/api/config", "/app.js", "/style.css"):
            with self.subTest(path=path):
                status, headers = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
                self.assertEqual(headers.get("Cache-Control"), "no-store")
                self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))

    def test_cross_origin_write_rejected(self):
        status, _ = self.request(
            "POST", "/api/login",
            body='{"email":"test@example.com","password":"invalid"}',
            headers={"Origin": "https://attacker.example", "Content-Type": "application/json"},
        )
        self.assertEqual(status, 403)

    def test_missing_origin_write_rejected(self):
        status, _ = self.request(
            "POST", "/api/login",
            body='{"email":"test@example.com","password":"invalid"}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
