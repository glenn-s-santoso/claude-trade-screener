# Claude Trade Screener

A hybrid crypto screening and trading tool. Python handles the free, deterministic work (data fetching, chart screenshots); Claude handles the intelligent work (chart analysis, setup identification, trade execution).

## How it works

1. **Screen** — Fetch top coins from CoinMarketCap, filter by volume/market cap ratio ≥ 0.2, take 4H chart screenshots from Coinglass
2. **Analyze** — Claude reads each chart image and rates setups using Smart Money Concepts, Wyckoff Theory, Fibonacci levels, and on-chain metrics
3. **Trade** — Place limit orders on Bybit with partial TP (limit) + market SL via Bybit V5 API

## Setup

```bash
# screen-coins skill
cd .claude/skills/screen-coins
uv sync
uv run playwright install chromium
cp .env.example .env  # Add CMC_API_KEY

# bybit-trading skill
cd .claude/skills/bybit-trading
uv sync
cp .env.example .env  # Add BYBIT_API_KEY, BYBIT_API_SECRET, RISK_PER_TRADE
```

## Usage

Run the full screening pipeline:
```
/screen-coins
```

Place a trade (with explicit args or from a chart image):
```
/bybit-trading
```

Or run scripts directly:
```bash
uv run scripts/screen_cmc.py              # Fetch & filter top coins by vol/mcap ratio
uv run scripts/screenshot_coinglass.py    # Screenshot 4H Coinglass charts
```

## Skills

### `/screen-coins`

Orchestrates a 4-step pipeline:

1. `screen_cmc.py` — Calls CMC API, filters stablecoins, ranks by `volume_24h / market_cap`, keeps top 20 with ratio ≥ 0.2
2. `screenshot_coinglass.py` — Uses Playwright to capture 4H charts from Coinglass (Bybit feed), with retry logic and rate limiting
3. Claude analyzes each chart for: market structure, Smart Money Concepts (order blocks, FVGs, liquidity sweeps, ChoCh/MSS/BoS), Wyckoff patterns, Golden Pocket (Fib levels), volume profile, spot/futures CVD, open interest
4. Results saved to `LLM_RESULT.md` with a ranked table and top 3-5 actionable setups

### `/bybit-trading`

Places a limit order on Bybit with:

- Max leverage (auto-fetched per instrument)
- Partial TP as a Limit order (separate `tpLimitPrice`)
- Market SL
- Auto-calculated quantity from `RISK_PER_TRADE` if `qty` is omitted

**Required inputs:** `symbol`, `side`, `entry_price`, `take_profit`, `tp_limit_price`, `stop_loss`
**Optional:** `qty` (auto-calculated from risk), `--testnet`

```bash
uv run python scripts/trading_setup.py \
  --symbol BTCUSDT \
  --side Buy \
  --entry-price 60000 \
  --take-profit 63000 \
  --tp-limit-price 62950 \
  --stop-loss 58000
```

## Project structure

```
.claude/skills/
├── screen-coins/
│   ├── scripts/
│   │   ├── screen_cmc.py               # CMC API → filter → JSON
│   │   └── screenshot_coinglass.py     # Playwright → 4H chart PNGs
│   ├── data/                           # Runtime output (gitignored)
│   │   ├── screening_results.json
│   │   └── charts/*.png
│   └── SKILL.md                        # Skill definition
└── bybit-trading/
    ├── scripts/
    │   ├── trading_setup.py            # Bybit V5 order placement
    │   └── example_usage.py
    └── SKILL.md                        # Skill definition

LLM_RESULT.md                           # Analysis output (gitignored, regenerated each run)
```

## Environment variables

**screen-coins:**
```
CMC_API_KEY=          # CoinMarketCap Pro API key (free tier works)
```

**bybit-trading:**
```
BYBIT_API_KEY=        # Bybit API key
BYBIT_API_SECRET=     # Bybit API secret
RISK_PER_TRADE=100    # USD to risk per trade (used for auto qty calculation)
```

## Notes

- CMC free tier: 200 coins/call, 1 credit/call
- Coinglass URLs use `Bybit_{SYMBOL}USDT` format
- Charts are forced to 4H via localStorage injection before screenshot
- Bybit UTA in cross margin, one-way mode (`positionIdx = 0`)
- Quantity calculation: `RISK_PER_TRADE / |entry - stop_loss|`, rounded down to nearest lot step
