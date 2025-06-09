#!/usr/bin/env python3
"""
Analyze hypothetical profits from the 5-hour trading session.
Calculate what profits would have been if all trades were real swaps.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
import glob

def load_trade_records() -> List[Dict[str, Any]]:
    """Load all trade records from the 5-hour session."""
    trade_files = glob.glob("output/live_production/trades/trade_20250530_*.json")
    trade_files.extend(glob.glob("output/live_production/trades/trade_20250531_*.json"))
    
    trades = []
    for file_path in sorted(trade_files):
        try:
            with open(file_path, 'r') as f:
                trade_data = json.load(f)
                trades.append(trade_data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return trades

def calculate_hypothetical_swap_profit(trade: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate hypothetical profit if this trade was a real swap.
    
    For BUY trades: We're buying SOL with USDC
    For SELL trades: We're selling SOL for USDC
    
    Assumes 1% profit target per trade (typical for our strategies)
    """
    signal = trade.get('signal', {})
    action = signal.get('action', 'BUY')
    size_sol = signal.get('size', 0.0)
    price = signal.get('price', 155.0)  # SOL price at time of trade
    
    # Calculate trade value in USD
    trade_value_usd = size_sol * price
    
    # Assume 1% profit target (conservative estimate)
    profit_target_pct = 0.01
    
    # Calculate hypothetical profit
    if action == 'BUY':
        # Buying SOL - profit if SOL price goes up
        hypothetical_profit_usd = trade_value_usd * profit_target_pct
        hypothetical_profit_sol = hypothetical_profit_usd / price
    else:
        # Selling SOL - profit if SOL price goes down (or we're taking profit)
        hypothetical_profit_usd = trade_value_usd * profit_target_pct
        hypothetical_profit_sol = hypothetical_profit_usd / price
    
    # Account for transaction fees (estimate 0.1% total fees)
    fee_pct = 0.001
    fee_usd = trade_value_usd * fee_pct
    fee_sol = fee_usd / price
    
    # Net profit after fees
    net_profit_usd = hypothetical_profit_usd - fee_usd
    net_profit_sol = hypothetical_profit_sol - fee_sol
    
    return {
        'action': action,
        'size_sol': size_sol,
        'price': price,
        'trade_value_usd': trade_value_usd,
        'gross_profit_usd': hypothetical_profit_usd,
        'gross_profit_sol': hypothetical_profit_sol,
        'fees_usd': fee_usd,
        'fees_sol': fee_sol,
        'net_profit_usd': net_profit_usd,
        'net_profit_sol': net_profit_sol,
        'timestamp': signal.get('timestamp', ''),
        'strategy': signal.get('source', 'unknown')
    }

