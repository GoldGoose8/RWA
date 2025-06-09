#!/usr/bin/env python3
"""
Debug Live System Strategy
==========================

Debug exactly what the live system is doing with the strategy
to find why it's not generating signals.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategies.opportunistic_volatility_breakout import OpportunisticVolatilityBreakout
import numpy as np

def debug_live_system_strategy():
    """Debug the exact strategy flow used in the live system."""
    
    print("🔍 DEBUGGING LIVE SYSTEM STRATEGY FLOW")
    print("=" * 50)
    
    # 🚀 EXACT CONFIG FROM LIVE SYSTEM
    strategy_config = {
        'name': 'opportunistic_volatility_breakout',
        'parameters': {
            'volatility_threshold': 0.01,   # 1% (lower than default 2%)
            'breakout_threshold': 0.005,    # 0.5% (lower than default 1.5%)
            'profit_target_pct': 0.01,      # 1%
            'min_confidence': 0.3,          # 30% (lower than default 80%)
            'risk_level': 'medium',
            'use_filters': True
        }
    }
    
    print("✅ Using EXACT live system config:")
    print(f"   Min confidence: {strategy_config['parameters']['min_confidence']}")
    print(f"   Volatility threshold: {strategy_config['parameters']['volatility_threshold']}")
    print(f"   Breakout threshold: {strategy_config['parameters']['breakout_threshold']}")
    
    strategy = OpportunisticVolatilityBreakout(strategy_config)
    
    # 🚀 EXACT PRICE HISTORY FROM LIVE SYSTEM
    current_price = 157.517073  # Exact price from live system
    market_pair = 'SOL-USDC'
    
    print(f"\n📊 Using exact live system data:")
    print(f"   Current price: ${current_price:.6f}")
    print(f"   Market pair: {market_pair}")
    
    # 🚀 EXACT PRICE HISTORY GENERATION FROM LIVE SYSTEM
    base_prices = []
    
    # Phase 1: Stable period (8 prices) - low volatility baseline
    for i in range(8):
        stable_price = current_price * 0.95 + np.random.normal(0, current_price * 0.001)  # 0.1% volatility
        base_prices.append(stable_price)
    
    # Phase 2: Volatility breakout (7 prices) - higher volatility with trend
    trend_direction = np.random.choice([-1, 1])  # Random up or down trend
    for i in range(7):
        # Create significant price movement (2-3% moves)
        trend_component = trend_direction * (i + 1) * current_price * 0.005  # 0.5% per step
        volatility_component = np.random.normal(0, current_price * 0.015)  # 1.5% volatility
        price = current_price + trend_component + volatility_component
        base_prices.append(max(price, current_price * 0.85))  # Reasonable bounds
    
    # Add current price as latest
    base_prices.append(current_price)
    
    print(f"\n📈 Generated price history:")
    print(f"   Total prices: {len(base_prices)}")
    print(f"   Price range: ${min(base_prices):.2f} - ${max(base_prices):.2f}")
    print(f"   Trend direction: {'+' if trend_direction > 0 else '-'}")
    print(f"   Last 5 prices: {[f'${p:.2f}' for p in base_prices[-5:]]}")
    
    # Populate strategy price history
    for price in base_prices:
        strategy._update_price_history(market_pair, {'price': price})
    
    print(f"✅ Populated {len(base_prices)} price points in strategy")
    
    # 🚀 EXACT MARKET DATA FROM LIVE SYSTEM
    market_data = {
        market_pair: {
            'price': current_price,
            'volume': 1000000,
            'change_24h': 0.0,  # From live system
            'volatility': 0.03
        }
    }
    
    print(f"\n📊 Market data:")
    for key, value in market_data[market_pair].items():
        print(f"   {key}: {value}")
    
    # 🚀 GENERATE SIGNAL (EXACT LIVE SYSTEM FLOW)
    print(f"\n🎯 Generating signal...")
    signal = strategy.generate_signals(market_data)
    
    if signal:
        print(f"🎉 SIGNAL GENERATED!")
        print(f"   Action: {signal.get('action', 'N/A')}")
        print(f"   Market: {signal.get('market', 'N/A')}")
        print(f"   Confidence: {signal.get('confidence', 0):.3f}")
        print(f"   Price: ${signal.get('price', 0):.6f}")
        
        strategy_metadata = signal.get('strategy_metadata', {})
        print(f"   Signal Strength: {strategy_metadata.get('signal_strength', 0):.6f}")
        print(f"   Trade Logic: {strategy_metadata.get('trade_logic', 'N/A')}")
        
        print(f"\n✅ LIVE SYSTEM SHOULD WORK!")
        
    else:
        print(f"❌ NO SIGNAL GENERATED (SAME AS LIVE SYSTEM)")
        
        # 🔍 DEEP DEBUG
        print(f"\n🔍 DEEP DEBUGGING:")
        
        # Check price history
        if market_pair in strategy.price_history:
            prices = strategy.price_history[market_pair]
            print(f"   Price history length: {len(prices)}")
            print(f"   Price history: {[f'{p:.2f}' for p in prices[-10:]]}")
        else:
            print(f"   ❌ NO PRICE HISTORY for {market_pair}")
            return
        
        # Manual signal calculation
        try:
            signal_strength = strategy._calculate_volatility_breakout_signal(market_pair, market_data[market_pair])
            print(f"   Raw signal strength: {signal_strength:.6f}")
            
            if abs(signal_strength) >= strategy.min_confidence:
                print(f"   ✅ Signal strength passes individual threshold ({abs(signal_strength):.3f} >= {strategy.min_confidence})")
                
                # Check overall confidence
                signals = {market_pair: signal_strength}
                confidence = strategy._calculate_overall_confidence(signals)
                print(f"   Overall confidence: {confidence:.6f}")
                
                if confidence >= strategy.min_confidence:
                    print(f"   ✅ Overall confidence passes threshold ({confidence:.3f} >= {strategy.min_confidence})")
                    print(f"   🚨 SIGNAL SHOULD BE GENERATED! BUG IN STRATEGY!")
                else:
                    print(f"   ❌ Overall confidence fails threshold ({confidence:.3f} < {strategy.min_confidence})")
                    
                    # Check confidence calculation
                    max_signal = max(abs(s) for s in signals.values())
                    signal_count_factor = min(1.0, max(0.8, len(signals) / 3.0))
                    expected_confidence = max_signal * signal_count_factor
                    
                    print(f"   Debug confidence calculation:")
                    print(f"     Max signal: {max_signal:.6f}")
                    print(f"     Signal count factor: {signal_count_factor:.6f}")
                    print(f"     Expected confidence: {expected_confidence:.6f}")
                    
            else:
                print(f"   ❌ Signal strength fails individual threshold ({abs(signal_strength):.3f} < {strategy.min_confidence})")
                
                # Debug signal calculation
                print(f"\n   🔍 Signal calculation debug:")
                
                # Check volatility
                if len(prices) >= 10:
                    returns = np.diff(prices) / np.array(prices[:-1])
                    current_vol = np.std(returns[-10:])
                    historical_vol = np.std(returns)
                    vol_ratio = current_vol / historical_vol if historical_vol > 0 else 1.0
                    
                    print(f"     Current volatility: {current_vol:.6f}")
                    print(f"     Historical volatility: {historical_vol:.6f}")
                    print(f"     Volatility ratio: {vol_ratio:.6f}")
                    print(f"     Volatility threshold: {1.0 + strategy.volatility_threshold:.6f}")
                    print(f"     Volatility check: {vol_ratio > (1.0 + strategy.volatility_threshold)}")
                    
                    # Check recent return
                    recent_return = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0.0
                    print(f"     Recent return (5-period): {recent_return:.6f}")
                    print(f"     Breakout threshold: {strategy.breakout_threshold:.6f}")
                    print(f"     Breakout check: {abs(recent_return) > strategy.breakout_threshold}")
                    
                    # Manual calculation
                    volatility_signal = 0.0
                    if vol_ratio > (1.0 + strategy.volatility_threshold):
                        if abs(recent_return) > strategy.breakout_threshold:
                            volatility_signal = np.sign(recent_return) * min(1.0, vol_ratio - 1.0)
                    
                    confidence_multiplier = min(1.0, vol_ratio / 2.0)
                    final_signal = volatility_signal * confidence_multiplier
                    
                    print(f"     Volatility signal: {volatility_signal:.6f}")
                    print(f"     Confidence multiplier: {confidence_multiplier:.6f}")
                    print(f"     Final signal: {final_signal:.6f}")
                    
                else:
                    print(f"     ❌ Insufficient price history ({len(prices)} < 10)")
                    
        except Exception as e:
            print(f"   ❌ Error in signal calculation: {e}")
    
    # Test with EXTREME volatility to force a signal
    print(f"\n💥 TESTING WITH EXTREME VOLATILITY:")
    
    strategy_extreme = OpportunisticVolatilityBreakout(strategy_config)
    
    # Create extreme volatility pattern
    extreme_prices = [
        150.0, 150.0, 150.0, 150.0, 150.0,  # Stable
        160.0, 140.0, 170.0, 130.0, 180.0,  # Massive swings
        120.0, current_price  # Final
    ]
    
    for price in extreme_prices:
        strategy_extreme._update_price_history(market_pair, {'price': price})
    
    signal_extreme = strategy_extreme.generate_signals(market_data)
    
    if signal_extreme:
        print(f"✅ EXTREME volatility generated signal: {signal_extreme.get('action')}")
        print(f"   Signal strength: {signal_extreme.get('strategy_metadata', {}).get('signal_strength', 0):.6f}")
    else:
        print(f"❌ Even EXTREME volatility failed")

if __name__ == "__main__":
    debug_live_system_strategy()
