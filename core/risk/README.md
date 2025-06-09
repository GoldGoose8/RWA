# Risk Management Module for Synergy7 Trading System

This directory contains the risk management components for the Synergy7 Trading System, implementing the directives from the strategy_finder.md file.

## Overview

The risk management module provides comprehensive risk controls at multiple levels:

1. **Position Level**: Dynamic position sizing and stop-loss management
2. **Portfolio Level**: Exposure limits and drawdown controls
3. **System Level**: Circuit breakers to halt trading when risk thresholds are exceeded

## Components

### Position Sizer (`position_sizer.py`)

The Position Sizer calculates optimal position sizes based on:

- Volatility scaling (smaller positions during high volatility)
- Account balance
- Signal strength
- Risk parameters

Key features:
- Dynamic position sizing based on market conditions
- Volatility-adjusted position sizes
- Risk-based stop-loss calculation
- Take-profit level calculation based on risk-reward ratio

### Stop Loss Manager (`stop_loss.py`)

The Stop Loss Manager provides advanced stop-loss functionality:

- Trailing stops that move with price
- Time-based stop widening
- Volatility-based stop calculation

Key features:
- Trailing stops that activate after a certain profit threshold
- Automatic stop updates based on price movement
- Support for both long and short positions
- Time-based widening to avoid getting stopped out by noise

### Portfolio Limits (`portfolio_limits.py`)

The Portfolio Limits component enforces risk constraints at the portfolio level:

- Maximum portfolio exposure
- Maximum single-market exposure
- Maximum drawdown limits

Key features:
- Real-time tracking of positions and exposures
- Daily, weekly, and monthly drawdown limits
- Pre-trade checks to ensure new positions don't exceed limits
- Position tracking and PnL calculation

### Circuit Breaker (`circuit_breaker.py`)

The Circuit Breaker automatically halts trading when risk thresholds are exceeded:

- Maximum consecutive losses
- Maximum daily loss
- Maximum drawdown
- API failure detection
- Market volatility monitoring

Key features:
- Automatic trading halt when thresholds are exceeded
- Cooldown period before trading can resume
- Half-open state requiring manual reset
- API failure detection to prevent trading during outages

## Configuration

Risk management parameters can be configured in the `config.yaml` file:

```yaml
risk_management:
  # Position Sizer
  max_position_size: 0.1
  min_position_size: 0.01
  volatility_scaling: true
  volatility_lookback: 20
  
  # Stop Loss
  trailing_enabled: true
  trailing_activation_pct: 0.01
  trailing_distance_pct: 0.02
  time_based_widening: true
  
  # Portfolio Limits
  max_portfolio_exposure: 0.8
  max_single_market_exposure: 0.3
  max_daily_drawdown: 0.05
  max_weekly_drawdown: 0.1
  max_monthly_drawdown: 0.15
  
  # Circuit Breaker
  circuit_breaker_enabled: true
  max_consecutive_losses: 3
  max_daily_loss_pct: 0.05
  max_drawdown_pct: 0.1
  cooldown_minutes: 60
  api_failure_threshold: 5
```

## Usage

### Position Sizing

```python
from core.risk.position_sizer import PositionSizer

# Initialize position sizer
position_sizer = PositionSizer(config)

# Calculate position size
position_size_info = position_sizer.calculate_position_size(
    price_data,
    account_balance,
    market,
    signal_strength
)

# Calculate stop loss
stop_loss_info = position_sizer.calculate_stop_loss(
    entry_price,
    position_size_info["position_size"],
    account_balance,
    price_data,
    is_long
)

# Calculate take profit
take_profit_price = position_sizer.calculate_take_profit(
    entry_price,
    stop_loss_info["stop_loss_price"],
    is_long,
    risk_reward_ratio=2.0
)
```

### Stop Loss Management

```python
from core.risk.stop_loss import StopLossManager

# Initialize stop loss manager
stop_loss_manager = StopLossManager(config)

# Set initial stop
stop_info = stop_loss_manager.set_initial_stop(
    trade_id,
    entry_price,
    entry_time,
    initial_stop_price,
    is_long
)

# Update stop based on current price
updated_stop_info = stop_loss_manager.update_stop(
    trade_id,
    current_price,
    current_time
)

# Check if stop is triggered
if stop_loss_manager.check_stop_triggered(trade_id, current_price):
    # Close position
    pass
```

### Portfolio Limits

```python
from core.risk.portfolio_limits import PortfolioLimits

# Initialize portfolio limits
portfolio_limits = PortfolioLimits(config)

# Set initial balance
portfolio_limits.set_initial_balance(account_balance)

# Check if a new position can be opened
can_open, reason = portfolio_limits.can_open_position(
    market,
    size,
    price
)

if can_open:
    # Open position
    portfolio_limits.add_position(
        position_id,
        market,
        size,
        entry_price,
        is_long
    )
else:
    # Log reason why position can't be opened
    logger.warning(reason)
```

### Circuit Breaker

```python
from core.risk.circuit_breaker import CircuitBreaker

# Initialize circuit breaker
circuit_breaker = CircuitBreaker(config)

# Check if trading is allowed
can_trade, reason = circuit_breaker.can_trade()

if can_trade:
    # Execute trade
    pass
else:
    # Log reason why trading is not allowed
    logger.warning(reason)

# Record trade result
circuit_breaker.record_trade_result(
    trade_id,
    profit_loss,
    initial_balance
)

# Record API failure
circuit_breaker.record_api_failure("helius")

# Record API success
circuit_breaker.record_api_success("helius")
```

## Testing

Unit tests for all risk management components are available in the `tests/` directory:

- `test_position_sizer.py`
- `test_stop_loss.py`
- `test_portfolio_limits.py`
- `test_circuit_breaker.py`

Run all tests with:

```bash
python -m unittest discover tests
```

Or run individual tests with:

```bash
python -m unittest tests.test_position_sizer
```
