#!/usr/bin/env python3
"""
Production Position Sizer for 0.5 Wallet Strategy
Optimized for real asset deployment with fee efficiency and risk management.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductionPositionSizer:
    """
    Enhanced position sizer for live production with 0.5 wallet strategy.
    Optimizes position sizes for fee efficiency while maintaining risk controls.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the production position sizer."""
        self.config = config

        # Wallet strategy settings - 🚀 FIXED: 90% wallet strategy
        self.active_trading_pct = config.get('wallet', {}).get('active_trading_pct', 0.9)  # 90% active trading
        self.reserve_pct = config.get('wallet', {}).get('reserve_pct', 0.1)  # 10% reserve

        # Position sizing settings - 🚨 CRITICAL FIX: Larger positions to overcome fees
        trading_config = config.get('trading', {})
        self.base_position_size_pct = trading_config.get('base_position_size_pct', 0.50)  # 50% base for profitability
        self.max_position_size_pct = trading_config.get('max_position_size_pct', 0.80)   # 80% max for meaningful trades
        self.min_position_size_pct = trading_config.get('min_position_size_pct', 0.20)   # 20% min for fee coverage

        # Fee optimization settings - 🚨 CRITICAL FIX: Higher minimums for profitability
        self.min_trade_size_usd = trading_config.get('min_trade_size_usd', 50)   # $50 minimum to overcome fees
        self.target_trade_size_usd = trading_config.get('target_trade_size_usd', 200)  # $200 target for profits

        # Risk management settings - 🔧 REMOVED HARDCODED EXPOSURE LIMITS
        risk_config = config.get('risk_management', {})
        self.max_risk_per_trade = risk_config.get('max_risk_per_trade', 0.02)
        self.max_portfolio_exposure = risk_config.get('max_portfolio_exposure', 0.8)  # Increased from 0.5 to 0.8 (80%)

        # Current state
        self.current_wallet_balance = 0.0
        self.current_active_capital = 0.0
        self.current_exposure = 0.0
        self.sol_price_usd = 180.0  # Default, will be updated

        logger.info(f"Production Position Sizer initialized with {self.active_trading_pct:.1%} wallet strategy")

    def update_wallet_state(self, wallet_balance: float, current_exposure: float, sol_price: float):
        """Update current wallet state for position sizing calculations."""
        # 🚀 FIXED: Dynamic fee reserve based on wallet size and proper active capital calculation
        # Use 1% of wallet for fees, minimum 0.001 SOL, maximum 0.01 SOL
        self.fee_reserve_sol = max(0.001, min(0.01, wallet_balance * 0.01))

        # Calculate available balance after fee reserve
        available_balance = max(0, wallet_balance - self.fee_reserve_sol)

        # 🚀 FIXED: Properly implement 90% active trading strategy
        self.current_wallet_balance = available_balance
        self.current_active_capital = available_balance * self.active_trading_pct  # 90% of available balance
        self.reserve_balance = available_balance * self.reserve_pct  # 10% reserve
        self.current_exposure = current_exposure
        self.sol_price_usd = sol_price

        logger.info(f"🚀 WALLET STATE UPDATED:")
        logger.info(f"   Total Wallet: {wallet_balance:.6f} SOL")
        logger.info(f"   Fee Reserve: {self.fee_reserve_sol:.6f} SOL ({(self.fee_reserve_sol/wallet_balance)*100:.1f}%)")
        logger.info(f"   Available Balance: {available_balance:.6f} SOL")
        logger.info(f"   Active Capital (90%): {self.current_active_capital:.6f} SOL")
        logger.info(f"   Reserve (10%): {self.reserve_balance:.6f} SOL")
        logger.info(f"   Current Exposure: {current_exposure:.6f} SOL")

    def calculate_position_size(self, signal_strength: float, strategy: str,
                              market_regime: str, volatility: float) -> Dict[str, Any]:
        """
        Calculate optimal position size for the given signal.

        Args:
            signal_strength: Signal confidence (0.0 to 1.0)
            strategy: Strategy name
            market_regime: Current market regime
            volatility: Current market volatility

        Returns:
            Dict containing position size details
        """
        try:
            # Base position size as percentage of active capital
            base_size_pct = self.base_position_size_pct

            # Adjust for signal strength
            signal_multiplier = 0.5 + (signal_strength * 0.5)  # 0.5 to 1.0 range
            adjusted_size_pct = base_size_pct * signal_multiplier

            # Adjust for strategy
            strategy_multiplier = self._get_strategy_multiplier(strategy)
            adjusted_size_pct *= strategy_multiplier

            # Adjust for market regime
            regime_multiplier = self._get_regime_multiplier(market_regime)
            adjusted_size_pct *= regime_multiplier

            # Adjust for volatility
            volatility_multiplier = self._get_volatility_multiplier(volatility)
            adjusted_size_pct *= volatility_multiplier

            # Apply limits
            adjusted_size_pct = max(self.min_position_size_pct,
                                  min(self.max_position_size_pct, adjusted_size_pct))

            # 🚀 FIXED: Calculate position size based on active capital (not total wallet)
            position_size_sol = self.current_active_capital * adjusted_size_pct
            position_size_usd = position_size_sol * self.sol_price_usd

            # 🚀 FIXED: Improved fee optimization with better minimum thresholds
            # Lower minimum trade size since strategy is working
            effective_min_trade_usd = max(self.min_trade_size_usd * 0.5, 5.0)  # Reduce minimum to $5-25

            if position_size_usd < effective_min_trade_usd:
                # Only increase if significantly below minimum
                position_size_usd = effective_min_trade_usd
                position_size_sol = position_size_usd / self.sol_price_usd
                adjusted_size_pct = position_size_sol / self.current_active_capital

                logger.info(f"🚀 Position size adjusted to ${position_size_usd:.2f} for fee efficiency (min: ${effective_min_trade_usd:.2f})")

            # 🚀 FIXED: Ensure we don't exceed active capital
            if position_size_sol > self.current_active_capital:
                position_size_sol = self.current_active_capital * 0.95  # Use 95% max to leave buffer
                position_size_usd = position_size_sol * self.sol_price_usd
                adjusted_size_pct = 0.95
                logger.warning(f"🚀 Position size capped at 95% of active capital: {position_size_sol:.6f} SOL")

            # Risk check - ensure we don't exceed exposure limits
            new_exposure = self.current_exposure + position_size_sol
            max_allowed_exposure = self.current_wallet_balance * self.max_portfolio_exposure

            if new_exposure > max_allowed_exposure:
                # Reduce position size to stay within exposure limits
                available_exposure = max_allowed_exposure - self.current_exposure
                if available_exposure > 0:
                    position_size_sol = available_exposure
                    position_size_usd = position_size_sol * self.sol_price_usd
                    adjusted_size_pct = position_size_sol / self.current_active_capital

                    logger.warning(f"Position size reduced to {position_size_sol:.4f} SOL due to exposure limits")
                else:
                    # No room for new positions
                    return {
                        'position_size_sol': 0.0,
                        'position_size_usd': 0.0,
                        'position_size_pct': 0.0,
                        'rejected': True,
                        'rejection_reason': 'Maximum exposure reached',
                        'max_exposure': max_allowed_exposure,
                        'current_exposure': self.current_exposure
                    }

            # Final validation
            risk_amount = position_size_sol * self.max_risk_per_trade

            # 🚀 FIXED: Proper percentage calculations for monitoring and transparency
            pct_of_active_capital = (position_size_sol / self.current_active_capital) if self.current_active_capital > 0 else 0
            pct_of_total_wallet = (position_size_sol / (self.current_wallet_balance + self.fee_reserve_sol)) if (self.current_wallet_balance + self.fee_reserve_sol) > 0 else 0

            return {
                'position_size_sol': position_size_sol,
                'position_size_usd': position_size_usd,
                'position_size_pct': adjusted_size_pct,  # Percentage of active capital used
                'position_size_pct_of_active': pct_of_active_capital,  # Actual percentage of active capital
                'position_size_pct_of_total': pct_of_total_wallet,  # Percentage of total wallet
                'risk_amount_sol': risk_amount,
                'risk_amount_usd': risk_amount * self.sol_price_usd,
                'signal_strength': signal_strength,
                'strategy': strategy,
                'market_regime': market_regime,
                'volatility': volatility,
                'multipliers': {
                    'signal': signal_multiplier,
                    'strategy': strategy_multiplier,
                    'regime': regime_multiplier,
                    'volatility': volatility_multiplier
                },
                'rejected': False,
                'fee_optimized': position_size_usd >= effective_min_trade_usd,
                'active_capital_sol': self.current_active_capital,
                'total_wallet_sol': self.current_wallet_balance + self.fee_reserve_sol,  # Include fee reserve in total
                'available_balance_sol': self.current_wallet_balance,  # Available after fees
                'fee_reserve_sol': self.fee_reserve_sol,
                'reserve_balance_sol': self.reserve_balance,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                'position_size_sol': 0.0,
                'position_size_usd': 0.0,
                'position_size_pct': 0.0,
                'rejected': True,
                'rejection_reason': f'Calculation error: {str(e)}',
                'error': str(e)
            }

    def _get_strategy_multiplier(self, strategy: str) -> float:
        """Get position size multiplier for strategy."""
        strategy_multipliers = {
            'momentum': 1.0,
            'mean_reversion': 1.2,  # Slightly larger for mean reversion
            'breakout': 0.8,        # Smaller for breakout (higher risk)
            'momentum_strategy': 1.0,
            'breakout_strategy': 0.8
        }
        return strategy_multipliers.get(strategy.lower(), 1.0)

    def _get_regime_multiplier(self, regime: str) -> float:
        """Get position size multiplier for market regime."""
        regime_multipliers = {
            'trending': 1.2,    # Larger positions in trending markets
            'ranging': 1.0,     # Normal positions in ranging markets
            'volatile': 0.7,    # Smaller positions in volatile markets
            'choppy': 0.5,      # Much smaller in choppy markets
            'unknown': 0.8      # Conservative for unknown regimes
        }
        return regime_multipliers.get(regime.lower(), 1.0)

    def _get_volatility_multiplier(self, volatility: float) -> float:
        """Get position size multiplier based on volatility."""
        if volatility < 0.2:
            return 1.2      # Low volatility - larger positions
        elif volatility < 0.5:
            return 1.0      # Normal volatility - normal positions
        elif volatility < 0.8:
            return 0.8      # High volatility - smaller positions
        else:
            return 0.6      # Very high volatility - much smaller positions

    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status for monitoring."""
        exposure_pct_total = (self.current_exposure / self.current_wallet_balance) if self.current_wallet_balance > 0 else 0
        exposure_pct_active = (self.current_exposure / self.current_active_capital) if self.current_active_capital > 0 else 0

        return {
            'total_wallet_sol': self.current_wallet_balance,
            'total_wallet_usd': self.current_wallet_balance * self.sol_price_usd,
            'active_capital_sol': self.current_active_capital,
            'active_capital_usd': self.current_active_capital * self.sol_price_usd,
            'reserve_balance_sol': self.current_wallet_balance - self.current_active_capital,
            'reserve_balance_usd': (self.current_wallet_balance - self.current_active_capital) * self.sol_price_usd,
            'current_exposure_sol': self.current_exposure,
            'current_exposure_usd': self.current_exposure * self.sol_price_usd,
            'exposure_pct_of_total': exposure_pct_total,
            'exposure_pct_of_active': exposure_pct_active,
            'available_capital_sol': self.current_active_capital - self.current_exposure,
            'available_capital_usd': (self.current_active_capital - self.current_exposure) * self.sol_price_usd,
            'max_position_size_sol': self.current_active_capital * self.max_position_size_pct,
            'max_position_size_usd': self.current_active_capital * self.max_position_size_pct * self.sol_price_usd,
            'sol_price_usd': self.sol_price_usd,
            'strategy_active': True,
            'timestamp': datetime.now().isoformat()
        }

    def save_state(self, filepath: str):
        """Save current state to file."""
        state = {
            'config': self.config,
            'portfolio_status': self.get_portfolio_status(),
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Position sizer state saved to {filepath}")

    def load_state(self, filepath: str):
        """Load state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            # Update from saved state if needed
            logger.info(f"Position sizer state loaded from {filepath}")
            return True

        except Exception as e:
            logger.warning(f"Could not load state from {filepath}: {e}")
            return False


def create_production_position_sizer(config_path: str = "config/live_production.yaml") -> ProductionPositionSizer:
    """Create and initialize a production position sizer."""
    import yaml

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        sizer = ProductionPositionSizer(config)
        logger.info("Production position sizer created successfully")
        return sizer

    except Exception as e:
        logger.error(f"Failed to create production position sizer: {e}")
        raise
