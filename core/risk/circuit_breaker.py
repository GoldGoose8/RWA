#!/usr/bin/env python3
"""
Circuit Breaker Module for Synergy7 Trading System

This module provides circuit breaker functionality to automatically
halt trading when certain risk thresholds are exceeded.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("circuit_breaker")

class CircuitBreaker:
    """
    Circuit breaker that halts trading when risk thresholds are exceeded.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the circuit breaker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Default parameters
        self.enabled = self.config.get("enabled", True)
        self.max_consecutive_losses = self.config.get("max_consecutive_losses", 3)
        self.max_daily_loss_pct = self.config.get("max_daily_loss_pct", 0.05)
        self.max_drawdown_pct = self.config.get("max_drawdown_pct", 0.1)
        self.cooldown_minutes = self.config.get("cooldown_minutes", 60)
        self.volatility_threshold = self.config.get("volatility_threshold", 0.05)
        self.api_failure_threshold = self.config.get("api_failure_threshold", 5)
        
        # State variables
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.consecutive_losses = 0
        self.daily_loss_pct = 0.0
        self.current_drawdown_pct = 0.0
        self.peak_balance = 0.0
        self.current_balance = 0.0
        self.last_trade_time = None
        self.last_trade_result = None
        self.trip_time = None
        self.trip_reason = None
        self.api_failures = {}
        self.market_volatility = {}
        
        logger.info(f"Initialized CircuitBreaker (enabled: {self.enabled})")
    
    def update_balance(self, balance: float) -> None:
        """
        Update the current account balance.
        
        Args:
            balance: Current account balance
        """
        self.current_balance = balance
        
        # Update peak balance if needed
        if balance > self.peak_balance:
            self.peak_balance = balance
        
        # Update drawdown
        if self.peak_balance > 0:
            self.current_drawdown_pct = 1 - (balance / self.peak_balance)
        
        # Check if drawdown threshold is exceeded
        if self.enabled and self.current_drawdown_pct > self.max_drawdown_pct:
            self.trip_circuit("Drawdown threshold exceeded")
    
    def record_trade_result(self, trade_id: str, profit_loss: float, initial_balance: float) -> None:
        """
        Record the result of a trade.
        
        Args:
            trade_id: Unique trade identifier
            profit_loss: Profit or loss amount
            initial_balance: Account balance before the trade
        """
        self.last_trade_time = datetime.now()
        self.last_trade_result = profit_loss
        
        # Calculate profit/loss percentage
        pnl_pct = profit_loss / initial_balance if initial_balance > 0 else 0
        
        # Update consecutive losses
        if profit_loss < 0:
            self.consecutive_losses += 1
            logger.info(f"Trade {trade_id} resulted in loss: {profit_loss:.2f} ({pnl_pct:.2%}), consecutive losses: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0
            logger.info(f"Trade {trade_id} resulted in profit: {profit_loss:.2f} ({pnl_pct:.2%}), consecutive losses reset")
        
        # Update daily loss percentage
        self.daily_loss_pct += pnl_pct if pnl_pct < 0 else 0
        
        # Check if thresholds are exceeded
        if self.enabled:
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.trip_circuit(f"Max consecutive losses ({self.max_consecutive_losses}) exceeded")
            
            if abs(self.daily_loss_pct) > self.max_daily_loss_pct:
                self.trip_circuit(f"Max daily loss ({self.max_daily_loss_pct:.2%}) exceeded")
    
    def record_api_failure(self, api_name: str) -> None:
        """
        Record an API failure.
        
        Args:
            api_name: Name of the API that failed
        """
        if api_name not in self.api_failures:
            self.api_failures[api_name] = {
                "count": 0,
                "last_failure_time": None
            }
        
        self.api_failures[api_name]["count"] += 1
        self.api_failures[api_name]["last_failure_time"] = datetime.now()
        
        logger.warning(f"API failure recorded for {api_name}, count: {self.api_failures[api_name]['count']}")
        
        # Check if threshold is exceeded
        if self.enabled and self.api_failures[api_name]["count"] >= self.api_failure_threshold:
            self.trip_circuit(f"API failure threshold ({self.api_failure_threshold}) exceeded for {api_name}")
    
    def record_api_success(self, api_name: str) -> None:
        """
        Record an API success.
        
        Args:
            api_name: Name of the API that succeeded
        """
        if api_name in self.api_failures:
            self.api_failures[api_name]["count"] = 0
    
    def update_market_volatility(self, market: str, volatility: float) -> None:
        """
        Update the volatility for a market.
        
        Args:
            market: Market symbol
            volatility: Current volatility measure
        """
        self.market_volatility[market] = volatility
        
        # Check if volatility threshold is exceeded
        if self.enabled and volatility > self.volatility_threshold:
            logger.warning(f"High volatility detected for {market}: {volatility:.4f} > {self.volatility_threshold:.4f}")
            
            # Only trip circuit if multiple markets have high volatility
            high_vol_markets = [m for m, v in self.market_volatility.items() if v > self.volatility_threshold]
            if len(high_vol_markets) >= 2:
                self.trip_circuit(f"Volatility threshold exceeded for multiple markets: {', '.join(high_vol_markets)}")
    
    def trip_circuit(self, reason: str) -> None:
        """
        Trip the circuit breaker.
        
        Args:
            reason: Reason for tripping the circuit
        """
        if self.state == "CLOSED":
            self.state = "OPEN"
            self.trip_time = datetime.now()
            self.trip_reason = reason
            logger.warning(f"Circuit breaker TRIPPED: {reason}")
    
    def reset_circuit(self) -> None:
        """Reset the circuit breaker to closed state."""
        if self.state != "CLOSED":
            self.state = "CLOSED"
            self.trip_time = None
            self.trip_reason = None
            logger.info("Circuit breaker manually RESET")
    
    def reset_daily_metrics(self) -> None:
        """Reset daily metrics (called at the start of each trading day)."""
        self.daily_loss_pct = 0.0
        logger.info("Daily metrics reset")
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Check if trading is allowed.
        
        Returns:
            Tuple of (can_trade, reason)
        """
        if not self.enabled:
            return True, "Circuit breaker is disabled"
        
        if self.state == "CLOSED":
            return True, "Circuit breaker is closed"
        
        if self.state == "OPEN":
            # Check if cooldown period has elapsed
            if self.trip_time and datetime.now() > self.trip_time + timedelta(minutes=self.cooldown_minutes):
                self.state = "HALF-OPEN"
                logger.info(f"Circuit breaker state changed to HALF-OPEN after cooldown period ({self.cooldown_minutes} minutes)")
                return False, f"Circuit breaker is in cooldown (tripped {(datetime.now() - self.trip_time).total_seconds() / 60:.1f} minutes ago)"
            
            return False, f"Circuit breaker is OPEN: {self.trip_reason}"
        
        if self.state == "HALF-OPEN":
            return False, "Circuit breaker is HALF-OPEN, manual reset required"
        
        return False, "Unknown circuit breaker state"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the circuit breaker.
        
        Returns:
            Dictionary containing circuit breaker status
        """
        return {
            "enabled": self.enabled,
            "state": self.state,
            "consecutive_losses": self.consecutive_losses,
            "daily_loss_pct": self.daily_loss_pct,
            "current_drawdown_pct": self.current_drawdown_pct,
            "trip_time": self.trip_time,
            "trip_reason": self.trip_reason,
            "api_failures": self.api_failures,
            "market_volatility": self.market_volatility,
            "thresholds": {
                "max_consecutive_losses": self.max_consecutive_losses,
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_drawdown_pct": self.max_drawdown_pct,
                "cooldown_minutes": self.cooldown_minutes,
                "volatility_threshold": self.volatility_threshold,
                "api_failure_threshold": self.api_failure_threshold
            }
        }
