# Strategy Optimization Module for Synergy7 Trading System

This directory contains the strategy optimization components for the Synergy7 Trading System, implementing the directives from the strategy_finder.md file.

## Overview

The strategy optimization module provides tools for optimizing trading strategies, with a focus on the Momentum strategy as directed by the strategy_finder.md file.

## Components

### Momentum Optimizer (`momentum_optimizer.py`)

The Momentum Optimizer provides tools for optimizing the Momentum strategy:

- Parameter optimization using grid search
- Walk-forward optimization
- Performance evaluation
- Visualization of optimization results

Key features:
- Grid search over parameter space
- Train/test split validation
- Walk-forward optimization to prevent overfitting
- Performance metrics calculation
- Visualization of parameter distributions

## Configuration

Strategy optimization parameters can be configured in the `config.yaml` file:

```yaml
strategy_optimization:
  momentum:
    # Parameter ranges for optimization
    window_size_range: [5, 10, 15, 20, 25, 30]
    threshold_range: [0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
    smoothing_factor_range: [0.1, 0.2, 0.3, 0.4, 0.5]
    max_value_range: [0.05, 0.1, 0.15, 0.2, 0.25]
    
    # Optimization settings
    train_test_split: 0.7
    walk_forward_window: 30
    walk_forward_step: 7
    min_trades: 10
    
    # Output settings
    output_dir: "output/momentum_optimizer"
```

## Usage

### Parameter Optimization

```python
from core.strategies.momentum_optimizer import MomentumOptimizer

# Initialize optimizer
optimizer = MomentumOptimizer(config)

# Optimize parameters
results = optimizer.optimize_parameters(price_data)

# Get best parameters
best_params = results["best_params"]
print(f"Best parameters: {best_params}")
print(f"Train performance: {results['train_performance']}")
print(f"Test performance: {results['test_performance']}")
```

### Walk-Forward Optimization

```python
from core.strategies.momentum_optimizer import MomentumOptimizer

# Initialize optimizer
optimizer = MomentumOptimizer(config)

# Perform walk-forward optimization
wfo_results = optimizer.walk_forward_optimization(price_data)

# Analyze results
for period_result in wfo_results["wfo_results"]:
    print(f"Period: {period_result['period']['start']} to {period_result['period']['end']}")
    print(f"Best parameters: {period_result['best_params']}")
    print(f"Test performance: {period_result['test_performance']}")
```

### Visualization

```python
from core.strategies.momentum_optimizer import MomentumOptimizer

# Initialize optimizer
optimizer = MomentumOptimizer(config)

# Optimize parameters
results = optimizer.optimize_parameters(price_data)

# Plot optimization results
optimizer.plot_optimization_results(results["all_results"])
```

## Momentum Strategy Parameters

The Momentum strategy uses the following parameters:

- **window_size**: The lookback window for calculating momentum (in periods)
- **threshold**: The threshold for generating signals (as a decimal)
- **smoothing_factor**: The smoothing factor for the momentum calculation (0-1)
- **max_value**: The maximum momentum value (caps extreme values)

## Performance Metrics

The optimizer calculates the following performance metrics:

- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Profit Factor**: Gross profit / gross loss (higher is better)
- **Win Rate**: Percentage of winning trades (higher is better)
- **Max Drawdown**: Maximum peak-to-trough decline (lower is better)
- **Total Return**: Total return over the period (higher is better)
- **Number of Trades**: Total number of trades
- **Average Trade Return**: Average return per trade (higher is better)

## Testing

Unit tests for the Momentum Optimizer are available in the `tests/` directory:

- `test_momentum_optimizer.py`

Run the tests with:

```bash
python -m unittest tests.test_momentum_optimizer
```

## Optimization Process

The optimization process follows these steps:

1. **Parameter Grid Definition**: Define the parameter space to search
2. **Train/Test Split**: Split the data into training and testing sets
3. **Grid Search**: Evaluate all parameter combinations on the training data
4. **Parameter Selection**: Select the best parameters based on Sharpe ratio
5. **Out-of-Sample Testing**: Evaluate the best parameters on the testing data
6. **Walk-Forward Optimization**: Repeat the process on rolling windows of data

## Avoiding Overfitting

To avoid overfitting, the optimizer uses several techniques:

- **Train/Test Split**: Parameters are selected on training data and validated on testing data
- **Walk-Forward Optimization**: Parameters are optimized on rolling windows of data
- **Minimum Trades Requirement**: Strategies must generate a minimum number of trades
- **Multiple Metrics**: Strategies are evaluated on multiple performance metrics

## Future Enhancements

Planned enhancements for the strategy optimization module:

- **Genetic Algorithms**: More efficient parameter search
- **Machine Learning Integration**: Use ML to identify optimal parameters
- **Multi-Strategy Optimization**: Optimize multiple strategies together
- **Portfolio Optimization**: Optimize strategy weights in a portfolio
