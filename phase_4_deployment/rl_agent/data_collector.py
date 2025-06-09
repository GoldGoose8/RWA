#!/usr/bin/env python3
"""
RL Data Collector Module

This module collects data for reinforcement learning training.
It stores signal-result pairs for later training.
"""

import os
import sys
import json
import time
import logging
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rl_data_collector')

class RLDataCollector:
    """
    Collects data for reinforcement learning training.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the RL data collector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.data_collection = self.config.get('data_collection', True)
        self.collection_path = self.config.get('collection_path', 'output/rl_data')
        
        # Create collection directory if it doesn't exist
        if self.enabled and self.data_collection:
            os.makedirs(self.collection_path, exist_ok=True)
        
        # Initialize data storage
        self.signals = {}  # Map of signal_id -> signal
        self.results = {}  # Map of signal_id -> result
        self.pairs = []    # List of (signal, result) pairs
        
        logger.info(f"Initialized RLDataCollector with enabled={self.enabled}, "
                   f"data_collection={self.data_collection}")
    
    def _generate_signal_id(self, signal: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a signal.
        
        Args:
            signal: Signal to generate ID for
            
        Returns:
            Unique signal ID
        """
        # Use timestamp and strategy_id if available
        timestamp = signal.get('timestamp', time.time())
        strategy_id = signal.get('strategy_id', 'unknown')
        market = signal.get('market', 'unknown')
        
        # Generate a unique ID
        return f"{strategy_id}_{market}_{timestamp}"
    
    def store_signal(self, signal: Dict[str, Any]) -> str:
        """
        Store a signal for later pairing with a result.
        
        Args:
            signal: Signal to store
            
        Returns:
            Signal ID
        """
        if not self.enabled or not self.data_collection:
            return ""
        
        # Generate signal ID
        signal_id = self._generate_signal_id(signal)
        
        # Store signal
        self.signals[signal_id] = signal
        
        logger.debug(f"Stored signal with ID {signal_id}")
        return signal_id
    
    def store_result(self, signal_id: str, result: Dict[str, Any]) -> None:
        """
        Store a result for a signal.
        
        Args:
            signal_id: ID of the signal
            result: Result to store
        """
        if not self.enabled or not self.data_collection:
            return
        
        # Check if signal exists
        if signal_id not in self.signals:
            logger.warning(f"Signal with ID {signal_id} not found")
            return
        
        # Store result
        self.results[signal_id] = result
        
        # Create signal-result pair
        signal = self.signals[signal_id]
        self.pairs.append((signal, result))
        
        logger.debug(f"Stored result for signal with ID {signal_id}")
        
        # Save pair to file
        self._save_pair(signal, result)
    
    def _save_pair(self, signal: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Save a signal-result pair to file.
        
        Args:
            signal: Signal
            result: Result
        """
        try:
            # Generate filename
            timestamp = int(time.time())
            strategy_id = signal.get('strategy_id', 'unknown')
            market = signal.get('market', 'unknown')
            filename = f"{timestamp}_{strategy_id}_{market}.json"
            
            # Create file path
            file_path = os.path.join(self.collection_path, filename)
            
            # Save pair to file
            with open(file_path, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'signal': signal,
                    'result': result
                }, f, indent=2)
            
            logger.debug(f"Saved signal-result pair to {file_path}")
        except Exception as e:
            logger.error(f"Error saving signal-result pair: {str(e)}")
    
    def get_training_data(self, limit: int = 1000) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Get training data for RL training.
        
        Args:
            limit: Maximum number of pairs to return
            
        Returns:
            List of (signal, result) pairs
        """
        if not self.enabled:
            return []
        
        # Return pairs from memory
        return self.pairs[-limit:]
    
    def load_training_data(self, days: int = 30) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Load training data from files.
        
        Args:
            days: Number of days of data to load
            
        Returns:
            List of (signal, result) pairs
        """
        if not self.enabled or not self.data_collection:
            return []
        
        try:
            # Calculate cutoff timestamp
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Get list of files
            files = os.listdir(self.collection_path)
            
            # Filter files by timestamp
            filtered_files = []
            for file in files:
                if not file.endswith('.json'):
                    continue
                
                try:
                    # Extract timestamp from filename
                    timestamp = int(file.split('_')[0])
                    
                    if timestamp >= cutoff_timestamp:
                        filtered_files.append(file)
                except:
                    # Skip files with invalid names
                    continue
            
            # Sort files by timestamp (newest first)
            filtered_files.sort(reverse=True)
            
            # Load pairs from files
            pairs = []
            for file in filtered_files:
                try:
                    with open(os.path.join(self.collection_path, file), 'r') as f:
                        data = json.load(f)
                    
                    signal = data.get('signal', {})
                    result = data.get('result', {})
                    
                    pairs.append((signal, result))
                except Exception as e:
                    logger.error(f"Error loading pair from {file}: {str(e)}")
            
            logger.info(f"Loaded {len(pairs)} signal-result pairs from {len(filtered_files)} files")
            return pairs
        except Exception as e:
            logger.error(f"Error loading training data: {str(e)}")
            return []
    
    def extract_features(self, signal: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from a signal for RL training.
        
        Args:
            signal: Signal to extract features from
            
        Returns:
            NumPy array of features
        """
        # Extract basic features
        features = []
        
        # Confidence
        confidence = signal.get('confidence', 0.5)
        features.append(confidence)
        
        # Metadata
        metadata = signal.get('metadata', {})
        
        # Priority score
        priority_score = metadata.get('priority_score', 0.0)
        features.append(priority_score)
        
        # Filter scores
        momentum_score = 0.0
        liquidity_score = 0.0
        volatility_score = 0.0
        alpha_wallet_score = 0.0
        
        # Extract scores from metadata
        if 'momentum_score' in metadata:
            momentum_score = metadata['momentum_score']
        if 'liquidity_score' in metadata:
            liquidity_score = metadata['liquidity_score']
        if 'volatility_score' in metadata:
            volatility_score = metadata['volatility_score']
        if 'alpha_wallet_score' in metadata:
            alpha_wallet_score = metadata['alpha_wallet_score']
        
        # Extract scores from filter results
        if 'filter_results' in metadata:
            for result in metadata['filter_results']:
                if 'momentum_score' in result:
                    momentum_score = result['momentum_score']
                if 'liquidity_score' in result:
                    liquidity_score = result['liquidity_score']
                if 'volatility_score' in result:
                    volatility_score = result['volatility_score']
                if 'alpha_wallet_score' in result:
                    alpha_wallet_score = result['alpha_wallet_score']
        
        features.extend([momentum_score, liquidity_score, volatility_score, alpha_wallet_score])
        
        return np.array(features, dtype=np.float32)
    
    def extract_reward(self, result: Dict[str, Any]) -> float:
        """
        Extract reward from a result for RL training.
        
        Args:
            result: Result to extract reward from
            
        Returns:
            Reward value
        """
        # Extract profit/loss
        profit_loss = result.get('profit_loss', 0.0)
        
        # Extract execution quality
        execution_quality = result.get('execution_quality', 0.5)
        
        # Calculate reward
        # 80% profit/loss, 20% execution quality
        reward = 0.8 * profit_loss + 0.2 * execution_quality
        
        return reward
    
    def prepare_training_batch(self, pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare a batch of training data for RL training.
        
        Args:
            pairs: List of (signal, result) pairs
            
        Returns:
            Tuple of (features, rewards)
        """
        if not pairs:
            return np.array([]), np.array([])
        
        # Extract features and rewards
        features = []
        rewards = []
        
        for signal, result in pairs:
            try:
                # Extract features
                signal_features = self.extract_features(signal)
                features.append(signal_features)
                
                # Extract reward
                reward = self.extract_reward(result)
                rewards.append(reward)
            except Exception as e:
                logger.error(f"Error preparing training data: {str(e)}")
        
        return np.array(features), np.array(rewards)
    
    def clear_memory(self) -> None:
        """Clear in-memory data."""
        self.signals = {}
        self.results = {}
        self.pairs = []
        
        logger.info("Cleared in-memory data")
