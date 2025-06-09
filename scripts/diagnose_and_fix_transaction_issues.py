#!/usr/bin/env python3
"""
Transaction Issue Diagnostic and Fix Tool
=========================================

Diagnoses and fixes common transaction verification issues:
- ProgramFailedToComplete errors
- Account setup problems
- Slippage and timing issues
- RPC endpoint problems
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransactionDiagnosticTool:
    """Comprehensive transaction diagnostic and fix tool."""
    
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.rpc_url = os.getenv('HELIUS_RPC_URL', 'https://api.mainnet-beta.solana.com')
        
        # Token addresses
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
    async def check_wallet_and_accounts(self):
        """Check wallet balance and token account status."""
        print("🔍 WALLET AND ACCOUNT DIAGNOSTIC")
        print("=" * 60)
        
        try:
            import httpx
            
            # Check SOL balance
            async with httpx.AsyncClient(timeout=30.0) as client:
                sol_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }
                
                response = await client.post(self.rpc_url, json=sol_payload)
                data = response.json()
                
                if 'result' in data:
                    sol_balance = data['result']['value'] / 1_000_000_000
                    print(f"💰 SOL Balance: {sol_balance:.6f} SOL")
                    
                    if sol_balance < 0.01:
                        print("❌ CRITICAL: Insufficient SOL for transactions!")
                        print("💡 Solution: Fund wallet with at least 0.1 SOL")
                        return False
                    elif sol_balance < 0.1:
                        print("⚠️ WARNING: Low SOL balance for trading")
                else:
                    print(f"❌ Error getting SOL balance: {data}")
                    return False
                
                # Check token accounts
                await self.check_token_accounts(client)
                
                return True
                
        except Exception as e:
            print(f"❌ Error checking wallet: {e}")
            return False
    
    async def check_token_accounts(self, client):
        """Check if token accounts exist and are properly set up."""
        print(f"\n📋 TOKEN ACCOUNT STATUS:")
        
        # Get associated token addresses
        from solders.pubkey import Pubkey
        from solders.spl.associated_token_account import get_associated_token_address
        
        try:
            wallet_pubkey = Pubkey.from_string(self.wallet_address)
            usdc_mint = Pubkey.from_string(self.USDC_MINT)
            
            # Calculate USDC associated token account
            usdc_account = get_associated_token_address(wallet_pubkey, usdc_mint)
            print(f"   Expected USDC Account: {usdc_account}")
            
            # Check if USDC account exists
            usdc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [str(usdc_account), {"encoding": "base64"}]
            }
            
            response = await client.post(self.rpc_url, json=usdc_payload)
            data = response.json()
            
            if data.get('result', {}).get('value') is None:
                print("❌ USDC token account does not exist!")
                print("💡 Solution: Create USDC token account first")
                return False
            else:
                print("✅ USDC token account exists")
                
                # Check USDC balance
                balance_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountBalance",
                    "params": [str(usdc_account)]
                }
                
                balance_response = await client.post(self.rpc_url, json=balance_payload)
                balance_data = balance_response.json()
                
                if 'result' in balance_data:
                    usdc_amount = balance_data['result']['value']['amount']
                    usdc_decimals = balance_data['result']['value']['decimals']
                    usdc_balance = int(usdc_amount) / (10 ** usdc_decimals)
                    print(f"   USDC Balance: {usdc_balance:.6f} USDC")
                
            return True
            
        except Exception as e:
            print(f"❌ Error checking token accounts: {e}")
            return False
    
    async def create_usdc_token_account(self):
        """Create USDC token account if it doesn't exist."""
        print("\n🔧 CREATING USDC TOKEN ACCOUNT")
        print("=" * 60)
        
        try:
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.spl.associated_token_account import get_associated_token_address, create_associated_token_account
            from solders.spl.token import ID as TOKEN_PROGRAM_ID
            from solana.rpc.api import Client
            from solana.transaction import Transaction
            import base58
            
            # Initialize client and keypair
            client = Client(self.rpc_url)
            keypair_bytes = base58.b58decode(self.private_key)
            keypair = Keypair.from_bytes(keypair_bytes)
            
            wallet_pubkey = keypair.pubkey()
            usdc_mint = Pubkey.from_string(self.USDC_MINT)
            
            # Get associated token address
            usdc_account = get_associated_token_address(wallet_pubkey, usdc_mint)
            
            print(f"Creating USDC account: {usdc_account}")
            
            # Create instruction
            create_account_ix = create_associated_token_account(
                payer=wallet_pubkey,
                owner=wallet_pubkey,
                mint=usdc_mint
            )
            
            # Get recent blockhash
            recent_blockhash = client.get_latest_blockhash()
            
            # Create transaction
            transaction = Transaction()
            transaction.add(create_account_ix)
            transaction.recent_blockhash = recent_blockhash.value.blockhash
            transaction.fee_payer = wallet_pubkey
            
            # Sign transaction
            transaction.sign(keypair)
            
            # Send transaction
            result = client.send_transaction(transaction)
            
            if result.value:
                print(f"✅ USDC token account created successfully!")
                print(f"   Transaction: {result.value}")
                print(f"   Account: {usdc_account}")
                
                # Update environment variable
                from dotenv import set_key
                env_file = Path(__file__).parent.parent / '.env'
                set_key(env_file, 'WALLET_USDC_ACCOUNT', str(usdc_account))
                print(f"✅ Updated .env with USDC account address")
                
                return True
            else:
                print(f"❌ Failed to create USDC token account")
                return False
                
        except Exception as e:
            print(f"❌ Error creating USDC token account: {e}")
            return False
    
    async def test_simple_transaction(self):
        """Test a simple transaction to verify basic functionality."""
        print("\n🧪 TESTING SIMPLE TRANSACTION")
        print("=" * 60)
        
        try:
            # Test a simple SOL transfer to self (minimal amount)
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.system_program import transfer, TransferParams
            from solana.rpc.api import Client
            from solana.transaction import Transaction
            import base58
            
            # Initialize client and keypair
            client = Client(self.rpc_url)
            keypair_bytes = base58.b58decode(self.private_key)
            keypair = Keypair.from_bytes(keypair_bytes)
            
            wallet_pubkey = keypair.pubkey()
            
            # Create a minimal self-transfer (1 lamport)
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=wallet_pubkey,
                    to_pubkey=wallet_pubkey,
                    lamports=1
                )
            )
            
            # Get recent blockhash
            recent_blockhash = client.get_latest_blockhash()
            
            # Create transaction
            transaction = Transaction()
            transaction.add(transfer_ix)
            transaction.recent_blockhash = recent_blockhash.value.blockhash
            transaction.fee_payer = wallet_pubkey
            
            # Sign transaction
            transaction.sign(keypair)
            
            # Send transaction
            result = client.send_transaction(transaction)
            
            if result.value:
                print(f"✅ Simple transaction successful!")
                print(f"   Transaction: {result.value}")
                return True
            else:
                print(f"❌ Simple transaction failed")
                return False
                
        except Exception as e:
            print(f"❌ Error testing simple transaction: {e}")
            return False
    
    async def check_rpc_endpoints(self):
        """Check RPC endpoint health and performance."""
        print("\n📡 RPC ENDPOINT DIAGNOSTIC")
        print("=" * 60)
        
        endpoints = [
            ("QuickNode (Primary)", os.getenv('QUICKNODE_RPC_URL', 'Not configured')),
            ("Helius (Fallback)", self.rpc_url)
        ]
        
        import httpx
        
        for name, url in endpoints:
            if url == 'Not configured':
                print(f"   {name}: ❌ Not configured")
                continue
                
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    start_time = datetime.now()
                    
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getHealth"
                    }
                    
                    response = await client.post(url, json=payload)
                    end_time = datetime.now()
                    
                    latency = (end_time - start_time).total_seconds() * 1000
                    
                    if response.status_code == 200:
                        print(f"   {name}: ✅ Healthy ({latency:.0f}ms)")
                    else:
                        print(f"   {name}: ⚠️ Status {response.status_code}")
                        
            except Exception as e:
                print(f"   {name}: ❌ Error - {str(e)[:50]}")
    
    async def run_comprehensive_diagnostic(self):
        """Run complete diagnostic and provide fixes."""
        print("🔧 COMPREHENSIVE TRANSACTION DIAGNOSTIC TOOL")
        print("=" * 70)
        print(f"📍 Wallet: {self.wallet_address}")
        print(f"📡 RPC: {self.rpc_url}")
        print()
        
        # Step 1: Check wallet and accounts
        wallet_ok = await self.check_wallet_and_accounts()
        
        # Step 2: Check RPC endpoints
        await self.check_rpc_endpoints()
        
        # Step 3: Create token account if needed
        if not wallet_ok:
            print("\n🔧 ATTEMPTING TO FIX ISSUES...")
            account_created = await self.create_usdc_token_account()
            if account_created:
                wallet_ok = True
        
        # Step 4: Test simple transaction
        if wallet_ok:
            transaction_ok = await self.test_simple_transaction()
        else:
            transaction_ok = False
        
        # Step 5: Provide recommendations
        print("\n💡 DIAGNOSTIC RESULTS AND RECOMMENDATIONS")
        print("=" * 70)
        
        if wallet_ok and transaction_ok:
            print("✅ SYSTEM READY FOR TRADING!")
            print("🚀 All checks passed - transaction issues should be resolved")
            print()
            print("🔧 RECOMMENDED FIXES FOR TRADING:")
            print("1. Increase slippage tolerance: 1-2%")
            print("2. Use higher priority fees: 20,000+ lamports")
            print("3. Add transaction retry logic")
            print("4. Implement better error handling")
        else:
            print("❌ ISSUES DETECTED - MANUAL INTERVENTION REQUIRED")
            if not wallet_ok:
                print("• Fund wallet with SOL")
                print("• Create missing token accounts")
            if not transaction_ok:
                print("• Check RPC endpoint connectivity")
                print("• Verify wallet private key")
        
        print("\n🚀 NEXT STEPS:")
        print("1. Fix any issues above")
        print("2. Test with: python3 scripts/test_simple_swap.py")
        print("3. Start trading: python3 scripts/unified_live_trading.py")

async def main():
    """Main function."""
    diagnostic = TransactionDiagnosticTool()
    await diagnostic.run_comprehensive_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())
