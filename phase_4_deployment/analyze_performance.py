#!/usr/bin/env python3
"""
Analyze Performance

This script analyzes the performance of the trading strategies.
"""

import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analyzer for trading strategy performance."""

    def __init__(self, data_dir: str = "phase_0_env_setup/data/historical"):
        """
        Initialize the performance analyzer.

        Args:
            data_dir: Directory containing historical data
        """
        self.data_dir = data_dir

        # Create output directory
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"Initialized performance analyzer with data directory: {data_dir}")
        logger.info(f"Output directory: {self.output_dir}")

    def load_historical_data(self, market: str, interval: str = "1d") -> pd.DataFrame:
        """
        Load historical data for a market.

        Args:
            market: Market symbol
            interval: Time interval

        Returns:
            pd.DataFrame: Historical data
        """
        try:
            # Get file path
            file_path = os.path.join(
                self.data_dir,
                f"{market.replace('-', '_').lower()}_{interval}.csv",
            )

            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"Historical data file not found: {file_path}")
                return pd.DataFrame()

            # Load data
            df = pd.read_csv(file_path, parse_dates=["timestamp"])

            logger.info(f"Loaded {len(df)} rows of historical data for {market}")

            return df
        except Exception as e:
            logger.error(f"Error loading historical data for {market}: {str(e)}")
            return pd.DataFrame()

    def analyze_momentum_strategy(
        self,
        df: pd.DataFrame,
        window_size: int = 20,
        threshold: float = 0.01,
        max_value: float = 0.05,
        smoothing_factor: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Analyze momentum strategy performance.

        Args:
            df: Historical data
            window_size: Window size for momentum calculation
            threshold: Signal threshold
            max_value: Maximum signal value
            smoothing_factor: Smoothing factor for momentum calculation

        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            # Calculate returns
            df["returns"] = df["close"].pct_change()

            # Calculate momentum
            df["momentum"] = df["returns"].ewm(span=window_size, adjust=False).mean()

            # Calculate signal
            df["signal"] = 0.0
            df.loc[df["momentum"] > threshold, "signal"] = 1.0
            df.loc[df["momentum"] < -threshold, "signal"] = -1.0

            # Calculate strategy returns
            df["strategy_returns"] = df["signal"].shift(1) * df["returns"]

            # Calculate cumulative returns
            df["cumulative_returns"] = (1 + df["returns"]).cumprod() - 1
            df["strategy_cumulative_returns"] = (1 + df["strategy_returns"]).cumprod() - 1

            # Calculate metrics
            total_return = df["strategy_cumulative_returns"].iloc[-1]
            annualized_return = (1 + total_return) ** (252 / len(df)) - 1
            sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252) if df["strategy_returns"].std() > 0 else 0
            max_drawdown = (df["strategy_cumulative_returns"] - df["strategy_cumulative_returns"].cummax()).min()
            win_rate = len(df[df["strategy_returns"] > 0]) / len(df[df["strategy_returns"] != 0]) if len(df[df["strategy_returns"] != 0]) > 0 else 0

            # Create metrics dictionary
            metrics = {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
            }

            logger.info(f"Momentum strategy metrics: {metrics}")

            return metrics
        except Exception as e:
            logger.error(f"Error analyzing momentum strategy: {str(e)}")
            return {}

    def analyze_order_book_imbalance_strategy(
        self,
        df: pd.DataFrame,
        window_size: int = 20,
        threshold: float = 0.1,
        max_value: float = 0.5,
        depth: int = 10,
        smoothing_factor: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Analyze order book imbalance strategy performance.

        Args:
            df: Historical data
            window_size: Window size for imbalance calculation
            threshold: Signal threshold
            max_value: Maximum signal value
            depth: Order book depth
            smoothing_factor: Smoothing factor for imbalance calculation

        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            # Calculate returns
            df["returns"] = df["close"].pct_change()

            # Simulate order book imbalance (we don't have real order book data)
            np.random.seed(42)  # For reproducibility
            df["imbalance"] = np.random.normal(0, 0.1, len(df))

            # Calculate smoothed imbalance
            df["smoothed_imbalance"] = df["imbalance"].ewm(span=window_size, adjust=False).mean()

            # Calculate signal
            df["signal"] = 0.0
            df.loc[df["smoothed_imbalance"] > threshold, "signal"] = 1.0
            df.loc[df["smoothed_imbalance"] < -threshold, "signal"] = -1.0

            # Calculate strategy returns
            df["strategy_returns"] = df["signal"].shift(1) * df["returns"]

            # Calculate cumulative returns
            df["cumulative_returns"] = (1 + df["returns"]).cumprod() - 1
            df["strategy_cumulative_returns"] = (1 + df["strategy_returns"]).cumprod() - 1

            # Calculate metrics
            total_return = df["strategy_cumulative_returns"].iloc[-1]
            annualized_return = (1 + total_return) ** (252 / len(df)) - 1
            sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252) if df["strategy_returns"].std() > 0 else 0
            max_drawdown = (df["strategy_cumulative_returns"] - df["strategy_cumulative_returns"].cummax()).min()
            win_rate = len(df[df["strategy_returns"] > 0]) / len(df[df["strategy_returns"] != 0]) if len(df[df["strategy_returns"] != 0]) > 0 else 0

            # Create metrics dictionary
            metrics = {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
            }

            logger.info(f"Order book imbalance strategy metrics: {metrics}")

            return metrics
        except Exception as e:
            logger.error(f"Error analyzing order book imbalance strategy: {str(e)}")
            return {}

    def plot_returns(
        self,
        df: pd.DataFrame,
        market: str,
        strategy_name: str,
    ) -> str:
        """
        Plot strategy returns.

        Args:
            df: Historical data with strategy returns
            market: Market symbol
            strategy_name: Strategy name

        Returns:
            str: Path to the plot file
        """
        try:
            # Create figure
            plt.figure(figsize=(12, 8))

            # Plot cumulative returns
            plt.plot(df["timestamp"], df["cumulative_returns"], label="Buy and Hold")
            plt.plot(df["timestamp"], df["strategy_cumulative_returns"], label=strategy_name)

            # Add labels and title
            plt.xlabel("Date")
            plt.ylabel("Cumulative Returns")
            plt.title(f"{strategy_name} vs Buy and Hold ({market})")
            plt.legend()
            plt.grid(True)

            # Save figure
            plot_path = os.path.join(self.output_dir, f"{market.replace('-', '_').lower()}_{strategy_name.lower()}_returns.png")
            plt.savefig(plot_path)
            plt.close()

            logger.info(f"Saved returns plot to {plot_path}")

            return plot_path
        except Exception as e:
            logger.error(f"Error plotting returns: {str(e)}")
            return ""

    def analyze_strategy(
        self,
        market: str,
        strategy_type: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze a strategy.

        Args:
            market: Market symbol
            strategy_type: Strategy type
            parameters: Strategy parameters

        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            # Load historical data
            df = self.load_historical_data(market)

            if df.empty:
                logger.error(f"No historical data found for {market}")
                return {}

            # Analyze strategy
            if strategy_type == "momentum":
                metrics = self.analyze_momentum_strategy(
                    df,
                    window_size=parameters.get("window_size", 20),
                    threshold=parameters.get("threshold", 0.01),
                    max_value=parameters.get("max_value", 0.05),
                    smoothing_factor=parameters.get("smoothing_factor", 0.1),
                )

                # Plot returns
                self.plot_returns(df, market, "Momentum")
            elif strategy_type == "order_book_imbalance":
                metrics = self.analyze_order_book_imbalance_strategy(
                    df,
                    window_size=parameters.get("window_size", 20),
                    threshold=parameters.get("threshold", 0.1),
                    max_value=parameters.get("max_value", 0.5),
                    depth=parameters.get("depth", 10),
                    smoothing_factor=parameters.get("smoothing_factor", 0.2),
                )

                # Plot returns
                self.plot_returns(df, market, "Order Book Imbalance")
            else:
                logger.error(f"Unknown strategy type: {strategy_type}")
                return {}

            return metrics
        except Exception as e:
            logger.error(f"Error analyzing strategy: {str(e)}")
            return {}

    def analyze_strategies(self, config_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all strategies in a configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dict[str, Dict[str, Any]]: Performance metrics for each strategy
        """
        try:
            # Load configuration
            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            logger.info(f"Loaded configuration from {config_path}")

            # Get strategies
            strategies = config.get("strategies", [])

            if not strategies:
                logger.error("No strategies found in configuration")
                return {}

            # Analyze each strategy
            metrics = {}

            for strategy in strategies:
                strategy_name = strategy.get("name")
                strategy_type = strategy.get("type")
                strategy_markets = strategy.get("markets", [])
                strategy_parameters = strategy.get("parameters", {})

                if not strategy_name or not strategy_type or not strategy_markets:
                    logger.warning(f"Invalid strategy: {strategy}")
                    continue

                logger.info(f"Analyzing strategy: {strategy_name}")

                # Analyze strategy for each market
                strategy_metrics = {}

                for market in strategy_markets:
                    logger.info(f"Analyzing strategy {strategy_name} for market {market}")

                    market_metrics = self.analyze_strategy(
                        market=market,
                        strategy_type=strategy_type,
                        parameters=strategy_parameters,
                    )

                    if market_metrics:
                        strategy_metrics[market] = market_metrics

                metrics[strategy_name] = strategy_metrics

            # Save metrics to file
            metrics_path = os.path.join(self.output_dir, "strategy_metrics.json")

            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)

            logger.info(f"Saved strategy metrics to {metrics_path}")

            return metrics
        except Exception as e:
            logger.error(f"Error analyzing strategies: {str(e)}")
            return {}

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze trading strategy performance")
    parser.add_argument("--config", default="phase_4_deployment/test_config.yaml", help="Path to configuration file")
    parser.add_argument("--data-dir", default="phase_0_env_setup/data/historical", help="Directory containing historical data")

    args = parser.parse_args()

    # Create performance analyzer
    analyzer = PerformanceAnalyzer(data_dir=args.data_dir)

    # Analyze strategies
    metrics = analyzer.analyze_strategies(config_path=args.config)

    # Print metrics
    for strategy_name, strategy_metrics in metrics.items():
        print(f"\nStrategy: {strategy_name}")

        for market, market_metrics in strategy_metrics.items():
            print(f"  Market: {market}")

            for metric_name, metric_value in market_metrics.items():
                print(f"    {metric_name}: {metric_value:.4f}")

if __name__ == "__main__":
    main()
