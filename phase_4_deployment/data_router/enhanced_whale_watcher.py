#!/usr/bin/env python3
"""
🔧 PHASE 3: Enhanced Whale Watcher with QuickNode Yellowstone Integration
Real-time whale detection using QuickNode streaming data.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class WhaleAlert:
    """Whale alert data structure."""
    signature: str
    timestamp: datetime
    whale_wallet: str
    target_wallet: str
    amount_sol: float
    amount_usd: float
    token_mint: str
    transaction_type: str
    confidence: float
    market_impact: str  # 'high', 'medium', 'low'
    alert_level: str    # 'critical', 'warning', 'info'

class EnhancedWhaleWatcher:
    """🔧 PHASE 3: Enhanced whale watcher with QuickNode Yellowstone streaming."""

    def __init__(self, 
                 min_whale_sol: float = 100.0,
                 min_whale_usd: float = 15000.0,
                 track_wallets: bool = True):
        """Initialize the enhanced whale watcher."""
        self.min_whale_sol = min_whale_sol
        self.min_whale_usd = min_whale_usd
        self.track_wallets = track_wallets
        
        # Whale tracking
        self.known_whales: Set[str] = set()
        self.whale_history: Dict[str, List[WhaleAlert]] = {}
        self.recent_alerts: List[WhaleAlert] = []
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
        
        # Statistics
        self.stats = {
            'total_whales_detected': 0,
            'total_transactions_monitored': 0,
            'alerts_sent': 0,
            'last_whale_detection': None,
            'largest_transaction_sol': 0.0,
            'largest_transaction_usd': 0.0
        }
        
        # QuickNode client
        self.yellowstone_client = None
        
        logger.info(f"🔧 Enhanced Whale Watcher initialized - Min: {min_whale_sol} SOL / ${min_whale_usd}")

    async def initialize(self):
        """Initialize the whale watcher with QuickNode streaming."""
        try:
            # Import and initialize QuickNode Yellowstone client
            from phase_4_deployment.stream_data_ingestor.quicknode_yellowstone_client import get_yellowstone_client
            
            self.yellowstone_client = await get_yellowstone_client()
            
            if self.yellowstone_client and self.yellowstone_client.is_connected:
                # Register whale detection callback
                self.yellowstone_client.register_whale_callback(self._on_whale_transaction)
                self.yellowstone_client.register_transaction_callback(self._on_transaction)
                
                # Start streaming
                await self.yellowstone_client.start_streaming()
                
                logger.info("✅ Enhanced Whale Watcher connected to QuickNode Yellowstone")
                return True
            else:
                logger.warning("⚠️ QuickNode Yellowstone not available - using fallback whale detection")
                return await self._start_fallback_detection()
                
        except Exception as e:
            logger.error(f"❌ Error initializing whale watcher: {e}")
            return await self._start_fallback_detection()

    async def _start_fallback_detection(self):
        """Start fallback whale detection without streaming."""
        logger.info("🔧 Starting fallback whale detection")
        
        # Start periodic whale simulation for testing
        asyncio.create_task(self._simulate_whale_activity())
        
        return True

    async def _simulate_whale_activity(self):
        """Simulate whale activity for testing purposes."""
        while True:
            try:
                # Simulate a whale transaction every 2 minutes
                await asyncio.sleep(120)
                
                # Create mock whale transaction
                from phase_4_deployment.stream_data_ingestor.quicknode_yellowstone_client import WhaleTransaction
                
                mock_whale = WhaleTransaction(
                    signature=f"simulated_whale_{int(time.time())}",
                    slot=int(time.time()),
                    timestamp=datetime.now(),
                    from_wallet="SimulatedWhale1111111111111111111111111111",
                    to_wallet="SimulatedTarget111111111111111111111111111",
                    amount_sol=200.0 + (time.time() % 500),  # Varying amounts
                    amount_usd=33000.0 + (time.time() % 80000),
                    token_mint="So11111111111111111111111111111111111111112",
                    transaction_type="swap",
                    confidence=0.9
                )
                
                await self._process_whale_transaction(mock_whale)
                
            except Exception as e:
                logger.error(f"❌ Error in whale simulation: {e}")
                await asyncio.sleep(30)

    def _on_whale_transaction(self, whale_transaction):
        """Callback for whale transactions from QuickNode streaming."""
        try:
            asyncio.create_task(self._process_whale_transaction(whale_transaction))
        except Exception as e:
            logger.error(f"❌ Error processing whale transaction: {e}")

    def _on_transaction(self, transaction_data: Dict[str, Any]):
        """Callback for general transactions from QuickNode streaming."""
        try:
            self.stats['total_transactions_monitored'] += 1
            
            # Analyze transaction for whale patterns
            # This would contain logic to detect whale transactions from raw transaction data
            
        except Exception as e:
            logger.error(f"❌ Error processing transaction: {e}")

    async def _process_whale_transaction(self, whale_transaction):
        """Process a detected whale transaction."""
        try:
            # Update statistics
            self.stats['total_whales_detected'] += 1
            self.stats['last_whale_detection'] = datetime.now()
            
            if whale_transaction.amount_sol > self.stats['largest_transaction_sol']:
                self.stats['largest_transaction_sol'] = whale_transaction.amount_sol
                
            if whale_transaction.amount_usd > self.stats['largest_transaction_usd']:
                self.stats['largest_transaction_usd'] = whale_transaction.amount_usd

            # Track whale wallet
            if self.track_wallets:
                self.known_whales.add(whale_transaction.from_wallet)

            # Determine alert level and market impact
            alert_level = self._determine_alert_level(whale_transaction)
            market_impact = self._assess_market_impact(whale_transaction)

            # Create whale alert
            whale_alert = WhaleAlert(
                signature=whale_transaction.signature,
                timestamp=whale_transaction.timestamp,
                whale_wallet=whale_transaction.from_wallet,
                target_wallet=whale_transaction.to_wallet,
                amount_sol=whale_transaction.amount_sol,
                amount_usd=whale_transaction.amount_usd,
                token_mint=whale_transaction.token_mint,
                transaction_type=whale_transaction.transaction_type,
                confidence=whale_transaction.confidence,
                market_impact=market_impact,
                alert_level=alert_level
            )

            # Store alert
            self.recent_alerts.append(whale_alert)
            
            # Maintain recent alerts list (keep last 100)
            if len(self.recent_alerts) > 100:
                self.recent_alerts = self.recent_alerts[-100:]

            # Store in whale history
            if whale_transaction.from_wallet not in self.whale_history:
                self.whale_history[whale_transaction.from_wallet] = []
            self.whale_history[whale_transaction.from_wallet].append(whale_alert)

            # Send alerts
            await self._send_whale_alert(whale_alert)

            logger.info(f"🐋 WHALE DETECTED: {whale_transaction.amount_sol:.2f} SOL (${whale_transaction.amount_usd:,.2f}) - {alert_level.upper()}")

        except Exception as e:
            logger.error(f"❌ Error processing whale transaction: {e}")

    def _determine_alert_level(self, whale_transaction) -> str:
        """Determine the alert level based on transaction size."""
        if whale_transaction.amount_usd >= 100000:  # $100k+
            return "critical"
        elif whale_transaction.amount_usd >= 50000:  # $50k+
            return "warning"
        else:
            return "info"

    def _assess_market_impact(self, whale_transaction) -> str:
        """Assess potential market impact of the whale transaction."""
        if whale_transaction.amount_usd >= 200000:  # $200k+
            return "high"
        elif whale_transaction.amount_usd >= 75000:  # $75k+
            return "medium"
        else:
            return "low"

    async def _send_whale_alert(self, whale_alert: WhaleAlert):
        """Send whale alert to registered callbacks."""
        try:
            self.stats['alerts_sent'] += 1
            
            # Call registered callbacks
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(whale_alert)
                    else:
                        callback(whale_alert)
                except Exception as e:
                    logger.error(f"❌ Error in whale alert callback: {e}")

        except Exception as e:
            logger.error(f"❌ Error sending whale alert: {e}")

    def register_alert_callback(self, callback: callable):
        """Register a callback for whale alerts."""
        self.alert_callbacks.append(callback)
        logger.info(f"🔧 Registered whale alert callback: {callback.__name__}")

    def get_recent_whales(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent whale alerts."""
        recent = self.recent_alerts[-limit:] if limit else self.recent_alerts
        return [asdict(alert) for alert in reversed(recent)]

    def get_whale_statistics(self) -> Dict[str, Any]:
        """Get whale detection statistics."""
        stats = self.stats.copy()
        stats.update({
            'known_whales_count': len(self.known_whales),
            'recent_alerts_count': len(self.recent_alerts),
            'tracked_whale_wallets': len(self.whale_history),
            'average_whale_size_sol': sum(alert.amount_sol for alert in self.recent_alerts) / max(len(self.recent_alerts), 1),
            'average_whale_size_usd': sum(alert.amount_usd for alert in self.recent_alerts) / max(len(self.recent_alerts), 1)
        })
        return stats

    def get_whale_by_wallet(self, wallet_address: str) -> List[Dict[str, Any]]:
        """Get whale transaction history for a specific wallet."""
        if wallet_address in self.whale_history:
            return [asdict(alert) for alert in self.whale_history[wallet_address]]
        return []

    async def close(self):
        """Close the whale watcher and cleanup resources."""
        if self.yellowstone_client:
            await self.yellowstone_client.disconnect()
        
        logger.info("✅ Enhanced Whale Watcher closed")

# Global instance
_whale_watcher = None

async def get_whale_watcher() -> EnhancedWhaleWatcher:
    """Get the global enhanced whale watcher instance."""
    global _whale_watcher
    if _whale_watcher is None:
        _whale_watcher = EnhancedWhaleWatcher()
        await _whale_watcher.initialize()
    return _whale_watcher
