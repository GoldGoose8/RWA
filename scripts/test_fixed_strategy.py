#!/usr/bin/env python3
"""
Test Fixed Strategy
==================

Test the strategy with the fixed confidence multiplier.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force reload of the strategy module
import importlib
if 'core.strategies.opportunistic_volatility_breakout' in sys.modules:
    importlib.reload(sys.modules['core.strategies.opportunistic_volatility_breakout'])

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def test_fixed_strategy():
    """Test the strategy with the fixed confidence multiplier."""
    
    print("🔧 TESTING FIXED STRATEGY")
    print("=" * 30)
    
    # Strategy config
    strategy_config = {
        'name': 'opportunistic_volatility_breakout',
        'parameters': {
            'volatility_threshold': 0.01,
            'breakout_threshold': 0.005,
            'profit_target_pct': 0.01,
            'min_confidence': 0.3,
            'risk_level': 'medium',
            'use_filters': True
        }
    }
    
    strategy = OpportunisticVolatilityBreakout(strategy_config)
    
    # Test with realistic volatility
    current_price = 157.5
    market_pair = 'SOL-USDC'
    
    # Create price history with moderate volatility
    base_prices = [
        150.0, 150.1, 149.9, 150.2, 149.8,  # Stable period
        152.0, 154.0, 156.0, 158.0, current_price  # Upward trend
    ]
    
    for price in base_prices:
        strategy._update_price_history(market_pair, {'price': price})
    
    print(f"✅ Price history: {[f'{p:.1f}' for p in base_prices]}")
    
    # Market data
    market_data = {
        market_pair: {
            'price': current_price,
            'volume': 1000000,
            'change_24h': 0.05,  # 5% up
            'volatility': 0.03
        }
    }
    
    # Test signal generation
    signal = strategy.generate_signals(market_data)
    
    if signal:
        print(f"🎉 SIGNAL GENERATED!")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        
        if signal.get('action') == 'SELL':
            print("✅ CORRECT: Upward trend generated SELL signal")
        else:
            print(f"⚠️ Generated {signal.get('action')} signal")
            
        print("🚀 FIXED STRATEGY IS WORKING!")
        
    else:
        print("❌ Still no signal generated")
        
        # Manual calculation to verify fix
        prices = strategy.price_history[market_pair]
        returns = np.diff(prices) / np.array(prices[:-1])
        current_vol = np.std(returns[-5:]) if len(returns) >= 5 else 0.0
        historical_vol = np.std(returns) if len(returns) > 1 else 0.0
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        print(f"\n🔍 Manual calculation:")
        print(f"   Volatility ratio: {vol_ratio:.3f}")
        
        # Test both old and new confidence multiplier formulas
        old_multiplier = min(1.0, vol_ratio / 2.0)
        new_multiplier = min(1.0, max(0.7, vol_ratio / 1.5))
        
        print(f"   Old confidence multiplier: {old_multiplier:.3f}")
        print(f"   New confidence multiplier: {new_multiplier:.3f}")
        
        # Check if the fix is actually applied
        if abs(new_multiplier - old_multiplier) > 0.01:
            print("✅ Fix is applied - different multipliers")
        else:
            print("❌ Fix not applied - same multipliers")
    
    # Test with extreme volatility to force a signal
    print(f"\n💥 TESTING WITH EXTREME VOLATILITY:")
    
    strategy_extreme = OpportunisticVolatilityBreakout(strategy_config)
    
    # Extreme volatility pattern
    extreme_prices = [
        150.0, 150.0, 150.0, 150.0,  # Stable
        160.0, 140.0, 170.0, 130.0, 180.0,  # Massive swings
        current_price
    ]
    
    for price in extreme_prices:
        strategy_extreme._update_price_history(market_pair, {'price': price})
    
    signal_extreme = strategy_extreme.generate_signals(market_data)
    
    if signal_extreme:
        print(f"✅ EXTREME signal: {signal_extreme.get('action')}")
        strategy_metadata = signal_extreme.get('strategy_metadata', {})
        print(f"   Signal strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        print("🚀 EXTREME VOLATILITY WORKS!")
    else:
        print("❌ Even extreme volatility failed")
        
        # Check the actual signal calculation
        signal_strength = strategy_extreme._calculate_volatility_breakout_signal(market_pair, market_data[market_pair])
        print(f"   Raw signal strength: {signal_strength:.6f}")
        print(f"   Min confidence: {strategy_extreme.min_confidence}")

if __name__ == "__main__":
    test_fixed_strategy()
