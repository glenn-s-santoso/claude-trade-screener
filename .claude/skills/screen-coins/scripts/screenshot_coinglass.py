#!/usr/bin/env python3
"""Take Coinglass 4H chart screenshots for each coin in screening results."""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_FILE = DATA_DIR / "screening_results.json"
CHARTS_DIR = DATA_DIR / "charts"

LOCAL_STORAGE_ITEMS = {
    "cg_atinterval_v2main": "h4",
    "tradingview.chart.lastUsedTimeBasedResolution": "240",
}


def screenshot_coin(page, symbol: str, url: str, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for TradingView canvas to render
            time.sleep(10)
            output = CHARTS_DIR / f"{symbol}.png"
            page.screenshot(path=str(output), full_page=False)
            if attempt > 0:
                print(f"  ✓ {symbol} (retry {attempt})")
            else:
                print(f"  ✓ {symbol}")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  ⟳ {symbol}: Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ✗ {symbol}: {e}")
                return False
    return False


def main():
    if not RESULTS_FILE.exists():
        raise SystemExit(f"No screening results found at {RESULTS_FILE}. Run screen_cmc.py first.")

    coins = json.loads(RESULTS_FILE.read_text())
    if not coins:
        raise SystemExit("No coins in screening results.")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Taking screenshots for {len(coins)} coins...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

        # Seed localStorage by visiting coinglass first
        page = context.new_page()
        page.goto("https://www.coinglass.com", wait_until="domcontentloaded", timeout=30000)
        for key, value in LOCAL_STORAGE_ITEMS.items():
            page.evaluate(f"localStorage.setItem('{key}', '{value}')")

        success = 0
        for i, coin in enumerate(coins):
            if i > 0:
                time.sleep(1.5)
            if screenshot_coin(page, coin["symbol"], coin["coinglass_url"]):
                success += 1

        browser.close()
    print(f"Done. {success}/{len(coins)} screenshots saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
