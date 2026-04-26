---
name: screen-coins
description: Run crypto screening pipeline — fetch from CMC or Santiment, analyze market microstructure via ccxt, analyze charts
user_invocable: true
allowed-tools: Bash(uv run *) Bash(uv add *) Bash(uv sync *) Read Write
---

# Crypto Trade Screener

Two modes: **full pipeline** (screen all coins + ccxt analysis) or **specific ticker** (analyze one coin at multiple timeframes).

---

## Mode A: Specific Ticker Analysis

Triggered when a ticker is provided, e.g. `/screen-coins BTCUSDT` or `/screen-coins ETH`.

1. **Take Coinglass screenshots at h1, h4, m15**
   Run (from `.claude/skills/screen-coins/`):
   ```
   uv run python scripts/screenshot_ticker.py --ticker {TICKER}
   ```
   Optional: `--timeframes m15,h1,h4` (default: h1,h4,m15). Output: `data/charts/{SYMBOL}_{TIMEFRAME}.png`.

2. **Analyze all three timeframes**
   Read `data/charts/{SYMBOL}_h1.png`, `data/charts/{SYMBOL}_h4.png`, `data/charts/{SYMBOL}_m15.png`.
   For each timeframe analyze:
   - **Market Structure**: uptrend / downtrend / ranging, key S/R levels
   - **Smart Money Concepts**: order blocks, fair value gaps, liquidity sweeps, ChoCh/MSS/BoS
   - **Wyckoff Theory**: accumulation/distribution phases
   - **Golden Pocket**: 0.5 & 0.618 Fibonacci retracement levels
   - **Order Flow**: absorption or convergence potential
   - **Volume profile**: increasing/decreasing, divergences
   - **On-chain Metrics**: spot/futures CVD, open interest
   - **Patterns**: triangles, flags, head & shoulders, breakouts

3. **Present focused analysis**
   Provide a multi-timeframe synthesis: HTF bias (h4) → entry zone (h1) → trigger (m15).
   Include entry zone, take-profit targets, and invalidation level.
   **Save result (override if needed) to `LLM_RESULT.md`.**

---

## Mode B: Full Pipeline Screening

Default when no ticker is specified: `/screen-coins`

Optional arg: `--source cmc|santiment|coinglass` (default: cmc).

| Source | Signal | How it works |
|---|---|---|
| `cmc` | vol/mcap ratio ≥ 0.2, top 20 | CMC API, no browser |
| `santiment` | top 24h price performers | Playwright scrape, paginated |
| `coinglass` | OI-ranked derivatives | Playwright scrape, sorts OI desc |

1. **Fetch & filter coins**
   Run (from `.claude/skills/screen-coins/`):
   ```
   uv run python scripts/screen.py --source {SOURCE}
   ```
   Show the user a summary table (symbol, price, 24h change, OI data if present).

2. **For each coin, fetch market microstructure via ccxt-market-data**
   Read `data/screening_results.json`. For each coin's symbol, run:
   ```
   uv run python ../ccxt-market-data/scripts/market_metrics.py --symbol {SYMBOL}/USDT --days 2 --cvd-hours 4
   ```
   Output: `../ccxt-market-data/data/market_metrics_{SYMBOL}-USDT.json`.
   See `../ccxt-market-data/SKILL.md` and `../ccxt-market-data/examples/market_metrics.md`
   for the interpretation guide (confluence patterns, squeeze risk, etc.).

3. **Analyze and rank**
   For each coin, read its `market_metrics_*.json` and classify:
   - OI trend (rising/falling/flat)
   - CVD direction (net buy/sell)
   - Funding crowding (crowded long / crowded short / neutral)
   - Combined bias per the confluence table in the ccxt examples
   - Setup rating: STRONG BUY / BUY / NEUTRAL / AVOID

4. **Present final results**
   Save to `LLM_RESULT.md`. Ranked table sorted by setup quality. Highlight top 3-5.
