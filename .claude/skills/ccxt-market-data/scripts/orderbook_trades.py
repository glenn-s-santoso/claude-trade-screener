#!/usr/bin/env python3
"""
Fetch real-time order book depth and recent trades via ccxt (no API keys required).

Usage:
    python scripts/orderbook_trades.py --symbol BTC/USDT
    python scripts/orderbook_trades.py --symbol BTCUSDT --depth 20 --trades 100
    python scripts/orderbook_trades.py --symbol ETH/USDT --exchange bybit
    python scripts/orderbook_trades.py --symbol BTC/USDT --quiet

Output: data/orderbook_trades_{SYMBOL}.json
"""

import argparse
import json
from datetime import datetime, timezone

import ccxt

from utils import DATA_DIR, make_exchange, ms_to_iso, normalize_symbol

QUIET = False


def _print(*args, **kwargs):
    if not QUIET:
        print(*args, **kwargs)


def fetch_order_book(exchange: ccxt.Exchange, symbol: str, depth: int) -> dict:
    _print(f"[OB] {symbol}  (depth={depth})")

    book = exchange.fetch_order_book(symbol, limit=depth)

    bids = [{"price": b[0], "amount": b[1]} for b in book["bids"][:depth]]
    asks = [{"price": a[0], "amount": a[1]} for a in book["asks"][:depth]]

    spread = None
    if bids and asks:
        spread = round(asks[0]["price"] - bids[0]["price"], 8)

    bid_total_vol = round(sum(b["amount"] for b in bids), 8)
    ask_total_vol = round(sum(a["amount"] for a in asks), 8)

    total_vol = bid_total_vol + ask_total_vol
    imbalance_ratio = None
    imbalance_side = "neutral"
    if total_vol > 0:
        imbalance_ratio = round(bid_total_vol / total_vol, 4)
        if imbalance_ratio > 0.55:
            imbalance_side = "bid"   # more bid volume → buy wall / bullish depth
        elif imbalance_ratio < 0.45:
            imbalance_side = "ask"   # more ask volume → sell wall / bearish depth

    if bids and asks:
        _print(f"  Best bid : {bids[0]['price']}  qty={bids[0]['amount']}")
        _print(f"  Best ask : {asks[0]['price']}  qty={asks[0]['amount']}")
    _print(f"  Spread   : {spread}")
    _print(f"  Imbalance: {imbalance_side}  "
           f"(bid_vol={bid_total_vol} / ask_vol={ask_total_vol}  ratio={imbalance_ratio})")

    ts = book.get("timestamp") or int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        "timestamp":      ms_to_iso(ts),
        "depth":          depth,
        "best_bid":       bids[0]["price"] if bids else None,
        "best_ask":       asks[0]["price"] if asks else None,
        "spread":         spread,
        "bid_total_vol":  bid_total_vol,
        "ask_total_vol":  ask_total_vol,
        "imbalance_ratio": imbalance_ratio,
        "imbalance_side": imbalance_side,
        "bids":           bids,
        "asks":           asks,
    }


