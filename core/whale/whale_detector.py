#!/usr/bin/env python3
"""
Whale Detector - Core whale transaction detection system
Monitors Solana blockchain for large transactions and whale activity.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import httpx
from dataclasses import dataclass
import base58

logger = logging.getLogger(__name__)

@dataclass
class WhaleTransaction:
    """Represents a detected whale transaction."""
    signature: str
    timestamp: datetime
    from_address: str
    to_address: str
    amount_sol: float
    amount_usd: float
    transaction_type: str  # 'transfer', 'swap', 'stake', 'unstake'
    is_exchange_related: bool
    exchange_name: Optional[str]
    confidence_score: float
    metadata: Dict[str, Any]

class WhaleDetector:
    """Detects and analyzes whale transactions on Solana."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize whale detector."""
        self.config = config
        self.whale_config = config.get('whale_detection', {})
        
        # Detection thresholds
        self.min_whale_amount_sol = self.whale_config.get('min_whale_amount_sol', 100.0)
        self.min_whale_amount_usd = self.whale_config.get('min_whale_amount_usd', 18000.0)
        
        # RPC configuration
        self.rpc_url = config.get('solana', {}).get('rpc_url', '')
        self.backup_rpc_url = config.get('solana', {}).get('fallback_rpc_url', '')
        
        # HTTP client for RPC calls
        self.http_client = None
        
        # Known exchange addresses (major Solana exchanges)
        self.exchange_addresses = self._load_exchange_addresses()
        
        # Whale wallet addresses (known large holders)
        self.whale_wallets = self._load_whale_wallets()
        
        # Detection state
        self.last_processed_slot = 0
        self.detected_transactions = []
        self.is_monitoring = False
        
        # Performance metrics
        self.metrics = {
            'transactions_processed': 0,
            'whales_detected': 0,
            'api_calls': 0,
            'errors': 0,
            'last_detection': None
        }
        
        logger.info(f"Whale detector initialized with {self.min_whale_amount_sol} SOL threshold")
    
    async def initialize(self) -> bool:
        """Initialize the whale detector."""
        try:
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # Test RPC connection
            test_result = await self._test_rpc_connection()
            if not test_result:
                logger.error("Failed to connect to Solana RPC")
                return False
            
            # Load latest slot
            self.last_processed_slot = await self._get_current_slot()
            
            logger.info(f"✅ Whale detector initialized at slot {self.last_processed_slot}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing whale detector: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start continuous whale monitoring."""
        if self.is_monitoring:
            logger.warning("Whale monitoring already active")
            return
        
        self.is_monitoring = True
        logger.info("🐋 Starting whale transaction monitoring...")
        
        try:
            while self.is_monitoring:
                await self._monitor_cycle()
                await asyncio.sleep(self.whale_config.get('monitoring_interval', 10))
                
        except Exception as e:
            logger.error(f"Error in whale monitoring: {e}")
        finally:
            self.is_monitoring = False
    
    def stop_monitoring(self) -> None:
        """Stop whale monitoring."""
        self.is_monitoring = False
        logger.info("🛑 Whale monitoring stopped")
    
    async def _monitor_cycle(self) -> None:
        """Execute one monitoring cycle."""
        try:
            # Get recent transactions
            recent_transactions = await self._get_recent_transactions()
            
            # Process each transaction
            for tx in recent_transactions:
                whale_tx = await self._analyze_transaction(tx)
                if whale_tx:
                    self.detected_transactions.append(whale_tx)
                    self.metrics['whales_detected'] += 1
                    self.metrics['last_detection'] = datetime.now()
                    
                    logger.info(f"🐋 Whale detected: {whale_tx.amount_sol:.2f} SOL (${whale_tx.amount_usd:.0f})")
                    
                    # Save whale transaction
                    await self._save_whale_transaction(whale_tx)
                
                self.metrics['transactions_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            self.metrics['errors'] += 1
    
    async def _get_recent_transactions(self) -> List[Dict[str, Any]]:
        """Get recent transactions from Solana RPC."""
        try:
            # Get current slot
            current_slot = await self._get_current_slot()
            
            # Get block data for recent slots
            transactions = []
            slots_to_check = min(5, current_slot - self.last_processed_slot)
            
            for i in range(slots_to_check):
                slot = current_slot - i
                block_data = await self._get_block_data(slot)
                
                if block_data and 'transactions' in block_data:
                    for tx in block_data['transactions']:
                        if tx and 'transaction' in tx:
                            transactions.append(tx)
            
            self.last_processed_slot = current_slot
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []
    
    async def _analyze_transaction(self, tx_data: Dict[str, Any]) -> Optional[WhaleTransaction]:
        """Analyze a transaction to determine if it's a whale transaction."""
        try:
            transaction = tx_data.get('transaction', {})
            meta = tx_data.get('meta', {})
            
            # Skip failed transactions
            if meta.get('err'):
                return None
            
            # Analyze pre/post balances for SOL transfers
            pre_balances = meta.get('preBalances', [])
            post_balances = meta.get('postBalances', [])
            
            if len(pre_balances) != len(post_balances):
                return None
            
            # Find largest balance change
            max_change = 0
            from_idx = -1
            to_idx = -1
            
            for i in range(len(pre_balances)):
                balance_change = abs(post_balances[i] - pre_balances[i])
                if balance_change > max_change:
                    max_change = balance_change
                    if post_balances[i] > pre_balances[i]:
                        to_idx = i
                    else:
                        from_idx = i
            
            # Convert lamports to SOL
            amount_sol = max_change / 1e9
            
            # Check if it meets whale threshold
            if amount_sol < self.min_whale_amount_sol:
                return None
            
            # Get account addresses
            account_keys = transaction.get('message', {}).get('accountKeys', [])
            
            from_address = account_keys[from_idx] if from_idx >= 0 and from_idx < len(account_keys) else 'unknown'
            to_address = account_keys[to_idx] if to_idx >= 0 and to_idx < len(account_keys) else 'unknown'
            
            # Calculate USD value (approximate)
            amount_usd = amount_sol * 180.0  # Approximate SOL price
            
            # Check if exchange-related
            is_exchange_related = self._is_exchange_address(from_address) or self._is_exchange_address(to_address)
            exchange_name = self._get_exchange_name(from_address) or self._get_exchange_name(to_address)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(amount_sol, from_address, to_address, is_exchange_related)
            
            # Create whale transaction
            whale_tx = WhaleTransaction(
                signature=tx_data.get('transaction', {}).get('signatures', ['unknown'])[0],
                timestamp=datetime.now(),
                from_address=from_address,
                to_address=to_address,
                amount_sol=amount_sol,
                amount_usd=amount_usd,
                transaction_type='transfer',
                is_exchange_related=is_exchange_related,
                exchange_name=exchange_name,
                confidence_score=confidence_score,
                metadata={
                    'slot': tx_data.get('slot'),
                    'block_time': tx_data.get('blockTime'),
                    'fee': meta.get('fee', 0),
                    'compute_units_consumed': meta.get('computeUnitsConsumed', 0)
                }
            )
            
            return whale_tx
            
        except Exception as e:
            logger.error(f"Error analyzing transaction: {e}")
            return None
    
    def _calculate_confidence_score(self, amount_sol: float, from_addr: str, to_addr: str, is_exchange: bool) -> float:
        """Calculate confidence score for whale transaction."""
        score = 0.5  # Base score
        
        # Amount-based scoring
        if amount_sol > 1000:
            score += 0.3
        elif amount_sol > 500:
            score += 0.2
        elif amount_sol > 200:
            score += 0.1
        
        # Known whale wallet bonus
        if from_addr in self.whale_wallets or to_addr in self.whale_wallets:
            score += 0.2
        
        # Exchange-related bonus/penalty
        if is_exchange:
            score += 0.1  # Exchange flows are significant
        
        return min(1.0, score)
    
    def _is_exchange_address(self, address: str) -> bool:
        """Check if address belongs to a known exchange."""
        return address in self.exchange_addresses
    
    def _get_exchange_name(self, address: str) -> Optional[str]:
        """Get exchange name for address."""
        return self.exchange_addresses.get(address)
    
    def _load_exchange_addresses(self) -> Dict[str, str]:
        """Load known exchange addresses."""
        try:
            exchange_file = 'config/whale_wallets.json'
            if os.path.exists(exchange_file):
                with open(exchange_file, 'r') as f:
                    data = json.load(f)
                    return data.get('exchanges', {})
        except Exception as e:
            logger.warning(f"Could not load exchange addresses: {e}")
        
        # Default exchange addresses (major Solana exchanges)
        return {
            # Binance
            '5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9': 'Binance',
            # FTX (historical)
            '2ojv9BAiHUrvsm9gxDe7fJSzbNZSJcxZvf8dqmWGHG8S': 'FTX',
            # Coinbase
            'GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE': 'Coinbase',
            # Kraken
            'AC5RDfQFmDS1deWZos921JfqscXdByf8BKHs5ACWjtW2': 'Kraken'
        }
    
    def _load_whale_wallets(self) -> Set[str]:
        """Load known whale wallet addresses."""
        try:
            whale_file = 'config/whale_wallets.json'
            if os.path.exists(whale_file):
                with open(whale_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('whales', []))
        except Exception as e:
            logger.warning(f"Could not load whale wallets: {e}")
        
        # Default known whale addresses
        return {
            # Solana Foundation
            'GThUX1Atko4tqhN2NaiTazWSeFWMuiUiswQztfEHxHUD',
            # Major validators and known large holders
            'J1S9H3QjnRtBbbuD4HjPV6RpRhwuk4zKbxsnCHuTgh9w',
            'DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh'
        }
    
    async def _test_rpc_connection(self) -> bool:
        """Test RPC connection."""
        try:
            response = await self._rpc_call('getHealth')
            return response is not None
        except:
            return False
    
    async def _get_current_slot(self) -> int:
        """Get current slot number."""
        try:
            response = await self._rpc_call('getSlot')
            return response if response else 0
        except:
            return 0
    
    async def _get_block_data(self, slot: int) -> Optional[Dict[str, Any]]:
        """Get block data for a specific slot."""
        try:
            response = await self._rpc_call('getBlock', [slot, {"encoding": "json", "maxSupportedTransactionVersion": 0}])
            return response
        except:
            return None
    
    async def _rpc_call(self, method: str, params: List[Any] = None) -> Any:
        """Make RPC call to Solana node."""
        if not self.http_client:
            return None
        
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params or []
        }
        
        try:
            response = await self.http_client.post(self.rpc_url, json=payload)
            self.metrics['api_calls'] += 1
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
            else:
                logger.warning(f"RPC call failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"RPC call error: {e}")
            return None
    
    async def _save_whale_transaction(self, whale_tx: WhaleTransaction) -> None:
        """Save whale transaction to disk."""
        try:
            os.makedirs('output/whale_data/transactions', exist_ok=True)
            
            filename = f"whale_tx_{whale_tx.timestamp.strftime('%Y%m%d_%H%M%S')}_{whale_tx.signature[:8]}.json"
            filepath = os.path.join('output/whale_data/transactions', filename)
            
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
                
        except Exception as e:
            logger.error(f"Error saving whale transaction: {e}")
    
    def get_recent_whales(self, hours: int = 1) -> List[WhaleTransaction]:
        """Get whale transactions from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [tx for tx in self.detected_transactions if tx.timestamp > cutoff_time]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get whale detector metrics."""
        return {
            **self.metrics,
            'is_monitoring': self.is_monitoring,
            'last_processed_slot': self.last_processed_slot,
            'total_detected': len(self.detected_transactions),
            'exchange_addresses_loaded': len(self.exchange_addresses),
            'whale_wallets_loaded': len(self.whale_wallets)
        }
    
    async def close(self) -> None:
        """Close whale detector and cleanup resources."""
        self.stop_monitoring()
        
        if self.http_client:
            await self.http_client.aclose()
        
        logger.info("Whale detector closed")
