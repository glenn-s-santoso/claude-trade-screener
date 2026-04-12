---
name: ccxt-market-data
description: Fetch market microstructure data (Open Interest, Spot CVD, Funding Rates, OHLCV, Order Book, Recent Trades) via ccxt — no API keys required
user_invocable: true
model: haiku
---

# CCXT Market Data Skill

Fetches numerical market microstructure metrics for any crypto pair via public ccxt endpoints (no API keys). Complements chart screenshots with actual OI, CVD, and funding data.

## What It Does

Three modes:

### Mode A — Market Metrics (primary)

Fetches three signals that reveal market positioning:
1. **Open Interest** — total outstanding futures contracts (rising = new conviction, falling = deleverage)
2. **Spot CVD** — Cumulative Volume Delta derived from raw trades (positive = net buying, negative = net selling)
3. **Funding Rates** — current rate + history (positive = longs pay shorts = crowded long; negative = shorts pay longs = crowded short)

### Mode B — OHLCV

Fetches historical candles with full pagination (handles any timeframe, any window).

### Mode C — Order Book + Recent Trades

Real-time market depth snapshot and tape analysis:
- **Order book**: top N bid/ask levels, spread, bid vs ask volume imbalance
- **Recent trades**: last N trades with side (buy/sell), volume ratio, dominant aggressor

---

## Usage

### Mode A — Market Metrics

Invoked as `/ccxt-market-data BTCUSDT` or `/ccxt-market-data BTC/USDT`

Run from `.claude/skills/ccxt-market-data/`:
```bash
uv run python scripts/market_metrics.py \
  --symbol BTC/USDT \
  [--days 2] \        # OI and funding history window (default: 2)
  [--cvd-hours 4] \   # CVD trade window in hours (default: 4)
  [--cvd-tf 5m] \     # CVD bucket size: 1m 5m 15m 1h (default: 5m)
  [--exchange binance] # default: binance
```

Output: `data/market_metrics_BTC-USDT.json`

After running, read the output file and provide a **market microstructure summary**:
- OI trend (rising / falling / flat) and what it signals
- CVD direction (net buying / net selling pressure)
- Funding rate and crowding direction
- **Combined bias**: whether OI + CVD + funding are in confluence or diverging
- One-line trading implication (e.g., "Bullish: rising OI + positive CVD + negative funding = unlevered buying with room to run")

### Mode B — OHLCV

Invoked as `/ccxt-market-data BTCUSDT ohlcv 1h 7d` or `/ccxt-market-data BTC/USDT ohlcv 5m 1d`

Run from `.claude/skills/ccxt-market-data/`:
```bash
uv run python scripts/ohlcv_fetch.py \
  --symbol BTC/USDT \
  --timeframe 1h \
  --days 7 \
  [--exchange binance]
```

Output: `data/ohlcv_BTC-USDT_1h_7d.json`

After running, report: candle count, date range, and a brief OHLCV summary (price range, recent close, volume trend if notable).

### Mode C — Order Book + Recent Trades

Invoked as `/ccxt-market-data BTCUSDT depth` or `/ccxt-market-data BTC/USDT orderbook`

Run from `.claude/skills/ccxt-market-data/`:
```bash
uv run python scripts/orderbook_trades.py \
  --symbol BTC/USDT \
  [--depth 10]         # order book levels (default: 10)
  [--trades 50]        # recent trades to fetch (default: 50)
  [--exchange binance]
```

Output: `data/orderbook_trades_BTC-USDT.json`

After running, read the output and report:
- Best bid/ask prices and spread (tight = liquid, wide = volatile/illiquid)
- Book imbalance: bid vs ask volume in top N levels (`imbalance_side` + `imbalance_ratio`)
- Tape summary: buy vs sell count/volume, `dominant_side`
- `combined_signal` from the file (pre-computed confluence interpretation)

---

## Symbol Normalization

Both scripts accept any common format:
- `BTCUSDT` → normalized to `BTC/USDT` (spot) and `BTC/USDT:USDT` (futures)
- `BTC/USDT` → used as-is
- `ETH` → normalized to `ETH/USDT`

---

## CVD Interpretation Guide

| Signal | Meaning |
|---|---|
| Rising OI + Positive CVD + Negative funding | Strong unlevered buying; room to run upward |
| Rising OI + Negative CVD + Positive funding | Shorts building aggressively; watch for squeeze |
| Falling OI + Any CVD | Deleverage event; read price action for direction |
| High positive funding | Crowded long; long squeeze risk |
| High negative funding | Crowded short; short squeeze risk |

---

## Notes

- No API keys required — all public endpoints
- Default exchange: Binance (most reliable, highest data availability)
- CVD has a batch cap of 100k trades to avoid rate limiting on high-volume pairs
- Futures data (OI, funding) uses `binanceusdm`; spot data (CVD) uses `binance`

---

## Additional Resources

For detailed use cases and examples, see:

- **Market Metrics**: [examples/market_metrics.md](examples/market_metrics.md) — 12 use cases for OI, CVD, and funding analysis
- **OHLCV Fetch**: [examples/ohlcv_fetch.md](examples/ohlcv_fetch.md) — 10 use cases for candlestick analysis
- **Order Book + Trades**: [examples/orderbook_traders.md](examples/orderbook_traders.md) — 8 use cases for liquidity and tape reading
