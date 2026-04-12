# Order Book + Recent Trades Use Cases

## Overview
Fetch real-time market depth and tape analysis to understand immediate liquidity, spread, and aggressive buyer/seller activity.

## Use Cases

### 1. **Liquidity Assessment**
- **Goal**: Determine if a pair is liquid enough to trade
- **How**: Check bid/ask spread and order book depth
- **Example**: 
  ```bash
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT --depth 20
  ```
- **Interpretation**: Tight spread (<0.01%) = highly liquid; wide spread (>0.1%) = illiquid or volatile

### 2. **Market Imbalance Detection**
- **Goal**: Identify if buyers or sellers are dominating the order book
- **How**: Compare bid vs ask volume in top N levels
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol ETH/USDT --depth 10
  ```
- **Interpretation**: `imbalance_side: "bid"` + high ratio = bullish pressure; `imbalance_side: "ask"` = bearish pressure

### 3. **Tape Reading (Aggressor Analysis)**
- **Goal**: See who's pushing price — buyers or sellers
- **How**: Analyze recent trades for dominant side and volume ratio
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol SOL/USDT --trades 100
  ```
- **Interpretation**: If recent trades are dominated by buys = aggressive buying; dominated by sells = aggressive selling

### 4. **Confluence with Chart Analysis**
- **Goal**: Confirm chart breakout/breakdown with real-time tape
- **How**: Check if order book imbalance aligns with chart setup
- **Example**:
  - Chart shows breakout above resistance
  - Run orderbook script → `imbalance_side: "bid"` with high ratio
  - **Confluence**: Both chart and tape confirm bullish bias
  ```bash
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT
  ```

### 5. **Entry Confirmation**
- **Goal**: Validate entry point before placing trade
- **How**: Check spread, imbalance, and recent tape at entry price
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol AAPL/USDT --depth 15 --trades 50
  ```
- **Interpretation**: Tight spread + bullish imbalance + buy-dominated tape = strong entry signal

### 6. **Multi-Exchange Comparison**
- **Goal**: Find the most liquid exchange for a pair
- **How**: Run orderbook on different exchanges, compare spreads
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT --exchange binance
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT --exchange okx
  ```
- **Interpretation**: Binance spread 0.01% vs OKX spread 0.05% → Binance is more liquid

### 7. **Scalping Setup Validation**
- **Goal**: Ensure pair has tight spread for scalping
- **How**: Check spread and order book depth
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol BTC/USDT --depth 5
  ```
- **Interpretation**: Spread <0.01% + deep book = good for scalping

### 8. **Momentum Confirmation**
- **Goal**: Confirm momentum by checking if recent trades are one-sided
- **How**: Look at `dominant_side` and buy/sell ratio in recent trades
- **Example**:
  ```bash
  uv run python scripts/orderbook_trades.py --symbol ETH/USDT --trades 200
  ```
- **Interpretation**: If 80%+ of recent trades are buys = strong upside momentum

## Output Fields

- **`imbalance_side`**: "bid" (bullish) or "ask" (bearish)
- **`imbalance_ratio`**: bid_volume / ask_volume (>1 = bullish, <1 = bearish)
- **`spread`**: bid/ask spread in percentage
- **`dominant_side`**: "buy" or "sell" from recent trades
- **`buy_sell_ratio`**: buy_volume / sell_volume from recent trades
- **`combined_signal`**: Pre-computed confluence interpretation
