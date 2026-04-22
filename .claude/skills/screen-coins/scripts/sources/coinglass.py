"""Coinglass derivatives screener source — ranked by OI descending."""

import logging
import re

from .base import CoinRecord, Source, bybit_tv_url
from scrapers.playwright_utils import browser_page, parse_money

log = logging.getLogger(__name__)

_URL = "https://www.coinglass.com/"
_MAX_PAGES = 10
_TABLE_BODY = "div.ant-table-body tbody"
_DATA_ROW = f"{_TABLE_BODY} tr:not(.ant-table-measure-row)"

# Ant Design pagination: two arrow buttons (prev / next); next is the last one
_NEXT_BTN = "button.MuiButton-root.MuiButton-variantOutlined.MuiButton-colorNeutral"

# Tokens that are not tradeable setups
_SKIP_SYMBOLS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "FRAX", "LUSD", "USDD"}

# Column positions as seen in the Derivatives tab (0-based)
# ★ | Ranking | Symbol | Price | Price(24h%) | Funding Rate | Vol(24h) | Vol(24h%)
# | Market Cap | OI | OI(1h%) | OI(24h%) | Liquidation(24h)
_COL = {
    "symbol": 2,
    "price": 3,
    "price_24h": 4,
    "funding_rate": 5,
    "volume_24h": 6,
    "market_cap": 8,
    "oi": 9,
    "oi_1h": 10,
    "oi_24h": 11,
    "liquidation_24h": 12,
}


class CoinglassSource(Source):
    name = "coinglass"

    def fetch(self, limit: int = 20) -> list[CoinRecord]:
        log.info("Opening Coinglass: %s", _URL)
        with browser_page(_URL) as page:
            log.debug("Waiting for table rows to appear")
            page.wait_for_selector(_DATA_ROW, timeout=30000)
            log.debug("Table visible; sorting by OI (24h%%) descending")
            _sort_by_oi_24h_desc(page)

            raw_rows: list[dict] = []
            for page_num in range(_MAX_PAGES):
                before = len(raw_rows)
                raw_rows.extend(_scrape_rows(page))
                log.debug("Page %d scraped: +%d rows (total %d)", page_num + 1, len(raw_rows) - before, len(raw_rows))
                if len(raw_rows) >= limit * 3:
                    log.debug("Over-fetch threshold reached (%d rows), stopping pagination", len(raw_rows))
                    break
                if not _click_next(page):
                    log.debug("No more pages (Next button disabled or absent)")
                    break

            log.info("Scraped %d raw rows across %d page(s)", len(raw_rows), page_num + 1)
            records = _to_records(raw_rows, limit)
            log.info("Returning %d Coinglass records (limit=%d)", len(records), limit)
            return records


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sort_by_oi_24h_desc(page) -> None:
    """Click the OI (24h%) column sorter twice to land on descending order."""
    sorter = page.locator("div.ant-table-column-sorters").filter(
        has=page.locator("span.ant-table-column-title").filter(
            has_text=re.compile(r"^\s*OI\s*\(24h%\)\s*$")
        )
    ).first
    if sorter.count() == 0:
        log.debug("OI (24h%) sorter not found by title filter; falling back to has-text")
        sorter = page.locator("div.ant-table-column-sorters:has-text('OI (24h%)')").first
    log.debug("Clicking OI (24h%%) sorter (first click — ascending)")
    sorter.click()
    page.wait_for_timeout(600)
    log.debug("Clicking OI (24h%%) sorter (second click — descending)")
    sorter.click()
    page.wait_for_timeout(800)
    log.debug("OI (24h%%) column sorted descending")


def _scrape_rows(page) -> list[dict]:
    rows = page.locator(_DATA_ROW).all()
    log.debug("Found %d raw <tr> elements on current page", len(rows))
    results = []
    skipped_short = 0
    for row in rows:
        cells = row.locator("td").all()
        if len(cells) < 9:
            skipped_short += 1
            continue
        record = {}
        for key, idx in _COL.items():
            record[key] = cells[idx].inner_text().strip() if idx < len(cells) else ""
        results.append(record)
    if skipped_short:
        log.debug("Skipped %d rows with fewer than 8 cells", skipped_short)
    log.debug("Extracted %d valid rows from page", len(results))
    return results


