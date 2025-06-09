"""
Portfolio Risk Manager for Synergy7 Trading System.

This module implements comprehensive portfolio-level risk management including
correlation analysis, position limits, and VaR-based risk controls.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .var_calculator import VaRCalculator

# Configure logging
logger = logging.getLogger(__name__)

class PortfolioRiskManager:
    """
    Comprehensive portfolio risk manager with VaR integration.
    
    This class provides portfolio-level risk monitoring, correlation analysis,
    position limit enforcement, and VaR-based risk controls.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the portfolio risk manager.
        
        Args:
            config: Configuration dictionary with risk_management section
        """
        # Get risk management configuration
        risk_config = config.get("risk_management", {})
        
        # Basic configuration
        self.enabled = risk_config.get("var_enabled", True)
        self.correlation_threshold = risk_config.get("correlation_threshold", 0.7)
        self.max_correlated_exposure_pct = risk_config.get("max_correlated_exposure_pct", 0.3)
        self.portfolio_var_limit_pct = risk_config.get("portfolio_var_limit_pct", 0.02)
        
        # Position limits
        self.max_position_size_pct = risk_config.get("max_position_size_pct", 0.1)
        self.max_sector_exposure_pct = risk_config.get("max_sector_exposure_pct", 0.4)
        self.max_single_asset_pct = risk_config.get("max_single_asset_pct", 0.15)
        
        # Risk monitoring parameters
        self.risk_update_interval = risk_config.get("risk_update_interval", 300)  # seconds
        self.correlation_lookback_days = risk_config.get("correlation_lookback_days", 60)
        self.min_correlation_observations = 30
        
        # Initialize VaR calculator
        self.var_calculator = VaRCalculator(config)
        
        # Portfolio state
        self.current_positions = {}
        self.position_history = []
        self.correlation_matrix = pd.DataFrame()
        self.risk_metrics = {}
        self.risk_alerts = []
        
        # Risk limits tracking
        self.limit_violations = defaultdict(list)
        self.last_risk_update = None
        
        logger.info("Initialized portfolio risk manager")
    
    def update_positions(self, positions: Dict[str, Dict[str, Any]]) -> None:
        """
        Update current portfolio positions.
        
        Args:
            positions: Dictionary of current positions
                      {asset: {'size': float, 'value': float, 'entry_price': float, ...}}
        """
        try:
            self.current_positions = positions.copy()
            
            # Add to position history
            position_snapshot = {
                'timestamp': datetime.now().isoformat(),
                'positions': positions.copy(),
                'total_value': sum(pos.get('value', 0) for pos in positions.values()),
                'position_count': len(positions)
            }
            
            self.position_history.append(position_snapshot)
            
            # Maintain history size
            if len(self.position_history) > 1000:
                self.position_history.pop(0)
            
            logger.debug(f"Updated positions: {len(positions)} assets, total value: ${position_snapshot['total_value']:,.2f}")
        
        except Exception as e:
            logger.error(f"Error updating positions: {str(e)}")
    
    def calculate_correlation_matrix(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate correlation matrix for portfolio assets.
        
        Args:
            price_data: Dictionary of price data for each asset
            
        Returns:
            Correlation matrix DataFrame
        """
        try:
            if not price_data:
                return pd.DataFrame()
            
            # Calculate returns for each asset
            returns_data = {}
            for asset, data in price_data.items():
                if 'close' in data.columns and len(data) > self.min_correlation_observations:
                    returns = data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        returns_data[asset] = returns.tail(self.correlation_lookback_days * 24)  # Assuming hourly data
            
            if len(returns_data) < 2:
                logger.warning("Insufficient data for correlation calculation")
                return pd.DataFrame()
            
            # Create returns DataFrame
            returns_df = pd.DataFrame(returns_data)
            returns_df = returns_df.dropna()
            
            if len(returns_df) < self.min_correlation_observations:
                logger.warning(f"Insufficient observations for correlation: {len(returns_df)} < {self.min_correlation_observations}")
                return pd.DataFrame()
            
            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()
            
            # Store correlation matrix
            self.correlation_matrix = correlation_matrix
            
            logger.debug(f"Calculated correlation matrix for {len(correlation_matrix)} assets")
            return correlation_matrix
        
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {str(e)}")
            return pd.DataFrame()
    
    def identify_correlated_positions(self, correlation_matrix: pd.DataFrame = None) -> Dict[str, List[str]]:
        """
        Identify highly correlated position groups.
        
        Args:
            correlation_matrix: Correlation matrix (uses stored matrix if None)
            
        Returns:
            Dictionary of correlated asset groups
        """
        try:
            if correlation_matrix is None:
                correlation_matrix = self.correlation_matrix
            
            if correlation_matrix.empty:
                return {}
            
            correlated_groups = {}
            processed_assets = set()
            
            for asset1 in correlation_matrix.index:
                if asset1 in processed_assets:
                    continue
                
                # Find assets highly correlated with asset1
                correlations = correlation_matrix.loc[asset1]
                highly_correlated = correlations[
                    (correlations.abs() >= self.correlation_threshold) & 
                    (correlations.index != asset1)
                ].index.tolist()
                
                if highly_correlated:
                    group_name = f"corr_group_{asset1}"
                    correlated_groups[group_name] = [asset1] + highly_correlated
                    processed_assets.update([asset1] + highly_correlated)
            
            logger.debug(f"Identified {len(correlated_groups)} correlated groups")
            return correlated_groups
        
        except Exception as e:
            logger.error(f"Error identifying correlated positions: {str(e)}")
            return {}
    
    def calculate_portfolio_risk_metrics(self, price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio risk metrics.
        
        Args:
            price_data: Dictionary of price data for each asset
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        try:
            if not self.current_positions:
                return {}
            
            # Calculate total portfolio value
            total_portfolio_value = sum(pos.get('value', 0) for pos in self.current_positions.values())
            
            if total_portfolio_value <= 0:
                return {}
            
            # Calculate position weights
            position_weights = {}
            for asset, position in self.current_positions.items():
                position_weights[asset] = position.get('value', 0) / total_portfolio_value
            
            # Calculate returns for VaR calculation
            portfolio_returns = {}
            for asset, data in price_data.items():
                if asset in self.current_positions and 'close' in data.columns:
                    returns = data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        portfolio_returns[asset] = returns
            
            # Calculate portfolio VaR
            portfolio_var_metrics = {}
            if portfolio_returns and len(portfolio_returns) >= 2:
                portfolio_var_metrics = self.var_calculator.calculate_portfolio_var(
                    portfolio_returns, position_weights
                )
            
            # Calculate correlation matrix
            correlation_matrix = self.calculate_correlation_matrix(price_data)
            
            # Identify correlated positions
            correlated_groups = self.identify_correlated_positions(correlation_matrix)
            
            # Calculate concentration metrics
            concentration_metrics = self._calculate_concentration_metrics(position_weights)
            
            # Calculate risk-adjusted metrics
            risk_adjusted_metrics = self._calculate_risk_adjusted_metrics(
                portfolio_returns, position_weights
            )
            
            # Combine all metrics
            risk_metrics = {
                'portfolio_value': total_portfolio_value,
                'position_count': len(self.current_positions),
                'position_weights': position_weights,
                'var_metrics': portfolio_var_metrics,
                'correlation_metrics': {
                    'correlation_matrix_size': len(correlation_matrix) if not correlation_matrix.empty else 0,
                    'correlated_groups': correlated_groups,
                    'max_correlation': correlation_matrix.abs().max().max() if not correlation_matrix.empty else 0.0
                },
                'concentration_metrics': concentration_metrics,
                'risk_adjusted_metrics': risk_adjusted_metrics,
                'calculation_timestamp': datetime.now().isoformat()
            }
            
            # Store risk metrics
            self.risk_metrics = risk_metrics
            self.last_risk_update = datetime.now()
            
            return risk_metrics
        
        except Exception as e:
            logger.error(f"Error calculating portfolio risk metrics: {str(e)}")
            return {}
    
    def _calculate_concentration_metrics(self, position_weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate portfolio concentration metrics.
        
        Args:
            position_weights: Dictionary of position weights
            
        Returns:
            Dictionary with concentration metrics
        """
        try:
            if not position_weights:
                return {}
            
            weights = list(position_weights.values())
            
            # Herfindahl-Hirschman Index (HHI)
            hhi = sum(w**2 for w in weights)
            
            # Effective number of positions
            effective_positions = 1 / hhi if hhi > 0 else 0
            
            # Largest position weight
            max_weight = max(weights)
            
            # Top 3 positions concentration
            top_3_weights = sorted(weights, reverse=True)[:3]
            top_3_concentration = sum(top_3_weights)
            
            return {
                'herfindahl_index': hhi,
                'effective_positions': effective_positions,
                'max_position_weight': max_weight,
                'top_3_concentration': top_3_concentration,
                'position_count': len(weights)
            }
        
        except Exception as e:
            logger.error(f"Error calculating concentration metrics: {str(e)}")
            return {}
    
    def _calculate_risk_adjusted_metrics(self, portfolio_returns: Dict[str, pd.Series], 
                                       position_weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate risk-adjusted portfolio metrics.
        
        Args:
            portfolio_returns: Dictionary of asset returns
            position_weights: Dictionary of position weights
            
        Returns:
            Dictionary with risk-adjusted metrics
        """
        try:
            if not portfolio_returns or not position_weights:
                return {}
            
            # Align data
            common_assets = set(portfolio_returns.keys()) & set(position_weights.keys())
            if not common_assets:
                return {}
            
            # Create portfolio returns
            returns_df = pd.DataFrame({asset: portfolio_returns[asset] for asset in common_assets})
            returns_df = returns_df.dropna()
            
            if len(returns_df) < 30:  # Need minimum data for meaningful metrics
                return {}
            
            # Calculate weighted portfolio returns
            weight_vector = np.array([position_weights[asset] for asset in common_assets])
            portfolio_returns_series = returns_df.dot(weight_vector)
            
            # Calculate metrics
            mean_return = portfolio_returns_series.mean()
            std_return = portfolio_returns_series.std()
            
            # Sharpe ratio (assuming risk-free rate of 0)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns_series).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdowns.min()
            
            # Volatility (annualized)
            annualized_volatility = std_return * np.sqrt(252)  # Assuming daily returns
            
            return {
                'mean_return': mean_return,
                'volatility': std_return,
                'annualized_volatility': annualized_volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': abs(max_drawdown),
                'return_periods': len(portfolio_returns_series)
            }
        
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted metrics: {str(e)}")
            return {}
    
    def check_risk_limits(self) -> List[Dict[str, Any]]:
        """
        Check portfolio against risk limits and generate alerts.
        
        Returns:
            List of risk limit violations
        """
        try:
            violations = []
            current_time = datetime.now()
            
            if not self.current_positions or not self.risk_metrics:
                return violations
            
            # Check individual position size limits
            position_weights = self.risk_metrics.get('position_weights', {})
            for asset, weight in position_weights.items():
                if weight > self.max_single_asset_pct:
                    violation = {
                        'type': 'position_size_limit',
                        'asset': asset,
                        'current_weight': weight,
                        'limit': self.max_single_asset_pct,
                        'excess': weight - self.max_single_asset_pct,
                        'severity': 'high' if weight > self.max_single_asset_pct * 1.5 else 'medium',
                        'timestamp': current_time.isoformat()
                    }
                    violations.append(violation)
            
            # Check VaR limits
            var_metrics = self.risk_metrics.get('var_metrics', {})
            portfolio_var = var_metrics.get('portfolio_var', 0)
            if portfolio_var > self.portfolio_var_limit_pct:
                violation = {
                    'type': 'portfolio_var_limit',
                    'current_var': portfolio_var,
                    'limit': self.portfolio_var_limit_pct,
                    'excess': portfolio_var - self.portfolio_var_limit_pct,
                    'severity': 'critical' if portfolio_var > self.portfolio_var_limit_pct * 1.5 else 'high',
                    'timestamp': current_time.isoformat()
                }
                violations.append(violation)
            
            # Check correlation concentration
            correlation_metrics = self.risk_metrics.get('correlation_metrics', {})
            correlated_groups = correlation_metrics.get('correlated_groups', {})
            
            for group_name, assets in correlated_groups.items():
                group_exposure = sum(position_weights.get(asset, 0) for asset in assets)
                if group_exposure > self.max_correlated_exposure_pct:
                    violation = {
                        'type': 'correlation_concentration',
                        'group': group_name,
                        'assets': assets,
                        'current_exposure': group_exposure,
                        'limit': self.max_correlated_exposure_pct,
                        'excess': group_exposure - self.max_correlated_exposure_pct,
                        'severity': 'medium',
                        'timestamp': current_time.isoformat()
                    }
                    violations.append(violation)
            
            # Store violations
            for violation in violations:
                self.limit_violations[violation['type']].append(violation)
                
                # Keep only recent violations (last 24 hours)
                cutoff_time = current_time - timedelta(hours=24)
                self.limit_violations[violation['type']] = [
                    v for v in self.limit_violations[violation['type']]
                    if datetime.fromisoformat(v['timestamp']) > cutoff_time
                ]
            
            # Update risk alerts
            self.risk_alerts = violations
            
            return violations
        
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return []
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio risk summary.
        
        Returns:
            Dictionary with risk summary
        """
        try:
            current_violations = self.check_risk_limits()
            
            return {
                'enabled': self.enabled,
                'portfolio_value': self.risk_metrics.get('portfolio_value', 0),
                'position_count': len(self.current_positions),
                'last_risk_update': self.last_risk_update.isoformat() if self.last_risk_update else None,
                'current_violations': len(current_violations),
                'violation_types': list(set(v['type'] for v in current_violations)),
                'risk_limits': {
                    'max_single_asset_pct': self.max_single_asset_pct,
                    'portfolio_var_limit_pct': self.portfolio_var_limit_pct,
                    'max_correlated_exposure_pct': self.max_correlated_exposure_pct,
                    'correlation_threshold': self.correlation_threshold
                },
                'var_calculator_summary': self.var_calculator.get_var_summary(),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting risk summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
