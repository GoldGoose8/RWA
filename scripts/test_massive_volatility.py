#!/usr/bin/env python3
"""
Test Strategy with MASSIVE Volatility
=====================================

Create extreme volatility to trigger strong signals.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def test_massive_volatility():
    """Test strategy with massive volatility to trigger strong signals."""
    
    print("🚀 TESTING STRATEGY WITH MASSIVE VOLATILITY")
    print("=" * 50)
    
    # Ultra-low thresholds for easy triggering
    config = {
        'name': 'opportunistic_volatility_breakout',
        'parameters': {
            'volatility_threshold': 0.001,  # 0.1%
            'breakout_threshold': 0.001,    # 0.1%
            'profit_target_pct': 0.02,
            'min_confidence': 0.1,          # 10% confidence
            'risk_level': 'medium',
            'use_filters': True
        }
    }
    
    strategy = OpportunisticVolatilityBreakout(config)
    
    print(f"✅ Strategy initialized with ultra-low thresholds:")
    print(f"   Min confidence: {strategy.min_confidence}")
    print(f"   Volatility threshold: {strategy.volatility_threshold}")
    print(f"   Breakout threshold: {strategy.breakout_threshold}")
    
    # Test: MASSIVE volatility scenario
    print("\n💥 TEST: MASSIVE VOLATILITY SCENARIO")
    print("-" * 40)
    
    current_price = 200.0
    base_prices = []
    
    # Create MASSIVE volatility pattern
    # Phase 1: Stable period (low volatility baseline)
    for i in range(8):
        price = 150.0 + np.random.normal(0, 0.05)  # Very stable
        base_prices.append(price)
    
    # Phase 2: MASSIVE volatility explosion
    # Create huge swings to get volatility_ratio >> 2.0
    volatile_prices = [
        150.0,  # Start
        160.0,  # +6.7%
        140.0,  # -12.5%
        170.0,  # +21.4%
        130.0,  # -23.5%
        180.0,  # +38.5%
        120.0,  # -33.3%
        current_price  # Final price
    ]
    
    base_prices.extend(volatile_prices)
    
    # Populate price history
    for price in base_prices:
        strategy._update_price_history('SOL-USDC', {'price': price})
    
    print(f"✅ Added {len(base_prices)} price points")
    print(f"   Price range: ${min(base_prices):.2f} - ${max(base_prices):.2f}")
    print(f"   Current price: ${current_price:.2f}")
    print(f"   Volatility pattern: Stable → MASSIVE swings")
    
    # Create market data
    market_data = {
        'SOL-USDC': {
            'price': current_price,
            'volume': 1000000,
            'change_24h': 0.20,  # 20% up
            'volatility': 0.15   # 15% volatility
        }
    }
    
    # Generate signal
    signal = strategy.generate_signals(market_data)
    
    if signal:
        print(f"🎉 MASSIVE VOLATILITY SIGNAL GENERATED!")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Market: {signal.get('market', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        print(f"   Price: ${signal.get('price', 0):.2f}")
        
        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        print(f"   Trade Logic: {strategy_metadata.get('trade_logic', 'N/A')}")
        
        if signal.get('action') == 'SELL':
            print("✅ CORRECT: Upward breakout generated SELL signal")
            print("🚀 INTELLIGENT BUY/SELL LOGIC IS WORKING!")
        else:
            print(f"⚠️ Generated {signal.get('action')} signal")
    else:
        print("❌ EVEN MASSIVE VOLATILITY FAILED")
        
        # Ultra-deep debugging
        print("\n🔍 ULTRA-DEEP DEBUGGING:")
        prices = strategy.price_history['SOL-USDC']
        print(f"   All prices: {[f'{p:.1f}' for p in prices]}")
        
        # Calculate everything manually
        prices_array = np.array(prices)
        returns = np.diff(prices_array) / prices_array[:-1]
        
        print(f"   All returns: {[f'{r:.3f}' for r in returns]}")
        
        current_vol = np.std(returns[-10:]) if len(returns) >= 10 else 0.0
        historical_vol = np.std(returns) if len(returns) > 1 else 0.0
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
        
        print(f"   Current volatility: {current_vol:.4f}")
        print(f"   Historical volatility: {historical_vol:.4f}")
        print(f"   Volatility ratio: {vol_ratio:.4f}")
        print(f"   Volatility threshold: {1.0 + strategy.volatility_threshold:.4f}")
        print(f"   Volatility check: {vol_ratio > (1.0 + strategy.volatility_threshold)}")
        
        recent_return = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0.0
        print(f"   Recent return (5-period): {recent_return:.4f}")
        print(f"   Breakout threshold: {strategy.breakout_threshold:.4f}")
        print(f"   Breakout check: {abs(recent_return) > strategy.breakout_threshold}")
        
        # Manual signal calculation
        volatility_signal = 0.0
        if vol_ratio > (1.0 + strategy.volatility_threshold):
            if abs(recent_return) > strategy.breakout_threshold:
                volatility_signal = np.sign(recent_return) * min(1.0, vol_ratio - 1.0)
        
        confidence_multiplier = min(1.0, vol_ratio / 2.0)
        final_signal = volatility_signal * confidence_multiplier
        
        print(f"   Volatility signal: {volatility_signal:.4f}")
        print(f"   Confidence multiplier: {confidence_multiplier:.4f}")
        print(f"   Final signal: {final_signal:.4f}")
        print(f"   Min confidence: {strategy.min_confidence:.4f}")
        print(f"   Signal passes threshold: {abs(final_signal) >= strategy.min_confidence}")
    
    # Test with DOWNWARD massive volatility
    print("\n📉 TEST: MASSIVE DOWNWARD VOLATILITY")
    print("-" * 40)
    
    strategy_down = OpportunisticVolatilityBreakout(config)
    
    # Create downward massive volatility
    down_prices = []
    
    # Stable period
    for i in range(8):
        price = 200.0 + np.random.normal(0, 0.05)
        down_prices.append(price)
    
    # Massive downward volatility
    down_volatile = [
        200.0,  # Start
        180.0,  # -10%
        220.0,  # +22%
        160.0,  # -27%
        240.0,  # +50%
        140.0,  # -42%
        260.0,  # +86%
        120.0   # Final: -40% from start
    ]
    
    down_prices.extend(down_volatile)
    
    for price in down_prices:
        strategy_down._update_price_history('SOL-USDC', {'price': price})
    
    market_data_down = {
        'SOL-USDC': {
            'price': 120.0,
            'volume': 1000000,
            'change_24h': -0.40,  # 40% down
            'volatility': 0.20    # 20% volatility
        }
    }
    
    signal_down = strategy_down.generate_signals(market_data_down)
    
    if signal_down:
        print(f"🎉 DOWNWARD SIGNAL GENERATED!")
        print(f"   Action: {signal_down.get('action', 'N/A')}")
        print(f"   Confidence: {signal_down.get('confidence', 0):.3f}")
        strategy_metadata = signal_down.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        
        if signal_down.get('action') == 'BUY':
            print("✅ CORRECT: Downward breakout generated BUY signal")
            print("🚀 INTELLIGENT BUY/SELL LOGIC CONFIRMED!")
        else:
            print(f"⚠️ Generated {signal_down.get('action')} signal")
    else:
        print("❌ Downward volatility also failed")

if __name__ == "__main__":
    test_massive_volatility()
