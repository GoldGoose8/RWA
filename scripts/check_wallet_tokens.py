#!/usr/bin/env python3
"""
Check Wallet Token Accounts
===========================

Check all token accounts in the wallet to see USDC balance.
"""

import os
import asyncio
import httpx
from solders.keypair import Keypair

async def check_wallet_tokens():
    """Check all token accounts in the wallet."""
    
    # Get wallet address
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        print("❌ WALLET_PRIVATE_KEY not found in environment")
        return
        
    keypair = Keypair.from_base58_string(private_key)
    wallet_address = str(keypair.pubkey())
    
    print(f"🔍 Checking wallet: {wallet_address}")
    
    # Check all token accounts
    async with httpx.AsyncClient() as client:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"}
            ]
        }
        
        try:
            response = await client.post(
                "https://mainnet.helius-rpc.com/?api-key=dda9f776-9a40-447d-9ca4-22a27c21169e",
                json=request,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                accounts = result.get("result", {}).get("value", [])
                
                print(f"📊 Found {len(accounts)} token accounts:")
                print("=" * 60)
                
                usdc_found = False
                
                for account in accounts:
                    try:
                        account_info = account["account"]["data"]["parsed"]["info"]
                        mint = account_info["mint"]
                        balance = float(account_info["tokenAmount"]["uiAmount"] or 0)
                        decimals = account_info["tokenAmount"]["decimals"]
                        raw_amount = account_info["tokenAmount"]["amount"]
                        
                        # Check if this is USDC
                        if mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":
                            usdc_found = True
                            print(f"💰 USDC ACCOUNT FOUND!")
                            print(f"   Account Address: {account['pubkey']}")
                            print(f"   Balance: {balance:.6f} USDC")
                            print(f"   Decimals: {decimals}")
                            print(f"   Raw Amount: {raw_amount}")
                            print(f"   ✅ This account should work for trading!")
                        else:
                            # Try to identify other common tokens
                            token_name = "Unknown"
                            if mint == "So11111111111111111111111111111111111111112":
                                token_name = "Wrapped SOL"
                            elif mint == "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB":
                                token_name = "USDT"
                            elif mint == "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R":
                                token_name = "RAY"
                            
                            print(f"🪙 {token_name} ({mint[:8]}...): {balance:.6f}")
                    
                    except Exception as e:
                        print(f"⚠️ Error parsing account: {e}")
                
                if not usdc_found:
                    print("\n❌ NO USDC ACCOUNT FOUND!")
                    print("   This explains why the transaction failed with InvalidAccountData")
                    print("   You need to create a USDC token account first")
                else:
                    print(f"\n✅ USDC account exists with {balance:.6f} USDC")
                    print("   The transaction should work - there might be another issue")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking wallet: {e}")

if __name__ == "__main__":
    asyncio.run(check_wallet_tokens())
