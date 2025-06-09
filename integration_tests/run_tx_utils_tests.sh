#!/bin/bash
# Run the integration tests for the solana_tx_utils package

# Change to the project root directory
cd "$(dirname "$0")/.."

# Build and install the package
echo "Building and installing solana_tx_utils package..."
cd solana_tx_utils
./build_and_install.sh
cd ..

# Run the integration tests
echo "Running integration tests..."
python -m integration_tests.tx_utils_tests.test_transaction_integration

echo "Integration tests completed!"
