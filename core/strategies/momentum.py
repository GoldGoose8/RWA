#!/usr/bin/env python3
"""
Momentum Strategy

This module provides a momentum trading strategy.
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

class MomentumStrategy(BaseStrategy):
    """Momentum trading strategy."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy.
        
        Args:
            config: Strategy configuration
        """
        super().__init__(config)
        
        # Initialize price history
        self.price_history = {}
        
        # Initialize parameters
        self.window_size = self.parameters.get("window_size", 20)
        self.threshold = self.parameters.get("threshold", 0.01)
        self.max_value = self.parameters.get("max_value", 0.05)
        self.smoothing_factor = self.parameters.get("smoothing_factor", 0.1)
        
        logger.info(f"Initialized momentum strategy: {self.name}")
    
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
                
                # Get mid price
                mid_price = self.get_mid_price(order_book)
                
                if mid_price <= 0:
                    continue
                
                # Update price history
                if market not in self.price_history:
                    self.price_history[market] = []
                
                self.price_history[market].append(mid_price)
                
                # Limit price history to window size
                if len(self.price_history[market]) > self.window_size:
                    self.price_history[market].pop(0)
                
                # Calculate momentum
                momentum = self._calculate_momentum(market)
                
                # Calculate signal strength
                signal_strength = self.calculate_signal_strength(momentum, self.threshold, self.max_value)
                
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
    
    def _calculate_momentum(self, market: str) -> float:
        """
        Calculate momentum for a market.
        
        Args:
            market: Market symbol
            
        Returns:
            float: Momentum
        """
        if market not in self.price_history or len(self.price_history[market]) < 2:
            return 0.0
        
        # Get price history
        prices = self.price_history[market]
        
        # Calculate returns
        returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
        
        # Calculate momentum (exponentially weighted moving average of returns)
        momentum = 0.0
        weight_sum = 0.0
        
        for i, ret in enumerate(returns):
            weight = (1 - self.smoothing_factor) ** (len(returns) - i - 1)
            momentum += weight * ret
            weight_sum += weight
        
        if weight_sum > 0:
            momentum /= weight_sum
        
        return momentum
