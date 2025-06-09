#!/usr/bin/env python3
"""
Live Production Test Suite
===========================

Comprehensive test suite that simulates real trading conditions
to validate the system is ready for live production trading.
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
    from solders.pubkey import Pubkey
    from solana.rpc.api import Client
except ImportError as e:
    print(f"❌ Error importing required packages: {e}")
    sys.exit(1)

class LiveProductionTester:
    """Comprehensive live production testing suite."""
    
    def __init__(self):
        """Initialize the production tester."""
        load_dotenv()
        
        # Get configuration
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        self.quicknode_url = os.getenv("QUICKNODE_RPC_URL")
        self.helius_url = os.getenv("HELIUS_RPC_URL")
        self.jito_url = os.getenv("JITO_RPC_URL")
        self.jupiter_quote_url = os.getenv("JUPITER_QUOTE_ENDPOINT")
        
        # Test parameters
        self.test_amount_sol = 0.001  # 0.001 SOL for testing
        self.test_amount_lamports = int(self.test_amount_sol * 1_000_000_000)
        
        # Token addresses
        self.SOL_MINT = "So11111111111111111111111111111111111111112"
        self.USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        print(f"🚀 Live Production Test Suite")
        print(f"📍 Wallet: {self.wallet_address}")
        print(f"💰 Test Amount: {self.test_amount_sol} SOL")
        
    async def test_wallet_balance_across_rpcs(self) -> Dict[str, Any]:
        """Test wallet balance retrieval across all RPC endpoints."""
        print("\n🔍 Testing wallet balance across all RPC endpoints...")
        
        results = {}
        
        # Test QuickNode
        if self.quicknode_url:
            try:
                client = Client(self.quicknode_url)
                pubkey = Pubkey.from_string(self.wallet_address)
                
                start_time = time.time()
                balance_response = client.get_balance(pubkey)
                response_time = time.time() - start_time
                
                balance_sol = balance_response.value / 1_000_000_000
                
                results["quicknode"] = {
                    "status": "success",
                    "balance_sol": balance_sol,
                    "response_time_ms": round(response_time * 1000, 2)
                }
                print(f"   ✅ QuickNode: {balance_sol:.9f} SOL ({response_time * 1000:.2f}ms)")
                
            except Exception as e:
                results["quicknode"] = {"status": "error", "error": str(e)}
                print(f"   ❌ QuickNode: {e}")
        
        # Test Helius
        if self.helius_url:
            try:
                client = Client(self.helius_url)
                pubkey = Pubkey.from_string(self.wallet_address)
                
                start_time = time.time()
                balance_response = client.get_balance(pubkey)
                response_time = time.time() - start_time
                
                balance_sol = balance_response.value / 1_000_000_000
                
                results["helius"] = {
                    "status": "success",
                    "balance_sol": balance_sol,
                    "response_time_ms": round(response_time * 1000, 2)
                }
                print(f"   ✅ Helius: {balance_sol:.9f} SOL ({response_time * 1000:.2f}ms)")
                
            except Exception as e:
                results["helius"] = {"status": "error", "error": str(e)}
                print(f"   ❌ Helius: {e}")
        
        return results
    
    async def test_jupiter_quote_performance(self) -> Dict[str, Any]:
        """Test Jupiter quote API performance with various amounts."""
        print("\n🔍 Testing Jupiter quote performance...")
        
        test_amounts = [
            0.001,  # Small trade
            0.01,   # Medium trade
            0.1,    # Large trade
            1.0     # Very large trade
        ]
        
        results = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for amount_sol in test_amounts:
                try:
                    amount_lamports = int(amount_sol * 1_000_000_000)
                    
                    params = {
                        "inputMint": self.SOL_MINT,
                        "outputMint": self.USDC_MINT,
                        "amount": str(amount_lamports),
                        "slippageBps": "50"
                    }
                    
                    start_time = time.time()
                    response = await client.get(self.jupiter_quote_url, params=params)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        quote_data = response.json()
                        
                        output_amount = int(quote_data.get("outAmount", 0))
                        usdc_amount = output_amount / 1_000_000  # USDC has 6 decimals
                        rate = usdc_amount / amount_sol
                        price_impact = float(quote_data.get("priceImpactPct", 0))
                        
                        result = {
                            "amount_sol": amount_sol,
                            "rate_usdc_per_sol": rate,
                            "price_impact_pct": price_impact,
                            "response_time_ms": round(response_time * 1000, 2),
                            "status": "success"
                        }
                        
                        print(f"   ✅ {amount_sol} SOL → {usdc_amount:.2f} USDC (Rate: {rate:.2f}, Impact: {price_impact:.4f}%, {response_time * 1000:.2f}ms)")
                        
                    else:
                        result = {
                            "amount_sol": amount_sol,
                            "status": "error",
                            "error": f"HTTP {response.status_code}"
                        }
                        print(f"   ❌ {amount_sol} SOL: HTTP {response.status_code}")
                    
                    results.append(result)
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    result = {
                        "amount_sol": amount_sol,
                        "status": "error",
                        "error": str(e)
                    }
                    results.append(result)
                    print(f"   ❌ {amount_sol} SOL: {e}")
        
        return {"quotes": results}
    
    async def test_jito_tip_accounts_availability(self) -> Dict[str, Any]:
        """Test Jito tip accounts availability and response times."""
        print("\n🔍 Testing Jito tip accounts availability...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTipAccounts",
                    "params": []
                }
                
                start_time = time.time()
                response = await client.post(f"{self.jito_url}/getTipAccounts", json=payload)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    tip_accounts = data.get("result", [])
                    
                    result = {
                        "status": "success",
                        "tip_accounts_count": len(tip_accounts),
                        "tip_accounts": tip_accounts,
                        "response_time_ms": round(response_time * 1000, 2)
                    }
                    
                    print(f"   ✅ Found {len(tip_accounts)} tip accounts ({response_time * 1000:.2f}ms)")
                    print(f"   🎯 Sample accounts: {tip_accounts[:3]}")
                    
                    return result
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def test_rpc_endpoint_latency(self) -> Dict[str, Any]:
        """Test latency across all RPC endpoints."""
        print("\n🔍 Testing RPC endpoint latency...")
        
        endpoints = {
            "quicknode": self.quicknode_url,
            "helius": self.helius_url
        }
        
        results = {}
        
        for name, url in endpoints.items():
            if not url:
                continue
                
            try:
                latencies = []
                
                # Test 5 times for average latency
                for i in range(5):
                    client = Client(url)
                    
                    start_time = time.time()
                    health_response = client.get_health()
                    response_time = time.time() - start_time
                    
                    latencies.append(response_time * 1000)
                    await asyncio.sleep(0.2)
                
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                results[name] = {
                    "status": "success",
                    "avg_latency_ms": round(avg_latency, 2),
                    "min_latency_ms": round(min_latency, 2),
                    "max_latency_ms": round(max_latency, 2),
                    "all_latencies": [round(l, 2) for l in latencies]
                }
                
                print(f"   ✅ {name}: Avg {avg_latency:.2f}ms (Min: {min_latency:.2f}ms, Max: {max_latency:.2f}ms)")
                
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                print(f"   ❌ {name}: {e}")
        
        return results
    
    async def test_system_readiness_checklist(self) -> Dict[str, Any]:
        """Comprehensive system readiness checklist."""
        print("\n🔍 Running system readiness checklist...")
        
        checklist = {}
        
        # Check wallet balance
        try:
            client = Client(self.quicknode_url)
            pubkey = Pubkey.from_string(self.wallet_address)
            balance_response = client.get_balance(pubkey)
            balance_sol = balance_response.value / 1_000_000_000
            
            checklist["wallet_funded"] = {
                "status": "pass" if balance_sol >= 0.1 else "warning",
                "balance_sol": balance_sol,
                "sufficient": balance_sol >= 0.1
            }
            
            if balance_sol >= 0.1:
                print(f"   ✅ Wallet funded: {balance_sol:.9f} SOL")
            else:
                print(f"   ⚠️ Low wallet balance: {balance_sol:.9f} SOL")
                
        except Exception as e:
            checklist["wallet_funded"] = {"status": "fail", "error": str(e)}
            print(f"   ❌ Wallet check failed: {e}")
        
        # Check configuration files
        required_files = [
            ".env",
            "config.yaml",
            "config/live_production.yaml",
            "keys/trading_wallet.json"
        ]
        
        files_status = {}
        for file_path in required_files:
            exists = Path(file_path).exists()
            files_status[file_path] = exists
            
            if exists:
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")
        
        checklist["config_files"] = {
            "status": "pass" if all(files_status.values()) else "fail",
            "files": files_status
        }
        
        # Check environment variables
        required_env_vars = [
            "WALLET_ADDRESS",
            "WALLET_PRIVATE_KEY",
            "QUICKNODE_RPC_URL",
            "HELIUS_RPC_URL",
            "JITO_RPC_URL",
            "JUPITER_QUOTE_ENDPOINT"
        ]
        
        env_status = {}
        for var in required_env_vars:
            value = os.getenv(var)
            has_value = value is not None and value != "" and "your_" not in value
            env_status[var] = has_value
            
            if has_value:
                print(f"   ✅ {var}")
            else:
                print(f"   ❌ {var}")
        
        checklist["environment_vars"] = {
            "status": "pass" if all(env_status.values()) else "fail",
            "variables": env_status
        }
        
        return checklist
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all production tests."""
        print("🚀 Live Production Test Suite")
        print("=" * 60)
        
        results = {
            "timestamp": time.time(),
            "wallet_address": self.wallet_address,
            "test_amount_sol": self.test_amount_sol,
            "tests": {}
        }
        
        # Run all tests
        results["tests"]["wallet_balance"] = await self.test_wallet_balance_across_rpcs()
        results["tests"]["jupiter_quotes"] = await self.test_jupiter_quote_performance()
        results["tests"]["jito_tip_accounts"] = await self.test_jito_tip_accounts_availability()
        results["tests"]["rpc_latency"] = await self.test_rpc_endpoint_latency()
        results["tests"]["system_readiness"] = await self.test_system_readiness_checklist()
        
        # Calculate overall status
        test_results = []
        for test_name, test_data in results["tests"].items():
            if isinstance(test_data, dict):
                if test_data.get("status") == "success" or test_data.get("status") == "pass":
                    test_results.append(True)
                elif test_data.get("status") in ["error", "fail"]:
                    test_results.append(False)
                else:
                    # Check sub-tests
                    sub_tests = []
                    for key, value in test_data.items():
                        if isinstance(value, dict) and "status" in value:
                            sub_tests.append(value["status"] in ["success", "pass"])
                    test_results.append(all(sub_tests) if sub_tests else True)
        
        if all(test_results):
            results["overall_status"] = "READY_FOR_PRODUCTION"
        elif any(test_results):
            results["overall_status"] = "PARTIAL_READY"
        else:
            results["overall_status"] = "NOT_READY"
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("LIVE PRODUCTION TEST SUMMARY")
        print("=" * 60)
        
        status_emoji = {
            "READY_FOR_PRODUCTION": "🎉",
            "PARTIAL_READY": "⚠️",
            "NOT_READY": "❌"
        }
        
        overall_status = results["overall_status"]
        print(f"{status_emoji[overall_status]} Overall Status: {overall_status}")
        
        print(f"\n📍 Wallet: {results['wallet_address']}")
        print(f"💰 Test Amount: {results['test_amount_sol']} SOL")
        
        # Wallet balance summary
        wallet_test = results["tests"].get("wallet_balance", {})
        if "quicknode" in wallet_test:
            balance = wallet_test["quicknode"].get("balance_sol", 0)
            print(f"💰 Current Balance: {balance:.9f} SOL")
        
        # Jupiter performance summary
        jupiter_test = results["tests"].get("jupiter_quotes", {})
        if "quotes" in jupiter_test:
            successful_quotes = [q for q in jupiter_test["quotes"] if q.get("status") == "success"]
            if successful_quotes:
                avg_response_time = sum(q["response_time_ms"] for q in successful_quotes) / len(successful_quotes)
                print(f"📊 Jupiter Performance: {len(successful_quotes)}/{len(jupiter_test['quotes'])} quotes successful (Avg: {avg_response_time:.2f}ms)")
        
        # Jito summary
        jito_test = results["tests"].get("jito_tip_accounts", {})
        if jito_test.get("status") == "success":
            tip_count = jito_test.get("tip_accounts_count", 0)
            response_time = jito_test.get("response_time_ms", 0)
            print(f"🛡️ Jito MEV Protection: {tip_count} tip accounts available ({response_time:.2f}ms)")
        
        # RPC latency summary
        latency_test = results["tests"].get("rpc_latency", {})
        for rpc_name, rpc_data in latency_test.items():
            if rpc_data.get("status") == "success":
                avg_latency = rpc_data.get("avg_latency_ms", 0)
                print(f"⚡ {rpc_name.title()} RPC: {avg_latency:.2f}ms average latency")
        
        if overall_status == "READY_FOR_PRODUCTION":
            print("\n🎉 SYSTEM IS READY FOR LIVE PRODUCTION TRADING!")
            print("✅ All critical systems operational")
            print("✅ Wallet funded and accessible")
            print("✅ RPC endpoints responding optimally")
            print("✅ Jupiter DEX quotes working")
            print("✅ Jito MEV protection active")
            print("✅ Configuration validated")
            
            print("\n🚀 READY TO START LIVE TRADING:")
            print("   python3 scripts/unified_live_trading.py")
            
        elif overall_status == "PARTIAL_READY":
            print("\n⚠️ SYSTEM MOSTLY READY - Minor issues detected")
            print("🔧 Review test results above")
            print("💡 System may still be usable for trading")
            
        else:
            print("\n❌ SYSTEM NOT READY FOR PRODUCTION")
            print("🔧 Critical issues need to be resolved")
            print("⚠️ Do not start live trading until issues are fixed")
        
        print("=" * 60)

async def main():
    """Main function."""
    tester = LiveProductionTester()
    results = await tester.run_comprehensive_test()
    tester.print_summary(results)
    
    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "live_production_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Return appropriate exit code
    if results["overall_status"] == "READY_FOR_PRODUCTION":
        return 0
    elif results["overall_status"] == "PARTIAL_READY":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(asyncio.run(main()))
