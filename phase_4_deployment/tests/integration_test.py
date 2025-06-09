#!/usr/bin/env python3
"""
Test script for integration with external services.
"""

import os
import time
import json
import asyncio
import logging
import httpx
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("integration_test")

async def test_helius_integration():
    """Test integration with Helius API."""
    logger.info("Testing Helius API integration...")
    
    try:
        # Get API key from environment
        api_key = os.environ.get("HELIUS_API_KEY")
        if not api_key:
            logger.error("HELIUS_API_KEY environment variable not set")
            return False
        
        # Set up RPC URL
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        
        # Test getLatestBlockhash
        async with httpx.AsyncClient() as client:
            response = await client.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [],
                },
                timeout=10.0,
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get latest blockhash: {response.text}")
                return False
            
            result = response.json()
            if "error" in result:
                logger.error(f"Failed to get latest blockhash: {result['error']}")
                return False
            
            blockhash = result["result"]["value"]["blockhash"]
            logger.info(f"Got latest blockhash: {blockhash}")
        
        # Test with PyO3 extension
        from shared.solana_utils.tx_utils import Keypair, Transaction
        
        # Create a keypair
        keypair = Keypair()
        pubkey = keypair.pubkey()
        
        # Create a transaction
        tx = Transaction(blockhash, pubkey)
        
        # Sign the transaction
        tx.sign(keypair.to_bytes())
        
        # Serialize the transaction
        serialized = tx.serialize()
        
        logger.info(f"Created and signed transaction with PyO3 extension")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing Helius integration: {str(e)}")
        return False

async def test_birdeye_integration():
    """Test integration with Birdeye API."""
    logger.info("Testing Birdeye API integration...")
    
    try:
        # Get API key from environment
        api_key = os.environ.get("BIRDEYE_API_KEY")
        if not api_key:
            logger.error("BIRDEYE_API_KEY environment variable not set")
            return False
        
        # Set up API URL
        api_url = "https://public-api.birdeye.so/defi/price"
        
        # Test getting token price
        async with httpx.AsyncClient() as client:
            response = await client.get(
                api_url,
                params={"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"},  # USDC
                headers={"X-API-KEY": api_key},
                timeout=10.0,
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get token price: {response.text}")
                return False
            
            result = response.json()
            if "data" not in result or "value" not in result["data"]:
                logger.error(f"Invalid response format: {result}")
                return False
            
            price = result["data"]["value"]
            logger.info(f"Got USDC price: ${price}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing Birdeye integration: {str(e)}")
        return False

async def test_end_to_end_flow():
    """Test end-to-end transaction flow."""
    logger.info("Testing end-to-end transaction flow...")
    
    try:
        # Get API key from environment
        api_key = os.environ.get("HELIUS_API_KEY")
        if not api_key:
            logger.error("HELIUS_API_KEY environment variable not set")
            return False
        
        # Set up RPC URL
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        
        # Get latest blockhash
        async with httpx.AsyncClient() as client:
            response = await client.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [],
                },
                timeout=10.0,
            )
            
            result = response.json()
            blockhash = result["result"]["value"]["blockhash"]
        
        # Create a transaction with PyO3 extension
        from shared.solana_utils.tx_utils import Keypair, Transaction
        
        # Create a keypair
        keypair = Keypair()
        pubkey = keypair.pubkey()
        
        # Create a transaction
        tx = Transaction(blockhash, pubkey)
        
        # Sign the transaction
        tx.sign(keypair.to_bytes())
        
        # Serialize the transaction
        serialized = tx.serialize()
        
        logger.info(f"Created and signed transaction with PyO3 extension")
        
        # This is a simulation, so we don't actually send the transaction
        logger.info(f"Transaction simulation successful")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing end-to-end flow: {str(e)}")
        return False

async def main():
    """Main function."""
    logger.info("Starting integration tests...")
    
    tests = [
        ("Helius Integration", test_helius_integration),
        ("Birdeye Integration", test_birdeye_integration),
        ("End-to-End Flow", test_end_to_end_flow),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        
        try:
            if await test_func():
                logger.info(f"Test passed: {name}")
                passed += 1
            else:
                logger.error(f"Test failed: {name}")
                failed += 1
        except Exception as e:
            logger.error(f"Error running test {name}: {str(e)}")
            failed += 1
    
    logger.info(f"Test summary: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
