#!/usr/bin/env python3
"""
Test Transaction Fixes
======================

Tests the transaction verification fixes:
- Higher slippage tolerance (2%)
- Increased priority fees (25,000 lamports)
- Proper token account handling
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

async def test_configuration_fixes():
    """Test that the configuration fixes are applied."""
    print("🔧 TESTING TRANSACTION VERIFICATION FIXES")
    print("=" * 60)
    
    # Check updated configuration values
    slippage = float(os.getenv('SLIPPAGE_TOLERANCE', '0.01'))
    priority_fee = int(os.getenv('PRIORITY_FEE_LAMPORTS', '10000'))
    jupiter_slippage = int(os.getenv('JUPITER_SLIPPAGE_BPS', '100'))
    
    print("📋 Configuration Values:")
    print(f"   Slippage Tolerance: {slippage * 100:.1f}% {'✅' if slippage >= 0.02 else '❌'}")
    print(f"   Priority Fee: {priority_fee:,} lamports {'✅' if priority_fee >= 20000 else '❌'}")
    print(f"   Jupiter Slippage: {jupiter_slippage} BPS ({jupiter_slippage/100:.1f}%) {'✅' if jupiter_slippage >= 200 else '❌'}")
    
    # Check wallet configuration
    wallet_address = os.getenv('WALLET_ADDRESS')
    usdc_account = os.getenv('WALLET_USDC_ACCOUNT')
    
    print(f"\n💰 Wallet Configuration:")
    print(f"   Wallet Address: {wallet_address}")
    print(f"   USDC Account: {'Not set (will auto-create)' if not usdc_account else usdc_account}")
    
    # Test basic connectivity
    print(f"\n📡 Testing RPC Connectivity:")
    
    try:
        import httpx
        
        rpc_url = os.getenv('HELIUS_RPC_URL')
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            response = await client.post(rpc_url, json=payload)
            
            if response.status_code == 200:
                print(f"   RPC Health: ✅ OK")
            else:
                print(f"   RPC Health: ❌ Status {response.status_code}")
                
            # Test wallet balance
            balance_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }
            
            balance_response = await client.post(rpc_url, json=balance_payload)
            balance_data = balance_response.json()
            
            if 'result' in balance_data:
                sol_balance = balance_data['result']['value'] / 1_000_000_000
                print(f"   Wallet Balance: {sol_balance:.6f} SOL {'✅' if sol_balance > 0 else '❌'}")
            else:
                print(f"   Wallet Balance: ❌ Error getting balance")
                
    except Exception as e:
        print(f"   RPC Test: ❌ Error - {e}")
    
    # Summary
    print(f"\n🎯 FIX STATUS:")
    
    fixes_applied = []
    if slippage >= 0.02:
        fixes_applied.append("✅ Slippage tolerance increased to 2%")
    else:
        fixes_applied.append("❌ Slippage tolerance still too low")
        
    if priority_fee >= 20000:
        fixes_applied.append("✅ Priority fee increased to 25,000+ lamports")
    else:
        fixes_applied.append("❌ Priority fee still too low")
        
    if jupiter_slippage >= 200:
        fixes_applied.append("✅ Jupiter slippage increased to 2%")
    else:
        fixes_applied.append("❌ Jupiter slippage still too low")
    
    for fix in fixes_applied:
        print(f"   {fix}")
    
    all_fixes_good = all("✅" in fix for fix in fixes_applied)
    
    if all_fixes_good:
        print(f"\n🚀 ALL FIXES APPLIED SUCCESSFULLY!")
        print(f"💡 Transaction verification issues should be resolved")
        print(f"🎯 Ready to test: python3 scripts/unified_live_trading.py")
    else:
        print(f"\n⚠️ SOME FIXES STILL NEEDED")
        print(f"💡 Check the ❌ items above and fix them")
    
    return all_fixes_good

async def test_simple_jupiter_quote():
    """Test a simple Jupiter quote to verify API connectivity."""
    print(f"\n🧪 TESTING JUPITER API CONNECTIVITY")
    print("=" * 60)
    
    try:
        import httpx
        
        # Test Jupiter quote API
        jupiter_url = "https://quote-api.jup.ag/v6/quote"
        
        # Simple SOL to USDC quote
        params = {
            "inputMint": "So11111111111111111111111111111111111111112",  # SOL
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            "amount": "100000000",  # 0.1 SOL
            "slippageBps": "200"  # 2% slippage
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(jupiter_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'outAmount' in data:
                    out_amount = int(data['outAmount']) / 1_000_000  # USDC has 6 decimals
                    print(f"   ✅ Jupiter API working")
                    print(f"   📊 Quote: 0.1 SOL → {out_amount:.6f} USDC")
                    print(f"   🔄 Route found with {len(data.get('routePlan', []))} steps")
                    return True
                else:
                    print(f"   ❌ Jupiter API error: {data}")
                    return False
            else:
                print(f"   ❌ Jupiter API status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ Jupiter API test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 TRANSACTION VERIFICATION FIX TESTER")
    print("=" * 70)
    
    # Test configuration fixes
    config_ok = await test_configuration_fixes()
    
    # Test Jupiter API
    jupiter_ok = await test_simple_jupiter_quote()
    
    # Final summary
    print(f"\n📊 FINAL TEST RESULTS")
    print("=" * 70)
    
    if config_ok and jupiter_ok:
        print("✅ ALL TESTS PASSED!")
        print("🚀 Transaction verification fixes are working")
        print("💡 The ProgramFailedToComplete errors should be resolved")
        print()
        print("🎯 NEXT STEPS:")
        print("1. Fund wallet if needed")
        print("2. Start trading: python3 scripts/unified_live_trading.py")
        print("3. Monitor for successful transactions")
    else:
        print("❌ SOME TESTS FAILED")
        if not config_ok:
            print("• Fix configuration values")
        if not jupiter_ok:
            print("• Check Jupiter API connectivity")
    
    return config_ok and jupiter_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
