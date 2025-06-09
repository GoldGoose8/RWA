#!/usr/bin/env python3
"""
Native Wallet Balance Checker
=============================

Simple balance checker for native Solana wallets that avoids proxy issues.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_native_wallet_balance():
    """Check the balance of the native wallet."""
    try:
        import httpx
        
        wallet_address = os.getenv('WALLET_ADDRESS')
        rpc_url = os.getenv('QUICKNODE_RPC_URL') or os.getenv('HELIUS_RPC_URL')
        
        if not wallet_address:
            print("❌ No wallet address found in environment")
            print("💡 Create a wallet first: python3 scripts/create_native_solana_wallet.py")
            return False
        
        print("🔍 NATIVE WALLET BALANCE CHECK")
        print("=" * 60)
        print(f"📍 Wallet Address: {wallet_address}")
        print(f"📡 RPC Endpoint: {rpc_url}")
        print()
        
        # Check SOL balance
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }
            
            response = await client.post(rpc_url, json=payload)
            data = response.json()
            
            if 'result' in data and 'value' in data['result']:
                sol_balance = data['result']['value'] / 1_000_000_000
                usd_value = sol_balance * 151  # Approximate SOL price
                
                print(f"💰 SOL Balance: {sol_balance:.6f} SOL")
                print(f"💵 USD Value: ~${usd_value:.2f}")
                print()
                
                # Status assessment
                if sol_balance >= 10.0:
                    print("🟢 STATUS: Excellent! Ready for serious trading")
                    print("💡 This balance supports meaningful position sizes")
                elif sol_balance >= 1.0:
                    print("🟢 STATUS: Good! Ready for trading")
                    print("💡 Sufficient balance for active trading")
                elif sol_balance >= 0.1:
                    print("🟡 STATUS: Minimal funding - ready for testing")
                    print("💡 Consider adding more SOL for larger trades")
                elif sol_balance > 0:
                    print("🟡 STATUS: Funded but very low balance")
                    print("💡 Add more SOL for meaningful trading")
                else:
                    print("🔴 STATUS: Wallet is empty - needs funding")
                    print("💡 Send SOL to this address to start trading")
                
                print()
                
                if sol_balance == 0:
                    print("📋 FUNDING INSTRUCTIONS:")
                    print("1. Send SOL from an exchange (Coinbase, Binance, etc.)")
                    print("2. Use Phantom/Solflare wallet to transfer SOL")
                    print("3. Use Solana CLI: solana transfer <address> <amount>")
                    print()
                    print("💡 Recommended amounts:")
                    print("   • Testing: 0.5-1 SOL (~$75-150)")
                    print("   • Active Trading: 5-20 SOL (~$750-3000)")
                    print("   • Serious Trading: 20+ SOL (~$3000+)")
                
                return sol_balance > 0
                
            else:
                print(f"❌ Error getting balance: {data}")
                return False
        
    except Exception as e:
        print(f"❌ Error checking wallet balance: {e}")
        return False

async def check_token_accounts():
    """Check if token accounts exist (simplified version)."""
    try:
        wallet_address = os.getenv('WALLET_ADDRESS')
        usdc_account = os.getenv('WALLET_USDC_ACCOUNT')
        
        print("📋 TOKEN ACCOUNT STATUS:")
        print(f"   USDC Account: {usdc_account if usdc_account else 'Not configured'}")
        
        if not usdc_account:
            print("💡 Token accounts will be created automatically during first trade")
        
        print()
        
    except Exception as e:
        print(f"❌ Error checking token accounts: {e}")

async def main():
    """Main function."""
    print("🚀 NATIVE SOLANA WALLET BALANCE CHECKER")
    print("=" * 60)
    
    # Check wallet balance
    balance_ok = await check_native_wallet_balance()
    
    # Check token accounts
    await check_token_accounts()
    
    print("=" * 60)
    
    if balance_ok:
        print("✅ Wallet check complete - ready for trading!")
        print("🚀 Start trading: python3 scripts/unified_live_trading.py")
    else:
        print("⚠️ Wallet needs funding before trading")
        print("💡 Fund wallet: python3 scripts/fund_native_wallet.py --instructions")
    
    return 0 if balance_ok else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
