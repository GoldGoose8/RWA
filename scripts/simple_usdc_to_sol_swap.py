#!/usr/bin/env python3
"""
🚀 SIMPLE USDC → SOL SWAP
Convert USDC back to SOL using existing Jupiter infrastructure
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from phase_4_deployment.utils.jupiter_swap_fallback import JupiterSwapFallback
from phase_4_deployment.rpc_execution.modern_transaction_executor import ModernTransactionExecutor
import httpx

async def simple_usdc_to_sol_swap():
    """Simple USDC to SOL swap using existing infrastructure"""
    
    print("🚀 SIMPLE USDC → SOL SWAP")
    print("=" * 40)
    
    # Create a manual signal for USDC → SOL
    signal = {
        'action': 'SELL',  # SELL USDC for SOL
        'market': 'USDC-SOL',
        'price': 160.0,
        'size': 200.0,  # 200 USDC
        'confidence': 0.9,
        'timestamp': '2025-05-30T14:30:00.000000',
        'source': 'manual_funding'
    }
    
    print(f"🔄 Manual swap signal: {signal['size']} USDC → SOL")
    
    try:
        # Initialize Jupiter swap
        jupiter = JupiterSwapFallback()
        
        # Build USDC → SOL transaction
        print("🪐 Building Jupiter USDC → SOL transaction...")
        
        # Convert to proper format for Jupiter
        usdc_amount = int(signal['size'] * 1_000_000)  # Convert to micro USDC
        
        # Get quote for USDC → SOL
        quote_url = "https://quote-api.jup.ag/v6/quote"
        params = {
            "inputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "outputMint": "So11111111111111111111111111111111111111112",   # SOL
            "amount": usdc_amount,
            "slippageBps": 50,
            "onlyDirectRoutes": False,
            "asLegacyTransaction": True
        }
        
        async with httpx.AsyncClient() as client:
            quote_response = await client.get(quote_url, params=params)
            quote_data = quote_response.json()
            
            if "error" in quote_data:
                print(f"❌ Jupiter quote error: {quote_data['error']}")
                return
            
            output_amount = int(quote_data["outAmount"])
            sol_amount = output_amount / 1_000_000_000  # Convert from lamports
            
            print(f"✅ Jupiter quote: {signal['size']:.2f} USDC → {sol_amount:.6f} SOL")
            
            # Get wallet address
            private_key = os.getenv('WALLET_PRIVATE_KEY')
            from solders.keypair import Keypair
            keypair = Keypair.from_base58_string(private_key)
            wallet_address = str(keypair.pubkey())
            
            # Build swap transaction
            swap_response = await client.post("https://quote-api.jup.ag/v6/swap", json={
                "quoteResponse": quote_data,
                "userPublicKey": wallet_address,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": 10000
            })
            
            swap_data = swap_response.json()
            
            if "error" in swap_data:
                print(f"❌ Jupiter swap error: {swap_data['error']}")
                return
            
            print("✅ Jupiter swap transaction built")
            
            # Get fresh blockhash
            helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
            
            blockhash_response = await client.post(helius_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash"
            })
            
            blockhash_data = blockhash_response.json()
            fresh_blockhash = blockhash_data["result"]["value"]["blockhash"]
            
            print(f"✅ Fresh blockhash: {fresh_blockhash}")
            
            # Submit transaction directly
            print("🚀 Submitting transaction...")
            
            tx_response = await client.post(helius_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    swap_data["swapTransaction"],
                    {
                        "encoding": "base64",
                        "maxRetries": 3,
                        "skipPreflight": True
                    }
                ]
            })
            
            tx_data = tx_response.json()
            
            if "error" in tx_data:
                print(f"❌ Transaction error: {tx_data['error']}")
                return
            
            signature = tx_data["result"]
            print(f"✅ Transaction submitted: {signature}")
            
            # Wait for confirmation
            print("⏳ Waiting for confirmation...")
            await asyncio.sleep(10)
            
            # Check final balances
            sol_response = await client.post(helius_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            })
            
            sol_data = sol_response.json()
            final_sol = sol_data["result"]["value"] / 1_000_000_000
            
            print("\n🎉 WALLET FUNDING COMPLETE!")
            print("=" * 40)
            print(f"💰 Final SOL balance: {final_sol:.6f} SOL")
            print(f"🔗 Transaction: https://solscan.io/tx/{signature}")
            print("\n🚀 Wallet is now funded for scaled trading!")
            
    except Exception as e:
        print(f"❌ Funding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_usdc_to_sol_swap())
