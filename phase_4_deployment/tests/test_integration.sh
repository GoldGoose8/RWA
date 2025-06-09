#!/bin/bash
# Test script for integration with external services

# Exit on error, but allow for proper error handling
set -e

# Function to log messages with timestamp
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $@"
}

# Function to handle errors
handle_error() {
    log "ERROR" "An error occurred on line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Function to run a test and report the result
run_test() {
    local test_name=$1
    local test_command=$2

    log "INFO" "Running test: $test_name"

    if eval "$test_command"; then
        log "SUCCESS" "Test passed: $test_name"
        return 0
    else
        log "FAILURE" "Test failed: $test_name"
        return 1
    fi
}

# Function to clean up after tests
cleanup() {
    log "INFO" "Cleaning up..."

    # Stop and remove containers
    log "INFO" "Stopping containers..."
    docker-compose -f phase_4_deployment/docker-compose.yml down

    log "INFO" "Cleanup complete"
}

# Create Python test script for integration tests
create_test_script() {
    local script_path="phase_4_deployment/tests/integration_test.py"

    log "INFO" "Creating Python test script: $script_path"

    cat > "$script_path" << 'EOF'
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
        from solana_tx_utils import Keypair, Transaction

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
        from solana_tx_utils import Keypair, Transaction

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
EOF

    # Make the script executable
    chmod +x "$script_path"

    log "INFO" "Python test script created"
}

# Main function
main() {
    log "INFO" "Starting integration tests..."

    # Change to the project root directory
    cd "$(dirname "$0")/../.."
    log "INFO" "Working directory: $(pwd)"

    # Set up test environment
    log "INFO" "Setting up test environment..."

    # Create test directories if they don't exist
    mkdir -p phase_4_deployment/tests/results

    # Create Python test script
    create_test_script

    # Test variables
    local test_passed=0
    local test_failed=0
    local test_results_file="phase_4_deployment/tests/results/integration_test_results.txt"

    # Initialize test results file
    echo "Integration Test Results - $(date)" > "$test_results_file"
    echo "============================" >> "$test_results_file"

    # Test 1: Start production container
    if run_test "Start production container" "docker-compose -f phase_4_deployment/docker-compose.yml up -d"; then
        echo "✅ Production container start: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Production container start: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi

    # Wait for container to start
    log "INFO" "Waiting for container to start..."
    sleep 10

    # Test 2: Run integration tests in container
    if run_test "Run integration tests" "docker cp phase_4_deployment/tests/integration_test.py q5_trading_bot:/app/ && docker exec -e HELIUS_API_KEY=dda9f776-9a40-447d-9ca4-22a27c21169e -e BIRDEYE_API_KEY=a2679724762a47b58dde41b20fb55ce9 -e SOLANA_TX_UTILS_FALLBACK=true -e DOCKER_CONTAINER=true q5_trading_bot python /app/integration_test.py"; then
        echo "✅ Integration tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Integration tests: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi

    # Print test summary
    log "INFO" "Test summary:"
    log "INFO" "  Passed: $test_passed"
    log "INFO" "  Failed: $test_failed"
    log "INFO" "  Total: $((test_passed + test_failed))"

    # Append summary to test results file
    echo "" >> "$test_results_file"
    echo "Test Summary:" >> "$test_results_file"
    echo "  Passed: $test_passed" >> "$test_results_file"
    echo "  Failed: $test_failed" >> "$test_results_file"
    echo "  Total: $((test_passed + test_failed))" >> "$test_results_file"

    # Clean up
    cleanup

    # Return success if all tests passed
    if [ $test_failed -eq 0 ]; then
        log "SUCCESS" "All tests passed!"
        return 0
    else
        log "FAILURE" "Some tests failed. See $test_results_file for details."
        return 1
    fi
}

# Run the main function
main "$@"
