"""
Strategy Selector for Synergy7 Trading System.

This module implements intelligent strategy selection based on market conditions,
performance metrics, and adaptive weighting for optimal strategy deployment.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class StrategySelector:
    """
    Intelligent strategy selector that chooses optimal strategies based on
    market conditions, performance metrics, and adaptive weights.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy selector.

        Args:
            config: Configuration dictionary with adaptive_weighting section
        """
        # Get configuration
        weighting_config = config.get("adaptive_weighting", {})

        # Basic configuration
        self.enabled = weighting_config.get("enabled", True)
        self.min_strategy_weight = weighting_config.get("min_strategy_weight", 0.1)
        self.max_strategy_weight = weighting_config.get("max_strategy_weight", 0.6)
        self.performance_lookback_days = weighting_config.get("performance_lookback_days", 14)

        # Selection parameters
        self.confidence_threshold = weighting_config.get("confidence_threshold", 0.6)
        self.regime_confidence_weight = weighting_config.get("regime_confidence_weight", 0.3)
        self.performance_weight = weighting_config.get("performance_weight", 0.4)
        self.risk_weight = weighting_config.get("risk_weight", 0.3)

        # Strategy availability tracking
        self.available_strategies = {}
        self.strategy_status = {}
        self.selection_history = []

        # Performance tracking
        self.strategy_performance_cache = {}
        self.last_selection_time = None

        logger.info("Initialized Strategy Selector")

    def register_strategy(self, strategy_name: str, strategy_config: Dict[str, Any]) -> None:
        """
        Register a strategy as available for selection.

        Args:
            strategy_name: Name of the strategy
            strategy_config: Strategy configuration
        """
        try:
            self.available_strategies[strategy_name] = {
                'config': strategy_config,
                'enabled': strategy_config.get('enabled', True),
                'min_confidence': strategy_config.get('min_confidence', 0.5),
                'preferred_regimes': strategy_config.get('preferred_regimes', []),
                'risk_level': strategy_config.get('risk_level', 'medium'),
                'registration_time': datetime.now().isoformat()
            }

            self.strategy_status[strategy_name] = {
                'active': False,
                'last_used': None,
                'selection_count': 0,
                'performance_score': 0.0
            }

            logger.info(f"Registered strategy: {strategy_name}")

        except Exception as e:
            logger.error(f"Error registering strategy {strategy_name}: {str(e)}")

    def update_strategy_status(self, strategy_name: str, active: bool,
                             performance_score: float = None) -> None:
        """
        Update strategy status and performance.

        Args:
            strategy_name: Name of the strategy
            active: Whether the strategy is currently active
            performance_score: Optional performance score update
        """
        try:
            if strategy_name not in self.strategy_status:
                logger.warning(f"Strategy {strategy_name} not registered")
                return

            self.strategy_status[strategy_name]['active'] = active

            if active:
                self.strategy_status[strategy_name]['last_used'] = datetime.now().isoformat()
                self.strategy_status[strategy_name]['selection_count'] += 1

            if performance_score is not None:
                self.strategy_status[strategy_name]['performance_score'] = performance_score

            logger.debug(f"Updated status for {strategy_name}: active={active}")

        except Exception as e:
            logger.error(f"Error updating strategy status for {strategy_name}: {str(e)}")

    def calculate_strategy_suitability(self, strategy_name: str, market_regime: str,
                                     regime_confidence: float,
                                     strategy_performance: Dict[str, Any]) -> float:
        """
        Calculate how suitable a strategy is for current market conditions.

        Args:
            strategy_name: Name of the strategy
            market_regime: Current market regime
            regime_confidence: Confidence in regime detection
            strategy_performance: Strategy performance metrics

        Returns:
            Suitability score (0.0 to 1.0)
        """
        try:
            if strategy_name not in self.available_strategies:
                return 0.0

            strategy_config = self.available_strategies[strategy_name]

            # Check if strategy is enabled
            if not strategy_config.get('enabled', True):
                return 0.0

            # Base suitability score
            suitability_score = 0.5

            # Regime suitability
            preferred_regimes = strategy_config.get('preferred_regimes', [])
            if preferred_regimes:
                if market_regime in preferred_regimes:
                    regime_bonus = 0.3 * regime_confidence
                else:
                    regime_bonus = -0.2 * regime_confidence
                suitability_score += regime_bonus * self.regime_confidence_weight

            # 🔧 PHASE 4: RANGING MARKET BOOST - Extra suitability for ranging markets
            if market_regime == 'ranging':
                # Check if strategy has ranging suitability defined
                regime_suitability = strategy_config.get('regime_suitability', {})
                ranging_suitability = regime_suitability.get('ranging', 0.5)

                # Boost suitability for strategies good in ranging markets
                if ranging_suitability >= 0.7:
                    suitability_score += 0.2  # 20% boost for ranging-friendly strategies
                    logger.debug(f"🔧 RANGING BOOST: {strategy_name} +0.2 suitability (ranging-friendly)")
                elif ranging_suitability >= 0.5:
                    suitability_score += 0.1  # 10% boost for moderate ranging strategies
                    logger.debug(f"🔧 RANGING BOOST: {strategy_name} +0.1 suitability (ranging-moderate)")

            # Performance suitability
            if strategy_performance:
                sharpe_ratio = strategy_performance.get('sharpe_ratio', 0.0)
                win_rate = strategy_performance.get('win_rate', 0.0)
                recent_pnl = strategy_performance.get('recent_pnl_7d', 0.0)
                max_drawdown = strategy_performance.get('max_drawdown', 0.0)

                # Performance score (0 to 1)
                performance_score = 0.0

                # Sharpe ratio component
                if sharpe_ratio > 1.0:
                    performance_score += 0.3
                elif sharpe_ratio > 0.5:
                    performance_score += 0.2
                elif sharpe_ratio > 0:
                    performance_score += 0.1

                # Win rate component
                if win_rate > 0.6:
                    performance_score += 0.25
                elif win_rate > 0.5:
                    performance_score += 0.15
                elif win_rate > 0.4:
                    performance_score += 0.05

                # Recent performance component
                if recent_pnl > 0.01:
                    performance_score += 0.25
                elif recent_pnl > 0:
                    performance_score += 0.1
                elif recent_pnl < -0.02:
                    performance_score -= 0.2

                # Drawdown component
                if max_drawdown > -0.05:
                    performance_score += 0.2
                elif max_drawdown > -0.1:
                    performance_score += 0.1
                elif max_drawdown < -0.2:
                    performance_score -= 0.3

                suitability_score += performance_score * self.performance_weight

            # Risk suitability
            strategy_risk = strategy_config.get('risk_level', 'medium')
            risk_adjustment = 0.0

            if strategy_risk == 'low':
                risk_adjustment = 0.1  # Slight preference for low risk
            elif strategy_risk == 'high':
                risk_adjustment = -0.1  # Slight penalty for high risk

            suitability_score += risk_adjustment * self.risk_weight

            # Ensure score is within bounds
            suitability_score = max(0.0, min(1.0, suitability_score))

            return suitability_score

        except Exception as e:
            logger.error(f"Error calculating suitability for {strategy_name}: {str(e)}")
            return 0.0

    def select_strategies(self, market_regime: str, regime_confidence: float,
                         strategy_weights: Dict[str, float],
                         strategy_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select strategies based on market conditions and weights.

        Args:
            market_regime: Current market regime
            regime_confidence: Confidence in regime detection
            strategy_weights: Current strategy weights
            strategy_performance: Strategy performance data

        Returns:
            List of selected strategies with allocation details
        """
        try:
            selected_strategies = []

            # Calculate suitability scores for all strategies
            suitability_scores = {}
            for strategy_name in self.available_strategies.keys():
                perf_data = strategy_performance.get(strategy_name, {})
                suitability = self.calculate_strategy_suitability(
                    strategy_name, market_regime, regime_confidence, perf_data
                )
                suitability_scores[strategy_name] = suitability

            # Select strategies based on weights and suitability
            for strategy_name, weight in strategy_weights.items():
                if strategy_name not in self.available_strategies:
                    continue

                suitability = suitability_scores.get(strategy_name, 0.0)

                # Determine if strategy should be selected
                selection_score = weight * suitability

                # 🔧 PHASE 4: TUNED FOR RANGING MARKETS - More lenient selection criteria
                min_confidence = self.available_strategies[strategy_name].get('min_confidence', 0.5)
                should_select = (
                    selection_score >= self.confidence_threshold and
                    suitability >= min_confidence and
                    weight >= self.min_strategy_weight
                )

                # 🔧 PHASE 4: RANGING MARKET BOOST - Special handling for ranging markets
                if not should_select and market_regime == 'ranging':
                    # Lower thresholds for ranging markets
                    ranging_threshold = self.confidence_threshold * 0.5  # 50% of normal threshold
                    ranging_min_confidence = min_confidence * 0.5
                    ranging_min_weight = self.min_strategy_weight * 0.1  # 10% of normal min weight

                    should_select = (
                        selection_score >= ranging_threshold and
                        suitability >= ranging_min_confidence and
                        weight >= ranging_min_weight
                    )

                    if should_select:
                        logger.info(f"🔧 RANGING MARKET BOOST: Selected {strategy_name} with relaxed criteria")

                if should_select:
                    # Calculate effective allocation
                    effective_allocation = min(weight, self.max_strategy_weight)

                    strategy_selection = {
                        'strategy_name': strategy_name,
                        'weight': weight,
                        'effective_allocation': effective_allocation,
                        'suitability_score': suitability,
                        'selection_score': selection_score,
                        'market_regime': market_regime,
                        'regime_confidence': regime_confidence,
                        'selection_reason': self._get_selection_reason(
                            strategy_name, suitability, weight, market_regime
                        ),
                        'risk_level': self.available_strategies[strategy_name].get('risk_level', 'medium'),
                        'selection_timestamp': datetime.now().isoformat()
                    }

                    selected_strategies.append(strategy_selection)

                    # Update strategy status
                    self.update_strategy_status(strategy_name, True, suitability)
                else:
                    # Update strategy status as inactive
                    self.update_strategy_status(strategy_name, False)

            # Sort by selection score (highest first)
            selected_strategies.sort(key=lambda x: x['selection_score'], reverse=True)

            # Normalize allocations if needed
            total_allocation = sum(s['effective_allocation'] for s in selected_strategies)
            if total_allocation > 1.0:
                for strategy in selected_strategies:
                    strategy['effective_allocation'] /= total_allocation

            # Store selection in history
            self.selection_history.append({
                'timestamp': datetime.now().isoformat(),
                'market_regime': market_regime,
                'regime_confidence': regime_confidence,
                'selected_strategies': [s['strategy_name'] for s in selected_strategies],
                'total_strategies': len(selected_strategies),
                'total_allocation': sum(s['effective_allocation'] for s in selected_strategies)
            })

            # Maintain history size
            if len(self.selection_history) > 100:
                self.selection_history.pop(0)

            self.last_selection_time = datetime.now()

            logger.info(f"Selected {len(selected_strategies)} strategies for regime {market_regime}")
            for strategy in selected_strategies:
                logger.debug(f"  {strategy['strategy_name']}: {strategy['effective_allocation']:.3f} allocation")

            return selected_strategies

        except Exception as e:
            logger.error(f"Error selecting strategies: {str(e)}")
            return []

    def _get_selection_reason(self, strategy_name: str, suitability: float,
                            weight: float, market_regime: str) -> str:
        """
        Generate human-readable selection reason.

        Args:
            strategy_name: Name of the strategy
            suitability: Suitability score
            weight: Strategy weight
            market_regime: Market regime

        Returns:
            Selection reason string
        """
        try:
            reasons = []

            if suitability > 0.8:
                reasons.append("excellent suitability")
            elif suitability > 0.6:
                reasons.append("good suitability")
            else:
                reasons.append("adequate suitability")

            if weight > 0.3:
                reasons.append("high allocation weight")
            elif weight > 0.15:
                reasons.append("medium allocation weight")
            else:
                reasons.append("low allocation weight")

            strategy_config = self.available_strategies.get(strategy_name, {})
            preferred_regimes = strategy_config.get('preferred_regimes', [])
            if market_regime in preferred_regimes:
                reasons.append(f"preferred for {market_regime} regime")

            return ", ".join(reasons)

        except Exception as e:
            logger.warning(f"Error generating selection reason: {str(e)}")
            return "performance-based selection"

    def get_strategy_recommendations(self, market_regime: str,
                                   strategy_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get strategy recommendations for current market conditions.

        Args:
            market_regime: Current market regime
            strategy_performance: Strategy performance data

        Returns:
            List of strategy recommendations
        """
        try:
            recommendations = []

            # Calculate suitability for all strategies
            for strategy_name in self.available_strategies.keys():
                perf_data = strategy_performance.get(strategy_name, {})
                suitability = self.calculate_strategy_suitability(
                    strategy_name, market_regime, 0.8, perf_data  # Assume high regime confidence
                )

                strategy_config = self.available_strategies[strategy_name]
                current_status = self.strategy_status.get(strategy_name, {})

                recommendation = {
                    'strategy_name': strategy_name,
                    'suitability_score': suitability,
                    'current_active': current_status.get('active', False),
                    'risk_level': strategy_config.get('risk_level', 'medium'),
                    'preferred_regimes': strategy_config.get('preferred_regimes', []),
                    'recommendation': self._get_recommendation_type(suitability, current_status),
                    'reason': self._get_recommendation_reason(suitability, market_regime, strategy_config)
                }

                recommendations.append(recommendation)

            # Sort by suitability score
            recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting strategy recommendations: {str(e)}")
            return []

    def _get_recommendation_type(self, suitability: float, current_status: Dict[str, Any]) -> str:
        """Get recommendation type based on suitability and current status."""
        is_active = current_status.get('active', False)

        if suitability > 0.7:
            return "activate" if not is_active else "maintain"
        elif suitability > 0.4:
            return "consider" if not is_active else "monitor"
        else:
            return "avoid" if not is_active else "deactivate"

    def _get_recommendation_reason(self, suitability: float, market_regime: str,
                                 strategy_config: Dict[str, Any]) -> str:
        """Get recommendation reason."""
        preferred_regimes = strategy_config.get('preferred_regimes', [])

        if suitability > 0.7:
            if market_regime in preferred_regimes:
                return f"High suitability and preferred for {market_regime} regime"
            else:
                return "High suitability based on performance metrics"
        elif suitability > 0.4:
            return "Moderate suitability, monitor performance"
        else:
            if market_regime in preferred_regimes:
                return f"Low performance despite regime preference"
            else:
                return f"Low suitability for {market_regime} regime"

    def get_selection_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy selection summary.

        Returns:
            Dictionary with selection summary
        """
        try:
            active_strategies = [name for name, status in self.strategy_status.items()
                               if status.get('active', False)]

            return {
                'enabled': self.enabled,
                'total_registered_strategies': len(self.available_strategies),
                'active_strategies': len(active_strategies),
                'active_strategy_names': active_strategies,
                'last_selection_time': self.last_selection_time.isoformat() if self.last_selection_time else None,
                'selection_history_length': len(self.selection_history),
                'recent_selections': self.selection_history[-5:] if self.selection_history else [],
                'strategy_status': self.strategy_status.copy(),
                'configuration': {
                    'confidence_threshold': self.confidence_threshold,
                    'min_strategy_weight': self.min_strategy_weight,
                    'max_strategy_weight': self.max_strategy_weight
                }
            }

        except Exception as e:
            logger.error(f"Error getting selection summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
