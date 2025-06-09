#!/usr/bin/env python3
"""
Debug Signal Calculation
========================

Debug the exact signal calculation step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force reload
import importlib
if 'core.strategies.opportunistic_volatility_breakout' in sys.modules:
    importlib.reload(sys.modules['core.strategies.opportunistic_volatility_breakout'])

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def debug_signal_calculation():
    """Debug the signal calculation step by step."""
    
    print("🔍 DEBUGGING SIGNAL CALCULATION STEP BY STEP")
    print("=" * 55)
    
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
    market_pair = 'SOL-USDC'
    
    print(f"✅ Strategy initialized:")
    print(f"   Volatility threshold: {strategy.volatility_threshold}")
    print(f"   Breakout threshold: {strategy.breakout_threshold}")
    print(f"   Min confidence: {strategy.min_confidence}")
    
    # Test 1: Simple upward trend
    print(f"\n📈 TEST 1: SIMPLE UPWARD TREND")
    print("-" * 35)
    
    prices = [150.0, 151.0, 152.0, 153.0, 154.0, 155.0, 156.0, 157.0, 158.0, 159.0]
    
    for price in prices:
        strategy._update_price_history(market_pair, {'price': price})
    
    print(f"✅ Price history: {prices}")
    
    market_data = {
        market_pair: {
            'price': 159.0,
            'volume': 1000000,
            'change_24h': 0.06,  # 6% up
            'volatility': 0.03
        }
    }
    
    # Manual step-by-step calculation
    print(f"\n🔍 MANUAL CALCULATION:")
    
    # Step 1: Check price history
    if market_pair not in strategy.price_history:
        print(f"❌ No price history for {market_pair}")
        return
    
    price_history = strategy.price_history[market_pair]
    print(f"   Price history length: {len(price_history)}")
    
    if len(price_history) < 10:
        print(f"❌ Insufficient price history ({len(price_history)} < 10)")
        return
    
    # Step 2: Calculate returns
    returns = np.diff(price_history) / np.array(price_history[:-1])
    print(f"   Returns: {[f'{r:.4f}' for r in returns[-5:]]}")
    
    # Step 3: Calculate volatilities
    current_vol = np.std(returns[-10:]) if len(returns) >= 10 else 0.0
    historical_vol = np.std(returns) if len(returns) > 1 else 0.0
    
    print(f"   Current volatility (last 10): {current_vol:.6f}")
    print(f"   Historical volatility (all): {historical_vol:.6f}")
    
    if historical_vol == 0:
        print(f"❌ Historical volatility is zero - no signal possible")
        return
    
    # Step 4: Calculate volatility ratio
    volatility_ratio = current_vol / historical_vol
    print(f"   Volatility ratio: {volatility_ratio:.6f}")
    print(f"   Volatility threshold: {1.0 + strategy.volatility_threshold:.6f}")
    print(f"   Volatility check: {volatility_ratio > (1.0 + strategy.volatility_threshold)}")
    
    # Step 5: Calculate recent return
    recent_return = (price_history[-1] - price_history[-5]) / price_history[-5] if len(price_history) >= 5 else 0.0
    print(f"   Recent return (5-period): {recent_return:.6f}")
    print(f"   Breakout threshold: {strategy.breakout_threshold:.6f}")
    print(f"   Breakout check: {abs(recent_return) > strategy.breakout_threshold}")
    
    # Step 6: Calculate volatility signal
    volatility_signal = 0.0
    if volatility_ratio > (1.0 + strategy.volatility_threshold):
        print(f"   ✅ Volatility condition met")
        if abs(recent_return) > strategy.breakout_threshold:
            print(f"   ✅ Breakout condition met")
            volatility_signal = np.sign(recent_return) * min(1.0, volatility_ratio - 1.0)
            print(f"   ✅ Volatility signal: {volatility_signal:.6f}")
        else:
            print(f"   ❌ Breakout condition failed")
    else:
        print(f"   ❌ Volatility condition failed")
    
    # Step 7: Apply confidence multiplier
    confidence_multiplier = min(1.0, max(0.7, volatility_ratio / 1.5))
    final_signal = volatility_signal * confidence_multiplier
    
    print(f"   Confidence multiplier: {confidence_multiplier:.6f}")
    print(f"   Final signal: {final_signal:.6f}")
    print(f"   Signal passes threshold: {abs(final_signal) >= strategy.min_confidence}")
    
    # Step 8: Test actual strategy method
    actual_signal = strategy._calculate_volatility_breakout_signal(market_pair, market_data[market_pair])
    print(f"   Actual strategy signal: {actual_signal:.6f}")
    
    if abs(actual_signal - final_signal) < 0.001:
        print(f"   ✅ Manual calculation matches strategy")
    else:
        print(f"   ❌ Manual calculation differs from strategy")
    
    # Test 2: Extreme volatility
    print(f"\n💥 TEST 2: EXTREME VOLATILITY")
    print("-" * 30)
    
    strategy_extreme = OpportunisticVolatilityBreakout(strategy_config)
    
    # Create extreme volatility
    extreme_prices = [
        100.0, 100.0, 100.0, 100.0, 100.0,  # Stable baseline
        120.0, 80.0, 140.0, 60.0, 160.0,    # Massive swings
        40.0, 180.0, 200.0                   # Final extreme moves
    ]
    
    for price in extreme_prices:
        strategy_extreme._update_price_history(market_pair, {'price': price})
    
    print(f"✅ Extreme prices: {extreme_prices}")
    
    # Calculate extreme volatility manually
    extreme_returns = np.diff(extreme_prices) / np.array(extreme_prices[:-1])
    extreme_current_vol = np.std(extreme_returns[-10:])
    extreme_historical_vol = np.std(extreme_returns)
    extreme_vol_ratio = extreme_current_vol / extreme_historical_vol if extreme_historical_vol > 0 else 1.0
    
    print(f"   Extreme volatility ratio: {extreme_vol_ratio:.6f}")
    print(f"   Should easily pass threshold: {extreme_vol_ratio > 1.01}")
    
    extreme_recent_return = (extreme_prices[-1] - extreme_prices[-5]) / extreme_prices[-5]
    print(f"   Extreme recent return: {extreme_recent_return:.6f}")
    print(f"   Should easily pass breakout: {abs(extreme_recent_return) > 0.005}")
    
    # Test extreme signal
    extreme_signal = strategy_extreme._calculate_volatility_breakout_signal(market_pair, market_data[market_pair])
    print(f"   Extreme signal: {extreme_signal:.6f}")
    
    if abs(extreme_signal) >= strategy_extreme.min_confidence:
        print(f"   ✅ EXTREME signal passes threshold!")
    else:
        print(f"   ❌ Even extreme signal fails threshold")
    
    # Test 3: Lower thresholds
    print(f"\n🔧 TEST 3: ULTRA-LOW THRESHOLDS")
    print("-" * 35)
    
    ultra_config = {
        'name': 'opportunistic_volatility_breakout',
        'parameters': {
            'volatility_threshold': 0.001,  # 0.1%
            'breakout_threshold': 0.001,    # 0.1%
            'profit_target_pct': 0.01,
            'min_confidence': 0.05,         # 5%
            'risk_level': 'medium',
            'use_filters': True
        }
    }
    
    strategy_ultra = OpportunisticVolatilityBreakout(ultra_config)
    
    # Use simple trend
    simple_prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
    
    for price in simple_prices:
        strategy_ultra._update_price_history(market_pair, {'price': price})
    
    ultra_signal = strategy_ultra._calculate_volatility_breakout_signal(market_pair, market_data[market_pair])
    print(f"   Ultra-low threshold signal: {ultra_signal:.6f}")
    print(f"   Ultra-low min confidence: {strategy_ultra.min_confidence}")
    print(f"   Ultra-low signal passes: {abs(ultra_signal) >= strategy_ultra.min_confidence}")
    
    if abs(ultra_signal) >= strategy_ultra.min_confidence:
        print(f"   ✅ ULTRA-LOW thresholds work!")
        
        # Test full signal generation
        full_signal = strategy_ultra.generate_signals(market_data)
        if full_signal:
            print(f"   ✅ FULL SIGNAL GENERATED: {full_signal.get('action')}")
            print(f"🚀 STRATEGY IS WORKING WITH LOW THRESHOLDS!")
        else:
            print(f"   ❌ Full signal generation still fails")
    else:
        print(f"   ❌ Even ultra-low thresholds fail")

if __name__ == "__main__":
    debug_signal_calculation()
