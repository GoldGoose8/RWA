#!/usr/bin/env python3
"""
VectorBT Backtest Runner Module

This module provides a backtest runner using VectorBT for realistic backtesting
with variable slippage and liquidity penalties.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vectorbt_runner')

class VectorBTRunner:
    """
    Backtest runner using VectorBT for realistic backtesting.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the VectorBT backtest runner.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Load backtest configuration
        self.start_date = self.config.get('start_date', '2023-01-01')
        self.end_date = self.config.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        self.initial_capital = self.config.get('initial_capital', 10000)
        self.fee_pct = self.config.get('fee_pct', 0.001)  # 0.1%

        # Load slippage configuration
        self.slippage_model = self.config.get('slippage_model', 'variable')
        self.base_slippage = self.config.get('base_slippage', 0.001)  # 0.1%
        self.liquidity_penalty = self.config.get('liquidity_penalty', True)
        self.min_liquidity_usd = self.config.get('min_liquidity_usd', 50000)

        # Load data configuration
        self.data_source = self.config.get('data_source', 'phase_2_backtest_engine/datasets/solana_meme_master')
        self.output_dir = self.config.get('output_dir', 'phase_4_deployment/backtest/output')

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"Initialized VectorBTRunner with start_date={self.start_date}, "
                   f"end_date={self.end_date}, initial_capital=${self.initial_capital}")

    def load_price_data(self, symbol: str) -> pd.DataFrame:
        """
        Load historical price data for a symbol.

        Args:
            symbol: Symbol to load data for (e.g., 'SOL-USD')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Extract token symbol from market pair
            token = symbol.split('-')[0].lower()

            # Construct file path
            file_path = os.path.join(self.data_source, f"ohlcv/{token}_usdc.csv")

            # Check if file exists, if not try the old path format
            if not os.path.exists(file_path):
                old_path = os.path.join("phase_2_backtest_engine/datasets/solana_meme_master", f"ohlcv/{token}_usdc.csv")
                if os.path.exists(old_path):
                    file_path = old_path
                    logger.info(f"Using alternative path: {file_path}")

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Price data file not found: {file_path}")
                return pd.DataFrame()

            # Load data from CSV
            df = pd.read_csv(file_path)

            # Convert timestamp to datetime
            if 'Timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['Timestamp'], unit='s')
                df.set_index('datetime', inplace=True)
            elif 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('datetime', inplace=True)
            elif 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
                df.set_index('datetime', inplace=True)

            # Filter by date range
            df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]

            # Rename columns to lowercase if needed
            column_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)

            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Required column '{col}' not found in price data")
                    return pd.DataFrame()

            # Add enhanced features to metadata
            self.enhanced_features = {}
            for col in df.columns:
                if col not in required_columns and col not in ['datetime', 'timestamp', 'date']:
                    self.enhanced_features[col] = df[col].tolist()

            logger.info(f"Loaded {len(df)} price data points for {symbol} with {len(self.enhanced_features)} enhanced features")
            return df
        except Exception as e:
            logger.error(f"Error loading price data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def load_signal_data(self, strategy_id: str) -> pd.DataFrame:
        """
        Load signal data for a strategy.

        Args:
            strategy_id: Strategy ID to load signals for

        Returns:
            DataFrame with signal data
        """
        try:
            # Construct file path
            file_path = os.path.join(self.data_source, 'signals', f"{strategy_id}_signals.json")

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Signal data file not found: {file_path}")
                return pd.DataFrame()

            # Load data from JSON
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Extract signals
            signals = data.get('signals', [])

            # Convert to DataFrame
            df = pd.DataFrame(signals)

            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('datetime', inplace=True)

            # Filter by date range
            df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]

            # Load corresponding outcome data if available
            outcome_path = os.path.join(self.data_source, 'outcomes', f"{strategy_id}_outcomes.json")
            if os.path.exists(outcome_path):
                try:
                    with open(outcome_path, 'r') as f:
                        outcome_data = json.load(f)

                    outcomes = outcome_data.get('outcomes', [])
                    outcome_df = pd.DataFrame(outcomes)

                    if 'signal_timestamp' in outcome_df.columns:
                        # Create a mapping from signal timestamp to outcome
                        outcome_map = {
                            outcome['signal_timestamp']: outcome
                            for outcome in outcomes
                        }

                        # Add outcome data to signal dataframe
                        df['actual_profit_loss_pct'] = df.apply(
                            lambda row: outcome_map.get(row.name.timestamp(), {}).get('profit_loss_pct', 0),
                            axis=1
                        )

                        df['actual_exit_price'] = df.apply(
                            lambda row: outcome_map.get(row.name.timestamp(), {}).get('exit_price', 0),
                            axis=1
                        )

                        df['actual_exit_reason'] = df.apply(
                            lambda row: outcome_map.get(row.name.timestamp(), {}).get('exit_reason', ''),
                            axis=1
                        )

                        logger.info(f"Added outcome data to signals for {strategy_id}")
                except Exception as e:
                    logger.error(f"Error loading outcome data for {strategy_id}: {str(e)}")

            logger.info(f"Loaded {len(df)} signals for {strategy_id}")
            return df
        except Exception as e:
            logger.error(f"Error loading signal data for {strategy_id}: {str(e)}")
            return pd.DataFrame()

    def calculate_variable_slippage(self, price_data: pd.DataFrame) -> pd.Series:
        """
        Calculate variable slippage based on volume and volatility.

        Args:
            price_data: DataFrame with OHLCV data

        Returns:
            Series with slippage values
        """
        # Calculate volatility (standard deviation of returns)
        returns = price_data['close'].pct_change()
        volatility = returns.rolling(window=20).std().fillna(0)

        # Calculate volume relative to average
        volume = price_data['volume']
        avg_volume = volume.rolling(window=20).mean().fillna(volume)
        volume_ratio = volume / avg_volume

        # Calculate slippage
        # Base slippage + volatility adjustment - volume adjustment
        slippage = self.base_slippage + (volatility * 2) - (0.001 * (volume_ratio - 1))

        # Ensure slippage is at least 0.0001 (0.01%)
        slippage = np.maximum(slippage, 0.0001)

        return slippage

    def calculate_liquidity_penalty(self, price_data: pd.DataFrame) -> pd.Series:
        """
        Calculate liquidity penalty based on volume.

        Args:
            price_data: DataFrame with OHLCV data

        Returns:
            Series with liquidity penalty values
        """
        # Calculate dollar volume
        dollar_volume = price_data['close'] * price_data['volume']

        # Calculate liquidity penalty
        # Penalty is higher when dollar volume is lower
        penalty = np.maximum(0, 1 - (dollar_volume / self.min_liquidity_usd))

        # Scale penalty to 0-0.05 (0-5%)
        penalty = penalty * 0.05

        return penalty

    def run_backtest(self, symbol: str, strategy_id: str) -> Dict[str, Any]:
        """
        Run a backtest for a symbol and strategy.

        Args:
            symbol: Symbol to backtest (e.g., 'SOL-USD')
            strategy_id: Strategy ID to backtest

        Returns:
            Dictionary with backtest results
        """
        # Load price data
        price_data = self.load_price_data(symbol)
        if price_data.empty:
            return {'success': False, 'error': f"No price data for {symbol}"}

        # Load signal data
        signal_data = self.load_signal_data(strategy_id)
        if signal_data.empty:
            return {'success': False, 'error': f"No signal data for {strategy_id}"}

        try:
            # Prepare entry/exit signals
            entries = pd.Series(False, index=price_data.index)
            exits = pd.Series(False, index=price_data.index)

            # Map signals to price data
            for idx, row in signal_data.iterrows():
                # Find closest timestamp in price data
                closest_idx = price_data.index[price_data.index.get_indexer([idx], method='nearest')[0]]

                # Set entry/exit signal
                action = row.get('action', '').upper()
                if action == 'BUY':
                    entries[closest_idx] = True
                elif action == 'SELL':
                    exits[closest_idx] = True

            # Calculate variable slippage if enabled
            if self.slippage_model == 'variable':
                slippage = self.calculate_variable_slippage(price_data)
            else:
                slippage = pd.Series(self.base_slippage, index=price_data.index)

            # Calculate liquidity penalty if enabled
            if self.liquidity_penalty:
                penalty = self.calculate_liquidity_penalty(price_data)
                # Add penalty to slippage
                slippage = slippage + penalty

            # Run VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                price_data['close'],
                entries,
                exits,
                init_cash=self.initial_capital,
                fees=self.fee_pct,
                slippage=slippage
            )

            # Calculate metrics
            metrics = portfolio.stats()

            # Convert metrics to dictionary
            metrics_dict = {}
            for metric, value in metrics.items():
                if isinstance(value, (int, float, str, bool)):
                    metrics_dict[metric] = value
                elif hasattr(value, 'item'):
                    # Convert numpy types to Python types
                    metrics_dict[metric] = value.item()
                else:
                    # Convert other types to string
                    metrics_dict[metric] = str(value)

            # Add additional metrics
            metrics_dict['symbol'] = symbol
            metrics_dict['strategy_id'] = strategy_id
            metrics_dict['start_date'] = self.start_date
            metrics_dict['end_date'] = self.end_date
            metrics_dict['initial_capital'] = self.initial_capital
            metrics_dict['final_capital'] = portfolio.final_value()
            metrics_dict['total_return_pct'] = (portfolio.final_value() / self.initial_capital - 1) * 100
            metrics_dict['max_drawdown_pct'] = portfolio.max_drawdown() * 100
            metrics_dict['sharpe_ratio'] = portfolio.sharpe_ratio()
            metrics_dict['win_rate'] = portfolio.win_rate() * 100 if hasattr(portfolio, 'win_rate') else None
            metrics_dict['profit_factor'] = portfolio.profit_factor() if hasattr(portfolio, 'profit_factor') else None

            # Save results
            self._save_results(metrics_dict)

            logger.info(f"Backtest completed for {symbol} with {strategy_id}")
            return {'success': True, 'metrics': metrics_dict}
        except Exception as e:
            logger.error(f"Error running backtest for {symbol} with {strategy_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _save_results(self, results: Dict[str, Any]) -> None:
        """
        Save backtest results to file.

        Args:
            results: Dictionary with backtest results
        """
        try:
            # Generate filename
            symbol = results.get('symbol', 'unknown')
            strategy_id = results.get('strategy_id', 'unknown')
            timestamp = int(datetime.now().timestamp())
            filename = f"{timestamp}_{symbol}_{strategy_id}.json"

            # Create file path
            file_path = os.path.join(self.output_dir, filename)

            # Save results to file
            with open(file_path, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'results': results
                }, f, indent=2)

            logger.info(f"Saved backtest results to {file_path}")
        except Exception as e:
            logger.error(f"Error saving backtest results: {str(e)}")

    def run_parameter_sweep(self, symbol: str, strategy_id: str, params: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Run a parameter sweep for a strategy.

        Args:
            symbol: Symbol to backtest (e.g., 'SOL-USD')
            strategy_id: Strategy ID to backtest
            params: Dictionary of parameters to sweep

        Returns:
            List of dictionaries with backtest results
        """
        # TODO: Implement parameter sweep
        pass
