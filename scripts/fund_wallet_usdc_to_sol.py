#!/usr/bin/env python3
"""
🚀 WALLET FUNDING SCRIPT: USDC → SOL
Convert USDC back to SOL to enable scaled trading parameters
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
from core.notifications.telegram_notifier import TelegramNotifier
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base58

async def get_usdc_balance(wallet_address: str) -> float:
    """Get USDC balance for wallet"""
    helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
    
    # USDC mint address
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
            token_account = data["result"]["value"][0]
            balance = float(token_account["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"])
            return balance
        return 0.0

async def fund_wallet_with_sol():
    """Convert USDC to SOL for scaled trading"""
    
    print("🚀 WALLET FUNDING: Converting USDC → SOL for Scaled Trading")
    print("=" * 60)
    
    # Load wallet
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        print("❌ WALLET_PRIVATE_KEY not found in environment")
        return
    
    try:
        keypair = Keypair.from_base58_string(private_key)
        wallet_address = str(keypair.pubkey())
        print(f"✅ Wallet loaded: {wallet_address}")
    except Exception as e:
        print(f"❌ Failed to load wallet: {e}")
        return
    
    # Get current USDC balance
    usdc_balance = await get_usdc_balance(wallet_address)
    print(f"💰 Current USDC balance: {usdc_balance:.2f} USDC")
    
    if usdc_balance < 50:
        print(f"❌ Insufficient USDC balance for meaningful swap (need >50 USDC)")
        return
    
    # Calculate swap amount (leave 10 USDC for fees/buffer)
    swap_amount = max(0, usdc_balance - 10)
    swap_amount_raw = int(swap_amount * 1_000_000)  # Convert to micro USDC
    
    print(f"🔄 Swapping {swap_amount:.2f} USDC → SOL")
    print(f"💰 Keeping 10 USDC as buffer")
    
    # Initialize Jupiter swap
    jupiter = JupiterSwapFallback()
    
    try:
        # Build USDC → SOL swap
        print("🪐 Building Jupiter USDC → SOL transaction...")
        
        # USDC to SOL
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        sol_mint = "So11111111111111111111111111111111111111112"
        
        # Get quote
        quote_url = f"https://quote-api.jup.ag/v6/quote"
        params = {
            "inputMint": usdc_mint,
            "outputMint": sol_mint,
            "amount": swap_amount_raw,
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
            
            print(f"✅ Jupiter quote: {swap_amount:.2f} USDC → {sol_amount:.6f} SOL")
            
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
            
            # Get fresh blockhash and sign
            helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
            
            blockhash_response = await client.post(helius_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash"
            })
            
            blockhash_data = blockhash_response.json()
            fresh_blockhash = blockhash_data["result"]["value"]["blockhash"]
            
            print(f"✅ Fresh blockhash obtained: {fresh_blockhash}")
            
            # Execute transaction
            executor = ModernTransactionExecutor()
            
            # Submit transaction
            tx_response = await client.post(helius_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    swap_data["swapTransaction"],
                    {"encoding": "base64", "maxRetries": 3}
                ]
            })
            
            tx_data = tx_response.json()
            
            if "error" in tx_data:
                print(f"❌ Transaction error: {tx_data['error']}")
                return
            
            signature = tx_data["result"]
            print(f"✅ Transaction submitted: {signature}")
            
            # Wait for confirmation
            print("⏳ Waiting for transaction confirmation...")
            await asyncio.sleep(5)
            
            # Check final balances
            final_usdc = await get_usdc_balance(wallet_address)
            
            # Get SOL balance
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
            print(f"💵 Final USDC balance: {final_usdc:.2f} USDC")
            print(f"🔗 Transaction: https://solscan.io/tx/{signature}")
            print("\n🚀 Wallet is now funded for scaled trading!")
            
            # Send Telegram notification
            try:
                notifier = TelegramNotifier()
                await notifier.send_message(
                    f"🚀 WALLET FUNDED FOR SCALING!\n\n"
                    f"💰 Swapped {swap_amount:.2f} USDC → {sol_amount:.6f} SOL\n"
                    f"📊 New SOL balance: {final_sol:.6f} SOL\n"
                    f"🔗 TX: {signature}\n\n"
                    f"✅ Ready for scaled trading parameters!"
                )
                print("📱 Telegram notification sent")
            except Exception as e:
                print(f"⚠️ Telegram notification failed: {e}")
            
    except Exception as e:
        print(f"❌ Funding failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fund_wallet_with_sol())
