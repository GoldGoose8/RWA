#!/usr/bin/env python3
"""
Base Strategy

This module provides a base class for trading strategies.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseStrategy:
    """Base class for trading strategies."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy.

        Args:
            config: Strategy configuration
        """
        self.config = config
        self.name = config.get("name", "")
        self.markets = config.get("markets", [])
        self.parameters = config.get("parameters", {})
        self.state = {}

        logger.info(f"Initialized strategy: {self.name}")

    def generate_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signals.

        Args:
            market_data: Market data

        Returns:
            Dict[str, Any]: Trading signals
        """
        raise NotImplementedError("Subclasses must implement generate_signals()")

    def get_order_book(self, market_data: Dict[str, Any], market: str) -> Dict[str, Any]:
        """
        Get order book for a market.

        Args:
            market_data: Market data
            market: Market symbol

        Returns:
            Dict[str, Any]: Order book
        """
        return market_data.get("order_books", {}).get(market, {})

    def get_transactions(self, market_data: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent transactions.

        Args:
            market_data: Market data
            limit: Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: Transactions
        """
        return market_data.get("transactions", [])[-limit:]

    def get_account(self, market_data: Dict[str, Any], address: str) -> Dict[str, Any]:
        """
        Get account by address.

        Args:
            market_data: Market data
            address: Account address

        Returns:
            Dict[str, Any]: Account
        """
        return market_data.get("accounts", {}).get(address, {})

    def get_mid_price(self, order_book: Dict[str, Any]) -> float:
        """
        Get mid price from order book.

        Args:
            order_book: Order book

        Returns:
            float: Mid price
        """
        metrics = order_book.get("metrics", {})
        return metrics.get("mid_price", 0.0)

    def get_spread(self, order_book: Dict[str, Any]) -> float:
        """
        Get spread from order book.

        Args:
            order_book: Order book

        Returns:
            float: Spread
        """
        metrics = order_book.get("metrics", {})
        return metrics.get("spread", 0.0)

    def get_spread_pct(self, order_book: Dict[str, Any]) -> float:
        """
        Get spread percentage from order book.

        Args:
            order_book: Order book

        Returns:
            float: Spread percentage
        """
        metrics = order_book.get("metrics", {})
        return metrics.get("spread_pct", 0.0)

    def get_bid_ask_imbalance(self, order_book: Dict[str, Any]) -> float:
        """
        Get bid-ask imbalance from order book.

        Args:
            order_book: Order book

        Returns:
            float: Bid-ask imbalance
        """
        metrics = order_book.get("metrics", {})
        return metrics.get("bid_ask_imbalance", 0.0)

    def get_price_impact(self, order_book: Dict[str, Any], size: int, side: str) -> float:
        """
        Get price impact from order book.

        Args:
            order_book: Order book
            size: Order size in USD
            side: Order side ("buy" or "sell")

        Returns:
            float: Price impact
        """
        metrics = order_book.get("metrics", {})
        price_impact = metrics.get("price_impact", {})
        return price_impact.get(str(size), {}).get(side, 0.0)

    def calculate_signal_strength(self, value: float, threshold: float, max_value: float) -> float:
        """
        Calculate signal strength.

        Args:
            value: Signal value
            threshold: Signal threshold
            max_value: Maximum signal value

        Returns:
            float: Signal strength between 0 and 1
        """
        if abs(value) <= threshold:
            return 0.0

        # Normalize value between threshold and max_value
        normalized_value = (abs(value) - threshold) / (max_value - threshold)

        # Clamp between 0 and 1
        normalized_value = max(0.0, min(1.0, normalized_value))

        # Apply sign and round to avoid floating point precision issues
        result = normalized_value if value > 0 else -normalized_value

        # Round to 6 decimal places to avoid floating point precision issues in tests
        return round(result, 6)

    def calculate_confidence(self, signals: Dict[str, float]) -> float:
        """
        Calculate confidence from signals.

        Args:
            signals: Trading signals

        Returns:
            float: Confidence between 0 and 1
        """
        # Calculate average absolute signal strength
        signal_values = [abs(value) for value in signals.values()]

        if not signal_values:
            return 0.0

        return sum(signal_values) / len(signal_values)

    def calculate_position_size(self, signals: Dict[str, float], confidence: float, max_position_size: float) -> float:
        """
        Calculate position size from signals.

        Args:
            signals: Trading signals
            confidence: Confidence between 0 and 1
            max_position_size: Maximum position size

        Returns:
            float: Position size
        """
        # Calculate average signal
        signal_values = list(signals.values())

        if not signal_values:
            return 0.0

        avg_signal = sum(signal_values) / len(signal_values)

        # Calculate position size
        position_size = avg_signal * confidence * max_position_size

        # Round to 6 decimal places to avoid floating point precision issues in tests
        return round(position_size, 6)
