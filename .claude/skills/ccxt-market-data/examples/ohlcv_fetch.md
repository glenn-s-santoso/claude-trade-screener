# OHLCV Fetch Use Cases

## Overview
Fetch historical candlestick data with full pagination support for any timeframe and any lookback window. No API key required.

## Use Cases

### 1. **Technical Analysis Setup Validation**
- **Goal**: Get candles to confirm chart patterns (triangles, flags, breakouts)
- **How**: Fetch 1h or 4h candles for the past 7-14 days
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 4h --days 14
  ```
- **Interpretation**: Analyze candles for support/resistance, trend direction, volume profile

### 2. **Moving Average Calculation**
- **Goal**: Calculate 20/50/200 MA for trend confirmation
- **How**: Fetch daily candles for 200+ days, compute MAs
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol ETH/USDT --timeframe 1d --days 365
  ```
- **Interpretation**: Price above 200MA = uptrend; below = downtrend

### 3. **Volatility Assessment**
- **Goal**: Measure recent volatility to size positions
- **How**: Fetch 1h candles for past 7 days, calculate ATR or standard deviation
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol SOL/USDT --timeframe 1h --days 7
  ```
- **Interpretation**: High volatility (large candles) = wider stops; low volatility = tighter stops

### 4. **Confluence with Market Metrics**
- **Goal**: Combine OHLCV with OI/CVD/funding for complete picture
- **How**: Fetch candles + run market_metrics.py, compare price action with OI/CVD trends
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1h --days 2
  uv run python scripts/market_metrics.py --symbol BTC/USDT --days 2
  ```
- **Interpretation**: Rising OI + bullish candles + positive CVD = strong confluence

### 5. **Breakout Validation**
- **Goal**: Confirm breakout above resistance with volume
- **How**: Fetch recent candles, check if volume increased on breakout
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1h --days 3
  ```
- **Interpretation**: High volume on breakout candle = strong breakout; low volume = weak/fake breakout

### 6. **Intraday Scalping Setup**
- **Goal**: Identify intraday momentum for scalping
- **How**: Fetch 5m or 15m candles for past 1-2 days
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 5m --days 1
  ```
- **Interpretation**: Series of higher highs/lows = uptrend; lower highs/lows = downtrend

### 7. **Swing Trade Entry Timing**
- **Goal**: Find optimal entry on 4h timeframe
- **How**: Fetch 4h candles for past 30 days, identify support zones
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol ETH/USDT --timeframe 4h --days 30
  ```
- **Interpretation**: Price pulling back to 50MA on 4h = potential swing entry

### 8. **Gap Analysis**
- **Goal**: Identify overnight gaps for gap-fill trades
- **How**: Fetch daily candles, compare previous close to next open
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1d --days 30
  ```
- **Interpretation**: Large gap up/down = potential gap-fill opportunity

### 9. **Volume Profile Analysis**
- **Goal**: Identify high-volume nodes for support/resistance
- **How**: Fetch candles and analyze volume distribution
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol SOL/USDT --timeframe 1h --days 7
  ```
- **Interpretation**: High volume at certain price level = strong support/resistance

### 10. **Trend Strength Measurement**
- **Goal**: Quantify trend strength by analyzing consecutive candles
- **How**: Fetch hourly candles, count consecutive higher/lower closes
- **Example**:
  ```bash
  uv run python scripts/ohlcv_fetch.py --symbol BTC/USDT --timeframe 1h --days 7
  ```
- **Interpretation**: 5+ consecutive green candles = strong uptrend; 5+ red = strong downtrend

## Output Fields

- **`timestamp_ms`**: Unix timestamp in milliseconds
- **`datetime`**: ISO 8601 formatted timestamp
- **`open`**: Opening price
- **`high`**: Highest price in candle
- **`low`**: Lowest price in candle
- **`close`**: Closing price
- **`volume`**: Trading volume in base asset
- **`candle_count`**: Total number of candles fetched
- **`first_candle`**: Oldest candle (earliest timestamp)
- **`last_candle`**: Newest candle (latest timestamp)

## Tips

- Use `--summary-only` flag to omit the full candles array for large windows (useful for quick summaries)
- Timeframes: 1m, 5m, 15m, 1h, 4h, 1d (varies by exchange)
- Default exchange: Binance (most reliable data)
