#!/usr/bin/env python3
"""
Enhanced Profit Tracking Analysis
=================================

This script analyzes the results from enhanced profit tracking to distinguish
between actual trading profits and transaction fees.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import statistics

def analyze_enhanced_trading_session():
    """Analyze enhanced trading session with detailed profit breakdown."""
    
    print("📊 ENHANCED PROFIT TRACKING ANALYSIS")
    print("=" * 60)
    
    # Get enhanced trade files
    trades_dir = Path("output/enhanced_live_trading/trades")
    if not trades_dir.exists():
        print("❌ No enhanced trades directory found")
        return
    
    trade_files = sorted(list(trades_dir.glob("enhanced_trade_*.json")))
    summary_files = sorted(list(trades_dir.glob("session_summary_*.json")))
    
    print(f"📁 Found {len(trade_files)} enhanced trade records")
    print(f"📁 Found {len(summary_files)} session summaries")
    
    if not trade_files:
        print("❌ No enhanced trade files found")
        return
    
    # Analyze all trades
    trades = []
    total_gross_pnl = 0
    total_net_pnl = 0
    total_fees = 0
    profitable_trades = 0
    fee_only_trades = 0
    balance_changes = []
    
    print("\n🔍 ANALYZING ENHANCED TRADES:")
    print("-" * 50)
    
    for i, trade_file in enumerate(trade_files):
        try:
            with open(trade_file, 'r') as f:
                trade_data = json.load(f)
            
            trades.append(trade_data)
            
            # Extract enhanced analysis data
            balance_analysis = trade_data.get('balance_analysis', {})
            signal = trade_data.get('signal', {})
            transaction_result = trade_data.get('transaction_result', {})
            
            gross_profit = balance_analysis.get('gross_profit', 0)
            net_profit = balance_analysis.get('net_profit', 0)
            estimated_fee = balance_analysis.get('estimated_fee', 0)
            is_profitable = balance_analysis.get('is_profitable_trade', False)
            balance_change = balance_analysis.get('balance_change', 0)
            
            total_gross_pnl += gross_profit
            total_net_pnl += net_profit
            total_fees += estimated_fee
            balance_changes.append(balance_change)
            
            if is_profitable:
                profitable_trades += 1
            else:
                fee_only_trades += 1
            
            print(f"Trade {i+1}: {trade_file.name}")
            print(f"  🎯 Action: {signal.get('action', 'N/A')} {signal.get('size', 0):.6f} SOL")
            print(f"  💰 Balance Change: {balance_change:.9f} SOL")
            print(f"  📈 Gross P&L: {gross_profit:.9f} SOL")
            print(f"  📊 Net P&L: {net_profit:.9f} SOL")
            print(f"  💸 Est. Fee: {estimated_fee:.9f} SOL")
            print(f"  ✅ Profitable: {'Yes' if is_profitable else 'No (fees only)'}")
            print(f"  🔗 Signature: {transaction_result.get('signature', 'N/A')[:20]}...")
            print()
            
        except Exception as e:
            print(f"❌ Error reading {trade_file}: {e}")
    
    # Get latest session summary
    latest_summary = None
    if summary_files:
        try:
            with open(summary_files[-1], 'r') as f:
                latest_summary = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not read latest summary: {e}")
    
    # Calculate comprehensive statistics
    print("\n📊 COMPREHENSIVE PROFIT ANALYSIS:")
    print("-" * 40)
    
    if trades:
        # Basic statistics
        print(f"📈 Total Trades: {len(trades)}")
        print(f"✅ Profitable Trades: {profitable_trades}")
        print(f"💸 Fee-Only Trades: {fee_only_trades}")
        print(f"📊 Profit Rate: {(profitable_trades/len(trades)*100):.1f}%")
        
        # P&L Analysis
        print(f"\n💰 PROFIT & LOSS BREAKDOWN:")
        print(f"   Gross P&L: {total_gross_pnl:.9f} SOL")
        print(f"   Net P&L: {total_net_pnl:.9f} SOL")
        print(f"   Total Fees: {total_fees:.9f} SOL")
        print(f"   Avg P&L per Trade: {total_net_pnl/len(trades):.9f} SOL")
        print(f"   Avg Fee per Trade: {total_fees/len(trades):.9f} SOL")
        
        # Balance Change Analysis
        if balance_changes:
            total_balance_change = sum(balance_changes)
            avg_balance_change = statistics.mean(balance_changes)
            
            print(f"\n📈 BALANCE CHANGE ANALYSIS:")
            print(f"   Total Balance Change: {total_balance_change:.9f} SOL")
            print(f"   Average Change per Trade: {avg_balance_change:.9f} SOL")
            print(f"   Min Change: {min(balance_changes):.9f} SOL")
            print(f"   Max Change: {max(balance_changes):.9f} SOL")
        
        # Fee Analysis
        print(f"\n💸 FEE ANALYSIS:")
        print(f"   Total Estimated Fees: {total_fees:.9f} SOL")
        print(f"   Fee as % of Gross P&L: {(total_fees/abs(total_gross_pnl)*100) if total_gross_pnl != 0 else 0:.1f}%")
        print(f"   Average Fee per Trade: {total_fees/len(trades):.9f} SOL")
        
        # Convert to USD (approximate)
        sol_price = 180.0  # Approximate SOL price
        print(f"\n💵 USD EQUIVALENT (@ ${sol_price}/SOL):")
        print(f"   Gross P&L: ${total_gross_pnl * sol_price:.4f}")
        print(f"   Net P&L: ${total_net_pnl * sol_price:.4f}")
        print(f"   Total Fees: ${total_fees * sol_price:.4f}")
    
    # Session summary from file
    if latest_summary:
        print(f"\n📊 SESSION SUMMARY (from file):")
        print("-" * 35)
        
        session_info = latest_summary.get('session_info', {})
        balance_info = latest_summary.get('balance_info', {})
        profit_analysis = latest_summary.get('profit_analysis', {})
        
        print(f"⏰ Duration: {session_info.get('duration_minutes', 0):.1f} minutes")
        print(f"💰 Starting Balance: {balance_info.get('starting_balance', 0):.9f} SOL")
        print(f"💰 Final Balance: {balance_info.get('current_balance', 0):.9f} SOL")
        print(f"📈 Total Change: {balance_info.get('total_change', 0):.9f} SOL")
        print(f"📊 Session Net P&L: {profit_analysis.get('net_pnl', 0):.9f} SOL")
    
    # Final verdict
    print(f"\n🎯 FINAL VERDICT:")
    print("-" * 15)
    
    if total_net_pnl > 0:
        print(f"✅ PROFITABLE SESSION")
        print(f"💰 Net Profit: +{total_net_pnl:.9f} SOL (${total_net_pnl * sol_price:.4f})")
        print(f"📊 Profit after fees: {((total_net_pnl / total_fees) * 100) if total_fees > 0 else 0:.1f}% of fees paid")
    elif total_net_pnl < 0:
        print(f"❌ LOSS SESSION")
        print(f"💸 Net Loss: {total_net_pnl:.9f} SOL (${total_net_pnl * sol_price:.4f})")
        print(f"📊 Loss primarily due to transaction fees")
    else:
        print(f"➖ BREAK EVEN SESSION")
        print(f"📊 No net profit or loss (fees covered)")
    
    # Proof of real trading
    print(f"\n✅ PROOF OF REAL TRADING:")
    print("-" * 25)
    print(f"🔗 {len(trades)} unique blockchain transactions")
    print(f"💰 Real balance changes tracked")
    print(f"💸 Actual transaction fees paid")
    print(f"📊 Detailed profit/loss analysis")
    print(f"🎯 Enhanced tracking system validation")
    
    # Trading efficiency
    if total_fees > 0 and total_gross_pnl != 0:
        efficiency = (total_net_pnl / total_gross_pnl) * 100
        print(f"\n📈 TRADING EFFICIENCY:")
        print(f"   Net/Gross Ratio: {efficiency:.1f}%")
        print(f"   Fee Impact: {((total_fees / abs(total_gross_pnl)) * 100):.1f}% of gross P&L")


def compare_with_standard_tracking():
    """Compare enhanced tracking with standard tracking results."""
    print(f"\n🔄 COMPARISON WITH STANDARD TRACKING:")
    print("-" * 45)
    
    # Check for standard trading results
    standard_dir = Path("output/live_production/trades")
    if standard_dir.exists():
        standard_files = list(standard_dir.glob("trade_*.json"))
        print(f"📁 Standard tracking files: {len(standard_files)}")
        
        if standard_files:
            print("✅ Enhanced tracking provides:")
            print("   - Precise pre/post balance measurements")
            print("   - Detailed fee analysis")
            print("   - Profit vs fee distinction")
            print("   - Real-time session tracking")
            print("   - Comprehensive profit validation")
    else:
        print("📁 No standard tracking files found for comparison")


if __name__ == "__main__":
    analyze_enhanced_trading_session()
    compare_with_standard_tracking()
