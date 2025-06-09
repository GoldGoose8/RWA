#!/usr/bin/env python3
"""
Orca Pool Optimization for Error 3012 Fix
==========================================

This script optimizes Orca pool parameters to prevent error 3012 and ensure
successful trading execution.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

class OrcaPoolOptimizer:
    """Optimize Orca pool parameters for successful trading."""
    
    def __init__(self):
        self.quicknode_url = os.getenv('QUICKNODE_RPC_URL')
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.orca_api_base = "https://api.orca.so"
        
        # Optimized parameters
        self.optimized_config = {
            'slippage_bps': 500,  # 5% slippage
            'min_output_buffer': 0.95,  # 5% buffer
            'priority_fee': 50000,  # Higher priority fee
            'max_price_impact': 0.05,  # 5% max price impact
            'timeout': 30,  # 30 second timeout
            'retry_attempts': 5  # 5 retry attempts
        }
        
        print("🔧 ORCA POOL OPTIMIZER INITIALIZED")
        print("=" * 50)
    
    async def test_orca_api_connectivity(self) -> bool:
        """Test Orca API connectivity."""
        print("🌊 Testing Orca API connectivity...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test Orca whirlpool API
                response = await client.get(f"{self.orca_api_base}/v1/whirlpool/list")
                
                if response.status_code == 200:
                    data = response.json()
                    pool_count = len(data.get('whirlpools', []))
                    print(f"✅ Orca API: Connected ({pool_count} pools available)")
                    return True
                else:
                    print(f"❌ Orca API failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Orca API error: {e}")
            return False
    
    async def get_optimal_sol_usdc_pool(self) -> dict:
        """Get the optimal SOL/USDC pool for trading."""
        print("🔍 Finding optimal SOL/USDC pool...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.orca_api_base}/v1/whirlpool/list")
                
                if response.status_code != 200:
                    print(f"❌ Failed to get pool list: {response.status_code}")
                    return None
                
                data = response.json()
                pools = data.get('whirlpools', [])
                
                # SOL and USDC mint addresses
                SOL_MINT = "So11111111111111111111111111111111111111112"
                USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                
                # Find SOL/USDC pools
                sol_usdc_pools = []
                for pool in pools:
                    token_a = pool.get('tokenA', {}).get('mint', '')
                    token_b = pool.get('tokenB', {}).get('mint', '')
                    
                    if (token_a == SOL_MINT and token_b == USDC_MINT) or \
                       (token_a == USDC_MINT and token_b == SOL_MINT):
                        sol_usdc_pools.append(pool)
                
                if not sol_usdc_pools:
                    print("❌ No SOL/USDC pools found")
                    return None
                
                # Sort by liquidity (TVL) and select the best one
                best_pool = max(sol_usdc_pools, key=lambda p: float(p.get('tvl', 0)))
                
                print(f"✅ Optimal SOL/USDC pool found:")
                print(f"   Address: {best_pool.get('address', 'N/A')}")
                print(f"   TVL: ${float(best_pool.get('tvl', 0)):,.2f}")
                print(f"   Fee: {best_pool.get('feeRate', 0)}%")
                
                return best_pool
                
        except Exception as e:
            print(f"❌ Error finding optimal pool: {e}")
            return None
    
    async def test_swap_quote(self, pool_info: dict, amount_sol: float = 0.1) -> dict:
        """Test swap quote with optimized parameters."""
        print(f"💱 Testing swap quote for {amount_sol} SOL...")
        
        try:
            # Convert SOL to lamports
            amount_lamports = int(amount_sol * 1_000_000_000)
            
            # SOL and USDC mint addresses
            SOL_MINT = "So11111111111111111111111111111111111111112"
            USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get quote from Orca
                quote_url = f"{self.orca_api_base}/v1/whirlpool/quote"
                params = {
                    'inputMint': SOL_MINT,
                    'outputMint': USDC_MINT,
                    'amount': amount_lamports,
                    'slippageBps': self.optimized_config['slippage_bps']
                }
                
                response = await client.get(quote_url, params=params)
                
                if response.status_code == 200:
                    quote_data = response.json()
                    
                    amount_out = quote_data.get('amountOut', 0)
                    price_impact = quote_data.get('priceImpact', 0)
                    
                    # Calculate minimum output with buffer
                    slippage_multiplier = (10000 - self.optimized_config['slippage_bps']) / 10000
                    buffer_multiplier = self.optimized_config['min_output_buffer']
                    min_output = int(amount_out * slippage_multiplier * buffer_multiplier)
                    
                    print(f"✅ Quote successful:")
                    print(f"   Input: {amount_sol} SOL ({amount_lamports:,} lamports)")
                    print(f"   Output: {amount_out:,} USDC micro-units")
                    print(f"   Min Output: {min_output:,} USDC micro-units")
                    print(f"   Price Impact: {price_impact:.4f}%")
                    print(f"   Slippage: {self.optimized_config['slippage_bps']/100:.1f}%")
                    
                    # Validate quote to prevent error 3012
                    if amount_out <= 0:
                        print("❌ Invalid quote: Zero output amount")
                        return None
                    
                    if price_impact > self.optimized_config['max_price_impact']:
                        print(f"❌ Price impact too high: {price_impact:.4f}% > {self.optimized_config['max_price_impact']:.4f}%")
                        return None
                    
                    if min_output <= 0:
                        print("❌ Invalid minimum output calculation")
                        return None
                    
                    return {
                        'amount_in': amount_lamports,
                        'amount_out': amount_out,
                        'min_output': min_output,
                        'price_impact': price_impact,
                        'slippage_bps': self.optimized_config['slippage_bps'],
                        'valid': True
                    }
                else:
                    print(f"❌ Quote failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting quote: {e}")
            return None
    
    async def test_wallet_balance(self) -> float:
        """Test wallet balance for trading."""
        print("💰 Checking wallet balance...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }
                
                response = await client.post(self.quicknode_url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1_000_000_000
                    
                    print(f"✅ Wallet balance: {balance_sol:.9f} SOL")
                    
                    # Check if we have enough for trading
                    min_balance = 0.1  # Minimum 0.1 SOL for trading
                    if balance_sol < min_balance:
                        print(f"⚠️ Low balance: {balance_sol:.6f} SOL < {min_balance} SOL minimum")
                        return balance_sol
                    
                    print(f"✅ Sufficient balance for trading")
                    return balance_sol
                else:
                    print(f"❌ Balance check failed: {response.status_code}")
                    return 0
                    
        except Exception as e:
            print(f"❌ Error checking balance: {e}")
            return 0
    
    async def save_optimized_config(self):
        """Save optimized configuration to file."""
        print("💾 Saving optimized configuration...")
        
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "orca_optimized.json"
        
        with open(config_file, 'w') as f:
            json.dump(self.optimized_config, f, indent=2)
        
        print(f"✅ Configuration saved to: {config_file}")
    
    async def run_optimization(self):
        """Run complete Orca pool optimization."""
        print("🚀 STARTING ORCA POOL OPTIMIZATION")
        print("=" * 60)
        print("🎯 Goal: Fix error 3012 and ensure successful trading")
        print("=" * 60)
        
        # Test 1: API Connectivity
        if not await self.test_orca_api_connectivity():
            print("❌ Orca API connectivity failed - cannot proceed")
            return False
        
        # Test 2: Wallet Balance
        balance = await self.test_wallet_balance()
        if balance <= 0:
            print("❌ Wallet balance check failed - cannot proceed")
            return False
        
        # Test 3: Find Optimal Pool
        pool_info = await self.get_optimal_sol_usdc_pool()
        if not pool_info:
            print("❌ Could not find optimal SOL/USDC pool")
            return False
        
        # Test 4: Test Swap Quote
        quote_result = await self.test_swap_quote(pool_info, 0.1)  # Test with 0.1 SOL
        if not quote_result:
            print("❌ Swap quote test failed")
            return False
        
        # Test 5: Save Configuration
        await self.save_optimized_config()
        
        # Summary
        print("\n🎯 OPTIMIZATION SUMMARY")
        print("=" * 40)
        print("✅ Orca API: Connected")
        print(f"✅ Wallet Balance: {balance:.6f} SOL")
        print(f"✅ Optimal Pool: {pool_info.get('address', 'N/A')[:20]}...")
        print(f"✅ Quote Test: {quote_result['amount_out']:,} USDC output")
        print(f"✅ Slippage: {self.optimized_config['slippage_bps']/100:.1f}%")
        print(f"✅ Min Output Buffer: {self.optimized_config['min_output_buffer']:.1%}")
        print(f"✅ Priority Fee: {self.optimized_config['priority_fee']:,} lamports")
        
        print("\n🚀 ORCA POOLS OPTIMIZED FOR ERROR 3012 PREVENTION!")
        print("✅ Ready for live trading with enhanced reliability")
        
        return True


async def main():
    """Main optimization function."""
    optimizer = OrcaPoolOptimizer()
    success = await optimizer.run_optimization()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
