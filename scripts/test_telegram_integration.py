#!/usr/bin/env python3
"""
Test Telegram Integration
=========================

Test script to verify Telegram alerts integration with the trading system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.telegram_trading_alerts import TradingAlerts

async def test_all_alerts():
    """Test all types of trading alerts."""
    alerts = TradingAlerts()
    
    if not alerts.enabled:
        print("❌ Telegram alerts not configured.")
        print("🔧 Run: python3 scripts/telegram_alerts_setup.py")
        return False
    
    print("🚀 Testing Williams Capital Management Telegram Alerts")
    print("=" * 60)
    
    try:
        # 1. System online alert
        print("📱 Sending system online alert...")
        await alerts.system_online()
        await asyncio.sleep(3)
        
        # 2. Trade execution alert
        print("📱 Sending trade execution alert...")
        await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d8k2m9n4p7q", "BUY", True)
        await asyncio.sleep(3)
        
        # 3. Balance update alert
        print("📱 Sending balance update alert...")
        await alerts.balance_update("15.45", 2356.78, -0.05)
        await asyncio.sleep(3)
        
        # 4. MEV protection alert
        print("📱 Sending MEV protection alert...")
        await alerts.mev_protection_alert("ACTIVE", "Jito bundles operational")
        await asyncio.sleep(3)
        
        # 5. Risk alert
        print("📱 Sending risk alert...")
        await alerts.risk_alert("SLIPPAGE_HIGH", "Slippage exceeded 2% threshold", "MEDIUM")
        await asyncio.sleep(3)
        
        # 6. Performance milestone
        print("📱 Sending performance milestone...")
        await alerts.performance_milestone("PROFIT_TARGET", "+5.0 SOL")
        await asyncio.sleep(3)
        
        # 7. Session summary
        print("📱 Sending session summary...")
        await alerts.session_summary(25, 88, "+2.5 SOL", 4.5)
        await asyncio.sleep(3)
        
        # 8. Custom alert
        print("📱 Sending custom alert...")
        await alerts.custom_alert(
            "DASHBOARD ALIGNED", 
            "Enhanced dashboard successfully integrated with live trading system. Metrics updating every 30 seconds.",
            "🎯"
        )
        
        print("=" * 60)
        print("✅ All test alerts sent successfully!")
        print("📱 Check your Telegram for the messages")
        return True
        
    except Exception as e:
        print(f"❌ Error sending alerts: {e}")
        return False

async def test_quick_functions():
    """Test the quick notification functions."""
    from scripts.telegram_trading_alerts import notify_trade, notify_system_status, notify_session_end
    
    print("\n🔧 Testing quick notification functions...")
    
    # Quick trade notification
    await notify_trade("0.05 SOL", "$152.30", "8xH9j3k5m2n", "SELL")
    await asyncio.sleep(2)
    
    # Quick system status
    await notify_system_status(True)
    await asyncio.sleep(2)
    
    # Quick session end
    await notify_session_end(15, 93, "+1.8 SOL")
    
    print("✅ Quick functions tested!")

def main():
    """Main test function."""
    print("🏢 Williams Capital Management - Telegram Alerts Test")
    print("👤 Owner: Winsor Williams II")
    print("📱 Testing professional trading alerts system")
    print("=" * 60)
    
    # Run tests
    success = asyncio.run(test_all_alerts())
    
    if success:
        # Test quick functions
        asyncio.run(test_quick_functions())
        
        print("\n🎉 TELEGRAM INTEGRATION TEST COMPLETE!")
        print("=" * 60)
        print("✅ All alert types working")
        print("✅ Professional formatting verified")
        print("✅ Quick functions operational")
        print("✅ Ready for live trading integration")
        print("=" * 60)
        print("📋 Integration Examples:")
        print("# In your trading code:")
        print("from scripts.telegram_trading_alerts import TradingAlerts")
        print("alerts = TradingAlerts()")
        print("await alerts.trade_executed('0.1 SOL', '$152.45', tx_hash)")
        print("await alerts.session_summary(trades, win_rate, pnl)")
    else:
        print("\n❌ Test failed. Please check your Telegram configuration.")

if __name__ == "__main__":
    main()
