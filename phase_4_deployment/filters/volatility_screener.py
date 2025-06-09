#!/usr/bin/env python3
"""
Volatility Screener Filter Module

This module provides a filter that screens signals based on market volatility
to avoid high-wick traps and excessive price swings.
"""

import os
import sys
import json
import time
import logging
import asyncio
import httpx
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import base filter
from phase_4_deployment.filters.base_filter import BaseFilter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('volatility_screener')

class VolatilityScreener(BaseFilter):
    """
    Filter that screens signals based on market volatility.
    
    This filter checks if a market has acceptable volatility levels
    to avoid high-wick traps and excessive price swings.
    """
    
    def __init__(self, config: Dict[str, Any] = None, cache_ttl: int = 300):
        """
        Initialize the volatility screener filter.
        
        Args:
            config: Filter configuration
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        super().__init__(config, cache_ttl)
        
        # Load configuration
        self.max_volatility = self.config.get('max_volatility', 0.05)  # 5%
        self.wick_threshold = self.config.get('wick_threshold', 0.02)  # 2%
        self.lookback_periods = self.config.get('lookback_periods', [1, 4, 24])  # hours
        
        # Load API configuration
        self.birdeye_api_key = os.environ.get('BIRDEYE_API_KEY', '')
        self.birdeye_endpoint = self.config.get('birdeye_endpoint', 'https://api.birdeye.so/v1')
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Initialized VolatilityScreener with max_volatility={self.max_volatility}, "
                   f"wick_threshold={self.wick_threshold}")
    
    async def get_historical_prices(self, token_address: str, interval: str = '1H', limit: int = 24) -> List[Dict[str, Any]]:
        """
        Get historical price data for a token.
        
        Args:
            token_address: Token address to check
            interval: Time interval (1H, 4H, 1D, etc.)
            limit: Number of data points to retrieve
            
        Returns:
            List of price data points
        """
        # Check cache first
        cache_key = f"prices_{token_address}_{interval}_{limit}"
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Query Birdeye API for historical prices
            url = f"{self.birdeye_endpoint}/defi/ohlcv"
            
            params = {
                "address": token_address,
                "type": "token",
                "interval": interval,
                "limit": limit
            }
            
            headers = {
                "X-API-KEY": self.birdeye_api_key
            }
            
            response = await self.http_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract price data
            price_data = []
            
            if 'data' in data and 'items' in data['data']:
                price_data = data['data']['items']
            
            # Cache the results
            self.set_in_cache(cache_key, price_data)
            
            return price_data
        except Exception as e:
            logger.error(f"Error getting historical prices for {token_address}: {str(e)}")
            return []
    
    def calculate_volatility(self, price_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate volatility metrics from price data.
        
        Args:
            price_data: List of price data points
            
        Returns:
            Dictionary of volatility metrics
        """
        if not price_data:
            return {
                "volatility": 0,
                "wick_ratio": 0,
                "price_range": 0,
                "avg_volume": 0
            }
        
        # Extract OHLCV data
        opens = np.array([float(item.get('o', 0)) for item in price_data])
        highs = np.array([float(item.get('h', 0)) for item in price_data])
        lows = np.array([float(item.get('l', 0)) for item in price_data])
        closes = np.array([float(item.get('c', 0)) for item in price_data])
        volumes = np.array([float(item.get('v', 0)) for item in price_data])
        
        # Calculate returns
        returns = np.diff(np.log(closes)) if len(closes) > 1 else np.array([0])
        
        # Calculate volatility (standard deviation of returns)
        volatility = np.std(returns)
        
        # Calculate price range
        price_range = (np.max(highs) - np.min(lows)) / np.mean(closes) if np.mean(closes) > 0 else 0
        
        # Calculate wick ratio (average ratio of wick to body)
        body_sizes = np.abs(closes - opens)
        wick_sizes = (highs - np.maximum(opens, closes)) + (np.minimum(opens, closes) - lows)
        wick_ratio = np.mean(wick_sizes / body_sizes) if np.mean(body_sizes) > 0 else 0
        
        # Calculate average volume
        avg_volume = np.mean(volumes)
        
        return {
            "volatility": float(volatility),
            "wick_ratio": float(wick_ratio),
            "price_range": float(price_range),
            "avg_volume": float(avg_volume)
        }
    
    async def calculate_volatility_score(self, token_address: str) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate volatility score for a token.
        
        Args:
            token_address: Token address to check
            
        Returns:
            Tuple of (volatility_score, metadata)
        """
        # Get historical prices for different time periods
        volatility_metrics = {}
        
        for period in self.lookback_periods:
            interval = '1H' if period <= 24 else '4H' if period <= 96 else '1D'
            limit = period if interval == '1H' else period // 4 if interval == '4H' else period // 24
            
            price_data = await self.get_historical_prices(token_address, interval, limit)
            metrics = self.calculate_volatility(price_data)
            
            volatility_metrics[f"{period}h"] = metrics
        
        # Calculate overall volatility score
        # Lower is better (less volatile)
        volatility_scores = [
            1 - min(1, metrics["volatility"] / self.max_volatility)
            for period, metrics in volatility_metrics.items()
        ]
        
        # Calculate wick score
        # Lower is better (fewer wicks)
        wick_scores = [
            1 - min(1, metrics["wick_ratio"] / self.wick_threshold)
            for period, metrics in volatility_metrics.items()
        ]
        
        # Combine scores (weighted average)
        # 70% volatility, 30% wick ratio
        combined_scores = [
            0.7 * vol_score + 0.3 * wick_score
            for vol_score, wick_score in zip(volatility_scores, wick_scores)
        ]
        
        # Use the minimum score across all periods
        # This ensures we reject if any period has high volatility
        volatility_score = min(combined_scores) if combined_scores else 0
        
        # Prepare metadata
        metadata = {
            "volatility_metrics": volatility_metrics,
            "volatility_scores": {f"{period}h": score for period, score in zip(self.lookback_periods, volatility_scores)},
            "wick_scores": {f"{period}h": score for period, score in zip(self.lookback_periods, wick_scores)},
            "combined_scores": {f"{period}h": score for period, score in zip(self.lookback_periods, combined_scores)}
        }
        
        return volatility_score, metadata
    
    async def filter_signal(self, signal: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Filter a signal based on market volatility.
        
        Args:
            signal: Signal to filter
            
        Returns:
            Tuple of (passed_filter, metadata)
        """
        # Extract token address from signal
        token_address = signal.get('token_address')
        
        if not token_address:
            return False, {
                "filter": self.name,
                "status": "rejected",
                "reason": "No token address in signal",
                "volatility_score": 0.0
            }
        
        # Calculate volatility score
        volatility_score, volatility_metadata = await self.calculate_volatility_score(token_address)
        
        # Check if volatility is acceptable
        # Higher score is better (less volatile)
        passed = volatility_score >= 0.5  # At least 50% of the ideal score
        
        # Prepare metadata
        metadata = {
            "filter": self.name,
            "status": "passed" if passed else "rejected",
            "reason": f"Volatility score: {volatility_score:.2f} (min: 0.5)",
            "volatility_score": volatility_score,
            **volatility_metadata
        }
        
        return passed, metadata
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
