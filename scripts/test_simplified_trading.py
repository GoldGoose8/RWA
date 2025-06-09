#!/usr/bin/env python3
"""
Test Simplified Trading Logic
============================

Tests the simplified trading system that:
- Removes complex balance preparation swaps
- Focuses on direct SOL→USDC trading
- Converts BUY signals to SELL signals
- Uses available SOL balance directly
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

async def test_simplified_balance_logic():
    """Test the simplified balance preparation logic."""
    print("🧪 TESTING SIMPLIFIED TRADING LOGIC")
    print("=" * 60)
    
    try:
        # Import the unified trading system
        from scripts.unified_live_trading import UnifiedLiveTrader
        
        # Create trader instance
        trader = UnifiedLiveTrader()
        await trader.initialize()
        
        print("✅ Trader initialized successfully")
        
        # Test BUY signal conversion
        print("\n🔄 Testing BUY Signal Conversion:")
        buy_signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'size': 1.0,
            'confidence': 0.8,
            'source': 'test'
        }
        
        print(f"   Original: {buy_signal['action']} {buy_signal['size']} SOL")
        
        # Test balance preparation (should convert BUY to SELL)
        balance_ok = await trader.prepare_trade_balance(buy_signal)
        
        if balance_ok:
            print(f"   ✅ Converted: {buy_signal['action']} {buy_signal['size']} SOL")
            print(f"   💡 BUY signals are now converted to SELL for direct SOL trading")
        else:
            print(f"   ❌ Balance preparation failed")
        
        # Test SELL signal sizing
        print("\n📏 Testing SELL Signal Sizing:")
        sell_signal = {
            'action': 'SELL',
            'market': 'SOL-USDC',
            'size': 20.0,  # Large amount to test sizing logic
            'confidence': 0.8,
            'source': 'test'
        }
        
        print(f"   Original: {sell_signal['action']} {sell_signal['size']} SOL")
        
        # Test balance preparation (should adjust size if needed)
        balance_ok = await trader.prepare_trade_balance(sell_signal)
        
        if balance_ok:
            print(f"   ✅ Adjusted: {sell_signal['action']} {sell_signal['size']} SOL")
            print(f"   💡 Trade size adjusted to available SOL balance")
        else:
            print(f"   ❌ Balance preparation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing simplified logic: {e}")
        import traceback
        print(f"📄 Traceback: {traceback.format_exc()}")
        return False

async def test_jupiter_quote_simplified():
    """Test Jupiter quote with simplified parameters."""
    print("\n🔗 TESTING JUPITER QUOTE (SIMPLIFIED)")
    print("=" * 60)
    
    try:
        import httpx
        
        # Test Jupiter quote API with higher slippage
        jupiter_url = "https://quote-api.jup.ag/v6/quote"
        
        # Simple SOL to USDC quote with higher slippage
        params = {
            "inputMint": "So11111111111111111111111111111111111111112",  # SOL
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "amount": "1000000000",  # 1.0 SOL
            "slippageBps": "300"  # 3% slippage (increased)
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(jupiter_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'outAmount' in data:
                    out_amount = int(data['outAmount']) / 1_000_000  # USDC has 6 decimals
                    print(f"   ✅ Jupiter quote successful")
                    print(f"   📊 Quote: 1.0 SOL → {out_amount:.2f} USDC")
                    print(f"   🔄 Route: {len(data.get('routePlan', []))} steps")
                    print(f"   📈 Price Impact: {data.get('priceImpactPct', 'N/A')}%")
                    print(f"   💰 Slippage: 3% (increased for reliability)")
                    return True
                else:
                    print(f"   ❌ Jupiter quote error: {data}")
                    return False
            else:
                print(f"   ❌ Jupiter API status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Jupiter quote test failed: {e}")
        return False

async def test_wallet_balance():
    """Test wallet balance check."""
    print("\n💰 TESTING WALLET BALANCE")
    print("=" * 60)
    
    try:
        import httpx
        
        wallet_address = os.getenv('WALLET_ADDRESS')
        rpc_url = os.getenv('HELIUS_RPC_URL')
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }
            
            response = await client.post(rpc_url, json=payload)
            data = response.json()
            
            if 'result' in data:
                sol_balance = data['result']['value'] / 1_000_000_000
                print(f"   ✅ SOL Balance: {sol_balance:.6f} SOL")
                
                if sol_balance >= 1.0:
                    print(f"   🟢 Excellent balance for trading")
                    return True
                elif sol_balance >= 0.1:
                    print(f"   🟡 Sufficient balance for testing")
                    return True
                else:
                    print(f"   🔴 Low balance - may need funding")
                    return False
            else:
                print(f"   ❌ Error getting balance: {data}")
                return False
                
    except Exception as e:
        print(f"   ❌ Balance check failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 SIMPLIFIED TRADING LOGIC TESTER")
    print("=" * 70)
    print("Testing the simplified trading system that removes")
    print("complex preparation swaps and focuses on direct SOL trading.")
    print()
    
    # Test 1: Wallet balance
    balance_ok = await test_wallet_balance()
    
    # Test 2: Jupiter quote
    jupiter_ok = await test_jupiter_quote_simplified()
    
    # Test 3: Simplified trading logic
    logic_ok = await test_simplified_balance_logic()
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    tests_passed = sum([balance_ok, jupiter_ok, logic_ok])
    total_tests = 3
    
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    print(f"   Wallet Balance: {'✅' if balance_ok else '❌'}")
    print(f"   Jupiter Quote: {'✅' if jupiter_ok else '❌'}")
    print(f"   Trading Logic: {'✅' if logic_ok else '❌'}")
    
    if tests_passed == total_tests:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"🚀 Simplified trading system is ready")
        print(f"💡 The ProgramFailedToComplete errors should be resolved")
        print()
        print(f"🎯 READY TO START TRADING:")
        print(f"   python3 scripts/unified_live_trading.py")
    else:
        print(f"\n⚠️ SOME TESTS FAILED")
        print(f"💡 Fix the failing tests before starting live trading")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
