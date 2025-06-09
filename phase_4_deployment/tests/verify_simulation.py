#!/usr/bin/env python3
"""
Simulation Verification Script for Q5 Trading System

This script verifies that the end-to-end simulation test was successful
by checking all output files and their contents.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Define expected output files
EXPECTED_FILES = [
    ("output/token_opportunities.json", "Token opportunities data"),
    ("output/active_launches.json", "Active launches data"),
    ("output/whale_opportunities.json", "Whale opportunities data"),
    ("output/signals.json", "Sample signals"),
    ("output/enriched_signals.json", "Enriched signals data"),
    ("output/execution_log.txt", "Execution log"),
    ("output/tx_history.json", "Transaction history"),
    ("output/jito_metrics.json", "Jito metrics")
]

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{BLUE}======================================{NC}")
    print(f"{BLUE}{message}{NC}")
    print(f"{BLUE}======================================{NC}\n")

def check_file(file_path: str, description: str) -> Tuple[bool, Any]:
    """
    Check if a file exists and has valid content.

    Args:
        file_path: Path to the file
        description: Description of the file

    Returns:
        Tuple of (success, content)
    """
    if not os.path.exists(file_path):
        print(f"{RED}✗ {description} not found: {file_path}{NC}")
        return False, None

    if os.path.getsize(file_path) == 0:
        print(f"{RED}✗ {description} is empty: {file_path}{NC}")
        return False, None

    # Try to parse JSON files
    if file_path.endswith('.json'):
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
            print(f"{GREEN}✓ {description} is valid JSON: {file_path}{NC}")
            return True, content
        except json.JSONDecodeError:
            print(f"{RED}✗ {description} contains invalid JSON: {file_path}{NC}")
            return False, None

    # For text files, just read the content
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        print(f"{GREEN}✓ {description} exists and has content: {file_path}{NC}")
        return True, content
    except Exception as e:
        print(f"{RED}✗ Error reading {description}: {str(e)}{NC}")
        return False, None

def verify_enriched_signals(content: Dict[str, Any]) -> bool:
    """
    Verify that enriched signals have all required fields.

    Args:
        content: Enriched signals JSON content

    Returns:
        True if valid, False otherwise
    """
    if 'signals' not in content:
        print(f"{RED}✗ Enriched signals missing 'signals' key{NC}")
        return False

    signals = content['signals']
    if not signals or not isinstance(signals, list):
        print(f"{RED}✗ Enriched signals has empty or invalid 'signals' list{NC}")
        return False

    # Check required fields in each signal
    required_fields = ['action', 'market', 'price', 'size', 'strategy_id', 'timestamp']
    enrichment_fields = ['market_context', 'route_info', 'execution_price', 'risk_metrics']

    all_valid = True
    for i, signal in enumerate(signals):
        # Check basic fields
        for field in required_fields:
            if field not in signal:
                print(f"{RED}✗ Signal {i} missing required field: {field}{NC}")
                all_valid = False

        # Check enrichment fields (at least some should be present)
        has_enrichment = False
        for field in enrichment_fields:
            if field in signal:
                has_enrichment = True
                break

        if not has_enrichment:
            print(f"{YELLOW}⚠ Signal {i} has no enrichment fields{NC}")

    if all_valid:
        print(f"{GREEN}✓ All signals have required fields{NC}")

    return all_valid

def verify_tx_history(content: Dict[str, Any]) -> bool:
    """
    Verify that transaction history has all required fields.

    Args:
        content: Transaction history JSON content

    Returns:
        True if valid, False otherwise
    """
    if 'transactions' not in content:
        print(f"{RED}✗ Transaction history missing 'transactions' key{NC}")
        return False

    transactions = content['transactions']
    if not isinstance(transactions, list):
        print(f"{RED}✗ Transaction history has invalid 'transactions' list{NC}")
        return False

    # Empty transactions list is OK for simulation
    if not transactions:
        print(f"{YELLOW}⚠ Transaction history has empty 'transactions' list{NC}")
        return True

    # Check required fields in each transaction
    required_fields = ['timestamp', 'signature', 'status', 'market', 'action']

    all_valid = True
    for i, tx in enumerate(transactions):
        for field in required_fields:
            if field not in tx:
                print(f"{RED}✗ Transaction {i} missing required field: {field}{NC}")
                all_valid = False

    if all_valid:
        print(f"{GREEN}✓ All transactions have required fields{NC}")

    return all_valid

def main():
    """Main function."""
    print_header("Q5 TRADING SYSTEM - SIMULATION VERIFICATION")
    print(f"{YELLOW}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{NC}")

    # Check all expected files
    all_files_valid = True
    file_contents = {}

    for file_path, description in EXPECTED_FILES:
        valid, content = check_file(file_path, description)
        if not valid:
            all_files_valid = False
        else:
            file_contents[file_path] = content

    # Perform deeper verification on key files
    if 'output/enriched_signals.json' in file_contents:
        if not verify_enriched_signals(file_contents['output/enriched_signals.json']):
            all_files_valid = False

    if 'output/tx_history.json' in file_contents:
        if not verify_tx_history(file_contents['output/tx_history.json']):
            all_files_valid = False

    # Print summary
    print_header("VERIFICATION SUMMARY")

    if all_files_valid:
        print(f"{GREEN}✓ All simulation outputs are valid!{NC}")
        print(f"\n{GREEN}The end-to-end simulation test was successful.{NC}")
        print(f"{GREEN}You can proceed to Step 2: Live Execution Prep.{NC}")
        return 0
    else:
        print(f"{RED}✗ Some simulation outputs are invalid or missing.{NC}")
        print(f"\n{YELLOW}Please check the errors above and run the simulation test again.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
