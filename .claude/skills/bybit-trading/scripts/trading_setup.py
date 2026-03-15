import logging
import math
import os
import argparse
import json
from dotenv import load_dotenv
from pybit.exceptions import InvalidRequestError
from pybit.unified_trading import HTTP

load_dotenv()

logger = logging.getLogger(__name__)


class TradingSetup:
    def __init__(self, testnet: bool = False):
        api_key = os.environ["BYBIT_API_KEY"]
        api_secret = os.environ["BYBIT_API_SECRET"]
        self._risk_per_trade = float(os.environ.get("RISK_PER_TRADE", "100"))
        self._session = HTTP(testnet=testnet, api_key=api_key, api_secret=api_secret)
        logger.info("TradingSetup initialized (testnet=%s)", testnet)

    def get_max_leverage(self, symbol: str) -> str:
        try:
            resp = self._session.get_instruments_info(category="linear", symbol=symbol)
            max_lev = resp["result"]["list"][0]["leverageFilter"]["maxLeverage"]
            logger.info("Max leverage for %s: %s", symbol, max_lev)
            return max_lev
        except Exception:
            logger.exception("Failed to get max leverage for %s", symbol)
            raise

    def set_leverage(self, symbol: str, leverage: str = None) -> dict:
        try:
            if leverage is None:
                leverage = self.get_max_leverage(symbol)
            resp = self._session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=leverage,
                sellLeverage=leverage,
            )
            logger.info("Leverage set for %s to %s: %s", symbol, leverage, resp)
            return resp
        except InvalidRequestError as e:
            if e.status_code == 110043:
                logger.info("Leverage for %s already at %s (110043), skipping", symbol, leverage)
                return {}
            logger.exception("Failed to set leverage for %s", symbol)
            raise
        except Exception:
            logger.exception("Failed to set leverage for %s", symbol)
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        qty: str,
        entry_price: str,
        take_profit: str,
        tp_limit_price: str,
        stop_loss: str,
    ) -> dict:
        try:
            resp = self._session.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Limit",
                qty=qty,
                price=entry_price,
                timeInForce="GTC",
                positionIdx=0,
                tpslMode="Partial",
                takeProfit=take_profit,
                tpLimitPrice=tp_limit_price,
                tpOrderType="Limit",
                stopLoss=stop_loss,
                slOrderType="Market",
            )
            logger.info("Order placed for %s: %s", symbol, resp)
            return resp
        except Exception:
            logger.exception("Failed to place order for %s", symbol)
            raise

    def calculate_qty(self, symbol: str, entry_price: str, stop_loss: str) -> str:
        try:
            risk_per_unit = abs(float(entry_price) - float(stop_loss))
            raw_qty = self._risk_per_trade / risk_per_unit

            resp = self._session.get_instruments_info(category="linear", symbol=symbol)
            qty_step = float(
                resp["result"]["list"][0]["lotSizeFilter"]["qtyStep"]
            )

            # Round down to nearest qty_step
            step_decimals = len(str(qty_step).rstrip("0").split(".")[-1]) if "." in str(qty_step) else 0
            qty = math.floor(raw_qty / qty_step) * qty_step
            qty_str = f"{qty:.{step_decimals}f}"

            logger.info(
                "Calculated qty for %s: %s (risk=$%.2f, risk_per_unit=%s, step=%s)",
                symbol,
                qty_str,
                self._risk_per_trade,
                risk_per_unit,
                qty_step,
            )
            return qty_str
        except Exception:
            logger.exception("Failed to calculate qty for %s", symbol)
            raise

    def setup_and_trade(
        self,
        symbol: str,
        side: str,
        entry_price: str,
        take_profit: str,
        tp_limit_price: str,
        stop_loss: str,
        qty: str = None,
    ) -> dict:
        try:
            if qty is None:
                qty = self.calculate_qty(symbol, entry_price, stop_loss)

            max_lev = self.get_max_leverage(symbol)
            logger.info("Using max leverage %s for %s", max_lev, symbol)
            self.set_leverage(symbol, max_lev)

            return self.place_limit_order(
                symbol=symbol,
                side=side,
                qty=qty,
                entry_price=entry_price,
                take_profit=take_profit,
                tp_limit_price=tp_limit_price,
                stop_loss=stop_loss,
            )
        except Exception:
            logger.exception("setup_and_trade failed for %s", symbol)
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

    parser = argparse.ArgumentParser(description="Place a Bybit limit order with max leverage, Limit TP, and Market SL")
    parser.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["Buy", "Sell"])
    parser.add_argument("--entry-price", required=True, dest="entry_price", help="Limit entry price")
    parser.add_argument("--take-profit", required=True, dest="take_profit", help="TP trigger price")
    parser.add_argument("--tp-limit-price", required=True, dest="tp_limit_price", help="TP limit fill price")
    parser.add_argument("--stop-loss", required=True, dest="stop_loss", help="SL trigger price")
    parser.add_argument("--qty", default=None, help="Order qty (auto-calculated from RISK_PER_TRADE if omitted)")
    parser.add_argument("--testnet", action="store_true", default=False, help="Use Bybit testnet")
    args = parser.parse_args()

    symbol: str = args.symbol.upper()
    side: str = args.side.capitalize()
    entry_price: str = args.entry_price
    take_profit: str = args.take_profit
    tp_limit_price: str = args.tp_limit_price
    stop_loss: str = args.stop_loss
    qty: str | None = args.qty

    ts = TradingSetup(testnet=args.testnet)
    result = ts.setup_and_trade(
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        take_profit=take_profit,
        tp_limit_price=tp_limit_price,
        stop_loss=stop_loss,
        qty=qty,
    )
    print(json.dumps(result, indent=2))
