"""
Whale Signal Processor for Synergy7 Trading System.

This module processes whale signals for integration with trading strategies,
applies filters and validation, and generates trading recommendations.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class WhaleSignalProcessor:
    """
    Processes whale signals for trading strategy integration.
    
    This class takes raw whale signals and processes them for use in trading strategies,
    applying filters, validation, and generating actionable trading recommendations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the whale signal processor.
        
        Args:
            config: Configuration dictionary with whale_watching section
        """
        # Get whale watching configuration
        whale_config = config.get("whale_watching", {})
        
        # Basic configuration
        self.enabled = whale_config.get("enabled", True)
        self.confidence_weight = whale_config.get("whale_confidence_weight", 0.3)
        self.signal_decay_hours = whale_config.get("whale_signal_decay_hours", 6)
        
        # Signal filters
        signal_filters = whale_config.get("whale_signal_filters", {})
        self.min_whale_count = signal_filters.get("min_whale_count", 3)
        self.min_transaction_volume = signal_filters.get("min_transaction_volume", 500000)
        self.min_confidence_threshold = 0.2
        self.max_signal_age_hours = 12
        
        # Signal processing parameters
        self.signal_smoothing_factor = 0.3
        self.momentum_lookback_periods = [5, 10, 20]
        self.volume_confirmation_threshold = 1.5
        
        # Historical data
        self.processed_signals_history = []
        self.signal_performance_tracking = {}
        
        logger.info("Initialized whale signal processor")
    
    def validate_whale_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Validate a whale signal for quality and reliability.
        
        Args:
            signal: Whale signal dictionary
            
        Returns:
            True if signal is valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['token_address', 'signal_direction', 'confidence', 'whale_count', 'total_volume_usd']
            for field in required_fields:
                if field not in signal:
                    logger.debug(f"Signal missing required field: {field}")
                    return False
            
            # Check whale count threshold
            if signal.get('whale_count', 0) < self.min_whale_count:
                logger.debug(f"Signal whale count {signal.get('whale_count')} below threshold {self.min_whale_count}")
                return False
            
            # Check volume threshold
            if signal.get('total_volume_usd', 0) < self.min_transaction_volume:
                logger.debug(f"Signal volume {signal.get('total_volume_usd')} below threshold {self.min_transaction_volume}")
                return False
            
            # Check confidence threshold
            if signal.get('confidence', 0) < self.min_confidence_threshold:
                logger.debug(f"Signal confidence {signal.get('confidence')} below threshold {self.min_confidence_threshold}")
                return False
            
            # Check signal age
            try:
                signal_time = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                age_hours = (datetime.now() - signal_time).total_seconds() / 3600
                if age_hours > self.max_signal_age_hours:
                    logger.debug(f"Signal age {age_hours:.1f}h exceeds maximum {self.max_signal_age_hours}h")
                    return False
            except:
                logger.debug("Could not parse signal timestamp")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Error validating whale signal: {str(e)}")
            return False
    
    def calculate_signal_strength(self, signal: Dict[str, Any], market_data: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate enhanced signal strength incorporating market context.
        
        Args:
            signal: Whale signal dictionary
            market_data: Optional market data for context
            
        Returns:
            Enhanced signal strength (0.0 to 1.0)
        """
        try:
            base_strength = signal.get('signal_strength', 0.0)
            confidence = signal.get('confidence', 0.0)
            whale_count = signal.get('whale_count', 0)
            volume_usd = signal.get('total_volume_usd', 0)
            
            # Base signal strength from whale activity
            whale_count_factor = min(1.0, whale_count / (self.min_whale_count * 2))
            volume_factor = min(1.0, volume_usd / (self.min_transaction_volume * 2))
            
            # Combine factors
            enhanced_strength = (
                base_strength * 0.4 +
                confidence * 0.3 +
                whale_count_factor * 0.2 +
                volume_factor * 0.1
            )
            
            # Apply market context if available
            if market_data is not None and len(market_data) > 0:
                try:
                    # Check volume confirmation
                    recent_volume = market_data['volume'].tail(5).mean()
                    avg_volume = market_data['volume'].tail(20).mean()
                    volume_ratio = recent_volume / max(avg_volume, 1)
                    
                    if volume_ratio > self.volume_confirmation_threshold:
                        enhanced_strength *= 1.2  # Boost signal if volume confirms
                    elif volume_ratio < 0.5:
                        enhanced_strength *= 0.8  # Reduce signal if volume is low
                    
                    # Check price momentum alignment
                    if len(market_data) >= 10:
                        short_momentum = (market_data['close'].iloc[-1] / market_data['close'].iloc[-5] - 1)
                        signal_direction = signal.get('signal_direction', 0)
                        
                        # If whale signal aligns with price momentum, boost strength
                        if (signal_direction > 0 and short_momentum > 0) or (signal_direction < 0 and short_momentum < 0):
                            enhanced_strength *= 1.1
                        elif (signal_direction > 0 and short_momentum < -0.02) or (signal_direction < 0 and short_momentum > 0.02):
                            enhanced_strength *= 0.9  # Slight reduction for counter-trend signals
                
                except Exception as e:
                    logger.debug(f"Error applying market context: {str(e)}")
            
            return min(1.0, enhanced_strength)
        
        except Exception as e:
            logger.warning(f"Error calculating signal strength: {str(e)}")
            return signal.get('signal_strength', 0.0)
    
    def process_whale_signal(self, signal: Dict[str, Any], market_data: Optional[pd.DataFrame] = None) -> Optional[Dict[str, Any]]:
        """
        Process a whale signal into a trading recommendation.
        
        Args:
            signal: Raw whale signal
            market_data: Optional market data for context
            
        Returns:
            Processed trading signal or None if signal is invalid
        """
        if not self.enabled:
            return None
        
        try:
            # Validate signal
            if not self.validate_whale_signal(signal):
                return None
            
            # Calculate enhanced signal strength
            enhanced_strength = self.calculate_signal_strength(signal, market_data)
            
            # Create processed signal
            processed_signal = {
                'source': 'whale_watching',
                'token_address': signal['token_address'],
                'signal_type': 'whale_momentum',
                'direction': signal.get('signal_direction', 0),
                'strength': enhanced_strength,
                'confidence': signal.get('confidence', 0.0),
                'weight': self.confidence_weight,
                'whale_metrics': {
                    'whale_count': signal.get('whale_count', 0),
                    'total_volume_usd': signal.get('total_volume_usd', 0),
                    'net_buying_ratio': signal.get('net_buying_ratio', 0.0)
                },
                'timestamp': datetime.now().isoformat(),
                'original_timestamp': signal.get('timestamp'),
                'decay_time': signal.get('decay_time'),
                'processing_metadata': {
                    'validated': True,
                    'enhanced_strength': enhanced_strength,
                    'original_strength': signal.get('signal_strength', 0.0),
                    'market_context_applied': market_data is not None
                }
            }
            
            # Add to history
            self.processed_signals_history.append(processed_signal.copy())
            
            # Maintain history size
            if len(self.processed_signals_history) > 1000:
                self.processed_signals_history.pop(0)
            
            return processed_signal
        
        except Exception as e:
            logger.error(f"Error processing whale signal: {str(e)}")
            return None
    
    def combine_whale_signals(self, signals: List[Dict[str, Any]], token_address: str) -> Optional[Dict[str, Any]]:
        """
        Combine multiple whale signals for the same token.
        
        Args:
            signals: List of whale signals for the same token
            token_address: Token address
            
        Returns:
            Combined signal or None if no valid signals
        """
        try:
            if not signals:
                return None
            
            # Filter valid signals
            valid_signals = [s for s in signals if self.validate_whale_signal(s)]
            
            if not valid_signals:
                return None
            
            # Calculate weighted average direction and strength
            total_weight = 0
            weighted_direction = 0
            weighted_strength = 0
            total_confidence = 0
            total_whale_count = 0
            total_volume = 0
            
            for signal in valid_signals:
                weight = signal.get('confidence', 0.0)
                total_weight += weight
                weighted_direction += signal.get('signal_direction', 0) * weight
                weighted_strength += signal.get('signal_strength', 0.0) * weight
                total_confidence += signal.get('confidence', 0.0)
                total_whale_count += signal.get('whale_count', 0)
                total_volume += signal.get('total_volume_usd', 0)
            
            if total_weight == 0:
                return None
            
            # Calculate combined metrics
            combined_direction = weighted_direction / total_weight
            combined_strength = weighted_strength / total_weight
            avg_confidence = total_confidence / len(valid_signals)
            
            # Create combined signal
            combined_signal = {
                'source': 'whale_watching_combined',
                'token_address': token_address,
                'signal_type': 'whale_momentum_combined',
                'direction': 1 if combined_direction > 0.1 else (-1 if combined_direction < -0.1 else 0),
                'strength': combined_strength,
                'confidence': avg_confidence,
                'weight': self.confidence_weight,
                'whale_metrics': {
                    'whale_count': total_whale_count,
                    'total_volume_usd': total_volume,
                    'signal_count': len(valid_signals)
                },
                'timestamp': datetime.now().isoformat(),
                'processing_metadata': {
                    'combined_from_signals': len(valid_signals),
                    'total_weight': total_weight,
                    'weighted_direction': combined_direction
                }
            }
            
            return combined_signal
        
        except Exception as e:
            logger.error(f"Error combining whale signals: {str(e)}")
            return None
    
    def get_signal_recommendation(self, processed_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading recommendation from processed whale signal.
        
        Args:
            processed_signal: Processed whale signal
            
        Returns:
            Trading recommendation dictionary
        """
        try:
            direction = processed_signal.get('direction', 0)
            strength = processed_signal.get('strength', 0.0)
            confidence = processed_signal.get('confidence', 0.0)
            
            # Calculate position sizing recommendation
            base_position_size = 0.05  # 5% base position
            strength_multiplier = strength * 2.0  # Scale by strength
            confidence_multiplier = confidence * 1.5  # Scale by confidence
            
            recommended_position_size = base_position_size * strength_multiplier * confidence_multiplier
            recommended_position_size = min(0.15, recommended_position_size)  # Cap at 15%
            
            # Generate recommendation
            recommendation = {
                'action': 'buy' if direction > 0 else ('sell' if direction < 0 else 'hold'),
                'position_size_pct': recommended_position_size,
                'confidence_score': confidence,
                'signal_strength': strength,
                'priority': 'high' if confidence > 0.7 and strength > 0.6 else ('medium' if confidence > 0.4 else 'low'),
                'time_horizon': 'short_term',  # Whale signals are typically short-term
                'risk_level': 'medium',
                'stop_loss_pct': 0.05,  # 5% stop loss
                'take_profit_pct': 0.10,  # 10% take profit
                'whale_context': processed_signal.get('whale_metrics', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            return recommendation
        
        except Exception as e:
            logger.error(f"Error generating signal recommendation: {str(e)}")
            return {'action': 'hold', 'error': str(e)}
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get summary of signal processing activity.
        
        Returns:
            Dictionary with processing summary
        """
        try:
            total_processed = len(self.processed_signals_history)
            
            if total_processed == 0:
                return {
                    'enabled': self.enabled,
                    'total_processed': 0,
                    'recent_activity': 'none'
                }
            
            # Analyze recent signals (last hour)
            recent_cutoff = datetime.now() - timedelta(hours=1)
            recent_signals = []
            
            for signal in self.processed_signals_history[-50:]:  # Check last 50 signals
                try:
                    signal_time = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                    if signal_time > recent_cutoff:
                        recent_signals.append(signal)
                except:
                    continue
            
            # Calculate statistics
            buy_signals = sum(1 for s in recent_signals if s.get('direction', 0) > 0)
            sell_signals = sum(1 for s in recent_signals if s.get('direction', 0) < 0)
            avg_confidence = np.mean([s.get('confidence', 0) for s in recent_signals]) if recent_signals else 0.0
            avg_strength = np.mean([s.get('strength', 0) for s in recent_signals]) if recent_signals else 0.0
            
            return {
                'enabled': self.enabled,
                'total_processed': total_processed,
                'recent_signals_1h': len(recent_signals),
                'recent_buy_signals': buy_signals,
                'recent_sell_signals': sell_signals,
                'average_confidence': avg_confidence,
                'average_strength': avg_strength,
                'last_update': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting processing summary: {str(e)}")
            return {'enabled': self.enabled, 'error': str(e)}
