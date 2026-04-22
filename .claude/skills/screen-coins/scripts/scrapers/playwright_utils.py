"""Shared Playwright screenshot and scraping utilities."""

import re
import time
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


@contextmanager
def browser_page(url: str | None = None):
    """Launch headless Chromium; optionally pre-navigate to url."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=_USER_AGENT,
        )
        page = context.new_page()
        if url:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        yield page
        browser.close()


@contextmanager
def coinglass_page():
    """Thin wrapper: browser pre-navigated to coinglass.com."""
    with browser_page("https://www.coinglass.com") as page:
        yield page


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


def header_index_map(page: Page, header_selector: str) -> dict[str, int]:
    """Return {header_text: column_index} from a thead."""
    headers = page.locator(header_selector).all()
    return {h.inner_text().strip(): i for i, h in enumerate(headers)}


def scrape_table(page: Page, row_selector: str, headers: dict[str, int]) -> list[dict]:
    """Extract rows from a table; each row is a dict keyed by header name."""
    rows = page.locator(row_selector).all()
    results = []
    for row in rows:
        cells = row.locator("td").all()
        if not cells:
            continue
        record = {}
        for header, idx in headers.items():
            if idx < len(cells):
                record[header] = cells[idx].inner_text().strip()
        results.append(record)
    return results


def click_next_if_enabled(page: Page, selector: str) -> bool:
    """Click the 'Next' button if it's not disabled. Returns True if clicked."""
    btn = page.locator(selector).first
    if btn.count() == 0:
        return False
    # Check both disabled property and aria-disabled attribute
    try:
        is_disabled = btn.is_disabled()
    except Exception:
        is_disabled = True
    if is_disabled:
        return False
    aria_disabled = btn.get_attribute("aria-disabled")
    if aria_disabled in ("true", "True"):
        return False
    btn.click()
    return True


def parse_money(s: str) -> float | None:
    """Parse strings like '$1.23B', '45.6M', '-12.3%' into a float."""
    if not s:
        return None
    s = s.strip().replace(",", "")
    multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
    m = re.match(r"^[+\-$]*([\d.]+)\s*([TBMK%])?$", s, re.IGNORECASE)
    if not m:
        return None
    value = float(m.group(1))
    suffix = (m.group(2) or "").upper()
    if suffix in multipliers:
        value *= multipliers[suffix]
    if s.startswith("-"):
        value = -value
    return value
