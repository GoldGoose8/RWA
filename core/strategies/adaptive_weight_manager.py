"""
Adaptive Strategy Weight Manager for Synergy7 Trading System.

This module implements dynamic weight adjustment based on strategy performance,
market conditions, and risk metrics for optimal portfolio allocation.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

# Configure logging
logger = logging.getLogger(__name__)

class AdaptiveWeightManager:
    """
    Manages dynamic strategy weight adjustments based on performance and market conditions.
    
    This class implements sophisticated weight adjustment algorithms that consider
    performance attribution, risk metrics, market regimes, and correlation effects.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adaptive weight manager.
        
        Args:
            config: Configuration dictionary with adaptive_weighting section
        """
        # Get adaptive weighting configuration
        weighting_config = config.get("adaptive_weighting", {})
        
        # Basic configuration
        self.enabled = weighting_config.get("enabled", True)
        self.learning_rate = weighting_config.get("learning_rate", 0.01)
        self.weight_update_interval = weighting_config.get("weight_update_interval", 3600)  # seconds
        self.min_strategy_weight = weighting_config.get("min_strategy_weight", 0.1)
        self.max_strategy_weight = weighting_config.get("max_strategy_weight", 0.6)
        self.performance_lookback_days = weighting_config.get("performance_lookback_days", 14)
        
        # Weight adjustment parameters
        self.momentum_factor = weighting_config.get("momentum_factor", 0.3)
        self.mean_reversion_factor = weighting_config.get("mean_reversion_factor", 0.2)
        self.risk_adjustment_factor = weighting_config.get("risk_adjustment_factor", 0.5)
        self.regime_adjustment_factor = weighting_config.get("regime_adjustment_factor", 0.3)
        
        # Performance thresholds
        self.performance_threshold_high = weighting_config.get("performance_threshold_high", 0.02)
        self.performance_threshold_low = weighting_config.get("performance_threshold_low", -0.01)
        self.sharpe_threshold = weighting_config.get("sharpe_threshold", 1.0)
        self.drawdown_threshold = weighting_config.get("drawdown_threshold", -0.1)
        
        # Current state
        self.current_weights = {}
        self.target_weights = {}
        self.weight_history = deque(maxlen=1000)
        self.performance_history = defaultdict(deque)
        self.last_update_time = None
        
        # Adjustment tracking
        self.adjustment_reasons = {}
        self.weight_changes = deque(maxlen=100)
        
        logger.info("Initialized Adaptive Weight Manager")
    
    def calculate_performance_scores(self, strategy_performance: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate performance scores for each strategy.
        
        Args:
            strategy_performance: Dictionary of strategy performance metrics
            
        Returns:
            Dictionary of performance scores (0.0 to 1.0)
        """
        try:
            scores = {}
            
            # Collect metrics for normalization
            sharpe_ratios = []
            returns = []
            drawdowns = []
            win_rates = []
            
            for strategy_name, performance in strategy_performance.items():
                if performance and performance.get('total_trades', 0) >= 5:
                    sharpe_ratios.append(performance.get('sharpe_ratio', 0.0))
                    returns.append(performance.get('net_pnl', 0.0))
                    drawdowns.append(performance.get('max_drawdown', 0.0))
                    win_rates.append(performance.get('win_rate', 0.0))
            
            if not sharpe_ratios:
                return {}
            
            # Calculate normalization parameters
            sharpe_mean, sharpe_std = np.mean(sharpe_ratios), np.std(sharpe_ratios)
            return_mean, return_std = np.mean(returns), np.std(returns)
            dd_mean, dd_std = np.mean(drawdowns), np.std(drawdowns)
            wr_mean, wr_std = np.mean(win_rates), np.std(win_rates)
            
            # Calculate scores for each strategy
            for strategy_name, performance in strategy_performance.items():
                if not performance or performance.get('total_trades', 0) < 5:
                    scores[strategy_name] = 0.0
                    continue
                
                # Normalize metrics
                sharpe = performance.get('sharpe_ratio', 0.0)
                net_return = performance.get('net_pnl', 0.0)
                max_dd = performance.get('max_drawdown', 0.0)
                win_rate = performance.get('win_rate', 0.0)
                
                # Z-score normalization (with bounds)
                sharpe_score = max(0, min(1, (sharpe - sharpe_mean) / max(sharpe_std, 0.1) * 0.2 + 0.5))
                return_score = max(0, min(1, (net_return - return_mean) / max(return_std, 0.001) * 0.2 + 0.5))
                dd_score = max(0, min(1, -(max_dd - dd_mean) / max(dd_std, 0.01) * 0.2 + 0.5))
                wr_score = max(0, min(1, (win_rate - wr_mean) / max(wr_std, 0.1) * 0.2 + 0.5))
                
                # Composite score with weights
                composite_score = (
                    sharpe_score * 0.35 +
                    return_score * 0.25 +
                    dd_score * 0.25 +
                    wr_score * 0.15
                )
                
                scores[strategy_name] = max(0.0, min(1.0, composite_score))
            
            return scores
        
        except Exception as e:
            logger.error(f"Error calculating performance scores: {str(e)}")
            return {}
    
    def calculate_regime_adjustments(self, market_regime: str, strategy_performance: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate regime-based weight adjustments.
        
        Args:
            market_regime: Current market regime
            strategy_performance: Strategy performance data
            
        Returns:
            Dictionary of regime adjustment factors
        """
        try:
            adjustments = {}
            
            # Regime-specific strategy preferences
            regime_preferences = {
                'trending_up': {
                    'momentum_strategy': 1.3,
                    'breakout_strategy': 1.2,
                    'mean_reversion': 0.8,
                    'scalping_strategy': 0.9
                },
                'trending_down': {
                    'momentum_strategy': 0.7,
                    'mean_reversion': 1.2,
                    'scalping_strategy': 1.1,
                    'breakout_strategy': 0.8
                },
                'ranging': {
                    'mean_reversion': 1.4,
                    'scalping_strategy': 1.2,
                    'momentum_strategy': 0.7,
                    'breakout_strategy': 0.6
                },
                'volatile': {
                    'scalping_strategy': 0.8,
                    'mean_reversion': 1.1,
                    'momentum_strategy': 0.9,
                    'breakout_strategy': 0.7
                },
                'choppy': {
                    'scalping_strategy': 0.6,
                    'momentum_strategy': 0.5,
                    'mean_reversion': 0.8,
                    'breakout_strategy': 0.4
                }
            }
            
            # Get regime preferences
            preferences = regime_preferences.get(market_regime, {})
            
            # Calculate adjustments for each strategy
            for strategy_name in strategy_performance.keys():
                # Check for exact match first
                if strategy_name in preferences:
                    adjustments[strategy_name] = preferences[strategy_name]
                else:
                    # Check for partial matches (e.g., "momentum" in "momentum_sol_usdc")
                    adjustment = 1.0
                    for pref_strategy, pref_value in preferences.items():
                        if pref_strategy.replace('_', '') in strategy_name.replace('_', '').lower():
                            adjustment = pref_value
                            break
                    adjustments[strategy_name] = adjustment
            
            return adjustments
        
        except Exception as e:
            logger.error(f"Error calculating regime adjustments: {str(e)}")
            return {}
    
    def calculate_risk_adjustments(self, strategy_performance: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate risk-based weight adjustments.
        
        Args:
            strategy_performance: Strategy performance data
            
        Returns:
            Dictionary of risk adjustment factors
        """
        try:
            adjustments = {}
            
            for strategy_name, performance in strategy_performance.items():
                if not performance:
                    adjustments[strategy_name] = 0.5
                    continue
                
                # Risk metrics
                sharpe_ratio = performance.get('sharpe_ratio', 0.0)
                max_drawdown = performance.get('max_drawdown', 0.0)
                volatility = performance.get('volatility', 0.0)
                
                # Risk adjustment factors
                sharpe_adjustment = 1.0
                if sharpe_ratio > self.sharpe_threshold:
                    sharpe_adjustment = 1.2
                elif sharpe_ratio < 0:
                    sharpe_adjustment = 0.5
                
                drawdown_adjustment = 1.0
                if max_drawdown < self.drawdown_threshold:
                    drawdown_adjustment = 0.6
                elif max_drawdown > -0.05:
                    drawdown_adjustment = 1.1
                
                volatility_adjustment = 1.0
                if volatility > 0.05:  # High volatility
                    volatility_adjustment = 0.8
                elif volatility < 0.02:  # Low volatility
                    volatility_adjustment = 1.1
                
                # Combine adjustments
                combined_adjustment = (
                    sharpe_adjustment * 0.4 +
                    drawdown_adjustment * 0.4 +
                    volatility_adjustment * 0.2
                )
                
                adjustments[strategy_name] = max(0.3, min(1.5, combined_adjustment))
            
            return adjustments
        
        except Exception as e:
            logger.error(f"Error calculating risk adjustments: {str(e)}")
            return {}
    
    def calculate_target_weights(self, strategy_performance: Dict[str, Any], 
                               market_regime: str = "unknown") -> Dict[str, float]:
        """
        Calculate target weights for strategies based on performance and market conditions.
        
        Args:
            strategy_performance: Strategy performance data
            market_regime: Current market regime
            
        Returns:
            Dictionary of target weights
        """
        try:
            if not strategy_performance:
                return {}
            
            # Calculate performance scores
            performance_scores = self.calculate_performance_scores(strategy_performance)
            
            # Calculate regime adjustments
            regime_adjustments = self.calculate_regime_adjustments(market_regime, strategy_performance)
            
            # Calculate risk adjustments
            risk_adjustments = self.calculate_risk_adjustments(strategy_performance)
            
            # Combine scores and adjustments
            combined_scores = {}
            for strategy_name in strategy_performance.keys():
                perf_score = performance_scores.get(strategy_name, 0.0)
                regime_adj = regime_adjustments.get(strategy_name, 1.0)
                risk_adj = risk_adjustments.get(strategy_name, 1.0)
                
                # Weighted combination
                combined_score = (
                    perf_score * (1 - self.regime_adjustment_factor - self.risk_adjustment_factor) +
                    perf_score * regime_adj * self.regime_adjustment_factor +
                    perf_score * risk_adj * self.risk_adjustment_factor
                )
                
                combined_scores[strategy_name] = max(0.0, combined_score)
            
            # Normalize to weights
            total_score = sum(combined_scores.values())
            if total_score == 0:
                # Equal weights fallback
                num_strategies = len(strategy_performance)
                target_weights = {name: 1.0/num_strategies for name in strategy_performance.keys()}
            else:
                # Proportional weights
                target_weights = {name: score/total_score for name, score in combined_scores.items()}
            
            # Apply weight constraints
            for strategy_name in target_weights.keys():
                target_weights[strategy_name] = max(
                    self.min_strategy_weight,
                    min(self.max_strategy_weight, target_weights[strategy_name])
                )
            
            # Renormalize after constraints
            total_weight = sum(target_weights.values())
            if total_weight > 0:
                target_weights = {name: weight/total_weight for name, weight in target_weights.items()}
            
            return target_weights
        
        except Exception as e:
            logger.error(f"Error calculating target weights: {str(e)}")
            return {}
    
    def update_weights(self, strategy_performance: Dict[str, Any], 
                      market_regime: str = "unknown", 
                      force_update: bool = False) -> Dict[str, float]:
        """
        Update strategy weights based on performance and market conditions.
        
        Args:
            strategy_performance: Strategy performance data
            market_regime: Current market regime
            force_update: Force update regardless of time interval
            
        Returns:
            Updated strategy weights
        """
        try:
            current_time = datetime.now()
            
            # Check if update is needed
            if not force_update and self.last_update_time:
                time_since_update = (current_time - self.last_update_time).total_seconds()
                if time_since_update < self.weight_update_interval:
                    return self.current_weights.copy()
            
            # Calculate target weights
            target_weights = self.calculate_target_weights(strategy_performance, market_regime)
            
            if not target_weights:
                return self.current_weights.copy()
            
            # Initialize current weights if empty
            if not self.current_weights:
                self.current_weights = {name: 1.0/len(target_weights) for name in target_weights.keys()}
            
            # Gradual weight adjustment using learning rate
            new_weights = {}
            weight_changes = {}
            
            for strategy_name in target_weights.keys():
                current_weight = self.current_weights.get(strategy_name, 1.0/len(target_weights))
                target_weight = target_weights[strategy_name]
                
                # Gradual adjustment
                weight_change = (target_weight - current_weight) * self.learning_rate
                new_weight = current_weight + weight_change
                
                # Apply constraints
                new_weight = max(self.min_strategy_weight, min(self.max_strategy_weight, new_weight))
                
                new_weights[strategy_name] = new_weight
                weight_changes[strategy_name] = weight_change
            
            # Normalize weights
            total_weight = sum(new_weights.values())
            if total_weight > 0:
                new_weights = {name: weight/total_weight for name, weight in new_weights.items()}
            
            # Store weight changes
            self.weight_changes.append({
                'timestamp': current_time.isoformat(),
                'changes': weight_changes.copy(),
                'market_regime': market_regime,
                'reason': 'performance_based_adjustment'
            })
            
            # Update current weights
            self.current_weights = new_weights.copy()
            self.target_weights = target_weights.copy()
            self.last_update_time = current_time
            
            # Store in history
            self.weight_history.append({
                'timestamp': current_time.isoformat(),
                'weights': new_weights.copy(),
                'target_weights': target_weights.copy(),
                'market_regime': market_regime
            })
            
            logger.info(f"Updated strategy weights for regime {market_regime}")
            for name, weight in new_weights.items():
                logger.debug(f"  {name}: {weight:.3f}")
            
            return new_weights.copy()
        
        except Exception as e:
            logger.error(f"Error updating weights: {str(e)}")
            return self.current_weights.copy()
    
    def get_weight_recommendations(self, strategy_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get weight adjustment recommendations.
        
        Args:
            strategy_performance: Strategy performance data
            
        Returns:
            List of weight adjustment recommendations
        """
        try:
            recommendations = []
            
            if not self.current_weights or not self.target_weights:
                return recommendations
            
            for strategy_name in self.current_weights.keys():
                current_weight = self.current_weights[strategy_name]
                target_weight = self.target_weights.get(strategy_name, current_weight)
                
                weight_diff = target_weight - current_weight
                
                if abs(weight_diff) > 0.05:  # 5% threshold
                    action = "increase" if weight_diff > 0 else "decrease"
                    magnitude = "large" if abs(weight_diff) > 0.15 else "medium"
                    
                    # Get performance metrics for reasoning
                    performance = strategy_performance.get(strategy_name, {})
                    sharpe = performance.get('sharpe_ratio', 0.0)
                    recent_pnl = performance.get('recent_pnl_7d', 0.0)
                    
                    reason = f"Performance-based adjustment (Sharpe: {sharpe:.2f}, Recent PnL: {recent_pnl:.4f})"
                    
                    recommendations.append({
                        'strategy': strategy_name,
                        'action': action,
                        'magnitude': magnitude,
                        'current_weight': current_weight,
                        'target_weight': target_weight,
                        'weight_change': weight_diff,
                        'reason': reason
                    })
            
            # Sort by magnitude of change
            recommendations.sort(key=lambda x: abs(x['weight_change']), reverse=True)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting weight recommendations: {str(e)}")
            return []
    
    def get_weight_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive weight management summary.
        
        Returns:
            Dictionary with weight management summary
        """
        try:
            return {
                'enabled': self.enabled,
                'current_weights': self.current_weights.copy(),
                'target_weights': self.target_weights.copy(),
                'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
                'weight_update_interval': self.weight_update_interval,
                'learning_rate': self.learning_rate,
                'weight_constraints': {
                    'min_weight': self.min_strategy_weight,
                    'max_weight': self.max_strategy_weight
                },
                'weight_history_length': len(self.weight_history),
                'recent_changes': list(self.weight_changes)[-5:] if self.weight_changes else []
            }
        
        except Exception as e:
            logger.error(f"Error getting weight summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
