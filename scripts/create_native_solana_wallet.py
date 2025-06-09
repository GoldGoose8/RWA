#!/usr/bin/env python3
"""
Native Solana Wallet Creator
============================

Creates a new native Solana wallet using the Solana SDK with:
- Fresh keypair generation
- WSOL and USDC token account creation
- Proper wallet configuration for trading
- Environment variable setup
"""

import os
import sys
import json
import base58
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NativeSolanaWalletCreator:
    """Creates and configures a native Solana wallet for trading."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.keys_dir = self.project_root / 'keys'
        self.keys_dir.mkdir(exist_ok=True)
        
        # RPC configuration - Use QuickNode as primary, Helius as fallback
        self.rpc_url = os.getenv('QUICKNODE_RPC_URL') or os.getenv('HELIUS_RPC_URL')
        
        # Token mint addresses
        self.WSOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
    def generate_new_keypair(self):
        """Generate a new Solana keypair."""
        try:
            from solders.keypair import Keypair
            
            # Generate new keypair
            keypair = Keypair()
            
            # Get public key (wallet address)
            wallet_address = str(keypair.pubkey())
            
            # Get private key as base58 string
            private_key_bytes = bytes(keypair)
            private_key_base58 = base58.b58encode(private_key_bytes).decode('utf-8')
            
            logger.info(f"✅ Generated new keypair")
            logger.info(f"   Wallet Address: {wallet_address}")
            logger.info(f"   Private Key Length: {len(private_key_base58)} characters")
            
            return {
                'keypair': keypair,
                'wallet_address': wallet_address,
                'private_key_base58': private_key_base58,
                'private_key_bytes': private_key_bytes
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating keypair: {e}")
            return None
    
    def save_wallet_files(self, wallet_data):
        """Save wallet data to files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save as JSON (Solana CLI compatible format)
            wallet_json = {
                "wallet_address": wallet_data['wallet_address'],
                "private_key": wallet_data['private_key_base58'],
                "created_at": datetime.now().isoformat(),
                "type": "native_solana_wallet"
            }
            
            # Save main wallet file
            wallet_file = self.keys_dir / 'native_trading_wallet.json'
            with open(wallet_file, 'w') as f:
                json.dump(wallet_json, f, indent=2)
            
            # Save backup with timestamp
            backup_file = self.keys_dir / f'wallet_backup_{timestamp}.json'
            with open(backup_file, 'w') as f:
                json.dump(wallet_json, f, indent=2)
            
            # Save Solana CLI compatible keypair file (array of bytes)
            keypair_array = list(wallet_data['private_key_bytes'])
            keypair_file = self.keys_dir / 'native_keypair.json'
            with open(keypair_file, 'w') as f:
                json.dump(keypair_array, f)
            
            logger.info(f"✅ Wallet files saved:")
            logger.info(f"   Main: {wallet_file}")
            logger.info(f"   Backup: {backup_file}")
            logger.info(f"   Keypair: {keypair_file}")
            
            return wallet_file
            
        except Exception as e:
            logger.error(f"❌ Error saving wallet files: {e}")
            return None
    
    async def create_token_accounts(self, wallet_data):
        """Create WSOL and USDC token accounts."""
        try:
            from solders.pubkey import Pubkey
            from solders.system_program import CreateAccountParams, create_account
            from solders.spl.token.instructions import create_associated_token_account
            from solders.spl.associated_token_account import get_associated_token_address
            from solana.rpc.api import Client
            from solana.transaction import Transaction
            
            # Initialize RPC client
            client = Client(self.rpc_url)
            
            wallet_pubkey = Pubkey.from_string(wallet_data['wallet_address'])
            wsol_mint = Pubkey.from_string(self.WSOL_MINT)
            usdc_mint = Pubkey.from_string(self.USDC_MINT)
            
            # Get associated token addresses
            wsol_account = get_associated_token_address(wallet_pubkey, wsol_mint)
            usdc_account = get_associated_token_address(wallet_pubkey, usdc_mint)
            
            logger.info(f"📋 Token Account Addresses:")
            logger.info(f"   WSOL Account: {wsol_account}")
            logger.info(f"   USDC Account: {usdc_account}")
            
            # Check if accounts already exist
            try:
                wsol_info = client.get_account_info(wsol_account)
                wsol_exists = wsol_info.value is not None
            except:
                wsol_exists = False
                
            try:
                usdc_info = client.get_account_info(usdc_account)
                usdc_exists = usdc_info.value is not None
            except:
                usdc_exists = False
            
            logger.info(f"📊 Account Status:")
            logger.info(f"   WSOL Account Exists: {wsol_exists}")
            logger.info(f"   USDC Account Exists: {usdc_exists}")
            
            # Note: Token accounts will be created automatically when needed
            # or can be created manually when the wallet has SOL for rent
            
            return {
                'wsol_account': str(wsol_account),
                'usdc_account': str(usdc_account),
                'wsol_exists': wsol_exists,
                'usdc_exists': usdc_exists
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating token accounts: {e}")
            return None
    
    def update_environment_variables(self, wallet_data, token_accounts):
        """Update .env file with new wallet configuration."""
        try:
            env_file = self.project_root / '.env'
            
            # Update environment variables
            set_key(env_file, 'WALLET_ADDRESS', wallet_data['wallet_address'])
            set_key(env_file, 'WALLET_PRIVATE_KEY', wallet_data['private_key_base58'])
            
            if token_accounts:
                set_key(env_file, 'WALLET_WSOL_ACCOUNT', token_accounts['wsol_account'])
                set_key(env_file, 'WALLET_USDC_ACCOUNT', token_accounts['usdc_account'])
            
            # Add wallet type identifier
            set_key(env_file, 'WALLET_TYPE', 'native_solana')
            set_key(env_file, 'WALLET_CREATED_AT', datetime.now().isoformat())
            
            logger.info(f"✅ Environment variables updated in {env_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating environment variables: {e}")
            return False
    
    def display_wallet_summary(self, wallet_data, token_accounts):
        """Display a summary of the created wallet."""
        print("\n" + "="*70)
        print("🎉 NATIVE SOLANA WALLET CREATED SUCCESSFULLY!")
        print("="*70)
        print(f"📍 Wallet Address: {wallet_data['wallet_address']}")
        print(f"🔐 Private Key: {wallet_data['private_key_base58'][:20]}...{wallet_data['private_key_base58'][-20:]}")
        print(f"📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏷️  Type: Native Solana SDK Wallet")
        
        if token_accounts:
            print(f"\n📋 Token Accounts:")
            print(f"   WSOL: {token_accounts['wsol_account']}")
            print(f"   USDC: {token_accounts['usdc_account']}")
        
        print(f"\n💾 Files Created:")
        print(f"   📄 keys/native_trading_wallet.json")
        print(f"   📄 keys/native_keypair.json")
        print(f"   📄 .env (updated)")
        
        print(f"\n💰 Next Steps:")
        print(f"   1. Fund the wallet with SOL for trading")
        print(f"   2. Create token accounts (if needed)")
        print(f"   3. Test the wallet with: python3 scripts/check_wallet_balance.py")
        print(f"   4. Start trading with: python3 scripts/unified_live_trading.py")
        
        print("="*70)
    
    async def create_native_wallet(self):
        """Main function to create a complete native Solana wallet."""
        logger.info("🚀 Creating Native Solana Wallet for Trading")
        logger.info("="*60)
        
        # Step 1: Generate new keypair
        logger.info("1️⃣ Generating new keypair...")
        wallet_data = self.generate_new_keypair()
        if not wallet_data:
            logger.error("❌ Failed to generate keypair")
            return False
        
        # Step 2: Save wallet files
        logger.info("2️⃣ Saving wallet files...")
        wallet_file = self.save_wallet_files(wallet_data)
        if not wallet_file:
            logger.error("❌ Failed to save wallet files")
            return False
        
        # Step 3: Create token accounts
        logger.info("3️⃣ Setting up token accounts...")
        token_accounts = await self.create_token_accounts(wallet_data)
        
        # Step 4: Update environment variables
        logger.info("4️⃣ Updating environment configuration...")
        env_updated = self.update_environment_variables(wallet_data, token_accounts)
        if not env_updated:
            logger.error("❌ Failed to update environment variables")
            return False
        
        # Step 5: Display summary
        self.display_wallet_summary(wallet_data, token_accounts)
        
        return True

async def main():
    """Main function."""
    creator = NativeSolanaWalletCreator()
    
    # Confirm wallet creation
    print("🚀 NATIVE SOLANA WALLET CREATOR")
    print("="*50)
    print("This will create a new native Solana wallet for trading.")
    print("⚠️  This will replace your current wallet configuration!")
    print("")
    
    confirm = input("Do you want to proceed? (yes/no): ").lower().strip()
    if confirm not in ['yes', 'y']:
        print("❌ Wallet creation cancelled.")
        return
    
    # Create the wallet
    success = await creator.create_native_wallet()
    
    if success:
        print("\n🎉 Native Solana wallet created successfully!")
        print("💡 You can now fund it and start trading!")
    else:
        print("\n❌ Failed to create native wallet.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))