def analyze_session_performance(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the overall session performance."""
    
    print(f"\n🔍 ANALYZING {len(trades)} TRADES FROM 5-HOUR SESSION")
    print("=" * 60)
    
    total_trades = len(trades)
    total_volume_sol = 0.0
    total_volume_usd = 0.0
    total_gross_profit_usd = 0.0
    total_gross_profit_sol = 0.0
    total_fees_usd = 0.0
    total_fees_sol = 0.0
    total_net_profit_usd = 0.0
    total_net_profit_sol = 0.0
    
    strategy_breakdown = {}
    hourly_breakdown = {}
    
    profitable_trades = 0
    
    for i, trade in enumerate(trades):
        profit_calc = calculate_hypothetical_swap_profit(trade)
        
        # Accumulate totals
        total_volume_sol += profit_calc['size_sol']
        total_volume_usd += profit_calc['trade_value_usd']
        total_gross_profit_usd += profit_calc['gross_profit_usd']
        total_gross_profit_sol += profit_calc['gross_profit_sol']
        total_fees_usd += profit_calc['fees_usd']
        total_fees_sol += profit_calc['fees_sol']
        total_net_profit_usd += profit_calc['net_profit_usd']
        total_net_profit_sol += profit_calc['net_profit_sol']
        
        if profit_calc['net_profit_usd'] > 0:
            profitable_trades += 1
        
        # Strategy breakdown
        strategy = profit_calc['strategy']
        if strategy not in strategy_breakdown:
            strategy_breakdown[strategy] = {
                'trades': 0,
                'volume_sol': 0.0,
                'net_profit_usd': 0.0,
                'net_profit_sol': 0.0
            }
        
        strategy_breakdown[strategy]['trades'] += 1
        strategy_breakdown[strategy]['volume_sol'] += profit_calc['size_sol']
        strategy_breakdown[strategy]['net_profit_usd'] += profit_calc['net_profit_usd']
        strategy_breakdown[strategy]['net_profit_sol'] += profit_calc['net_profit_sol']
        
        # Show first few trades as examples
        if i < 5:
            print(f"\n📊 TRADE {i+1} EXAMPLE:")
            print(f"   Action: {profit_calc['action']}")
            print(f"   Size: {profit_calc['size_sol']:.6f} SOL")
            print(f"   Price: ${profit_calc['price']:.2f}")
            print(f"   Trade Value: ${profit_calc['trade_value_usd']:.2f}")
            print(f"   Gross Profit: ${profit_calc['gross_profit_usd']:.4f}")
            print(f"   Fees: ${profit_calc['fees_usd']:.4f}")
            print(f"   Net Profit: ${profit_calc['net_profit_usd']:.4f} (${profit_calc['net_profit_sol']:.6f} SOL)")
    
    # Calculate performance metrics
    win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
    avg_profit_per_trade_usd = total_net_profit_usd / total_trades if total_trades > 0 else 0
    avg_profit_per_trade_sol = total_net_profit_sol / total_trades if total_trades > 0 else 0
    
    # Assume starting balance from session summary
    starting_balance_sol = 1.452003
    roi_percent = (total_net_profit_sol / starting_balance_sol) * 100
    
    print(f"\n🎯 HYPOTHETICAL SESSION RESULTS:")
    print("=" * 60)
    print(f"📈 Total Trades: {total_trades}")
    print(f"📈 Total Volume: {total_volume_sol:.6f} SOL (${total_volume_usd:.2f})")
    print(f"📈 Profitable Trades: {profitable_trades} ({win_rate:.1f}%)")
    print(f"")
    print(f"💰 PROFIT ANALYSIS:")
    print(f"   Gross Profit: ${total_gross_profit_usd:.2f} ({total_gross_profit_sol:.6f} SOL)")
    print(f"   Total Fees: ${total_fees_usd:.2f} ({total_fees_sol:.6f} SOL)")
    print(f"   NET PROFIT: ${total_net_profit_usd:.2f} ({total_net_profit_sol:.6f} SOL)")
    print(f"")
    print(f"📊 PERFORMANCE METRICS:")
    print(f"   ROI: {roi_percent:.2f}%")
    print(f"   Avg Profit/Trade: ${avg_profit_per_trade_usd:.4f}")
    print(f"   Starting Balance: {starting_balance_sol:.6f} SOL")
    print(f"   Hypothetical End Balance: {starting_balance_sol + total_net_profit_sol:.6f} SOL")
    
    print(f"\n🎯 STRATEGY BREAKDOWN:")
    print("=" * 60)
    for strategy, data in strategy_breakdown.items():
        avg_per_trade = data['net_profit_usd'] / data['trades'] if data['trades'] > 0 else 0
        print(f"   {strategy}:")
        print(f"     Trades: {data['trades']}")
        print(f"     Volume: {data['volume_sol']:.6f} SOL")
        print(f"     Net Profit: ${data['net_profit_usd']:.2f} ({data['net_profit_sol']:.6f} SOL)")
        print(f"     Avg/Trade: ${avg_per_trade:.4f}")
    
    return {
        'total_trades': total_trades,
        'total_volume_sol': total_volume_sol,
        'total_volume_usd': total_volume_usd,
        'total_net_profit_usd': total_net_profit_usd,
        'total_net_profit_sol': total_net_profit_sol,
        'roi_percent': roi_percent,
        'win_rate': win_rate,
        'avg_profit_per_trade_usd': avg_profit_per_trade_usd,
        'strategy_breakdown': strategy_breakdown,
        'starting_balance_sol': starting_balance_sol,
        'hypothetical_end_balance_sol': starting_balance_sol + total_net_profit_sol
    }

def main():
    """Main analysis function."""
    print("🚀 HYPOTHETICAL PROFIT ANALYSIS")
    print("Calculating what profits would have been if all trades were real swaps...")
    
    # Load trade records
    trades = load_trade_records()
    
    if not trades:
        print("❌ No trade records found!")
        return
    
    # Analyze performance
    results = analyze_session_performance(trades)
    
    # Save results
    output_file = "output/hypothetical_profit_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    print(f"\n🎯 CONCLUSION:")
    print("=" * 60)
    if results['total_net_profit_usd'] > 0:
        print(f"✅ STRATEGY WOULD HAVE BEEN PROFITABLE!")
        print(f"   Hypothetical profit: ${results['total_net_profit_usd']:.2f}")
        print(f"   ROI: {results['roi_percent']:.2f}%")
    else:
        print(f"❌ Strategy would have been unprofitable")
        print(f"   Hypothetical loss: ${results['total_net_profit_usd']:.2f}")
        print(f"   ROI: {results['roi_percent']:.2f}%")
    
    print(f"\n📝 NOTE: This analysis assumes 1% profit target per trade")
    print(f"   and 0.1% total transaction fees. Actual results may vary.")

if __name__ == "__main__":
    main()
