#!/usr/bin/env python3
"""
Test script for the stream data ingestor client.
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
logger = logging.getLogger('test_client')

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

async def test_liljito_stream() -> None:
    """Test the Lil' Jito stream."""
    # Get API key from environment variable
    api_key = os.environ.get("LILJITO_QUICKNODE_API_KEY")
    if not api_key:
        logger.error("LILJITO_QUICKNODE_API_KEY environment variable not set")
        return
    
    # Create a stream data ingestor for Lil' Jito
    ingestor = StreamDataIngestor(
        stream_type=StreamType.CUSTOM_WEBSOCKET,
        stream_url=f"wss://lil-jito.quiknode.pro/{api_key}/",
        api_key=api_key,
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
    ingestor.on_message(on_message)
    ingestor.on_connect(on_connect)
    ingestor.on_disconnect(on_disconnect)
    ingestor.on_error(on_error)
    
    # Start consuming data
    await ingestor.start()
    
    try:
        # Run for 30 seconds
        logger.info("Running for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get metrics
        metrics = ingestor.get_metrics()
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
    finally:
        # Stop consuming data
        await ingestor.stop()

async def test_helius_stream() -> None:
    """Test the Helius stream."""
    # Get API key from environment variable
    api_key = os.environ.get("HELIUS_API_KEY")
    if not api_key:
        logger.error("HELIUS_API_KEY environment variable not set")
        return
    
    # Create a stream data ingestor for Helius
    ingestor = StreamDataIngestor(
        stream_type=StreamType.HELIUS_WEBHOOK,
        stream_url=f"https://api.helius-rpc.com/{api_key}/v0/addresses/J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz/transactions",
        api_key=api_key,
        subscription_params={
            "poll_interval": 2.0  # Poll every 2 seconds
        }
    )
    
    # Register callbacks
    ingestor.on_message(on_message)
    ingestor.on_connect(on_connect)
    ingestor.on_disconnect(on_disconnect)
    ingestor.on_error(on_error)
    
    # Start consuming data
    await ingestor.start()
    
    try:
        # Run for 30 seconds
        logger.info("Running for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get metrics
        metrics = ingestor.get_metrics()
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
    finally:
        # Stop consuming data
        await ingestor.stop()

async def main() -> None:
    """Main function."""
    # Test Lil' Jito stream
    await test_liljito_stream()
    
    # Test Helius stream
    await test_helius_stream()

if __name__ == "__main__":
    asyncio.run(main())
