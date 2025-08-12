"""Playwright-based E2E tests for the frontend contact form UX.

These tests run against the static `index.html` over the `file://` protocol and
mock network calls to exercise success, validation error, and network failure
scenarios without requiring a live backend.
"""

import os
import time
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


class FrontendE2ETests(unittest.TestCase):
    """End-to-end UI tests that verify form validation and messaging behavior."""

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

        # Intercept Tailwind CDN to avoid network dependency but keep 'tailwind' defined
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
        # Mock API success
        def fulfill_success(route, request):
            if request.method == 'POST':
                route.fulfill(
                    status=201,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json",
                    },
                    body='{"message":"Contact submitted successfully"}',
                )
            else:
                route.fallback()

        self.page.route("https://adventaiservices.com/api/contact", fulfill_success)

        self._goto_page()
        self._fill_form_and_submit("Alice", "alice@example.com", f"Hello {int(time.time()*1000)}")

        success = self.page.locator('#success-message')
        error = self.page.locator('#error-message')

        expect(success).to_be_visible()
        expect(error).to_be_hidden()

    def test_validation_error_shows_server_error_text(self):
        # Mock API validation error
        def fulfill_validation_error(route, request):
            if request.method == 'POST':
                route.fulfill(
                    status=400,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Content-Type": "application/json",
                    },
                    body='{"error":"All fields are required"}',
                )
            else:
                route.fallback()

        self.page.route("https://adventaiservices.com/api/contact", fulfill_validation_error)

        self._goto_page()
        # Use valid values so native HTML5 validation does not block form submission
        self._fill_form_and_submit("Alice QA", "alice.qa@example.com", "trigger server validation message")

        error = self.page.locator('#error-message')
        expect(error).to_be_visible()
        expect(error).to_contain_text("All fields are required")

    def test_network_failure_shows_fetch_error_message(self):
        # Simulate network failure
        def abort_network(route, request):
            if request.method == 'POST':
                route.abort(error_code='failed')
            else:
                route.fallback()

        self.page.route("https://adventaiservices.com/api/contact", abort_network)

        self._goto_page()
        self._fill_form_and_submit("Bob", "bob@example.com", "Network down")

        error = self.page.locator('#error-message')
        expect(error).to_be_visible()
        # Browser message may vary; assert it includes "Failed" which covers typical "Failed to fetch"
        expect(error).to_contain_text("Failed")