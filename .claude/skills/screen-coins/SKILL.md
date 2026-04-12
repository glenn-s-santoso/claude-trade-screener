---
name: screen-coins
description: Run crypto screening pipeline — fetch from CMC, screenshot charts, analyze setups
user_invocable: true
allowed-tools: Bash(uv run *) Bash(uv add *) Bash(uv sync *) Read Write
---

# Crypto Trade Screener

Two modes: **full pipeline** (screen all CMC coins) or **specific ticker** (analyze one coin at multiple timeframes).

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

1. **Fetch & filter coins from CoinMarketCap**
   Run (from `.claude/skills/screen-coins/`): `uv run python scripts/screen_cmc.py`
   Show the user a summary table of the filtered coins (symbol, price, vol/mcap ratio, 24h change).

2. **Take Coinglass 4H chart screenshots**
   Run (from `.claude/skills/screen-coins/`): `uv run python scripts/screenshot_coinglass.py`
   Report how many screenshots succeeded.

3. **Analyze each chart**
   Read `data/screening_results.json` to get the coin list.
   For each coin, read the screenshot at `data/charts/{SYMBOL}.png` and analyze:
   - **Market Structure**: uptrend / downtrend / ranging
   - **Key levels**: support and resistance zones visible on chart
   - **Smart Money Concepts**: order blocks, fair value gaps, buyside/sellside liquidity, ChoCh/MSS, BoS
   - **Wyckoff Theory**: accumulation/distribution phases
   - **Golden Cross**: golden cross patterns
   - **Golden Pocket**: 0.5 & 0.618 fibonacci retracement levels
   - **Order Flow**: absorption or convergence potential
   - **Trend**: uptrend / downtrend / sideways
   - **Volume profile**: increasing/decreasing, divergences
   - **Patterns**: triangles, flags, head & shoulders, breakouts, etc.
   - **On-chain Metrics**: spot and futures CVD, open interest
   - **Setup rating**: STRONG BUY / BUY / NEUTRAL / AVOID

4. **Present final results**
   **Save your result (override if needed) to `LLM_RESULT.md`.**
   Show a ranked table of all analyzed coins sorted by setup quality.
   Highlight the top 3-5 actionable setups with brief reasoning for each.
   Include entry zones and invalidation levels where visible on the chart.
