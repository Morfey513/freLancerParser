"""Playwright browser client using a local, persistent profile."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class FreelancerBrowserClient:
    """Fetch rendered HTML through a separate, persistent Opera profile."""

    def __init__(
        self,
        profile_dir: Path,
        headless: bool = False,
        timeout_ms: int = 30_000,
        cdp_url: str | None = None,
    ) -> None:
        self.profile_dir = profile_dir
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.cdp_url = cdp_url
        self.executable_path = Path(
            os.environ.get(
                "OPERA_EXECUTABLE",
                r"C:\Users\And\AppData\Local\Programs\Opera\opera.exe",
            )
        )
        self.existing_profile_dir = Path(
            os.environ.get(
                "OPERA_PROFILE_DIR",
                r"C:\Users\And\AppData\Roaming\Opera Software\Opera Stable",
            )
        )

    def import_existing_session(self) -> None:
        """Copy the user's Opera profile once, without modifying the original.

        The copied profile is deliberately kept under ``data`` and must never
        be committed because it can contain authenticated session data.
        """
        if self.profile_dir.exists():
            return
        if not self.existing_profile_dir.is_dir():
            raise FileNotFoundError(
                "Existing Opera profile was not found. Set OPERA_PROFILE_DIR to its full path."
            )
        shutil.copytree(
            self.existing_profile_dir,
            self.profile_dir,
            ignore=shutil.ignore_patterns("Singleton*", "lockfile"),
        )

    def _launch_context(self, playwright):
        if not self.executable_path.is_file():
            raise FileNotFoundError(
                "Opera was not found. Set OPERA_EXECUTABLE to the full path of opera.exe."
            )
        return playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            executable_path=str(self.executable_path),
            headless=self.headless,
        )

    def save_login_session(self) -> None:
        """Allow the user to authenticate manually in a visible browser window."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = self._launch_context(playwright)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.freelancer.com/login", wait_until="domcontentloaded")
            input("After you have logged in, press Enter to save the session and close the browser... ")
            context.close()

    def fetch_page(self, url: str) -> str:
        if self.cdp_url:
            return self._fetch_from_existing_opera(url)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = self._launch_context(playwright)
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                try:
                    page.wait_for_selector(".JobSearchCard-item", timeout=self.timeout_ms)
                except PlaywrightTimeoutError:
                    # Preserve the HTML for diagnosis if the page changes or redirects.
                    pass
                return page.content()
            finally:
                context.close()

    def _fetch_from_existing_opera(self, url: str) -> str:
        """Attach to Opera over CDP without closing the user's browser."""
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(self.cdp_url)
            if not browser.contexts:
                raise RuntimeError("Opera has no available browser context.")
            context = browser.contexts[0]
            page = next((item for item in context.pages if "freelancer.com" in item.url), None)
            if page is None:
                page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            try:
                page.wait_for_selector(".JobSearchCard-item", timeout=self.timeout_ms)
            except PlaywrightTimeoutError:
                pass
            # Do not call browser.close(): this is the user's Opera process.
            return page.content()
