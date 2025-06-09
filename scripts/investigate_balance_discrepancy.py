#!/usr/bin/env python3
"""
Investigate Balance Discrepancy
==============================

Check if the reported loss is actually from trading or from initial USDC→SOL swap.
Also check for Phantom wallet sync delays.
"""

import json
import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

async def get_current_balances():
    """Get current wallet balances."""
    load_dotenv()
    helius_url = f'https://mainnet.helius-rpc.com/?api-key={os.getenv("HELIUS_API_KEY")}'
    wallet = 'J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz'
    
    async with httpx.AsyncClient() as client:
        # Get SOL balance
        sol_response = await client.post(helius_url, json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'getBalance',
            'params': [wallet]
        })
        
        sol_data = sol_response.json()
        sol_balance = sol_data['result']['value'] / 1_000_000_000
        
        # Get USDC balance
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
        usdc_balance = 0
        if 'result' in usdc_data and usdc_data['result']['value']:
            usdc_balance = float(usdc_data['result']['value'][0]['account']['data']['parsed']['info']['tokenAmount']['uiAmount'])
        
        return sol_balance, usdc_balance

def analyze_trade_pattern():
    """Analyze the trade pattern to understand what happened."""
    
    print("🔍 INVESTIGATING BALANCE DISCREPANCY")
    print("=" * 50)
    
    # Get trade files
    trades_dir = Path("output/live_production/trades")
    trade_files = sorted(list(trades_dir.glob("trade_*.json")))
    
    print(f"📁 Found {len(trade_files)} trade records")
    
    if not trade_files:
        print("❌ No trade files found")
        return
    
    # Analyze first few and last few trades
    print("\n🔍 FIRST 3 TRADES:")
    print("-" * 20)
    
    for i, trade_file in enumerate(trade_files[:3]):
        with open(trade_file, 'r') as f:
            trade_data = json.load(f)
        
        balance_val = trade_data.get('balance_validation', {})
        signal = trade_data.get('signal', {})
        
        print(f"Trade {i+1}: {trade_file.name}")
        print(f"  Action: {signal.get('action', 'N/A')}")
        print(f"  Market: {signal.get('market', 'N/A')}")
        print(f"  Size: {signal.get('size', 0):.6f} SOL")
        print(f"  USD Value: ${signal.get('position_info', {}).get('position_size_usd', 0):.2f}")
        print(f"  Balance Before: {balance_val.get('balance_before', 0):.9f} SOL")
        print(f"  Balance After: {balance_val.get('balance_after', 0):.9f} SOL")
        print(f"  Balance Change: {balance_val.get('balance_change', 0):.9f} SOL")
        print()
    
    print("\n🔍 LAST 3 TRADES:")
    print("-" * 20)
    
    for i, trade_file in enumerate(trade_files[-3:]):
        with open(trade_file, 'r') as f:
            trade_data = json.load(f)
        
        balance_val = trade_data.get('balance_validation', {})
        signal = trade_data.get('signal', {})
        
        print(f"Trade {len(trade_files)-2+i}: {trade_file.name}")
        print(f"  Action: {signal.get('action', 'N/A')}")
        print(f"  Market: {signal.get('market', 'N/A')}")
        print(f"  Size: {signal.get('size', 0):.6f} SOL")
        print(f"  USD Value: ${signal.get('position_info', {}).get('position_size_usd', 0):.2f}")
        print(f"  Balance Before: {balance_val.get('balance_before', 0):.9f} SOL")
        print(f"  Balance After: {balance_val.get('balance_after', 0):.9f} SOL")
        print(f"  Balance Change: {balance_val.get('balance_change', 0):.9f} SOL")
        print()
    
    # Check for balance inconsistencies
    print("\n🔍 BALANCE CONSISTENCY CHECK:")
    print("-" * 30)
    
    first_trade = trade_files[0]
    last_trade = trade_files[-1]
    
    with open(first_trade, 'r') as f:
        first_data = json.load(f)
    with open(last_trade, 'r') as f:
        last_data = json.load(f)
    
    first_balance = first_data.get('balance_validation', {}).get('balance_before', 0)
    last_balance = last_data.get('balance_validation', {}).get('balance_after', 0)
    
    print(f"First Trade Balance: {first_balance:.9f} SOL")
    print(f"Last Trade Balance: {last_balance:.9f} SOL")
    print(f"Recorded Change: {last_balance - first_balance:.9f} SOL")
    
    # Check if all trades are BUY SOL-USDC (which would be self-swaps)
    all_actions = []
    all_markets = []
    
    for trade_file in trade_files:
        with open(trade_file, 'r') as f:
            trade_data = json.load(f)
        signal = trade_data.get('signal', {})
        all_actions.append(signal.get('action', 'N/A'))
        all_markets.append(signal.get('market', 'N/A'))
    
    unique_actions = set(all_actions)
    unique_markets = set(all_markets)
    
    print(f"\n🔍 TRADE PATTERN ANALYSIS:")
    print("-" * 25)
    print(f"Unique Actions: {unique_actions}")
    print(f"Unique Markets: {unique_markets}")
    print(f"All BUY SOL-USDC: {unique_actions == {'BUY'} and unique_markets == {'SOL-USDC'}}")
    
    if unique_actions == {'BUY'} and unique_markets == {'SOL-USDC'}:
        print("⚠️ WARNING: All trades are BUY SOL-USDC - these might be self-swaps!")
        print("💡 This could explain why balance doesn't change much per trade")

async def main():
    """Main investigation function."""
    
    # Analyze trade pattern first
    analyze_trade_pattern()
    
    # Get current balances
    print("\n💰 CURRENT WALLET BALANCES:")
    print("-" * 30)
    
    try:
        sol_balance, usdc_balance = await get_current_balances()
        
        print(f"Wallet: J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz")
        print(f"SOL Balance: {sol_balance:.9f} SOL")
        print(f"USDC Balance: {usdc_balance:.6f} USDC")
        print(f"SOL in USD (~$157): ${sol_balance * 157:.2f}")
        print(f"Total Value: ${(sol_balance * 157) + usdc_balance:.2f} USD")
        
        # Compare with last recorded balance
        trades_dir = Path("output/live_production/trades")
        trade_files = sorted(list(trades_dir.glob("trade_*.json")))
        
        if trade_files:
            with open(trade_files[-1], 'r') as f:
                last_trade = json.load(f)
            
            last_recorded = last_trade.get('balance_validation', {}).get('balance_after', 0)
            
            print(f"\n📊 BALANCE COMPARISON:")
            print("-" * 22)
            print(f"Last Recorded: {last_recorded:.9f} SOL")
            print(f"Current Actual: {sol_balance:.9f} SOL")
            print(f"Difference: {sol_balance - last_recorded:.9f} SOL")
            
            if abs(sol_balance - last_recorded) > 0.001:
                print("⚠️ SIGNIFICANT DIFFERENCE DETECTED!")
                print("💡 This could indicate Phantom wallet sync delay or additional transactions")
            else:
                print("✅ Balances match closely")
        
    except Exception as e:
        print(f"❌ Error getting current balances: {e}")
    
    print(f"\n🎯 INVESTIGATION SUMMARY:")
    print("-" * 25)
    print("1. Check if all trades are BUY SOL-USDC (self-swaps)")
    print("2. Compare recorded vs actual current balance")
    print("3. Look for Phantom wallet sync delays")
    print("4. Verify if 'loss' is actually from initial USDC→SOL conversion")

if __name__ == "__main__":
    asyncio.run(main())
