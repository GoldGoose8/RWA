#!/usr/bin/env python3
"""
Create USDC Token Account for Trading
=====================================

This script creates an Associated Token Account (ATA) for USDC if it doesn't exist.
This fixes the 'InvalidAccountData' error when trying to swap USDC.
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def check_usdc_token_account(wallet_address: str) -> bool:
    """Check if USDC token account exists for wallet."""
    helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
    usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(helius_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"mint": usdc_mint},
                {"encoding": "jsonParsed"}
            ]
        })
        
        data = response.json()
        if "result" in data and data["result"]["value"]:
            account = data["result"]["value"][0]
            balance = float(account["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"])
            print(f"✅ USDC token account exists with {balance:.6f} USDC")
            return True
        else:
            print("❌ No USDC token account found - this is causing InvalidAccountData error")
            return False

async def create_usdc_token_account():
    """Create USDC token account using Jupiter API."""
    try:
        # Get wallet info
        private_key = os.getenv('WALLET_PRIVATE_KEY')
        if not private_key:
            print("❌ WALLET_PRIVATE_KEY not found in environment")
            return False
            
        from solders.keypair import Keypair
        keypair = Keypair.from_base58_string(private_key)
        wallet_address = str(keypair.pubkey())
        
        print(f"🔧 Creating USDC token account for wallet: {wallet_address}")
        
        # Check if account already exists
        if await check_usdc_token_account(wallet_address):
            print("✅ USDC token account already exists - no action needed")
            return True
        
        # Create token account using Jupiter's create-account endpoint
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        async with httpx.AsyncClient() as client:
            # Use Jupiter's account creation
            response = await client.post("https://quote-api.jup.ag/v6/swap", json={
                "quoteResponse": {
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": usdc_mint,  # USDC
                    "inAmount": "1000000",  # 0.001 SOL (minimal amount)
                    "outAmount": "1",  # Minimal USDC
                    "otherAmountThreshold": "1",
                    "swapMode": "ExactIn",
                    "slippageBps": 50,
                    "platformFee": None,
                    "priceImpactPct": "0",
                    "routePlan": []
                },
                "userPublicKey": wallet_address,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": 10000,
                "asLegacyTransaction": False
            })
            
            if response.status_code == 200:
                swap_data = response.json()
                if "swapTransaction" in swap_data:
                    print("✅ Token account creation transaction built")
                    
                    # Sign and send transaction
                    import base64
                    from solders.transaction import VersionedTransaction
                    
                    tx_bytes = base64.b64decode(swap_data["swapTransaction"])
                    tx = VersionedTransaction.from_bytes(tx_bytes)
                    
                    # Sign transaction
                    signed_tx = VersionedTransaction(tx.message, [keypair])
                    signed_bytes = bytes(signed_tx)
                    
                    # Send transaction
                    helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
                    send_response = await client.post(helius_url, json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "sendTransaction",
                        "params": [
                            base64.b64encode(signed_bytes).decode(),
                            {"encoding": "base64", "skipPreflight": True}
                        ]
                    })
                    
                    send_data = send_response.json()
                    if "result" in send_data:
                        signature = send_data["result"]
                        print(f"✅ Token account creation transaction sent: {signature}")
                        print("⏳ Waiting for confirmation...")
                        
                        # Wait a bit for confirmation
                        await asyncio.sleep(5)
                        
                        # Check if account was created
                        if await check_usdc_token_account(wallet_address):
                            print("🎉 USDC token account created successfully!")
                            return True
                        else:
                            print("⚠️ Transaction sent but account not yet visible")
                            return False
                    else:
                        print(f"❌ Failed to send transaction: {send_data}")
                        return False
                else:
                    print(f"❌ No transaction in response: {swap_data}")
                    return False
            else:
                print(f"❌ Jupiter API error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error creating USDC token account: {e}")
        return False

async def main():
    """Main function."""
    print("🔧 USDC Token Account Creator")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get wallet address
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        print("❌ WALLET_PRIVATE_KEY not found in environment")
        return
        
    from solders.keypair import Keypair
    keypair = Keypair.from_base58_string(private_key)
    wallet_address = str(keypair.pubkey())
    
    print(f"🔍 Checking wallet: {wallet_address}")
    
    # Check current status
    has_account = await check_usdc_token_account(wallet_address)
    
    if not has_account:
        print("\n💡 SOLUTION: Creating USDC token account...")
        success = await create_usdc_token_account()
        
        if success:
            print("\n✅ SUCCESS: USDC token account created!")
            print("✅ You can now execute USDC swaps without InvalidAccountData errors")
        else:
            print("\n❌ FAILED: Could not create USDC token account")
            print("💡 Try transferring some USDC to your wallet first")
    else:
        print("\n✅ USDC token account already exists - ready for trading!")

if __name__ == "__main__":
    asyncio.run(main())
