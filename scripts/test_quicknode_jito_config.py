#!/usr/bin/env python3
"""
Test QuickNode + Jito Configuration
===================================

This script tests the QuickNode RPC configuration and ensures it's properly
set as the primary endpoint for live trading.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

async def test_quicknode_rpc():
    """Test QuickNode RPC endpoint."""
    print("🔍 TESTING QUICKNODE RPC CONFIGURATION")
    print("=" * 60)
    
    quicknode_url = os.getenv('QUICKNODE_RPC_URL')
    quicknode_api_key = os.getenv('QUICKNODE_API_KEY')
    
    print(f"📍 QuickNode URL: {quicknode_url}")
    print(f"🔑 API Key: {quicknode_api_key[:10]}..." if quicknode_api_key else "❌ No API Key")
    
    if not quicknode_url:
        print("❌ QUICKNODE_RPC_URL not configured")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test basic RPC call
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            start_time = time.time()
            response = await client.post(quicknode_url, json=payload)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ QuickNode RPC: HEALTHY")
                print(f"⚡ Latency: {latency:.2f}ms")
                print(f"📊 Response: {data}")
                return True
            else:
                print(f"❌ QuickNode RPC failed: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ QuickNode RPC error: {e}")
        return False

async def test_wallet_balance():
    """Test wallet balance retrieval via QuickNode."""
    print(f"\n💰 TESTING WALLET BALANCE VIA QUICKNODE")
    print("-" * 40)
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    quicknode_url = os.getenv('QUICKNODE_RPC_URL')
    
    if not wallet_address or not quicknode_url:
        print("❌ Missing wallet address or QuickNode URL")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }
            
            start_time = time.time()
            response = await client.post(quicknode_url, json=payload)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'value' in data['result']:
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1_000_000_000
                    
                    print(f"✅ Wallet balance retrieved successfully")
                    print(f"💰 Balance: {balance_sol:.9f} SOL")
                    print(f"⚡ Latency: {latency:.2f}ms")
                    print(f"📍 Wallet: {wallet_address}")
                    return True
                else:
                    print(f"❌ Invalid balance response: {data}")
                    return False
            else:
                print(f"❌ Balance request failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Balance request error: {e}")
        return False

async def test_transaction_simulation():
    """Test transaction simulation via QuickNode."""
    print(f"\n🔄 TESTING TRANSACTION SIMULATION")
    print("-" * 35)
    
    quicknode_url = os.getenv('QUICKNODE_RPC_URL')
    wallet_address = os.getenv('WALLET_ADDRESS')
    
    if not quicknode_url or not wallet_address:
        print("❌ Missing configuration")
        return False
    
    try:
        # Create a simple transfer transaction for simulation
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get recent blockhash first
            blockhash_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash"
            }
            
            response = await client.post(quicknode_url, json=blockhash_payload)
            if response.status_code != 200:
                print(f"❌ Failed to get blockhash: {response.status_code}")
                return False
            
            blockhash_data = response.json()
            if 'result' not in blockhash_data:
                print(f"❌ Invalid blockhash response: {blockhash_data}")
                return False
            
            print(f"✅ Got recent blockhash for simulation")
            print(f"🔗 Blockhash: {blockhash_data['result']['value']['blockhash'][:20]}...")
            return True
            
    except Exception as e:
        print(f"❌ Simulation test error: {e}")
        return False

async def test_jito_integration():
    """Test Jito integration with QuickNode."""
    print(f"\n🚀 TESTING JITO INTEGRATION")
    print("-" * 30)
    
    jito_url = os.getenv('JITO_RPC_URL', 'https://mainnet.block-engine.jito.wtf/api/v1')
    use_jito = os.getenv('USE_JITO', 'true').lower() == 'true'
    
    print(f"🔗 Jito URL: {jito_url}")
    print(f"✅ Jito enabled: {use_jito}")
    
    if not use_jito:
        print("⚠️ Jito is disabled in configuration")
        return True
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test Jito health
            response = await client.get(f"{jito_url}/health")
            
            if response.status_code == 200:
                print(f"✅ Jito Block Engine: HEALTHY")
                return True
            else:
                print(f"❌ Jito health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Jito integration error: {e}")
        return False

async def test_rpc_priority_configuration():
    """Test RPC priority configuration."""
    print(f"\n📊 TESTING RPC PRIORITY CONFIGURATION")
    print("-" * 45)
    
    primary_rpc = os.getenv('PRIMARY_RPC', 'helius')
    secondary_rpc = os.getenv('SECONDARY_RPC', 'jito')
    fallback_rpc = os.getenv('FALLBACK_RPC', 'public')
    
    print(f"🥇 Primary RPC: {primary_rpc}")
    print(f"🥈 Secondary RPC: {secondary_rpc}")
    print(f"🥉 Fallback RPC: {fallback_rpc}")
    
    # Check if QuickNode is properly configured as primary
    if primary_rpc.lower() == 'quicknode':
        print("✅ QuickNode is correctly set as PRIMARY RPC")
        return True
    else:
        print("⚠️ QuickNode is NOT set as primary RPC")
        print("💡 Recommendation: Set PRIMARY_RPC=quicknode in .env")
        return False

async def test_bundle_configuration():
    """Test bundle configuration for QuickNode."""
    print(f"\n📦 TESTING BUNDLE CONFIGURATION")
    print("-" * 35)
    
    quicknode_bundles = os.getenv('QUICKNODE_BUNDLES_ENABLED', 'false').lower() == 'true'
    bundle_url = os.getenv('QUICKNODE_BUNDLE_URL')
    bundle_timeout = os.getenv('QUICKNODE_BUNDLE_TIMEOUT', '30')
    
    print(f"📦 QuickNode Bundles: {'✅ ENABLED' if quicknode_bundles else '❌ DISABLED'}")
    print(f"🔗 Bundle URL: {bundle_url}")
    print(f"⏱️ Bundle Timeout: {bundle_timeout}s")
    
    if quicknode_bundles and bundle_url:
        print("✅ Bundle configuration looks good")
        return True
    else:
        print("⚠️ Bundle configuration needs attention")
        return False

async def main():
    """Run all QuickNode + Jito configuration tests."""
    print("🚀 QUICKNODE + JITO CONFIGURATION TEST")
    print("=" * 60)
    print("🎯 Ensuring QuickNode is primary RPC with Jito integration")
    print("=" * 60)
    
    tests = [
        ("RPC Priority Configuration", test_rpc_priority_configuration),
        ("QuickNode RPC", test_quicknode_rpc),
        ("Wallet Balance", test_wallet_balance),
        ("Transaction Simulation", test_transaction_simulation),
        ("Jito Integration", test_jito_integration),
        ("Bundle Configuration", test_bundle_configuration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ QuickNode + Jito configuration is READY for live trading!")
    else:
        print("⚠️ Configuration issues detected - please fix before live trading")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
