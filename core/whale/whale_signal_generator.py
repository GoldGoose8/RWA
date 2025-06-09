#!/usr/bin/env python3
"""
Whale Signal Generator - Converts whale activity into trading signals
Analyzes whale transactions and flows to generate actionable trading signals.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

from .whale_detector import WhaleTransaction

logger = logging.getLogger(__name__)

@dataclass
class WhaleSignal:
    """Represents a trading signal generated from whale activity."""
    signal_id: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    strength: float
    signal_type: str  # 'accumulation', 'distribution', 'exchange_flow', 'smart_money'
    timeframe: str  # 'short', 'medium', 'long'
    whale_data: Dict[str, Any]
    metadata: Dict[str, Any]

class WhaleSignalGenerator:
    """Generates trading signals from whale activity analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize whale signal generator."""
        self.config = config
        self.whale_config = config.get('whale_detection', {})
        self.signal_config = config.get('signal_generation', {})
        
        # Signal generation settings
        self.accumulation_threshold = self.whale_config.get('accumulation_threshold_sol', 1000)
        self.distribution_threshold = self.whale_config.get('distribution_threshold_sol', 500)
        self.confidence_threshold = self.whale_config.get('confidence_threshold', 0.6)
        
        # Time windows for analysis
        self.short_term_window = timedelta(minutes=self.signal_config.get('short_term_minutes', 15))
        self.medium_term_window = timedelta(minutes=self.signal_config.get('medium_term_minutes', 60))
        self.long_term_window = timedelta(minutes=self.signal_config.get('long_term_minutes', 240))
        
        # Signal strength settings
        self.accumulation_strength = self.signal_config.get('accumulation_signal_strength', 0.8)
        self.distribution_strength = self.signal_config.get('distribution_signal_strength', 0.6)
        self.exchange_flow_strength = self.signal_config.get('exchange_flow_signal_strength', 0.7)
        self.whale_confirmation_bonus = self.signal_config.get('whale_confirmation_bonus', 0.2)
        
        # Generated signals cache
        self.generated_signals = []
        self.signal_history = defaultdict(list)
        
        logger.info("Whale signal generator initialized")
    
    def generate_signals(self, whale_transactions: List[WhaleTransaction], 
                        base_signal: Optional[Dict[str, Any]] = None) -> List[WhaleSignal]:
        """Generate trading signals from whale transactions."""
        
        if not whale_transactions:
            return []
        
        signals = []
        current_time = datetime.now()
        
        # Analyze different timeframes
        for timeframe, window in [
            ('short', self.short_term_window),
            ('medium', self.medium_term_window),
            ('long', self.long_term_window)
        ]:
            # Filter transactions for this timeframe
            cutoff_time = current_time - window
            timeframe_transactions = [
                tx for tx in whale_transactions 
                if tx.timestamp > cutoff_time
            ]
            
            if not timeframe_transactions:
                continue
            
            # Generate signals for this timeframe
            timeframe_signals = self._analyze_timeframe(timeframe_transactions, timeframe, base_signal)
            signals.extend(timeframe_signals)
        
        # Store generated signals
        self.generated_signals.extend(signals)
        
        # Clean old signals (keep last 1000)
        if len(self.generated_signals) > 1000:
            self.generated_signals = self.generated_signals[-1000:]
        
        return signals
    
    def _analyze_timeframe(self, transactions: List[WhaleTransaction], 
                          timeframe: str, base_signal: Optional[Dict[str, Any]]) -> List[WhaleSignal]:
        """Analyze whale transactions for a specific timeframe."""
        
        signals = []
        
        # 1. Accumulation/Distribution Analysis
        accumulation_signal = self._analyze_accumulation_distribution(transactions, timeframe)
        if accumulation_signal:
            signals.append(accumulation_signal)
        
        # 2. Exchange Flow Analysis
        exchange_flow_signal = self._analyze_exchange_flows(transactions, timeframe)
        if exchange_flow_signal:
            signals.append(exchange_flow_signal)
        
        # 3. Smart Money Analysis
        smart_money_signal = self._analyze_smart_money(transactions, timeframe)
        if smart_money_signal:
            signals.append(smart_money_signal)
        
        # 4. Whale Confirmation Analysis (if base signal provided)
        if base_signal:
            confirmation_signal = self._analyze_whale_confirmation(transactions, base_signal, timeframe)
            if confirmation_signal:
                signals.append(confirmation_signal)
        
        return signals
    
    def _analyze_accumulation_distribution(self, transactions: List[WhaleTransaction], 
                                         timeframe: str) -> Optional[WhaleSignal]:
        """Analyze accumulation vs distribution patterns."""
        
        if not transactions:
            return None
        
        # Calculate net flow
        total_accumulation = 0
        total_distribution = 0
        exchange_inflow = 0
        exchange_outflow = 0
        
        for tx in transactions:
            if tx.is_exchange_related:
                # Determine if this is inflow (to exchange) or outflow (from exchange)
                # This is simplified - in reality, we'd need to check transaction direction
                if tx.amount_sol > 0:
                    exchange_inflow += tx.amount_sol
                else:
                    exchange_outflow += abs(tx.amount_sol)
            else:
                # Non-exchange transactions
                if tx.confidence_score > 0.7:
                    total_accumulation += tx.amount_sol
                else:
                    total_distribution += tx.amount_sol
        
        # Calculate net flow
        net_exchange_flow = exchange_outflow - exchange_inflow  # Positive = bullish (leaving exchanges)
        net_whale_flow = total_accumulation - total_distribution
        
        # Determine signal
        action = 'HOLD'
        confidence = 0.5
        strength = 0.5
        signal_type = 'accumulation'
        
        # Exchange flow signals (stronger)
        if net_exchange_flow > self.accumulation_threshold:
            action = 'BUY'
            confidence = min(0.9, 0.6 + (net_exchange_flow / self.accumulation_threshold) * 0.2)
            strength = self.exchange_flow_strength
            signal_type = 'exchange_outflow'
        elif net_exchange_flow < -self.distribution_threshold:
            action = 'SELL'
            confidence = min(0.9, 0.6 + (abs(net_exchange_flow) / self.distribution_threshold) * 0.2)
            strength = self.exchange_flow_strength
            signal_type = 'exchange_inflow'
        
        # Whale accumulation/distribution signals
        elif net_whale_flow > self.accumulation_threshold:
            action = 'BUY'
            confidence = min(0.85, 0.6 + (net_whale_flow / self.accumulation_threshold) * 0.15)
            strength = self.accumulation_strength
            signal_type = 'whale_accumulation'
        elif net_whale_flow < -self.distribution_threshold:
            action = 'SELL'
            confidence = min(0.85, 0.6 + (abs(net_whale_flow) / self.distribution_threshold) * 0.15)
            strength = self.distribution_strength
            signal_type = 'whale_distribution'
        
        # Only generate signal if confidence is above threshold
        if confidence < self.confidence_threshold:
            return None
        
        # Create signal
        signal_id = f"whale_{signal_type}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        whale_data = {
            'net_exchange_flow': net_exchange_flow,
            'net_whale_flow': net_whale_flow,
            'total_accumulation': total_accumulation,
            'total_distribution': total_distribution,
            'exchange_inflow': exchange_inflow,
            'exchange_outflow': exchange_outflow,
            'transaction_count': len(transactions),
            'avg_transaction_size': np.mean([tx.amount_sol for tx in transactions]),
            'max_transaction_size': max([tx.amount_sol for tx in transactions]),
            'unique_addresses': len(set([tx.from_address for tx in transactions] + [tx.to_address for tx in transactions]))
        }
        
        metadata = {
            'analysis_window': timeframe,
            'transactions_analyzed': len(transactions),
            'signal_generation_time': datetime.now().isoformat(),
            'confidence_factors': {
                'exchange_flow_impact': abs(net_exchange_flow) / max(1, self.accumulation_threshold),
                'whale_flow_impact': abs(net_whale_flow) / max(1, self.accumulation_threshold),
                'transaction_volume': len(transactions),
                'average_confidence': np.mean([tx.confidence_score for tx in transactions])
            }
        }
        
        return WhaleSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            strength=strength,
            signal_type=signal_type,
            timeframe=timeframe,
            whale_data=whale_data,
            metadata=metadata
        )
    
    def _analyze_exchange_flows(self, transactions: List[WhaleTransaction], 
                               timeframe: str) -> Optional[WhaleSignal]:
        """Analyze exchange inflow/outflow patterns."""
        
        exchange_transactions = [tx for tx in transactions if tx.is_exchange_related]
        
        if not exchange_transactions:
            return None
        
        # Group by exchange
        exchange_flows = defaultdict(lambda: {'inflow': 0, 'outflow': 0})
        
        for tx in exchange_transactions:
            exchange = tx.exchange_name or 'unknown'
            # Simplified flow detection - in reality, need to check transaction direction
            if tx.amount_sol > 0:
                exchange_flows[exchange]['outflow'] += tx.amount_sol
            else:
                exchange_flows[exchange]['inflow'] += abs(tx.amount_sol)
        
        # Calculate total net flow
        total_net_flow = sum(
            flows['outflow'] - flows['inflow'] 
            for flows in exchange_flows.values()
        )
        
        # Generate signal based on net flow
        if abs(total_net_flow) < 200:  # Minimum threshold
            return None
        
        action = 'BUY' if total_net_flow > 0 else 'SELL'
        confidence = min(0.85, 0.6 + (abs(total_net_flow) / 1000) * 0.2)
        strength = self.exchange_flow_strength
        
        if confidence < self.confidence_threshold:
            return None
        
        signal_id = f"whale_exchange_flow_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        whale_data = {
            'total_net_flow': total_net_flow,
            'exchange_flows': dict(exchange_flows),
            'dominant_exchange': max(exchange_flows.keys(), key=lambda x: exchange_flows[x]['outflow'] + exchange_flows[x]['inflow']) if exchange_flows else None
        }
        
        metadata = {
            'analysis_type': 'exchange_flow',
            'timeframe': timeframe,
            'exchanges_involved': len(exchange_flows)
        }
        
        return WhaleSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            strength=strength,
            signal_type='exchange_flow',
            timeframe=timeframe,
            whale_data=whale_data,
            metadata=metadata
        )
    
    def _analyze_smart_money(self, transactions: List[WhaleTransaction], 
                            timeframe: str) -> Optional[WhaleSignal]:
        """Analyze smart money (high-confidence whale) activity."""
        
        # Filter for high-confidence whale transactions
        smart_money_transactions = [
            tx for tx in transactions 
            if tx.confidence_score > 0.8 and tx.amount_sol > 200
        ]
        
        if not smart_money_transactions:
            return None
        
        # Analyze smart money direction
        total_volume = sum(tx.amount_sol for tx in smart_money_transactions)
        avg_confidence = np.mean([tx.confidence_score for tx in smart_money_transactions])
        
        # Simple direction analysis (in reality, would need more sophisticated analysis)
        # For now, assume net positive volume is bullish
        if total_volume < 500:  # Minimum threshold
            return None
        
        action = 'BUY'  # Simplified - smart money activity generally bullish
        confidence = min(0.9, avg_confidence * 0.9)
        strength = 0.75
        
        if confidence < self.confidence_threshold:
            return None
        
        signal_id = f"whale_smart_money_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        whale_data = {
            'smart_money_volume': total_volume,
            'smart_money_count': len(smart_money_transactions),
            'average_confidence': avg_confidence,
            'largest_transaction': max(tx.amount_sol for tx in smart_money_transactions)
        }
        
        metadata = {
            'analysis_type': 'smart_money',
            'timeframe': timeframe,
            'min_confidence_threshold': 0.8
        }
        
        return WhaleSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            action=action,
            confidence=confidence,
            strength=strength,
            signal_type='smart_money',
            timeframe=timeframe,
            whale_data=whale_data,
            metadata=metadata
        )
    
    def _analyze_whale_confirmation(self, transactions: List[WhaleTransaction], 
                                   base_signal: Dict[str, Any], timeframe: str) -> Optional[WhaleSignal]:
        """Analyze if whale activity confirms a base trading signal."""
        
        if not base_signal or not transactions:
            return None
        
        base_action = base_signal.get('action', 'HOLD')
        if base_action == 'HOLD':
            return None
        
        # Analyze if whale activity supports the base signal
        supporting_volume = 0
        opposing_volume = 0
        
        for tx in transactions:
            # Simplified confirmation logic
            if base_action == 'BUY':
                if not tx.is_exchange_related or tx.amount_sol > 0:  # Accumulation or outflow
                    supporting_volume += tx.amount_sol * tx.confidence_score
                else:
                    opposing_volume += tx.amount_sol * tx.confidence_score
            elif base_action == 'SELL':
                if tx.is_exchange_related and tx.amount_sol < 0:  # Inflow to exchanges
                    supporting_volume += abs(tx.amount_sol) * tx.confidence_score
                else:
                    opposing_volume += tx.amount_sol * tx.confidence_score
        
        # Calculate confirmation strength
        total_volume = supporting_volume + opposing_volume
        if total_volume == 0:
            return None
        
        confirmation_ratio = supporting_volume / total_volume
        
        if confirmation_ratio < 0.6:  # Not enough confirmation
            return None
        
        # Enhance base signal with whale confirmation
        enhanced_confidence = min(0.95, base_signal.get('confidence', 0.5) + self.whale_confirmation_bonus)
        
        signal_id = f"whale_confirmation_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        whale_data = {
            'base_signal': base_signal,
            'supporting_volume': supporting_volume,
            'opposing_volume': opposing_volume,
            'confirmation_ratio': confirmation_ratio,
            'confidence_boost': self.whale_confirmation_bonus
        }
        
        metadata = {
            'analysis_type': 'whale_confirmation',
            'timeframe': timeframe,
            'base_signal_id': base_signal.get('signal_id', 'unknown')
        }
        
        return WhaleSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            action=base_action,
            confidence=enhanced_confidence,
            strength=base_signal.get('strength', 0.5) + 0.1,
            signal_type='whale_confirmation',
            timeframe=timeframe,
            whale_data=whale_data,
            metadata=metadata
        )
    
    def get_recent_signals(self, hours: int = 1) -> List[WhaleSignal]:
        """Get whale signals from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [signal for signal in self.generated_signals if signal.timestamp > cutoff_time]
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """Get summary of recent whale signals."""
        recent_signals = self.get_recent_signals(24)  # Last 24 hours
        
        if not recent_signals:
            return {'total_signals': 0, 'summary': 'No recent whale signals'}
        
        signal_types = defaultdict(int)
        actions = defaultdict(int)
        avg_confidence = np.mean([s.confidence for s in recent_signals])
        
        for signal in recent_signals:
            signal_types[signal.signal_type] += 1
            actions[signal.action] += 1
        
        return {
            'total_signals': len(recent_signals),
            'signal_types': dict(signal_types),
            'actions': dict(actions),
            'average_confidence': avg_confidence,
            'latest_signal': recent_signals[-1].signal_type if recent_signals else None,
            'timeframe_coverage': len(set(s.timeframe for s in recent_signals))
        }
