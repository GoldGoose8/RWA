# Risk Management Configuration Guide

This guide provides detailed information on configuring and tuning the risk management components for the Synergy7 Trading System.

## Overview

The risk management system consists of four main components:

1. **Position Sizer**: Determines optimal position sizes based on volatility and account balance
2. **Stop Loss Manager**: Manages trailing stops and time-based stop widening
3. **Portfolio Limits**: Enforces exposure and drawdown limits at the portfolio level
4. **Circuit Breaker**: Automatically halts trading when risk thresholds are exceeded

## Configuration File Structure

Risk management configuration is defined in the `config.yaml` file under the `risk_management` section:

```yaml
risk_management:
  position_sizer:
    # Position sizer configuration
    
  stop_loss:
    # Stop loss configuration
    
  portfolio_limits:
    # Portfolio limits configuration
    
  circuit_breaker:
    # Circuit breaker configuration
```

## Position Sizer Configuration

The position sizer determines the optimal size for each trade based on volatility and account balance.

```yaml
position_sizer:
  max_position_size: 0.1         # Maximum position size as a fraction of account balance
  min_position_size: 0.01        # Minimum position size as a fraction of account balance
  position_size_increment: 0.01  # Increment for position sizing
  volatility_scaling: true       # Whether to scale position size based on volatility
  volatility_lookback: 20        # Number of periods to look back for volatility calculation
  risk_per_trade: 0.01           # Maximum risk per trade as a fraction of account balance
  atr_multiplier: 2.0            # Multiplier for ATR when calculating stop distance
```

### Tuning Guidelines

- **max_position_size**: Start conservative (0.05-0.1) and increase gradually as the system proves reliable
- **volatility_scaling**: Keep enabled to reduce position sizes during high volatility
- **risk_per_trade**: 0.01 (1%) is a good starting point; never exceed 0.02 (2%)
- **atr_multiplier**: 2.0-3.0 is typical; higher values give more room but increase potential loss

## Stop Loss Manager Configuration

The stop loss manager handles the placement and updating of stop losses, including trailing stops.

```yaml
stop_loss:
  trailing_enabled: true           # Whether to use trailing stops
  trailing_activation_pct: 0.01    # Profit percentage required to activate trailing stop
  trailing_distance_pct: 0.02      # Distance of trailing stop as percentage of price
  volatility_multiplier: 2.0       # Multiplier for volatility when calculating stop distance
  time_based_widening: true        # Whether to widen stops over time
  widening_factor: 0.001           # Factor for time-based stop widening per hour
```

### Tuning Guidelines

- **trailing_activation_pct**: 0.01 (1%) is a good starting point; increase for longer-term trades
- **trailing_distance_pct**: 0.02 (2%) is typical; smaller values track price more closely but risk premature stopouts
- **time_based_widening**: Enable for longer-term trades to avoid stopouts from normal market noise
- **widening_factor**: Start small (0.0005-0.001) and adjust based on average trade duration

## Portfolio Limits Configuration

Portfolio limits enforce risk constraints at the portfolio level to prevent overexposure.

```yaml
portfolio_limits:
  max_portfolio_exposure: 0.8       # Maximum total portfolio exposure
  max_single_market_exposure: 0.3   # Maximum exposure to a single market
  max_correlated_exposure: 0.5      # Maximum exposure to correlated markets
  max_daily_drawdown: 0.05          # Maximum allowed daily drawdown
  max_weekly_drawdown: 0.1          # Maximum allowed weekly drawdown
  max_monthly_drawdown: 0.15        # Maximum allowed monthly drawdown
```

### Tuning Guidelines

- **max_portfolio_exposure**: Start conservative (0.5-0.6) and increase as system proves reliable
- **max_single_market_exposure**: Keep below 0.3 (30%) to ensure diversification
- **max_daily_drawdown**: 0.05 (5%) is a good starting point; adjust based on strategy volatility
- **max_weekly_drawdown**: Typically 2x daily drawdown limit
- **max_monthly_drawdown**: Typically 3x daily drawdown limit

## Circuit Breaker Configuration

The circuit breaker automatically halts trading when risk thresholds are exceeded.

```yaml
circuit_breaker:
  enabled: true                    # Whether the circuit breaker is enabled
  max_consecutive_losses: 3        # Maximum number of consecutive losing trades
  max_daily_loss_pct: 0.05         # Maximum daily loss as percentage of account
  max_drawdown_pct: 0.1            # Maximum drawdown percentage
  cooldown_minutes: 60             # Cooldown period after circuit breaker trips
  volatility_threshold: 0.05       # Market volatility threshold
  api_failure_threshold: 5         # Number of API failures before tripping
```

### Tuning Guidelines

- **max_consecutive_losses**: 3-5 is typical; adjust based on strategy win rate
- **max_daily_loss_pct**: Should align with max_daily_drawdown in portfolio limits
- **cooldown_minutes**: 60 minutes is a good starting point; increase for more conservative approach
- **volatility_threshold**: Set slightly above normal market volatility

## API Circuit Breakers

API circuit breakers prevent continued trading during API outages or failures.

```yaml
apis:
  helius:
    circuit_breaker:
      failure_threshold: 5           # Number of failures before tripping
      reset_timeout_seconds: 300     # Timeout before attempting reset
    retry_policy:
      max_retries: 3                 # Maximum number of retries
      backoff_factor: 2              # Backoff factor for retries
      max_backoff_seconds: 30        # Maximum backoff time
```

### Tuning Guidelines

- **failure_threshold**: 5 is a good starting point; lower for critical APIs
- **reset_timeout_seconds**: 300 (5 minutes) is typical; increase for persistent issues
- **max_retries**: 3-5 is standard; adjust based on API reliability

## Risk Profile Presets

