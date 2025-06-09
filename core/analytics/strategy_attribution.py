"""
Strategy Performance Attribution for Synergy7 Trading System.

This module tracks individual strategy performance, calculates attribution metrics,
and provides comprehensive performance analysis for strategy optimization.
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

class StrategyAttributionTracker:
    """
    Tracks and analyzes individual strategy performance with comprehensive attribution metrics.
    
    This class provides detailed performance tracking for each strategy, including
    returns attribution, risk metrics, and performance analytics.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy attribution tracker.
        
        Args:
            config: Configuration dictionary with strategy_attribution section
        """
        # Get strategy attribution configuration
        attribution_config = config.get("strategy_attribution", {})
        
        # Basic configuration
        self.enabled = attribution_config.get("enabled", True)
        self.attribution_window_days = attribution_config.get("attribution_window_days", 30)
        self.min_trades_for_attribution = attribution_config.get("min_trades_for_attribution", 10)
        self.performance_decay_factor = attribution_config.get("performance_decay_factor", 0.95)
        self.rebalance_threshold = attribution_config.get("rebalance_threshold", 0.1)
        
        # Performance tracking parameters
        self.max_history_days = attribution_config.get("max_history_days", 90)
        self.update_interval_minutes = attribution_config.get("update_interval_minutes", 60)
        self.benchmark_return = attribution_config.get("benchmark_return", 0.0)  # Daily benchmark return
        
        # Data storage
        self.strategy_trades = defaultdict(list)  # Strategy -> List of trades
        self.strategy_performance = defaultdict(dict)  # Strategy -> Performance metrics
        self.strategy_weights = {}  # Current strategy weights
        self.portfolio_performance = []  # Overall portfolio performance history
        
        # Attribution metrics
        self.attribution_history = deque(maxlen=1000)
        self.performance_rankings = {}
        self.last_attribution_update = None
        
        # Risk-free rate (annualized)
        self.risk_free_rate = attribution_config.get("risk_free_rate", 0.02)
        
        logger.info("Initialized Strategy Attribution Tracker")
    
    def record_trade(self, strategy_name: str, trade_data: Dict[str, Any]) -> None:
        """
        Record a trade for strategy performance tracking.
        
        Args:
            strategy_name: Name of the strategy
            trade_data: Dictionary containing trade information
        """
        try:
            # Validate trade data
            required_fields = ['timestamp', 'symbol', 'side', 'quantity', 'price', 'pnl']
            for field in required_fields:
                if field not in trade_data:
                    logger.warning(f"Trade data missing required field: {field}")
                    return
            
            # Add trade to strategy history
            trade_record = {
                'timestamp': trade_data['timestamp'],
                'symbol': trade_data['symbol'],
                'side': trade_data['side'],
                'quantity': trade_data['quantity'],
                'price': trade_data['price'],
                'pnl': trade_data['pnl'],
                'commission': trade_data.get('commission', 0.0),
                'slippage': trade_data.get('slippage', 0.0),
                'signal_strength': trade_data.get('signal_strength', 1.0),
                'market_regime': trade_data.get('market_regime', 'unknown'),
                'trade_id': trade_data.get('trade_id', f"{strategy_name}_{len(self.strategy_trades[strategy_name])}")
            }
            
            self.strategy_trades[strategy_name].append(trade_record)
            
            # Maintain history size
            max_trades_per_strategy = 1000
            if len(self.strategy_trades[strategy_name]) > max_trades_per_strategy:
                self.strategy_trades[strategy_name].pop(0)
            
            logger.debug(f"Recorded trade for strategy {strategy_name}: {trade_record['pnl']:.4f} PnL")
        
        except Exception as e:
            logger.error(f"Error recording trade for strategy {strategy_name}: {str(e)}")
    
    def calculate_strategy_performance(self, strategy_name: str, 
                                     lookback_days: int = None) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            lookback_days: Number of days to look back (None for all data)
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            if strategy_name not in self.strategy_trades:
                return {}
            
            trades = self.strategy_trades[strategy_name]
            
            if not trades:
                return {}
            
            # Filter trades by lookback period
            if lookback_days:
                cutoff_date = datetime.now() - timedelta(days=lookback_days)
                trades = [t for t in trades if datetime.fromisoformat(t['timestamp']) > cutoff_date]
            
            if len(trades) < self.min_trades_for_attribution:
                logger.debug(f"Insufficient trades for {strategy_name}: {len(trades)} < {self.min_trades_for_attribution}")
                return {}
            
            # Calculate basic metrics
            total_pnl = sum(trade['pnl'] for trade in trades)
            total_commission = sum(trade.get('commission', 0) for trade in trades)
            total_slippage = sum(trade.get('slippage', 0) for trade in trades)
            net_pnl = total_pnl - total_commission - total_slippage
            
            # Trade statistics
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            win_rate = len(winning_trades) / len(trades) if trades else 0.0
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0.0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0.0
            profit_factor = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades else float('inf')
            
            # Calculate returns series
            returns = [trade['pnl'] for trade in trades]
            
            # Risk metrics
            volatility = np.std(returns) if len(returns) > 1 else 0.0
            sharpe_ratio = (np.mean(returns) - self.risk_free_rate/252) / volatility if volatility > 0 else 0.0
            
            # Maximum drawdown
            cumulative_pnl = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdowns = cumulative_pnl - running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
            
            # Calmar ratio
            calmar_ratio = (total_pnl / len(trades) * 252) / abs(max_drawdown) if max_drawdown != 0 else 0.0
            
            # Trade frequency
            if len(trades) > 1:
                first_trade = datetime.fromisoformat(trades[0]['timestamp'])
                last_trade = datetime.fromisoformat(trades[-1]['timestamp'])
                days_active = (last_trade - first_trade).days + 1
                trades_per_day = len(trades) / max(days_active, 1)
            else:
                trades_per_day = 0.0
            
            # Performance by market regime
            regime_performance = defaultdict(list)
            for trade in trades:
                regime = trade.get('market_regime', 'unknown')
                regime_performance[regime].append(trade['pnl'])
            
            regime_stats = {}
            for regime, pnls in regime_performance.items():
                regime_stats[regime] = {
                    'trade_count': len(pnls),
                    'total_pnl': sum(pnls),
                    'avg_pnl': np.mean(pnls),
                    'win_rate': len([p for p in pnls if p > 0]) / len(pnls) if pnls else 0.0
                }
            
            # Recent performance (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_trades = [t for t in trades if datetime.fromisoformat(t['timestamp']) > recent_cutoff]
            recent_pnl = sum(trade['pnl'] for trade in recent_trades)
            
            performance_metrics = {
                'strategy_name': strategy_name,
                'total_trades': len(trades),
                'total_pnl': total_pnl,
                'net_pnl': net_pnl,
                'total_commission': total_commission,
                'total_slippage': total_slippage,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio,
                'trades_per_day': trades_per_day,
                'recent_pnl_7d': recent_pnl,
                'regime_performance': regime_stats,
                'calculation_timestamp': datetime.now().isoformat(),
                'lookback_days': lookback_days or 'all'
            }
            
            # Store performance metrics
            self.strategy_performance[strategy_name] = performance_metrics
            
            return performance_metrics
        
        except Exception as e:
            logger.error(f"Error calculating performance for strategy {strategy_name}: {str(e)}")
            return {}
    
    def calculate_portfolio_attribution(self, strategy_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Calculate portfolio-level performance attribution across strategies.
        
        Args:
            strategy_weights: Dictionary of strategy weights (None to use equal weights)
            
        Returns:
            Dictionary with portfolio attribution metrics
        """
        try:
            if not self.strategy_trades:
                return {}
            
            # Use provided weights or equal weights
            if strategy_weights:
                self.strategy_weights = strategy_weights.copy()
            else:
                strategies = list(self.strategy_trades.keys())
                self.strategy_weights = {s: 1.0/len(strategies) for s in strategies}
            
            # Calculate individual strategy performance
            strategy_performances = {}
            for strategy_name in self.strategy_weights.keys():
                perf = self.calculate_strategy_performance(strategy_name, self.attribution_window_days)
                if perf:
                    strategy_performances[strategy_name] = perf
            
            if not strategy_performances:
                return {}
            
            # Calculate weighted portfolio metrics
            total_weighted_pnl = 0.0
            total_weighted_trades = 0
            weighted_win_rate = 0.0
            weighted_sharpe = 0.0
            weighted_max_dd = 0.0
            
            strategy_contributions = {}
            
            for strategy_name, weight in self.strategy_weights.items():
                if strategy_name in strategy_performances:
                    perf = strategy_performances[strategy_name]
                    
                    # Calculate contributions
                    pnl_contribution = perf['net_pnl'] * weight
                    total_weighted_pnl += pnl_contribution
                    total_weighted_trades += perf['total_trades'] * weight
                    weighted_win_rate += perf['win_rate'] * weight
                    weighted_sharpe += perf['sharpe_ratio'] * weight
                    weighted_max_dd += perf['max_drawdown'] * weight
                    
                    strategy_contributions[strategy_name] = {
                        'weight': weight,
                        'pnl_contribution': pnl_contribution,
                        'pnl_percentage': (pnl_contribution / total_weighted_pnl * 100) if total_weighted_pnl != 0 else 0.0,
                        'individual_performance': perf
                    }
            
            # Calculate portfolio-level metrics
            portfolio_metrics = {
                'total_portfolio_pnl': total_weighted_pnl,
                'weighted_win_rate': weighted_win_rate,
                'weighted_sharpe_ratio': weighted_sharpe,
                'weighted_max_drawdown': weighted_max_dd,
                'total_weighted_trades': total_weighted_trades,
                'strategy_count': len(strategy_contributions),
                'attribution_window_days': self.attribution_window_days,
                'calculation_timestamp': datetime.now().isoformat()
            }
            
            # Combine results
            attribution_result = {
                'portfolio_metrics': portfolio_metrics,
                'strategy_contributions': strategy_contributions,
                'strategy_weights': self.strategy_weights.copy()
            }
            
            # Store in history
            self.attribution_history.append(attribution_result)
            self.last_attribution_update = datetime.now()
            
            return attribution_result
        
        except Exception as e:
            logger.error(f"Error calculating portfolio attribution: {str(e)}")
            return {}
    
    def rank_strategies(self, metric: str = 'sharpe_ratio') -> List[Tuple[str, float]]:
        """
        Rank strategies by a specific performance metric.
        
        Args:
            metric: Performance metric to rank by
            
        Returns:
            List of (strategy_name, metric_value) tuples sorted by performance
        """
        try:
            strategy_scores = []
            
            for strategy_name in self.strategy_trades.keys():
                perf = self.calculate_strategy_performance(strategy_name, self.attribution_window_days)
                if perf and metric in perf:
                    strategy_scores.append((strategy_name, perf[metric]))
            
            # Sort by metric value (descending)
            strategy_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Store rankings
            self.performance_rankings[metric] = strategy_scores
            
            return strategy_scores
        
        except Exception as e:
            logger.error(f"Error ranking strategies by {metric}: {str(e)}")
            return []
    
    def get_strategy_summary(self, strategy_name: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary with strategy summary
        """
        try:
            if strategy_name not in self.strategy_trades:
                return {'error': f'Strategy {strategy_name} not found'}
            
            # Get performance metrics
            performance = self.calculate_strategy_performance(strategy_name)
            
            # Get recent trades
            recent_trades = self.strategy_trades[strategy_name][-10:]  # Last 10 trades
            
            # Calculate trend (last 7 days vs previous 7 days)
            now = datetime.now()
            last_7d_cutoff = now - timedelta(days=7)
            prev_7d_cutoff = now - timedelta(days=14)
            
            last_7d_trades = [t for t in self.strategy_trades[strategy_name] 
                            if datetime.fromisoformat(t['timestamp']) > last_7d_cutoff]
            prev_7d_trades = [t for t in self.strategy_trades[strategy_name] 
                            if prev_7d_cutoff < datetime.fromisoformat(t['timestamp']) <= last_7d_cutoff]
            
            last_7d_pnl = sum(t['pnl'] for t in last_7d_trades)
            prev_7d_pnl = sum(t['pnl'] for t in prev_7d_trades)
            
            trend = 'improving' if last_7d_pnl > prev_7d_pnl else 'declining'
            
            return {
                'strategy_name': strategy_name,
                'performance_metrics': performance,
                'recent_trades': recent_trades,
                'trend_7d': trend,
                'last_7d_pnl': last_7d_pnl,
                'prev_7d_pnl': prev_7d_pnl,
                'current_weight': self.strategy_weights.get(strategy_name, 0.0),
                'total_trades': len(self.strategy_trades[strategy_name]),
                'last_update': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting strategy summary for {strategy_name}: {str(e)}")
            return {'error': str(e)}
    
    def get_attribution_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive attribution summary.
        
        Returns:
            Dictionary with attribution summary
        """
        try:
            # Calculate current attribution
            current_attribution = self.calculate_portfolio_attribution()
            
            # Get strategy rankings
            sharpe_rankings = self.rank_strategies('sharpe_ratio')
            pnl_rankings = self.rank_strategies('net_pnl')
            
            return {
                'enabled': self.enabled,
                'total_strategies': len(self.strategy_trades),
                'attribution_window_days': self.attribution_window_days,
                'last_attribution_update': self.last_attribution_update.isoformat() if self.last_attribution_update else None,
                'current_attribution': current_attribution,
                'strategy_rankings': {
                    'by_sharpe_ratio': sharpe_rankings[:5],  # Top 5
                    'by_net_pnl': pnl_rankings[:5]  # Top 5
                },
                'attribution_history_length': len(self.attribution_history),
                'total_trades_tracked': sum(len(trades) for trades in self.strategy_trades.values())
            }
        
        except Exception as e:
            logger.error(f"Error getting attribution summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
