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
