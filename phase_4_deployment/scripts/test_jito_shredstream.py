#!/usr/bin/env python3
"""
Jito ShredStream Connection Test

This script tests the connection to Jito's ShredStream service.
It verifies that your keypair is properly registered and can authenticate with the service.
"""

import os
import json
import asyncio
import logging
import argparse
import websockets
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('jito_shredstream_test')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test Jito ShredStream connection')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to Jito config file (default: configs/jito_config.yaml)')
    parser.add_argument('--keypair', type=str, default=None,
                        help='Path to keypair file (default: from config)')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Connection timeout in seconds (default: 30)')
    return parser.parse_args()

async def test_shredstream_connection(config_path, keypair_path=None, timeout=30):
    """
    Test connection to Jito ShredStream service.
    
    Args:
        config_path: Path to Jito config file
        keypair_path: Path to keypair file (overrides config)
        timeout: Connection timeout in seconds
        
    Returns:
        True if connection successful, False otherwise
    """
    # Load config
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        shredstream_url = config['rpc']['shredstream_url']
        keypair_path = keypair_path or config['auth']['keypair_path']
        
        logger.info(f"ShredStream URL: {shredstream_url}")
        logger.info(f"Keypair path: {keypair_path}")
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        return False
    
    # Load keypair
    try:
        with open(keypair_path, 'r') as f:
            keypair_data = json.load(f)
        
        public_key = keypair_data.get('public_key')
        private_key = keypair_data.get('private_key')
        
        if not public_key or not private_key:
            logger.error("Public key or private key not found in keypair file")
            return False
        
        logger.info(f"Using public key: {public_key}")
    except Exception as e:
        logger.error(f"Failed to load keypair: {str(e)}")
        return False
    
    # Connect to ShredStream
    try:
        logger.info(f"Connecting to ShredStream at {shredstream_url}...")
        
        # According to Jito docs, we need to include the keypair in the connection
        headers = {
            "X-Jito-Key": public_key,
            "X-Jito-Signature": private_key  # In a real implementation, we would sign a challenge
        }
        
        # Set up connection with timeout
        connection_task = asyncio.create_task(
            websockets.connect(shredstream_url, extra_headers=headers)
        )
        
        # Wait for connection with timeout
        try:
            websocket = await asyncio.wait_for(connection_task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"Connection timed out after {timeout} seconds")
            return False
        
        logger.info("Connected to ShredStream successfully!")
        
        # Subscribe to shreds
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "subscribeShreds",
            "params": []
        }
        
        await websocket.send(json.dumps(subscribe_msg))
        logger.info("Sent subscription request")
        
        # Wait for subscription confirmation
        response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
        response_data = json.loads(response)
        
        if 'result' in response_data:
            logger.info(f"Subscription successful: {response_data['result']}")
        else:
            logger.error(f"Subscription failed: {response_data.get('error')}")
            await websocket.close()
            return False
        
        # Wait for first shred
        logger.info("Waiting for first shred...")
        shred = await asyncio.wait_for(websocket.recv(), timeout=timeout)
        shred_data = json.loads(shred)
        
        logger.info(f"Received first shred: {shred_data}")
        
        # Close connection
        await websocket.close()
        logger.info("Connection closed")
        
        return True
    except Exception as e:
        logger.error(f"Error connecting to ShredStream: {str(e)}")
        return False

async def main_async():
    """Async main function."""
    args = parse_args()
    
    # Default config path
    config_path = args.config or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'configs', 'jito_config.yaml'
    )
    
    logger.info("Starting Jito ShredStream connection test")
    
    result = await test_shredstream_connection(
        config_path=config_path,
        keypair_path=args.keypair,
        timeout=args.timeout
    )
    
    if result:
        logger.info("Jito ShredStream connection test PASSED")
        return 0
    else:
        logger.error("Jito ShredStream connection test FAILED")
        return 1

def main():
    """Main function."""
    return asyncio.run(main_async())

if __name__ == "__main__":
    import sys
    sys.exit(main())