def fetch_recent_trades(exchange: ccxt.Exchange, symbol: str, n_trades: int) -> dict:
    _print(f"[RT] {symbol}  (last {n_trades} trades)")

    raw = exchange.fetch_trades(symbol, limit=n_trades)

    trades = [
        {
            "id":       t.get("id"),
            "datetime": t.get("datetime"),
            "side":     t.get("side"),
            "price":    t.get("price"),
            "amount":   t.get("amount"),
            "cost":     t.get("cost"),
        }
        for t in raw
    ]

    buy_trades  = [t for t in trades if t["side"] == "buy"]
    sell_trades = [t for t in trades if t["side"] == "sell"]
    buy_vol  = round(sum(t["amount"] for t in buy_trades  if t["amount"]), 8)
    sell_vol = round(sum(t["amount"] for t in sell_trades if t["amount"]), 8)

    dominant_side = "neutral"
    if buy_vol + sell_vol > 0:
        buy_ratio = buy_vol / (buy_vol + sell_vol)
        if buy_ratio > 0.55:
            dominant_side = "buy"
        elif buy_ratio < 0.45:
            dominant_side = "sell"

    if trades:
        latest = trades[-1]
        side_str = (latest["side"] or "unknown").upper()
        _print(f"  Latest   : {side_str}  {latest['amount']} @ {latest['price']}")
    _print(f"  Buy/Sell : {len(buy_trades)}/{len(sell_trades)} trades  "
           f"vol={buy_vol}/{sell_vol}  dominant={dominant_side}")

    return {
        "count": len(trades),
        "summary": {
            "buy_count":    len(buy_trades),
            "sell_count":   len(sell_trades),
            "buy_volume":   buy_vol,
            "sell_volume":  sell_vol,
            "dominant_side": dominant_side,
            "interpretation": (
                "Aggressive buyers dominating tape" if dominant_side == "buy"
                else "Aggressive sellers dominating tape" if dominant_side == "sell"
                else "Balanced tape — no clear aggressor"
            ),
        },
        "trades": trades,
    }


def build_combined_signal(ob_side: str, tape_side: str) -> str:
    """Produce a combined interpretation covering all combinations of ob_side and tape_side."""
    if ob_side == "bid" and tape_side == "buy":
        return "Bullish: bid-heavy book + buy-dominant tape → buying pressure on both depth and tape"
    if ob_side == "ask" and tape_side == "sell":
        return "Bearish: ask-heavy book + sell-dominant tape → selling pressure on both depth and tape"
    if ob_side == "bid" and tape_side == "sell":
        return "Mixed: bid wall present but tape is sell-dominated → bids being actively tested"
    if ob_side == "ask" and tape_side == "buy":
        return "Mixed: ask wall present but tape is buy-dominated → asks being actively tested"
    if ob_side == "bid" and tape_side == "neutral":
        return "Leaning bullish: bid-heavy book but tape shows no clear aggressor"
    if ob_side == "ask" and tape_side == "neutral":
        return "Leaning bearish: ask-heavy book but tape shows no clear aggressor"
    if ob_side == "neutral" and tape_side == "buy":
        return "Leaning bullish: buy-dominant tape but book depth is balanced"
    if ob_side == "neutral" and tape_side == "sell":
        return "Leaning bearish: sell-dominant tape but book depth is balanced"
    return "Neutral: no strong directional signal from book or tape"


def main():
    global QUIET

    parser = argparse.ArgumentParser(description="Fetch order book and recent trades via ccxt")
    parser.add_argument("--symbol",   required=True,  help="Symbol, e.g. BTC/USDT or BTCUSDT")
    parser.add_argument("--depth",    default=10,     type=int, help="Order book levels to fetch (default 10)")
    parser.add_argument("--trades",   default=50,     type=int, help="Recent trades to fetch (default 50)")
    parser.add_argument("--exchange", default="binance", help="Exchange (default binance)")
    parser.add_argument("--quiet",    action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    QUIET = args.quiet

    spot_symbol, _ = normalize_symbol(args.symbol)
    tag = spot_symbol.replace("/", "-")

    _print("\n=== ccxt order book + recent trades ===")
    _print(f"Symbol  : {spot_symbol}")
    _print(f"Depth   : {args.depth} levels")
    _print(f"Trades  : {args.trades}")
    _print(f"Exchange: {args.exchange}")
    _print()

    exchange = make_exchange(args.exchange)

    order_book    = fetch_order_book(exchange,    spot_symbol, args.depth)
    recent_trades = fetch_recent_trades(exchange, spot_symbol, args.trades)

    combined = build_combined_signal(
        order_book["imbalance_side"],
        recent_trades["summary"]["dominant_side"],
    )

    result = {
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "symbol":        spot_symbol,
        "exchange":      args.exchange,
        "order_book":    order_book,
        "recent_trades": recent_trades,
        "combined_signal": combined,
    }

    out_path = DATA_DIR / f"orderbook_trades_{tag}.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    _print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
