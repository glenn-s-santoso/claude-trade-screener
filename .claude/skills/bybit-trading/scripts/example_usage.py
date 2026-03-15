import logging

from dotenv import load_dotenv

load_dotenv()

from trading_setup import TradingSetup

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    ts = TradingSetup(testnet=True)

    result = ts.setup_and_trade(
        symbol="BTCUSDT",
        side="Buy",
        entry_price="60000",
        take_profit="63000",
        tp_limit_price="62950",
        stop_loss="58000",
        # qty omitted — auto-calculated from RISK_PER_TRADE env var
    )

    print(result)
