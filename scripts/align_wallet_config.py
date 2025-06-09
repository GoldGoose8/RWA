#!/usr/bin/env python3
"""
Wallet Configuration Alignment Script
=====================================

This script helps align the .env file with the currently active trading wallet.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def get_current_active_wallet():
    """Get the currently active trading wallet from recent trades."""
    try:
        # Get the most recent trade file
        trade_dir = Path('backups/trades_backup_20250531_175013')
        if not trade_dir.exists():
            print("❌ No trade backup directory found")
            return None
            
        trade_files = sorted(trade_dir.glob('trade_*.json'))
        if not trade_files:
            print("❌ No trade files found")
            return None
            
        latest_trade = trade_files[-1]
        with open(latest_trade, 'r') as f:
            trade_data = json.load(f)
        
        wallet_address = trade_data.get('wallet_address')
        timestamp = trade_data.get('timestamp')
        balance_validation = trade_data.get('balance_validation', {})
        
        return {
            'address': wallet_address,
            'timestamp': timestamp,
            'balance_before': balance_validation.get('balance_before', 0),
            'balance_after': balance_validation.get('balance_after', 0),
            'trade_file': latest_trade.name
        }
        
    except Exception as e:
        print(f"❌ Error getting current wallet: {e}")
        return None

def check_env_alignment():
    """Check if .env file is aligned with current trading wallet."""
    load_dotenv()
    
    current_wallet = get_current_active_wallet()
    if not current_wallet:
        return False
        
    env_wallet = os.getenv('WALLET_ADDRESS')
    
    print("🔍 WALLET ALIGNMENT CHECK")
    print("=" * 50)
    print(f"Current Active Wallet: {current_wallet['address']}")
    print(f"Env File Wallet:       {env_wallet}")
    print(f"Last Trade:            {current_wallet['timestamp']}")
    print(f"Current Balance:       {current_wallet['balance_after']:.9f} SOL")
    print()
    
    if current_wallet['address'] == env_wallet:
        print("✅ ALIGNED: .env file matches current trading wallet")
        return True
    else:
        print("❌ MISALIGNED: .env file does not match current trading wallet")
        return False

def get_wallet_info():
    """Get comprehensive wallet information."""
    current_wallet = get_current_active_wallet()
    if not current_wallet:
        return
        
    wallet_address = current_wallet['address']
    
    print("💰 CURRENT TRADING WALLET INFO")
    print("=" * 50)
    print(f"Address: {wallet_address}")
    print(f"Balance: {current_wallet['balance_after']:.9f} SOL")
    print(f"Last Trade: {current_wallet['timestamp']}")
    print()
    print("🔗 Explorer Links:")
    print(f"Solana Explorer: https://explorer.solana.com/address/{wallet_address}")
    print(f"Solscan: https://solscan.io/account/{wallet_address}")
    print()
    print("📋 REQUIRED ACTIONS:")
    print("1. Get the private key for this wallet")
    print("2. Update .env file with the correct WALLET_PRIVATE_KEY")
    print("3. Find or create USDC token account for this wallet")
    print("4. Update WALLET_USDC_ACCOUNT in .env file")
    print()
    print("⚠️  SECURITY WARNING:")
    print("- Never share your private key")
    print("- Ensure .env file is secure and not committed to version control")
    print("- Use a dedicated trading wallet with limited funds")

def check_balance():
    """Check current balance of the active wallet."""
    current_wallet = get_current_active_wallet()
    if not current_wallet:
        return
        
    wallet_address = current_wallet['address']
    
    try:
        from solders.pubkey import Pubkey
        from solana.rpc.api import Client
        
        print("💰 LIVE BALANCE CHECK")
        print("=" * 50)
        
        # Try multiple RPC endpoints
        endpoints = [
            ("Helius", os.getenv("HELIUS_RPC_URL")),
            ("QuickNode", os.getenv("QUICKNODE_RPC_URL")),
            ("Public", "https://api.mainnet-beta.solana.com")
        ]
        
        for name, url in endpoints:
            if not url or "your_" in url:
                continue
                
            try:
                print(f"📡 Checking {name} RPC...")
                client = Client(url)
                pubkey = Pubkey.from_string(wallet_address)
                balance_response = client.get_balance(pubkey)
                balance_lamports = balance_response.value
                balance_sol = balance_lamports / 1_000_000_000
                
                print(f"✅ {name}: {balance_sol:.9f} SOL ({balance_lamports:,} lamports)")
                
                # Calculate USD value
                sol_price = 156.0  # Approximate
                balance_usd = balance_sol * sol_price
                print(f"💵 USD Value: ${balance_usd:.2f} (at ${sol_price:.2f}/SOL)")
                break
                
            except Exception as e:
                print(f"❌ {name} error: {e}")
                
    except ImportError:
        print("❌ Solana packages not available for live balance check")
        print("Install with: pip install solders solana")

def main():
    """Main function."""
    print("🚀 WALLET CONFIGURATION ALIGNMENT TOOL")
    print("=" * 60)
    print()
    
    # Check current alignment
    is_aligned = check_env_alignment()
    print()
    
    # Show wallet info
    get_wallet_info()
    print()
    
    # Check live balance
    check_balance()
    print()
    
    if not is_aligned:
        print("🔧 NEXT STEPS:")
        print("1. Update WALLET_PRIVATE_KEY in .env file")
        print("2. Update WALLET_USDC_ACCOUNT in .env file")
        print("3. Run this script again to verify alignment")
        print("4. Test with: python3 scripts/check_wallet_balance.py")

if __name__ == "__main__":
    main()
