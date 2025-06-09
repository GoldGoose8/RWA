#!/usr/bin/env python3
"""
Test script for PyO3 extension functionality.
"""

import os
import time
import base58
import base64
import logging
from typing import Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pyo3_test")

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

def test_performance_comparison():
    """Compare performance of PyO3 extension vs. fallback."""
    logger.info("Testing performance comparison...")
    
    try:
        # First, test with PyO3 extension
        os.environ["SOLANA_TX_UTILS_FALLBACK"] = "false"
        
        # Force reload of the module
        import importlib
        if "solana_tx_utils" in sys.modules:
            importlib.reload(sys.modules["solana_tx_utils"])
        
        # Test keypair generation with PyO3
        start_time = time.time()
        from shared.solana_utils.tx_utils import Keypair
        for _ in range(100):
            keypair = Keypair()
            _ = keypair.pubkey()
        pyo3_time = time.time() - start_time
        
        logger.info(f"PyO3 extension time for 100 keypairs: {pyo3_time:.6f} seconds")
        
        # Now, test with fallback
        os.environ["SOLANA_TX_UTILS_FALLBACK"] = "true"
        
        # Force reload of the module
        if "solana_tx_utils" in sys.modules:
            importlib.reload(sys.modules["solana_tx_utils"])
        
        # Test keypair generation with fallback
        start_time = time.time()
        from shared.solana_utils.tx_utils import Keypair
        for _ in range(100):
            keypair = Keypair()
            _ = keypair.pubkey()
        fallback_time = time.time() - start_time
        
        logger.info(f"Fallback implementation time for 100 keypairs: {fallback_time:.6f} seconds")
        
        # Compare performance
        if pyo3_time < fallback_time:
            logger.info(f"PyO3 extension is {fallback_time / pyo3_time:.2f}x faster than fallback")
            return True
        else:
            logger.warning(f"Fallback is {pyo3_time / fallback_time:.2f}x faster than PyO3 extension")
            return False
    
    except Exception as e:
        logger.error(f"Error testing performance comparison: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("Starting PyO3 functionality tests...")
    
    tests = [
        ("Keypair Generation", test_keypair_generation),
        ("Transaction Creation", test_transaction_creation),
        ("Encoding Functions", test_encoding_functions),
        ("Performance Comparison", test_performance_comparison),
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
    import sys
    sys.exit(main())
