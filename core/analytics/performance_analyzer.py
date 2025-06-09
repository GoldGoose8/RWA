"""
Performance Analyzer for Synergy7 Trading System.

This module analyzes strategy effectiveness, identifies underperforming strategies,
and generates optimization recommendations for portfolio management.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Configure logging
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """
    Analyzes strategy performance and provides optimization recommendations.
    
    This class provides comprehensive performance analysis including trend detection,
    underperformance identification, and strategy optimization recommendations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the performance analyzer.
        
        Args:
            config: Configuration dictionary with strategy_attribution section
        """
        # Get configuration
        attribution_config = config.get("strategy_attribution", {})
        
        # Basic configuration
        self.enabled = attribution_config.get("enabled", True)
        self.performance_decay_factor = attribution_config.get("performance_decay_factor", 0.95)
        self.rebalance_threshold = attribution_config.get("rebalance_threshold", 0.1)
        self.min_trades_for_analysis = attribution_config.get("min_trades_for_attribution", 10)
        
        # Analysis parameters
        self.underperformance_threshold = -0.02  # 2% negative return threshold
        self.volatility_threshold = 0.05  # 5% daily volatility threshold
        self.drawdown_threshold = -0.1  # 10% maximum drawdown threshold
        self.sharpe_threshold = 0.5  # Minimum acceptable Sharpe ratio
        
        # Trend analysis parameters
        self.trend_lookback_days = 7
        self.trend_significance_threshold = 0.05  # 5% change threshold
        
        # Performance tracking
        self.analysis_history = []
        self.recommendations_history = []
        self.last_analysis_time = None
        
        logger.info("Initialized Performance Analyzer")
    
    def analyze_strategy_trends(self, strategy_performance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze performance trends for strategies.
        
        Args:
            strategy_performance: Dictionary of strategy performance data
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            trend_analysis = {}
            
            for strategy_name, performance in strategy_performance.items():
                if not performance or 'recent_pnl_7d' not in performance:
                    continue
                
                # Get recent performance metrics
                recent_pnl = performance.get('recent_pnl_7d', 0.0)
                total_pnl = performance.get('net_pnl', 0.0)
                total_trades = performance.get('total_trades', 0)
                
                if total_trades < self.min_trades_for_analysis:
                    continue
                
                # Calculate average daily PnL
                avg_daily_pnl = total_pnl / max(total_trades, 1)
                recent_avg_daily_pnl = recent_pnl / 7  # Last 7 days average
                
                # Determine trend
                if abs(recent_avg_daily_pnl - avg_daily_pnl) < self.trend_significance_threshold:
                    trend = 'stable'
                elif recent_avg_daily_pnl > avg_daily_pnl:
                    trend = 'improving'
                else:
                    trend = 'declining'
                
                # Calculate trend strength
                if avg_daily_pnl != 0:
                    trend_strength = abs((recent_avg_daily_pnl - avg_daily_pnl) / avg_daily_pnl)
                else:
                    trend_strength = 0.0
                
                # Performance classification
                performance_class = self._classify_performance(performance)
                
                trend_analysis[strategy_name] = {
                    'trend': trend,
                    'trend_strength': trend_strength,
                    'recent_avg_daily_pnl': recent_avg_daily_pnl,
                    'overall_avg_daily_pnl': avg_daily_pnl,
                    'performance_class': performance_class,
                    'total_trades': total_trades
                }
            
            return trend_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing strategy trends: {str(e)}")
            return {}
    
    def _classify_performance(self, performance: Dict[str, Any]) -> str:
        """
        Classify strategy performance into categories.
        
        Args:
            performance: Strategy performance metrics
            
        Returns:
            Performance classification string
        """
        try:
            sharpe_ratio = performance.get('sharpe_ratio', 0.0)
            max_drawdown = performance.get('max_drawdown', 0.0)
            win_rate = performance.get('win_rate', 0.0)
            net_pnl = performance.get('net_pnl', 0.0)
            
            # Excellent performance
            if (sharpe_ratio > 1.5 and max_drawdown > -0.05 and win_rate > 0.6 and net_pnl > 0):
                return 'excellent'
            
            # Good performance
            elif (sharpe_ratio > 1.0 and max_drawdown > -0.1 and win_rate > 0.5 and net_pnl > 0):
                return 'good'
            
            # Average performance
            elif (sharpe_ratio > 0.5 and max_drawdown > -0.15 and net_pnl > 0):
                return 'average'
            
            # Poor performance
            elif (sharpe_ratio > 0 and max_drawdown > -0.25):
                return 'poor'
            
            # Very poor performance
            else:
                return 'very_poor'
        
        except Exception as e:
            logger.warning(f"Error classifying performance: {str(e)}")
            return 'unknown'
    
    def identify_underperforming_strategies(self, strategy_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify strategies that are underperforming.
        
        Args:
            strategy_performance: Dictionary of strategy performance data
            
        Returns:
            List of underperforming strategies with details
        """
        try:
            underperforming = []
            
            for strategy_name, performance in strategy_performance.items():
                if not performance:
                    continue
                
                issues = []
                severity = 'low'
                
                # Check various performance metrics
                sharpe_ratio = performance.get('sharpe_ratio', 0.0)
                max_drawdown = performance.get('max_drawdown', 0.0)
                win_rate = performance.get('win_rate', 0.0)
                net_pnl = performance.get('net_pnl', 0.0)
                volatility = performance.get('volatility', 0.0)
                recent_pnl = performance.get('recent_pnl_7d', 0.0)
                
                # Check for negative returns
                if net_pnl < 0:
                    issues.append('negative_total_returns')
                    severity = 'high'
                
                # Check for poor Sharpe ratio
                if sharpe_ratio < self.sharpe_threshold:
                    issues.append('low_sharpe_ratio')
                    if sharpe_ratio < 0:
                        severity = 'high'
                    elif severity == 'low':
                        severity = 'medium'
                
                # Check for excessive drawdown
                if max_drawdown < self.drawdown_threshold:
                    issues.append('excessive_drawdown')
                    severity = 'high'
                
                # Check for high volatility
                if volatility > self.volatility_threshold:
                    issues.append('high_volatility')
                    if severity == 'low':
                        severity = 'medium'
                
                # Check for poor recent performance
                if recent_pnl < self.underperformance_threshold:
                    issues.append('poor_recent_performance')
                    if severity == 'low':
                        severity = 'medium'
                
                # Check for low win rate
                if win_rate < 0.4:
                    issues.append('low_win_rate')
                    if severity == 'low':
                        severity = 'medium'
                
                # If any issues found, add to underperforming list
                if issues:
                    underperforming.append({
                        'strategy_name': strategy_name,
                        'issues': issues,
                        'severity': severity,
                        'performance_metrics': {
                            'sharpe_ratio': sharpe_ratio,
                            'max_drawdown': max_drawdown,
                            'win_rate': win_rate,
                            'net_pnl': net_pnl,
                            'volatility': volatility,
                            'recent_pnl_7d': recent_pnl
                        }
                    })
            
            # Sort by severity (high -> medium -> low)
            severity_order = {'high': 3, 'medium': 2, 'low': 1}
            underperforming.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
            
            return underperforming
        
        except Exception as e:
            logger.error(f"Error identifying underperforming strategies: {str(e)}")
            return []
    
    def generate_optimization_recommendations(self, strategy_performance: Dict[str, Any], 
                                            current_weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations for strategy allocation.
        
        Args:
            strategy_performance: Dictionary of strategy performance data
            current_weights: Current strategy weights
            
        Returns:
            List of optimization recommendations
        """
        try:
            recommendations = []
            
            # Analyze trends
            trend_analysis = self.analyze_strategy_trends(strategy_performance)
            
            # Identify underperforming strategies
            underperforming = self.identify_underperforming_strategies(strategy_performance)
            
            # Calculate performance scores for ranking
            strategy_scores = {}
            for strategy_name, performance in strategy_performance.items():
                if performance and performance.get('total_trades', 0) >= self.min_trades_for_analysis:
                    # Composite score based on multiple metrics
                    sharpe = performance.get('sharpe_ratio', 0.0)
                    win_rate = performance.get('win_rate', 0.0)
                    profit_factor = performance.get('profit_factor', 1.0)
                    max_dd = performance.get('max_drawdown', 0.0)
                    
                    # Normalize and weight metrics
                    score = (
                        sharpe * 0.3 +  # Sharpe ratio weight
                        win_rate * 0.2 +  # Win rate weight
                        min(profit_factor, 5.0) * 0.2 +  # Profit factor (capped at 5)
                        max(0, 1 + max_dd/0.2) * 0.3  # Drawdown penalty
                    )
                    
                    strategy_scores[strategy_name] = score
            
            # Sort strategies by score
            sorted_strategies = sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Generate weight adjustment recommendations
            if len(sorted_strategies) > 1:
                top_performers = sorted_strategies[:len(sorted_strategies)//2]
                bottom_performers = sorted_strategies[len(sorted_strategies)//2:]
                
                # Recommend increasing allocation to top performers
                for strategy_name, score in top_performers:
                    current_weight = current_weights.get(strategy_name, 0.0)
                    trend = trend_analysis.get(strategy_name, {}).get('trend', 'stable')
                    
                    if trend == 'improving' and current_weight < 0.3:  # Cap at 30%
                        recommended_weight = min(0.3, current_weight * 1.2)
                        recommendations.append({
                            'type': 'increase_allocation',
                            'strategy': strategy_name,
                            'current_weight': current_weight,
                            'recommended_weight': recommended_weight,
                            'reason': f'Strong performance (score: {score:.2f}) and improving trend',
                            'priority': 'medium'
                        })
                
                # Recommend decreasing allocation to bottom performers
                for strategy_name, score in bottom_performers:
                    current_weight = current_weights.get(strategy_name, 0.0)
                    trend = trend_analysis.get(strategy_name, {}).get('trend', 'stable')
                    
                    if trend == 'declining' and current_weight > 0.05:  # Minimum 5%
                        recommended_weight = max(0.05, current_weight * 0.8)
                        recommendations.append({
                            'type': 'decrease_allocation',
                            'strategy': strategy_name,
                            'current_weight': current_weight,
                            'recommended_weight': recommended_weight,
                            'reason': f'Poor performance (score: {score:.2f}) and declining trend',
                            'priority': 'medium'
                        })
            
            # Generate specific recommendations for underperforming strategies
            for underperformer in underperforming:
                strategy_name = underperformer['strategy_name']
                severity = underperformer['severity']
                issues = underperformer['issues']
                
                if severity == 'high':
                    recommendations.append({
                        'type': 'disable_strategy',
                        'strategy': strategy_name,
                        'current_weight': current_weights.get(strategy_name, 0.0),
                        'recommended_weight': 0.0,
                        'reason': f'Critical issues: {", ".join(issues)}',
                        'priority': 'high'
                    })
                elif severity == 'medium':
                    current_weight = current_weights.get(strategy_name, 0.0)
                    recommendations.append({
                        'type': 'reduce_allocation',
                        'strategy': strategy_name,
                        'current_weight': current_weight,
                        'recommended_weight': max(0.02, current_weight * 0.5),
                        'reason': f'Performance issues: {", ".join(issues)}',
                        'priority': 'medium'
                    })
            
            # Sort recommendations by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {str(e)}")
            return []
    
    def analyze_portfolio_performance(self, attribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze overall portfolio performance and provide insights.
        
        Args:
            attribution_data: Portfolio attribution data
            
        Returns:
            Dictionary with portfolio analysis
        """
        try:
            if not attribution_data or 'portfolio_metrics' not in attribution_data:
                return {}
            
            portfolio_metrics = attribution_data['portfolio_metrics']
            strategy_contributions = attribution_data.get('strategy_contributions', {})
            
            # Portfolio-level analysis
            total_pnl = portfolio_metrics.get('total_portfolio_pnl', 0.0)
            weighted_sharpe = portfolio_metrics.get('weighted_sharpe_ratio', 0.0)
            weighted_win_rate = portfolio_metrics.get('weighted_win_rate', 0.0)
            
            # Diversification analysis
            strategy_count = len(strategy_contributions)
            
            # Calculate concentration (Herfindahl index)
            weights = [contrib.get('weight', 0) for contrib in strategy_contributions.values()]
            herfindahl_index = sum(w**2 for w in weights) if weights else 1.0
            effective_strategies = 1 / herfindahl_index if herfindahl_index > 0 else 0
            
            # Top contributors analysis
            sorted_contributors = sorted(
                strategy_contributions.items(),
                key=lambda x: x[1].get('pnl_contribution', 0),
                reverse=True
            )
            
            top_3_contribution = sum(
                contrib.get('pnl_contribution', 0) 
                for _, contrib in sorted_contributors[:3]
            )
            top_3_percentage = (top_3_contribution / total_pnl * 100) if total_pnl != 0 else 0
            
            # Portfolio health assessment
            health_score = 0
            health_factors = []
            
            # Positive returns
            if total_pnl > 0:
                health_score += 25
                health_factors.append('positive_returns')
            
            # Good Sharpe ratio
            if weighted_sharpe > 1.0:
                health_score += 25
                health_factors.append('good_risk_adjusted_returns')
            elif weighted_sharpe > 0.5:
                health_score += 15
            
            # Good win rate
            if weighted_win_rate > 0.6:
                health_score += 20
                health_factors.append('high_win_rate')
            elif weighted_win_rate > 0.5:
                health_score += 10
            
            # Good diversification
            if effective_strategies > 3:
                health_score += 15
                health_factors.append('well_diversified')
            elif effective_strategies > 2:
                health_score += 10
            
            # Low concentration
            if top_3_percentage < 70:
                health_score += 15
                health_factors.append('low_concentration')
            elif top_3_percentage < 80:
                health_score += 10
            
            # Health classification
            if health_score >= 80:
                health_status = 'excellent'
            elif health_score >= 60:
                health_status = 'good'
            elif health_score >= 40:
                health_status = 'fair'
            else:
                health_status = 'poor'
            
            analysis = {
                'portfolio_pnl': total_pnl,
                'weighted_sharpe_ratio': weighted_sharpe,
                'weighted_win_rate': weighted_win_rate,
                'strategy_count': strategy_count,
                'effective_strategies': effective_strategies,
                'herfindahl_index': herfindahl_index,
                'top_3_contribution_pct': top_3_percentage,
                'health_score': health_score,
                'health_status': health_status,
                'health_factors': health_factors,
                'top_contributors': sorted_contributors[:5],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Store analysis
            self.analysis_history.append(analysis)
            self.last_analysis_time = datetime.now()
            
            # Maintain history size
            if len(self.analysis_history) > 100:
                self.analysis_history.pop(0)
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing portfolio performance: {str(e)}")
            return {}
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive analysis summary.
        
        Returns:
            Dictionary with analysis summary
        """
        try:
            return {
                'enabled': self.enabled,
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'analysis_history_length': len(self.analysis_history),
                'recommendations_history_length': len(self.recommendations_history),
                'thresholds': {
                    'underperformance_threshold': self.underperformance_threshold,
                    'volatility_threshold': self.volatility_threshold,
                    'drawdown_threshold': self.drawdown_threshold,
                    'sharpe_threshold': self.sharpe_threshold
                },
                'latest_analysis': self.analysis_history[-1] if self.analysis_history else None
            }
        
        except Exception as e:
            logger.error(f"Error getting analysis summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
