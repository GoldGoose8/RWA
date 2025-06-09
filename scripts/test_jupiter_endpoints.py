#!/usr/bin/env python3
"""
Jupiter Endpoints Test
======================

Test the corrected Jupiter v6 endpoints to ensure they're working properly
and diagnose any remaining issues with the shared_accounts_route error.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    import httpx
    import json
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    sys.exit(1)

async def test_jupiter_endpoints():
    """Test all Jupiter v6 endpoints."""
    
    load_dotenv()
    
    # Get configuration
    quote_endpoint = os.getenv("JUPITER_QUOTE_ENDPOINT")
    swap_endpoint = os.getenv("JUPITER_SWAP_ENDPOINT")
    slippage_bps = os.getenv("JUPITER_SLIPPAGE_BPS", "100")
    
    print("🔍 JUPITER V6 ENDPOINTS TEST")
    print("=" * 50)
    print(f"Quote Endpoint: {quote_endpoint}")
    print(f"Swap Endpoint: {swap_endpoint}")
    print(f"Slippage BPS: {slippage_bps}")
    print("")
    
    # Test parameters
    sol_mint = "So11111111111111111111111111111111111111112"
    usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    test_amount = "100000000"  # 0.1 SOL
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Quote Endpoint
        print("1️⃣ Testing Quote Endpoint...")
        try:
            quote_params = {
                "inputMint": sol_mint,
                "outputMint": usdc_mint,
                "amount": test_amount,
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": "true"
            }
            
            response = await client.get(quote_endpoint, params=quote_params)
            
            if response.status_code == 200:
                quote_data = response.json()
                print(f"   ✅ Quote successful")
                print(f"   📊 Input: {float(test_amount)/1e9:.3f} SOL")
                print(f"   📊 Output: {float(quote_data.get('outAmount', 0))/1e6:.6f} USDC")
                print(f"   📊 Price Impact: {quote_data.get('priceImpactPct', 0)}%")
                print(f"   📊 Route: {len(quote_data.get('routePlan', []))} steps")
                
                # Test 2: Swap Instructions Endpoint
                print("\n2️⃣ Testing Swap Instructions Endpoint...")
                try:
                    swap_payload = {
                        "quoteResponse": quote_data,
                        "userPublicKey": os.getenv("WALLET_ADDRESS"),
                        "wrapAndUnwrapSol": True,
                        "useSharedAccounts": True,  # This might be causing the issue
                        "feeAccount": None,
                        "computeUnitPriceMicroLamports": "auto",
                        "asLegacyTransaction": False
                    }
                    
                    swap_response = await client.post(
                        swap_endpoint,
                        json=swap_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if swap_response.status_code == 200:
                        swap_data = swap_response.json()
                        print(f"   ✅ Swap instructions successful")
                        print(f"   📊 Instructions: {len(swap_data.get('setupInstructions', []))} setup, {len(swap_data.get('swapInstruction', {}).get('accounts', []))} swap accounts")
                        print(f"   📊 Compute Units: {swap_data.get('computeUnitLimit', 'auto')}")
                        
                        # Check for shared accounts
                        if 'addressLookupTableAddresses' in swap_data:
                            print(f"   📊 Address Lookup Tables: {len(swap_data['addressLookupTableAddresses'])}")
                        
                    else:
                        print(f"   ❌ Swap instructions failed: {swap_response.status_code}")
                        print(f"   📄 Response: {swap_response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Swap instructions error: {e}")
                
            else:
                print(f"   ❌ Quote failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Quote error: {e}")
        
        # Test 3: Alternative Configuration
        print("\n3️⃣ Testing Alternative Configuration (No Shared Accounts)...")
        try:
            # Get quote again
            response = await client.get(quote_endpoint, params=quote_params)
            
            if response.status_code == 200:
                quote_data = response.json()
                
                # Try swap without shared accounts
                swap_payload = {
                    "quoteResponse": quote_data,
                    "userPublicKey": os.getenv("WALLET_ADDRESS"),
                    "wrapAndUnwrapSol": True,
                    "useSharedAccounts": False,  # Disable shared accounts
                    "feeAccount": None,
                    "computeUnitPriceMicroLamports": "auto",
                    "asLegacyTransaction": False
                }
                
                swap_response = await client.post(
                    swap_endpoint,
                    json=swap_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if swap_response.status_code == 200:
                    print(f"   ✅ Alternative config successful (no shared accounts)")
                    print(f"   💡 Recommendation: Disable shared accounts to avoid errors")
                else:
                    print(f"   ❌ Alternative config failed: {swap_response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ Alternative config error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 RECOMMENDATIONS:")
    print("1. Use onlyDirectRoutes=true for better reliability")
    print("2. Consider disabling useSharedAccounts if errors persist")
    print("3. Increase slippage to 1.0% (100 BPS) for better execution")
    print("4. Use versioned transactions (asLegacyTransaction=false)")

async def main():
    """Main function."""
    await test_jupiter_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
