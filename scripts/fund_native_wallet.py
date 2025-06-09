#!/usr/bin/env python3
"""
Native Wallet Funding Helper
============================

Helps fund a native Solana wallet and create necessary token accounts.
Provides instructions and utilities for wallet setup.
"""

import os
import sys
import json
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

class NativeWalletFunder:
    """Helper for funding and setting up native Solana wallets."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.rpc_url = os.getenv('HELIUS_RPC_URL', 'https://api.mainnet-beta.solana.com')
        
        # Token mint addresses
        self.WSOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    async def check_wallet_balance(self):
        """Check current wallet balance."""
        try:
            import httpx

            if not self.wallet_address:
                logger.error("❌ No wallet address found in environment")
                return None

            # Use direct HTTP client to avoid proxy issues
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }

                response = await client.post(self.rpc_url, json=payload)
                data = response.json()

                if 'result' in data and 'value' in data['result']:
                    sol_balance = data['result']['value'] / 1_000_000_000
                    logger.info(f"💰 Current wallet balance: {sol_balance:.6f} SOL")
                    return sol_balance
                else:
                    logger.warning(f"⚠️ Could not get SOL balance: {data}")
                    return 0.0

        except Exception as e:
            logger.error(f"❌ Error checking wallet balance: {e}")
            return 0.0
    
    async def check_token_accounts(self):
        """Check if token accounts exist and their balances."""
        try:
            from solders.pubkey import Pubkey
            from solders.spl.associated_token_account import get_associated_token_address
            from solana.rpc.api import Client
            
            if not self.wallet_address:
                logger.error("❌ No wallet address found in environment")
                return None
            
            client = Client(self.rpc_url)
            wallet_pubkey = Pubkey.from_string(self.wallet_address)
            wsol_mint = Pubkey.from_string(self.WSOL_MINT)
            usdc_mint = Pubkey.from_string(self.USDC_MINT)
            
            # Get associated token addresses
            wsol_account = get_associated_token_address(wallet_pubkey, wsol_mint)
            usdc_account = get_associated_token_address(wallet_pubkey, usdc_mint)
            
            # Check WSOL account
            try:
                wsol_response = client.get_token_account_balance(wsol_account)
                wsol_balance = float(wsol_response.value.amount) / (10 ** wsol_response.value.decimals)
                wsol_exists = True
            except:
                wsol_balance = 0.0
                wsol_exists = False
            
            # Check USDC account
            try:
                usdc_response = client.get_token_account_balance(usdc_account)
                usdc_balance = float(usdc_response.value.amount) / (10 ** usdc_response.value.decimals)
                usdc_exists = True
            except:
                usdc_balance = 0.0
                usdc_exists = False
            
            logger.info(f"📋 Token Account Status:")
            logger.info(f"   WSOL Account: {wsol_account}")
            logger.info(f"   WSOL Exists: {wsol_exists}, Balance: {wsol_balance:.6f}")
            logger.info(f"   USDC Account: {usdc_account}")
            logger.info(f"   USDC Exists: {usdc_exists}, Balance: {usdc_balance:.6f}")
            
            return {
                'wsol_account': str(wsol_account),
                'wsol_exists': wsol_exists,
                'wsol_balance': wsol_balance,
                'usdc_account': str(usdc_account),
                'usdc_exists': usdc_exists,
                'usdc_balance': usdc_balance
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking token accounts: {e}")
            return None
    
    async def create_token_accounts_if_needed(self):
        """Create token accounts if they don't exist and wallet has SOL."""
        try:
            # Check current balance
            sol_balance = await self.check_wallet_balance()
            if not sol_balance or sol_balance < 0.01:
                logger.warning("⚠️ Insufficient SOL balance to create token accounts")
                logger.info("💡 Fund wallet with at least 0.01 SOL first")
                return False
            
            # Check token accounts
            token_info = await self.check_token_accounts()
            if not token_info:
                return False
            
            accounts_to_create = []
            if not token_info['wsol_exists']:
                accounts_to_create.append('WSOL')
            if not token_info['usdc_exists']:
                accounts_to_create.append('USDC')
            
            if not accounts_to_create:
                logger.info("✅ All token accounts already exist")
                return True
            
            logger.info(f"🔧 Need to create token accounts: {', '.join(accounts_to_create)}")
            logger.info("💡 Token accounts will be created automatically during first trade")
            logger.info("💡 Or you can create them manually using Solana CLI:")
            
            if 'WSOL' in accounts_to_create:
                logger.info(f"   spl-token create-account {self.WSOL_MINT}")
            if 'USDC' in accounts_to_create:
                logger.info(f"   spl-token create-account {self.USDC_MINT}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating token accounts: {e}")
            return False
    
    def display_funding_instructions(self):
        """Display instructions for funding the wallet."""
        print("\n" + "="*70)
        print("💰 WALLET FUNDING INSTRUCTIONS")
        print("="*70)
        print(f"📍 Wallet Address: {self.wallet_address}")
        print()
        print("🚀 FUNDING OPTIONS:")
        print()
        print("1️⃣ EXCHANGE TRANSFER (Recommended)")
        print("   • Send SOL from Coinbase, Binance, etc.")
        print("   • Use the wallet address above")
        print("   • Minimum: 0.1 SOL for testing")
        print("   • Recommended: 5-20 SOL for trading")
        print()
        print("2️⃣ SOLANA CLI (If you have another wallet)")
        print(f"   solana transfer {self.wallet_address} 1 --allow-unfunded-recipient")
        print()
        print("3️⃣ PHANTOM/SOLFLARE WALLET")
        print("   • Send SOL to the address above")
        print("   • Make sure you're on Solana mainnet")
        print()
        print("💡 TRADING RECOMMENDATIONS:")
        print("   • Minimum for testing: 0.5 SOL (~$75)")
        print("   • Recommended for trading: 10+ SOL (~$1,500)")
        print("   • Keep 0.1 SOL for transaction fees")
        print()
        print("🔧 AFTER FUNDING:")
        print("   1. Check balance: python3 scripts/check_wallet_balance.py")
        print("   2. Create token accounts: python3 scripts/fund_native_wallet.py --setup")
        print("   3. Start trading: python3 scripts/unified_live_trading.py")
        print("="*70)
    
    def display_wallet_status(self, sol_balance, token_info):
        """Display current wallet status."""
        print("\n" + "="*70)
        print("📊 NATIVE WALLET STATUS")
        print("="*70)
        print(f"📍 Address: {self.wallet_address}")

        # Handle None balance gracefully
        if sol_balance is not None:
            print(f"💰 SOL Balance: {sol_balance:.6f} SOL (~${sol_balance * 151:.2f} USD)")
        else:
            print(f"💰 SOL Balance: Unable to fetch (wallet may be unfunded)")
        print()
        
        if token_info:
            print("📋 Token Accounts:")
            print(f"   WSOL: {'✅ Created' if token_info['wsol_exists'] else '❌ Not Created'}")
            if token_info['wsol_exists']:
                print(f"         Balance: {token_info['wsol_balance']:.6f} WSOL")
            print(f"   USDC: {'✅ Created' if token_info['usdc_exists'] else '❌ Not Created'}")
            if token_info['usdc_exists']:
                print(f"         Balance: {token_info['usdc_balance']:.6f} USDC")
        
        print()
        
        # Status assessment
        if sol_balance is not None and sol_balance >= 0.1:
            print("🟢 STATUS: Ready for trading!")
            if token_info and (not token_info['wsol_exists'] or not token_info['usdc_exists']):
                print("💡 Note: Token accounts will be created automatically during first trade")
        elif sol_balance is not None and sol_balance > 0:
            print("🟡 STATUS: Funded but needs more SOL for trading")
            print("💡 Recommended: Add more SOL for meaningful trading")
        else:
            print("🔴 STATUS: Wallet needs funding")
            print("💡 Send SOL to this address to start trading")
        
        print("="*70)

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Native wallet funding helper')
    parser.add_argument('--setup', action='store_true', help='Setup token accounts')
    parser.add_argument('--status', action='store_true', help='Show wallet status')
    parser.add_argument('--instructions', action='store_true', help='Show funding instructions')
    
    args = parser.parse_args()
    
    funder = NativeWalletFunder()
    
    if not funder.wallet_address:
        print("❌ No native wallet found!")
        print("💡 Create one first: python3 scripts/create_native_solana_wallet.py")
        return 1
    
    # Check current status
    sol_balance = await funder.check_wallet_balance()
    token_info = await funder.check_token_accounts()
    
    if args.setup:
        print("🔧 Setting up token accounts...")
        await funder.create_token_accounts_if_needed()
    elif args.instructions:
        funder.display_funding_instructions()
    elif args.status:
        funder.display_wallet_status(sol_balance, token_info)
    else:
        # Default: show status and instructions
        funder.display_wallet_status(sol_balance, token_info)
        
        if not sol_balance or sol_balance < 0.01:
            funder.display_funding_instructions()
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
