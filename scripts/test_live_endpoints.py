#!/usr/bin/env python3
"""
Live Trading Endpoints Test
===========================

Test script to verify all RPC endpoints and transaction execution components
are working correctly before starting live trading.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EndpointTester:
    """Test all live trading endpoints and components."""
    
    def __init__(self):
        """Initialize the tester."""
        load_dotenv()
        self.results = {
            "timestamp": None,
            "overall_status": "unknown",
            "tests": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
    async def test_quicknode_rpc(self) -> Dict[str, Any]:
        """Test QuickNode RPC endpoint performance."""
        logger.info("🔍 Testing QuickNode RPC endpoint...")
        
        quicknode_url = os.getenv("QUICKNODE_RPC_URL")
        if not quicknode_url or "your-" in quicknode_url:
            return {"status": "SKIPPED", "reason": "Not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                import time
                
                # Test 1: Health check
                start_time = time.time()
                health_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                response = await client.post(quicknode_url, json=health_payload)
                health_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                
                # Test 2: Get slot
                start_time = time.time()
                slot_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "getSlot"
                }
                
                response = await client.post(quicknode_url, json=slot_payload)
                slot_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"getSlot failed: HTTP {response.status_code}"}
                
                slot_result = response.json()
                current_slot = slot_result.get("result")
                
                # Test 3: Get recent blockhash
                start_time = time.time()
                blockhash_payload = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "getRecentBlockhash"
                }
                
                response = await client.post(quicknode_url, json=blockhash_payload)
                blockhash_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"getRecentBlockhash failed: HTTP {response.status_code}"}
                
                return {
                    "status": "PASSED",
                    "current_slot": current_slot,
                    "performance": {
                        "health_check_ms": round(health_time * 1000, 2),
                        "get_slot_ms": round(slot_time * 1000, 2),
                        "get_blockhash_ms": round(blockhash_time * 1000, 2)
                    }
                }
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    async def test_helius_rpc(self) -> Dict[str, Any]:
        """Test Helius RPC endpoint performance."""
        logger.info("🔍 Testing Helius RPC endpoint...")
        
        helius_url = os.getenv("HELIUS_RPC_URL")
        if not helius_url or "your_" in helius_url:
            return {"status": "SKIPPED", "reason": "Not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                import time
                
                # Test enhanced APIs
                start_time = time.time()
                health_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                }
                
                response = await client.post(helius_url, json=health_payload)
                response_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                
                result = response.json()
                
                return {
                    "status": "PASSED",
                    "performance": {
                        "response_time_ms": round(response_time * 1000, 2)
                    },
                    "health": result.get("result", "unknown")
                }
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    async def test_jito_endpoint(self) -> Dict[str, Any]:
        """Test Jito bundle endpoint."""
        logger.info("🔍 Testing Jito bundle endpoint...")
        
        jito_url = os.getenv("JITO_RPC_URL", "https://mainnet.block-engine.jito.wtf/api/v1")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                import time
                
                # Test basic connectivity
                start_time = time.time()
                response = await client.get(f"{jito_url.rstrip('/api/v1')}/", timeout=10.0)
                response_time = time.time() - start_time
                
                # Jito may return 404 for root path, which is expected
                if response.status_code in [200, 404]:
                    return {
                        "status": "PASSED",
                        "performance": {
                            "response_time_ms": round(response_time * 1000, 2)
                        },
                        "endpoint_reachable": True
                    }
                else:
                    return {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    async def test_jupiter_api(self) -> Dict[str, Any]:
        """Test Jupiter DEX API."""
        logger.info("🔍 Testing Jupiter DEX API...")
        
        jupiter_url = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                import time
                
                # Test quote endpoint with SOL to USDC
                start_time = time.time()
                quote_url = f"{jupiter_url}/quote"
                params = {
                    "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                    "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                    "amount": "1000000",  # 0.001 SOL
                    "slippageBps": "50"
                }
                
                response = await client.get(quote_url, params=params)
                response_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                
                quote_data = response.json()
                
                return {
                    "status": "PASSED",
                    "performance": {
                        "quote_time_ms": round(response_time * 1000, 2)
                    },
                    "quote_available": "outAmount" in quote_data
                }
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    async def test_wallet_balance(self) -> Dict[str, Any]:
        """Test wallet balance retrieval."""
        logger.info("🔍 Testing wallet balance retrieval...")
        
        wallet_address = os.getenv("WALLET_ADDRESS")
        quicknode_url = os.getenv("QUICKNODE_RPC_URL")
        
        if not wallet_address or "your_" in wallet_address:
            return {"status": "SKIPPED", "reason": "Wallet not configured"}
        
        if not quicknode_url or "your-" in quicknode_url:
            return {"status": "SKIPPED", "reason": "RPC not configured"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                import time
                
                start_time = time.time()
                balance_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [wallet_address]
                }
                
                response = await client.post(quicknode_url, json=balance_payload)
                response_time = time.time() - start_time
                
                if response.status_code != 200:
                    return {"status": "FAILED", "error": f"HTTP {response.status_code}"}
                
                result = response.json()
                if "result" not in result:
                    return {"status": "FAILED", "error": "Invalid response format"}
                
                balance_lamports = result["result"]["value"]
                balance_sol = balance_lamports / 1_000_000_000
                
                return {
                    "status": "PASSED",
                    "balance_sol": balance_sol,
                    "balance_lamports": balance_lamports,
                    "performance": {
                        "query_time_ms": round(response_time * 1000, 2)
                    }
                }
                
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests."""
        logger.info("🚀 Starting live trading endpoints test...")
        logger.info("=" * 60)
        
        import time
        self.results["timestamp"] = time.time()
        
        # Run all tests
        tests = {
            "quicknode_rpc": await self.test_quicknode_rpc(),
            "helius_rpc": await self.test_helius_rpc(),
            "jito_endpoint": await self.test_jito_endpoint(),
            "jupiter_api": await self.test_jupiter_api(),
            "wallet_balance": await self.test_wallet_balance()
        }
        
        self.results["tests"] = tests
        
        # Calculate overall status
        passed_tests = sum(1 for test in tests.values() if test["status"] == "PASSED")
        failed_tests = sum(1 for test in tests.values() if test["status"] == "FAILED")
        skipped_tests = sum(1 for test in tests.values() if test["status"] == "SKIPPED")
        
        if failed_tests == 0 and passed_tests > 0:
            self.results["overall_status"] = "READY"
        elif failed_tests > 0 and passed_tests > 0:
            self.results["overall_status"] = "PARTIAL"
        else:
            self.results["overall_status"] = "NOT_READY"
        
        # Add performance metrics
        self.results["performance_metrics"] = {
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "tests_skipped": skipped_tests,
            "total_tests": len(tests)
        }
        
        # Add recommendations
        if failed_tests > 0:
            self.results["recommendations"].append("Fix failed endpoint tests before live trading")
        if skipped_tests > 0:
            self.results["recommendations"].append("Configure skipped endpoints for full functionality")
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("LIVE TRADING ENDPOINTS TEST SUMMARY")
        logger.info("=" * 60)
        
        # Overall status
        status_emoji = {
            "READY": "🟢",
            "PARTIAL": "🟡",
            "NOT_READY": "🔴"
        }
        
        logger.info(f"Overall Status: {status_emoji[self.results['overall_status']]} {self.results['overall_status']}")
        logger.info("")
        
        # Individual test results
        for test_name, test_result in self.results["tests"].items():
            status = test_result["status"]
            status_emoji_test = {"PASSED": "✅", "FAILED": "❌", "SKIPPED": "⏭️"}
            
            logger.info(f"{status_emoji_test[status]} {test_name}: {status}")
            
            if status == "FAILED" and "error" in test_result:
                logger.info(f"    Error: {test_result['error']}")
            elif status == "PASSED" and "performance" in test_result:
                perf = test_result["performance"]
                perf_str = ", ".join([f"{k}: {v}" for k, v in perf.items()])
                logger.info(f"    Performance: {perf_str}")
        
        # Performance summary
        metrics = self.results["performance_metrics"]
        logger.info(f"\n📊 Test Results: {metrics['tests_passed']}/{metrics['total_tests']} passed")
        
        # Recommendations
        if self.results["recommendations"]:
            logger.info("\n💡 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                logger.info(f"  • {rec}")
        
        logger.info("=" * 60)

async def main():
    """Main function."""
    tester = EndpointTester()
    results = await tester.run_all_tests()
    tester.print_summary()
    
    # Save results
    output_file = "output/endpoint_test_results.json"
    os.makedirs("output", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Detailed results saved to: {output_file}")
    
    # Exit with appropriate code
    if results["overall_status"] == "READY":
        return 0
    elif results["overall_status"] == "PARTIAL":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(asyncio.run(main()))
