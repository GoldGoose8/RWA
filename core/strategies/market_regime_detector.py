"""
Enhanced Market Regime Detection for Synergy7 Trading System.

This module implements enhanced market regime detection with dynamic thresholds,
probabilistic regime detection, and configuration-driven parameters.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime types."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CHOPPY = "choppy"
    UNKNOWN = "unknown"


class MarketRegimeDetector:
    """
    Enhanced Market Regime Detector with dynamic thresholds and probabilistic detection.

    This class detects the current market regime based on various indicators
    with adaptive thresholds and provides probabilistic regime confidence.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the enhanced market regime detector.

        Args:
            config: Configuration dictionary with market_regime section
        """
        # Get market regime configuration
        regime_config = config.get("market_regime", {})

        # Basic configuration
        self.enabled = regime_config.get("enabled", True)
        self.adaptive_thresholds = regime_config.get("adaptive_thresholds", True)

        # Trend detection parameters
        self.adx_period = regime_config.get("adx_period", 14)
        self.adx_threshold_base = regime_config.get("adx_threshold_base", 25)
        self.adx_threshold_multiplier = regime_config.get("adx_threshold_multiplier", 1.2)

        # Volatility detection parameters
        self.bb_period = regime_config.get("bb_period", 20)
        self.bb_std_dev = regime_config.get("bb_std_dev", 2)
        self.atr_period = regime_config.get("atr_period", 14)
        self.volatility_lookback_periods = regime_config.get("volatility_lookback_periods", [20, 50, 100])
        self.volatility_threshold = regime_config.get("volatility_threshold", 0.03)

        # Range detection parameters
        self.range_period = regime_config.get("range_period", 20)
        self.range_threshold = regime_config.get("range_threshold", 0.05)

        # Choppiness detection parameters
        self.choppiness_period = regime_config.get("choppiness_period", 14)
        self.choppiness_threshold_base = regime_config.get("choppiness_threshold_base", 61.8)
        self.choppiness_threshold_multiplier = regime_config.get("choppiness_threshold_multiplier", 1.1)

        # Regime confidence and change detection
        self.regime_confidence_threshold = regime_config.get("regime_confidence_threshold", 0.7)
        self.regime_change_cooldown = regime_config.get("regime_change_cooldown", 300)  # seconds
        self.regime_change_lookback = regime_config.get("regime_change_lookback", 5)

        # ML models configuration
        ml_config = regime_config.get("ml_models", {})
        self.hmm_enabled = ml_config.get("hmm_enabled", True)
        self.hmm_states = ml_config.get("hmm_states", 4)
        self.hmm_lookback_days = ml_config.get("hmm_lookback_days", 30)

        # Historical data
        self.historical_regimes = []
        self.historical_metrics = []
        self.last_regime_change = None

        # Dynamic thresholds
        self.current_adx_threshold = self.adx_threshold_base
        self.current_choppiness_threshold = self.choppiness_threshold_base

        logger.info("Initialized market regime detector")

    def _calculate_dynamic_thresholds(self, df: pd.DataFrame) -> None:
        """
        Calculate dynamic thresholds based on historical data.

        Args:
            df: DataFrame with OHLCV data
        """
        if not self.adaptive_thresholds or len(df) < max(self.volatility_lookback_periods):
            return

        try:
            # Calculate historical volatility for different periods
            returns = df['close'].pct_change().dropna()
            volatilities = []

            for period in self.volatility_lookback_periods:
                if len(returns) >= period:
                    vol = returns.rolling(window=period).std().iloc[-1] * np.sqrt(252)
                    volatilities.append(vol)

            if volatilities:
                avg_volatility = np.mean(volatilities)

                # Adjust ADX threshold based on volatility
                # Higher volatility -> lower ADX threshold (easier to detect trends)
                volatility_factor = max(0.5, min(2.0, 1.0 / (1.0 + avg_volatility)))
                self.current_adx_threshold = self.adx_threshold_base * self.adx_threshold_multiplier * volatility_factor

                # Adjust choppiness threshold based on volatility
                # Higher volatility -> higher choppiness threshold (harder to detect choppiness)
                choppiness_factor = max(0.8, min(1.5, 1.0 + avg_volatility))
                self.current_choppiness_threshold = self.choppiness_threshold_base * self.choppiness_threshold_multiplier * choppiness_factor

                logger.debug(f"Dynamic thresholds - ADX: {self.current_adx_threshold:.2f}, Choppiness: {self.current_choppiness_threshold:.2f}")

        except Exception as e:
            logger.warning(f"Error calculating dynamic thresholds: {str(e)}")

    def calculate_adx(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Average Directional Index (ADX) for trend detection.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with ADX values
        """
        # Make a copy of the data
        data = df.copy()

        # Calculate True Range (TR)
        data['tr0'] = abs(data['high'] - data['low'])
        data['tr1'] = abs(data['high'] - data['close'].shift())
        data['tr2'] = abs(data['low'] - data['close'].shift())
        data['tr'] = data[['tr0', 'tr1', 'tr2']].max(axis=1)

        # Calculate Directional Movement (DM)
        data['up_move'] = data['high'] - data['high'].shift()
        data['down_move'] = data['low'].shift() - data['low']

        # Calculate Positive and Negative DM
        data['plus_dm'] = 0
        data.loc[(data['up_move'] > data['down_move']) & (data['up_move'] > 0), 'plus_dm'] = data['up_move']

        data['minus_dm'] = 0
        data.loc[(data['down_move'] > data['up_move']) & (data['down_move'] > 0), 'minus_dm'] = data['down_move']

        # Calculate Smoothed TR and DM
        period = self.adx_period

        # Calculate smoothed TR
        data['atr'] = data['tr'].rolling(window=period).mean()

        # Calculate smoothed +DI and -DI
        data['plus_di'] = 100 * (data['plus_dm'].rolling(window=period).mean() / data['atr'])
        data['minus_di'] = 100 * (data['minus_dm'].rolling(window=period).mean() / data['atr'])

        # Calculate Directional Index (DX)
        data['dx'] = 100 * (abs(data['plus_di'] - data['minus_di']) / (data['plus_di'] + data['minus_di']))

        # Calculate ADX
        data['adx'] = data['dx'].rolling(window=period).mean()

        return data

    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands for volatility detection.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with Bollinger Bands
        """
        # Make a copy of the data
        data = df.copy()

        # Calculate Bollinger Bands
        data['ma'] = data['close'].rolling(window=self.bb_period).mean()
        data['std'] = data['close'].rolling(window=self.bb_period).std()
        data['upper_band'] = data['ma'] + (data['std'] * self.bb_std_dev)
        data['lower_band'] = data['ma'] - (data['std'] * self.bb_std_dev)
        data['bb_width'] = (data['upper_band'] - data['lower_band']) / data['ma']

        return data

    def calculate_choppiness_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Choppiness Index for detecting choppy markets.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with Choppiness Index
        """
        # Make a copy of the data
        data = df.copy()

        # Calculate ATR sum
        data['atr_sum'] = data['tr'].rolling(window=self.choppiness_period).sum()

        # Calculate range
        data['range'] = data['high'].rolling(window=self.choppiness_period).max() - data['low'].rolling(window=self.choppiness_period).min()

        # Calculate Choppiness Index
        data['choppiness'] = 100 * np.log10(data['atr_sum'] / data['range']) / np.log10(self.choppiness_period)

        return data

    def calculate_regime_probabilities(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate probabilistic regime scores.

        Args:
            metrics: Dictionary of calculated metrics

        Returns:
            Dictionary with regime probabilities
        """
        probabilities = {
            MarketRegime.TRENDING_UP.value: 0.0,
            MarketRegime.TRENDING_DOWN.value: 0.0,
            MarketRegime.RANGING.value: 0.0,
            MarketRegime.VOLATILE.value: 0.0,
            MarketRegime.CHOPPY.value: 0.0
        }

        try:
            adx = metrics.get('adx', 0)
            plus_di = metrics.get('plus_di', 0)
            minus_di = metrics.get('minus_di', 0)
            choppiness = metrics.get('choppiness', 50)
            volatility = metrics.get('volatility', 0)
            bb_width = metrics.get('bb_width', 0)

            # Choppiness probability
            if choppiness > self.current_choppiness_threshold:
                probabilities[MarketRegime.CHOPPY.value] = min(1.0, (choppiness - self.current_choppiness_threshold) / 20.0)

            # Volatility probability
            if volatility > self.volatility_threshold:
                probabilities[MarketRegime.VOLATILE.value] = min(1.0, (volatility - self.volatility_threshold) / 0.02)

            # Trending probabilities
            if adx > self.current_adx_threshold:
                trend_strength = min(1.0, (adx - self.current_adx_threshold) / 20.0)
                if plus_di > minus_di:
                    probabilities[MarketRegime.TRENDING_UP.value] = trend_strength
                else:
                    probabilities[MarketRegime.TRENDING_DOWN.value] = trend_strength

            # Ranging probability (inverse of trending)
            max_trend_prob = max(probabilities[MarketRegime.TRENDING_UP.value],
                               probabilities[MarketRegime.TRENDING_DOWN.value])
            probabilities[MarketRegime.RANGING.value] = max(0.0, 1.0 - max_trend_prob -
                                                          probabilities[MarketRegime.CHOPPY.value] -
                                                          probabilities[MarketRegime.VOLATILE.value])

            # Normalize probabilities
            total_prob = sum(probabilities.values())
            if total_prob > 0:
                probabilities = {k: v / total_prob for k, v in probabilities.items()}

        except Exception as e:
            logger.warning(f"Error calculating regime probabilities: {str(e)}")

        return probabilities

    def detect_regime(self, df: pd.DataFrame) -> Tuple[MarketRegime, Dict[str, float], Dict[str, float]]:
        """
        Detect the current market regime with probabilistic confidence.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Tuple of (MarketRegime, metrics, probabilities)
        """
        if not self.enabled:
            return MarketRegime.UNKNOWN, {}, {}

        if len(df) < max(self.adx_period, self.bb_period, self.choppiness_period) + 10:
            logger.warning("Not enough data for regime detection")
            return MarketRegime.UNKNOWN, {}, {}

        try:
            # Calculate dynamic thresholds
            self._calculate_dynamic_thresholds(df)

            # Calculate indicators
            data = self.calculate_adx(df)
            data = self.calculate_bollinger_bands(data)
            data = self.calculate_choppiness_index(data)

            # Get the latest values
            latest = data.iloc[-1]

            # Calculate historical volatility
            returns = df['close'].pct_change().dropna()
            volatility = returns.rolling(max(self.volatility_lookback_periods)).std().iloc[-1] * np.sqrt(252)

            # Calculate metrics
            metrics = {
                "adx": latest['adx'],
                "plus_di": latest['plus_di'],
                "minus_di": latest['minus_di'],
                "bb_width": latest['bb_width'],
                "choppiness": latest['choppiness'],
                "volatility": volatility,
                "adx_threshold": self.current_adx_threshold,
                "choppiness_threshold": self.current_choppiness_threshold
            }

            # Calculate regime probabilities
            probabilities = self.calculate_regime_probabilities(metrics)

            # Determine primary regime based on highest probability
            primary_regime_name = max(probabilities.keys(), key=lambda k: probabilities[k])
            primary_regime = MarketRegime(primary_regime_name)

            # Check confidence threshold
            max_probability = probabilities[primary_regime_name]
            if max_probability < self.regime_confidence_threshold:
                primary_regime = MarketRegime.UNKNOWN
                logger.debug(f"Regime confidence {max_probability:.3f} below threshold {self.regime_confidence_threshold}")

            # Store regime and metrics
            self.historical_regimes.append(primary_regime)
            self.historical_metrics.append(metrics)

            # Maintain history size
            if len(self.historical_regimes) > self.regime_change_lookback * 2:
                self.historical_regimes.pop(0)
                self.historical_metrics.pop(0)

            return primary_regime, metrics, probabilities

        except Exception as e:
            logger.error(f"Error in regime detection: {str(e)}")
            return MarketRegime.UNKNOWN, {}, {}

    def get_strategy_recommendation(self, regime: MarketRegime, probabilities: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Get enhanced strategy recommendations based on market regime and probabilities.

        Args:
            regime: Current market regime
            probabilities: Regime probabilities (optional)

        Returns:
            Dictionary with strategy recommendations
        """
        recommendations = {
            "primary_strategy": None,
            "position_size_multiplier": 1.0,
            "stop_loss_multiplier": 1.0,
            "take_profit_multiplier": 1.0,
            "regime": regime.value,
            "confidence": 0.0
        }

        # Get confidence from probabilities if available
        if probabilities:
            recommendations["confidence"] = probabilities.get(regime.value, 0.0)

        # Strategy recommendations based on regime
        if regime == MarketRegime.TRENDING_UP:
            recommendations["primary_strategy"] = "momentum"
            recommendations["position_size_multiplier"] = 1.0
            recommendations["stop_loss_multiplier"] = 1.2
            recommendations["take_profit_multiplier"] = 1.5

        elif regime == MarketRegime.TRENDING_DOWN:
            recommendations["primary_strategy"] = "momentum"
            recommendations["position_size_multiplier"] = 0.8
            recommendations["stop_loss_multiplier"] = 1.0
            recommendations["take_profit_multiplier"] = 1.2

        elif regime == MarketRegime.RANGING:
            recommendations["primary_strategy"] = "mean_reversion"
            recommendations["position_size_multiplier"] = 1.0
            recommendations["stop_loss_multiplier"] = 1.0
            recommendations["take_profit_multiplier"] = 1.0

        elif regime == MarketRegime.VOLATILE:
            recommendations["primary_strategy"] = "mean_reversion"
            recommendations["position_size_multiplier"] = 0.7
            recommendations["stop_loss_multiplier"] = 1.5
            recommendations["take_profit_multiplier"] = 0.8

        elif regime == MarketRegime.CHOPPY:
            recommendations["primary_strategy"] = None  # No trading
            recommendations["position_size_multiplier"] = 0.0
            recommendations["stop_loss_multiplier"] = 0.0
            recommendations["take_profit_multiplier"] = 0.0

        else:  # UNKNOWN
            recommendations["primary_strategy"] = None
            recommendations["position_size_multiplier"] = 0.5
            recommendations["stop_loss_multiplier"] = 1.5
            recommendations["take_profit_multiplier"] = 0.8

        # Adjust recommendations based on confidence
        if probabilities and recommendations["confidence"] < self.regime_confidence_threshold:
            recommendations["position_size_multiplier"] *= 0.7  # Reduce position size for low confidence

        return recommendations

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the market and provide enhanced regime detection and strategy recommendations.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with analysis results
        """
        # Detect regime
        regime, metrics, probabilities = self.detect_regime(df)

        # Get strategy recommendations
        recommendations = self.get_strategy_recommendation(regime, probabilities)

        # Check for regime change
        regime_change = False
        regime_change_confidence = 0.0

        if len(self.historical_regimes) > 1:
            regime_change = self.historical_regimes[-1] != self.historical_regimes[-2]

            # Calculate regime change confidence
            if regime_change and len(self.historical_regimes) >= self.regime_change_lookback:
                recent_regimes = self.historical_regimes[-self.regime_change_lookback:]
                regime_stability = len(set(recent_regimes)) / len(recent_regimes)
                regime_change_confidence = 1.0 - regime_stability

        # Combine results
        results = {
            "regime": regime.value,
            "metrics": metrics,
            "probabilities": probabilities,
            "recommendations": recommendations,
            "regime_change": regime_change,
            "regime_change_confidence": regime_change_confidence,
            "adaptive_thresholds": {
                "adx_threshold": self.current_adx_threshold,
                "choppiness_threshold": self.current_choppiness_threshold
            },
            "timestamp": datetime.now().isoformat()
        }

        return results

    def get_regime_history(self, lookback: int = None) -> List[Dict[str, Any]]:
        """
        Get historical regime data.

        Args:
            lookback: Number of historical points to return (None for all)

        Returns:
            List of historical regime data
        """
        if lookback is None:
            lookback = len(self.historical_regimes)

        history = []
        for i in range(max(0, len(self.historical_regimes) - lookback), len(self.historical_regimes)):
            if i < len(self.historical_metrics):
                history.append({
                    "regime": self.historical_regimes[i].value,
                    "metrics": self.historical_metrics[i],
                    "index": i
                })

        return history
