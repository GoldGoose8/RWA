#!/usr/bin/env python3
"""
Stop Loss Module for Synergy7 Trading System

This module provides trailing stop-loss functionality for managing risk.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("stop_loss")

class StopLossManager:
    """
    Stop loss manager that provides various stop loss strategies,
    including fixed, trailing, and volatility-based stops.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the stop loss manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Default parameters
        self.trailing_enabled = self.config.get("trailing_enabled", True)
        self.trailing_activation_pct = self.config.get("trailing_activation_pct", 0.01)
        self.trailing_distance_pct = self.config.get("trailing_distance_pct", 0.02)
        self.volatility_multiplier = self.config.get("volatility_multiplier", 2.0)
        self.time_based_widening = self.config.get("time_based_widening", False)
        self.widening_factor = self.config.get("widening_factor", 0.001)  # Per hour
        
        # Store active stops
        self.active_stops = {}
        
        logger.info("Initialized StopLossManager")
    
    def set_initial_stop(self,
                        trade_id: str,
                        entry_price: float,
                        entry_time: pd.Timestamp,
                        initial_stop_price: float,
                        is_long: bool,
                        volatility: Optional[float] = None) -> Dict[str, Any]:
        """
        Set the initial stop loss for a trade.
        
        Args:
            trade_id: Unique trade identifier
            entry_price: Entry price
            entry_time: Entry time
            initial_stop_price: Initial stop loss price
            is_long: Whether the position is long (True) or short (False)
            volatility: Volatility measure (optional)
            
        Returns:
            Dictionary containing stop loss information
        """
        stop_info = {
            "trade_id": trade_id,
            "entry_price": entry_price,
            "entry_time": entry_time,
            "initial_stop_price": initial_stop_price,
            "current_stop_price": initial_stop_price,
            "is_long": is_long,
            "volatility": volatility,
            "highest_price": entry_price if is_long else float("-inf"),
            "lowest_price": entry_price if not is_long else float("inf"),
            "trailing_activated": False,
            "stop_updated_time": entry_time,
            "stop_type": "initial"
        }
        
        self.active_stops[trade_id] = stop_info
        
        logger.info(f"Set initial stop for trade {trade_id}: {initial_stop_price:.4f}")
        
        return stop_info
    
    def update_stop(self,
                   trade_id: str,
                   current_price: float,
                   current_time: pd.Timestamp) -> Dict[str, Any]:
        """
        Update the stop loss for a trade based on current price.
        
        Args:
            trade_id: Unique trade identifier
            current_price: Current price
            current_time: Current time
            
        Returns:
            Updated stop loss information
        """
        if trade_id not in self.active_stops:
            logger.warning(f"Trade {trade_id} not found in active stops")
            return None
        
        stop_info = self.active_stops[trade_id]
        is_long = stop_info["is_long"]
        entry_price = stop_info["entry_price"]
        current_stop_price = stop_info["current_stop_price"]
        
        # Update highest/lowest prices
        if is_long:
            stop_info["highest_price"] = max(stop_info["highest_price"], current_price)
        else:
            stop_info["lowest_price"] = min(stop_info["lowest_price"], current_price)
        
        # Check if trailing stop should be activated
        if self.trailing_enabled and not stop_info["trailing_activated"]:
            if is_long:
                price_movement_pct = (current_price - entry_price) / entry_price
                if price_movement_pct >= self.trailing_activation_pct:
                    stop_info["trailing_activated"] = True
                    stop_info["stop_type"] = "trailing"
                    logger.info(f"Trailing stop activated for trade {trade_id}")
            else:
                price_movement_pct = (entry_price - current_price) / entry_price
                if price_movement_pct >= self.trailing_activation_pct:
                    stop_info["trailing_activated"] = True
                    stop_info["stop_type"] = "trailing"
                    logger.info(f"Trailing stop activated for trade {trade_id}")
        
        # Update trailing stop if activated
        if self.trailing_enabled and stop_info["trailing_activated"]:
            if is_long:
                highest_price = stop_info["highest_price"]
                new_stop_price = highest_price * (1 - self.trailing_distance_pct)
                
                # Only move stop up, never down
                if new_stop_price > current_stop_price:
                    stop_info["current_stop_price"] = new_stop_price
                    stop_info["stop_updated_time"] = current_time
                    logger.info(f"Updated trailing stop for trade {trade_id}: {new_stop_price:.4f}")
            else:
                lowest_price = stop_info["lowest_price"]
                new_stop_price = lowest_price * (1 + self.trailing_distance_pct)
                
                # Only move stop down, never up
                if new_stop_price < current_stop_price:
                    stop_info["current_stop_price"] = new_stop_price
                    stop_info["stop_updated_time"] = current_time
                    logger.info(f"Updated trailing stop for trade {trade_id}: {new_stop_price:.4f}")
        
        # Apply time-based widening if enabled
        if self.time_based_widening:
            hours_elapsed = (current_time - stop_info["entry_time"]).total_seconds() / 3600
            widening_amount = entry_price * self.widening_factor * hours_elapsed
            
            if is_long:
                widened_stop = stop_info["initial_stop_price"] - widening_amount
                stop_info["current_stop_price"] = max(stop_info["current_stop_price"], widened_stop)
            else:
                widened_stop = stop_info["initial_stop_price"] + widening_amount
                stop_info["current_stop_price"] = min(stop_info["current_stop_price"], widened_stop)
        
        # Update the active stops dictionary
        self.active_stops[trade_id] = stop_info
        
        return stop_info
    
    def check_stop_triggered(self,
                            trade_id: str,
                            current_price: float) -> bool:
        """
        Check if a stop loss has been triggered.
        
        Args:
            trade_id: Unique trade identifier
            current_price: Current price
            
        Returns:
            True if stop loss triggered, False otherwise
        """
        if trade_id not in self.active_stops:
            logger.warning(f"Trade {trade_id} not found in active stops")
            return False
        
        stop_info = self.active_stops[trade_id]
        is_long = stop_info["is_long"]
        stop_price = stop_info["current_stop_price"]
        
        # Check if stop loss is triggered
        if is_long and current_price <= stop_price:
            logger.info(f"Stop loss triggered for long trade {trade_id}: {current_price:.4f} <= {stop_price:.4f}")
            return True
        elif not is_long and current_price >= stop_price:
            logger.info(f"Stop loss triggered for short trade {trade_id}: {current_price:.4f} >= {stop_price:.4f}")
            return True
        
        return False
    
    def remove_stop(self, trade_id: str) -> None:
        """
        Remove a stop loss from active stops.
        
        Args:
            trade_id: Unique trade identifier
        """
        if trade_id in self.active_stops:
            del self.active_stops[trade_id]
            logger.info(f"Removed stop loss for trade {trade_id}")
    
    def get_all_stops(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active stop losses.
        
        Returns:
            Dictionary of all active stop losses
        """
        return self.active_stops
    
    def get_stop_info(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stop loss information for a specific trade.
        
        Args:
            trade_id: Unique trade identifier
            
        Returns:
            Stop loss information or None if not found
        """
        return self.active_stops.get(trade_id)
