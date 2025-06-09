#!/usr/bin/env python3
"""
Example usage of the stream data ingestion client.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from client import StreamDataIngestor, StreamType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stream_data_example')

async def on_message(message: Dict[str, Any]) -> None:
    """
    Callback for when a message is received.
    
    Args:
        message: Message received from the stream
    """
    logger.info(f"Received message: {json.dumps(message, indent=2)[:200]}...")

async def on_connect() -> None:
    """Callback for when a connection is established."""
    logger.info("Connected to stream")

async def on_disconnect() -> None:
    """Callback for when a connection is closed."""
    logger.info("Disconnected from stream")

async def on_error(error: str) -> None:
    """
    Callback for when an error occurs.
    
    Args:
        error: Error message
    """
    logger.error(f"Error: {error}")

async def main() -> None:
    """Main function."""
    # Get API keys from environment variables
    liljito_api_key = os.environ.get("LILJITO_QUICKNODE_API_KEY")
    helius_api_key = os.environ.get("HELIUS_API_KEY")
    
    # Create a stream data ingestor for Lil' Jito QuickNode
    if liljito_api_key:
        logger.info("Creating Lil' Jito QuickNode stream data ingestor")
        liljito_ingestor = StreamDataIngestor(
            stream_type=StreamType.CUSTOM_WEBSOCKET,
            stream_url=f"wss://lil-jito.quiknode.pro/{liljito_api_key}/",
            api_key=liljito_api_key,
            subscription_params={
                "subscription_message": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "blockSubscribe",
                    "params": {
                        "commitment": "confirmed",
                        "encoding": "json",
                        "transactionDetails": "full",
                        "showRewards": False
                    }
                },
                "expect_confirmation": True
            }
        )
        
        # Register callbacks
        liljito_ingestor.on_message(on_message)
        liljito_ingestor.on_connect(on_connect)
        liljito_ingestor.on_disconnect(on_disconnect)
        liljito_ingestor.on_error(on_error)
        
        # Start consuming data
        await liljito_ingestor.start()
        
        # Wait for some messages
        try:
            await asyncio.sleep(30)  # Run for 30 seconds
        except asyncio.CancelledError:
            pass
        
        # Stop consuming data
        await liljito_ingestor.stop()
    else:
        logger.warning("LILJITO_QUICKNODE_API_KEY not set, skipping Lil' Jito QuickNode example")
    
    # Create a stream data ingestor for Helius
    if helius_api_key:
        logger.info("Creating Helius stream data ingestor")
        helius_ingestor = StreamDataIngestor(
            stream_type=StreamType.HELIUS_WEBHOOK,
            stream_url=f"https://api.helius-rpc.com/{helius_api_key}/v0/addresses/J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz/transactions",
            api_key=helius_api_key,
            subscription_params={
                "poll_interval": 2.0  # Poll every 2 seconds
            }
        )
        
        # Register callbacks
        helius_ingestor.on_message(on_message)
        helius_ingestor.on_connect(on_connect)
        helius_ingestor.on_disconnect(on_disconnect)
        helius_ingestor.on_error(on_error)
        
        # Start consuming data
        await helius_ingestor.start()
        
        # Wait for some messages
        try:
            await asyncio.sleep(30)  # Run for 30 seconds
        except asyncio.CancelledError:
            pass
        
        # Stop consuming data
        await helius_ingestor.stop()
    else:
        logger.warning("HELIUS_API_KEY not set, skipping Helius example")

if __name__ == "__main__":
    asyncio.run(main())
