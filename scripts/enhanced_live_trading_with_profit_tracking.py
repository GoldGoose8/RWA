#!/usr/bin/env python3
"""
Enhanced Live Trading with Accurate Profit/Loss Tracking
========================================================

This script runs the live trading system with enhanced profit tracking that
distinguishes between actual trading profits/losses and transaction fees.
"""

import asyncio
import logging
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Setup enhanced logging for profit tracking."""
    try:
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logs_dir / 'enhanced_profit_tracking.log'),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        print(f"⚠️ Warning: Could not setup file logging: {e}")

setup_logging()
logger = logging.getLogger(__name__)


class ProfitTracker:
    """Enhanced profit tracking system for live trading."""
    
    def __init__(self, wallet_address: str, helius_api_key: str):
        self.wallet_address = wallet_address
        self.helius_api_key = helius_api_key
        
        # Session tracking
        self.session_start_time = datetime.now()
        self.session_start_balance = None
        self.session_trades = 0
        self.session_fees_paid = 0.0
        self.session_gross_pnl = 0.0
        self.session_net_pnl = 0.0
        
        # Trade tracking
        self.trade_history = []
        self.balance_history = []
        
        # Profit analysis
        self.last_balance_check = None
        self.balance_check_interval = 30  # seconds
        
        logger.info("💰 Enhanced Profit Tracker initialized")
    
    async def get_precise_balance(self) -> float:
        """Get precise wallet balance using direct RPC call."""
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
                    
                    # Record balance in history
                    self.balance_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'balance_sol': balance_sol,
                        'balance_lamports': balance_lamports
                    })
                    
                    return balance_sol
                else:
                    logger.error(f"❌ Invalid balance response: {data}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting precise balance: {e}")
            return None
    
    async def initialize_session(self):
        """Initialize trading session with starting balance."""
        logger.info("🚀 Initializing profit tracking session...")
        
        self.session_start_balance = await self.get_precise_balance()
        if self.session_start_balance is None:
            logger.error("❌ Could not get starting balance")
            return False
            
        logger.info(f"💰 Session starting balance: {self.session_start_balance:.9f} SOL")
        logger.info(f"⏰ Session start time: {self.session_start_time}")
        
        return True
    
    async def track_trade_profit(self, signal: dict, pre_balance: float, post_balance: float, 
                               transaction_result: dict, execution_time: float) -> dict:
        """Track profit/loss for a specific trade."""
        
        # Calculate balance change
        balance_change = post_balance - pre_balance
        
        # Estimate transaction fee (typical Solana fee is 0.000005 SOL)
        estimated_fee = 0.000005  # Base fee
        if transaction_result.get('execution_type') == 'jito_bundle':
            # Jito bundles have additional tip
            tip_lamports = transaction_result.get('tip_amount', 10000)
            estimated_fee += tip_lamports / 1_000_000_000
        
        # Calculate gross profit (before fees)
        gross_profit = balance_change + estimated_fee
        net_profit = balance_change
        
        # Determine if this was a profitable trade vs just fees
        is_profitable_trade = abs(gross_profit) > estimated_fee * 2
        
        trade_analysis = {
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'transaction_result': transaction_result,
            'balance_analysis': {
                'pre_balance': pre_balance,
                'post_balance': post_balance,
                'balance_change': balance_change,
                'estimated_fee': estimated_fee,
                'gross_profit': gross_profit,
                'net_profit': net_profit,
                'is_profitable_trade': is_profitable_trade
            },
            'execution_time': execution_time,
            'trade_number': self.session_trades + 1
        }
        
        # Update session totals
        self.session_trades += 1
        self.session_fees_paid += estimated_fee
        self.session_gross_pnl += gross_profit
        self.session_net_pnl += net_profit
        
        # Add to trade history
        self.trade_history.append(trade_analysis)
        
        # Log detailed analysis with enhanced precision
        logger.info("📊 ENHANCED TRADE PROFIT ANALYSIS:")
        logger.info("=" * 60)
        logger.info(f"   💰 Pre-trade balance:  {pre_balance:.9f} SOL")
        logger.info(f"   💰 Post-trade balance: {post_balance:.9f} SOL")
        logger.info(f"   📈 Balance change:     {balance_change:.9f} SOL")
        logger.info(f"   💸 Estimated fee:      {estimated_fee:.9f} SOL")
        logger.info(f"   📊 Gross profit:       {gross_profit:.9f} SOL")
        logger.info(f"   📊 Net profit:         {net_profit:.9f} SOL")
        logger.info(f"   ✅ Profitable trade:   {is_profitable_trade}")

        # Convert to USD for easier understanding
        sol_price = signal.get('price', 180.0)
        logger.info(f"   💵 Balance change USD: ${balance_change * sol_price:.6f}")
        logger.info(f"   💵 Net profit USD:     ${net_profit * sol_price:.6f}")

        # Wallet proof information
        logger.info("🔗 WALLET PROOF:")
        logger.info(f"   📍 Wallet: {signal.get('wallet_address', 'N/A')}")
        logger.info(f"   🔗 Signature: {transaction_result.get('signature', 'N/A')}")
        logger.info(f"   ⏰ Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        return trade_analysis
    
    async def get_session_summary(self) -> dict:
        """Get comprehensive session profit summary."""
        current_balance = await self.get_precise_balance()
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        
        if current_balance is None or self.session_start_balance is None:
            return None
            
        total_session_change = current_balance - self.session_start_balance
        
        summary = {
            'session_info': {
                'start_time': self.session_start_time.isoformat(),
                'duration_minutes': session_duration,
                'trades_executed': self.session_trades
            },
            'balance_info': {
                'starting_balance': self.session_start_balance,
                'current_balance': current_balance,
                'total_change': total_session_change
            },
            'profit_analysis': {
                'gross_pnl': self.session_gross_pnl,
                'net_pnl': self.session_net_pnl,
                'total_fees_paid': self.session_fees_paid,
                'average_fee_per_trade': self.session_fees_paid / max(self.session_trades, 1)
            },
            'performance_metrics': {
                'profitable_trades': len([t for t in self.trade_history if t['balance_analysis']['is_profitable_trade']]),
                'fee_only_trades': len([t for t in self.trade_history if not t['balance_analysis']['is_profitable_trade']]),
                'average_profit_per_trade': self.session_net_pnl / max(self.session_trades, 1)
            }
        }
        
        return summary


class EnhancedLiveTrader:
    """Enhanced live trader with accurate profit tracking."""
    
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        
        # Initialize profit tracker
        self.profit_tracker = ProfitTracker(self.wallet_address, self.helius_api_key)
        
        # Initialize base trader
        self.base_trader = None
        
        # Trading control
        self.is_running = False
        self.max_trades = 3  # Focus on 3 trades for proof
        self.trade_interval = 45  # seconds between trades (faster for demonstration)
        
        logger.info("🚀 Enhanced Live Trader initialized")
    
    async def initialize(self):
        """Initialize the enhanced trading system."""
        logger.info("🔧 Initializing enhanced trading system...")
        
        # Initialize profit tracking
        if not await self.profit_tracker.initialize_session():
            logger.error("❌ Failed to initialize profit tracking")
            return False
        
        # Initialize base trading system
        try:
            from scripts.unified_live_trading import UnifiedLiveTrader
            
            self.base_trader = UnifiedLiveTrader()
            if not await self.base_trader.initialize_components():
                logger.error("❌ Failed to initialize base trading components")
                return False
                
            logger.info("✅ Enhanced trading system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing trading system: {e}")
            return False

    async def execute_enhanced_trade(self, signal: dict) -> dict:
        """Execute a trade with enhanced profit tracking."""
        logger.info(f"🚀 Executing enhanced trade: {signal['action']} {signal['market']}")

        try:
            # Get precise pre-trade balance
            pre_balance = await self.profit_tracker.get_precise_balance()
            if pre_balance is None:
                logger.error("❌ Could not get pre-trade balance")
                return None

            logger.info(f"💰 Pre-trade balance: {pre_balance:.9f} SOL")

            # Execute trade using base trader
            start_time = datetime.now()
            result = await self.base_trader.execute_trade(signal)
            execution_time = (datetime.now() - start_time).total_seconds()

            if not result or not result.get('success'):
                logger.error(f"❌ Trade execution failed: {result}")
                return None

            # Wait for blockchain confirmation
            logger.info("⏳ Waiting for blockchain confirmation...")
            await asyncio.sleep(10)  # Wait longer for accurate balance

            # Get precise post-trade balance
            post_balance = await self.profit_tracker.get_precise_balance()
            if post_balance is None:
                logger.error("❌ Could not get post-trade balance")
                return None

            logger.info(f"💰 Post-trade balance: {post_balance:.9f} SOL")

            # Track profit/loss for this trade
            trade_analysis = await self.profit_tracker.track_trade_profit(
                signal, pre_balance, post_balance, result, execution_time
            )

            # Save enhanced trade record
            await self.save_enhanced_trade_record(trade_analysis)

            # Send enhanced Telegram notification
            await self.send_enhanced_notification(trade_analysis)

            return trade_analysis

        except Exception as e:
            logger.error(f"❌ Error executing enhanced trade: {e}")
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
            return None

    async def save_enhanced_trade_record(self, trade_analysis: dict):
        """Save enhanced trade record with profit analysis."""
        try:
            # Create enhanced trades directory
            trades_dir = Path('output/enhanced_live_trading/trades')
            trades_dir.mkdir(parents=True, exist_ok=True)

            # Save individual trade record
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_trade_{timestamp}.json"
            filepath = trades_dir / filename

            with open(filepath, 'w') as f:
                json.dump(trade_analysis, f, indent=2, default=str)

            logger.info(f"💾 Enhanced trade record saved: {filepath}")

            # Also save session summary
            summary = await self.profit_tracker.get_session_summary()
            if summary:
                summary_file = trades_dir / f"session_summary_{timestamp}.json"
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2, default=str)
                logger.info(f"📊 Session summary saved: {summary_file}")

        except Exception as e:
            logger.error(f"❌ Error saving enhanced trade record: {e}")

    async def send_enhanced_notification(self, trade_analysis: dict):
        """Send enhanced Telegram notification with profit details."""
        try:
            if not self.base_trader.telegram_notifier or not self.base_trader.telegram_notifier.enabled:
                return

            balance_analysis = trade_analysis['balance_analysis']
            signal = trade_analysis['signal']

            # Create enhanced message
            message = f"🚀 ENHANCED TRADE EXECUTED\n\n"
            message += f"📊 Trade #{trade_analysis['trade_number']}\n"
            message += f"🎯 Action: {signal['action']} {signal['market']}\n"
            message += f"💰 Size: {signal.get('size', 0):.6f} SOL\n\n"

            message += f"💰 BALANCE ANALYSIS:\n"
            message += f"   Pre: {balance_analysis['pre_balance']:.9f} SOL\n"
            message += f"   Post: {balance_analysis['post_balance']:.9f} SOL\n"
            message += f"   Change: {balance_analysis['balance_change']:.9f} SOL\n\n"

            message += f"📈 PROFIT ANALYSIS:\n"
            message += f"   Gross P&L: {balance_analysis['gross_profit']:.9f} SOL\n"
            message += f"   Net P&L: {balance_analysis['net_profit']:.9f} SOL\n"
            message += f"   Est. Fee: {balance_analysis['estimated_fee']:.9f} SOL\n"
            message += f"   Profitable: {'✅' if balance_analysis['is_profitable_trade'] else '❌'}\n\n"

            # Add session totals
            summary = await self.profit_tracker.get_session_summary()
            if summary:
                message += f"📊 SESSION TOTALS:\n"
                message += f"   Trades: {summary['session_info']['trades_executed']}\n"
                message += f"   Duration: {summary['session_info']['duration_minutes']:.1f}m\n"
                message += f"   Net P&L: {summary['profit_analysis']['net_pnl']:.9f} SOL\n"
                message += f"   Total Fees: {summary['profit_analysis']['total_fees_paid']:.9f} SOL\n"

            # Send notification
            await self.base_trader.telegram_notifier.send_message(message)
            logger.info("📱 Enhanced Telegram notification sent")

        except Exception as e:
            logger.error(f"❌ Error sending enhanced notification: {e}")

    async def run_enhanced_trading_session(self):
        """Run enhanced trading session with profit tracking."""
        logger.info("🚀 Starting enhanced trading session...")

        self.is_running = True
        trades_executed = 0

        try:
            while self.is_running and trades_executed < self.max_trades:
                logger.info(f"🔄 Starting trading cycle {trades_executed + 1}/{self.max_trades}")

                # Run a trading cycle
                try:
                    # Generate trading signal (simplified for testing)
                    signal = await self.generate_test_signal()

                    if signal:
                        # Execute enhanced trade
                        result = await self.execute_enhanced_trade(signal)

                        if result:
                            trades_executed += 1
                            logger.info(f"✅ Trade {trades_executed} completed successfully")
                        else:
                            logger.warning("⚠️ Trade execution failed")
                    else:
                        logger.info("📊 No trading signal generated")

                except Exception as e:
                    logger.error(f"❌ Error in trading cycle: {e}")

                # Wait before next trade
                if trades_executed < self.max_trades:
                    logger.info(f"⏳ Waiting {self.trade_interval} seconds before next trade...")
                    await asyncio.sleep(self.trade_interval)

            # Final session summary
            await self.print_final_session_summary()

        except KeyboardInterrupt:
            logger.info("🛑 Trading session interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in trading session: {e}")
        finally:
            self.is_running = False
            logger.info("🏁 Enhanced trading session completed")

    async def generate_test_signal(self) -> dict:
        """Generate a scaled-up test trading signal for visible profit demonstration."""
        try:
            # Get current wallet balance to scale trade size appropriately
            current_balance = await self.profit_tracker.get_precise_balance()
            if current_balance is None:
                logger.error("❌ Could not get current balance for signal generation")
                return None

            # Use 90% active trading allocation as configured in .env
            active_trading_pct = 0.9
            available_balance = current_balance * active_trading_pct

            # Scale up trade size to 5% of available balance for visible changes
            # This ensures we see actual profit/loss beyond transaction fees
            scaled_trade_size = available_balance * 0.05  # 5% of available balance

            # Minimum trade size for meaningful results
            min_trade_size = 0.1  # 0.1 SOL minimum
            trade_size = max(scaled_trade_size, min_trade_size)

            logger.info(f"💰 SCALED TRADING: Current balance: {current_balance:.9f} SOL")
            logger.info(f"💰 SCALED TRADING: Available for trading: {available_balance:.9f} SOL")
            logger.info(f"💰 SCALED TRADING: Trade size: {trade_size:.9f} SOL")

            signal = {
                'action': 'SELL',  # Simplified to SELL only for consistent testing
                'market': 'SOL/USDC',
                'size': trade_size,  # Scaled-up size for visible changes
                'price': 180.0,  # Approximate SOL price
                'confidence': 0.8,
                'source': 'enhanced_profit_tracker_scaled',
                'timestamp': datetime.now().isoformat(),
                'wallet_address': self.wallet_address,  # Add wallet for proof
                'scaling_info': {
                    'wallet_balance': current_balance,
                    'active_trading_pct': active_trading_pct,
                    'available_balance': available_balance,
                    'trade_size_pct': 0.05,
                    'min_trade_size': min_trade_size
                }
            }

            logger.info(f"🎯 SCALED SIGNAL: {signal['action']} {signal['size']:.6f} SOL")
            return signal

        except Exception as e:
            logger.error(f"❌ Error generating scaled test signal: {e}")
            return None

    async def print_final_session_summary(self):
        """Print comprehensive final session summary."""
        logger.info("📊 FINAL SESSION SUMMARY")
        logger.info("=" * 60)

        summary = await self.profit_tracker.get_session_summary()
        if not summary:
            logger.error("❌ Could not generate session summary")
            return

        # Session info
        session_info = summary['session_info']
        logger.info(f"⏰ Duration: {session_info['duration_minutes']:.1f} minutes")
        logger.info(f"📊 Trades executed: {session_info['trades_executed']}")

        # Balance info
        balance_info = summary['balance_info']
        logger.info(f"💰 Starting balance: {balance_info['starting_balance']:.9f} SOL")
        logger.info(f"💰 Final balance: {balance_info['current_balance']:.9f} SOL")
        logger.info(f"📈 Total change: {balance_info['total_change']:.9f} SOL")

        # Profit analysis
        profit_analysis = summary['profit_analysis']
        logger.info(f"📊 Gross P&L: {profit_analysis['gross_pnl']:.9f} SOL")
        logger.info(f"📊 Net P&L: {profit_analysis['net_pnl']:.9f} SOL")
        logger.info(f"💸 Total fees: {profit_analysis['total_fees_paid']:.9f} SOL")
        logger.info(f"💸 Avg fee/trade: {profit_analysis['average_fee_per_trade']:.9f} SOL")

        # Performance metrics
        performance = summary['performance_metrics']
        logger.info(f"✅ Profitable trades: {performance['profitable_trades']}")
        logger.info(f"💸 Fee-only trades: {performance['fee_only_trades']}")
        logger.info(f"📈 Avg profit/trade: {performance['average_profit_per_trade']:.9f} SOL")

        # Determine if session was profitable
        net_pnl = profit_analysis['net_pnl']
        if net_pnl > 0:
            logger.info(f"✅ PROFITABLE SESSION: +{net_pnl:.9f} SOL")
        elif net_pnl < 0:
            logger.info(f"❌ LOSS SESSION: {net_pnl:.9f} SOL")
        else:
            logger.info("➖ BREAK EVEN SESSION")

        logger.info("=" * 60)


async def main():
    """Main function to run enhanced live trading with profit tracking."""
    logger.info("🚀 ENHANCED LIVE TRADING WITH PROFIT TRACKING")
    logger.info("=" * 60)
    logger.info("🎯 This system tracks actual profits vs transaction fees")
    logger.info("💰 Real-time balance monitoring and analysis")
    logger.info("📊 Comprehensive profit/loss validation")
    logger.info("=" * 60)

    # Initialize enhanced trader
    trader = EnhancedLiveTrader()

    # Initialize the system
    if not await trader.initialize():
        logger.error("❌ Failed to initialize enhanced trading system")
        return 1

    # Check wallet balance
    if not await trader.base_trader.check_wallet_balance():
        logger.error("❌ Insufficient wallet balance")
        return 1

    # Run enhanced trading session
    try:
        await trader.run_enhanced_trading_session()
        logger.info("✅ Enhanced trading session completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.info("🛑 Trading session interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error in enhanced trading session: {e}")
        logger.error(f"📄 Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
