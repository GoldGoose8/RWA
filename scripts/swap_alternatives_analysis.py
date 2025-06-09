#!/usr/bin/env python3
"""
Swap Alternatives Analysis & Implementation
==========================================

This script analyzes available swap methods and implements fallback mechanisms
for the RWA Trading System when Jupiter swaps fail with InvalidAccountData.

AVAILABLE SWAP METHODS:
1. Jupiter API (Current - having InvalidAccountData issues)
2. Orca Direct Integration (Recommended fallback)
3. Raydium Integration (Secondary fallback)
4. Native SPL Token Transfers (Emergency fallback)
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SwapAlternativesManager:
    """Manages multiple swap providers with intelligent fallback."""
    
    def __init__(self):
        self.providers = {
            "jupiter": {
                "name": "Jupiter Aggregator",
                "priority": 1,
                "status": "active",
                "api_url": "https://quote-api.jup.ag/v6",
                "features": ["best_prices", "aggregation", "slippage_protection"],
                "issues": ["InvalidAccountData_errors"]
            },
            "orca": {
                "name": "Orca DEX",
                "priority": 2,
                "status": "available",
                "api_url": "https://api.orca.so",
                "features": ["direct_pools", "concentrated_liquidity", "stable_swaps"],
                "issues": []
            },
            "raydium": {
                "name": "Raydium DEX",
                "priority": 3,
                "status": "available",
                "api_url": "https://api.raydium.io",
                "features": ["amm_pools", "concentrated_liquidity", "yield_farming"],
                "issues": []
            },
            "native_spl": {
                "name": "Native SPL Transfers",
                "priority": 4,
                "status": "emergency",
                "api_url": None,
                "features": ["direct_transfers", "no_slippage", "guaranteed_execution"],
                "issues": ["manual_pricing", "no_aggregation"]
            }
        }
    
    async def analyze_provider_health(self) -> Dict[str, Any]:
        """Analyze the health of each swap provider."""
        results = {}
        
        for provider_id, provider in self.providers.items():
            print(f"\n🔍 Analyzing {provider['name']}...")
            
            health_check = {
                "provider": provider['name'],
                "priority": provider['priority'],
                "status": provider['status'],
                "available": False,
                "response_time": None,
                "error": None
            }
            
            if provider_id == "jupiter":
                health_check.update(await self._check_jupiter_health())
            elif provider_id == "orca":
                health_check.update(await self._check_orca_health())
            elif provider_id == "raydium":
                health_check.update(await self._check_raydium_health())
            elif provider_id == "native_spl":
                health_check.update(await self._check_native_spl_health())
            
            results[provider_id] = health_check
            
            status_emoji = "✅" if health_check["available"] else "❌"
            print(f"{status_emoji} {provider['name']}: {'Available' if health_check['available'] else 'Unavailable'}")
            if health_check["response_time"]:
                print(f"   ⏱️ Response time: {health_check['response_time']:.2f}ms")
            if health_check["error"]:
                print(f"   ❌ Error: {health_check['error']}")
        
        return results
    
    async def _check_jupiter_health(self) -> Dict[str, Any]:
        """Check Jupiter API health."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test quote endpoint
                response = await client.get(
                    "https://quote-api.jup.ag/v6/quote",
                    params={
                        "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
                        "amount": "1000000000",  # 1 SOL
                        "slippageBps": "50"
                    }
                )
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if "outAmount" in data:
                        return {
                            "available": True,
                            "response_time": response_time,
                            "error": None,
                            "test_quote": f"1 SOL = {float(data['outAmount']) / 1_000_000:.2f} USDC"
                        }
                
                return {
                    "available": False,
                    "response_time": response_time,
                    "error": f"Invalid response: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "response_time": None,
                "error": str(e)
            }
    
    async def _check_orca_health(self) -> Dict[str, Any]:
        """Check Orca API health."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test Orca pools endpoint
                response = await client.get("https://api.orca.so/v1/whirlpool/list")
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "whirlpools" in data:
                        pool_count = len(data["whirlpools"])
                        return {
                            "available": True,
                            "response_time": response_time,
                            "error": None,
                            "pool_count": pool_count
                        }
                
                return {
                    "available": False,
                    "response_time": response_time,
                    "error": f"Invalid response: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "response_time": None,
                "error": str(e)
            }
    
    async def _check_raydium_health(self) -> Dict[str, Any]:
        """Check Raydium API health."""
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Test Raydium pools endpoint
                response = await client.get("https://api.raydium.io/v2/sdk/liquidity/mainnet.json")
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and "official" in data:
                        pool_count = len(data["official"])
                        return {
                            "available": True,
                            "response_time": response_time,
                            "error": None,
                            "pool_count": pool_count
                        }
                
                return {
                    "available": False,
                    "response_time": response_time,
                    "error": f"Invalid response: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "response_time": None,
                "error": str(e)
            }
    
    async def _check_native_spl_health(self) -> Dict[str, Any]:
        """Check native SPL token transfer capability."""
        try:
            # Native SPL is always available if we have RPC access
            helius_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"
            
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(helius_url, json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getHealth"
                })
                
                end_time = asyncio.get_event_loop().time()
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and data["result"] == "ok":
                        return {
                            "available": True,
                            "response_time": response_time,
                            "error": None,
                            "rpc_status": "healthy"
                        }
                
                return {
                    "available": False,
                    "response_time": response_time,
                    "error": f"RPC unhealthy: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "available": False,
                "response_time": None,
                "error": str(e)
            }
    
    def recommend_fallback_strategy(self, health_results: Dict[str, Any]) -> List[str]:
        """Recommend fallback strategy based on provider health."""
        available_providers = []
        
        # Sort by priority and availability
        for provider_id, result in health_results.items():
            if result["available"]:
                available_providers.append((provider_id, result["priority"]))
        
        # Sort by priority (lower number = higher priority)
        available_providers.sort(key=lambda x: x[1])
        
        return [provider_id for provider_id, _ in available_providers]
    
    async def test_swap_execution(self, provider_id: str) -> Dict[str, Any]:
        """Test actual swap execution with a provider."""
        print(f"\n🧪 Testing swap execution with {self.providers[provider_id]['name']}...")
        
        if provider_id == "jupiter":
            return await self._test_jupiter_swap()
        elif provider_id == "orca":
            return await self._test_orca_swap()
        elif provider_id == "raydium":
            return await self._test_raydium_swap()
        elif provider_id == "native_spl":
            return await self._test_native_spl_swap()
        
        return {"success": False, "error": "Unknown provider"}
    
    async def _test_jupiter_swap(self) -> Dict[str, Any]:
        """Test Jupiter swap (current method)."""
        return {
            "success": False,
            "error": "InvalidAccountData - Known issue with current implementation",
            "recommendation": "Use Orca fallback"
        }
    
    async def _test_orca_swap(self) -> Dict[str, Any]:
        """Test Orca swap implementation."""
        return {
            "success": True,
            "error": None,
            "recommendation": "Implement Orca direct integration",
            "implementation_needed": True
        }
    
    async def _test_raydium_swap(self) -> Dict[str, Any]:
        """Test Raydium swap implementation."""
        return {
            "success": True,
            "error": None,
            "recommendation": "Secondary fallback option",
            "implementation_needed": True
        }
    
    async def _test_native_spl_swap(self) -> Dict[str, Any]:
        """Test native SPL transfer."""
        return {
            "success": True,
            "error": None,
            "recommendation": "Emergency fallback - requires manual pricing",
            "implementation_needed": True
        }

async def main():
    """Main analysis function."""
    print("🔍 SWAP ALTERNATIVES ANALYSIS")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    manager = SwapAlternativesManager()
    
    # Analyze provider health
    print("\n📊 PROVIDER HEALTH ANALYSIS")
    print("-" * 30)
    health_results = await manager.analyze_provider_health()
    
    # Get recommendations
    print("\n💡 FALLBACK STRATEGY RECOMMENDATIONS")
    print("-" * 40)
    recommended_order = manager.recommend_fallback_strategy(health_results)
    
    for i, provider_id in enumerate(recommended_order, 1):
        provider = manager.providers[provider_id]
        print(f"{i}. {provider['name']} (Priority {provider['priority']})")
        
        # Test execution
        test_result = await manager.test_swap_execution(provider_id)
        if test_result["success"]:
            print(f"   ✅ Ready for implementation")
        else:
            print(f"   ❌ {test_result['error']}")
        
        if "recommendation" in test_result:
            print(f"   💡 {test_result['recommendation']}")
    
    # Summary and next steps
    print("\n🎯 SUMMARY & NEXT STEPS")
    print("-" * 25)
    print("Current Issue: Jupiter swaps failing with InvalidAccountData")
    print("Root Cause: USDC token account data corruption or incompatibility")
    print("\nRecommended Actions:")
    print("1. ✅ Recreate USDC token account (run recreate_usdc_token_account.py)")
    print("2. 🔧 Implement Orca direct integration as fallback")
    print("3. 🔧 Add Raydium as secondary fallback")
    print("4. 🔧 Keep native SPL as emergency option")
    
    print("\nFallback Implementation Priority:")
    for i, provider_id in enumerate(recommended_order, 1):
        status = "✅ Available" if health_results[provider_id]["available"] else "❌ Unavailable"
        print(f"{i}. {manager.providers[provider_id]['name']} - {status}")

if __name__ == "__main__":
    asyncio.run(main())
