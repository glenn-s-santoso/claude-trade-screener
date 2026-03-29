#!/usr/bin/env python3
"""Cancel open orders and/or market-exit open positions on Bybit V5."""

import argparse
import json
import logging

from pybit.unified_trading import HTTP

from session import get_session

logger = logging.getLogger(__name__)


def cancel_orders(session: HTTP, symbols: list[str] | None) -> list[dict]:
    """Cancel open orders. If symbols is None/empty, cancels all USDT-settled orders."""
    results = []
    if symbols:
        for sym in symbols:
            resp = session.cancel_all_orders(category="linear", symbol=sym.upper())
            results.append({"symbol": sym.upper(), "result": resp["result"]})
            logger.info("Cancelled orders for %s: %s", sym, resp)
    else:
        resp = session.cancel_all_orders(category="linear", settleCoin="USDT")
        results.append({"symbol": "ALL", "result": resp["result"]})
        logger.info("Cancelled all orders: %s", resp)
    return results


def market_exit_positions(session: HTTP, symbols: list[str] | None) -> list[dict]:
    """Market-close open positions. If symbols is None/empty, closes all."""
    kwargs = {"category": "linear", "settleCoin": "USDT"}
    if symbols:
        # Fetch per-symbol to keep it simple; Bybit doesn't support multi-symbol in one call
        positions = []
        for sym in symbols:
            resp = session.get_positions(category="linear", symbol=sym.upper())
            positions.extend(resp["result"]["list"])
    else:
        resp = session.get_positions(**kwargs)
        positions = resp["result"]["list"]

    open_positions = [p for p in positions if float(p.get("size", "0")) > 0]

    if not open_positions:
        logger.info("No open positions to exit.")
        return []

    results = []
    for pos in open_positions:
        sym = pos["symbol"]
        size = pos["size"]
        # Opposite side to close
        close_side = "Sell" if pos["side"] == "Buy" else "Buy"
        try:
            resp = session.place_order(
                category="linear",
                symbol=sym,
                side=close_side,
                orderType="Market",
                qty=size,
                timeInForce="IOC",
                positionIdx=0,
                reduceOnly=True,
            )
            results.append({"symbol": sym, "side": close_side, "qty": size, "result": resp["result"]})
            logger.info("Market exit %s %s qty=%s: %s", sym, close_side, size, resp)
        except Exception as e:
            logger.error("Failed to exit %s %s qty=%s: %s", sym, close_side, size, e)
            results.append({"symbol": sym, "side": close_side, "qty": size, "error": str(e)})

    return results


def main():
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(
        description="Cancel open orders and/or market-exit positions on Bybit V5"
    )
    parser.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated symbols, e.g. BTCUSDT,ETHUSDT. Omit to target all.",
    )
    parser.add_argument("--cancel", action="store_true", help="Cancel all open (unfilled) orders")
    parser.add_argument("--exit", action="store_true", dest="exit_pos", help="Market-exit open positions")
    parser.add_argument("--testnet", action="store_true", default=False)
    parser.add_argument("--json", action="store_true", default=False, help="Output raw JSON")
    args = parser.parse_args()

    if not args.cancel and not args.exit_pos:
        parser.error("Specify at least one of --cancel or --exit")

    symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else None
    session = get_session(testnet=args.testnet)

    output = {}

    if args.cancel:
        output["cancelled_orders"] = cancel_orders(session, symbols)

    if args.exit_pos:
        output["exited_positions"] = market_exit_positions(session, symbols)

    if args.json:
        print(json.dumps(output, indent=2))
        return

    label = f" ({args.symbols})" if args.symbols else " (ALL)"

    if "cancelled_orders" in output:
        print(f"\n=== Cancelled Orders{label} ===")
        for r in output["cancelled_orders"]:
            success = r["result"].get("success", r["result"])
            print(f"  {r['symbol']}: {success}")

    if "exited_positions" in output:
        print(f"\n=== Market Exits{label} ===")
        if output["exited_positions"]:
            for r in output["exited_positions"]:
                if "error" in r:
                    print(f"  {r['symbol']} {r['side']} qty={r['qty']} → ERROR: {r['error']}")
                else:
                    print(f"  {r['symbol']} {r['side']} qty={r['qty']} → orderId={r['result'].get('orderId', 'N/A')}")
        else:
            print("  (no open positions)")

    print()


if __name__ == "__main__":
    main()
