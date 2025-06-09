#!/usr/bin/env python3
"""
Test Strategy with Pre-populated History
========================================

Test the strategy with pre-populated price history to verify
signal generation is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def test_strategy_with_history():
    """Test strategy with pre-populated price history."""

    print("🧪 TESTING STRATEGY WITH PRE-POPULATED HISTORY")
    print("=" * 55)

    # Initialize strategy with config
    config = {
        'strategies': {
            'opportunistic_volatility_breakout': {
                'volatility_threshold': 0.02,
                'breakout_threshold': 0.01,
                'profit_target_pct': 0.02,
                'min_confidence': 0.7,
                'risk_level': 'medium',
                'use_filters': True
            }
        }
    }

    strategy = OpportunisticVolatilityBreakout(config)

    # Test 1: Upward trend (should generate SELL)
    print("\n📈 TEST 1: UPWARD TREND (Should generate SELL)")
    print("-" * 45)

    current_price = 157.5
    base_prices = []

    # Create upward trending price history with HIGH VOLATILITY
    for i in range(15):
        # Create STRONG upward trend (3% total movement)
        trend_component = i * 0.3  # Stronger upward trend
        # Create HIGH volatility (strategy needs volatility > 2%)
        volatility_component = np.random.normal(0, 1.5)  # Much higher volatility
        price = current_price - 5.0 + trend_component + volatility_component
        base_prices.append(max(price, current_price * 0.90))  # Allow wider range

    base_prices.append(current_price)

    # Populate price history
    for price in base_prices:
        strategy._update_price_history('SOL-USDC', {'price': price})

    print(f"✅ Added {len(base_prices)} price points")
    print(f"   Price range: ${min(base_prices):.2f} - ${max(base_prices):.2f}")
    print(f"   Current price: ${current_price:.2f}")

    # Create market data
    market_data = {
        'SOL-USDC': {
            'price': current_price,
            'volume': 1000000,
            'change_24h': 0.03,  # 3% up
            'volatility': 0.025
        }
    }

    # Generate signal
    signal = strategy.generate_signals(market_data)

    if signal:
        print(f"✅ Signal Generated:")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Market: {signal.get('market', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        print(f"   Price: ${signal.get('price', 0):.2f}")

        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        print(f"   Trade Logic: {strategy_metadata.get('trade_logic', 'N/A')}")

        if signal.get('action') == 'SELL':
            print("✅ CORRECT: Upward trend generated SELL signal")
        elif signal.get('action') == 'BUY':
            print("⚠️ UNEXPECTED: Upward trend generated BUY signal")
        else:
            print(f"❓ UNKNOWN: Generated {signal.get('action')} signal")
    else:
        print("❌ NO SIGNAL GENERATED")

        # Debug: Check strategy internals
        print("\n🔍 DEBUGGING:")
        print(f"   Price history length: {len(strategy.price_history.get('SOL-USDC', []))}")

        if 'SOL-USDC' in strategy.price_history:
            prices = strategy.price_history['SOL-USDC']  # Already floats
            print(f"   Price history: {prices[-5:]}")  # Last 5 prices

            # Check signal strength directly
            signal_strength = strategy._calculate_volatility_breakout_signal('SOL-USDC', market_data['SOL-USDC'])
            print(f"   Signal strength: {signal_strength:.4f}")

            # Check confidence
            signals = {'SOL-USDC': signal_strength} if signal_strength != 0 else {}
            confidence = strategy._calculate_overall_confidence(signals)
            print(f"   Confidence: {confidence:.4f}")

            # Check thresholds
            config_strategy = config['strategies']['opportunistic_volatility_breakout']
            print(f"   Min confidence threshold: {config_strategy['min_confidence']}")
            print(f"   Volatility threshold: {config_strategy['volatility_threshold']}")
            print(f"   Breakout threshold: {config_strategy['breakout_threshold']}")

    # Test 2: Downward trend (should generate BUY)
    print("\n📉 TEST 2: DOWNWARD TREND (Should generate BUY)")
    print("-" * 45)

    # Reset strategy
    strategy = OpportunisticVolatilityBreakout(config)

    current_price = 155.0
    base_prices = []

    # Create downward trending price history with HIGH VOLATILITY
    for i in range(15):
        # Create STRONG downward trend (3% total movement)
        trend_component = -i * 0.4  # Stronger downward trend
        # Create HIGH volatility (strategy needs volatility > 2%)
        volatility_component = np.random.normal(0, 1.5)  # Much higher volatility
        price = current_price + 6.0 + trend_component + volatility_component
        base_prices.append(max(price, current_price * 0.85))  # Allow wider range

    base_prices.append(current_price)

    # Populate price history
    for price in base_prices:
        strategy._update_price_history('SOL-USDC', {'price': price})

    print(f"✅ Added {len(base_prices)} price points")
    print(f"   Price range: ${min(base_prices):.2f} - ${max(base_prices):.2f}")
    print(f"   Current price: ${current_price:.2f}")

    # Create market data
    market_data = {
        'SOL-USDC': {
            'price': current_price,
            'volume': 1000000,
            'change_24h': -0.03,  # 3% down
            'volatility': 0.025
        }
    }

    # Generate signal
    signal = strategy.generate_signals(market_data)

    if signal:
        print(f"✅ Signal Generated:")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Market: {signal.get('market', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        print(f"   Price: ${signal.get('price', 0):.2f}")

        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.3f}")
        print(f"   Trade Logic: {strategy_metadata.get('trade_logic', 'N/A')}")

        if signal.get('action') == 'BUY':
            print("✅ CORRECT: Downward trend generated BUY signal")
        elif signal.get('action') == 'SELL':
            print("⚠️ UNEXPECTED: Downward trend generated SELL signal")
        else:
            print(f"❓ UNKNOWN: Generated {signal.get('action')} signal")
    else:
        print("❌ NO SIGNAL GENERATED")

        # Debug: Check strategy internals
        print("\n🔍 DEBUGGING:")
        print(f"   Price history length: {len(strategy.price_history.get('SOL-USDC', []))}")

        if 'SOL-USDC' in strategy.price_history:
            prices = strategy.price_history['SOL-USDC']  # Already floats
            print(f"   Price history: {prices[-5:]}")  # Last 5 prices

            # Check signal strength directly
            signal_strength = strategy._calculate_volatility_breakout_signal('SOL-USDC', market_data['SOL-USDC'])
            print(f"   Signal strength: {signal_strength:.4f}")

            # Check confidence
            signals = {'SOL-USDC': signal_strength} if signal_strength != 0 else {}
            confidence = strategy._calculate_overall_confidence(signals)
            print(f"   Confidence: {confidence:.4f}")

if __name__ == "__main__":
    test_strategy_with_history()
