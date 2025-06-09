#!/usr/bin/env python3
"""
Optimize Strategies

This script optimizes the trading strategies using historical data.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import yaml
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "numpy", "pandas", "scipy"])
    import yaml
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StrategyOptimizer:
    """Optimizer for trading strategies."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the strategy optimizer.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.strategies = self.config.get("strategies", [])
        self.markets = self.config.get("market_microstructure", {}).get("markets", [])
        self.historical_data = {}
        
        logger.info("Initialized strategy optimizer")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration
        """
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}
    
    def _save_config(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup of original config
            backup_path = f"{self.config_path}.bak"
            with open(self.config_path, "r") as f_in:
                with open(backup_path, "w") as f_out:
                    f_out.write(f_in.read())
            
            # Save updated config
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    async def load_historical_data(self, days: int = 30) -> bool:
        """
        Load historical data for all markets.
        
        Args:
            days: Number of days of historical data to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading historical data for the last {days} days...")
            
            # Calculate start and end dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Load historical data for each market
            for market in self.markets:
                logger.info(f"Loading historical data for {market}...")
                
                # Get historical data path
                data_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "phase_0_env_setup",
                    "data",
                    "historical",
                    f"{market.replace('-', '_').lower()}_1d.csv",
                )
                
                # Check if historical data exists
                if not os.path.exists(data_path):
                    logger.warning(f"Historical data not found for {market}: {data_path}")
                    
                    # Download historical data
                    await self._download_historical_data(market, start_date, end_date)
                
                # Load historical data
                try:
                    df = pd.read_csv(data_path, parse_dates=["timestamp"])
                    
                    # Filter data by date range
                    df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]
                    
                    # Store historical data
                    self.historical_data[market] = df
                    
                    logger.info(f"Loaded {len(df)} rows of historical data for {market}")
                except Exception as e:
                    logger.error(f"Error loading historical data for {market}: {str(e)}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return False
    
    async def _download_historical_data(self, market: str, start_date: datetime, end_date: datetime) -> bool:
        """
        Download historical data for a market.
        
        Args:
            market: Market symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading historical data for {market}...")
            
            # Get base and quote tokens
            base_token, quote_token = market.split("-")
            
            # Get historical data path
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "phase_0_env_setup",
                "data",
                "historical",
            )
            
            # Create directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            
            # Get data path
            data_path = os.path.join(
                data_dir,
                f"{market.replace('-', '_').lower()}_1d.csv",
            )
            
            # Get API key
            api_key = self.config.get("apis", {}).get("birdeye", {}).get("api_key", "")
            
            if not api_key:
                logger.error("Birdeye API key not found in configuration")
                return False
            
            # Get token addresses
            base_address = self._get_token_address(base_token)
            quote_address = self._get_token_address(quote_token)
            
            if not base_address or not quote_address:
                logger.error(f"Could not find token addresses for {market}")
                return False
            
            # Download historical data
            import httpx
            
            # Format dates
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            # Prepare request
            url = "https://api.birdeye.so/v1/defi/history"
            params = {
                "address": base_address,
                "type": "1D",
                "vsToken": quote_address,
                "fromTimestamp": start_timestamp,
                "toTimestamp": end_timestamp,
            }
            headers = {
                "X-API-KEY": api_key,
            }
            
            # Send request
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                if not data.get("success", False):
                    logger.error(f"Error downloading historical data for {market}: {data.get('message', 'Unknown error')}")
                    return False
                
                # Extract historical data
                items = data.get("data", {}).get("items", [])
                
                if not items:
                    logger.warning(f"No historical data found for {market}")
                    return False
                
                # Create dataframe
                df = pd.DataFrame(items)
                
                # Convert timestamp to datetime
                df["timestamp"] = pd.to_datetime(df["unixTime"], unit="s")
                
                # Save to CSV
                df.to_csv(data_path, index=False)
                
                logger.info(f"Downloaded {len(df)} rows of historical data for {market}")
                
                return True
        except Exception as e:
            logger.error(f"Error downloading historical data for {market}: {str(e)}")
            return False
    
    def _get_token_address(self, token: str) -> str:
        """
        Get token address.
        
        Args:
            token: Token symbol
            
        Returns:
            str: Token address
        """
        # Common token addresses
        token_addresses = {
            "SOL": "So11111111111111111111111111111111111111112",
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
            "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        }
        
        return token_addresses.get(token.upper(), token)
    
    def optimize_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """
        Optimize a strategy.
        
        Args:
            strategy_name: Strategy name
            
        Returns:
            Dict[str, Any]: Optimized strategy parameters
        """
        try:
            logger.info(f"Optimizing strategy: {strategy_name}")
            
            # Find strategy in configuration
            strategy = None
            
            for s in self.strategies:
                if s.get("name") == strategy_name:
                    strategy = s
                    break
            
            if not strategy:
                logger.error(f"Strategy not found: {strategy_name}")
                return {}
            
            # Get strategy type
            strategy_type = strategy.get("type")
            
            if not strategy_type:
                logger.error(f"Strategy type not found for {strategy_name}")
                return {}
            
            # Get strategy markets
            strategy_markets = strategy.get("markets", [])
            
            if not strategy_markets:
                logger.error(f"No markets found for strategy {strategy_name}")
                return {}
            
            # Get strategy parameters
            parameters = strategy.get("parameters", {})
            
            if not parameters:
                logger.error(f"No parameters found for strategy {strategy_name}")
                return {}
            
            # Optimize parameters for each market
            optimized_parameters = {}
            
            for market in strategy_markets:
                # Check if historical data is available
                if market not in self.historical_data:
                    logger.warning(f"No historical data found for {market}, skipping optimization")
                    continue
                
                # Get historical data
                df = self.historical_data[market]
                
                # Optimize parameters for this market
                if strategy_type == "momentum":
                    optimized_params = self._optimize_momentum_strategy(df, parameters)
                elif strategy_type == "order_book_imbalance":
                    optimized_params = self._optimize_order_book_imbalance_strategy(df, parameters)
                else:
                    logger.warning(f"Unknown strategy type: {strategy_type}, skipping optimization")
                    continue
                
                # Store optimized parameters
                optimized_parameters[market] = optimized_params
                
                logger.info(f"Optimized parameters for {strategy_name} on {market}: {optimized_params}")
            
            # Calculate average optimized parameters
            avg_params = {}
            
            for param_name in parameters.keys():
                values = [params.get(param_name) for params in optimized_parameters.values() if param_name in params]
                
                if values:
                    avg_params[param_name] = sum(values) / len(values)
            
            logger.info(f"Average optimized parameters for {strategy_name}: {avg_params}")
            
            return avg_params
        except Exception as e:
            logger.error(f"Error optimizing strategy {strategy_name}: {str(e)}")
            return {}
    
    def _optimize_momentum_strategy(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize momentum strategy parameters.
        
        Args:
            df: Historical data
            parameters: Strategy parameters
            
        Returns:
            Dict[str, Any]: Optimized parameters
        """
        try:
            # Define objective function
            def objective(params):
                window_size = int(params[0])
                threshold = params[1]
                max_value = params[2]
                smoothing_factor = params[3]
                
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
                
                # Calculate Sharpe ratio
                sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252)
                
                # Return negative Sharpe ratio (we want to maximize it)
                return -sharpe_ratio
            
            # Define bounds
            bounds = [
                (10, 50),  # window_size
                (0.001, 0.1),  # threshold
                (0.01, 0.2),  # max_value
                (0.05, 0.5),  # smoothing_factor
            ]
            
            # Define initial parameters
            initial_params = [
                parameters.get("window_size", 20),
                parameters.get("threshold", 0.01),
                parameters.get("max_value", 0.05),
                parameters.get("smoothing_factor", 0.1),
            ]
            
            # Run optimization
            result = minimize(
                objective,
                initial_params,
                bounds=bounds,
                method="L-BFGS-B",
            )
            
            # Extract optimized parameters
            optimized_params = {
                "window_size": int(result.x[0]),
                "threshold": result.x[1],
                "max_value": result.x[2],
                "smoothing_factor": result.x[3],
            }
            
            return optimized_params
        except Exception as e:
            logger.error(f"Error optimizing momentum strategy: {str(e)}")
            return parameters
    
    def _optimize_order_book_imbalance_strategy(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize order book imbalance strategy parameters.
        
        Args:
            df: Historical data
            parameters: Strategy parameters
            
        Returns:
            Dict[str, Any]: Optimized parameters
        """
        try:
            # Define objective function
            def objective(params):
                window_size = int(params[0])
                threshold = params[1]
                max_value = params[2]
                depth = int(params[3])
                smoothing_factor = params[4]
                
                # Calculate returns
                df["returns"] = df["close"].pct_change()
                
                # Simulate order book imbalance (we don't have real order book data)
                df["imbalance"] = np.random.normal(0, 0.1, len(df))
                
                # Calculate smoothed imbalance
                df["smoothed_imbalance"] = df["imbalance"].ewm(span=window_size, adjust=False).mean()
                
                # Calculate signal
                df["signal"] = 0.0
                df.loc[df["smoothed_imbalance"] > threshold, "signal"] = 1.0
                df.loc[df["smoothed_imbalance"] < -threshold, "signal"] = -1.0
                
                # Calculate strategy returns
                df["strategy_returns"] = df["signal"].shift(1) * df["returns"]
                
                # Calculate Sharpe ratio
                sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252)
                
                # Return negative Sharpe ratio (we want to maximize it)
                return -sharpe_ratio
            
            # Define bounds
            bounds = [
                (10, 50),  # window_size
                (0.05, 0.5),  # threshold
                (0.1, 1.0),  # max_value
                (5, 20),  # depth
                (0.05, 0.5),  # smoothing_factor
            ]
            
            # Define initial parameters
            initial_params = [
                parameters.get("window_size", 20),
                parameters.get("threshold", 0.1),
                parameters.get("max_value", 0.5),
                parameters.get("depth", 10),
                parameters.get("smoothing_factor", 0.2),
            ]
            
            # Run optimization
            result = minimize(
                objective,
                initial_params,
                bounds=bounds,
                method="L-BFGS-B",
            )
            
            # Extract optimized parameters
            optimized_params = {
                "window_size": int(result.x[0]),
                "threshold": result.x[1],
                "max_value": result.x[2],
                "depth": int(result.x[3]),
                "smoothing_factor": result.x[4],
            }
            
            return optimized_params
        except Exception as e:
            logger.error(f"Error optimizing order book imbalance strategy: {str(e)}")
            return parameters
    
    async def optimize_all_strategies(self) -> bool:
        """
        Optimize all strategies.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Optimizing all strategies...")
            
            # Load historical data
            success = await self.load_historical_data()
            
            if not success:
                logger.error("Failed to load historical data")
                return False
            
            # Optimize each strategy
            for strategy in self.strategies:
                strategy_name = strategy.get("name")
                
                if not strategy_name:
                    logger.warning("Strategy name not found, skipping")
                    continue
                
                # Optimize strategy
                optimized_params = self.optimize_strategy(strategy_name)
                
                if not optimized_params:
                    logger.warning(f"Failed to optimize strategy {strategy_name}, skipping")
                    continue
                
                # Update strategy parameters
                strategy["parameters"] = optimized_params
            
            # Save updated configuration
            success = self._save_config()
            
            if not success:
                logger.error("Failed to save updated configuration")
                return False
            
            logger.info("All strategies optimized successfully")
            return True
        except Exception as e:
            logger.error(f"Error optimizing all strategies: {str(e)}")
            return False

async def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Optimize trading strategies")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--strategy", help="Optimize a specific strategy")
    
    args = parser.parse_args()
    
    # Create strategy optimizer
    optimizer = StrategyOptimizer(config_path=args.config)
    
    # Optimize strategies
    if args.strategy:
        # Optimize a specific strategy
        await optimizer.load_historical_data()
        optimizer.optimize_strategy(args.strategy)
    else:
        # Optimize all strategies
        await optimizer.optimize_all_strategies()

if __name__ == "__main__":
    asyncio.run(main())
