"""Santiment top price performers screener source."""

import logging

from .base import CoinRecord, Source, bybit_tv_url
from scrapers.playwright_utils import (
    browser_page,
    click_next_if_enabled,
    header_index_map,
    parse_money,
    scrape_table,
)

log = logging.getLogger(__name__)

_URL = "https://app.santiment.net/screener/top-price-performers-8853"
_MAX_PAGES = 10


class SantimentSource(Source):
    name = "santiment"

    def fetch(self, limit: int = 20) -> list[CoinRecord]:
        log.info("Opening Santiment screener: %s", _URL)
        with browser_page(_URL) as page:
            log.debug("Waiting for table rows to appear")
            page.wait_for_selector("tbody tr", timeout=30000)
            log.debug("Table rows visible; setting rows-per-page to 50")
            _set_rows_to_50(page)
            headers = header_index_map(page, "thead th")
            log.info("Santiment columns: %s", list(headers.keys()))
            rows: list[dict] = []
            pages_scraped = 0
            for page_num in range(_MAX_PAGES):
                before = len(rows)
                rows.extend(scrape_table(page, "tbody tr", headers))
                pages_scraped = page_num + 1
                log.debug("Page %d scraped: +%d rows (total %d)", pages_scraped, len(rows) - before, len(rows))
                if len(rows) >= limit * 3:
                    log.debug("Over-fetch threshold reached (%d rows for limit=%d), stopping pagination", len(rows), limit)
                    break
                if not click_next_if_enabled(page, 'button:has-text("Next")'):
                    log.debug("No more pages (Next button disabled or absent)")
                    break
                log.debug("Navigating to page %d", page_num + 2)
                # Wait for the first row's rank number to change — it's a reliable signal
                # that the table has refreshed (td:nth-child(2) = the # column)
                last_rank = rows[-1].get("#", "") if rows else ""
                try:
                    page.wait_for_function(
                        f"() => document.querySelector('tbody tr td:nth-child(2)')?.innerText !== {repr(last_rank)}",
                        timeout=3000,
                    )
                    log.debug("Table refreshed (rank changed from %r)", last_rank)
                except Exception:
                    log.debug("Table refresh wait timed out; using 800ms fallback")
                    page.wait_for_timeout(800)
            log.info("Scraped %d raw rows across %d page(s)", len(rows), pages_scraped)
            records = _to_records(rows)[:limit]
            log.info("Returning %d Santiment records (limit=%d)", len(records), limit)
            return records


def _set_rows_to_50(page) -> None:
    """Click the rows-per-page trigger and select 50."""
    try:
        page.locator("button.rows-trigger").click(timeout=5000)
        log.debug("Clicked rows-per-page trigger")
        page.locator(".rows-dropdown >> text=50").click(timeout=5000)
        log.debug("Selected 50 rows per page")
        page.wait_for_timeout(500)
    except Exception as exc:
        log.debug("Could not set rows-per-page (dropdown may not exist or already 50): %s", exc)


def _to_records(rows: list[dict]) -> list[CoinRecord]:
    records = []
    seen = set()
    skipped_no_symbol = 0
    skipped_duplicate = 0
    for row in rows:
        symbol = _extract_symbol(row)
        if not symbol:
            log.debug("Skipping row — could not extract symbol: %s", row)
            skipped_no_symbol += 1
            continue
        if symbol in seen:
            log.debug("Skipping duplicate symbol: %s", symbol)
            skipped_duplicate += 1
            continue
        seen.add(symbol)
        name_raw = row.get("Name", "") or row.get("Project", "")
        records.append(CoinRecord(
            symbol=symbol,
            name=name_raw.split("\n")[0].strip() or None,
            price=parse_money(row.get("Price", "")),
            market_cap=parse_money(row.get("Market Cap", "") or row.get("Marketcap", "")),
            volume_24h=parse_money(row.get("Volume", "") or row.get("Volume 24h", "")),
            percent_change_24h=parse_money(
                row.get("% 24h", "") or row.get("24h Change", "") or row.get("Price, 1d %", "")
            ),
            coinglass_url=bybit_tv_url(symbol),
            source="santiment",
        ))
    log.info(
        "Converted rows to records — accepted: %d, no-symbol: %d, duplicates: %d",
        len(records), skipped_no_symbol, skipped_duplicate,
    )
    return records


def _extract_symbol(row: dict) -> str | None:
    """Pull the ticker symbol from Name/Project cell (usually 'Bitcoin\nBTC' format)."""
    name_cell = row.get("Name", "") or row.get("Project", "")
    parts = name_cell.strip().split("\n")
    if len(parts) >= 2:
        symbol = parts[-1].strip().upper() or None
        log.debug("Extracted symbol '%s' from Name/Project cell parts", symbol)
        return symbol
    # Some pages put symbol in a separate column
    sym = row.get("Ticker", "") or row.get("Symbol", "")
    symbol = sym.strip().upper() or None
    if symbol:
        log.debug("Extracted symbol '%s' from Ticker/Symbol column", symbol)
    return symbol
