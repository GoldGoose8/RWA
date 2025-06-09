#!/usr/bin/env python3
"""
Wallet Balance Checker
======================

Quick script to check the balance of the configured trading wallet.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    sys.exit(1)

def check_wallet_balance():
    """Check wallet balance using configured RPC endpoints."""
    # Load environment variables
    load_dotenv()
    
    wallet_address = os.getenv("WALLET_ADDRESS")
    if not wallet_address or "your_" in wallet_address:
        print("❌ Wallet address not configured in .env file")
        return
    
    print(f"🔍 Checking balance for wallet: {wallet_address}")
    print("=" * 60)
    
    # Try Helius RPC
    helius_url = os.getenv("HELIUS_RPC_URL")
    if helius_url and "your_" not in helius_url:
        try:
            print(f"📡 Testing Helius RPC...")
            client = Client(helius_url)
            pubkey = Pubkey.from_string(wallet_address)
            balance_response = client.get_balance(pubkey)
            balance_lamports = balance_response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            print(f"✅ Helius RPC: {balance_sol:.9f} SOL ({balance_lamports:,} lamports)")
            
        except Exception as e:
            print(f"❌ Helius RPC error: {e}")
    
    # Try public RPC as backup
    try:
        print(f"📡 Testing Public RPC...")
        public_client = Client("https://api.mainnet-beta.solana.com")
        pubkey = Pubkey.from_string(wallet_address)
        balance_response = public_client.get_balance(pubkey)
        balance_lamports = balance_response.value
        balance_sol = balance_lamports / 1_000_000_000
        
        print(f"✅ Public RPC: {balance_sol:.9f} SOL ({balance_lamports:,} lamports)")
        
    except Exception as e:
        print(f"❌ Public RPC error: {e}")
    
    print("=" * 60)
    
    if balance_sol == 0:
        print("💰 WALLET FUNDING NEEDED:")
        print(f"   Send SOL to: {wallet_address}")
        print(f"   Explorer: https://explorer.solana.com/address/{wallet_address}")
        print(f"   Recommended: 1-2 SOL for testing")
    else:
        print(f"✅ Wallet funded with {balance_sol:.9f} SOL")

if __name__ == "__main__":
    check_wallet_balance()
