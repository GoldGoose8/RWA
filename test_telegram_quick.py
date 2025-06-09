#!/usr/bin/env python3
"""
Quick Telegram Test
Tests Telegram notifications for the RWA Trading System.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

async def test_telegram_alerts():
    """Test Telegram alerts functionality."""
    print("🔔 Testing RWA Trading System Telegram Alerts")
    print("="*50)
    
    try:
        from core.notifications.telegram_notifier import TelegramNotifier
        
        # Initialize Telegram notifier
        notifier = TelegramNotifier()
        
        # Test message
        test_message = """
🚀 **RWA Trading System Test Alert**

✅ **System Status**: Fully Operational
✅ **Signature Verification**: Fixed and Working
✅ **Live Trading**: Ready for Execution
✅ **Dashboard**: Active at http://localhost:8505

🎯 **Test Timestamp**: {timestamp}
📊 **System Version**: v2.0 Production Ready

This is a test message to verify Telegram alerts are working correctly.
        """.strip()
        
        # Send test message
        success = await notifier.send_message(test_message)
        
        if success:
            print("✅ Telegram alert sent successfully!")
            print("📱 Check your Telegram for the test message")
            return True
        else:
            print("❌ Failed to send Telegram alert")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram alerts: {e}")
        return False

async def main():
    """Main function."""
    success = await test_telegram_alerts()
    
    if success:
        print("\n🎉 Telegram alerts are working!")
        print("✅ Ready for live trading notifications")
    else:
        print("\n❌ Telegram alerts need attention")
        print("❌ Check your bot token and chat ID")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
