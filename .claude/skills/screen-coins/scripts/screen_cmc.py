#!/usr/bin/env python3
"""Fetch top cryptos from CoinMarketCap and filter by volume/market_cap ratio."""

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "screening_results.json"


def fetch_listings(api_key: str) -> list[dict]:
    resp = requests.get(
        API_URL,
        headers={"X-CMC_PRO_API_KEY": api_key},
        params={"limit": 500, "convert": "USD", "sort": "market_cap"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def filter_and_rank(listings: list[dict]) -> list[dict]:
    results = []
    for coin in listings:
        if "stablecoin" in (coin.get("tags") or []):
            continue
        quote = coin["quote"]["USD"]
        mcap = quote.get("market_cap") or 0
        vol = quote.get("volume_24h") or 0
        if mcap <= 0:
            continue
        ratio = vol / mcap
        if ratio < 0.2:
            continue
        symbol = coin["symbol"]
        results.append({
            "symbol": symbol,
            "name": coin["name"],
            "price": quote["price"],
            "market_cap": mcap,
            "volume_24h": vol,
            "vol_mcap_ratio": round(ratio, 4),
            "percent_change_24h": quote.get("percent_change_24h"),
            "coinglass_url": f"https://www.coinglass.com/tv/Bybit_{symbol}USDT",
        })
    results.sort(key=lambda x: x["vol_mcap_ratio"], reverse=True)
    return results[:20]


def main():
    api_key = os.getenv("CMC_API_KEY")
    if not api_key:
        raise SystemExit("CMC_API_KEY not set. Add it to .env")

    print("Fetching top 200 coins from CoinMarketCap...")
    listings = fetch_listings(api_key)
    results = filter_and_rank(listings)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print(f"Saved {len(results)} coins to {OUTPUT_FILE}")

    for i, c in enumerate(results, 1):
        print(f"  {i:2}. {c['symbol']:>8}  ratio={c['vol_mcap_ratio']:.4f}  24h={c['percent_change_24h']:+.1f}%")


if __name__ == "__main__":
    main()
