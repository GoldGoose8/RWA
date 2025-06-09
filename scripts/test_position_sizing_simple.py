#!/usr/bin/env python3
"""
Simple test for improved position sizing logic.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_position_sizing():
    """Test the improved position sizing logic."""
    
    print("🚀 TESTING IMPROVED POSITION SIZING")
    print("=" * 60)
    
    try:
        from core.risk.production_position_sizer import ProductionPositionSizer
        print("✅ ProductionPositionSizer imported successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return
    
    # Test configuration
    config = {
        'wallet': {
            'active_trading_pct': 0.9,  # 90% active trading
            'reserve_pct': 0.1          # 10% reserve
        },
        'trading': {
            'base_position_size_pct': 0.5,    # 50% of active capital
            'max_position_size_pct': 0.8,     # 80% max
            'min_position_size_pct': 0.2,     # 20% min
            'min_trade_size_usd': 10,          # $10 minimum
            'target_trade_size_usd': 50        # $50 target
        },
        'risk_management': {
            'max_risk_per_trade': 0.02,       # 2% risk per trade
            'max_portfolio_exposure': 0.8     # 80% max exposure
        }
    }
    
    # Initialize position sizer
    try:
        sizer = ProductionPositionSizer(config)
        print("✅ ProductionPositionSizer initialized")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return
    
    # Test scenarios
    scenarios = [
        {
            "name": "Current Low Balance (Recent Trade)",
            "wallet_balance": 0.051537,
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
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 SCENARIO: {scenario['name']}")
        print("-" * 40)
        print(f"Wallet Balance: {scenario['wallet_balance']:.6f} SOL")
        print(f"SOL Price: ${scenario['sol_price']:.2f}")
        
        try:
            # Update wallet state
            sizer.update_wallet_state(
                wallet_balance=scenario['wallet_balance'],
                current_exposure=scenario['current_exposure'],
                sol_price=scenario['sol_price']
            )
            
            # Calculate position size with 80% signal strength
            result = sizer.calculate_position_size(
                signal_strength=0.8,
                strategy="opportunistic_volatility_breakout",
                market_regime="ranging",
                volatility=0.03
            )
            
            if result.get('rejected', False):
                print(f"❌ REJECTED: {result.get('rejection_reason', 'Unknown')}")
                continue
            
            print(f"\n🎯 POSITION SIZE RESULTS:")
            print(f"   Position: {result['position_size_sol']:.6f} SOL")
            print(f"   USD Value: ${result['position_size_usd']:.2f}")
            print(f"   % of Active Capital: {result['position_size_pct_of_active']*100:.1f}%")
            print(f"   % of Total Wallet: {result['position_size_pct_of_total']*100:.1f}%")
            
            print(f"\n💰 WALLET BREAKDOWN:")
            print(f"   Total Wallet: {result['total_wallet_sol']:.6f} SOL")
            print(f"   Fee Reserve: {result['fee_reserve_sol']:.6f} SOL")
            print(f"   Available: {result['available_balance_sol']:.6f} SOL")
            print(f"   Active Capital (90%): {result['active_capital_sol']:.6f} SOL")
            print(f"   Reserve (10%): {result['reserve_balance_sol']:.6f} SOL")
            
            print(f"\n✅ Fee Optimized: {result['fee_optimized']}")
            
        except Exception as e:
            print(f"❌ Error in scenario: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_position_sizing()
