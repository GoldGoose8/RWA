#!/usr/bin/env python3
"""
Test wallet balance functionality.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add current directory to path
sys.path.append('.')

# Load environment variables
load_dotenv()

async def test_wallet_balance():
    """Test wallet balance retrieval."""
    print("🔍 Testing Wallet Balance Functionality")
    print("=" * 50)
    
    wallet_address = os.getenv('WALLET_ADDRESS')
    helius_api_key = os.getenv('HELIUS_API_KEY')
    
    print(f"Wallet Address: {wallet_address}")
    print(f"Helius API Key: {'***' + helius_api_key[-4:] if helius_api_key else 'Not set'}")
    
    if not wallet_address:
        print("❌ WALLET_ADDRESS not set in .env")
        return False
    
    if not helius_api_key:
        print("❌ HELIUS_API_KEY not set in .env")
        return False
    
    try:
        # Test Helius client
        from phase_4_deployment.rpc_execution.helius_client import HeliusClient
        
        client = HeliusClient(api_key=helius_api_key)
        print("✅ Helius client created")
        
        # Get wallet balance
        print("📊 Getting wallet balance...")
        balance_data = await client.get_balance(wallet_address)
        
        if balance_data:
            print(f"✅ Balance retrieved: {balance_data}")
            if isinstance(balance_data, dict) and 'balance_sol' in balance_data:
                balance_sol = balance_data['balance_sol']
                print(f"💰 Wallet Balance: {balance_sol:.6f} SOL")
                
                # Save balance to file
                import json
                balance_file = 'output/wallet/current_balance.json'
                os.makedirs(os.path.dirname(balance_file), exist_ok=True)
                
                with open(balance_file, 'w') as f:
                    json.dump({
                        'wallet_address': wallet_address,
                        'balance_sol': balance_sol,
                        'timestamp': balance_data.get('timestamp'),
                        'last_updated': balance_data.get('last_updated')
                    }, f, indent=2)
                
                print(f"💾 Balance saved to {balance_file}")
                return True
            else:
                print(f"⚠️ Unexpected balance format: {balance_data}")
                return False
        else:
            print("❌ Failed to retrieve balance")
            return False
            
    except Exception as e:
        print(f"❌ Error testing wallet balance: {e}")
        return False

async def test_telegram_notifications():
    """Test Telegram notifications."""
    print("\n🔍 Testing Telegram Notifications")
    print("=" * 50)
    
    try:
        from core.notifications.telegram_notifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        
        if notifier.enabled:
            print("✅ Telegram notifier enabled")
            
            # Test simple message
            test_message = "🧪 Test message from Synergy7 Trading System"
            success = await notifier.send_message(test_message)
            
            if success:
                print("✅ Test message sent successfully")
                return True
            else:
                print("❌ Failed to send test message")
                return False
        else:
            print("⚠️ Telegram notifier disabled (credentials not found)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Telegram: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 SYNERGY7 SYSTEM COMPONENT TESTING")
    print("=" * 60)
    
    # Test wallet balance
    balance_success = await test_wallet_balance()
    
    # Test Telegram notifications
    telegram_success = await test_telegram_notifications()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"   Wallet Balance: {'✅ PASS' if balance_success else '❌ FAIL'}")
    print(f"   Telegram Notifications: {'✅ PASS' if telegram_success else '❌ FAIL'}")
    
    if balance_success and telegram_success:
        print("\n🎉 All core components working! System ready for trading.")
        return True
    else:
        print("\n⚠️ Some components need attention before live trading.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
