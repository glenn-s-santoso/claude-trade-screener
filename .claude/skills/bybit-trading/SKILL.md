---
name: bybit-trading
description: Set max leverage and place a Limit order with Partial TP (Limit) + SL (Market) on Bybit V5
user_invocable: true
model: haiku
---

# Bybit Trading Skill

Automates the Bybit V5 trading setup flow: configure leverage to max, then place a Limit entry order with Partial tpslMode, Limit TP, and Market SL.

## What It Does

1. Fetches the instrument's max leverage via `GET /v5/market/instruments-info`
2. Sets buy and sell leverage to max via `POST /v5/position/set-leverage`
3. Places a Limit order with:
   - `tpslMode = "Partial"` (required for Limit TP even at 100% qty)
   - `tpOrderType = "Limit"` with a separate `tpLimitPrice`
   - `slOrderType = "Market"`
   - `positionIdx = 0` (one-way mode)

## Required Inputs

| Parameter      | Type   | Description                                      |
|----------------|--------|--------------------------------------------------|
| `symbol`       | str    | e.g. `"BTCUSDT"`                                 |
| `side`         | str    | `"Buy"` or `"Sell"`                              |
| `entry_price`  | str    | Limit entry price                                |
| `take_profit`  | str    | TP trigger price                                 |
| `tp_limit_price` | str  | TP limit fill price                              |
| `stop_loss`    | str    | SL trigger price                                 |
| `qty`          | str    | Optional — auto-calculated from `RISK_PER_TRADE` if omitted |

## Expected Output

Returns the full Bybit API response dict, e.g.:
```json
{
  "retCode": 0,
  "retMsg": "OK",
  "result": {
    "orderId": "...",
    "orderLinkId": "..."
  }
}
```

## Account Assumptions

- UTA (Unified Trading Account)
- Cross margin (set at account level, not per-order)
- One-way mode (`positionIdx: 0`)

## Caveats

- Error `110043` ("leverage not modified") from `set-leverage` is non-fatal and is swallowed silently
- Set `testnet=True` when instantiating `TradingSetup` to use the testnet endpoint
- `RISK_PER_TRADE` env var is the USD amount to risk per trade (used for auto qty calculation)

## Usage

Run from `.claude/skills/bybit-trading/` with `uv run`:

```bash
uv run python scripts/trading_setup.py \
  --symbol BTCUSDT \
  --side Buy \
  --entry-price 60000 \
  --take-profit 63000 \
  --tp-limit-price 62950 \
  --stop-loss 58000
  # --qty 0.001        omit to auto-calculate from RISK_PER_TRADE
  # --testnet          add flag for testnet
```

All arguments except `--qty` are required. Add `--testnet` to hit the testnet endpoint.

When invoked as a skill (e.g. `/bybit-trading BTCUSDT Buy 60000 TP=63000 TPLimit=62950 SL=58000`), parse the user's arguments and run the command above from `.claude/skills/bybit-trading/`.

If the user attaches a chart image instead of providing explicit values, extract the parameters visually from the chart, show a confirmation summary, and only proceed after the user confirms.

---

## Position & Order Status

Check open positions and orders with `/bybit-trading status` or `/bybit-trading status BTCUSDT`.

Run (from `.claude/skills/bybit-trading/`):

```bash
uv run python scripts/position_status.py              # all positions & orders
uv run python scripts/position_status.py --symbol BTCUSDT   # filtered by symbol
uv run python scripts/position_status.py --json       # raw JSON output
uv run python scripts/position_status.py --testnet    # use testnet
```

Output shows per-position: symbol, side, size, avg entry, mark price, unrealised PnL, leverage, liquidation price, TP/SL.
Output shows per-order: symbol, side, type, qty, price, TP/SL, status, order ID.

---

## Cancel Orders & Market Exit

Cancel unfilled orders and/or market-close open positions via `/bybit-trading cancel` or `/bybit-trading exit`.

If no symbols are specified, the action applies to **all** open orders/positions.
Use comma-separated symbols to target specific ones.

Run (from `.claude/skills/bybit-trading/`):

```bash
# Cancel all open orders (all symbols)
uv run python scripts/cancel_exit.py --cancel

# Cancel open orders for specific symbols
uv run python scripts/cancel_exit.py --cancel --symbols BTCUSDT,ETHUSDT

# Market-exit all open positions
uv run python scripts/cancel_exit.py --exit

# Market-exit specific positions
uv run python scripts/cancel_exit.py --exit --symbols BTCUSDT

# Cancel orders AND exit positions in one go
uv run python scripts/cancel_exit.py --cancel --exit --symbols BTCUSDT,ETHUSDT

# Raw JSON output
uv run python scripts/cancel_exit.py --cancel --exit --json

# Testnet
uv run python scripts/cancel_exit.py --cancel --exit --testnet
```

When invoked as a skill (e.g. `/bybit-trading cancel BTCUSDT,ETHUSDT` or `/bybit-trading exit`), parse the user's intent and run the appropriate command above from `.claude/skills/bybit-trading/`.
