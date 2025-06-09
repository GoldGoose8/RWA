#!/usr/bin/env python3
"""
Enhanced Live Trading with Telegram Alerts
==========================================

Example integration of Telegram alerts with the live trading system.
Shows how to add professional notifications to Williams Capital Management operations.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import existing trading components
from scripts.debug_live_trading import LiveTradingDebugger
from scripts.telegram_trading_alerts import TradingAlerts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedLiveTradingWithAlerts(LiveTradingDebugger):
    """Enhanced live trading system with Telegram alerts integration."""
    
    def __init__(self):
        super().__init__()
        self.alerts = TradingAlerts()
        self.session_start_time = datetime.now()
        self.session_trades = 0
        self.successful_trades = 0
        
        logger.info("🚀 Enhanced Live Trading with Telegram Alerts")
        logger.info("👤 Owner: Winsor Williams II")
        logger.info(f"📱 Alerts enabled: {self.alerts.enabled}")
        
    async def start_trading_session(self):
        """Start trading session with alerts."""
        logger.info("🔄 Starting enhanced trading session...")
        
        # Send system online alert
        if self.alerts.enabled:
            await self.alerts.system_online()
            
        # Send session start notification
        if self.alerts.enabled:
            await self.alerts.custom_alert(
                "TRADING SESSION STARTED",
                f"Live trading session initiated at {self.session_start_time.strftime('%H:%M:%S')}",
                "🚀"
            )
            
        return await super().start_trading_session()
        
    async def execute_debug_trade(self, signal):
        """Execute trade with enhanced alerts."""
        logger.info(f"💰 Executing trade with alerts: {signal.get('side', 'UNKNOWN')}")
        
        self.session_trades += 1
        
        try:
            # Execute the trade using parent method
            result = await super().execute_debug_trade(signal)
            
            if result:
                self.successful_trades += 1
                
                # Send trade success alert
                if self.alerts.enabled:
                    await self.alerts.trade_executed(
                        f"{signal.get('amount', 0.1)} SOL",
                        f"${signal.get('price', 152.0):.2f}",
                        "Live_Trade_" + str(self.session_trades),
                        signal.get('side', 'BUY').upper(),
                        True
                    )
                    
                # Send balance update if significant change
                if self.session_trades % 5 == 0:  # Every 5 trades
                    try:
                        balance = await self.get_current_balance()
                        if balance and self.alerts.enabled:
                            await self.alerts.balance_update(
                                f"{balance:.6f}",
                                balance * signal.get('price', 152.0),
                                None  # Could calculate change if tracking
                            )
                    except Exception as e:
                        logger.error(f"Balance update error: {e}")
                        
            else:
                # Send trade failure alert
                if self.alerts.enabled:
                    await self.alerts.risk_alert(
                        "TRADE_EXECUTION_FAILED",
                        f"Failed to execute {signal.get('side', 'UNKNOWN')} order",
                        "HIGH"
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            
            # Send error alert
            if self.alerts.enabled:
                await self.alerts.risk_alert(
                    "TRADE_EXECUTION_ERROR",
                    f"Exception during trade execution: {str(e)[:100]}",
                    "CRITICAL"
                )
                
            return None
            
    async def get_current_balance(self):
        """Get current wallet balance."""
        try:
            # Use existing balance checking logic
            from phase_4_deployment.rpc_execution.helius_client import HeliusClient
            import os
            
            client = HeliusClient(api_key=os.getenv('HELIUS_API_KEY'))
            balance_data = await client.get_balance(os.getenv('WALLET_ADDRESS'))
            
            if isinstance(balance_data, dict):
                return balance_data.get('balance_sol', 0)
            return None
            
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return None
            
    async def send_session_summary(self):
        """Send trading session summary."""
        if not self.alerts.enabled:
            return
            
        duration = datetime.now() - self.session_start_time
        duration_hours = duration.total_seconds() / 3600
        
        win_rate = (self.successful_trades / self.session_trades * 100) if self.session_trades > 0 else 0
        
        # Calculate P&L (simplified)
        pnl_estimate = f"+{self.successful_trades * 0.01:.3f} SOL"  # Rough estimate
        
        await self.alerts.session_summary(
            self.session_trades,
            round(win_rate, 1),
            pnl_estimate,
            round(duration_hours, 1)
        )
        
    async def send_performance_milestones(self):
        """Check and send performance milestone alerts."""
        if not self.alerts.enabled:
            return
            
        # Check for milestones
        if self.session_trades == 10:
            await self.alerts.performance_milestone("TRADE_COUNT", "10 trades completed")
        elif self.session_trades == 25:
            await self.alerts.performance_milestone("TRADE_COUNT", "25 trades completed")
        elif self.session_trades == 50:
            await self.alerts.performance_milestone("TRADE_COUNT", "50 trades completed")
            
        # Check win streak
        if self.successful_trades >= 10 and self.successful_trades == self.session_trades:
            await self.alerts.performance_milestone("WIN_STREAK", f"{self.successful_trades} consecutive wins")
            
    async def run_enhanced_debug_session(self, cycles=5):
        """Run enhanced debug session with comprehensive alerts."""
        logger.info("🚀 STARTING ENHANCED LIVE TRADING SESSION WITH ALERTS")
        logger.info("=" * 60)
        
        try:
            # Start session
            await self.start_trading_session()
            
            # Run trading cycles
            for cycle in range(1, cycles + 1):
                logger.info(f"🔄 Enhanced Cycle {cycle}/{cycles}")
                
                try:
                    # Generate signal
                    signal = await self.generate_debug_signal()
                    
                    # Execute trade with alerts
                    result = await self.execute_debug_trade(signal)
                    
                    if result:
                        logger.info(f"✅ Enhanced Cycle {cycle} completed successfully")
                        
                        # Check for milestones
                        await self.send_performance_milestones()
                        
                    else:
                        logger.error(f"❌ Enhanced Cycle {cycle} failed")
                        
                    # Wait between cycles
                    await asyncio.sleep(30)  # 30 seconds between trades
                    
                except Exception as e:
                    logger.error(f"❌ Enhanced Cycle {cycle} error: {e}")
                    
                    # Send error alert
                    if self.alerts.enabled:
                        await self.alerts.risk_alert(
                            "CYCLE_ERROR",
                            f"Cycle {cycle} encountered error: {str(e)[:100]}",
                            "MEDIUM"
                        )
                        
            # Send final session summary
            await self.send_session_summary()
            
            # Send system offline alert
            if self.alerts.enabled:
                await self.alerts.system_offline("Session completed")
                
            logger.info("🎉 Enhanced trading session completed!")
            
        except KeyboardInterrupt:
            logger.info("🛑 Enhanced session interrupted by user")
            
            if self.alerts.enabled:
                await self.alerts.system_offline("Manual interruption")
                await self.send_session_summary()
                
        except Exception as e:
            logger.error(f"❌ Enhanced session error: {e}")
            
            if self.alerts.enabled:
                await self.alerts.risk_alert(
                    "SESSION_ERROR",
                    f"Trading session error: {str(e)[:100]}",
                    "CRITICAL"
                )

async def main():
    """Main function to run enhanced live trading."""
    print("🏢 WILLIAMS CAPITAL MANAGEMENT")
    print("👤 Winsor Williams II")
    print("📱 Enhanced Live Trading with Telegram Alerts")
    print("=" * 60)
    
    # Initialize enhanced trading system
    enhanced_trader = EnhancedLiveTradingWithAlerts()
    
    # Check if alerts are configured
    if not enhanced_trader.alerts.enabled:
        print("⚠️ Telegram alerts not configured.")
        print("🔧 Run: python3 scripts/telegram_alerts_setup.py")
        print("📱 Continuing without alerts...")
        
    # Run enhanced trading session
    await enhanced_trader.run_enhanced_debug_session(cycles=10)

if __name__ == "__main__":
    asyncio.run(main())
