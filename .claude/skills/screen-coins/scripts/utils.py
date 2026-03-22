"""Shared Playwright screenshot utilities."""

import time
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


@contextmanager
def coinglass_page():
    """Launch a headless Chromium browser and yield a Page already at coinglass.com."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=_USER_AGENT,
        )
        page = context.new_page()
        page.goto("https://www.coinglass.com", wait_until="domcontentloaded", timeout=30000)
        yield page
        browser.close()


def screenshot_page(page: Page, url: str, output: Path, label: str, max_retries: int = 3) -> bool:
    """Navigate to url, wait for TradingView canvas, screenshot, with retry."""
    for attempt in range(max_retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(10)  # Wait for TradingView canvas to render
            page.screenshot(path=str(output), full_page=False)
            print(f"  ✓ {label}" if attempt == 0 else f"  ✓ {label} (retry {attempt})")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2**attempt
                print(f"  ⟳ {label}: Retry {attempt + 1}/{max_retries} after {wait}s...")
                time.sleep(wait)
            else:
                print(f"  ✗ {label}: {e}")
                return False
    return False
