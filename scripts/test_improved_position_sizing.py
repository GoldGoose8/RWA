#!/usr/bin/env python3
"""
Test script for improved position sizing with accurate wallet balance usage.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.risk.production_position_sizer import ProductionPositionSizer
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_position_sizing():
    """Test the improved position sizing logic."""
    
    print("🚀 TESTING IMPROVED POSITION SIZING")
    print("=" * 60)
    
    # Load configuration
    try:
        config_path = project_root / "config" / "live_production.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Loaded config from {config_path}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Initialize position sizer
    position_sizer = ProductionPositionSizer(config)
    
    # Test scenarios with different wallet balances
    test_scenarios = [
        {
            "name": "Current Low Balance",
            "wallet_balance": 0.051537,  # Current balance from recent trades
            "sol_price": 156.0,
            "current_exposure": 0.0
        },
        {
            "name": "Medium Balance",
            "wallet_balance": 0.5,
            "sol_price": 156.0,
            "current_exposure": 0.0
        },
        {
            "name": "Higher Balance",
            "wallet_balance": 1.0,
            "sol_price": 156.0,
            "current_exposure": 0.0
        },
        {
            "name": "With Existing Exposure",
            "wallet_balance": 0.5,
            "sol_price": 156.0,
            "current_exposure": 0.1  # 0.1 SOL already in positions
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📊 SCENARIO: {scenario['name']}")
        print("-" * 40)
        
        # Update wallet state
        position_sizer.update_wallet_state(
            wallet_balance=scenario['wallet_balance'],
            current_exposure=scenario['current_exposure'],
            sol_price=scenario['sol_price']
        )
        
        # Test different signal strengths
        signal_strengths = [0.6, 0.8, 1.0]
        
        for signal_strength in signal_strengths:
            print(f"\n🎯 Signal Strength: {signal_strength}")
            
            # Calculate position size
            result = position_sizer.calculate_position_size(
                signal_strength=signal_strength,
                strategy="opportunistic_volatility_breakout",
                market_regime="ranging",
                volatility=0.03
            )
            
            if result.get('rejected', False):
                print(f"   ❌ REJECTED: {result.get('rejection_reason', 'Unknown')}")
                continue
            
            # Display results
            print(f"   💰 Position Size: {result['position_size_sol']:.6f} SOL (${result['position_size_usd']:.2f})")
            print(f"   📊 % of Active Capital: {result['position_size_pct_of_active']*100:.1f}%")
            print(f"   📊 % of Total Wallet: {result['position_size_pct_of_total']*100:.1f}%")
            print(f"   🎯 Fee Optimized: {result['fee_optimized']}")
            
            # Show wallet breakdown
            print(f"   📈 Wallet Breakdown:")
            print(f"      Total Wallet: {result['total_wallet_sol']:.6f} SOL")
            print(f"      Fee Reserve: {result['fee_reserve_sol']:.6f} SOL")
            print(f"      Available: {result['available_balance_sol']:.6f} SOL")
            print(f"      Active Capital: {result['active_capital_sol']:.6f} SOL")
            print(f"      Reserve: {result['reserve_balance_sol']:.6f} SOL")
    
    print(f"\n🎉 TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_position_sizing())
