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
uv run scripts/screen_cmc.py              # Fetch & filter top coins by vol/mcap ratio
uv run scripts/screenshot_coinglass.py    # Screenshot 4H charts from Coinglass
uv run scripts/screenshot_ticker.py --ticker BTCUSDT  # Screenshot specific ticker (h1, h4, m15)
```

Analyze a specific ticker across timeframes:
```
/screen-coins BTCUSDT
```

After analyzing the charts, save the result to `LLM_RESULT.md`.

## Structure

- `.claude/skills/screen-coins/scripts/screen_cmc.py` — CoinMarketCap API → filter by volume/market_cap ratio ≥ 0.2 → top 20 → JSON
- `.claude/skills/screen-coins/scripts/screenshot_coinglass.py` — Playwright screenshots of Coinglass 4H charts for each coin
- `.claude/skills/screen-coins/scripts/screenshot_ticker.py` — Playwright screenshots for a specific ticker at h1, h4, m15 timeframes
- `.claude/skills/screen-coins/SKILL.md` — Claude skill (two modes: full pipeline or specific ticker)
- `.claude/skills/screen-coins/data/` — Runtime output (gitignored): `screening_results.json` and `charts/*.png`
- `LLM_RESULT.md` — Analysis results from Claude (gitignored)

- `.claude/skills/bybit-trading/scripts/trading_setup.py` — Sets max leverage + places Limit order with Partial TP (Limit) + Market SL via Bybit V5 API
- `.claude/skills/bybit-trading/scripts/position_status.py` — Fetches open positions and orders from Bybit V5
- `.claude/skills/bybit-trading/SKILL.md` — Claude skill; invocable with explicit args or from a chart image; also handles `/bybit-trading status`

## Notes

- User trades on **Bybit**, so Coinglass URLs use `Bybit_{SYMBOL}USDT`
- Charts are set to **4H timeframe** via localStorage injection (full pipeline) or specified timeframe (specific ticker)
- CMC API free tier: 200 coins per call, 1 credit per call
- Specific ticker screenshots saved as `charts/{SYMBOL}_{TIMEFRAME}.png` (e.g. `BTC_h4.png`)
