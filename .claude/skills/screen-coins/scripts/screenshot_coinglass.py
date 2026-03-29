#!/usr/bin/env python3
"""Take Coinglass 4H chart screenshots for each coin in screening results."""

import json
import time
from pathlib import Path

from playwright.sync_api import Page

from utils import coinglass_page, screenshot_page

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESULTS_FILE = DATA_DIR / "screening_results.json"
CHARTS_DIR = DATA_DIR / "charts"

LOCAL_STORAGE_ITEMS = {
    "cg_atinterval_v2main": "h4",
    "tradingview.chart.lastUsedTimeBasedResolution": "240",
}


def screenshot_coin(page: Page, symbol: str, url: str, max_retries: int = 3) -> bool:
    return screenshot_page(page, url, CHARTS_DIR / f"{symbol}.png", symbol, max_retries)


def main():
    if not RESULTS_FILE.exists():
        raise SystemExit(f"No screening results found at {RESULTS_FILE}. Run screen_cmc.py first.")

    coins = json.loads(RESULTS_FILE.read_text())
    if not coins:
        raise SystemExit("No coins in screening results.")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Taking screenshots for {len(coins)} coins...")

    with coinglass_page() as page:
        for key, value in LOCAL_STORAGE_ITEMS.items():
            page.evaluate(f"localStorage.setItem('{key}', '{value}')")

        success = 0
        for i, coin in enumerate(coins):
            if i > 0:
                time.sleep(1.5)
            if screenshot_coin(page, coin["symbol"], coin["coinglass_url"]):
                success += 1
    print(f"Done. {success}/{len(coins)} screenshots saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