Here are some preset risk profiles you can use as starting points:

### Conservative Profile

```yaml
risk_management:
  position_sizer:
    max_position_size: 0.05
    min_position_size: 0.01
    volatility_scaling: true
    risk_per_trade: 0.005
    
  stop_loss:
    trailing_enabled: true
    trailing_activation_pct: 0.015
    trailing_distance_pct: 0.025
    
  portfolio_limits:
    max_portfolio_exposure: 0.5
    max_single_market_exposure: 0.2
    max_daily_drawdown: 0.03
    
  circuit_breaker:
    max_consecutive_losses: 3
    max_daily_loss_pct: 0.03
    cooldown_minutes: 120
```

### Moderate Profile

```yaml
risk_management:
  position_sizer:
    max_position_size: 0.1
    min_position_size: 0.01
    volatility_scaling: true
    risk_per_trade: 0.01
    
  stop_loss:
    trailing_enabled: true
    trailing_activation_pct: 0.01
    trailing_distance_pct: 0.02
    
  portfolio_limits:
    max_portfolio_exposure: 0.7
    max_single_market_exposure: 0.25
    max_daily_drawdown: 0.05
    
  circuit_breaker:
    max_consecutive_losses: 4
    max_daily_loss_pct: 0.05
    cooldown_minutes: 60
```

### Aggressive Profile

```yaml
risk_management:
  position_sizer:
    max_position_size: 0.15
    min_position_size: 0.02
    volatility_scaling: true
    risk_per_trade: 0.015
    
  stop_loss:
    trailing_enabled: true
    trailing_activation_pct: 0.008
    trailing_distance_pct: 0.018
    
  portfolio_limits:
    max_portfolio_exposure: 0.85
    max_single_market_exposure: 0.35
    max_daily_drawdown: 0.08
    
  circuit_breaker:
    max_consecutive_losses: 5
    max_daily_loss_pct: 0.08
    cooldown_minutes: 45
```

## Dynamic Risk Adjustment

The risk management system supports dynamic adjustment based on performance and market conditions.

### Performance-Based Adjustment

```python
def adjust_risk_based_on_performance(win_rate, sharpe_ratio, drawdown):
    """Adjust risk parameters based on performance metrics."""
    if win_rate > 0.7 and sharpe_ratio > 1.5 and drawdown < 0.05:
        # Increase risk for strong performance
        return {
            "position_sizer.max_position_size": 0.12,
            "position_sizer.risk_per_trade": 0.012,
            "portfolio_limits.max_portfolio_exposure": 0.75
        }
    elif win_rate < 0.5 or sharpe_ratio < 0.5 or drawdown > 0.1:
        # Decrease risk for poor performance
        return {
            "position_sizer.max_position_size": 0.07,
            "position_sizer.risk_per_trade": 0.007,
            "portfolio_limits.max_portfolio_exposure": 0.5
        }
    else:
        # Maintain current risk levels
        return {}
```

### Market Volatility Adjustment

```python
def adjust_risk_based_on_volatility(current_volatility, average_volatility):
    """Adjust risk parameters based on market volatility."""
    volatility_ratio = current_volatility / average_volatility
    
    if volatility_ratio > 1.5:
        # High volatility - reduce risk
        return {
            "position_sizer.max_position_size": 0.07,
            "stop_loss.trailing_distance_pct": 0.025,
            "circuit_breaker.max_daily_loss_pct": 0.04
        }
    elif volatility_ratio < 0.7:
        # Low volatility - can increase risk slightly
        return {
            "position_sizer.max_position_size": 0.12,
            "stop_loss.trailing_distance_pct": 0.018,
            "circuit_breaker.max_daily_loss_pct": 0.06
        }
    else:
        # Normal volatility - maintain current risk levels
        return {}
```

## Monitoring Risk Management

Key metrics to monitor for risk management effectiveness:

1. **Stopout Rate**: Percentage of trades closed by stop loss
2. **Average Loss Size**: Average size of losing trades
3. **Maximum Drawdown**: Maximum peak-to-trough decline
4. **Daily Value at Risk (VaR)**: Estimated maximum daily loss
5. **Exposure Utilization**: Current exposure as percentage of maximum allowed
6. **Circuit Breaker Activations**: Number and causes of circuit breaker trips

## Troubleshooting

### Common Issues and Solutions

1. **Frequent Stop Loss Triggers**
   - Increase `stop_loss.trailing_distance_pct`
   - Enable `stop_loss.time_based_widening`
   - Increase `stop_loss.volatility_multiplier`

2. **Position Sizes Too Small**
   - Increase `position_sizer.min_position_size`
   - Decrease `position_sizer.volatility_lookback`
   - Increase `position_sizer.risk_per_trade`

3. **Circuit Breaker Trips Too Often**
   - Increase `circuit_breaker.max_consecutive_losses`
   - Increase `circuit_breaker.max_daily_loss_pct`
   - Increase `circuit_breaker.volatility_threshold`

4. **Portfolio Limits Too Restrictive**
   - Increase `portfolio_limits.max_portfolio_exposure`
   - Increase `portfolio_limits.max_single_market_exposure`
   - Increase `portfolio_limits.max_daily_drawdown`

## Best Practices

1. **Start Conservative**: Begin with conservative risk settings and gradually increase as the system proves reliable
2. **Regular Review**: Review risk parameters weekly and adjust based on performance
3. **Stress Testing**: Regularly stress test the system with historical market crashes
4. **Documentation**: Document all risk parameter changes and their effects
5. **Correlation Awareness**: Be aware of correlations between markets when setting exposure limits
6. **Gradual Changes**: Make small, incremental changes to risk parameters
7. **Emergency Plan**: Have a clear plan for emergency risk reduction
