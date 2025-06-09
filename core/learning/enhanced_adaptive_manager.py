#!/usr/bin/env python3
"""
Enhanced Adaptive Strategy Manager - RL + Whale Integration
Combines reinforcement learning with whale activity analysis for superior trading performance.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from collections import deque
import pickle

from .adaptive_strategy_manager import AdaptiveStrategyManager
from ..whale.whale_signal_generator import WhaleSignal

logger = logging.getLogger(__name__)

class EnhancedAdaptiveManager(AdaptiveStrategyManager):
    """Enhanced adaptive strategy manager with whale intelligence integration."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced adaptive manager."""
        super().__init__(config)
        
        # Whale integration settings
        self.whale_config = config.get('whale_detection', {})
        self.whale_learning_enabled = self.whale_config.get('rl_learning_enabled', True)
        
        # Whale-specific learning parameters
        self.whale_signal_weight = 0.3  # Weight for whale signals in decision making
        self.whale_confirmation_bonus = 0.2  # Bonus for whale-confirmed signals
        self.whale_contradiction_penalty = 0.15  # Penalty for whale-contradicted signals
        
        # Whale signal tracking
        self.whale_signals_history = deque(maxlen=500)
        self.whale_performance_tracking = {}
        
        # Enhanced strategy weights with whale factors
        self.whale_enhanced_weights = {
            'momentum': 0.33,
            'mean_reversion': 0.33,
            'breakout': 0.34,
            'whale_following': 0.0  # New whale-following strategy
        }
        
        # Whale signal type performance
        self.whale_signal_performance = {
            'accumulation': {'trades': 0, 'profitable': 0, 'total_pnl': 0.0},
            'distribution': {'trades': 0, 'profitable': 0, 'total_pnl': 0.0},
            'exchange_flow': {'trades': 0, 'profitable': 0, 'total_pnl': 0.0},
            'smart_money': {'trades': 0, 'profitable': 0, 'total_pnl': 0.0},
            'whale_confirmation': {'trades': 0, 'profitable': 0, 'total_pnl': 0.0}
        }
        
        # Market regime detection enhanced with whale data
        self.whale_market_regimes = {
            'whale_accumulation': {'weight_multiplier': 1.4, 'confidence_boost': 0.15},
            'whale_distribution': {'weight_multiplier': 0.6, 'confidence_penalty': 0.1},
            'exchange_outflow': {'weight_multiplier': 1.3, 'confidence_boost': 0.1},
            'exchange_inflow': {'weight_multiplier': 0.7, 'confidence_penalty': 0.05},
            'smart_money_active': {'weight_multiplier': 1.5, 'confidence_boost': 0.2}
        }
        
        logger.info(f"Enhanced Adaptive Manager initialized with whale learning: {'ON' if self.whale_learning_enabled else 'OFF'}")
    
    def record_whale_signal(self, whale_signal: WhaleSignal) -> None:
        """Record a whale signal for learning."""
        if not self.whale_learning_enabled:
            return
        
        whale_signal_data = {
            'timestamp': whale_signal.timestamp.isoformat(),
            'signal_type': whale_signal.signal_type,
            'action': whale_signal.action,
            'confidence': whale_signal.confidence,
            'strength': whale_signal.strength,
            'timeframe': whale_signal.timeframe,
            'whale_data': whale_signal.whale_data,
            'metadata': whale_signal.metadata
        }
        
        self.whale_signals_history.append(whale_signal_data)
        logger.debug(f"Recorded whale signal: {whale_signal.signal_type} {whale_signal.action}")
    
    def record_trade_result_with_whale(self, signal: Dict[str, Any], result: Dict[str, Any], 
                                     pnl: float, whale_signals: List[WhaleSignal] = None):
        """Record trade result with whale signal correlation."""
        
        # Record base trade result
        super().record_trade_result(signal, result, pnl)
        
        if not self.whale_learning_enabled or not whale_signals:
            return
        
        # Analyze whale signal correlation
        for whale_signal in whale_signals:
            signal_type = whale_signal.signal_type
            
            # Update whale signal performance
            if signal_type in self.whale_signal_performance:
                perf = self.whale_signal_performance[signal_type]
                perf['trades'] += 1
                if pnl > 0:
                    perf['profitable'] += 1
                perf['total_pnl'] += pnl
                
                # Calculate correlation score
                correlation_score = self._calculate_whale_correlation(signal, whale_signal, pnl)
                
                # Store correlation for learning
                correlation_key = f"{signal.get('strategy', 'unknown')}_{signal_type}"
                if correlation_key not in self.whale_performance_tracking:
                    self.whale_performance_tracking[correlation_key] = {
                        'correlations': [],
                        'avg_correlation': 0.0,
                        'trade_count': 0
                    }
                
                tracking = self.whale_performance_tracking[correlation_key]
                tracking['correlations'].append(correlation_score)
                tracking['trade_count'] += 1
                tracking['avg_correlation'] = np.mean(tracking['correlations'][-50:])  # Last 50 trades
                
                logger.debug(f"Whale correlation {correlation_key}: {correlation_score:.3f}")
    
    def _calculate_whale_correlation(self, signal: Dict[str, Any], whale_signal: WhaleSignal, pnl: float) -> float:
        """Calculate correlation between whale signal and trade outcome."""
        
        # Base correlation from signal alignment
        signal_action = signal.get('action', 'HOLD')
        whale_action = whale_signal.action
        
        if signal_action == whale_action:
            alignment_score = 0.5
        elif signal_action == 'HOLD' or whale_action == 'HOLD':
            alignment_score = 0.0
        else:
            alignment_score = -0.5  # Opposite actions
        
        # Confidence factor
        confidence_factor = whale_signal.confidence * 0.3
        
        # Outcome factor
        outcome_factor = 0.2 if pnl > 0 else -0.2
        
        # Time proximity factor (closer in time = higher correlation)
        time_diff = abs((datetime.now() - whale_signal.timestamp).total_seconds())
        time_factor = max(0, 0.2 - (time_diff / 3600) * 0.1)  # Decay over hours
        
        correlation = alignment_score + confidence_factor + outcome_factor + time_factor
        return max(-1.0, min(1.0, correlation))
    
    def get_whale_enhanced_signal(self, base_signal: Dict[str, Any], 
                                 whale_signals: List[WhaleSignal]) -> Dict[str, Any]:
        """Enhance base signal with whale intelligence."""
        
        if not self.whale_learning_enabled or not whale_signals:
            return self.get_adapted_signal(base_signal)
        
        # Start with base RL adaptation
        adapted_signal = self.get_adapted_signal(base_signal)
        
        # Apply whale enhancements
        whale_enhanced_signal = adapted_signal.copy()
        
        # Analyze whale signal consensus
        whale_consensus = self._analyze_whale_consensus(whale_signals)
        
        # Apply whale-based modifications
        if whale_consensus['action'] != 'HOLD':
            # Whale signals provide direction
            if whale_consensus['action'] == adapted_signal.get('action'):
                # Whale confirms our signal - boost confidence
                whale_enhanced_signal['confidence'] = min(0.95, 
                    adapted_signal.get('confidence', 0.5) + whale_consensus['confidence_boost'])
                whale_enhanced_signal['whale_confirmation'] = True
                whale_enhanced_signal['whale_boost'] = whale_consensus['confidence_boost']
                
                # Increase position size if whale conviction is high
                if whale_consensus['strength'] > 0.8:
                    current_size = whale_enhanced_signal.get('size', 0)
                    whale_enhanced_signal['size'] = current_size * (1 + whale_consensus['strength'] * 0.2)
                    whale_enhanced_signal['whale_size_boost'] = whale_consensus['strength'] * 0.2
                
            elif whale_consensus['action'] != adapted_signal.get('action'):
                # Whale contradicts our signal - reduce confidence or override
                if whale_consensus['strength'] > 0.8:
                    # Strong whale signal overrides
                    whale_enhanced_signal['action'] = whale_consensus['action']
                    whale_enhanced_signal['confidence'] = whale_consensus['confidence']
                    whale_enhanced_signal['whale_override'] = True
                    whale_enhanced_signal['override_reason'] = f"Strong whale {whale_consensus['action']} signal"
                else:
                    # Weak whale signal - just reduce confidence
                    whale_enhanced_signal['confidence'] = max(0.1, 
                        adapted_signal.get('confidence', 0.5) - self.whale_contradiction_penalty)
                    whale_enhanced_signal['whale_contradiction'] = True
                    whale_enhanced_signal['confidence_penalty'] = self.whale_contradiction_penalty
        
        # Apply market regime adjustments based on whale activity
        current_regime = self._detect_whale_market_regime(whale_signals)
        if current_regime in self.whale_market_regimes:
            regime_config = self.whale_market_regimes[current_regime]
            
            # Apply regime-based adjustments
            if 'weight_multiplier' in regime_config:
                current_size = whale_enhanced_signal.get('size', 0)
                whale_enhanced_signal['size'] = current_size * regime_config['weight_multiplier']
                whale_enhanced_signal['regime_multiplier'] = regime_config['weight_multiplier']
            
            if 'confidence_boost' in regime_config:
                whale_enhanced_signal['confidence'] = min(0.95,
                    whale_enhanced_signal.get('confidence', 0.5) + regime_config['confidence_boost'])
                whale_enhanced_signal['regime_boost'] = regime_config['confidence_boost']
            
            if 'confidence_penalty' in regime_config:
                whale_enhanced_signal['confidence'] = max(0.1,
                    whale_enhanced_signal.get('confidence', 0.5) - regime_config['confidence_penalty'])
                whale_enhanced_signal['regime_penalty'] = regime_config['confidence_penalty']
            
            whale_enhanced_signal['whale_market_regime'] = current_regime
        
        # Add whale metadata
        whale_enhanced_signal['whale_enhanced'] = True
        whale_enhanced_signal['whale_signals_count'] = len(whale_signals)
        whale_enhanced_signal['whale_consensus'] = whale_consensus
        whale_enhanced_signal['whale_learning_enabled'] = self.whale_learning_enabled
        
        return whale_enhanced_signal
    
    def _analyze_whale_consensus(self, whale_signals: List[WhaleSignal]) -> Dict[str, Any]:
        """Analyze consensus from multiple whale signals."""
        
        if not whale_signals:
            return {'action': 'HOLD', 'confidence': 0.0, 'strength': 0.0, 'confidence_boost': 0.0}
        
        # Weight signals by confidence and recency
        weighted_actions = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_weight = 0.0
        total_strength = 0.0
        
        current_time = datetime.now()
        
        for signal in whale_signals:
            # Time decay factor (more recent = higher weight)
            time_diff = (current_time - signal.timestamp).total_seconds()
            time_weight = max(0.1, 1.0 - (time_diff / 3600))  # Decay over 1 hour
            
            # Signal quality weight
            quality_weight = signal.confidence * signal.strength
            
            # Combined weight
            signal_weight = time_weight * quality_weight
            
            weighted_actions[signal.action] += signal_weight
            total_weight += signal_weight
            total_strength += signal.strength * signal_weight
        
        if total_weight == 0:
            return {'action': 'HOLD', 'confidence': 0.0, 'strength': 0.0, 'confidence_boost': 0.0}
        
        # Normalize
        for action in weighted_actions:
            weighted_actions[action] /= total_weight
        
        avg_strength = total_strength / total_weight
        
        # Determine consensus action
        consensus_action = max(weighted_actions, key=weighted_actions.get)
        consensus_confidence = weighted_actions[consensus_action]
        
        # Calculate confidence boost
        confidence_boost = min(0.3, consensus_confidence * self.whale_confirmation_bonus)
        
        return {
            'action': consensus_action,
            'confidence': consensus_confidence,
            'strength': avg_strength,
            'confidence_boost': confidence_boost,
            'action_weights': weighted_actions,
            'signal_count': len(whale_signals)
        }
    
    def _detect_whale_market_regime(self, whale_signals: List[WhaleSignal]) -> str:
        """Detect current market regime based on whale activity."""
        
        if not whale_signals:
            return 'neutral'
        
        # Count signal types in recent timeframe
        signal_counts = {}
        total_volume = 0
        
        for signal in whale_signals:
            signal_type = signal.signal_type
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            
            # Add volume data if available
            if 'whale_data' in signal.whale_data:
                volume = signal.whale_data.get('total_accumulation', 0) + signal.whale_data.get('total_distribution', 0)
                total_volume += volume
        
        # Determine dominant regime
        if signal_counts.get('accumulation', 0) > signal_counts.get('distribution', 0):
            return 'whale_accumulation'
        elif signal_counts.get('distribution', 0) > signal_counts.get('accumulation', 0):
            return 'whale_distribution'
        elif signal_counts.get('exchange_flow', 0) > 0:
            # Check if net outflow or inflow
            return 'exchange_outflow'  # Simplified
        elif signal_counts.get('smart_money', 0) > 0:
            return 'smart_money_active'
        else:
            return 'neutral'
    
    def get_enhanced_learning_metrics(self) -> Dict[str, Any]:
        """Get enhanced learning metrics including whale performance."""
        
        base_metrics = self.get_learning_metrics()
        
        # Add whale-specific metrics
        whale_metrics = {
            'whale_learning_enabled': self.whale_learning_enabled,
            'whale_signals_tracked': len(self.whale_signals_history),
            'whale_signal_performance': self.whale_signal_performance.copy(),
            'whale_correlation_tracking': len(self.whale_performance_tracking),
            'whale_enhanced_weights': self.whale_enhanced_weights.copy()
        }
        
        # Calculate whale signal success rates
        whale_success_rates = {}
        for signal_type, perf in self.whale_signal_performance.items():
            if perf['trades'] > 0:
                whale_success_rates[signal_type] = {
                    'win_rate': perf['profitable'] / perf['trades'],
                    'avg_pnl': perf['total_pnl'] / perf['trades'],
                    'total_trades': perf['trades']
                }
        
        whale_metrics['whale_success_rates'] = whale_success_rates
        
        # Calculate best whale correlations
        best_correlations = {}
        for key, tracking in self.whale_performance_tracking.items():
            if tracking['trade_count'] >= 5:  # Minimum trades for reliability
                best_correlations[key] = {
                    'avg_correlation': tracking['avg_correlation'],
                    'trade_count': tracking['trade_count']
                }
        
        whale_metrics['best_whale_correlations'] = best_correlations
        
        # Combine with base metrics
        enhanced_metrics = {**base_metrics, 'whale_intelligence': whale_metrics}
        
        return enhanced_metrics
    
    def _save_enhanced_learning_state(self):
        """Save enhanced learning state including whale data."""
        try:
            # Save base state
            super()._save_learning_state()
            
            # Save whale-specific state
            whale_state = {
                'whale_signals_history': list(self.whale_signals_history),
                'whale_performance_tracking': self.whale_performance_tracking,
                'whale_signal_performance': self.whale_signal_performance,
                'whale_enhanced_weights': self.whale_enhanced_weights,
                'whale_learning_enabled': self.whale_learning_enabled
            }
            
            os.makedirs('output/learning', exist_ok=True)
            with open('output/learning/whale_adaptive_state.json', 'w') as f:
                json.dump(whale_state, f, indent=2)
                
            logger.debug("Enhanced learning state with whale data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving enhanced learning state: {e}")
    
    def _load_enhanced_learning_state(self):
        """Load enhanced learning state including whale data."""
        try:
            # Load base state
            super()._load_learning_state()
            
            # Load whale-specific state
            whale_state_file = 'output/learning/whale_adaptive_state.json'
            if os.path.exists(whale_state_file):
                with open(whale_state_file, 'r') as f:
                    whale_state = json.load(f)
                
                self.whale_signals_history = deque(whale_state.get('whale_signals_history', []), maxlen=500)
                self.whale_performance_tracking = whale_state.get('whale_performance_tracking', {})
                self.whale_signal_performance = whale_state.get('whale_signal_performance', self.whale_signal_performance)
                self.whale_enhanced_weights = whale_state.get('whale_enhanced_weights', self.whale_enhanced_weights)
                self.whale_learning_enabled = whale_state.get('whale_learning_enabled', True)
                
                logger.info("Enhanced learning state with whale data loaded successfully")
                
        except Exception as e:
            logger.warning(f"Could not load enhanced learning state: {e}")
            logger.info("Starting with fresh enhanced learning state")
