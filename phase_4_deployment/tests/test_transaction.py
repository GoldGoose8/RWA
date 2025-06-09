#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Q5 System Wallet Balance Check

This script checks the wallet balance to verify the system is working correctly.
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wallet_check')

# Load environment variables
load_dotenv()

def check_wallet_balance():
    """Check wallet balance."""
    try:
        # Get wallet address from environment
        wallet_address = os.getenv("WALLET_ADDRESS")
        if not wallet_address:
            logger.error("WALLET_ADDRESS not found in environment variables")
            return False

        # Get RPC URL from environment
        rpc_url = os.getenv("FALLBACK_RPC_URL", "https://api.mainnet-beta.solana.com")

        # Create payload for RPC request
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }

        # Send request
        logger.info(f"Checking balance for wallet: {wallet_address}")
        response = requests.post(rpc_url, json=payload)

        # Parse response
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                balance_lamports = data['result']['value']
                balance_sol = balance_lamports / 10**9  # Convert lamports to SOL
                logger.info(f"Wallet balance: {balance_sol} SOL")
                return True
            else:
                logger.error(f"Error in RPC response: {data.get('error')}")
                return False
        else:
            logger.error(f"Error connecting to RPC: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Error checking wallet balance: {str(e)}")
        return False

def main():
    """Main function."""
    success = check_wallet_balance()
    if success:
        logger.info("Wallet balance check completed successfully!")
    else:
        logger.error("Wallet balance check failed!")

if __name__ == "__main__":
    main()
