#!/usr/bin/env python3
"""
Analyze Transaction Execution Issue
==================================

Investigate why profits aren't reaching the wallet by analyzing:
1. Transaction types being executed
2. Token account states
3. Actual vs expected token movements
4. Jupiter swap execution details
"""

import json
import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

async def analyze_transaction_execution():
    """Analyze why profits aren't reaching the wallet."""
    
    print("🔍 ANALYZING TRANSACTION EXECUTION ISSUE")
    print("=" * 50)
    
    load_dotenv()
    helius_url = f'https://mainnet.helius-rpc.com/?api-key={os.getenv("HELIUS_API_KEY")}'
    wallet = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
    
    # Check current token accounts
    print("💰 CURRENT TOKEN ACCOUNT ANALYSIS:")
    print("-" * 40)
    
    async with httpx.AsyncClient() as client:
        # Get all token accounts
        token_response = await client.post(helius_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'getTokenAccountsByOwner',
            'params': [
                wallet,
                {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'},
                {'encoding': 'jsonParsed'}
            ]
        })
        
        token_data = token_response.json()
        
        if 'result' in token_data and token_data['result']['value']:
            print(f"✅ Found {len(token_data['result']['value'])} token accounts:")
            
            for account in token_data['result']['value']:
                account_info = account['account']['data']['parsed']['info']
                mint = account_info['mint']
                balance = float(account_info['tokenAmount']['uiAmount'] or 0)
                
                # Identify token type
                if mint == 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':
                    token_name = 'USDC'
                elif mint == 'So11111111111111111111111111111111111111112':
                    token_name = 'SOL (wrapped)'
                else:
                    token_name = f'Unknown ({mint[:8]}...)'
                
                print(f"  {token_name}: {balance:.6f}")
                print(f"    Account: {account['pubkey']}")
                print(f"    Mint: {mint}")
                print()
        else:
            print("❌ No token accounts found or error retrieving them")
    
    # Analyze trade records for transaction patterns
    print("📊 TRADE EXECUTION PATTERN ANALYSIS:")
    print("-" * 40)
    
    trades_dir = Path("output/live_production/trades")
    trade_files = sorted(list(trades_dir.glob("trade_*.json")))
    
    if not trade_files:
        print("❌ No trade files found")
        return
    
    # Analyze first few trades in detail
    print("🔍 DETAILED TRANSACTION ANALYSIS (First 3 trades):")
    print("-" * 50)
    
    for i, trade_file in enumerate(trade_files[:3]):
        with open(trade_file, 'r') as f:
            trade_data = json.load(f)
        
        signal = trade_data.get('signal', {})
        result = trade_data.get('result', {})
        
        print(f"\n📋 TRADE {i+1}: {trade_file.name}")
        print(f"Action: {signal.get('action', 'N/A')}")
        print(f"Market: {signal.get('market', 'N/A')}")
        print(f"Size: {signal.get('size', 0):.6f} SOL")
        print(f"Price: ${signal.get('price', 0):.2f}")
        print(f"Signature: {result.get('signature', 'N/A')}")
        
        # Check what the transaction was supposed to do
        position_info = signal.get('position_info', {})
        print(f"Expected USD Value: ${position_info.get('position_size_usd', 0):.2f}")
        
        # Check if this is a BUY SOL transaction
        if signal.get('action') == 'BUY' and signal.get('market') == 'SOL-USDC':
            print("⚠️ WARNING: This is a BUY SOL transaction!")
            print("💡 Issue: Wallet already has SOL, so this might be:")
            print("   1. Converting SOL → USDC → SOL (net zero)")
            print("   2. Failing due to insufficient USDC")
            print("   3. Creating circular transactions")
    
    # Check what transactions should actually be doing
    print(f"\n🎯 TRANSACTION LOGIC ANALYSIS:")
    print("-" * 30)
    
    print("❌ IDENTIFIED ISSUE:")
    print("All trades are 'BUY SOL-USDC' but wallet already has SOL!")
    print()
    print("💡 EXPECTED BEHAVIOR FOR PROFIT:")
    print("1. Start with SOL")
    print("2. SELL SOL → USDC (when price is high)")
    print("3. BUY SOL ← USDC (when price is low)")
    print("4. Profit = price difference")
    print()
    print("❌ ACTUAL BEHAVIOR:")
    print("1. Start with SOL")
    print("2. BUY SOL with USDC (but no USDC available)")
    print("3. Transaction fails or becomes self-transfer")
    print("4. No profit generated")
    
    # Check if wallet has USDC to buy SOL with
    print(f"\n💰 USDC AVAILABILITY CHECK:")
    print("-" * 30)
    
    async with httpx.AsyncClient() as client:
        # Check USDC balance specifically
        usdc_response = await client.post(helius_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'getTokenAccountsByOwner',
            'params': [
                wallet,
                {'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'},
                {'encoding': 'jsonParsed'}
            ]
        })
        
        usdc_data = usdc_response.json()
        
        if 'result' in usdc_data and usdc_data['result']['value']:
            usdc_balance = float(usdc_data['result']['value'][0]['account']['data']['parsed']['info']['tokenAmount']['uiAmount'])
            print(f"✅ USDC Balance: {usdc_balance:.6f} USDC")
            
            if usdc_balance > 50:
                print("✅ Sufficient USDC for trading")
            else:
                print("⚠️ Low USDC balance - may explain transaction issues")
        else:
            print("❌ No USDC account found - explains why BUY SOL transactions fail!")
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    print("-" * 20)
    print("1. 🔄 Fix Strategy Logic:")
    print("   - Change from 'BUY SOL-USDC' to 'SELL SOL-USDC' when appropriate")
    print("   - Implement proper buy/sell signals based on price movements")
    print()
    print("2. 💰 Ensure Token Availability:")
    print("   - Verify USDC balance before BUY transactions")
    print("   - Verify SOL balance before SELL transactions")
    print()
    print("3. 🎯 Fix Transaction Building:")
    print("   - Build SELL SOL → USDC transactions for profit taking")
    print("   - Build BUY SOL ← USDC transactions for position entry")
    print()
    print("4. ✅ Implement Proper Profit Cycle:")
    print("   - SOL → USDC (sell high)")
    print("   - USDC → SOL (buy low)")
    print("   - Track profit in USDC accumulation")

if __name__ == "__main__":
    asyncio.run(analyze_transaction_execution())
