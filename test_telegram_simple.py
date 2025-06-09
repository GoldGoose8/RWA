#!/usr/bin/env python3
"""
Simple Telegram Alert Test
Test the Telegram notification system for RWA Trading System.
"""

import os
import asyncio
import httpx
from datetime import datetime

async def test_telegram_connection():
    """Test basic Telegram connection and send test message."""
    
    # Get credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found in environment variables")
        return False
    
    print(f"✅ Bot Token: {bot_token[:10]}...{bot_token[-5:]}")
    print(f"✅ Chat ID: {chat_id}")
    
    # Test message
    test_message = f"""
🚀 *RWA TRADING SYSTEM ALERT TEST* 🚀

✅ *System Status*: OPERATIONAL
📊 *Test Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 *Wallet Balance*: 1.8375 SOL
🎯 *Phase 1-3 Status*: ALL ACTIVE

🔍 *Recent Session Results*:
- Duration: 10.4 minutes
- Cycles: 9 completed
- Opportunities: 45 scanned
- Trades: 0 (smart filtering)
- Capital Protection: 100%

🎉 *System Performance*: EXCELLENT
All Phase 1-3 optimizations working perfectly!

*RWA Trading System* - Telegram Alerts Working ✅
"""
    
    try:
        # Send test message
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": test_message,
                "parse_mode": "Markdown"
            }
            
            print("📤 Sending test message to Telegram...")
            response = await client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                print("✅ SUCCESS: Telegram message sent successfully!")
                print(f"📱 Message ID: {result.get('result', {}).get('message_id')}")
                return True
            else:
                print(f"❌ FAILED: Telegram API error: {result.get('description')}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: Failed to send Telegram message: {e}")
        return False

async def test_trading_alerts():
    """Test trading-specific alert messages."""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Telegram credentials not available")
        return False
    
    # Test different alert types
    alerts = [
        {
            "title": "🎯 TRADE OPPORTUNITY DETECTED",
            "message": """
*Token*: SOL/USDC
*Strategy*: Momentum
*Confidence*: 72%
*Position Size*: 0.1111 SOL ($20.00)
*Action*: FILTERED (Ranging market)
*Reason*: Market regime unfavorable
"""
        },
        {
            "title": "🛡️ CAPITAL PROTECTION ACTIVE",
            "message": """
*Protection Type*: Signal Filtering
*Signals Filtered*: 45 opportunities
*Confidence Threshold*: 65%
*Capital Protected*: 1.8375 SOL
*Status*: System working perfectly
"""
        },
        {
            "title": "📊 SYSTEM PERFORMANCE UPDATE",
            "message": """
*Session Duration*: 10.4 minutes
*Cycles Completed*: 9/9
*System Uptime*: 100%
*Market Regime*: RANGING (100% confidence)
*Position Sizing*: 11.1x improvement ready
*Multi-Strategy*: 3 strategies balanced
"""
        }
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, alert in enumerate(alerts, 1):
                full_message = f"""
{alert['title']}

{alert['message']}

*Time*: {datetime.now().strftime('%H:%M:%S')}
*RWA Trading System* - Alert #{i}
"""
                
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": full_message,
                    "parse_mode": "Markdown"
                }
                
                print(f"📤 Sending alert #{i}: {alert['title']}")
                response = await client.post(url, json=data)
                response.raise_for_status()
                
                result = response.json()
                if result.get("ok"):
                    print(f"✅ Alert #{i} sent successfully")
                else:
                    print(f"❌ Alert #{i} failed: {result.get('description')}")
                
                # Wait between messages
                await asyncio.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to send trading alerts: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 TESTING RWA TRADING SYSTEM TELEGRAM ALERTS")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n📡 Test 1: Basic Telegram Connection")
    basic_success = await test_telegram_connection()
    
    if not basic_success:
        print("❌ Basic connection failed. Stopping tests.")
        return
    
    # Wait between tests
    await asyncio.sleep(3)
    
    # Test 2: Trading alerts
    print("\n🎯 Test 2: Trading Alert Messages")
    alerts_success = await test_trading_alerts()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY:")
    print(f"✅ Basic Connection: {'PASSED' if basic_success else 'FAILED'}")
    print(f"✅ Trading Alerts: {'PASSED' if alerts_success else 'FAILED'}")
    
    if basic_success and alerts_success:
        print("\n🎉 ALL TESTS PASSED! Telegram alerts are working correctly.")
        print("📱 Check your Telegram for the test messages.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    asyncio.run(main())