def _click_next(page) -> bool:
    """Click the rightmost pagination arrow (Next). Returns False when disabled."""
    btns = page.locator(_NEXT_BTN).all()
    if not btns:
        log.debug("Pagination buttons not found; assuming last page")
        return False
    next_btn = btns[-1]
    try:
        if next_btn.is_disabled():
            log.debug("Next button is disabled")
            return False
    except Exception as exc:
        log.debug("Could not check Next button disabled state: %s", exc)
        return False
    aria_disabled = next_btn.get_attribute("aria-disabled")
    if aria_disabled in ("true", "True"):
        log.debug("Next button has aria-disabled=%s", aria_disabled)
        return False

    try:
        first_text = page.locator(f"{_DATA_ROW} td").nth(1).inner_text()
    except Exception:
        first_text = ""
    log.debug("Clicking Next; current first data-row cell text: %r", first_text[:40] if first_text else "")
    next_btn.click()
    try:
        page.wait_for_function(
            f"() => document.querySelector('{_TABLE_BODY} tr:not(.ant-table-measure-row) td:nth-child(2)')?.innerText"
            f" !== {repr(first_text)}",
            timeout=3000,
        )
        log.debug("Table refreshed after Next click")
    except Exception:
        log.debug("Table refresh wait timed out; using 1000ms fallback")
        page.wait_for_timeout(1000)
    return True


def _extract_symbol(cell_text: str) -> str | None:
    """Extract ticker from cell text.

    Coinglass symbol cells typically render as 'BTC\nBitcoin' or 'Bitcoin\nBTC'.
    We pick the shortest ALL-CAPS token (≤10 chars) from the lines.
    """
    lines = [l.strip() for l in cell_text.split("\n") if l.strip()]
    # Strict match: only uppercase letters and digits, no +/-/. (rejects aggregate rows like "+3.47K")
    candidates = [l for l in lines if re.match(r'^[A-Z][A-Z0-9]{1,9}$', l)]
    if candidates:
        symbol = min(candidates, key=len)
        log.debug("Extracted symbol '%s' from candidates %s", symbol, candidates)
        return symbol
    for line in lines:
        word = line.split()[0] if line.split() else ""
        if re.match(r"^[A-Z0-9]{2,10}$", word):
            log.debug("Extracted symbol '%s' via fallback regex from line %r", word, line)
            return word
    log.debug("Could not extract symbol from cell text: %r", cell_text[:60])
    return None


def _to_records(rows: list[dict], limit: int) -> list[CoinRecord]:
    records = []
    seen: set[str] = set()
    skipped_no_symbol = 0
    skipped_duplicate = 0
    skipped_stable = 0
    for row in rows:
        symbol = _extract_symbol(row.get("symbol", ""))
        if not symbol:
            skipped_no_symbol += 1
            continue
        if symbol in seen:
            skipped_duplicate += 1
            continue
        if symbol in _SKIP_SYMBOLS:
            log.debug("Skipping stablecoin/non-tradeable: %s", symbol)
            skipped_stable += 1
            continue
        seen.add(symbol)
        records.append(CoinRecord(
            symbol=symbol,
            price=parse_money(row.get("price", "")),
            percent_change_24h=parse_money(row.get("price_24h", "")),
            volume_24h=parse_money(row.get("volume_24h", "")),
            market_cap=parse_money(row.get("market_cap", "")),
            coinglass_url=bybit_tv_url(symbol),
            source="coinglass",
            extra={
                "funding_rate": row.get("funding_rate"),
                "oi": row.get("oi"),
                "oi_1h": row.get("oi_1h"),
                "oi_24h": row.get("oi_24h"),
                "liquidation_24h": row.get("liquidation_24h"),
            },
        ))
        log.debug("Accepted %s (OI: %s, OI 24h: %s, funding: %s)", symbol, row.get("oi"), row.get("oi_24h"), row.get("funding_rate"))
        if len(records) >= limit:
            log.debug("Reached limit of %d records", limit)
            break
    log.info(
        "Convert stats — accepted: %d, no-symbol: %d, duplicates: %d, stablecoins: %d",
        len(records), skipped_no_symbol, skipped_duplicate, skipped_stable,
    )
    return records
