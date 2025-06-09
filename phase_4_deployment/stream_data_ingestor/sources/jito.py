#!/usr/bin/env python3
"""
Jito Data Source

This module provides a data source for Jito RPC and ShredStream.
"""

import os
import sys
import json
import time
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

# Install required packages
try:
    import websockets
    import httpx
    import base58
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "httpx", "base58"])
    import websockets
    import httpx
    import base58

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import stream data ingestor
from phase_4_deployment.stream_data_ingestor.client import StreamDataIngestor, StreamType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JitoDataSource:
    """Data source for Jito RPC and ShredStream."""
    
    def __init__(
        self,
        rpc_url: str = "https://mainnet.block.jito.io",
        shredstream_url: str = "wss://mainnet.shredstream.jito.io/stream",
        keypair_path: str = "",
    ):
        """
        Initialize the Jito data source.
        
        Args:
            rpc_url: Jito RPC URL
            shredstream_url: Jito ShredStream URL
            keypair_path: Path to keypair file for authentication
        """
        self.rpc_url = rpc_url
        self.shredstream_url = shredstream_url
        self.keypair_path = keypair_path
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        
        # Initialize ShredStream
        self.shredstream = None
        
        # Initialize callbacks
        self.transaction_callbacks = []
        
        # Load keypair
        self.keypair = self._load_keypair()
        
        logger.info("Initialized Jito data source")
    
    async def subscribe_to_transaction_updates(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Subscribe to transaction updates.
        
        Args:
            callback: Callback function that takes transaction data and returns None
        """
        self.transaction_callbacks.append(callback)
        
        # Initialize ShredStream if not already initialized
        if not self.shredstream:
            # Prepare authentication
            auth_headers = {}
            if self.keypair:
                # Sign a message with the keypair
                message = f"jito-shredstream:{int(time.time())}"
                signature = self._sign_message(message)
                
                # Add authentication headers
                auth_headers = {
                    "X-Jito-Pubkey": self.keypair.get("public_key", ""),
                    "X-Jito-Signature": signature,
                    "X-Jito-Timestamp": str(int(time.time())),
                }
            
            self.shredstream = StreamDataIngestor(
                stream_type=StreamType.JITO_SHREDSTREAM,
                stream_url=self.shredstream_url,
                subscription_params={
                    "params": [
                        {
                            "type": "subscribe",
                            "filters": [
                                {"type": "tx"}
                            ]
                        }
                    ]
                },
                max_reconnect_attempts=10,
                reconnect_delay=1.0,
                buffer_size=1000,
            )
            
            # Register callback for transaction updates
            self.shredstream.on_message(self._handle_transaction_update)
            
            # Start the ShredStream
            await self.shredstream.start()
            
            logger.info("Subscribed to transaction updates")
    
    async def get_tip_accounts(self) -> Dict[str, Any]:
        """
        Get tip accounts.
        
        Returns:
            Dict[str, Any]: Tip accounts
        """
        try:
            # Prepare RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "jito_getTipAccounts",
                "params": []
            }
            
            # Send request
            response = await self.http_client.post(
                self.rpc_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "error" in response_data:
                logger.error(f"Error getting tip accounts: {response_data['error']}")
                return {}
            
            return response_data.get("result", {})
        except Exception as e:
            logger.error(f"Error getting tip accounts: {str(e)}")
            return {}
    
    async def get_bundle_fee(self) -> Dict[str, Any]:
        """
        Get bundle fee.
        
        Returns:
            Dict[str, Any]: Bundle fee
        """
        try:
            # Prepare RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "jito_getBundleFee",
                "params": []
            }
            
            # Send request
            response = await self.http_client.post(
                self.rpc_url,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "error" in response_data:
                logger.error(f"Error getting bundle fee: {response_data['error']}")
                return {}
            
            return response_data.get("result", {})
        except Exception as e:
            logger.error(f"Error getting bundle fee: {str(e)}")
            return {}
    
    async def close(self) -> None:
        """Close the data source."""
        logger.info("Closing Jito data source")
        
        # Stop ShredStream
        if self.shredstream:
            await self.shredstream.stop()
            self.shredstream = None
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("Jito data source closed")
    
    def _load_keypair(self) -> Dict[str, str]:
        """
        Load keypair from file.
        
        Returns:
            Dict[str, str]: Keypair with public_key and private_key
        """
        if not self.keypair_path or not os.path.exists(self.keypair_path):
            logger.warning(f"Keypair file not found: {self.keypair_path}")
            return {}
        
        try:
            with open(self.keypair_path, "r") as f:
                keypair_data = json.load(f)
            
            # Convert to base58
            private_key = base58.b58encode(bytes(keypair_data)).decode("utf-8")
            
            # Extract public key (last 32 bytes)
            public_key = base58.b58encode(bytes(keypair_data[-32:])).decode("utf-8")
            
            return {
                "public_key": public_key,
                "private_key": private_key,
            }
        except Exception as e:
            logger.error(f"Error loading keypair: {str(e)}")
            return {}
    
    def _sign_message(self, message: str) -> str:
        """
        Sign a message with the keypair.
        
        Args:
            message: Message to sign
            
        Returns:
            str: Base58-encoded signature
        """
        if not self.keypair:
            logger.warning("No keypair available for signing")
            return ""
        
        try:
            # This is a placeholder for actual signing logic
            # In a real implementation, you would use the Solana SDK to sign the message
            # For now, we'll just return a dummy signature
            return "dummysignature"
        except Exception as e:
            logger.error(f"Error signing message: {str(e)}")
            return ""
    
    async def _handle_transaction_update(self, message: Dict[str, Any]) -> None:
        """
        Handle transaction update.
        
        Args:
            message: Transaction update message
        """
        try:
            # Extract transaction data
            transaction_data = message.get("params", {}).get("result", {})
            
            if not transaction_data:
                return
            
            # Call callbacks
            for callback in self.transaction_callbacks:
                await callback(transaction_data)
        except Exception as e:
            logger.error(f"Error handling transaction update: {str(e)}")

async def main():
    """Main function for testing."""
    # Create Jito data source
    jito = JitoDataSource()
    
    # Define callback for transaction updates
    async def handle_transaction_update(transaction_data: Dict[str, Any]) -> None:
        print(f"Received transaction update: {json.dumps(transaction_data, indent=2)}")
    
    try:
        # Subscribe to transaction updates
        await jito.subscribe_to_transaction_updates(handle_transaction_update)
        
        # Get tip accounts
        tip_accounts = await jito.get_tip_accounts()
        print(f"Tip accounts: {json.dumps(tip_accounts, indent=2)}")
        
        # Get bundle fee
        bundle_fee = await jito.get_bundle_fee()
        print(f"Bundle fee: {json.dumps(bundle_fee, indent=2)}")
        
        # Run for 60 seconds
        print("Running for 60 seconds...")
        await asyncio.sleep(60)
    finally:
        # Close the data source
        await jito.close()

if __name__ == "__main__":
    asyncio.run(main())
