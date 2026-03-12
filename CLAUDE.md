# Crypto Trade Screener

Hybrid crypto screening tool: Python scripts handle data fetching/filtering/screenshots (free), Claude analyzes charts and picks setups (where intelligence is needed).

## Setup

```bash
uv sync
playwright install chromium
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
```

After analyzing the charts, save the result to `LLM_RESULT.md`.

## Structure

- `.claude/skills/screen-coins/scripts/screen_cmc.py` — CoinMarketCap API → filter by volume/market_cap ratio ≥ 0.2 → top 20 → JSON
- `.claude/skills/screen-coins/scripts/screenshot_coinglass.py` — Playwright screenshots of Coinglass 4H charts for each coin
- `.claude/skills/screen-coins/SKILL.md` — Claude skill that orchestrates the pipeline and analyzes charts
- `.claude/skills/screen-coins/data/` — Runtime output (gitignored): `screening_results.json` and `charts/*.png`
- `LLM_RESULT.md` — Analysis results from Claude (gitignored)

## Notes

- User trades on **Bybit**, so Coinglass URLs use `Bybit_{SYMBOL}USDT`
- Charts are set to **4H timeframe** via localStorage injection
- CMC API free tier: 200 coins per call, 1 credit per call
