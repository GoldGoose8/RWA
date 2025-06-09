#!/usr/bin/env python3
"""
Test Enhanced API Server
========================

Test script for the enhanced API server with live trading integration.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

class APITester:
    """Test the enhanced API server."""
    
    def __init__(self, base_url="http://localhost:8082"):
        self.base_url = base_url
        
    async def test_endpoint(self, endpoint, description):
        """Test a single API endpoint."""
        print(f"\n🔍 Testing {description}")
        print(f"📍 Endpoint: {endpoint}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success: {response.status_code}")
                    print(f"📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Show some key data
                    if isinstance(data, dict):
                        if 'timestamp' in data:
                            print(f"⏰ Timestamp: {data['timestamp']}")
                        if 'wallet' in data and 'balance' in data['wallet']:
                            print(f"💰 Wallet Balance: {data['wallet']['balance']} SOL")
                        if 'trading' in data and 'isActive' in data['trading']:
                            print(f"⚡ Trading Active: {data['trading']['isActive']}")
                        if 'market' in data and 'solPrice' in data['market']:
                            print(f"💲 SOL Price: ${data['market']['solPrice']}")
                            
                    return True
                else:
                    print(f"❌ Failed: {response.status_code}")
                    print(f"📄 Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    async def run_tests(self):
        """Run all API tests."""
        print("🚀 TESTING ENHANCED API SERVER")
        print("=" * 50)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"⏰ Test Time: {datetime.now().isoformat()}")
        print("=" * 50)
        
        # Test endpoints
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/metrics", "Live metrics"),
            ("/live-status", "Live trading status"),
            ("/wallet-info", "Wallet information"),
            ("/trading-session", "Trading session data"),
            ("/component/trading_engine", "Component status")
        ]
        
        results = []
        for endpoint, description in endpoints:
            success = await self.test_endpoint(endpoint, description)
            results.append((endpoint, success))
            await asyncio.sleep(1)  # Small delay between tests
            
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for endpoint, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {endpoint}")
            
        print(f"\n🎯 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! API server is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the API server logs.")
            
        return passed == total

async def main():
    """Main test function."""
    tester = APITester()
    
    print("🔍 Testing Enhanced API Server for Williams Capital Management")
    print("👤 Owner: Winsor Williams II")
    print("💼 Live Trading Integration")
    
    success = await tester.run_tests()
    
    if success:
        print("\n🚀 API server is ready for dashboard integration!")
        return 0
    else:
        print("\n❌ API server has issues that need to be resolved.")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
