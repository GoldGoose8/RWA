#!/usr/bin/env python3
"""
Quick script to check wallet SOL and USDC balances
"""

import asyncio
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_balances():
    """Check SOL and USDC balances"""
    
    wallet_address = "J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz"
    helius_api_key = os.getenv('HELIUS_API_KEY')
    rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"
    
    print(f"🔍 Checking balances for wallet: {wallet_address}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Check SOL balance
        sol_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }
        
        response = await client.post(rpc_url, json=sol_payload)
        response.raise_for_status()
        sol_result = response.json()
        
        if "result" in sol_result:
            sol_lamports = sol_result["result"]["value"]
            sol_balance = sol_lamports / 1_000_000_000
            print(f"💰 SOL Balance: {sol_balance:.9f} SOL (${sol_balance * 156:.2f} USD)")
        else:
            print(f"❌ Error getting SOL balance: {sol_result}")
        
        # Check USDC balance
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Get token accounts
        token_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"mint": usdc_mint},
                {"encoding": "jsonParsed"}
            ]
        }
        
        response = await client.post(rpc_url, json=token_payload)
        response.raise_for_status()
        token_result = response.json()
        
        if "result" in token_result and token_result["result"]["value"]:
            usdc_accounts = token_result["result"]["value"]
            total_usdc = 0
            
            print(f"💵 USDC Token Accounts Found: {len(usdc_accounts)}")
            
            for account in usdc_accounts:
                account_data = account["account"]["data"]["parsed"]["info"]
                usdc_amount = int(account_data["tokenAmount"]["amount"])
                usdc_balance = usdc_amount / 1_000_000  # USDC has 6 decimals
                total_usdc += usdc_balance
                
                print(f"   Account: {account['pubkey']}")
                print(f"   Balance: {usdc_balance:.6f} USDC")
            
            print(f"💵 Total USDC Balance: {total_usdc:.6f} USDC")
            
            if total_usdc < 50:
                print("⚠️  WARNING: Low USDC balance! Need USDC for swaps.")
                print("💡 Solution: Transfer some USDC to this wallet for trading")
            
        else:
            print("❌ No USDC token accounts found!")
            print("💡 Solution: You need to:")
            print("   1. Transfer some USDC to this wallet")
            print("   2. Or create a USDC token account")
        
        print("=" * 60)
        print("🎯 DIAGNOSIS:")
        
        if "result" in sol_result:
            sol_balance = sol_result["result"]["value"] / 1_000_000_000
            if sol_balance > 1.0:
                print("✅ SOL balance is sufficient for trading")
            else:
                print("⚠️  SOL balance is low")
        
        if "result" in token_result and token_result["result"]["value"]:
            print("✅ USDC token account exists")
            if total_usdc >= 50:
                print("✅ USDC balance is sufficient for trading")
            else:
                print("❌ USDC balance is too low for meaningful swaps")
                print("💡 Need at least $50-100 USDC for trading")
        else:
            print("❌ No USDC token account - this is why swaps are failing!")
            print("💡 The 'Custom Error 1' is because there's no USDC to swap")

if __name__ == "__main__":
    asyncio.run(check_balances())
