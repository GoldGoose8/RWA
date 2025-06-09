#!/usr/bin/env python3
"""
Real-Time Live Trading Profit Monitor
====================================

This script monitors live trading in real-time and provides immediate
profit/loss analysis with wallet proof for each trade.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LiveTradingMonitor:
    """Real-time monitor for live trading profits."""
    
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.trades_monitored = 0
        self.target_trades = 3
        self.monitoring = True
        
        # Directories to monitor
        self.enhanced_trades_dir = Path("output/enhanced_live_trading/trades")
        self.standard_trades_dir = Path("output/live_production/trades")
        
        # Track processed files
        self.processed_files = set()
        
        print("🔍 LIVE TRADING PROFIT MONITOR INITIALIZED")
        print("=" * 60)
        print(f"👤 Wallet: {self.wallet_address}")
        print(f"🎯 Target trades to monitor: {self.target_trades}")
        print(f"📁 Monitoring directories:")
        print(f"   - Enhanced: {self.enhanced_trades_dir}")
        print(f"   - Standard: {self.standard_trades_dir}")
        print("=" * 60)
    
    async def get_current_balance(self) -> float:
        """Get current wallet balance for verification."""
        try:
            import httpx
            
            rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address]
                }
                
                response = await client.post(rpc_url, json=payload)
                data = response.json()
                
                if 'result' in data and 'value' in data['result']:
                    balance_lamports = data['result']['value']
                    balance_sol = balance_lamports / 1_000_000_000
                    return balance_sol
                else:
                    return None
                    
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return None
    
    def analyze_trade_file(self, trade_file: Path) -> dict:
        """Analyze a single trade file for profit/loss."""
        try:
            with open(trade_file, 'r') as f:
                trade_data = json.load(f)
            
            # Check if this is enhanced or standard format
            if 'balance_analysis' in trade_data:
                # Enhanced format
                return self.analyze_enhanced_trade(trade_data)
            else:
                # Standard format
                return self.analyze_standard_trade(trade_data)
                
        except Exception as e:
            print(f"❌ Error analyzing {trade_file}: {e}")
            return None
    
    def analyze_enhanced_trade(self, trade_data: dict) -> dict:
        """Analyze enhanced trade format."""
        balance_analysis = trade_data.get('balance_analysis', {})
        signal = trade_data.get('signal', {})
        transaction_result = trade_data.get('transaction_result', {})
        
        return {
            'format': 'enhanced',
            'timestamp': trade_data.get('timestamp'),
            'action': signal.get('action'),
            'size': signal.get('size'),
            'pre_balance': balance_analysis.get('pre_balance'),
            'post_balance': balance_analysis.get('post_balance'),
            'balance_change': balance_analysis.get('balance_change'),
            'gross_profit': balance_analysis.get('gross_profit'),
            'net_profit': balance_analysis.get('net_profit'),
            'estimated_fee': balance_analysis.get('estimated_fee'),
            'is_profitable': balance_analysis.get('is_profitable_trade'),
            'signature': transaction_result.get('signature'),
            'success': transaction_result.get('success', False)
        }
    
    def analyze_standard_trade(self, trade_data: dict) -> dict:
        """Analyze standard trade format."""
        signal = trade_data.get('signal', {})
        result = trade_data.get('result', {})
        balance_val = trade_data.get('balance_validation', {})
        
        balance_change = balance_val.get('balance_change', 0)
        estimated_fee = 0.000005  # Standard Solana fee
        
        return {
            'format': 'standard',
            'timestamp': trade_data.get('timestamp'),
            'action': signal.get('action'),
            'size': signal.get('size'),
            'pre_balance': balance_val.get('balance_before'),
            'post_balance': balance_val.get('balance_after'),
            'balance_change': balance_change,
            'gross_profit': balance_change + estimated_fee if balance_change else 0,
            'net_profit': balance_change,
            'estimated_fee': estimated_fee,
            'is_profitable': abs(balance_change) > estimated_fee * 2 if balance_change else False,
            'signature': result.get('signature'),
            'success': result.get('success', False)
        }
    
    def print_trade_analysis(self, analysis: dict, trade_number: int):
        """Print detailed trade analysis."""
        print(f"\n🚀 TRADE #{trade_number} ANALYSIS ({analysis['format'].upper()} FORMAT)")
        print("=" * 70)
        print(f"⏰ Timestamp: {analysis['timestamp']}")
        print(f"🎯 Action: {analysis['action']} {analysis['size']:.6f} SOL")
        print(f"✅ Success: {analysis['success']}")
        print(f"🔗 Signature: {analysis['signature']}")
        
        print(f"\n💰 BALANCE ANALYSIS:")
        if analysis['pre_balance'] and analysis['post_balance']:
            print(f"   Pre-trade:  {analysis['pre_balance']:.9f} SOL")
            print(f"   Post-trade: {analysis['post_balance']:.9f} SOL")
            print(f"   Change:     {analysis['balance_change']:.9f} SOL")
        else:
            print(f"   Balance change: {analysis['balance_change']:.9f} SOL")
        
        print(f"\n📊 PROFIT ANALYSIS:")
        print(f"   Gross P&L:      {analysis['gross_profit']:.9f} SOL")
        print(f"   Net P&L:        {analysis['net_profit']:.9f} SOL")
        print(f"   Estimated Fee:  {analysis['estimated_fee']:.9f} SOL")
        print(f"   Profitable:     {'✅ YES' if analysis['is_profitable'] else '❌ NO (fees only)'}")
        
        # USD conversion
        sol_price = 180.0
        print(f"\n💵 USD EQUIVALENT (@ ${sol_price}/SOL):")
        print(f"   Net P&L:        ${analysis['net_profit'] * sol_price:.6f}")
        print(f"   Estimated Fee:  ${analysis['estimated_fee'] * sol_price:.6f}")
        
        print("=" * 70)
    
    async def monitor_new_trades(self):
        """Monitor for new trade files and analyze them."""
        print(f"\n🔍 STARTING REAL-TIME MONITORING...")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🔄 Waiting for new trades...")
        
        while self.monitoring and self.trades_monitored < self.target_trades:
            # Check both directories for new files
            new_files = []
            
            # Check enhanced trades directory
            if self.enhanced_trades_dir.exists():
                for file in self.enhanced_trades_dir.glob("enhanced_trade_*.json"):
                    if file not in self.processed_files:
                        new_files.append(file)
            
            # Check standard trades directory
            if self.standard_trades_dir.exists():
                for file in self.standard_trades_dir.glob("trade_*.json"):
                    if file not in self.processed_files:
                        new_files.append(file)
            
            # Process new files
            for trade_file in sorted(new_files):
                self.processed_files.add(trade_file)
                analysis = self.analyze_trade_file(trade_file)
                
                if analysis:
                    self.trades_monitored += 1
                    self.print_trade_analysis(analysis, self.trades_monitored)
                    
                    # Get current balance for verification
                    current_balance = await self.get_current_balance()
                    if current_balance:
                        print(f"🔍 WALLET VERIFICATION:")
                        print(f"   Current Balance: {current_balance:.9f} SOL")
                        print(f"   Wallet Address:  {self.wallet_address}")
                    
                    if self.trades_monitored >= self.target_trades:
                        print(f"\n🎯 TARGET REACHED: Monitored {self.target_trades} trades")
                        self.monitoring = False
                        break
            
            # Wait before checking again
            await asyncio.sleep(2)
        
        print(f"\n✅ MONITORING COMPLETE")
        print(f"📊 Total trades monitored: {self.trades_monitored}")
    
    async def run(self):
        """Run the monitoring system."""
        try:
            await self.monitor_new_trades()
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring interrupted by user")
            self.monitoring = False
        except Exception as e:
            print(f"\n❌ Error in monitoring: {e}")


async def main():
    """Main function."""
    monitor = LiveTradingMonitor()
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
