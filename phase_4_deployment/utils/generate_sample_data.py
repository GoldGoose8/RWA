#!/usr/bin/env python3
"""
Generate Sample Data

This script generates sample historical data for testing.
"""

import os
import sys
import json
import logging
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_ohlcv_data(
    market: str,
    start_date: datetime,
    end_date: datetime,
    interval: str = "1d",
    initial_price: float = 100.0,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """
    Generate sample OHLCV data.
    
    Args:
        market: Market symbol
        start_date: Start date
        end_date: End date
        interval: Time interval
        initial_price: Initial price
        volatility: Price volatility
        
    Returns:
        pd.DataFrame: OHLCV data
    """
    try:
        logger.info(f"Generating sample OHLCV data for {market} from {start_date} to {end_date}")
        
        # Calculate number of periods
        if interval == "1d":
            delta = timedelta(days=1)
        elif interval == "1h":
            delta = timedelta(hours=1)
        elif interval == "1m":
            delta = timedelta(minutes=1)
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        # Generate timestamps
        timestamps = []
        current_date = start_date
        while current_date <= end_date:
            timestamps.append(current_date)
            current_date += delta
        
        # Generate prices using geometric Brownian motion
        np.random.seed(42)  # For reproducibility
        returns = np.random.normal(0, volatility, len(timestamps))
        price_changes = np.exp(returns)
        prices = initial_price * np.cumprod(price_changes)
        
        # Generate OHLCV data
        data = []
        
        for i, timestamp in enumerate(timestamps):
            # Calculate price
            price = prices[i]
            
            # Generate random OHLCV data
            open_price = price * (1 + random.uniform(-0.005, 0.005))
            high_price = price * (1 + random.uniform(0, 0.01))
            low_price = price * (1 - random.uniform(0, 0.01))
            close_price = price
            volume = random.uniform(1000, 10000)
            
            # Add to data
            data.append({
                "timestamp": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
                "unixTime": int(timestamp.timestamp()),
            })
        
        # Create dataframe
        df = pd.DataFrame(data)
        
        logger.info(f"Generated {len(df)} rows of sample OHLCV data for {market}")
        
        return df
    except Exception as e:
        logger.error(f"Error generating sample OHLCV data for {market}: {str(e)}")
        raise

def save_ohlcv_data(df: pd.DataFrame, market: str, interval: str = "1d") -> str:
    """
    Save OHLCV data to a file.
    
    Args:
        df: OHLCV data
        market: Market symbol
        interval: Time interval
        
    Returns:
        str: File path
    """
    try:
        # Create directory if it doesn't exist
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "phase_0_env_setup",
            "data",
            "historical",
        )
        os.makedirs(data_dir, exist_ok=True)
        
        # Save to CSV
        file_path = os.path.join(
            data_dir,
            f"{market.replace('-', '_').lower()}_{interval}.csv",
        )
        df.to_csv(file_path, index=False)
        
        logger.info(f"Saved OHLCV data to {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving OHLCV data for {market}: {str(e)}")
        raise

def main():
    """Main function."""
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample historical data for testing")
    parser.add_argument("--markets", nargs="+", default=["SOL-USDC", "JTO-USDC", "BONK-USDC"], help="Markets to generate data for")
    parser.add_argument("--days", type=int, default=30, help="Number of days of historical data to generate")
    parser.add_argument("--interval", default="1d", choices=["1d", "1h", "1m"], help="Time interval")
    
    args = parser.parse_args()
    
    try:
        # Calculate start and end dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        # Generate and save data for each market
        for market in args.markets:
            # Set initial price based on market
            if market == "SOL-USDC":
                initial_price = 150.0
                volatility = 0.02
            elif market == "JTO-USDC":
                initial_price = 2.5
                volatility = 0.03
            elif market == "BONK-USDC":
                initial_price = 0.00002
                volatility = 0.05
            else:
                initial_price = 100.0
                volatility = 0.02
            
            # Generate OHLCV data
            df = generate_ohlcv_data(
                market=market,
                start_date=start_date,
                end_date=end_date,
                interval=args.interval,
                initial_price=initial_price,
                volatility=volatility,
            )
            
            # Save OHLCV data
            save_ohlcv_data(df, market, args.interval)
        
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
