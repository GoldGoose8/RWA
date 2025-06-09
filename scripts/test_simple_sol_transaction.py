#!/usr/bin/env python3
"""
Test Simple SOL Transaction
===========================

Tests a basic SOL transaction to verify the wallet and RPC work correctly.
This helps isolate whether the issue is with Jupiter swaps or basic transactions.
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

async def test_simple_sol_transfer():
    """Test a simple SOL self-transfer to verify basic functionality."""
    print("🧪 TESTING SIMPLE SOL TRANSACTION")
    print("=" * 60)
    
    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solders.system_program import transfer, TransferParams
        from solana.rpc.api import Client
        from solana.transaction import Transaction
        import base58
        
        # Get wallet info
        wallet_address = os.getenv('WALLET_ADDRESS')
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        rpc_url = os.getenv('HELIUS_RPC_URL')
        
        print(f"📍 Wallet: {wallet_address}")
        print(f"📡 RPC: {rpc_url}")
        
        # Initialize client and keypair
        client = Client(rpc_url)
        keypair_bytes = base58.b58decode(private_key)
        keypair = Keypair.from_bytes(keypair_bytes)
        
        wallet_pubkey = keypair.pubkey()
        
        print(f"🔑 Keypair loaded successfully")
        
        # Check balance first
        balance_response = client.get_balance(wallet_pubkey)
        if balance_response.value:
            sol_balance = balance_response.value / 1_000_000_000
            print(f"💰 Current balance: {sol_balance:.6f} SOL")
            
            if sol_balance < 0.001:
                print("❌ Insufficient balance for test transaction")
                return False
        else:
            print("❌ Could not get wallet balance")
            return False
        
        # Create a minimal self-transfer (1000 lamports = 0.000001 SOL)
        print(f"🔄 Creating self-transfer of 0.000001 SOL...")
        
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=wallet_pubkey,
                to_pubkey=wallet_pubkey,
                lamports=1000  # 0.000001 SOL
            )
        )
        
        # Get recent blockhash
        recent_blockhash_response = client.get_latest_blockhash()
        if not recent_blockhash_response.value:
            print("❌ Could not get recent blockhash")
            return False
        
        recent_blockhash = recent_blockhash_response.value.blockhash
        print(f"🔗 Got recent blockhash: {str(recent_blockhash)[:20]}...")
        
        # Create transaction
        transaction = Transaction()
        transaction.add(transfer_ix)
        transaction.recent_blockhash = recent_blockhash
        transaction.fee_payer = wallet_pubkey
        
        # Sign transaction
        transaction.sign(keypair)
        print(f"✅ Transaction signed")
        
        # Send transaction
        print(f"📤 Sending transaction...")
        result = client.send_transaction(transaction)
        
        if result.value:
            tx_signature = result.value
            print(f"✅ Transaction sent successfully!")
            print(f"📋 Transaction ID: {tx_signature}")
            print(f"🔗 Solscan: https://solscan.io/tx/{tx_signature}")
            
            # Wait a moment and check confirmation
            print(f"⏳ Waiting for confirmation...")
            await asyncio.sleep(3)
            
            # Check transaction status
            try:
                status_response = client.get_transaction(tx_signature)
                if status_response.value:
                    if status_response.value.meta and status_response.value.meta.err is None:
                        print(f"✅ Transaction confirmed successfully!")
                        return True
                    else:
                        print(f"❌ Transaction failed: {status_response.value.meta.err if status_response.value.meta else 'Unknown error'}")
                        return False
                else:
                    print(f"⏳ Transaction still pending...")
                    return True  # Sent successfully, even if not confirmed yet
            except Exception as e:
                print(f"⚠️ Could not check transaction status: {e}")
                return True  # Sent successfully
                
        else:
            print(f"❌ Failed to send transaction")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple SOL transaction test: {e}")
        import traceback
        print(f"📄 Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Main test function."""
    print("🚀 SIMPLE SOL TRANSACTION TESTER")
    print("=" * 70)
    print("This test verifies basic wallet and RPC functionality")
    print("by performing a minimal SOL self-transfer.")
    print()
    
    # Test simple SOL transaction
    success = await test_simple_sol_transfer()
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("=" * 70)
    
    if success:
        print("✅ SIMPLE SOL TRANSACTION SUCCESSFUL!")
        print("🎯 Basic wallet and RPC functionality is working")
        print("💡 The issue is likely with Jupiter swap complexity")
        print()
        print("🔧 RECOMMENDED FIXES:")
        print("1. Simplify Jupiter swap instructions")
        print("2. Increase compute unit limits")
        print("3. Use direct Orca swaps instead of Jupiter aggregation")
        print("4. Disable complex balance preparation")
    else:
        print("❌ SIMPLE SOL TRANSACTION FAILED!")
        print("🚨 Basic wallet or RPC functionality has issues")
        print("💡 Need to fix fundamental connectivity first")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
