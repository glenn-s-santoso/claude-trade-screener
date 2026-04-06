#!/usr/bin/env python3
"""
Fetch three market microstructure metrics via ccxt (no API keys required):
  1. Open Interest        — total outstanding futures contracts
  2. Spot CVD             — Cumulative Volume Delta (derived from raw trades)
  3. Funding Rates        — perpetual futures funding rate (current + history)

Usage:
    python scripts/market_metrics.py --symbol BTC/USDT
    python scripts/market_metrics.py --symbol BTCUSDT --days 3 --cvd-hours 4
    python scripts/market_metrics.py --symbol ETH/USDT --cvd-hours 1 --cvd-tf 1m
    python scripts/market_metrics.py --symbol BTC/USDT --quiet

Output: data/market_metrics_{SYMBOL}.json
"""

import argparse
import json
import time
from datetime import datetime, timezone

import ccxt
import pandas as pd

from utils import (
    DATA_DIR,
    days_ago_ms,
    hours_ago_ms,
    make_exchange,
    make_futures_exchange,
    ms_to_iso,
    normalize_symbol,
    now_ms,
)

TRADES_PER_REQ  = 1000
OI_LIMIT        = 500
FUNDING_LIMIT   = 1000
MAX_CVD_BATCHES = 100

# Default spot exchanges for aggregated CVD
SPOT_CVD_EXCHANGES = ["binance", "okx", "bybit", "coinbase", "bitfinex", "kraken", "bitstamp", "cryptocom"]

QUIET = False


def _print(*args, **kwargs):
    if not QUIET:
        print(*args, **kwargs)


def fetch_open_interest(futures_ex: ccxt.Exchange, futures_symbol: str, days: int) -> dict:
    _print(f"[OI] {futures_symbol}  (last {days} day(s))")

    current = futures_ex.fetch_open_interest(futures_symbol)
    current_clean = {
        "symbol":              current.get("symbol"),
        "datetime":            current.get("datetime") or ms_to_iso(current.get("timestamp", 0)),
        "openInterestAmount":  current.get("openInterestAmount"),
        "openInterestValue":   current.get("openInterestValue"),
    }
    oi_val = current_clean["openInterestValue"]
    _print(
        f"  Current OI: {current_clean['openInterestAmount']} (amount)"
        + (f"  ${oi_val:,.0f}" if oi_val else "")
    )

    since_ms = days_ago_ms(days)
    all_oi = []
    batch_count = 0

    while True:
        batch = futures_ex.fetch_open_interest_history(
            futures_symbol, timeframe="1h", since=since_ms, limit=OI_LIMIT
        )
        if not batch:
            break
        all_oi.extend(batch)
        batch_count += 1
        last_ts = batch[-1].get("timestamp", 0)
        since_ms = last_ts + 1
        if len(batch) < OI_LIMIT or since_ms >= now_ms():
            break
        time.sleep(futures_ex.rateLimit / 1000)

    history = [
        {
            "datetime":           e.get("datetime") or ms_to_iso(e.get("timestamp", 0)),
            "timestamp_ms":       e.get("timestamp"),
            "openInterestAmount": e.get("openInterestAmount"),
            "openInterestValue":  e.get("openInterestValue"),
        }
        for e in all_oi
    ]

    # Trend: compare average of first vs last quarter, using only non-None entries.
    trend = "insufficient_data"
    if len(history) >= 4:
        quarter = len(history) // 4
        early = [h["openInterestAmount"] for h in history[:quarter] if h["openInterestAmount"] is not None]
        late  = [h["openInterestAmount"] for h in history[-quarter:] if h["openInterestAmount"] is not None]
        if early and late:
            early_avg = sum(early) / len(early)
            late_avg  = sum(late)  / len(late)
            if late_avg > early_avg * 1.02:
                trend = "rising"
            elif late_avg < early_avg * 0.98:
                trend = "falling"
            else:
                trend = "flat"

    _print(f"  OI trend: {trend}  ({len(history)} hourly records)")
    return {"current": current_clean, "trend": trend, "history_count": len(history), "history": history}


