#!/usr/bin/env python3
"""Fetch and display open positions and orders from Bybit V5."""

import argparse
import json
import logging

from session import get_session

from pybit.unified_trading import HTTP

logger = logging.getLogger(__name__)


def get_positions(session: HTTP, symbol: str = None) -> list:
    kwargs = {"category": "linear", "settleCoin": "USDT"}
    if symbol:
        kwargs["symbol"] = symbol.upper()
    resp = session.get_positions(**kwargs)
    positions = resp["result"]["list"]
    return [p for p in positions if float(p.get("size", "0")) > 0]


def get_open_orders(session: HTTP, symbol: str = None) -> list:
    kwargs = {"category": "linear", "settleCoin": "USDT", "openOnly": 0}
    if symbol:
        kwargs["symbol"] = symbol.upper()
    resp = session.get_open_orders(**kwargs)
    return resp["result"]["list"]


def format_position(p: dict) -> str:
    side = p.get("side", "N/A")
    symbol = p.get("symbol", "N/A")
    size = p.get("size", "0")
    entry = p.get("avgPrice", "N/A")
    mark = p.get("markPrice", "N/A")
    pnl = p.get("unrealisedPnl", "N/A")
    lev = p.get("leverage", "N/A")
    liq = p.get("liqPrice", "N/A")
    tp = p.get("takeProfit", "") or "—"
    sl = p.get("stopLoss", "") or "—"
    return (
        f"  {symbol} {side} | size={size} | entry={entry} | mark={mark} | "
        f"uPnL={pnl} | lev={lev}x | liq={liq} | TP={tp} | SL={sl}"
    )


def format_order(o: dict) -> str:
    side = o.get("side", "N/A")
    symbol = o.get("symbol", "N/A")
    qty = o.get("qty", "N/A")
    price = o.get("price", "N/A")
    order_type = o.get("orderType", "N/A")
    status = o.get("orderStatus", "N/A")
    order_id = o.get("orderId", "N/A")[:12]
    tp = o.get("takeProfit", "") or "—"
    sl = o.get("stopLoss", "") or "—"
    return (
        f"  {symbol} {side} {order_type} | qty={qty} | price={price} | "
        f"TP={tp} | SL={sl} | status={status} | id={order_id}..."
    )

def normalize_symbol(symbol: str | None) -> str | None:
    """Normalize symbol to uppercase and ensure USDT suffix."""
    if not symbol:
        return None
    symbol = symbol.upper()
    return symbol if symbol.endswith("USDT") else f"{symbol}USDT"

def main():
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(description="Fetch open positions and orders from Bybit V5")
    parser.add_argument("--symbol", default=None, help="Filter by symbol, e.g. BTCUSDT")
    parser.add_argument("--testnet", action="store_true", default=False)
    parser.add_argument("--json", action="store_true", default=False, help="Output raw JSON")
    args = parser.parse_args()

    session = get_session(testnet=args.testnet)
    
    symbol = normalize_symbol(args.symbol)

    positions = get_positions(session, symbol)
    orders = get_open_orders(session, symbol)

    if args.json:
        print(json.dumps({"positions": positions, "orders": orders}, indent=2))
        return

    label = f" ({symbol.upper()})" if symbol else ""

    print(f"\n=== Open Positions{label} ({len(positions)}) ===")
    if positions:
        for p in positions:
            print(format_position(p))
    else:
        print("  (none)")

    print(f"\n=== Open Orders{label} ({len(orders)}) ===")
    if orders:
        for o in orders:
            print(format_order(o))
    else:
        print("  (none)")

    print()


if __name__ == "__main__":
    main()
