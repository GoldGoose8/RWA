#!/usr/bin/env python3
"""
Docker-specific test script for solana_tx_utils.

This script tests the functionality of the solana_tx_utils package in a Docker environment.
"""

import os
import sys
import time
import base58
import base64
import logging
import platform
from typing import Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("docker_test")

def test_environment():
    """Test the environment."""
    logger.info("Testing environment...")
    
    # Check if we're running in Docker
    in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER", "") == "true"
    logger.info(f"Running in Docker: {in_docker}")
    
    # Check platform
    platform_system = platform.system()
    platform_machine = platform.machine()
    logger.info(f"Platform: {platform_system} {platform_machine}")
    
    # Check Python version
    python_version = platform.python_version()
    logger.info(f"Python version: {python_version}")
    
    # Check environment variables
    fallback_enabled = os.environ.get("SOLANA_TX_UTILS_FALLBACK", "false").lower() in ("true", "1", "yes")
    logger.info(f"Fallback enabled: {fallback_enabled}")
    
    return True

def test_solana_tx_utils_import():
    """Test importing solana_tx_utils."""
    logger.info("Testing solana_tx_utils import...")
    
    try:
        import shared.solana_utils.tx_utils
        logger.info(f"solana_tx_utils version: {solana_tx_utils.__version__}")
        
        # Check if we're using the native implementation or fallback
        if hasattr(solana_tx_utils, "FORCE_FALLBACK"):
            logger.info(f"FORCE_FALLBACK: {solana_tx_utils.FORCE_FALLBACK}")
        
        if hasattr(solana_tx_utils, "IN_DOCKER"):
            logger.info(f"IN_DOCKER: {solana_tx_utils.IN_DOCKER}")
        
        if hasattr(solana_tx_utils, "PLATFORM"):
            logger.info(f"PLATFORM: {solana_tx_utils.PLATFORM}")
        
        if hasattr(solana_tx_utils, "ARCH"):
            logger.info(f"ARCH: {solana_tx_utils.ARCH}")
        
        return True
    except ImportError as e:
        logger.error(f"Failed to import shared.solana_utils.tx_utils: {e}")
        return False

def test_keypair_generation():
    """Test keypair generation."""
    logger.info("Testing keypair generation...")
    
    try:
        from shared.solana_utils.tx_utils import Keypair
        
        # Create a keypair
        start_time = time.time()
        keypair = Keypair()
        end_time = time.time()
        
        # Get the public key
        pubkey = keypair.pubkey()
        
        logger.info(f"Created keypair with pubkey: {pubkey}")
        logger.info(f"Time taken: {end_time - start_time:.6f} seconds")
        
        # Test to_bytes and from_bytes
        keypair_bytes = keypair.to_bytes()
        restored_keypair = Keypair.from_bytes(keypair_bytes)
        restored_pubkey = restored_keypair.pubkey()
        
        if pubkey == restored_pubkey:
            logger.info("Keypair serialization/deserialization test passed")
            return True
        else:
            logger.error("Keypair serialization/deserialization test failed")
            return False
    
    except Exception as e:
        logger.error(f"Error testing keypair generation: {str(e)}")
        return False

def test_transaction_creation():
    """Test transaction creation and signing."""
    logger.info("Testing transaction creation and signing...")
    
    try:
        from shared.solana_utils.tx_utils import Keypair, Transaction
        
        # Create a keypair
        keypair = Keypair()
        pubkey = keypair.pubkey()
        
        # Create a transaction
        start_time = time.time()
        tx = Transaction("CiRuABNr3yLxF3Gh9HedNdAVdXKgz1xTjEZTbq2U8LxW", pubkey)
        end_time = time.time()
        
        logger.info(f"Created transaction")
        logger.info(f"Time taken: {end_time - start_time:.6f} seconds")
        
        # Sign the transaction
        start_time = time.time()
        tx.sign(keypair.to_bytes())
        end_time = time.time()
        
        logger.info(f"Signed transaction")
        logger.info(f"Time taken: {end_time - start_time:.6f} seconds")
        
        # Serialize the transaction
        serialized = tx.serialize()
        encoded = base58.b58encode(serialized).decode('utf-8')
        
        logger.info(f"Serialized transaction: {encoded[:32]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing transaction creation: {str(e)}")
        return False

def test_encoding_functions():
    """Test encoding and decoding functions."""
    logger.info("Testing encoding and decoding functions...")
    
    try:
        from shared.solana_utils.tx_utils import encode_base58, decode_base58, encode_base64, decode_base64
        import os
        
        # Test data
        data = os.urandom(32)
        
        # Test base58 encoding/decoding
        start_time = time.time()
        encoded_b58 = encode_base58(data)
        decoded_b58 = decode_base58(encoded_b58)
        end_time = time.time()
        
        logger.info(f"Base58 encoding/decoding time: {end_time - start_time:.6f} seconds")
        
        # Test base64 encoding/decoding
        start_time = time.time()
        encoded_b64 = encode_base64(data)
        decoded_b64 = decode_base64(encoded_b64)
        end_time = time.time()
        
        logger.info(f"Base64 encoding/decoding time: {end_time - start_time:.6f} seconds")
        
        # Verify results
        if data == decoded_b58 and data == decoded_b64:
            logger.info("Encoding/decoding test passed")
            return True
        else:
            logger.error("Encoding/decoding test failed")
            return False
    
    except Exception as e:
        logger.error(f"Error testing encoding functions: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting Docker-specific tests...")
    
    tests = [
        ("Environment", test_environment),
        ("solana_tx_utils Import", test_solana_tx_utils_import),
        ("Keypair Generation", test_keypair_generation),
        ("Transaction Creation", test_transaction_creation),
        ("Encoding Functions", test_encoding_functions),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        
        try:
            if test_func():
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
    sys.exit(main())
