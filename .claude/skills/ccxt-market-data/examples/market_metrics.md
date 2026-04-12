# Market Metrics Use Cases

## Overview
Fetch Open Interest (OI), Spot Cumulative Volume Delta (CVD), and Funding Rates to understand market positioning, sentiment, and leverage crowding.

## Use Cases

### 1. **Bullish Confluence Detection**
- **Goal**: Identify when all three signals align bullishly
- **How**: Fetch market metrics, check for rising OI + positive CVD + negative funding
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 2 --cvd-hours 4
  ```
- **Interpretation**: 
  - Rising OI = new conviction entering
  - Positive CVD = net buying pressure
  - Negative funding = shorts paying longs (crowded short = squeeze risk)
  - **Result**: Strong bullish setup with room to run

### 2. **Bearish Confluence Detection**
- **Goal**: Identify when all three signals align bearishly
- **How**: Fetch market metrics, check for rising OI + negative CVD + positive funding
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol ETH/USDT --days 2 --cvd-hours 4
  ```
- **Interpretation**:
  - Rising OI = new conviction entering
  - Negative CVD = net selling pressure
  - Positive funding = longs paying shorts (crowded long = squeeze risk)
  - **Result**: Strong bearish setup with downside potential

### 3. **Deleverage Event Detection**
- **Goal**: Spot when market is unwinding leverage (liquidation cascade risk)
- **How**: Fetch market metrics, check for falling OI
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 5
  ```
- **Interpretation**:
  - Falling OI = contracts closing
  - Combined with price action = deleverage event
  - **Result**: Volatility spike likely; avoid or use tight stops

### 4. **Squeeze Risk Assessment**
- **Goal**: Identify crowded positions that could trigger a squeeze
- **How**: Check funding rates and OI trend
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol SOL/USDT --days 2
  ```
- **Interpretation**:
  - High positive funding (>0.01%) = crowded long → long squeeze risk
  - High negative funding (<-0.01%) = crowded short → short squeeze risk
  - Rising OI + extreme funding = imminent squeeze

### 5. **Entry Confirmation (Spot Trader)**
- **Goal**: Confirm spot entry with on-chain sentiment
- **How**: Check positive CVD + negative funding (unlevered buying)
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --cvd-hours 4 --cvd-tf 5m
  ```
- **Interpretation**:
  - Positive CVD = spot buyers dominating
  - Negative funding = shorts crowded (potential squeeze)
  - **Result**: Safe spot entry with upside potential

### 6. **Futures Trader Entry Confirmation**
- **Goal**: Confirm futures entry with OI + CVD + funding alignment
- **How**: Fetch all three metrics, check for confluence
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol ETH/USDT --days 2 --cvd-hours 2
  ```
- **Interpretation**:
  - Rising OI + positive CVD + negative funding = bullish long entry
  - Rising OI + negative CVD + positive funding = bearish short entry

### 7. **Spot vs Futures Divergence**
- **Goal**: Identify when spot and futures are misaligned
- **How**: Compare spot CVD with futures funding
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --cvd-hours 4
  ```
- **Interpretation**:
  - Positive CVD (spot buying) + positive funding (longs crowded) = divergence
  - Spot buyers vs futures longs = potential reversal

### 8. **Trend Strength Validation**
- **Goal**: Confirm uptrend/downtrend with OI and CVD
- **How**: Check if OI is rising (conviction) and CVD aligns with trend
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol SOL/USDT --days 3
  ```
- **Interpretation**:
  - Uptrend + rising OI + positive CVD = strong uptrend
  - Uptrend + falling OI + negative CVD = weak uptrend (reversal risk)

### 9. **Risk Management (Position Sizing)**
- **Goal**: Size positions based on funding rate extremes
- **How**: Check funding rate to gauge crowding
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 1
  ```
- **Interpretation**:
  - Extreme funding (>0.05%) = reduce position size (squeeze risk)
  - Normal funding (0.01-0.02%) = normal position size
  - Negative funding = can increase size (shorts crowded)

### 10. **Multi-Timeframe CVD Analysis**
- **Goal**: Confirm trend with different CVD windows
- **How**: Run market_metrics with different `--cvd-hours` values
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --cvd-hours 1
  uv run python scripts/market_metrics.py --symbol BTC/USDT --cvd-hours 4
  uv run python scripts/market_metrics.py --symbol BTC/USDT --cvd-hours 24
  ```
- **Interpretation**:
  - 1h CVD = short-term momentum
  - 4h CVD = intermediate trend
  - 24h CVD = macro sentiment
  - All positive = strong bullish confluence

### 11. **Funding Rate Arbitrage Setup**
- **Goal**: Identify when funding is extreme (arbitrage opportunity)
- **How**: Monitor funding rates, compare with spot price
- **Example**:
  ```bash
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 1
  ```
- **Interpretation**:
  - Positive funding >0.05% = futures overpriced vs spot
  - Negative funding <-0.05% = futures underpriced vs spot
  - **Result**: Potential cash-and-carry or reverse arbitrage

### 12. **Confluence with Chart + Tape**
- **Goal**: Complete analysis combining chart, tape, and on-chain metrics
- **How**: Run all three scripts (OHLCV, orderbook_trades, market_metrics)
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 4h --days 7
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT --depth 10
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 2
  ```
- **Interpretation**:
  - Chart: Breakout above resistance
  - Tape: Bid-side imbalance
  - Metrics: Rising OI + positive CVD + negative funding
  - **Result**: Maximum confluence = high-confidence entry

## Output Fields

- **`open_interest`**: Current OI, OI change, OI trend (rising/falling/flat)
- **`spot_cvd`**: Cumulative volume delta, CVD direction, recent trend
- **`funding_rates`**: Current rate, 24h average, historical rates
- **`interpretation_guide`**: Pre-computed meanings for each signal

## CVD Interpretation Quick Reference

| Signal | Meaning |
|---|---|
| Rising OI + Positive CVD + Negative funding | **Strong bullish** — unlevered buying, room to run |
| Rising OI + Negative CVD + Positive funding | **Strong bearish** — heavy shorts building, squeeze risk |
| Falling OI + Any CVD | **Deleverage** — read price action for direction |
| High positive funding (>0.05%) | **Crowded long** — long squeeze risk |
| High negative funding (<-0.05%) | **Crowded short** — short squeeze risk |
| Positive CVD + Negative funding | **Bullish unlevered** — spot buyers dominating |
| Negative CVD + Positive funding | **Bearish unlevered** — spot sellers dominating |

## Tips

- Default exchange: Binance (most reliable OI/funding data)
- CVD can aggregate across multiple spot exchanges for better signal (default: binance, okx, bybit, coinbase, bitfinex, kraken, bitstamp, cryptocom)
- Use `--cvd-exchange` to focus on single exchange
- Funding rates update every 8 hours on most exchanges
