# Crypto Trade Screener

Hybrid crypto screening tool: Python scripts handle data fetching/filtering/screenshots (free), Claude analyzes charts and picks setups (where intelligence is needed).

## Setup

```bash
uv sync
uv run playwright install chromium
cp .env.example .env  # Add your CMC_API_KEY
```

## Usage

Run the full pipeline via the Claude skill:
```
/screen-coins
```

Or run scripts individually:
```bash
uv run python scripts/screen.py                        # Fetch & filter top coins (default: CMC)
uv run python scripts/screen.py --source santiment     # Fetch from Santiment top performers
uv run python scripts/screenshot_ticker.py --ticker BTCUSDT  # Screenshot specific ticker (h1, h4, m15)
```

Analyze a specific ticker across timeframes:
```
/screen-coins BTCUSDT
```

After analyzing the charts, save the result to `LLM_RESULT.md`.

## Structure

- `.claude/skills/screen-coins/scripts/screen.py` — Unified CLI: `--source cmc|santiment` → filter → JSON
- `.claude/skills/screen-coins/scripts/sources/cmc.py` — CoinMarketCap API → filter by volume/market_cap ratio ≥ 0.2 → top 20
- `.claude/skills/screen-coins/scripts/sources/santiment.py` — Playwright scraper for Santiment top price performers
- `.claude/skills/screen-coins/scripts/sources/coinglass.py` — Playwright scraper for Coinglass derivatives table sorted by OI descending
- `.claude/skills/screen-coins/scripts/screenshot_ticker.py` — Playwright screenshots for a specific ticker at h1, h4, m15 timeframes
- `.claude/skills/screen-coins/SKILL.md` — Claude skill (two modes: full pipeline or specific ticker)
- `.claude/skills/screen-coins/data/` — Runtime output (gitignored): `screening_results.json` and `charts/*.png`
- `LLM_RESULT.md` — Analysis results from Claude (gitignored)

- `.claude/skills/bybit-trading/scripts/trading_setup.py` — Sets max leverage + places Limit order with Partial TP (Limit) + Market SL via Bybit V5 API
- `.claude/skills/bybit-trading/scripts/position_status.py` — Fetches open positions and orders from Bybit V5
- `.claude/skills/bybit-trading/scripts/cancel_exit.py` — Cancels open orders and/or market-exits positions via Bybit V5
- `.claude/skills/bybit-trading/SKILL.md` — Claude skill; invocable with explicit args or from a chart image; also handles `/bybit-trading status`

## Notes

- User trades on **Bybit**, so Coinglass URLs use `Bybit_{SYMBOL}USDT`
- Mode B uses ccxt numerical analysis (OI, CVD, funding) — no screenshots needed
- Charts are set to **specified timeframe** via localStorage injection (specific ticker mode)
- CMC API free tier: 500 coins per call, 1 credit per call
- Specific ticker screenshots saved as `charts/{SYMBOL}_{TIMEFRAME}.png` (e.g. `BTC_h4.png`)
