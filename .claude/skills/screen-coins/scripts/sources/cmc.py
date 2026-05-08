"""CoinMarketCap source: top coins by vol/mcap ratio."""

import logging
import os

import requests
from dotenv import load_dotenv

from .base import CoinRecord, Source, bybit_tv_url

load_dotenv()

log = logging.getLogger(__name__)

_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"


class CMCSource(Source):
    name = "cmc"

    def __init__(self):
        self.api_key = os.getenv("CMC_API_KEY")
        if not self.api_key:
            raise SystemExit("CMC_API_KEY not set. Add it to .env")

    def fetch(self, limit: int = 20) -> list[CoinRecord]:
        log.info("Fetching top 500 coins from CoinMarketCap")
        listings = self._fetch_listings()
        log.info("Received %d listings from CMC", len(listings))
        results = self._filter_and_rank(listings, limit)
        log.info("Returning %d coins after filter (vol/mcap ≥ 0.2, top %d)", len(results), limit)
        return results

    def _fetch_listings(self) -> list[dict]:
        log.debug("GET %s (limit=500, sort=market_cap)", _API_URL)
        resp = requests.get(
            _API_URL,
            headers={"X-CMC_PRO_API_KEY": self.api_key},
            params={"limit": 500, "convert": "USD", "sort": "market_cap"},
            timeout=30,
        )
        log.debug("CMC response status: %s", resp.status_code)
        resp.raise_for_status()
        data = resp.json()["data"]
        log.debug("Parsed %d coin entries from CMC response", len(data))
        return data

    def _filter_and_rank(self, listings: list[dict], limit: int) -> list[CoinRecord]:
        results = []
        skipped_stablecoin = 0
        skipped_no_mcap = 0
        skipped_low_ratio = 0
        for coin in listings:
            if "stablecoin" in (coin.get("tags") or []):
                skipped_stablecoin += 1
                continue
            quote = coin["quote"]["USD"]
            mcap = quote.get("market_cap") or 0
            vol = quote.get("volume_24h") or 0
            if mcap <= 0:
                skipped_no_mcap += 1
                continue
            ratio = vol / mcap
            if ratio < 0.2:
                skipped_low_ratio += 1
                continue
            symbol = coin["symbol"]
            log.debug("Accepted %s — vol/mcap ratio: %.4f", symbol, ratio)
            results.append(CoinRecord(
                symbol=symbol,
                name=coin["name"],
                price=quote["price"],
                market_cap=mcap,
                volume_24h=vol,
                percent_change_24h=quote.get("percent_change_24h"),
                vol_mcap_ratio=round(ratio, 4),
                coinglass_url=bybit_tv_url(symbol),
                source=self.name,
            ))
        log.info(
            "Filter stats — stablecoins skipped: %d, no mcap: %d, low ratio: %d, passed: %d",
            skipped_stablecoin, skipped_no_mcap, skipped_low_ratio, len(results),
        )
        results.sort(key=lambda x: x.vol_mcap_ratio or 0, reverse=True)
        log.debug("Top result after sort: %s (ratio=%.4f)", results[0].symbol if results else "none",
                  results[0].vol_mcap_ratio or 0 if results else 0)
        return results[:limit]
