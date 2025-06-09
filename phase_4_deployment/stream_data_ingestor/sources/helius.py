#!/usr/bin/env python3
"""
Helius Data Source

This module provides a data source for Helius API and WebSocket.
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
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "httpx"])
    import websockets
    import httpx

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

class HeliusDataSource:
    """Data source for Helius API and WebSocket."""
    
    def __init__(
        self,
        api_key: str,
        rpc_endpoint: str = "",
        ws_endpoint: str = "",
    ):
        """
        Initialize the Helius data source.
        
        Args:
            api_key: Helius API key
            rpc_endpoint: Helius RPC endpoint
            ws_endpoint: Helius WebSocket endpoint
        """
        self.api_key = api_key
        
        # Set default endpoints if not provided
        self.rpc_endpoint = rpc_endpoint or f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        self.ws_endpoint = ws_endpoint or f"wss://mainnet.helius-rpc.com/?api-key={api_key}"
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        
        # Initialize WebSocket stream
        self.account_stream = None
        self.transaction_stream = None
        
        # Initialize callbacks
        self.account_callbacks = []
        self.transaction_callbacks = []
        
        logger.info("Initialized Helius data source")
    
    async def subscribe_to_account_updates(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Subscribe to account updates.
        
        Args:
            callback: Callback function that takes account data and returns None
        """
        self.account_callbacks.append(callback)
        
        # Initialize account stream if not already initialized
        if not self.account_stream:
            self.account_stream = StreamDataIngestor(
                stream_type=StreamType.CUSTOM_WEBSOCKET,
                stream_url=self.ws_endpoint,
                api_key=self.api_key,
                subscription_params={
                    "subscription_message": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "accountSubscribe",
                        "params": [
                            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token program
                            {"encoding": "jsonParsed", "commitment": "confirmed"}
                        ]
                    },
                    "expect_confirmation": True
                },
                max_reconnect_attempts=10,
                reconnect_delay=1.0,
                buffer_size=1000,
            )
            
            # Register callback for account updates
            self.account_stream.on_message(self._handle_account_update)
            
            # Start the account stream
            await self.account_stream.start()
            
            logger.info("Subscribed to account updates")
    
    async def subscribe_to_transaction_updates(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Subscribe to transaction updates.
        
        Args:
            callback: Callback function that takes transaction data and returns None
        """
        self.transaction_callbacks.append(callback)
        
        # Initialize transaction stream if not already initialized
        if not self.transaction_stream:
            self.transaction_stream = StreamDataIngestor(
                stream_type=StreamType.CUSTOM_WEBSOCKET,
                stream_url=self.ws_endpoint,
                api_key=self.api_key,
                subscription_params={
                    "subscription_message": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "logsSubscribe",
                        "params": [
                            {"mentions": ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"]},
                            {"commitment": "confirmed"}
                        ]
                    },
                    "expect_confirmation": True
                },
                max_reconnect_attempts=10,
                reconnect_delay=1.0,
                buffer_size=1000,
            )
            
            # Register callback for transaction updates
            self.transaction_stream.on_message(self._handle_transaction_update)
            
            # Start the transaction stream
            await self.transaction_stream.start()
            
            logger.info("Subscribed to transaction updates")
    
    async def get_account_info(self, address: str) -> Dict[str, Any]:
        """
        Get account information.
        
        Args:
            address: Account address
            
        Returns:
            Dict[str, Any]: Account information
        """
        try:
            # Prepare RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    address,
                    {"encoding": "jsonParsed", "commitment": "confirmed"}
                ]
            }
            
            # Send request
            response = await self.http_client.post(
                self.rpc_endpoint,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "error" in response_data:
                logger.error(f"Error getting account info: {response_data['error']}")
                return {}
            
            return response_data.get("result", {})
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return {}
    
    async def get_transaction(self, signature: str) -> Dict[str, Any]:
        """
        Get transaction information.
        
        Args:
            signature: Transaction signature
            
        Returns:
            Dict[str, Any]: Transaction information
        """
        try:
            # Prepare RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                ]
            }
            
            # Send request
            response = await self.http_client.post(
                self.rpc_endpoint,
                json=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "error" in response_data:
                logger.error(f"Error getting transaction: {response_data['error']}")
                return {}
            
            return response_data.get("result", {})
        except Exception as e:
            logger.error(f"Error getting transaction: {str(e)}")
            return {}
    
    async def close(self) -> None:
        """Close the data source."""
        logger.info("Closing Helius data source")
        
        # Stop account stream
        if self.account_stream:
            await self.account_stream.stop()
            self.account_stream = None
        
        # Stop transaction stream
        if self.transaction_stream:
            await self.transaction_stream.stop()
            self.transaction_stream = None
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("Helius data source closed")
    
    async def _handle_account_update(self, message: Dict[str, Any]) -> None:
        """
        Handle account update.
        
        Args:
            message: Account update message
        """
        try:
            # Extract account data
            account_data = message.get("params", {}).get("result", {}).get("value", {})
            
            if not account_data:
                return
            
            # Call callbacks
            for callback in self.account_callbacks:
                await callback(account_data)
        except Exception as e:
            logger.error(f"Error handling account update: {str(e)}")
    
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
    # Create Helius data source
    helius = HeliusDataSource(
        api_key=os.environ.get("HELIUS_API_KEY", ""),
    )
    
    # Define callback for account updates
    async def handle_account_update(account_data: Dict[str, Any]) -> None:
        print(f"Received account update: {json.dumps(account_data, indent=2)}")
    
    # Define callback for transaction updates
    async def handle_transaction_update(transaction_data: Dict[str, Any]) -> None:
        print(f"Received transaction update: {json.dumps(transaction_data, indent=2)}")
    
    try:
        # Subscribe to account updates
        await helius.subscribe_to_account_updates(handle_account_update)
        
        # Subscribe to transaction updates
        await helius.subscribe_to_transaction_updates(handle_transaction_update)
        
        # Run for 60 seconds
        print("Running for 60 seconds...")
        await asyncio.sleep(60)
    finally:
        # Close the data source
        await helius.close()

if __name__ == "__main__":
    asyncio.run(main())
