"""
Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR) Calculator for Synergy7 Trading System.

This module implements advanced risk metrics including VaR and CVaR calculations
using multiple methodologies for comprehensive portfolio risk assessment.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Configure logging
logger = logging.getLogger(__name__)

class VaRCalculator:
    """
    Advanced VaR and CVaR calculator with multiple methodologies.
    
    This class provides comprehensive risk metrics calculation including:
    - Historical Simulation VaR
    - Parametric VaR (Normal and t-distribution)
    - Monte Carlo VaR
    - Conditional VaR (Expected Shortfall)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the VaR calculator.
        
        Args:
            config: Configuration dictionary with risk_management section
        """
        # Get risk management configuration
        risk_config = config.get("risk_management", {})
        
        # Basic configuration
        self.enabled = risk_config.get("var_enabled", True)
        self.confidence_levels = risk_config.get("var_confidence_levels", [0.95, 0.99])
        self.lookback_days = risk_config.get("var_lookback_days", 252)
        self.cvar_enabled = risk_config.get("cvar_enabled", True)
        
        # Calculation parameters
        self.min_observations = max(30, self.lookback_days // 10)
        self.monte_carlo_simulations = 10000
        self.bootstrap_samples = 1000
        
        # Risk limits
        self.portfolio_var_limit_pct = risk_config.get("portfolio_var_limit_pct", 0.02)
        self.correlation_threshold = risk_config.get("correlation_threshold", 0.7)
        self.max_correlated_exposure_pct = risk_config.get("max_correlated_exposure_pct", 0.3)
        
        # Historical data storage
        self.returns_history = {}
        self.var_history = []
        self.cvar_history = []
        
        logger.info("Initialized VaR calculator")
    
    def calculate_returns(self, price_data: pd.DataFrame, method: str = "simple") -> pd.Series:
        """
        Calculate returns from price data.
        
        Args:
            price_data: DataFrame with price data (must have 'close' column)
            method: Return calculation method ('simple' or 'log')
            
        Returns:
            Series of returns
        """
        try:
            if 'close' not in price_data.columns:
                raise ValueError("Price data must contain 'close' column")
            
            prices = price_data['close'].dropna()
            
            if method == "log":
                returns = np.log(prices / prices.shift(1)).dropna()
            else:  # simple returns
                returns = (prices / prices.shift(1) - 1).dropna()
            
            return returns
        
        except Exception as e:
            logger.error(f"Error calculating returns: {str(e)}")
            return pd.Series()
    
    def historical_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        Calculate VaR using historical simulation method.
        
        Args:
            returns: Series of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            
        Returns:
            VaR value (positive number representing loss)
        """
        try:
            if len(returns) < self.min_observations:
                logger.warning(f"Insufficient data for VaR calculation: {len(returns)} < {self.min_observations}")
                return 0.0
            
            # Use only recent data
            recent_returns = returns.tail(self.lookback_days)
            
            # Calculate percentile (VaR is the negative of the percentile)
            percentile = (1 - confidence_level) * 100
            var_value = -np.percentile(recent_returns, percentile)
            
            return max(0.0, var_value)
        
        except Exception as e:
            logger.error(f"Error calculating historical VaR: {str(e)}")
            return 0.0
    
    def parametric_var(self, returns: pd.Series, confidence_level: float = 0.95, 
                      distribution: str = "normal") -> float:
        """
        Calculate VaR using parametric method.
        
        Args:
            returns: Series of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            distribution: Distribution assumption ('normal' or 't')
            
        Returns:
            VaR value (positive number representing loss)
        """
        try:
            if len(returns) < self.min_observations:
                logger.warning(f"Insufficient data for parametric VaR: {len(returns)} < {self.min_observations}")
                return 0.0
            
            # Use only recent data
            recent_returns = returns.tail(self.lookback_days)
            
            # Calculate mean and standard deviation
            mean_return = recent_returns.mean()
            std_return = recent_returns.std()
            
            if std_return == 0:
                return 0.0
            
            # Calculate VaR based on distribution
            if distribution == "t":
                # Fit t-distribution
                try:
                    df, loc, scale = stats.t.fit(recent_returns)
                    var_multiplier = stats.t.ppf(1 - confidence_level, df, loc=0, scale=1)
                except:
                    # Fallback to normal distribution
                    var_multiplier = stats.norm.ppf(1 - confidence_level)
            else:  # normal distribution
                var_multiplier = stats.norm.ppf(1 - confidence_level)
            
            # Calculate VaR
            var_value = -(mean_return + var_multiplier * std_return)
            
            return max(0.0, var_value)
        
        except Exception as e:
            logger.error(f"Error calculating parametric VaR: {str(e)}")
            return 0.0
    
    def monte_carlo_var(self, returns: pd.Series, confidence_level: float = 0.95,
                       simulations: int = None) -> float:
        """
        Calculate VaR using Monte Carlo simulation.
        
        Args:
            returns: Series of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% VaR)
            simulations: Number of Monte Carlo simulations
            
        Returns:
            VaR value (positive number representing loss)
        """
        try:
            if len(returns) < self.min_observations:
                logger.warning(f"Insufficient data for Monte Carlo VaR: {len(returns)} < {self.min_observations}")
                return 0.0
            
            if simulations is None:
                simulations = self.monte_carlo_simulations
            
            # Use only recent data
            recent_returns = returns.tail(self.lookback_days)
            
            # Calculate parameters
            mean_return = recent_returns.mean()
            std_return = recent_returns.std()
            
            if std_return == 0:
                return 0.0
            
            # Generate random returns
            np.random.seed(42)  # For reproducibility
            simulated_returns = np.random.normal(mean_return, std_return, simulations)
            
            # Calculate VaR
            percentile = (1 - confidence_level) * 100
            var_value = -np.percentile(simulated_returns, percentile)
            
            return max(0.0, var_value)
        
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo VaR: {str(e)}")
            return 0.0
    
    def conditional_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        Args:
            returns: Series of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% CVaR)
            
        Returns:
            CVaR value (positive number representing expected loss beyond VaR)
        """
        try:
            if len(returns) < self.min_observations:
                logger.warning(f"Insufficient data for CVaR calculation: {len(returns)} < {self.min_observations}")
                return 0.0
            
            # Use only recent data
            recent_returns = returns.tail(self.lookback_days)
            
            # Calculate VaR first
            var_value = self.historical_var(recent_returns, confidence_level)
            
            # Calculate CVaR as the mean of returns worse than VaR
            tail_returns = recent_returns[recent_returns <= -var_value]
            
            if len(tail_returns) == 0:
                return var_value
            
            cvar_value = -tail_returns.mean()
            
            return max(var_value, cvar_value)
        
        except Exception as e:
            logger.error(f"Error calculating CVaR: {str(e)}")
            return 0.0
    
    def calculate_portfolio_var(self, portfolio_returns: Dict[str, pd.Series], 
                               weights: Dict[str, float], confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate portfolio VaR considering correlations.
        
        Args:
            portfolio_returns: Dictionary of asset returns
            weights: Dictionary of asset weights
            confidence_level: Confidence level
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        try:
            if not portfolio_returns or not weights:
                return {}
            
            # Align returns data
            common_assets = set(portfolio_returns.keys()) & set(weights.keys())
            if not common_assets:
                return {}
            
            # Create returns matrix
            returns_df = pd.DataFrame({asset: portfolio_returns[asset] for asset in common_assets})
            returns_df = returns_df.dropna()
            
            if len(returns_df) < self.min_observations:
                logger.warning(f"Insufficient data for portfolio VaR: {len(returns_df)} < {self.min_observations}")
                return {}
            
            # Calculate portfolio returns
            weight_vector = np.array([weights[asset] for asset in common_assets])
            portfolio_returns_series = returns_df.dot(weight_vector)
            
            # Calculate individual and portfolio VaR
            individual_vars = {}
            for asset in common_assets:
                individual_vars[asset] = self.historical_var(returns_df[asset], confidence_level)
            
            portfolio_var = self.historical_var(portfolio_returns_series, confidence_level)
            portfolio_cvar = self.conditional_var(portfolio_returns_series, confidence_level)
            
            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()
            
            # Calculate diversification benefit
            weighted_individual_var = sum(weights[asset] * individual_vars[asset] for asset in common_assets)
            diversification_benefit = max(0, weighted_individual_var - portfolio_var)
            
            # Calculate risk concentration
            risk_contributions = {}
            for asset in common_assets:
                # Marginal VaR contribution
                asset_weight = weights[asset]
                asset_var = individual_vars[asset]
                
                # Simplified risk contribution calculation
                risk_contributions[asset] = asset_weight * asset_var
            
            return {
                'portfolio_var': portfolio_var,
                'portfolio_cvar': portfolio_cvar,
                'individual_vars': individual_vars,
                'diversification_benefit': diversification_benefit,
                'risk_contributions': risk_contributions,
                'correlation_matrix': correlation_matrix.to_dict(),
                'confidence_level': confidence_level,
                'calculation_date': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {str(e)}")
            return {}
    
    def calculate_comprehensive_var(self, returns: pd.Series, confidence_levels: List[float] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive VaR metrics using multiple methods.
        
        Args:
            returns: Series of historical returns
            confidence_levels: List of confidence levels to calculate
            
        Returns:
            Dictionary with comprehensive VaR metrics
        """
        try:
            if confidence_levels is None:
                confidence_levels = self.confidence_levels
            
            if len(returns) < self.min_observations:
                logger.warning(f"Insufficient data for comprehensive VaR: {len(returns)} < {self.min_observations}")
                return {}
            
            results = {
                'calculation_date': datetime.now().isoformat(),
                'data_points': len(returns),
                'lookback_days': min(self.lookback_days, len(returns)),
                'confidence_levels': confidence_levels,
                'methods': {}
            }
            
            for confidence_level in confidence_levels:
                method_results = {
                    'historical_var': self.historical_var(returns, confidence_level),
                    'parametric_var_normal': self.parametric_var(returns, confidence_level, 'normal'),
                    'parametric_var_t': self.parametric_var(returns, confidence_level, 't'),
                    'monte_carlo_var': self.monte_carlo_var(returns, confidence_level),
                    'conditional_var': self.conditional_var(returns, confidence_level)
                }
                
                # Calculate average VaR across methods
                var_values = [v for v in method_results.values() if v > 0]
                method_results['average_var'] = np.mean(var_values) if var_values else 0.0
                method_results['var_range'] = max(var_values) - min(var_values) if len(var_values) > 1 else 0.0
                
                results['methods'][f'confidence_{int(confidence_level*100)}'] = method_results
            
            # Store in history
            self.var_history.append(results)
            if len(self.var_history) > 100:  # Keep last 100 calculations
                self.var_history.pop(0)
            
            return results
        
        except Exception as e:
            logger.error(f"Error calculating comprehensive VaR: {str(e)}")
            return {}
    
    def check_var_limits(self, portfolio_var: float, confidence_level: float = 0.95) -> Dict[str, Any]:
        """
        Check if portfolio VaR exceeds configured limits.
        
        Args:
            portfolio_var: Calculated portfolio VaR
            confidence_level: Confidence level used
            
        Returns:
            Dictionary with limit check results
        """
        try:
            limit_exceeded = portfolio_var > self.portfolio_var_limit_pct
            
            return {
                'portfolio_var': portfolio_var,
                'var_limit': self.portfolio_var_limit_pct,
                'limit_exceeded': limit_exceeded,
                'excess_var': max(0, portfolio_var - self.portfolio_var_limit_pct),
                'utilization_pct': (portfolio_var / self.portfolio_var_limit_pct) * 100,
                'confidence_level': confidence_level,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error checking VaR limits: {str(e)}")
            return {'error': str(e)}
    
    def get_var_summary(self) -> Dict[str, Any]:
        """
        Get summary of VaR calculation activity.
        
        Returns:
            Dictionary with VaR summary
        """
        try:
            return {
                'enabled': self.enabled,
                'confidence_levels': self.confidence_levels,
                'lookback_days': self.lookback_days,
                'cvar_enabled': self.cvar_enabled,
                'portfolio_var_limit_pct': self.portfolio_var_limit_pct,
                'calculations_performed': len(self.var_history),
                'last_calculation': self.var_history[-1]['calculation_date'] if self.var_history else None,
                'min_observations': self.min_observations
            }
        
        except Exception as e:
            logger.error(f"Error getting VaR summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
