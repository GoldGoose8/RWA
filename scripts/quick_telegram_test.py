#!/usr/bin/env python3
"""Quick Telegram test for live trading"""

import asyncio
import httpx
import os

async def test_telegram():
    """Test Telegram notification"""
    
    telegram_token = "7372873616:AAGKKdOKhJJJJJJJJJJJJJJJJJJJJJJJJJJ"  # Replace with actual token
    chat_id = "5135869709"
    
    message = """🧪 LIVE TRADING TEST STARTING
⏱️ Duration: 1 minute
🎯 Testing all components
✅ Dashboard: Running on localhost:8501
📱 Telegram: Testing now
🚀 Ready for live trading!"""
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = await client.post(url, data=data)
            
            if response.status_code == 200:
                print("✅ Telegram test notification sent successfully!")
                return True
            else:
                print(f"❌ Telegram test failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Telegram test error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_telegram())
    exit(0 if success else 1)
