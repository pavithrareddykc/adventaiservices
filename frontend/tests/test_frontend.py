"""Playwright-based E2E tests for the frontend contact form UX (Formspree flow).

These tests run against the static `index.html` over the `file://` protocol and
mock Formspree requests to verify:
- Successful submission redirects back and shows inline success message
- Native HTML5 validation prevents submission (no network call)
"""

import os
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs

from playwright.sync_api import sync_playwright, expect


class FrontendE2ETests(unittest.TestCase):
    """End-to-end UI tests that verify form behavior with Formspree submissions."""

    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()
        cls.context = cls.browser.new_context()
        cls.page = cls.context.new_page()

        # Resolve file:// URL to root index.html
        repo_root = Path(__file__).resolve().parents[2]
        index_path = repo_root / "index.html"
        cls.index_url = f"file://{index_path}"
        cls.redirect_url = "https://www.adventaiservices.com/?submitted=1#contact"
        cls.index_html = index_path.read_text(encoding="utf-8")

        # Intercept Tailwind CDN to avoid network dependency but keep `tailwind` defined
        def tailwind_route(route):
            route.fulfill(
                status=200,
                headers={"Content-Type": "application/javascript"},
                body="""
                // Minimal stub so `tailwind` exists and inline config assignment doesn't crash
                window.tailwind = window.tailwind || {};
                """,
            )

        cls.page.route("https://cdn.tailwindcss.com/**", tailwind_route)

        # Block fonts to speed up tests and avoid external network
        cls.page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
        cls.page.route("https://fonts.gstatic.com/**", lambda route: route.abort())
        # Block unpkg (React/Babel CDN) to keep tests offline; page should still function without React
        cls.page.route("https://unpkg.com/**", lambda route: route.abort())

    @classmethod
    def tearDownClass(cls):
        try:
            cls.context.close()
            cls.browser.close()
            cls.playwright.stop()
        except Exception:
            pass

    def _goto_page(self):
        """Open the local index page and ensure `.hidden` works without Tailwind."""
        self.page.goto(self.index_url)
        # Ensure the 'hidden' class behaves even without Tailwind CSS by injecting minimal CSS
        self.page.add_style_tag(content=".hidden{display:none !important}")

    def _fill_form_and_submit(self, name: str, email: str, message: str):
        """Helper to populate the contact form and click submit."""
        self.page.fill('#name', name)
        self.page.fill('#email', email)
        self.page.fill('#message', message)
        self.page.click('#submit-button')

    def test_successful_submission_shows_success_message(self):
        """Mock Formspree POST to redirect back to index with success flag and assert inline success."""
        captured = {"called": False, "body": "", "content_type": ""}

        # Mock POST to Formspree: 302 redirect to production thanks URL
        def formspree_post(route, request):
            if request.method == 'POST':
                captured["called"] = True
                captured["content_type"] = request.header_value("content-type") or ""
                captured["body"] = request.post_data or ""
                route.fulfill(
                    status=302,
                    headers={
                        "Location": self.redirect_url,
                        "Content-Type": "text/html; charset=utf-8",
                    },
                    body="",
                )
            else:
                route.fallback()

        # Mock GET of redirect URL to serve local index.html content (showing success message)
        def redirect_get(route, request):
            route.fulfill(
                status=200,
                headers={"Content-Type": "text/html; charset=utf-8"},
                body=self.index_html,
            )

        self.page.route("https://formspree.io/f/xnnzwrbl", formspree_post)
        self.page.route(self.redirect_url, redirect_get)

        self._goto_page()
        unique_msg = f"Hello {int(time.time()*1000)}"
        self._fill_form_and_submit("Alice", "alice@example.com", unique_msg)

        # Wait for redirect to the mocked success URL
        self.page.wait_for_url(self.redirect_url)

        # Assert inline success message is visible
        success_el = self.page.locator('#success-message')
        expect(success_el).to_be_visible()
        expect(success_el).to_contain_text("Thank you")

        # Assert the form actually submitted and included expected fields
        self.assertTrue(captured["called"], "Formspree POST was not called")
        parsed = parse_qs(captured["body"]) if captured["body"] else {}
        for key in ("name", "email", "message", "_next"):
            self.assertIn(key, parsed, f"Missing field in payload: {key}")

    def test_html5_validation_blocks_submission(self):
        """Ensure native validation prevents network call when required fields are missing/invalid."""
        called = {"value": False}

        def formspree_probe(route, request):
            if request.method == 'POST':
                called["value"] = True
                route.abort(error_code='failed')
            else:
                route.fallback()

        self.page.route("https://formspree.io/f/xnnzwrbl", formspree_probe)

        self._goto_page()
        # Leave required fields blank to trigger native validation
        self._fill_form_and_submit("", "not-an-email", "")

        # Give the browser a moment in case it would attempt a submission (it shouldn't)
        self.page.wait_for_timeout(300)

        # No POST should have been made due to HTML5 validation
        self.assertFalse(called["value"], "Form submission should be blocked by native validation")
        # Still on the index file URL
        self.assertTrue(self.page.url.startswith("file://"))
        self.assertIn("index.html", self.page.url)