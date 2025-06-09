#!/usr/bin/env python3
"""
Order Book Processor

This module provides a processor for order book data.
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

class OrderBookProcessor:
    """Processor for order book data."""
    
    def __init__(self):
        """Initialize the order book processor."""
        # Initialize order book cache
        self.order_books = {}
        
        # Initialize order book metrics
        self.metrics = {}
        
        logger.info("Initialized order book processor")
    
    def process(self, market: str, order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process order book data.
        
        Args:
            market: Market symbol
            order_book_data: Order book data
            
        Returns:
            Dict[str, Any]: Processed order book data
        """
        try:
            # Extract bids and asks
            bids = order_book_data.get("bids", [])
            asks = order_book_data.get("asks", [])
            
            # Normalize bids and asks
            normalized_bids = self._normalize_orders(bids)
            normalized_asks = self._normalize_orders(asks)
            
            # Calculate metrics
            metrics = self._calculate_metrics(market, normalized_bids, normalized_asks)
            
            # Update order book cache
            self.order_books[market] = {
                "bids": normalized_bids,
                "asks": normalized_asks,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Update metrics
            self.metrics[market] = metrics
            
            # Return processed data
            return {
                "market": market,
                "bids": normalized_bids,
                "asks": normalized_asks,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing order book data for {market}: {str(e)}")
            return {
                "market": market,
                "bids": [],
                "asks": [],
                "metrics": {},
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }
    
    def get_order_book(self, market: str) -> Dict[str, Any]:
        """
        Get order book for a market.
        
        Args:
            market: Market symbol
            
        Returns:
            Dict[str, Any]: Order book data
        """
        return self.order_books.get(market, {})
    
    def get_metrics(self, market: str) -> Dict[str, Any]:
        """
        Get metrics for a market.
        
        Args:
            market: Market symbol
            
        Returns:
            Dict[str, Any]: Metrics data
        """
        return self.metrics.get(market, {})
    
    def _normalize_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize orders.
        
        Args:
            orders: List of orders
            
        Returns:
            List[Dict[str, Any]]: Normalized orders
        """
        normalized_orders = []
        
        for order in orders:
            # Extract price and size
            price = order.get("price", 0.0)
            size = order.get("size", 0.0)
            
            # Skip invalid orders
            if price <= 0.0 or size <= 0.0:
                continue
            
            # Add normalized order
            normalized_orders.append({
                "price": price,
                "size": size,
            })
        
        return normalized_orders
    
    def _calculate_metrics(self, market: str, bids: List[Dict[str, Any]], asks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for an order book.
        
        Args:
            market: Market symbol
            bids: Normalized bids
            asks: Normalized asks
            
        Returns:
            Dict[str, Any]: Metrics
        """
        metrics = {}
        
        # Check if order book is valid
        if not bids or not asks:
            return metrics
        
        # Calculate mid price
        best_bid = bids[0]["price"]
        best_ask = asks[0]["price"]
        mid_price = (best_bid + best_ask) / 2
        
        # Calculate spread
        spread = best_ask - best_bid
        spread_pct = spread / mid_price if mid_price > 0 else 0
        
        # Calculate bid and ask liquidity
        bid_liquidity = sum(bid["price"] * bid["size"] for bid in bids)
        ask_liquidity = sum(ask["price"] * ask["size"] for ask in asks)
        total_liquidity = bid_liquidity + ask_liquidity
        
        # Calculate bid-ask imbalance
        bid_ask_imbalance = (bid_liquidity - ask_liquidity) / (bid_liquidity + ask_liquidity) if (bid_liquidity + ask_liquidity) > 0 else 0
        
        # Calculate price impact for standard order sizes
        standard_order_sizes = [100, 1000, 10000]  # in USD
        price_impact = {}
        
        for size in standard_order_sizes:
            # Calculate price impact for buy order
            buy_impact = self._calculate_price_impact(asks, size)
            
            # Calculate price impact for sell order
            sell_impact = self._calculate_price_impact(bids, size)
            
            price_impact[f"{size}"] = {
                "buy": buy_impact,
                "sell": sell_impact,
            }
        
        # Update metrics
        metrics = {
            "mid_price": mid_price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_pct": spread_pct,
            "bid_liquidity": bid_liquidity,
            "ask_liquidity": ask_liquidity,
            "total_liquidity": total_liquidity,
            "bid_ask_imbalance": bid_ask_imbalance,
            "price_impact": price_impact,
        }
        
        return metrics
    
    def _calculate_price_impact(self, orders: List[Dict[str, Any]], order_size_usd: float) -> float:
        """
        Calculate price impact for an order.
        
        Args:
            orders: List of orders (bids or asks)
            order_size_usd: Order size in USD
            
        Returns:
            float: Price impact as a percentage
        """
        if not orders:
            return 0.0
        
        # Get initial price
        initial_price = orders[0]["price"]
        
        # Calculate price impact
        remaining_size = order_size_usd
        executed_value = 0.0
        
        for order in orders:
            price = order["price"]
            size = order["size"]
            order_value = price * size
            
            if order_value >= remaining_size:
                # Order is fully executed at this price level
                executed_value += remaining_size
                remaining_size = 0
                break
            else:
                # Order is partially executed at this price level
                executed_value += order_value
                remaining_size -= order_value
        
        # Calculate average execution price
        if executed_value > 0:
            avg_price = executed_value / (order_size_usd - remaining_size)
            
            # Calculate price impact
            price_impact = abs(avg_price - initial_price) / initial_price
            
            return price_impact
        else:
            return 0.0
