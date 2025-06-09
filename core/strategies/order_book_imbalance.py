#!/usr/bin/env python3
"""
Order Book Imbalance Strategy

This module provides an order book imbalance trading strategy.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "pandas"])
    import numpy as np
    import pandas as pd

# Import base strategy
from core.strategies.base import BaseStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrderBookImbalanceStrategy(BaseStrategy):
    """Order book imbalance trading strategy."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy.
        
        Args:
            config: Strategy configuration
        """
        super().__init__(config)
        
        # Initialize imbalance history
        self.imbalance_history = {}
        
        # Initialize parameters
        self.window_size = self.parameters.get("window_size", 20)
        self.threshold = self.parameters.get("threshold", 0.1)
        self.max_value = self.parameters.get("max_value", 0.5)
        self.depth = self.parameters.get("depth", 10)
        self.smoothing_factor = self.parameters.get("smoothing_factor", 0.2)
        
        logger.info(f"Initialized order book imbalance strategy: {self.name}")
    
    def generate_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signals.
        
        Args:
            market_data: Market data
            
        Returns:
            Dict[str, Any]: Trading signals
        """
        signals = {}
        
        # Generate signals for each market
        for market in self.markets:
            try:
                # Get order book
                order_book = self.get_order_book(market_data, market)
                
                if not order_book:
                    continue
                
                # Calculate order book imbalance
                imbalance = self._calculate_imbalance(order_book)
                
                # Update imbalance history
                if market not in self.imbalance_history:
                    self.imbalance_history[market] = []
                
                self.imbalance_history[market].append(imbalance)
                
                # Limit imbalance history to window size
                if len(self.imbalance_history[market]) > self.window_size:
                    self.imbalance_history[market].pop(0)
                
                # Calculate smoothed imbalance
                smoothed_imbalance = self._calculate_smoothed_imbalance(market)
                
                # Calculate signal strength
                signal_strength = self.calculate_signal_strength(smoothed_imbalance, self.threshold, self.max_value)
                
                # Update signals
                signals[market] = signal_strength
            except Exception as e:
                logger.error(f"Error generating signals for {market}: {str(e)}")
        
        # Calculate confidence
        confidence = self.calculate_confidence(signals)
        
        # Calculate position size
        position_size = self.calculate_position_size(signals, confidence, self.parameters.get("max_position_size", 1.0))
        
        return {
            "signals": signals,
            "confidence": confidence,
            "position_size": position_size,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _calculate_imbalance(self, order_book: Dict[str, Any]) -> float:
        """
        Calculate order book imbalance.
        
        Args:
            order_book: Order book
            
        Returns:
            float: Order book imbalance
        """
        # Get bids and asks
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])
        
        if not bids or not asks:
            return 0.0
        
        # Limit to specified depth
        bids = bids[:self.depth]
        asks = asks[:self.depth]
        
        # Calculate bid and ask liquidity
        bid_liquidity = sum(bid["price"] * bid["size"] for bid in bids)
        ask_liquidity = sum(ask["price"] * ask["size"] for ask in asks)
        
        # Calculate imbalance
        total_liquidity = bid_liquidity + ask_liquidity
        
        if total_liquidity <= 0:
            return 0.0
        
        imbalance = (bid_liquidity - ask_liquidity) / total_liquidity
        
        return imbalance
    
    def _calculate_smoothed_imbalance(self, market: str) -> float:
        """
        Calculate smoothed imbalance for a market.
        
        Args:
            market: Market symbol
            
        Returns:
            float: Smoothed imbalance
        """
        if market not in self.imbalance_history or not self.imbalance_history[market]:
            return 0.0
        
        # Get imbalance history
        imbalances = self.imbalance_history[market]
        
        # Calculate smoothed imbalance (exponentially weighted moving average)
        smoothed_imbalance = 0.0
        weight_sum = 0.0
        
        for i, imbalance in enumerate(imbalances):
            weight = (1 - self.smoothing_factor) ** (len(imbalances) - i - 1)
            smoothed_imbalance += weight * imbalance
            weight_sum += weight
        
        if weight_sum > 0:
            smoothed_imbalance /= weight_sum
        
        return smoothed_imbalance
