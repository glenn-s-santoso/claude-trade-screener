#!/usr/bin/env python3
"""Take Coinglass chart screenshots for a specific ticker at multiple timeframes."""

import argparse
import time
from pathlib import Path

from playwright.sync_api import Page

from scrapers.playwright_utils import coinglass_page, screenshot_page

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHARTS_DIR = DATA_DIR / "charts"

TIMEFRAME_SETTINGS = {
    "m15": {"cg_atinterval_v2main": "m15", "tradingview.chart.lastUsedTimeBasedResolution": "15"},
    "h1": {"cg_atinterval_v2main": "h1", "tradingview.chart.lastUsedTimeBasedResolution": "60"},
    "h4": {"cg_atinterval_v2main": "h4", "tradingview.chart.lastUsedTimeBasedResolution": "240"},
}

DEFAULT_TIMEFRAMES = ["h1", "h4", "m15"]


def build_coinglass_url(symbol: str) -> str:
    return f"https://www.coinglass.com/tv/Bybit_{symbol}USDT"


def screenshot_timeframe(page: Page, symbol: str, timeframe: str, max_retries: int = 3) -> bool:
    settings = TIMEFRAME_SETTINGS[timeframe]
    for key, value in settings.items():
        page.evaluate(f"localStorage.setItem('{key}', '{value}')")

    url = build_coinglass_url(symbol)
    return screenshot_page(page, url, CHARTS_DIR / f"{symbol}_{timeframe}.png", f"{symbol} [{timeframe}]", max_retries)


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot Coinglass charts for a specific ticker at multiple timeframes"
    )
    parser.add_argument("--ticker", required=True, help="Coin symbol, e.g. BTC or BTCUSDT")
    parser.add_argument(
        "--timeframes",
        default=",".join(DEFAULT_TIMEFRAMES),
        help=f"Comma-separated timeframes: {', '.join(TIMEFRAME_SETTINGS)} (default: {','.join(DEFAULT_TIMEFRAMES)})",
    )
    args = parser.parse_args()

    symbol = args.ticker.upper().removesuffix("USDT")
    timeframes = [tf.strip() for tf in args.timeframes.split(",")]

    invalid = [tf for tf in timeframes if tf not in TIMEFRAME_SETTINGS]
    if invalid:
        raise SystemExit(f"Unknown timeframes: {', '.join(invalid)}. Valid: {', '.join(TIMEFRAME_SETTINGS)}")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Screenshotting {symbol} at: {', '.join(timeframes)}")

    with coinglass_page() as page:
        success = 0
        for i, tf in enumerate(timeframes):
            if i > 0:
                time.sleep(1.5)
            if screenshot_timeframe(page, symbol, tf):
                success += 1

    print(f"Done. {success}/{len(timeframes)} screenshots saved to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
