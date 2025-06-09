#!/usr/bin/env python3
"""
Test Strategy with Extreme Volatility
=====================================

Test the strategy with extreme volatility to trigger signals.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def test_extreme_volatility():
    """Test strategy with extreme volatility to trigger signals."""

    print("🧪 TESTING STRATEGY WITH EXTREME VOLATILITY")
    print("=" * 50)

    # Initialize strategy with LOWER thresholds
    config = {
        'name': 'opportunistic_volatility_breakout',
        'parameters': {
            'volatility_threshold': 0.01,  # Lower threshold (1%)
            'breakout_threshold': 0.005,   # Lower threshold (0.5%)
            'profit_target_pct': 0.02,
            'min_confidence': 0.3,         # Much lower confidence threshold
            'risk_level': 'medium',
            'use_filters': True
        }
    }

    strategy = OpportunisticVolatilityBreakout(config)

    print(f"✅ Strategy initialized with:")
    print(f"   Min confidence: {strategy.min_confidence}")
    print(f"   Volatility threshold: {strategy.volatility_threshold}")
    print(f"   Breakout threshold: {strategy.breakout_threshold}")

    # Test 1: EXTREME upward breakout
    print("\n🚀 TEST 1: EXTREME UPWARD BREAKOUT")
    print("-" * 40)

    current_price = 160.0
    base_prices = []

    # Create EXTREME volatility pattern
    # Start with stable prices, then MASSIVE breakout
    for i in range(10):
        # Stable period with low volatility
        price = 150.0 + np.random.normal(0, 0.1)
        base_prices.append(price)

    # Then MASSIVE upward breakout (10% move)
    for i in range(5):
        price = 150.0 + (i + 1) * 2.0  # 2% per step = 10% total
        base_prices.append(price)

    base_prices.append(current_price)  # Final price

    # Populate price history
    for price in base_prices:
        strategy._update_price_history('SOL-USDC', {'price': price})

    print(f"✅ Added {len(base_prices)} price points")
    print(f"   Price range: ${min(base_prices):.2f} - ${max(base_prices):.2f}")
    print(f"   Current price: ${current_price:.2f}")
    print(f"   Total movement: {((max(base_prices) - min(base_prices)) / min(base_prices) * 100):.1f}%")

    # Create market data
    market_data = {
        'SOL-USDC': {
            'price': current_price,
            'volume': 1000000,
            'change_24h': 0.10,  # 10% up
            'volatility': 0.05   # 5% volatility
        }
    }

    # Generate signal
    signal = strategy.generate_signals(market_data)

    if signal:
        print(f"🎉 SIGNAL GENERATED!")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Market: {signal.get('market', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        print(f"   Price: ${signal.get('price', 0):.2f}")

        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        print(f"   Trade Logic: {strategy_metadata.get('trade_logic', 'N/A')}")

        if signal.get('action') == 'SELL':
            print("✅ CORRECT: Upward breakout generated SELL signal")
        else:
            print(f"⚠️ UNEXPECTED: Generated {signal.get('action')} signal")
    else:
        print("❌ STILL NO SIGNAL GENERATED")

        # Deep debugging
        print("\n🔍 DEEP DEBUGGING:")
        prices = strategy.price_history['SOL-USDC']
        print(f"   All prices: {[f'{p:.1f}' for p in prices]}")

        # Calculate returns manually
        returns = np.diff(prices) / np.array(prices[:-1])
        print(f"   Returns: {[f'{r:.3f}' for r in returns[-5:]]}")

        # Calculate volatilities manually
        current_vol = np.std(returns[-10:]) if len(returns) >= 10 else 0.0
        historical_vol = np.std(returns) if len(returns) > 1 else 0.0
        vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0

        print(f"   Current volatility: {current_vol:.4f}")
        print(f"   Historical volatility: {historical_vol:.4f}")
        print(f"   Volatility ratio: {vol_ratio:.4f}")
        print(f"   Volatility threshold: {1.0 + strategy.volatility_threshold:.4f}")

        # Calculate recent return
        recent_return = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0.0
        print(f"   Recent return (5-period): {recent_return:.4f}")
        print(f"   Breakout threshold: {strategy.breakout_threshold:.4f}")

        # Check signal generation step by step
        signal_strength = strategy._calculate_volatility_breakout_signal('SOL-USDC', market_data['SOL-USDC'])
        print(f"   Final signal strength: {signal_strength:.4f}")
        print(f"   Min confidence required: {strategy.min_confidence:.4f}")

    # Test 2: Try with even MORE extreme settings
    print("\n💥 TEST 2: ULTRA-EXTREME SETTINGS")
    print("-" * 35)

    # Ultra-low thresholds
    config_extreme = {
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

    strategy_extreme = OpportunisticVolatilityBreakout(config_extreme)

    # Use same price history
    for price in base_prices:
        strategy_extreme._update_price_history('SOL-USDC', {'price': price})

    signal_extreme = strategy_extreme.generate_signals(market_data)

    if signal_extreme:
        print(f"🎉 ULTRA-EXTREME SIGNAL GENERATED!")
        print(f"   Action: {signal_extreme.get('action', 'N/A')}")
        print(f"   Confidence: {signal_extreme.get('confidence', 0):.3f}")
        strategy_metadata = signal_extreme.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
    else:
        print("❌ Even ultra-extreme settings failed")

        # Final debugging
        signal_strength = strategy_extreme._calculate_volatility_breakout_signal('SOL-USDC', market_data['SOL-USDC'])
        print(f"   Signal strength: {signal_strength:.6f}")
        print(f"   Min confidence: {strategy_extreme.min_confidence:.6f}")

if __name__ == "__main__":
    test_extreme_volatility()
