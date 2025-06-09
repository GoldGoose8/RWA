#!/usr/bin/env python3
"""
Jupiter API Configuration Test
==============================

Tests the Jupiter API configuration and endpoints to ensure
everything is working correctly with the free tier.
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    import httpx
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    print("Please run: pip3 install python-dotenv httpx")
    sys.exit(1)

class JupiterAPITester:
    """Tests Jupiter API configuration and functionality."""
    
    def __init__(self):
        """Initialize the Jupiter API tester."""
        load_dotenv()
        
        # Get Jupiter configuration
        self.base_url = os.getenv("JUPITER_API_URL", "https://lite-api.jup.ag")
        self.quote_endpoint = os.getenv("JUPITER_QUOTE_ENDPOINT", "https://lite-api.jup.ag/swap/v1/quote")
        self.swap_endpoint = os.getenv("JUPITER_SWAP_ENDPOINT", "https://lite-api.jup.ag/swap/v1/swap")
        self.price_endpoint = os.getenv("JUPITER_PRICE_ENDPOINT", "https://lite-api.jup.ag/price/v2")
        self.token_endpoint = os.getenv("JUPITER_TOKEN_ENDPOINT", "https://lite-api.jup.ag/tokens/v1")
        
        # Configuration
        self.timeout = int(os.getenv("JUPITER_TIMEOUT", "10"))
        self.slippage_bps = int(os.getenv("JUPITER_SLIPPAGE_BPS", "50"))
        
        # Token addresses
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        print(f"🔧 Jupiter API Base URL: {self.base_url}")
        print(f"⏱️ Timeout: {self.timeout}s")
        print(f"📊 Slippage: {self.slippage_bps} BPS ({self.slippage_bps/100}%)")
        
    async def test_quote_api(self) -> Dict[str, Any]:
        """Test Jupiter quote API."""
        print("\n🔍 Testing Jupiter Quote API...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test SOL to USDC quote
                params = {
                    "inputMint": self.SOL_MINT,
                    "outputMint": self.USDC_MINT,
                    "amount": "1000000",  # 0.001 SOL
                    "slippageBps": self.slippage_bps,
                    "onlyDirectRoutes": "false",
                    "asLegacyTransaction": "false"
                }
                
                start_time = time.time()
                response = await client.get(self.quote_endpoint, params=params)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    quote_data = response.json()
                    
                    # Extract key information
                    input_amount = int(quote_data.get("inAmount", 0))
                    output_amount = int(quote_data.get("outAmount", 0))
                    price_impact = float(quote_data.get("priceImpactPct", 0))
                    
                    # Calculate rates
                    sol_amount = input_amount / 1_000_000_000
                    usdc_amount = output_amount / 1_000_000  # USDC has 6 decimals
                    rate = usdc_amount / sol_amount if sol_amount > 0 else 0
                    
                    result = {
                        "status": "success",
                        "response_time_ms": round(response_time * 1000, 2),
                        "input_amount_sol": sol_amount,
                        "output_amount_usdc": usdc_amount,
                        "exchange_rate": rate,
                        "price_impact_pct": price_impact,
                        "route_plan_length": len(quote_data.get("routePlan", [])),
                        "other_amount_threshold": quote_data.get("otherAmountThreshold"),
                        "swap_mode": quote_data.get("swapMode", "ExactIn")
                    }
                    
                    print(f"✅ Quote API: {response_time * 1000:.2f}ms")
                    print(f"   📊 Rate: 1 SOL = {rate:.2f} USDC")
                    print(f"   📈 Price Impact: {price_impact:.4f}%")
                    print(f"   🛣️ Route Steps: {len(quote_data.get('routePlan', []))}")
                    
                    return result
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ Quote API failed: {error_msg}")
                    return {"status": "error", "error": error_msg}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Quote API error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def test_price_api(self) -> Dict[str, Any]:
        """Test Jupiter price API."""
        print("\n🔍 Testing Jupiter Price API...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test price endpoint
                params = {
                    "ids": f"{self.SOL_MINT},{self.USDC_MINT}",
                    "vsToken": self.USDC_MINT
                }
                
                start_time = time.time()
                response = await client.get(self.price_endpoint, params=params)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    price_data = response.json()
                    
                    result = {
                        "status": "success",
                        "response_time_ms": round(response_time * 1000, 2),
                        "data": price_data.get("data", {})
                    }
                    
                    print(f"✅ Price API: {response_time * 1000:.2f}ms")
                    
                    # Show price data
                    data = price_data.get("data", {})
                    for mint, price_info in data.items():
                        if mint == self.SOL_MINT:
                            price = price_info.get("price", 0)
                            try:
                                price_float = float(price)
                                print(f"   💰 SOL Price: ${price_float:.2f}")
                            except (ValueError, TypeError):
                                print(f"   💰 SOL Price: {price}")
                    
                    return result
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ Price API failed: {error_msg}")
                    return {"status": "error", "error": error_msg}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Price API error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def test_token_api(self) -> Dict[str, Any]:
        """Test Jupiter token API."""
        print("\n🔍 Testing Jupiter Token API...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Test token info endpoint
                token_url = f"{self.token_endpoint}/token/{self.SOL_MINT}"
                
                start_time = time.time()
                response = await client.get(token_url)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    result = {
                        "status": "success",
                        "response_time_ms": round(response_time * 1000, 2),
                        "token_info": {
                            "symbol": token_data.get("symbol"),
                            "name": token_data.get("name"),
                            "decimals": token_data.get("decimals"),
                            "verified": token_data.get("verified", False)
                        }
                    }
                    
                    print(f"✅ Token API: {response_time * 1000:.2f}ms")
                    print(f"   🪙 Token: {token_data.get('symbol')} ({token_data.get('name')})")
                    print(f"   ✅ Verified: {token_data.get('verified', False)}")
                    
                    return result
                    
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    print(f"❌ Token API failed: {error_msg}")
                    return {"status": "error", "error": error_msg}
                    
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Token API error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def test_rate_limits(self) -> Dict[str, Any]:
        """Test rate limiting behavior."""
        print("\n🔍 Testing Rate Limits...")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Make multiple quick requests to test rate limiting
                requests_made = 0
                successful_requests = 0
                rate_limited_requests = 0
                
                params = {
                    "inputMint": self.SOL_MINT,
                    "outputMint": self.USDC_MINT,
                    "amount": "1000000",
                    "slippageBps": self.slippage_bps
                }
                
                print("   Making 10 quick requests to test rate limits...")
                
                for i in range(10):
                    try:
                        response = await client.get(self.quote_endpoint, params=params)
                        requests_made += 1
                        
                        if response.status_code == 200:
                            successful_requests += 1
                        elif response.status_code == 429:
                            rate_limited_requests += 1
                            print(f"   ⚠️ Rate limited on request {i+1}")
                        
                        # Small delay between requests
                        await asyncio.sleep(0.1)
                        
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
                    print(f"   ⚠️ {rate_limited_requests} requests were rate limited")
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Rate limit test error: {error_msg}")
            return {"status": "error", "error": error_msg}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Jupiter API tests."""
        print("🚀 Jupiter API Configuration Test")
        print("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "configuration": {
                "base_url": self.base_url,
                "quote_endpoint": self.quote_endpoint,
                "price_endpoint": self.price_endpoint,
                "token_endpoint": self.token_endpoint,
                "timeout": self.timeout,
                "slippage_bps": self.slippage_bps
            },
            "tests": {}
        }
        
        # Run all tests
        results["tests"]["quote_api"] = await self.test_quote_api()
        results["tests"]["price_api"] = await self.test_price_api()
        results["tests"]["token_api"] = await self.test_token_api()
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
        print("JUPITER API TEST SUMMARY")
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
        print(f"📊 Slippage: {config['slippage_bps']} BPS")
        
        if overall_status == "ALL_PASSED":
            print("\n🎉 Jupiter API is fully configured and working!")
            print("✅ Ready for live trading with Jupiter DEX")
        elif overall_status == "PARTIAL_SUCCESS":
            print("\n⚠️ Some Jupiter API endpoints are working")
            print("🔧 Check failed tests and network connectivity")
        else:
            print("\n❌ Jupiter API configuration has issues")
            print("🔧 Check network connectivity and endpoint URLs")
        
        print("=" * 50)

async def main():
    """Main function."""
    tester = JupiterAPITester()
    results = await tester.run_all_tests()
    tester.print_summary(results)
    
    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "jupiter_api_test_results.json"
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
