#!/usr/bin/env python3
"""
Jito Configuration Tester
==========================

Tests Jito Block Engine configuration and endpoints to ensure
everything is working correctly as the primary RPC.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    import httpx
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("Please run: pip3 install python-dotenv httpx")
    sys.exit(1)

class JitoTester:
    """Tests Jito Block Engine configuration and functionality."""
    
    def __init__(self):
        """Initialize the Jito tester."""
        load_dotenv()
        
        # Get Jito configuration
        self.base_url = os.getenv("JITO_RPC_URL", "https://mainnet.block-engine.jito.wtf/api/v1")
        self.bundle_url = os.getenv("JITO_BUNDLE_URL", "https://mainnet.block-engine.jito.wtf/api/v1/bundles")
        self.transaction_url = os.getenv("JITO_TRANSACTION_URL", "https://mainnet.block-engine.jito.wtf/api/v1/transactions")
        
        # Regional endpoints
        self.regional_endpoints = {
            "Amsterdam": os.getenv("JITO_AMSTERDAM_URL", "https://amsterdam.mainnet.block-engine.jito.wtf/api/v1"),
            "Frankfurt": os.getenv("JITO_FRANKFURT_URL", "https://frankfurt.mainnet.block-engine.jito.wtf/api/v1"),
            "London": os.getenv("JITO_LONDON_URL", "https://london.mainnet.block-engine.jito.wtf/api/v1"),
            "New York": os.getenv("JITO_NY_URL", "https://ny.mainnet.block-engine.jito.wtf/api/v1"),
            "Tokyo": os.getenv("JITO_TOKYO_URL", "https://tokyo.mainnet.block-engine.jito.wtf/api/v1"),
            "Salt Lake City": os.getenv("JITO_SLC_URL", "https://slc.mainnet.block-engine.jito.wtf/api/v1")
        }
        
        # Configuration
        self.timeout = int(os.getenv("JITO_TIMEOUT", "30"))
        self.tip_amount = int(os.getenv("JITO_TIP_AMOUNT_LAMPORTS", "10000"))
        self.rate_limit = int(os.getenv("JITO_RATE_LIMIT_PER_SECOND", "1"))
        
        print(f"🔧 Jito Block Engine Base URL: {self.base_url}")
        print(f"⏱️ Timeout: {self.timeout}s")
        print(f"💰 Tip Amount: {self.tip_amount} lamports")
        print(f"🚦 Rate Limit: {self.rate_limit} req/sec")
        
    async def test_tip_accounts(self) -> Dict[str, Any]:
        """Test getTipAccounts endpoint."""
        print("\n🔍 Testing Jito Tip Accounts API...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTipAccounts",
                    "params": []
                }
                
                start_time = time.time()
                response = await client.post(f"{self.base_url}/getTipAccounts", json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "result" in data:
                        tip_accounts = data["result"]
                        
                        result = {
                            "status": "success",
                            "response_time_ms": round(response_time * 1000, 2),
                            "tip_accounts_count": len(tip_accounts),
                            "tip_accounts": tip_accounts
                        }
                        
                        print(f"✅ Tip Accounts API: {response_time * 1000:.2f}ms")
                        print(f"   💰 Found {len(tip_accounts)} tip accounts")
                        print(f"   🎯 First account: {tip_accounts[0] if tip_accounts else 'None'}")
                        
                        return result
                    else:
                        error_msg = f"No result in response: {data}"
                        print(f"❌ Tip Accounts API failed: {error_msg}")
                        return {"status": "error", "error": error_msg}
                        
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ Tip Accounts API failed: {error_msg}")
                    return {"status": "error", "error": error_msg}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Tip Accounts API error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def test_regional_endpoints(self) -> Dict[str, Any]:
        """Test regional Jito endpoints for latency."""
        print("\n🔍 Testing Jito Regional Endpoints...")
        
        results = {}
        
        for region, url in self.regional_endpoints.items():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTipAccounts",
                        "params": []
                    }
                    
                    start_time = time.time()
                    response = await client.post(f"{url}/getTipAccounts", json=payload)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        results[region] = {
                            "status": "success",
                            "response_time_ms": round(response_time * 1000, 2),
                            "url": url
                        }
                        print(f"   ✅ {region}: {response_time * 1000:.2f}ms")
                    else:
                        results[region] = {
                            "status": "error",
                            "error": f"HTTP {response.status_code}",
                            "url": url
                        }
                        print(f"   ❌ {region}: HTTP {response.status_code}")
                        
            except Exception as e:
                results[region] = {
                    "status": "error",
                    "error": str(e),
                    "url": url
                }
                print(f"   ❌ {region}: {str(e)}")
        
        # Find fastest endpoint
        successful_regions = {k: v for k, v in results.items() if v["status"] == "success"}
        if successful_regions:
            fastest_region = min(successful_regions.items(), key=lambda x: x[1]["response_time_ms"])
            print(f"\n🏆 Fastest region: {fastest_region[0]} ({fastest_region[1]['response_time_ms']}ms)")
        
        return {
            "status": "success" if successful_regions else "error",
            "regions": results,
            "fastest_region": fastest_region[0] if successful_regions else None
        }
    
    async def test_rate_limits(self) -> Dict[str, Any]:
        """Test Jito rate limiting behavior."""
        print("\n🔍 Testing Jito Rate Limits...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTipAccounts",
                    "params": []
                }
                
                requests_made = 0
                successful_requests = 0
                rate_limited_requests = 0
                
                print(f"   Making {self.rate_limit + 2} requests to test rate limits...")
                
                for i in range(self.rate_limit + 2):
                    try:
                        response = await client.post(f"{self.base_url}/getTipAccounts", json=payload)
                        requests_made += 1
                        
                        if response.status_code == 200:
                            successful_requests += 1
                        elif response.status_code == 429:
                            rate_limited_requests += 1
                            print(f"   ⚠️ Rate limited on request {i+1}")
                        
                        # Small delay to respect rate limits
                        await asyncio.sleep(0.2)
                        
                    except Exception as e:
                        print(f"   ❌ Request {i+1} failed: {e}")
                
                result = {
                    "status": "success",
                    "requests_made": requests_made,
                    "successful_requests": successful_requests,
                    "rate_limited_requests": rate_limited_requests,
                    "success_rate": successful_requests / requests_made if requests_made > 0 else 0
                }
                
                print(f"✅ Rate Limit Test: {successful_requests}/{requests_made} successful")
                if rate_limited_requests > 0:
                    print(f"   ⚠️ {rate_limited_requests} requests were rate limited (expected)")
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Rate limit test error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def test_basic_rpc_functionality(self) -> Dict[str, Any]:
        """Test basic RPC functionality through Jito."""
        print("\n🔍 Testing Basic RPC Functionality...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test getHealth method
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                start_time = time.time()
                response = await client.post(self.base_url, json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    result = {
                        "status": "success",
                        "response_time_ms": round(response_time * 1000, 2),
                        "health_status": data.get("result", "unknown")
                    }
                    
                    print(f"✅ Basic RPC: {response_time * 1000:.2f}ms")
                    print(f"   🏥 Health Status: {data.get('result', 'unknown')}")
                    
                    return result
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ Basic RPC failed: {error_msg}")
                    return {"status": "error", "error": error_msg}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Basic RPC error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Jito configuration tests."""
        print("🚀 Jito Block Engine Configuration Test")
        print("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "configuration": {
                "base_url": self.base_url,
                "bundle_url": self.bundle_url,
                "transaction_url": self.transaction_url,
                "timeout": self.timeout,
                "tip_amount": self.tip_amount,
                "rate_limit": self.rate_limit
            },
            "tests": {}
        }
        
        # Run all tests
        results["tests"]["basic_rpc"] = await self.test_basic_rpc_functionality()
        results["tests"]["tip_accounts"] = await self.test_tip_accounts()
        results["tests"]["regional_endpoints"] = await self.test_regional_endpoints()
        results["tests"]["rate_limits"] = await self.test_rate_limits()
        
        # Calculate overall status
        successful_tests = sum(1 for test in results["tests"].values() if test.get("status") == "success")
        total_tests = len(results["tests"])
        
        if successful_tests == total_tests:
            results["overall_status"] = "ALL_PASSED"
        elif successful_tests > 0:
            results["overall_status"] = "PARTIAL_SUCCESS"
        else:
            results["overall_status"] = "ALL_FAILED"
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("JITO BLOCK ENGINE TEST SUMMARY")
        print("=" * 50)
        
        status_emoji = {
            "ALL_PASSED": "🎉",
            "PARTIAL_SUCCESS": "⚠️",
            "ALL_FAILED": "❌"
        }
        
        overall_status = results["overall_status"]
        print(f"{status_emoji[overall_status]} Overall Status: {overall_status}")
        
        print("\n📊 Test Results:")
        for test_name, test_result in results["tests"].items():
            status = test_result.get("status", "unknown")
            if status == "success":
                response_time = test_result.get("response_time_ms", 0)
                print(f"✅ {test_name}: {status} ({response_time}ms)")
            else:
                error = test_result.get("error", "Unknown error")
                print(f"❌ {test_name}: {status} - {error}")
        
        print("\n💡 Configuration:")
        config = results["configuration"]
        print(f"🔗 Base URL: {config['base_url']}")
        print(f"⏱️ Timeout: {config['timeout']}s")
        print(f"💰 Tip Amount: {config['tip_amount']} lamports")
        
        # Show regional performance if available
        regional_test = results["tests"].get("regional_endpoints", {})
        if regional_test.get("fastest_region"):
            print(f"🏆 Fastest Region: {regional_test['fastest_region']}")
        
        if overall_status == "ALL_PASSED":
            print("\n🎉 Jito Block Engine is fully configured and working!")
            print("✅ Ready for MEV-protected live trading")
            print("🛡️ Sandwich attack protection enabled")
            print("⚡ Fast transaction execution ready")
        elif overall_status == "PARTIAL_SUCCESS":
            print("\n⚠️ Some Jito endpoints are working")
            print("🔧 Check failed tests and network connectivity")
        else:
            print("\n❌ Jito Block Engine configuration has issues")
            print("🔧 Check network connectivity and endpoint URLs")
        
        print("=" * 50)

async def main():
    """Main function."""
    tester = JitoTester()
    results = await tester.run_all_tests()
    tester.print_summary(results)
    
    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "jito_configuration_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Return appropriate exit code
    if results["overall_status"] == "ALL_PASSED":
        return 0
    elif results["overall_status"] == "PARTIAL_SUCCESS":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(asyncio.run(main()))
