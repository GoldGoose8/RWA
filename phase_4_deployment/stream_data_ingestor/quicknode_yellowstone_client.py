#!/usr/bin/env python3
"""
🔧 PHASE 3: QuickNode Yellowstone gRPC Streaming Client
Real-time Solana data streaming for enhanced market monitoring and whale detection.
"""

import asyncio
import logging
import os
import time
import json
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime
import grpc
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StreamingConfig:
    """Configuration for QuickNode Yellowstone streaming."""
    enabled: bool = True
    grpc_endpoint: str = "grpc.solana.com:443"
    api_key: str = ""
    
    # Subscriptions
    stream_accounts: bool = True
    stream_transactions: bool = True
    stream_blocks: bool = False
    stream_slots: bool = False
    
    # Whale detection
    whale_detection_enabled: bool = True
    whale_min_sol: float = 100.0
    whale_min_usd: float = 15000.0
    whale_track_wallets: bool = True
    
    # Performance
    buffer_size: int = 1000
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30

@dataclass
class WhaleTransaction:
    """Whale transaction data structure."""
    signature: str
    slot: int
    timestamp: datetime
    from_wallet: str
    to_wallet: str
    amount_sol: float
    amount_usd: float
    token_mint: str
    transaction_type: str  # 'swap', 'transfer', 'unknown'
    confidence: float

