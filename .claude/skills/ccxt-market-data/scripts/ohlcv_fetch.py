#!/usr/bin/env python3
"""
Fetch historical OHLCV candles via ccxt (no API keys required).

Usage:
    python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1h --days 7
    python scripts/ohlcv_fetch.py --symbol BTCUSDT --timeframe 5m --days 1
    python scripts/ohlcv_fetch.py --symbol ETH/USDT --timeframe 15m --days 3 --exchange bybit
    python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1h --days 7 --summary-only
    python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1m --days 1 --quiet

Output: data/ohlcv_{SYMBOL}_{TIMEFRAME}_{N}d.json
"""

import argparse
import json
import time
from datetime import datetime, timezone

import ccxt

from utils import DATA_DIR, make_exchange, ms_to_iso, normalize_symbol, now_ms

CANDLES_PER_REQ = 1000

QUIET = False


def _print(*args, **kwargs):
    if not QUIET:
        print(*args, **kwargs)


def fetch_ohlcv_paginated(
    exchange: ccxt.Exchange, symbol: str, timeframe: str, days: int
) -> list[dict]:
    tf_ms    = exchange.parse_timeframe(timeframe) * 1000
    _now_ms  = now_ms()
    since_ms = _now_ms - (days * 24 * 60 * 60 * 1000)

    all_candles: list = []
    seen_ts: set = set()
    batch_count = 0
    current_since = since_ms

    _print(f"Fetching {symbol} {timeframe} from {ms_to_iso(since_ms)} to {ms_to_iso(_now_ms)}")

    while current_since < _now_ms:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=CANDLES_PER_REQ)
        if not batch:
            break

        added = 0
        for c in batch:
            if c[0] not in seen_ts:
                seen_ts.add(c[0])
                all_candles.append(c)
                added += 1

        batch_count += 1
        last_ts = batch[-1][0]
        current_since = last_ts + tf_ms

        _print(f"  Batch {batch_count:>3}: {added} candles  up to {ms_to_iso(last_ts)}")

        if len(batch) < CANDLES_PER_REQ:
            break

        time.sleep(exchange.rateLimit / 1000)

    _print(f"Total: {len(all_candles)} unique candles across {batch_count} batch(es)")
    return all_candles


def main():
    global QUIET

    parser = argparse.ArgumentParser(description="Fetch paginated OHLCV data via ccxt")
    parser.add_argument("--symbol",       required=True, help="Symbol, e.g. BTC/USDT or BTCUSDT")
    parser.add_argument("--timeframe",    default="1h",  help="Timeframe: 1m 5m 15m 1h 4h 1d (default 1h)")
    parser.add_argument("--days",         default=7,     type=int,  help="Days of history (default 7)")
    parser.add_argument("--exchange",     default="binance", help="Exchange (default binance)")
    parser.add_argument("--summary-only", action="store_true", dest="summary_only",
                        help="Omit the full candles array from output (useful for large windows)")
    parser.add_argument("--quiet",        action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    QUIET = args.quiet

    spot_symbol, _ = normalize_symbol(args.symbol)
    tag = spot_symbol.replace("/", "-")

    _print("\n=== ccxt OHLCV fetch ===")
    _print(f"Symbol    : {spot_symbol}")
    _print(f"Timeframe : {args.timeframe}")
    _print(f"Days      : {args.days}")
    _print(f"Exchange  : {args.exchange}")
    if args.summary_only:
        _print("Mode      : summary only (candles array omitted)")
    _print()

    exchange = make_exchange(args.exchange)

    if args.timeframe not in exchange.timeframes:
        raise SystemExit(
            f"Timeframe '{args.timeframe}' not supported by {args.exchange}. "
            f"Available: {list(exchange.timeframes.keys())}"
        )

    candles_raw = fetch_ohlcv_paginated(exchange, spot_symbol, args.timeframe, args.days)

    candles = [
        {
            "timestamp_ms": c[0],
            "datetime":     ms_to_iso(c[0]),
            "open":         c[1],
            "high":         c[2],
            "low":          c[3],
            "close":        c[4],
            "volume":       c[5],
        }
        for c in candles_raw
    ]

    result: dict = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "symbol":        spot_symbol,
        "timeframe":     args.timeframe,
        "days":          args.days,
        "exchange":      args.exchange,
        "candle_count":  len(candles),
        "first_candle":  candles[0]  if candles else None,
        "last_candle":   candles[-1] if candles else None,
    }
    if not args.summary_only:
        result["candles"] = candles

    out_path = DATA_DIR / f"ohlcv_{tag}_{args.timeframe}_{args.days}d.json"
    out_path.write_text(json.dumps(result, indent=2))
    _print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
