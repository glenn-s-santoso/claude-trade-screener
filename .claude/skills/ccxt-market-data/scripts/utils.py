"""Shared utilities for ccxt-market-data scripts."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import ccxt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Exchanges with known-good futures support (OI + funding rates).
# For any exchange not listed here, market_metrics will warn and attempt a direct pass-through.
FUTURES_EXCHANGE_MAP: dict[str, str] = {
    "binance": "binanceusdm",
}


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def days_ago_ms(days: int) -> int:
    return now_ms() - int(days * 24 * 60 * 60 * 1000)


def hours_ago_ms(hours: float) -> int:
    return now_ms() - int(hours * 60 * 60 * 1000)


def normalize_symbol(symbol: str) -> tuple[str, str]:
    """Return (spot_symbol, futures_symbol) from any common format.

    Examples:
        "BTCUSDT"   → ("BTC/USDT", "BTC/USDT:USDT")
        "BTC/USDT"  → ("BTC/USDT", "BTC/USDT:USDT")
        "BTC"       → ("BTC/USDT", "BTC/USDT:USDT")
    """
    s = symbol.upper().replace("/", "").split(":")[0]  # strip :USDT suffix if present
    base = s[:-4] if s.endswith("USDT") else s
    return f"{base}/USDT", f"{base}/USDT:USDT"


def make_exchange(name: str) -> ccxt.Exchange:
    """Instantiate a spot ccxt exchange with rate limiting enabled."""
    if not hasattr(ccxt, name):
        sys.exit(f"Unknown exchange '{name}'. Run `python -c \"import ccxt; print(ccxt.exchanges)\"` for a full list.")
    ex = getattr(ccxt, name)({"enableRateLimit": True})
    ex.load_markets()
    return ex


def make_futures_exchange(name: str) -> ccxt.Exchange:
    """Instantiate a futures ccxt exchange, mapping spot names to their futures counterpart."""
    fut_name = FUTURES_EXCHANGE_MAP.get(name)
    if fut_name is None:
        print(
            f"  WARNING: '{name}' has no known futures exchange mapping. "
            f"Attempting to use '{name}' directly — OI and funding data may be incorrect. "
            f"Known mappings: {FUTURES_EXCHANGE_MAP}"
        )
        fut_name = name
    if not hasattr(ccxt, fut_name):
        sys.exit(f"Futures exchange '{fut_name}' not found in ccxt.")
    ex = getattr(ccxt, fut_name)({"enableRateLimit": True})
    ex.load_markets()
    return ex
