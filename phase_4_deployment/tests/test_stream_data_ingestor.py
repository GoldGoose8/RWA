#!/usr/bin/env python3
"""
Test script for the stream data ingestor.

This script tests the stream data ingestor with various stream types.
"""

import os
import sys
import json
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_stream_data_ingestor')

# Load environment variables
load_dotenv()

async def test_stream_data_ingestor():
    """Test the stream data ingestor with various stream types."""
    try:
        # Import the stream data ingestor
        from stream_data_ingestor.client import StreamDataIngestor, StreamType

        # Test creating a mock stream
        logger.info("Testing creating a mock stream...")

        # Create a mock stream
        mock_stream = StreamDataIngestor(
            stream_type=StreamType.CUSTOM_WEBSOCKET,
            stream_url="wss://echo.websocket.org",
            subscription_params={
                "subscription_message": {
                    "type": "subscribe",
                    "channels": ["test"]
                },
                "expect_confirmation": False
            }
        )

        # Register callbacks
        message_received = asyncio.Event()
        messages = []

        async def on_message(message):
            logger.info(f"Received message: {message}")
            messages.append(message)
            message_received.set()

        async def on_connect():
            logger.info("Connected to stream")

        async def on_disconnect():
            logger.info("Disconnected from stream")

        async def on_error(error):
            logger.error(f"Stream error: {error}")

        mock_stream.on_message(on_message)
        mock_stream.on_connect(on_connect)
        mock_stream.on_disconnect(on_disconnect)
        mock_stream.on_error(on_error)

        # Start the stream
        logger.info("Starting mock stream...")
        await mock_stream.start()

        # Wait for a bit
        await asyncio.sleep(2)

        # Get metrics
        metrics = mock_stream.get_metrics()
        logger.info(f"Mock stream metrics: {json.dumps(metrics, indent=2)}")

        # Stop the stream
        logger.info("Stopping mock stream...")
        await mock_stream.stop()

        # Test Helius stream if API key is available
        helius_api_key = os.environ.get('HELIUS_API_KEY')
        if helius_api_key:
            logger.info("Testing Helius stream...")

            # Create a Helius stream
            helius_stream = StreamDataIngestor(
                stream_type=StreamType.HELIUS_WEBHOOK,
                stream_url=f"https://api.helius-rpc.com/{helius_api_key}/v0/addresses/J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz/transactions",
                api_key=helius_api_key,
                subscription_params={
                    "poll_interval": 2.0  # Poll every 2 seconds
                }
            )

            # Register callbacks
            helius_stream.on_message(on_message)
            helius_stream.on_connect(on_connect)
            helius_stream.on_disconnect(on_disconnect)
            helius_stream.on_error(on_error)

            # Start the stream
            logger.info("Starting Helius stream...")
            await helius_stream.start()

            # Wait for a bit
            await asyncio.sleep(5)

            # Get metrics
            metrics = helius_stream.get_metrics()
            logger.info(f"Helius stream metrics: {json.dumps(metrics, indent=2)}")

            # Stop the stream
            logger.info("Stopping Helius stream...")
            await helius_stream.stop()
        else:
            logger.warning("HELIUS_API_KEY not found in environment variables, skipping Helius stream test")

        # Test Lil' Jito stream if API key is available
        liljito_api_key = os.environ.get('LILJITO_QUICKNODE_API_KEY')
        if liljito_api_key:
            logger.info("Testing Lil' Jito stream...")

            # Create a Lil' Jito stream
            liljito_stream = StreamDataIngestor(
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
            liljito_stream.on_message(on_message)
            liljito_stream.on_connect(on_connect)
            liljito_stream.on_disconnect(on_disconnect)
            liljito_stream.on_error(on_error)

            # Start the stream
            logger.info("Starting Lil' Jito stream...")
            await liljito_stream.start()

            # Wait for a bit
            await asyncio.sleep(5)

            # Get metrics
            metrics = liljito_stream.get_metrics()
            logger.info(f"Lil' Jito stream metrics: {json.dumps(metrics, indent=2)}")

            # Stop the stream
            logger.info("Stopping Lil' Jito stream...")
            await liljito_stream.stop()
        else:
            logger.warning("LILJITO_QUICKNODE_API_KEY not found in environment variables, skipping Lil' Jito stream test")

        return True

    except Exception as e:
        logger.error(f"Error testing stream data ingestor: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main_async():
    """Async main function."""
    success = await test_stream_data_ingestor()
    if success:
        logger.info("Stream data ingestor test completed successfully!")
    else:
        logger.error("Stream data ingestor test failed!")

def main():
    """Main function."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