# TODO: !! NEED REVIEW ATTENTION !! Since the data is calculated manually
def fetch_spot_cvd(spot_ex: ccxt.Exchange, spot_symbol: str, cvd_hours: float, cvd_tf: str) -> dict:
    since_ms = hours_ago_ms(cvd_hours)
    end_ms   = now_ms()
    window_ms = end_ms - since_ms

    _print(f"[CVD] {spot_symbol}  (last {cvd_hours}h, bucketed to {cvd_tf})")

    all_trades: list = []
    seen_ids: set = set()
    batch_count = 0
    current_since = since_ms

    while batch_count < MAX_CVD_BATCHES:
        batch = spot_ex.fetch_trades(spot_symbol, since=current_since, limit=TRADES_PER_REQ)
        if not batch:
            break

        # Deduplicate on trade id (or timestamp if id unavailable)
        for t in batch:
            key = t.get("id") or t.get("timestamp")
            if key not in seen_ids:
                seen_ids.add(key)
                all_trades.append(t)

        batch_count += 1
        last_ts = batch[-1]["timestamp"]
        elapsed_pct = min((last_ts - since_ms) / window_ms * 100, 100) if window_ms > 0 else 100
        _print(f"  Batch {batch_count:>3}: {len(batch)} trades  [{elapsed_pct:5.1f}%]")
        current_since = last_ts + 1
        if len(batch) < TRADES_PER_REQ or current_since >= end_ms:
            break
        time.sleep(spot_ex.rateLimit / 1000)

    if not all_trades:
        _print("  No trades — cannot compute CVD.")
        return {"error": "no trades returned"}

    _print(f"  Total unique trades: {len(all_trades)}")

    df = pd.DataFrame([
        {
            "timestamp_ms": t["timestamp"],
            "side":         t.get("side"),
            "amount":       t.get("amount"),
            "price":        t.get("price"),
        }
        for t in all_trades
    ])
    df["dt"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
    df.set_index("dt", inplace=True)
    df["buy_amount"]   = df["amount"].where(df["side"] == "buy",  0)
    df["sell_amount"]  = df["amount"].where(df["side"] == "sell", 0)
    df["volume_delta"] = df["buy_amount"] - df["sell_amount"]

    tf_alias_map = {
        "1m": "1min", "3m": "3min", "5m": "5min",
        "15m": "15min", "30m": "30min",
        "1h": "1h", "2h": "2h", "4h": "4h", "1d": "1D",
    }
    alias = tf_alias_map.get(cvd_tf, cvd_tf)
    candles = df.resample(alias).agg(
        open=        ("price",        "first"),
        high=        ("price",        "max"),
        low=         ("price",        "min"),
        close=       ("price",        "last"),
        buy_volume=  ("buy_amount",   "sum"),
        sell_volume= ("sell_amount",  "sum"),
        volume_delta=("volume_delta", "sum"),
        trade_count= ("amount",       "count"),
    ).dropna(subset=["open"])
    candles["cvd"] = candles["volume_delta"].cumsum()
    candles.index  = candles.index.astype(str)

    total_buy  = df[df["side"] == "buy"]["amount"].sum()
    total_sell = df[df["side"] == "sell"]["amount"].sum()
    net_delta  = total_buy - total_sell
    final_cvd  = float(candles["cvd"].iloc[-1]) if not candles.empty else 0

    direction = "positive" if net_delta > 0 else "negative"

    cvd_series = candles["cvd"].tolist()
    trend = "insufficient_data"
    if len(cvd_series) >= 4:
        quarter = len(cvd_series) // 4
        early_avg = sum(cvd_series[:quarter]) / quarter
        late_avg  = sum(cvd_series[-quarter:]) / quarter
        if late_avg > early_avg * 1.02:
            trend = "rising"
        elif late_avg < early_avg * 0.98:
            trend = "falling"
        else:
            trend = "flat"

    _print(f"  CVD direction: {direction}  final_cvd={final_cvd:.4f}  trend={trend}")

    return {
        "hours":          cvd_hours,
        "candle_tf":      cvd_tf,
        "total_trades":   len(all_trades),
        "hit_batch_cap":  batch_count >= MAX_CVD_BATCHES,
        "summary": {
            "total_buy_volume":  round(total_buy,  8),
            "total_sell_volume": round(total_sell, 8),
            "net_volume_delta":  round(net_delta,  8),
            "final_cvd":         round(final_cvd,  8),
            "direction":         direction,
            "trend":             trend,
            "interpretation": (
                "Net buying pressure (aggressive buyers dominating)" if net_delta > 0
                else "Net selling pressure (aggressive sellers dominating)"
            ),
        },
        "candles": candles.reset_index().rename(columns={"dt": "datetime"}).to_dict(orient="records"),
    }


def aggregate_spot_cvd(spot_symbol: str, cvd_hours: float, cvd_tf: str, exchanges: list[str] | None = None) -> dict:
    """Fetch spot CVD from multiple exchanges and aggregate into a single result."""
    if exchanges is None:
        exchanges = SPOT_CVD_EXCHANGES

    base = spot_symbol.split("/")[0]
    usd_symbol = f"{base}/USD"

    per_exchange: dict = {}
    candle_dfs: list   = []
    total_buy   = 0.0
    total_sell  = 0.0
    total_trades = 0

    for ex_name in exchanges:
        _print(f"\n--- [{ex_name}] ---")
        try:
            ex  = make_exchange(ex_name)
            sym = spot_symbol
            if sym not in ex.markets:
                if usd_symbol in ex.markets:
                    sym = usd_symbol
                    _print(f"  Symbol fallback: {spot_symbol} → {usd_symbol}")
                else:
                    per_exchange[ex_name] = {"error": f"symbol {spot_symbol!r} (and {usd_symbol!r}) not available"}
                    _print(f"  Skipping: symbol not available")
                    continue

            result = fetch_spot_cvd(ex, sym, cvd_hours, cvd_tf)

            if "error" in result:
                per_exchange[ex_name] = result
                continue

            per_exchange[ex_name] = {
                "symbol_used":   sym,
                "total_trades":  result["total_trades"],
                "hit_batch_cap": result["hit_batch_cap"],
                "summary":       result["summary"],
            }
            total_buy    += result["summary"]["total_buy_volume"]
            total_sell   += result["summary"]["total_sell_volume"]
            total_trades += result["total_trades"]

            # Keep only the volume_delta column per candle for merging
            candle_df = pd.DataFrame(result["candles"])
            if not candle_df.empty:
                candle_df = candle_df.set_index("datetime")[["volume_delta"]]
                candle_df.columns = [ex_name]
                candle_dfs.append(candle_df)

        except Exception as e:
            per_exchange[ex_name] = {"error": str(e)}
            _print(f"  Error ({ex_name}): {e}")

    exchanges_ok   = [ex for ex, v in per_exchange.items() if "error" not in v]
    exchanges_fail = [ex for ex, v in per_exchange.items() if "error" in v]

    if not candle_dfs:
        return {"error": "no data from any exchange", "per_exchange": per_exchange}

    # Merge all exchange candle series; outer join so every bucket is represented
    merged = pd.concat(candle_dfs, axis=1).fillna(0)
    merged["volume_delta"] = merged[exchanges_ok].sum(axis=1)
    merged["cvd"]          = merged["volume_delta"].cumsum()

    net_delta = total_buy - total_sell
    final_cvd = float(merged["cvd"].iloc[-1])
    direction = "positive" if net_delta > 0 else "negative"

    cvd_series = merged["cvd"].tolist()
    trend = "insufficient_data"
    if len(cvd_series) >= 4:
        quarter   = len(cvd_series) // 4
        early_avg = sum(cvd_series[:quarter])  / quarter
        late_avg  = sum(cvd_series[-quarter:]) / quarter
        if late_avg > early_avg * 1.02:
            trend = "rising"
        elif late_avg < early_avg * 0.98:
            trend = "falling"
        else:
            trend = "flat"

    _print(f"\n[CVD AGGREGATE] exchanges={exchanges_ok}  direction={direction}  final_cvd={final_cvd:.4f}  trend={trend}")

    agg_candles = (
        merged[["volume_delta", "cvd"]]
        .reset_index()
        .rename(columns={"index": "datetime"})
        .to_dict(orient="records")
    )

    return {
        "hours":            cvd_hours,
        "candle_tf":        cvd_tf,
        "exchanges_used":   exchanges_ok,
        "exchanges_failed": exchanges_fail,
        "total_trades":     total_trades,
        "summary": {
            "total_buy_volume":  round(total_buy,  8),
            "total_sell_volume": round(total_sell, 8),
            "net_volume_delta":  round(net_delta,  8),
            "final_cvd":         round(final_cvd,  8),
            "direction":         direction,
            "trend":             trend,
            "interpretation": (
                "Net buying pressure (aggressive buyers dominating)" if net_delta > 0
                else "Net selling pressure (aggressive sellers dominating)"
            ),
        },
        "per_exchange": per_exchange,
        "candles":      agg_candles,
    }


def fetch_funding_rates(futures_ex: ccxt.Exchange, futures_symbol: str, days: int) -> dict:
    _print(f"[FR] {futures_symbol}  (last {days} day(s))")

    current   = futures_ex.fetch_funding_rate(futures_symbol)
    rate      = current.get("fundingRate", 0) or 0
    rate_pct  = round(rate * 100, 6)
    annualized = round(rate * 3 * 365 * 100, 4)
    signal    = "longs_pay_shorts" if rate > 0 else "shorts_pay_longs"
    sentiment = "Bullish/long-heavy (longs pay shorts)" if rate > 0 else "Bearish/short-heavy (shorts pay longs)"

    current_clean = {
        "fundingRate":         rate,
        "fundingRate_pct":     rate_pct,
        "annualized_pct":      annualized,
        "signal":              signal,
        "sentiment":           sentiment,
        "markPrice":           current.get("markPrice"),
        "nextFundingDatetime": current.get("nextFundingDatetime"),
    }
    _print(f"  Current rate: {rate_pct:+.6f}%  ({annualized:+.2f}% annualised)  → {sentiment}")

    since_ms = days_ago_ms(days)
    all_fr: list = []
    batch_count = 0
    current_since = since_ms

    while True:
        batch = futures_ex.fetch_funding_rate_history(
            futures_symbol, since=current_since, limit=FUNDING_LIMIT
        )
        if not batch:
            break
        all_fr.extend(batch)
        batch_count += 1
        last_ts = batch[-1].get("timestamp", 0)
        current_since = last_ts + 1
        if len(batch) < FUNDING_LIMIT or current_since >= now_ms():
            break
        time.sleep(futures_ex.rateLimit / 1000)

    history = [
        {
            "datetime":        e.get("datetime") or ms_to_iso(e.get("timestamp", 0)),
            "timestamp_ms":    e.get("timestamp"),
            "fundingRate":     e.get("fundingRate", 0),
            "fundingRate_pct": round((e.get("fundingRate", 0) or 0) * 100, 6),
        }
        for e in all_fr
    ]

    stats: dict = {}
    rates = [h["fundingRate"] for h in history]
    if rates:
        positive = sum(1 for r in rates if r > 0)
        negative = sum(1 for r in rates if r < 0)
        stats = {
            "count":        len(rates),
            "average_pct":  round(sum(rates) / len(rates) * 100, 6),
            "max_pct":      round(max(rates) * 100, 6),
            "min_pct":      round(min(rates) * 100, 6),
            "positive_count": positive,
            "negative_count": negative,
            "dominant":     "bullish" if positive > negative else "bearish",
        }

    return {"current": current_clean, "period_stats": stats, "history": history}


def main():
    global QUIET

    parser = argparse.ArgumentParser(description="Fetch OI, Spot CVD, and Funding Rates via ccxt")
    parser.add_argument("--symbol",    required=True,  help="Symbol, e.g. BTC/USDT or BTCUSDT")
    parser.add_argument("--days",      default=2,      type=int,   help="Days of OI and funding history (default 2)")
    parser.add_argument("--cvd-hours", default=4.0,    type=float, dest="cvd_hours",
                        help="Hours of trade history for CVD (default 4)")
    parser.add_argument("--cvd-tf",    default="5m",   dest="cvd_tf",
                        help="CVD bucket timeframe: 1m 5m 15m 1h (default 5m)")
    parser.add_argument("--exchange",     default="binance", help="Futures exchange for OI + funding (default binance)")
    parser.add_argument("--cvd-exchange", default=None,     dest="cvd_exchange",
                        help="Single spot exchange for CVD (default: aggregate all — binance, okx, bybit, coinbase, bitfinex, kraken, bitstamp, cryptocom)")
    parser.add_argument("--quiet",        action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    QUIET = args.quiet

    spot_symbol, futures_symbol = normalize_symbol(args.symbol)
    tag = spot_symbol.replace("/", "-")

    _print("\n=== ccxt market metrics ===")
    _print(f"Spot      : {spot_symbol}")
    _print(f"Futures   : {futures_symbol}")
    _print(f"OI/FR days: {args.days}")
    _print(f"CVD window: {args.cvd_hours}h  tf={args.cvd_tf}")
    _print(f"CVD mode  : {'single (' + args.cvd_exchange + ')' if args.cvd_exchange else 'aggregate (' + ', '.join(SPOT_CVD_EXCHANGES) + ')'}")
    _print()

    fut_ex  = make_futures_exchange(args.exchange)

    oi      = fetch_open_interest(fut_ex,  futures_symbol, args.days)
    if args.cvd_exchange:
        spot_ex = make_exchange(args.cvd_exchange)
        cvd = fetch_spot_cvd(spot_ex, spot_symbol, args.cvd_hours, args.cvd_tf)
    else:
        cvd = aggregate_spot_cvd(spot_symbol, args.cvd_hours, args.cvd_tf)
    funding = fetch_funding_rates(fut_ex,  futures_symbol, args.days)

    result = {
        "generated_at":    datetime.now(timezone.utc).isoformat(),
        "symbol":          spot_symbol,
        "futures_symbol":  futures_symbol,
        "open_interest":   oi,
        "spot_cvd":        cvd,
        "funding_rates":   funding,
        "interpretation_guide": {
            "oi_rising":           "More contracts open → conviction / new positions entering",
            "oi_falling":          "Contracts closing → deleverage / profit-taking / capitulation",
            "cvd_positive":        "Aggressive buyers dominating → bullish pressure",
            "cvd_negative":        "Aggressive sellers dominating → bearish pressure",
            "funding_positive":    "Longs pay shorts → market is long-heavy (crowded long, potential squeeze risk)",
            "funding_negative":    "Shorts pay longs → market is short-heavy (crowded short, potential squeeze)",
            "confluence_bullish":  "Rising OI + Positive CVD + Negative funding → strong unlevered buying, room to run",
            "confluence_bearish":  "Rising OI + Negative CVD + Positive funding → heavy shorts building, watch for squeeze",
        },
    }

    out_path = DATA_DIR / f"market_metrics_{tag}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    _print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
