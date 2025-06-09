#!/usr/bin/env python3
"""
Portfolio Limits Module for Synergy7 Trading System

This module provides portfolio-level risk management, including
exposure limits, drawdown limits, and correlation-based position sizing.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("portfolio_limits")

class PortfolioLimits:
    """
    Portfolio limits manager that enforces risk constraints at the portfolio level.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the portfolio limits manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Default parameters
        self.max_portfolio_exposure = self.config.get("max_portfolio_exposure", 0.8)
        self.max_single_market_exposure = self.config.get("max_single_market_exposure", 0.3)
        self.max_correlated_exposure = self.config.get("max_correlated_exposure", 0.5)
        self.max_daily_drawdown = self.config.get("max_daily_drawdown", 0.05)
        self.max_weekly_drawdown = self.config.get("max_weekly_drawdown", 0.1)
        self.max_monthly_drawdown = self.config.get("max_monthly_drawdown", 0.15)
        
        # Track portfolio state
        self.positions = {}
        self.daily_pnl = []
        self.weekly_pnl = []
        self.monthly_pnl = []
        self.initial_balance = 0
        self.current_balance = 0
        self.peak_balance = 0
        self.last_reset_time = datetime.now()
        
        logger.info("Initialized PortfolioLimits")
    
    def set_initial_balance(self, balance: float) -> None:
        """
        Set the initial account balance.
        
        Args:
            balance: Initial account balance
        """
        self.initial_balance = balance
        self.current_balance = balance
        self.peak_balance = balance
        logger.info(f"Set initial balance: {balance:.2f}")
    
    def update_balance(self, balance: float) -> None:
        """
        Update the current account balance.
        
        Args:
            balance: Current account balance
        """
        old_balance = self.current_balance
        self.current_balance = balance
        
        # Update peak balance if needed
        if balance > self.peak_balance:
            self.peak_balance = balance
        
        # Calculate PnL
        pnl = balance - old_balance
        pnl_pct = pnl / old_balance if old_balance > 0 else 0
        
        # Update PnL history
        self.daily_pnl.append({
            "timestamp": datetime.now(),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "balance": balance
        })
        
        # Keep only the last 30 days of data
        self.daily_pnl = [p for p in self.daily_pnl if p["timestamp"] > datetime.now() - timedelta(days=30)]
        
        # Update weekly and monthly PnL
        self.weekly_pnl.append({
            "timestamp": datetime.now(),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "balance": balance
        })
        self.weekly_pnl = [p for p in self.weekly_pnl if p["timestamp"] > datetime.now() - timedelta(days=7)]
        
        self.monthly_pnl.append({
            "timestamp": datetime.now(),
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "balance": balance
        })
        self.monthly_pnl = [p for p in self.monthly_pnl if p["timestamp"] > datetime.now() - timedelta(days=30)]
        
        logger.info(f"Updated balance: {balance:.2f} (PnL: {pnl:.2f}, {pnl_pct:.2%})")
    
    def add_position(self,
                    position_id: str,
                    market: str,
                    size: float,
                    entry_price: float,
                    is_long: bool) -> None:
        """
        Add a new position to the portfolio.
        
        Args:
            position_id: Unique position identifier
            market: Market symbol
            size: Position size in base currency
            entry_price: Entry price
            is_long: Whether the position is long (True) or short (False)
        """
        position = {
            "position_id": position_id,
            "market": market,
            "size": size,
            "entry_price": entry_price,
            "is_long": is_long,
            "entry_time": datetime.now(),
            "value": size * entry_price
        }
        
        self.positions[position_id] = position
        logger.info(f"Added position {position_id}: {market} {'LONG' if is_long else 'SHORT'} {size:.4f} @ {entry_price:.4f}")
    
    def update_position(self,
                       position_id: str,
                       current_price: float) -> None:
        """
        Update a position with the current price.
        
        Args:
            position_id: Unique position identifier
            current_price: Current price
        """
        if position_id not in self.positions:
            logger.warning(f"Position {position_id} not found")
            return
        
        position = self.positions[position_id]
        old_value = position["value"]
        
        # Update position value
        position["value"] = position["size"] * current_price
        
        # Calculate unrealized PnL
        if position["is_long"]:
            position["unrealized_pnl"] = position["size"] * (current_price - position["entry_price"])
        else:
            position["unrealized_pnl"] = position["size"] * (position["entry_price"] - current_price)
        
        position["unrealized_pnl_pct"] = position["unrealized_pnl"] / old_value if old_value > 0 else 0
        
        self.positions[position_id] = position
    
    def remove_position(self, position_id: str) -> None:
        """
        Remove a position from the portfolio.
        
        Args:
            position_id: Unique position identifier
        """
        if position_id in self.positions:
            position = self.positions[position_id]
            logger.info(f"Removed position {position_id}: {position['market']}")
            del self.positions[position_id]
    
    def get_total_exposure(self) -> float:
        """
        Get the total portfolio exposure.
        
        Returns:
            Total exposure as a percentage of account balance
        """
        total_value = sum(p["value"] for p in self.positions.values())
        exposure = total_value / self.current_balance if self.current_balance > 0 else 0
        return exposure
    
    def get_market_exposure(self, market: str) -> float:
        """
        Get the exposure for a specific market.
        
        Args:
            market: Market symbol
            
        Returns:
            Market exposure as a percentage of account balance
        """
        market_value = sum(p["value"] for p in self.positions.values() if p["market"] == market)
        exposure = market_value / self.current_balance if self.current_balance > 0 else 0
        return exposure
    
    def get_drawdown(self) -> Dict[str, float]:
        """
        Get current drawdown metrics.
        
        Returns:
            Dictionary containing drawdown metrics
        """
        current_drawdown = 1 - (self.current_balance / self.peak_balance) if self.peak_balance > 0 else 0
        
        # Calculate daily drawdown
        if self.daily_pnl:
            daily_balance = [p["balance"] for p in self.daily_pnl]
            daily_peak = max(daily_balance)
            daily_drawdown = 1 - (self.current_balance / daily_peak) if daily_peak > 0 else 0
        else:
            daily_drawdown = 0
        
        # Calculate weekly drawdown
        if self.weekly_pnl:
            weekly_balance = [p["balance"] for p in self.weekly_pnl]
            weekly_peak = max(weekly_balance)
            weekly_drawdown = 1 - (self.current_balance / weekly_peak) if weekly_peak > 0 else 0
        else:
            weekly_drawdown = 0
        
        # Calculate monthly drawdown
        if self.monthly_pnl:
            monthly_balance = [p["balance"] for p in self.monthly_pnl]
            monthly_peak = max(monthly_balance)
            monthly_drawdown = 1 - (self.current_balance / monthly_peak) if monthly_peak > 0 else 0
        else:
            monthly_drawdown = 0
        
        return {
            "current_drawdown": current_drawdown,
            "daily_drawdown": daily_drawdown,
            "weekly_drawdown": weekly_drawdown,
            "monthly_drawdown": monthly_drawdown
        }
    
    def check_limits(self) -> Dict[str, Any]:
        """
        Check if any portfolio limits have been exceeded.
        
        Returns:
            Dictionary containing limit check results
        """
        # Get current exposures and drawdowns
        total_exposure = self.get_total_exposure()
        drawdowns = self.get_drawdown()
        
        # Check portfolio exposure limit
        portfolio_exposure_exceeded = total_exposure > self.max_portfolio_exposure
        
        # Check market exposure limits
        market_exposures = {}
        market_exposure_exceeded = False
        for market in set(p["market"] for p in self.positions.values()):
            market_exposure = self.get_market_exposure(market)
            market_exposures[market] = market_exposure
            if market_exposure > self.max_single_market_exposure:
                market_exposure_exceeded = True
        
        # Check drawdown limits
        daily_drawdown_exceeded = drawdowns["daily_drawdown"] > self.max_daily_drawdown
        weekly_drawdown_exceeded = drawdowns["weekly_drawdown"] > self.max_weekly_drawdown
        monthly_drawdown_exceeded = drawdowns["monthly_drawdown"] > self.max_monthly_drawdown
        
        # Compile results
        limits_exceeded = {
            "portfolio_exposure": portfolio_exposure_exceeded,
            "market_exposure": market_exposure_exceeded,
            "daily_drawdown": daily_drawdown_exceeded,
            "weekly_drawdown": weekly_drawdown_exceeded,
            "monthly_drawdown": monthly_drawdown_exceeded
        }
        
        any_exceeded = any(limits_exceeded.values())
        
        if any_exceeded:
            logger.warning(f"Portfolio limits exceeded: {limits_exceeded}")
        
        return {
            "limits_exceeded": limits_exceeded,
            "any_exceeded": any_exceeded,
            "total_exposure": total_exposure,
            "market_exposures": market_exposures,
            "drawdowns": drawdowns
        }
    
    def can_open_position(self,
                         market: str,
                         size: float,
                         price: float) -> Tuple[bool, str]:
        """
        Check if a new position can be opened within portfolio limits.
        
        Args:
            market: Market symbol
            size: Position size in base currency
            price: Current price
            
        Returns:
            Tuple of (can_open, reason)
        """
        # Calculate position value
        position_value = size * price
        
        # Calculate new exposures
        current_market_exposure = self.get_market_exposure(market)
        new_market_exposure = current_market_exposure + (position_value / self.current_balance)
        
        current_total_exposure = self.get_total_exposure()
        new_total_exposure = current_total_exposure + (position_value / self.current_balance)
        
        # Check drawdowns
        drawdowns = self.get_drawdown()
        
        # Check limits
        if new_total_exposure > self.max_portfolio_exposure:
            return False, f"Portfolio exposure limit exceeded: {new_total_exposure:.2%} > {self.max_portfolio_exposure:.2%}"
        
        if new_market_exposure > self.max_single_market_exposure:
            return False, f"Market exposure limit exceeded for {market}: {new_market_exposure:.2%} > {self.max_single_market_exposure:.2%}"
        
        if drawdowns["daily_drawdown"] > self.max_daily_drawdown:
            return False, f"Daily drawdown limit exceeded: {drawdowns['daily_drawdown']:.2%} > {self.max_daily_drawdown:.2%}"
        
        if drawdowns["weekly_drawdown"] > self.max_weekly_drawdown:
            return False, f"Weekly drawdown limit exceeded: {drawdowns['weekly_drawdown']:.2%} > {self.max_weekly_drawdown:.2%}"
        
        if drawdowns["monthly_drawdown"] > self.max_monthly_drawdown:
            return False, f"Monthly drawdown limit exceeded: {drawdowns['monthly_drawdown']:.2%} > {self.max_monthly_drawdown:.2%}"
        
        return True, "Position can be opened within portfolio limits"
