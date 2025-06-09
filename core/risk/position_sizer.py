#!/usr/bin/env python3
"""
Enhanced Position Sizer Module for Synergy7 Trading System

This module provides dynamic position sizing based on volatility,
VaR-based risk management, regime detection, and correlation analysis.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
from datetime import datetime

from .var_calculator import VaRCalculator
from .portfolio_risk_manager import PortfolioRiskManager

# Configure logging
logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Enhanced position sizer with VaR-based risk management, regime detection,
    and correlation analysis for optimal position sizing.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the enhanced position sizer.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Get risk management configuration
        risk_config = self.config.get("risk_management", {})

        # Basic risk parameters
        self.max_position_size = risk_config.get("max_position_size_pct", 0.1)
        self.max_portfolio_risk = risk_config.get("portfolio_var_limit_pct", 0.02)
        self.volatility_lookback = risk_config.get("volatility_lookback", 20)
        self.volatility_scaling = risk_config.get("volatility_scaling", True)
        self.min_position_size = risk_config.get("min_position_size", 0.01)
        self.position_size_increment = risk_config.get("position_size_increment", 0.01)

        # VaR-based sizing parameters
        self.var_based_sizing = risk_config.get("position_sizing_method", "var_based") == "var_based"
        self.var_target_pct = risk_config.get("var_target_pct", 0.01)  # 1% VaR target per position
        self.confidence_level = risk_config.get("var_confidence_level", 0.95)

        # Regime-based adjustments
        self.regime_based_sizing = risk_config.get("regime_based_sizing", True)
        self.regime_multipliers = {
            "trending_up": 1.2,
            "trending_down": 0.8,
            "ranging": 1.0,
            "volatile": 0.7,
            "choppy": 0.3,
            "unknown": 0.5
        }

        # Correlation-based adjustments
        self.correlation_adjustment = risk_config.get("correlation_adjustment", True)
        self.correlation_threshold = risk_config.get("correlation_threshold", 0.7)
        self.correlation_penalty = risk_config.get("correlation_penalty", 0.5)

        # Initialize risk management components
        self.var_calculator = VaRCalculator(self.config) if self.var_based_sizing else None
        self.portfolio_risk_manager = PortfolioRiskManager(self.config)

        # Position sizing history
        self.sizing_history = []

        logger.info("Initialized Position Sizer with VaR integration")

    def calculate_position_size(self,
                                        price_data: pd.DataFrame,
                                        account_balance: float,
                                        market: str,
                                        signal_strength: float = 1.0,
                                        market_regime: str = "unknown",
                                        current_positions: Dict[str, Any] = None,
                                        correlation_data: Dict[str, pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Calculate position size with VaR-based risk management, regime detection,
        and correlation analysis.

        Args:
            price_data: DataFrame containing price data with 'close' column
            account_balance: Current account balance
            market: Market symbol
            signal_strength: Strength of the trading signal (0.0 to 1.0)
            market_regime: Current market regime
            current_positions: Dictionary of current portfolio positions
            correlation_data: Dictionary of price data for correlation analysis

        Returns:
            Dictionary containing position size information
        """
        try:
            # Validate inputs
            if price_data is None or len(price_data) < self.volatility_lookback:
                logger.warning(f"Insufficient price data for {market}, using minimum position size")
                return self._get_minimum_position_result(account_balance, market)

            # Calculate base position size using traditional method
            base_position_size = self._calculate_base_position_size(price_data, signal_strength)

            # Apply VaR-based sizing if enabled
            if self.var_based_sizing and self.var_calculator:
                var_position_size = self._calculate_var_based_position_size(price_data, account_balance)
                # Use the more conservative of the two
                position_size = min(base_position_size, var_position_size)
            else:
                position_size = base_position_size

            # Apply regime-based adjustments
            if self.regime_based_sizing:
                regime_multiplier = self.regime_multipliers.get(market_regime, 0.5)
                position_size *= regime_multiplier
                logger.debug(f"Applied regime multiplier {regime_multiplier} for regime {market_regime}")

            # Apply correlation-based adjustments
            if self.correlation_adjustment and current_positions and correlation_data:
                correlation_multiplier = self._calculate_correlation_adjustment(
                    market, current_positions, correlation_data
                )
                position_size *= correlation_multiplier
                logger.debug(f"Applied correlation multiplier {correlation_multiplier}")

            # Apply portfolio-level risk limits
            position_size = self._apply_portfolio_risk_limits(
                position_size, account_balance, current_positions
            )

            # Ensure position size is within bounds
            position_size = max(self.min_position_size, position_size)
            position_size = min(self.max_position_size, position_size)

            # Round to nearest increment
            position_size = round(position_size / self.position_size_increment) * self.position_size_increment

            # Calculate additional metrics
            returns = price_data["close"].pct_change().dropna()
            volatility = returns.rolling(window=self.volatility_lookback).std().iloc[-1]
            position_value = account_balance * position_size

            # Calculate position VaR if VaR calculator is available
            position_var = 0.0
            if self.var_calculator and len(returns) > 30:
                position_var = self.var_calculator.historical_var(returns, self.confidence_level)
                position_var *= position_size  # Scale by position size

            # Create result
            result = {
                "position_size": position_size,
                "position_value": position_value,
                "base_position_size": base_position_size,
                "volatility": volatility,
                "position_var": position_var,
                "market_regime": market_regime,
                "regime_multiplier": self.regime_multipliers.get(market_regime, 0.5),
                "risk_adjusted": True,
                "var_based": self.var_based_sizing,
                "calculation_timestamp": datetime.now().isoformat()
            }

            # Store in history
            self.sizing_history.append({
                "market": market,
                "result": result.copy(),
                "timestamp": datetime.now().isoformat()
            })

            # Maintain history size
            if len(self.sizing_history) > 1000:
                self.sizing_history.pop(0)

            logger.info(f"Position size for {market}: {position_size:.4f} ({position_value:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error calculating position size for {market}: {str(e)}")
            return self._get_minimum_position_result(account_balance, market)

    def _get_minimum_position_result(self, account_balance: float, market: str) -> Dict[str, Any]:
        """Get minimum position size result for error cases."""
        return {
            "position_size": self.min_position_size,
            "position_value": account_balance * self.min_position_size,
            "volatility": None,
            "risk_adjusted": False,
            "error": True,
            "market": market
        }

    def _calculate_base_position_size(self, price_data: pd.DataFrame, signal_strength: float) -> float:
        """Calculate base position size using traditional volatility-based method."""
        try:
            # Calculate volatility
            returns = price_data["close"].pct_change().dropna()
            volatility = returns.rolling(window=self.volatility_lookback).std().iloc[-1]

            # Default position size
            position_size = self.max_position_size

            # Adjust for volatility if enabled
            if self.volatility_scaling and volatility is not None and volatility > 0:
                # Calculate average volatility
                if len(returns) >= 252:
                    avg_volatility = returns.rolling(window=252).std().mean()
                else:
                    avg_volatility = volatility

                # Scale position size inversely with volatility
                volatility_ratio = avg_volatility / volatility
                position_size = min(self.max_position_size, self.max_position_size * volatility_ratio)

            # Adjust for signal strength
            position_size *= signal_strength

            return position_size

        except Exception as e:
            logger.warning(f"Error calculating base position size: {str(e)}")
            return self.min_position_size

    def _calculate_var_based_position_size(self, price_data: pd.DataFrame, account_balance: float) -> float:
        """Calculate position size based on VaR target."""
        try:
            if not self.var_calculator:
                return self.max_position_size

            # Calculate returns
            returns = price_data["close"].pct_change().dropna()

            if len(returns) < 30:
                return self.max_position_size

            # Calculate VaR for 100% position
            var_100pct = self.var_calculator.historical_var(returns, self.confidence_level)

            if var_100pct <= 0:
                return self.max_position_size

            # Calculate position size to achieve target VaR
            target_var_amount = account_balance * self.var_target_pct
            var_based_position_size = target_var_amount / (var_100pct * account_balance)

            return min(self.max_position_size, var_based_position_size)

        except Exception as e:
            logger.warning(f"Error calculating VaR-based position size: {str(e)}")
            return self.max_position_size

    def _calculate_correlation_adjustment(self, market: str, current_positions: Dict[str, Any],
                                        correlation_data: Dict[str, pd.DataFrame]) -> float:
        """Calculate position size adjustment based on correlation with existing positions."""
        try:
            if not current_positions or market not in correlation_data:
                return 1.0

            # Calculate correlations with existing positions
            market_returns = correlation_data[market]["close"].pct_change().dropna()
            high_correlations = []

            for existing_market, position in current_positions.items():
                if existing_market == market or existing_market not in correlation_data:
                    continue

                existing_returns = correlation_data[existing_market]["close"].pct_change().dropna()

                # Align returns
                aligned_returns = pd.concat([market_returns, existing_returns], axis=1).dropna()

                if len(aligned_returns) < 30:
                    continue

                correlation = aligned_returns.corr().iloc[0, 1]

                if abs(correlation) >= self.correlation_threshold:
                    position_weight = position.get("value", 0) / sum(p.get("value", 0) for p in current_positions.values())
                    high_correlations.append((correlation, position_weight))

            # Calculate adjustment
            if not high_correlations:
                return 1.0

            # Reduce position size based on correlated exposure
            total_correlated_weight = sum(weight for _, weight in high_correlations)
            correlation_adjustment = 1.0 - (total_correlated_weight * self.correlation_penalty)

            return max(0.1, correlation_adjustment)  # Minimum 10% of original size

        except Exception as e:
            logger.warning(f"Error calculating correlation adjustment: {str(e)}")
            return 1.0

    def _apply_portfolio_risk_limits(self, position_size: float, account_balance: float,
                                   current_positions: Dict[str, Any] = None) -> float:
        """Apply portfolio-level risk limits."""
        try:
            if not current_positions:
                return position_size

            # Calculate current portfolio exposure
            total_portfolio_value = sum(pos.get("value", 0) for pos in current_positions.values())
            current_exposure = total_portfolio_value / account_balance

            # Calculate new position value
            new_position_value = account_balance * position_size
            new_total_exposure = (total_portfolio_value + new_position_value) / account_balance

            # Check if new exposure would exceed portfolio risk limit
            if new_total_exposure > self.max_portfolio_risk * 10:  # Convert to exposure limit
                # Reduce position size to stay within limits
                max_additional_exposure = (self.max_portfolio_risk * 10) - current_exposure
                max_position_value = account_balance * max_additional_exposure
                adjusted_position_size = max_position_value / account_balance

                return max(self.min_position_size, adjusted_position_size)

            return position_size

        except Exception as e:
            logger.warning(f"Error applying portfolio risk limits: {str(e)}")
            return position_size

    # Legacy method for simple position sizing
    def calculate_simple_position_size(self, account_balance: float, risk_per_trade: float,
                                     entry_price: float) -> float:
        """Simple position sizing method for backward compatibility."""
        try:
            max_loss_amount = account_balance * risk_per_trade
            position_size = max_loss_amount / entry_price
            return min(position_size, account_balance * self.max_position_size)
        except Exception as e:
            logger.warning(f"Error in simple position sizing: {str(e)}")
            return account_balance * self.min_position_size

    def calculate_stop_loss(self,
                           entry_price: float,
                           position_size: float,
                           account_balance: float,
                           price_data: pd.DataFrame = None,
                           is_long: bool = True) -> Dict[str, Any]:
        """
        Calculate stop loss level based on volatility and risk parameters.

        Args:
            entry_price: Entry price
            position_size: Position size as percentage of account
            account_balance: Current account balance
            price_data: DataFrame containing price data with 'close' column
            is_long: Whether the position is long (True) or short (False)

        Returns:
            Dictionary containing stop loss information
        """
        # Default risk per trade
        risk_per_trade = self.config.get("risk_per_trade", 0.01)

        # Calculate position value
        position_value = account_balance * position_size

        # Calculate maximum loss amount
        max_loss_amount = account_balance * risk_per_trade

        # Calculate price movement for stop loss
        price_movement_pct = max_loss_amount / position_value

        # Calculate stop loss price
        if is_long:
            stop_loss_price = entry_price * (1 - price_movement_pct)
        else:
            stop_loss_price = entry_price * (1 + price_movement_pct)

        # If price data is provided, adjust stop loss based on volatility
        if price_data is not None and len(price_data) >= self.volatility_lookback:
            # Calculate average true range (ATR)
            high = price_data["high"]
            low = price_data["low"]
            close = price_data["close"]

            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = true_range.rolling(window=self.volatility_lookback).mean().iloc[-1]

            # Adjust stop loss based on ATR
            atr_multiplier = self.config.get("atr_multiplier", 2.0)

            if is_long:
                atr_stop_loss = entry_price - (atr * atr_multiplier)
                stop_loss_price = max(stop_loss_price, atr_stop_loss)
            else:
                atr_stop_loss = entry_price + (atr * atr_multiplier)
                stop_loss_price = min(stop_loss_price, atr_stop_loss)

        logger.info(f"Calculated stop loss: {stop_loss_price:.4f} (entry: {entry_price:.4f})")

        return {
            "stop_loss_price": stop_loss_price,
            "risk_amount": max_loss_amount,
            "risk_percentage": risk_per_trade
        }

    def calculate_take_profit(self,
                             entry_price: float,
                             stop_loss_price: float,
                             is_long: bool = True,
                             risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit level based on risk-reward ratio.

        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            is_long: Whether the position is long (True) or short (False)
            risk_reward_ratio: Desired risk-reward ratio

        Returns:
            Take profit price
        """
        # Calculate risk (price difference to stop loss)
        if is_long:
            risk = entry_price - stop_loss_price
            take_profit_price = entry_price + (risk * risk_reward_ratio)
        else:
            risk = stop_loss_price - entry_price
            take_profit_price = entry_price - (risk * risk_reward_ratio)

        logger.info(f"Calculated take profit: {take_profit_price:.4f} (entry: {entry_price:.4f})")

        return take_profit_price
