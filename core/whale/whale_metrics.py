#!/usr/bin/env python3
"""
Whale Metrics - Provides metrics and analytics for whale activities
Calculates performance metrics for whale detection system.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WhaleMetrics:
    """Provides whale detection metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize whale metrics."""
        self.config = config
        self.whale_config = config.get('whale_watching', {})
        
        # Metrics data
        self.metrics = {
            'whales_detected': 0,
            'signals_generated': 0,
            'accuracy_score': 0.0,
            'last_detection': None,
            'detection_rate': 0.0
        }
        
        logger.info("Initialized WhaleMetrics")
    
    def update_metrics(self, whale_data: Dict[str, Any]) -> None:
        """Update whale detection metrics."""
        try:
            if whale_data.get('whales_detected', 0) > 0:
                self.metrics['whales_detected'] += whale_data['whales_detected']
                self.metrics['last_detection'] = datetime.now()
            
            if whale_data.get('signals_generated', 0) > 0:
                self.metrics['signals_generated'] += whale_data['signals_generated']
            
            # Calculate detection rate
            if self.metrics['signals_generated'] > 0:
                self.metrics['detection_rate'] = self.metrics['whales_detected'] / self.metrics['signals_generated']
            
            logger.debug("Updated whale metrics")
            
        except Exception as e:
            logger.error(f"Error updating whale metrics: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current whale metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset whale metrics."""
        self.metrics = {
            'whales_detected': 0,
            'signals_generated': 0,
            'accuracy_score': 0.0,
            'last_detection': None,
            'detection_rate': 0.0
        }
        logger.info("Reset whale metrics")
    
    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate whale detection performance."""
        try:
            performance = {
                'total_detections': self.metrics['whales_detected'],
                'total_signals': self.metrics['signals_generated'],
                'detection_rate': self.metrics['detection_rate'],
                'accuracy_score': self.metrics['accuracy_score'],
                'last_detection': self.metrics['last_detection'],
                'performance_score': self.metrics['detection_rate'] * self.metrics['accuracy_score']
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"Error calculating whale performance: {e}")
            return {}
