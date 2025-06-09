#!/usr/bin/env python3
"""
Whale Data Collector - Collects and stores whale transaction data
Manages historical whale data for analysis and learning.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import glob
from dataclasses import asdict

from .whale_detector import WhaleTransaction

logger = logging.getLogger(__name__)

class WhaleDataCollector:
    """Collects and manages whale transaction data."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize whale data collector."""
        self.config = config
        self.data_config = config.get('data_storage', {})
        
        # Storage settings
        self.save_transactions = self.data_config.get('save_whale_transactions', True)
        self.retention_days = self.data_config.get('retention_days', 30)
        self.backup_enabled = self.data_config.get('backup_enabled', True)
        
        # Data directories
        self.base_dir = "output/whale_data"
        self.transactions_dir = os.path.join(self.base_dir, "transactions")
        self.flows_dir = os.path.join(self.base_dir, "flows")
        self.signals_dir = os.path.join(self.base_dir, "signals")
        self.backups_dir = os.path.join(self.base_dir, "backups")
        
        # Create directories
        self._create_directories()
        
        # In-memory cache
        self.transaction_cache = []
        self.cache_size = 1000
        
        logger.info("Whale data collector initialized")
    
    def _create_directories(self):
        """Create necessary directories."""
        for directory in [self.transactions_dir, self.flows_dir, self.signals_dir, self.backups_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def store_whale_transaction(self, whale_tx: WhaleTransaction) -> bool:
        """Store a whale transaction."""
        if not self.save_transactions:
            return True
        
        try:
            # Add to cache
            self.transaction_cache.append(whale_tx)
            if len(self.transaction_cache) > self.cache_size:
                self.transaction_cache.pop(0)
            
            # Save to disk
            filename = f"whale_tx_{whale_tx.timestamp.strftime('%Y%m%d_%H%M%S')}_{whale_tx.signature[:8]}.json"
            filepath = os.path.join(self.transactions_dir, filename)
            
            tx_data = {
                'signature': whale_tx.signature,
                'timestamp': whale_tx.timestamp.isoformat(),
                'from_address': whale_tx.from_address,
                'to_address': whale_tx.to_address,
                'amount_sol': whale_tx.amount_sol,
                'amount_usd': whale_tx.amount_usd,
                'transaction_type': whale_tx.transaction_type,
                'is_exchange_related': whale_tx.is_exchange_related,
                'exchange_name': whale_tx.exchange_name,
                'confidence_score': whale_tx.confidence_score,
                'metadata': whale_tx.metadata
            }
            
            with open(filepath, 'w') as f:
                json.dump(tx_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing whale transaction: {e}")
            return False
    
    def load_whale_transactions(self, hours: int = 24) -> List[WhaleTransaction]:
        """Load whale transactions from the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            transactions = []
            
            # Get transaction files
            pattern = os.path.join(self.transactions_dir, "whale_tx_*.json")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        tx_data = json.load(f)
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(tx_data['timestamp'])
                    
                    # Filter by time
                    if timestamp > cutoff_time:
                        whale_tx = WhaleTransaction(
                            signature=tx_data['signature'],
                            timestamp=timestamp,
                            from_address=tx_data['from_address'],
                            to_address=tx_data['to_address'],
                            amount_sol=tx_data['amount_sol'],
                            amount_usd=tx_data['amount_usd'],
                            transaction_type=tx_data['transaction_type'],
                            is_exchange_related=tx_data['is_exchange_related'],
                            exchange_name=tx_data.get('exchange_name'),
                            confidence_score=tx_data['confidence_score'],
                            metadata=tx_data.get('metadata', {})
                        )
                        transactions.append(whale_tx)
                        
                except Exception as e:
                    logger.warning(f"Error loading transaction file {file_path}: {e}")
                    continue
            
            # Sort by timestamp
            transactions.sort(key=lambda x: x.timestamp)
            
            logger.info(f"Loaded {len(transactions)} whale transactions from last {hours} hours")
            return transactions
            
        except Exception as e:
            logger.error(f"Error loading whale transactions: {e}")
            return []
    
    def get_whale_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get whale transaction statistics."""
        try:
            transactions = self.load_whale_transactions(hours)
            
            if not transactions:
                return {'total_transactions': 0, 'total_volume_sol': 0, 'total_volume_usd': 0}
            
            total_volume_sol = sum(tx.amount_sol for tx in transactions)
            total_volume_usd = sum(tx.amount_usd for tx in transactions)
            
            exchange_transactions = [tx for tx in transactions if tx.is_exchange_related]
            exchange_volume_sol = sum(tx.amount_sol for tx in exchange_transactions)
            
            # Group by exchange
            exchange_breakdown = {}
            for tx in exchange_transactions:
                exchange = tx.exchange_name or 'Unknown'
                if exchange not in exchange_breakdown:
                    exchange_breakdown[exchange] = {'count': 0, 'volume_sol': 0}
                exchange_breakdown[exchange]['count'] += 1
                exchange_breakdown[exchange]['volume_sol'] += tx.amount_sol
            
            # Calculate averages
            avg_transaction_size = total_volume_sol / len(transactions)
            avg_confidence = sum(tx.confidence_score for tx in transactions) / len(transactions)
            
            return {
                'total_transactions': len(transactions),
                'total_volume_sol': total_volume_sol,
                'total_volume_usd': total_volume_usd,
                'exchange_transactions': len(exchange_transactions),
                'exchange_volume_sol': exchange_volume_sol,
                'exchange_breakdown': exchange_breakdown,
                'avg_transaction_size_sol': avg_transaction_size,
                'avg_confidence_score': avg_confidence,
                'largest_transaction_sol': max(tx.amount_sol for tx in transactions),
                'time_range_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Error calculating whale statistics: {e}")
            return {}
    
    def cleanup_old_data(self) -> int:
        """Clean up old whale data beyond retention period."""
        if self.retention_days <= 0:
            return 0
        
        try:
            cutoff_time = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            # Clean transaction files
            pattern = os.path.join(self.transactions_dir, "whale_tx_*.json")
            files = glob.glob(pattern)
            
            for file_path in files:
                try:
                    # Extract timestamp from filename
                    filename = os.path.basename(file_path)
                    timestamp_str = filename.split('_')[2] + '_' + filename.split('_')[3]
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old whale transaction files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def backup_data(self) -> bool:
        """Create backup of whale data."""
        if not self.backup_enabled:
            return True
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"whale_data_backup_{timestamp}.json"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            # Collect all data
            backup_data = {
                'backup_timestamp': timestamp,
                'transactions': [],
                'statistics': self.get_whale_statistics(24)
            }
            
            # Load recent transactions
            transactions = self.load_whale_transactions(24)
            for tx in transactions:
                backup_data['transactions'].append({
                    'signature': tx.signature,
                    'timestamp': tx.timestamp.isoformat(),
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'amount_sol': tx.amount_sol,
                    'amount_usd': tx.amount_usd,
                    'transaction_type': tx.transaction_type,
                    'is_exchange_related': tx.is_exchange_related,
                    'exchange_name': tx.exchange_name,
                    'confidence_score': tx.confidence_score,
                    'metadata': tx.metadata
                })
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Whale data backup created: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating whale data backup: {e}")
            return False
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of stored whale data."""
        try:
            # Count files
            tx_files = len(glob.glob(os.path.join(self.transactions_dir, "*.json")))
            backup_files = len(glob.glob(os.path.join(self.backups_dir, "*.json")))
            
            # Get disk usage
            total_size = 0
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            # Get recent statistics
            recent_stats = self.get_whale_statistics(24)
            
            return {
                'storage_summary': {
                    'transaction_files': tx_files,
                    'backup_files': backup_files,
                    'total_size_mb': total_size / (1024 * 1024),
                    'retention_days': self.retention_days
                },
                'recent_activity': recent_stats,
                'cache_size': len(self.transaction_cache),
                'directories': {
                    'transactions': self.transactions_dir,
                    'flows': self.flows_dir,
                    'signals': self.signals_dir,
                    'backups': self.backups_dir
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {}
