#!/usr/bin/env python3
"""
QuickNode Endpoint Tester
==========================

Tests different QuickNode URL formats to find the correct one
for your API key: QN_810042470c20437bb9ec222fbf20f071
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any

class QuickNodeTester:
    """Tests QuickNode endpoint configurations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        
        # Common QuickNode URL patterns
        self.url_patterns = [
            f"https://solana-mainnet.quiknode.pro/{api_key}/",
            f"https://example-guide-demo.solana-mainnet.quiknode.pro/{api_key}/",
            f"https://your-endpoint.solana-mainnet.quiknode.pro/{api_key}/",
            f"https://api.quicknode.com/solana/mainnet/{api_key}/",
            f"https://{api_key}.solana-mainnet.quiknode.pro/",
            f"https://solana-mainnet.discover.quiknode.pro/{api_key}/",
        ]
        
        # Test RPC call
        self.test_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth"
        }
    
    async def test_endpoint(self, url: str) -> Dict[str, Any]:
        """Test a single endpoint URL."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=self.test_payload)
                
                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "success": False,
                    "response_time_ms": 0,
                    "error": None
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "result" in data:
                            result["success"] = True
                            result["response_data"] = data
                    except json.JSONDecodeError:
                        result["error"] = "Invalid JSON response"
                else:
                    result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                
                return result
                
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "success": False,
                "response_time_ms": 0,
                "error": str(e)
            }
    
    async def test_all_patterns(self) -> List[Dict[str, Any]]:
        """Test all URL patterns."""
        print(f"🔍 Testing QuickNode endpoints for API key: {self.api_key}")
        print("=" * 60)
        
        results = []
        
        for i, url in enumerate(self.url_patterns, 1):
            print(f"\n{i}. Testing: {url}")
            
            result = await self.test_endpoint(url)
            results.append(result)
            
            if result["success"]:
                print(f"   ✅ SUCCESS - Working endpoint found!")
                print(f"   📊 Response: {result.get('response_data', {}).get('result', 'OK')}")
            else:
                print(f"   ❌ FAILED - {result['error']}")
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("QUICKNODE ENDPOINT TEST SUMMARY")
        print("=" * 60)
        
        working_endpoints = [r for r in results if r["success"]]
        
        if working_endpoints:
            print(f"🎉 Found {len(working_endpoints)} working endpoint(s)!")
            
            for endpoint in working_endpoints:
                print(f"\n✅ WORKING ENDPOINT:")
                print(f"   URL: {endpoint['url']}")
                print(f"   Status: HTTP {endpoint['status_code']}")
                
                # Show how to update .env file
                print(f"\n📝 UPDATE YOUR .env FILE:")
                print(f"   QUICKNODE_RPC_URL={endpoint['url']}")
                print(f"   QUICKNODE_API_KEY={self.api_key}")
        else:
            print("❌ No working endpoints found!")
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Verify your API key is correct")
            print("2. Check if your QuickNode endpoint is active")
            print("3. Ensure you have a Solana Mainnet endpoint")
            print("4. Check QuickNode dashboard for the exact URL")
            
            print("\n📋 COMMON ISSUES:")
            for result in results:
                if "401" in str(result.get("error", "")):
                    print("   • 401 Unauthorized: Check API key")
                elif "404" in str(result.get("error", "")):
                    print("   • 404 Not Found: Check endpoint URL format")
                elif "timeout" in str(result.get("error", "")).lower():
                    print("   • Timeout: Check network connectivity")
        
        print("=" * 60)

async def test_transaction_capabilities(url: str, api_key: str) -> Dict[str, Any]:
    """Test transaction-related capabilities of the endpoint."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test getLatestBlockhash
            blockhash_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getLatestBlockhash",
                "params": [{"commitment": "confirmed"}]
            }

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            response = await client.post(url, json=blockhash_payload, headers=headers)

            result = {
                "url": url,
                "blockhash_test": False,
                "fee_test": False,
                "bundle_support": False,
                "error": None
            }

            if response.status_code == 200:
                data = response.json()
                if "result" in data and "value" in data["result"]:
                    result["blockhash_test"] = True

                    # Test getFeeForMessage
                    fee_payload = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "getFees",
                        "params": []
                    }

                    fee_response = await client.post(url, json=fee_payload, headers=headers)
                    if fee_response.status_code == 200:
                        fee_data = fee_response.json()
                        if "result" in fee_data:
                            result["fee_test"] = True

                    # Test bundle endpoint (QuickNode specific)
                    if "quicknode" in url.lower():
                        bundle_url = url.replace("/api/v1", "/bundles") if "/api/v1" in url else f"{url.rstrip('/')}/bundles"
                        bundle_payload = {
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "sendBundle",
                            "params": []
                        }

                        try:
                            bundle_response = await client.post(bundle_url, json=bundle_payload, headers=headers)
                            if bundle_response.status_code in [200, 400]:  # 400 is expected for empty bundle
                                result["bundle_support"] = True
                        except:
                            pass  # Bundle endpoint might not be available
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"

            return result

    except Exception as e:
        return {
            "url": url,
            "blockhash_test": False,
            "fee_test": False,
            "bundle_support": False,
            "error": str(e)
        }

async def main():
    """Main function."""
    import os

    # Get API key from environment or use default
    api_key = os.getenv('QUICKNODE_API_KEY', "QN_810042470c20437bb9ec222fbf20f071")
    quicknode_url = os.getenv('QUICKNODE_RPC_URL', "https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/")

    print("🔧 Testing QuickNode Endpoint Functionality")
    print("=" * 50)
    print(f"API Key: {api_key}")
    print(f"RPC URL: {quicknode_url}")
    print()

    # Test basic connectivity
    tester = QuickNodeTester(api_key)
    results = await tester.test_all_patterns()
    tester.print_summary(results)

    # Test transaction capabilities for working endpoints
    working_endpoints = [r for r in results if r["success"]]

    if working_endpoints:
        print("\n🔧 Testing Transaction Capabilities...")
        print("=" * 50)

        for endpoint in working_endpoints:
            print(f"\n📡 Testing capabilities for: {endpoint['url']}")
            capabilities = await test_transaction_capabilities(endpoint['url'], api_key)

            print(f"   ✅ Blockhash Test: {'PASS' if capabilities['blockhash_test'] else 'FAIL'}")
            print(f"   ✅ Fee Test: {'PASS' if capabilities['fee_test'] else 'FAIL'}")
            print(f"   ✅ Bundle Support: {'PASS' if capabilities['bundle_support'] else 'FAIL'}")

            if capabilities['error']:
                print(f"   ❌ Error: {capabilities['error']}")

    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/quicknode_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed results saved to: output/quicknode_test_results.json")

    # Return success if any endpoint worked
    working_count = sum(1 for r in results if r["success"])
    return 0 if working_count > 0 else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
