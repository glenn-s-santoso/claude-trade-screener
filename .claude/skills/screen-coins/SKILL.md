---
name: screen-coins
description: Run crypto screening pipeline — fetch from CMC, screenshot charts, analyze setups
user_invocable: true
---

# Crypto Trade Screener

Run the full screening pipeline and analyze charts for trade setups.

## Steps

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
      - **Smart Money Concepts**: watch for order blocks, fair value gaps, buyside liquidity, sellside liquidity, ChoCh/MSS, BoS
      - **Wyckoff Theory**: Look for some accumulation/distribution phases
      - **Golden Cross**: Look for golden cross patterns
      - **Golden Pocket**: Look for 0.5 & 0.618 fibonacci retracement levels
      - **Order Flow**: Look for absorption potential or convergence potential
   - **Trend**: uptrend / downtrend / sideways
   - **Volume profile**: increasing/decreasing, any divergences
   - **Patterns**: triangles, flags, head & shoulders, breakouts, etc.
   - **On-chain Metrics**: watch for spot and futures CVD, open interest
   - **Setup rating**: STRONG BUY / BUY / NEUTRAL / AVOID

4. **Present final results**
   **Save your result (override if needed) tp `LLM_RESULT.md`.**
   Show a ranked table of all analyzed coins sorted by setup quality.
   Highlight the top 3-5 actionable setups with brief reasoning for each.
   Include entry zones and invalidation levels where visible on the chart.