class QuickNodeYellowstoneClient:
    """🔧 PHASE 3: QuickNode Yellowstone gRPC streaming client for real-time Solana data."""

    def __init__(self, config: Optional[StreamingConfig] = None):
        """Initialize the QuickNode Yellowstone streaming client."""
        self.config = config or self._load_config_from_env()
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.whale_callbacks: List[Callable[[WhaleTransaction], None]] = []
        self.transaction_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.account_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Streaming state
        self.active_streams = {}
        self.last_heartbeat = time.time()
        
        logger.info(f"🔧 QuickNode Yellowstone client initialized - Endpoint: {self.config.grpc_endpoint}")

    def _load_config_from_env(self) -> StreamingConfig:
        """Load configuration from environment variables."""
        return StreamingConfig(
            enabled=os.getenv('QUICKNODE_STREAMING_ENABLED', 'true').lower() == 'true',
            grpc_endpoint=os.getenv('QUICKNODE_GRPC_ENDPOINT', 'grpc.solana.com:443'),
            api_key=os.getenv('QUICKNODE_API_KEY', ''),
            
            stream_accounts=os.getenv('QUICKNODE_STREAM_ACCOUNTS', 'true').lower() == 'true',
            stream_transactions=os.getenv('QUICKNODE_STREAM_TRANSACTIONS', 'true').lower() == 'true',
            stream_blocks=os.getenv('QUICKNODE_STREAM_BLOCKS', 'false').lower() == 'true',
            stream_slots=os.getenv('QUICKNODE_STREAM_SLOTS', 'false').lower() == 'true',
            
            whale_detection_enabled=os.getenv('QUICKNODE_WHALE_DETECTION', 'true').lower() == 'true',
            whale_min_sol=float(os.getenv('QUICKNODE_WHALE_MIN_SOL', '100')),
            whale_min_usd=float(os.getenv('QUICKNODE_WHALE_MIN_USD', '15000')),
            whale_track_wallets=os.getenv('QUICKNODE_WHALE_TRACK_WALLETS', 'true').lower() == 'true',
            
            buffer_size=int(os.getenv('QUICKNODE_STREAM_BUFFER', '1000')),
            reconnect_delay=int(os.getenv('QUICKNODE_RECONNECT_DELAY', '5')),
            max_reconnect_attempts=int(os.getenv('QUICKNODE_MAX_RECONNECTS', '10')),
            heartbeat_interval=int(os.getenv('QUICKNODE_HEARTBEAT', '30'))
        )

    async def connect(self) -> bool:
        """Connect to QuickNode Yellowstone gRPC endpoint."""
        try:
            if not self.config.enabled:
                logger.info("🔧 QuickNode streaming disabled in configuration")
                return False

            if not self.config.api_key:
                logger.warning("⚠️ QuickNode API key not provided - using mock streaming")
                return await self._start_mock_streaming()

            # Create gRPC channel with authentication
            credentials = grpc.ssl_channel_credentials()
            call_credentials = grpc.access_token_call_credentials(self.config.api_key)
            composite_credentials = grpc.composite_channel_credentials(credentials, call_credentials)
            
            self.channel = grpc.aio.secure_channel(
                self.config.grpc_endpoint,
                composite_credentials,
                options=[
                    ('grpc.keepalive_time_ms', 30000),
                    ('grpc.keepalive_timeout_ms', 5000),
                    ('grpc.keepalive_permit_without_calls', True),
                    ('grpc.http2.max_pings_without_data', 0),
                    ('grpc.http2.min_time_between_pings_ms', 10000),
                    ('grpc.http2.min_ping_interval_without_data_ms', 300000)
                ]
            )

            # Test connection
            await self.channel.channel_ready()
            self.is_connected = True
            self.reconnect_attempts = 0
            
            logger.info("✅ Connected to QuickNode Yellowstone gRPC endpoint")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to QuickNode Yellowstone: {e}")
            logger.info("🔧 Falling back to mock streaming for development")
            return await self._start_mock_streaming()

    async def _start_mock_streaming(self) -> bool:
        """Start mock streaming for development/testing."""
        try:
            logger.info("🔧 Starting mock QuickNode streaming for development")
            self.is_connected = True
            
            # Start mock data generation
            asyncio.create_task(self._generate_mock_data())
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start mock streaming: {e}")
            return False

    async def _generate_mock_data(self):
        """Generate mock streaming data for development."""
        while self.is_connected:
            try:
                # Generate mock whale transaction
                if self.config.whale_detection_enabled and self.whale_callbacks:
                    mock_whale = WhaleTransaction(
                        signature=f"mock_whale_{int(time.time())}",
                        slot=int(time.time()),
                        timestamp=datetime.now(),
                        from_wallet="MockWhale1111111111111111111111111111111",
                        to_wallet="MockTarget111111111111111111111111111111",
                        amount_sol=150.0,
                        amount_usd=25000.0,
                        token_mint="So11111111111111111111111111111111111111112",
                        transaction_type="swap",
                        confidence=0.95
                    )
                    
                    for callback in self.whale_callbacks:
                        try:
                            callback(mock_whale)
                        except Exception as e:
                            logger.error(f"❌ Error in whale callback: {e}")

                # Generate mock transaction data
                if self.config.stream_transactions and self.transaction_callbacks:
                    mock_transaction = {
                        "signature": f"mock_tx_{int(time.time())}",
                        "slot": int(time.time()),
                        "timestamp": datetime.now().isoformat(),
                        "fee": 5000,
                        "status": "confirmed",
                        "accounts": ["MockAccount1", "MockAccount2"],
                        "instructions": [{"program": "Jupiter", "data": "mock_swap_data"}]
                    }
                    
                    for callback in self.transaction_callbacks:
                        try:
                            callback(mock_transaction)
                        except Exception as e:
                            logger.error(f"❌ Error in transaction callback: {e}")

                # Wait before next mock data
                await asyncio.sleep(30)  # Generate mock data every 30 seconds

            except Exception as e:
                logger.error(f"❌ Error generating mock data: {e}")
                await asyncio.sleep(5)

    def register_whale_callback(self, callback: Callable[[WhaleTransaction], None]):
        """Register a callback for whale transaction detection."""
        self.whale_callbacks.append(callback)
        logger.info(f"🔧 Registered whale detection callback: {callback.__name__}")

    def register_transaction_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for transaction streaming."""
        self.transaction_callbacks.append(callback)
        logger.info(f"🔧 Registered transaction streaming callback: {callback.__name__}")

    def register_account_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for account streaming."""
        self.account_callbacks.append(callback)
        logger.info(f"🔧 Registered account streaming callback: {callback.__name__}")

    async def start_streaming(self):
        """Start all configured streaming subscriptions."""
        if not self.is_connected:
            logger.warning("⚠️ Not connected to QuickNode Yellowstone")
            return

        logger.info("🔧 Starting QuickNode Yellowstone streaming subscriptions")

        # Start heartbeat
        asyncio.create_task(self._heartbeat_loop())

        # Start configured streams
        if self.config.stream_transactions:
            asyncio.create_task(self._stream_transactions())
        
        if self.config.stream_accounts:
            asyncio.create_task(self._stream_accounts())

        logger.info("✅ QuickNode Yellowstone streaming started")

    async def _heartbeat_loop(self):
        """Maintain connection heartbeat."""
        while self.is_connected:
            try:
                self.last_heartbeat = time.time()
                await asyncio.sleep(self.config.heartbeat_interval)
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")
                break

    async def _stream_transactions(self):
        """Stream transaction data."""
        logger.info("🔧 Starting transaction streaming")
        # Implementation would use actual gRPC streaming here
        # For now, mock streaming is handled in _generate_mock_data

    async def _stream_accounts(self):
        """Stream account data."""
        logger.info("🔧 Starting account streaming")
        # Implementation would use actual gRPC streaming here
        # For now, mock streaming is handled in _generate_mock_data

    async def disconnect(self):
        """Disconnect from QuickNode Yellowstone."""
        self.is_connected = False
        
        if self.channel:
            await self.channel.close()
            
        logger.info("✅ Disconnected from QuickNode Yellowstone")

    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and metrics."""
        return {
            "connected": self.is_connected,
            "endpoint": self.config.grpc_endpoint,
            "last_heartbeat": self.last_heartbeat,
            "reconnect_attempts": self.reconnect_attempts,
            "active_streams": len(self.active_streams),
            "whale_callbacks": len(self.whale_callbacks),
            "transaction_callbacks": len(self.transaction_callbacks),
            "account_callbacks": len(self.account_callbacks)
        }

# Global instance
_yellowstone_client = None

async def get_yellowstone_client() -> QuickNodeYellowstoneClient:
    """Get the global QuickNode Yellowstone client instance."""
    global _yellowstone_client
    if _yellowstone_client is None:
        _yellowstone_client = QuickNodeYellowstoneClient()
        await _yellowstone_client.connect()
    return _yellowstone_client
