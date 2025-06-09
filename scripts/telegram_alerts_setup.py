#!/usr/bin/env python3
"""
Telegram Alerts Setup Script
============================

Professional Telegram alerts system for Williams Capital Management trading operations.
Designed for Winsor Williams II hedge fund operations.

Features:
- Interactive setup of bot token and chat ID
- Automatic .env file configuration
- Test message functionality
- Trading alerts integration
- Professional message formatting
"""

import os
import sys
import asyncio
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, set_key
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TelegramAlertsSetup:
    """Professional Telegram alerts setup and management."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        load_dotenv(self.env_file)

        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        print("🚀 WILLIAMS CAPITAL MANAGEMENT - TELEGRAM ALERTS SETUP")
        print("👤 Owner: Winsor Williams II")
        print("📱 Professional Trading Alerts System")
        print("=" * 60)

    def validate_bot_token(self, token):
        """Validate Telegram bot token format."""
        # Telegram bot token format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
        pattern = r'^\d{8,10}:[A-Za-z0-9_-]{35}$'
        return bool(re.match(pattern, token))

    def validate_chat_id(self, chat_id):
        """Validate Telegram chat ID format."""
        # Chat ID can be positive/negative integer or @username
        if chat_id.startswith('@'):
            return len(chat_id) > 1
        try:
            int(chat_id)
            return True
        except ValueError:
            return False

    async def test_bot_connection(self, token):
        """Test bot token by calling getMe API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f'https://api.telegram.org/bot{token}/getMe')

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        print(f"✅ Bot connected: @{bot_info.get('username', 'Unknown')}")
                        print(f"📝 Bot name: {bot_info.get('first_name', 'Unknown')}")
                        return True
                    else:
                        print(f"❌ Bot API error: {data.get('description', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ HTTP error: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    async def test_send_message(self, token, chat_id):
        """Test sending a message to verify chat ID."""
        try:
            test_message = (
                "🎉 <b>Williams Capital Management</b>\n"
                "📱 <b>Telegram Alerts System</b>\n\n"
                "✅ <b>Setup Complete!</b>\n"
                f"👤 Owner: <b>Winsor Williams II</b>\n"
                f"⏰ Time: <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n"
                "🔔 You will now receive professional trading alerts for:\n"
                "• Trade executions\n"
                "• System status updates\n"
                "• Performance summaries\n"
                "• Risk management alerts\n\n"
                "🛡️ <i>MEV-Protected Trading System Active</i>"
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f'https://api.telegram.org/bot{token}/sendMessage',
                    json={
                        'chat_id': chat_id,
                        'text': test_message,
                        'parse_mode': 'HTML'
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        print("✅ Test message sent successfully!")
                        return True
                    else:
                        print(f"❌ Message send error: {data.get('description', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ HTTP error: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Send message error: {e}")
            return False

    def update_env_file(self, bot_token, chat_id):
        """Update .env file with Telegram credentials."""
        try:
            # Ensure .env file exists
            if not self.env_file.exists():
                self.env_file.touch()

            # Set the values
            set_key(str(self.env_file), 'TELEGRAM_BOT_TOKEN', bot_token)
            set_key(str(self.env_file), 'TELEGRAM_CHAT_ID', chat_id)

            print(f"✅ Updated .env file: {self.env_file}")
            return True

        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
            return False

    def get_bot_setup_instructions(self):
        """Display instructions for creating a Telegram bot."""
        print("\n📋 HOW TO CREATE A TELEGRAM BOT:")
        print("=" * 60)
        print("1. Open Telegram and search for @BotFather")
        print("2. Start a chat with BotFather")
        print("3. Send /newbot command")
        print("4. Choose a name for your bot (e.g., 'Williams Capital Alerts')")
        print("5. Choose a username ending in 'bot' (e.g., 'williams_capital_bot')")
        print("6. Copy the bot token (format: 123456789:ABCdefGHI...)")
        print("7. Send /start to your new bot")
        print("8. Get your chat ID by messaging @userinfobot")
        print("=" * 60)

    def get_chat_id_instructions(self):
        """Display instructions for getting chat ID."""
        print("\n📋 HOW TO GET YOUR CHAT ID:")
        print("=" * 60)
        print("Option 1 - Personal Chat:")
        print("1. Message @userinfobot in Telegram")
        print("2. Copy your user ID (positive number)")
        print("")
        print("Option 2 - Group Chat:")
        print("1. Add your bot to the group")
        print("2. Send a message in the group")
        print("3. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates")
        print("4. Look for 'chat':{'id': NEGATIVE_NUMBER}")
        print("=" * 60)

    async def interactive_setup(self):
        """Interactive setup process."""
        print("\n🔧 INTERACTIVE TELEGRAM SETUP")
        print("=" * 60)

        # Check if already configured
        if self.bot_token and self.chat_id:
            print(f"📱 Current bot token: {self.bot_token[:10]}...")
            print(f"💬 Current chat ID: {self.chat_id}")

            reconfigure = input("\n🔄 Reconfigure Telegram settings? (y/N): ").lower().strip()
            if reconfigure != 'y':
                print("✅ Using existing configuration")
                return await self.test_existing_config()

        # Show setup instructions
        show_instructions = input("\n📋 Show bot creation instructions? (Y/n): ").lower().strip()
        if show_instructions != 'n':
            self.get_bot_setup_instructions()
            self.get_chat_id_instructions()

        # Get bot token
        while True:
            print("\n🤖 BOT TOKEN SETUP")
            bot_token = input("Enter your Telegram bot token: ").strip()

            if not bot_token:
                print("❌ Bot token cannot be empty")
                continue

            if not self.validate_bot_token(bot_token):
                print("❌ Invalid bot token format")
                print("Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
                continue

            print("🔍 Testing bot connection...")
            if await self.test_bot_connection(bot_token):
                break
            else:
                retry = input("❌ Bot test failed. Try again? (Y/n): ").lower().strip()
                if retry == 'n':
                    return False

        # Get chat ID
        while True:
            print("\n💬 CHAT ID SETUP")
            chat_id = input("Enter your Telegram chat ID: ").strip()

            if not chat_id:
                print("❌ Chat ID cannot be empty")
                continue

            if not self.validate_chat_id(chat_id):
                print("❌ Invalid chat ID format")
                print("Expected: positive/negative number or @username")
                continue

            print("📤 Testing message send...")
            if await self.test_send_message(bot_token, chat_id):
                break
            else:
                retry = input("❌ Message test failed. Try again? (Y/n): ").lower().strip()
                if retry == 'n':
                    return False

        # Save to .env file
        print("\n💾 SAVING CONFIGURATION")
        if self.update_env_file(bot_token, chat_id):
            print("✅ Telegram alerts setup complete!")
            return True
        else:
            print("❌ Failed to save configuration")
            return False

    async def test_existing_config(self):
        """Test existing Telegram configuration."""
        if not self.bot_token or not self.chat_id:
            print("❌ Missing Telegram configuration")
            return False

        print("🔍 Testing existing configuration...")

        # Test bot connection
        if not await self.test_bot_connection(self.bot_token):
            return False

        # Test message sending
        if not await self.test_send_message(self.bot_token, self.chat_id):
            return False

        print("✅ Existing configuration working!")
        return True

    async def send_trading_alert(self, alert_type, message, data=None):
        """Send a professional trading alert."""
        if not self.bot_token or not self.chat_id:
            print("❌ Telegram not configured. Run setup first.")
            return False

        # Format message based on alert type
        formatted_message = self.format_trading_message(alert_type, message, data)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f'https://api.telegram.org/bot{self.bot_token}/sendMessage',
                    json={
                        'chat_id': self.chat_id,
                        'text': formatted_message,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': True
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        print(f"✅ Alert sent: {alert_type}")
                        return True
                    else:
                        print(f"❌ Alert failed: {data.get('description', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ HTTP error: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Send alert error: {e}")
            return False

    def format_trading_message(self, alert_type, message, data=None):
        """Format professional trading messages."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Header
        header = (
            "🏢 <b>Williams Capital Management</b>\n"
            f"👤 <b>Winsor Williams II</b>\n"
            f"⏰ <code>{timestamp}</code>\n"
        )

        # Alert type specific formatting
        if alert_type == "TRADE_EXECUTED":
            icon = "💰"
            title = "TRADE EXECUTED"
        elif alert_type == "SYSTEM_STATUS":
            icon = "🔧"
            title = "SYSTEM STATUS"
        elif alert_type == "PERFORMANCE_UPDATE":
            icon = "📊"
            title = "PERFORMANCE UPDATE"
        elif alert_type == "RISK_ALERT":
            icon = "⚠️"
            title = "RISK ALERT"
        elif alert_type == "SESSION_SUMMARY":
            icon = "📈"
            title = "SESSION SUMMARY"
        else:
            icon = "🔔"
            title = "TRADING ALERT"

        # Build message
        formatted_message = f"{header}\n{icon} <b>{title}</b>\n\n{message}"

        # Add data if provided
        if data:
            formatted_message += "\n\n📋 <b>Details:</b>\n"
            for key, value in data.items():
                formatted_message += f"• <b>{key}:</b> <code>{value}</code>\n"

        # Footer
        formatted_message += "\n🛡️ <i>MEV-Protected Trading System</i>"

        return formatted_message

    def show_usage_examples(self):
        """Show usage examples for the alerts system."""
        print("\n📚 USAGE EXAMPLES")
        print("=" * 60)
        print("# Send a trade execution alert")
        print("await alerts.send_trading_alert(")
        print("    'TRADE_EXECUTED',")
        print("    'Successfully executed SOL/USDC swap',")
        print("    {")
        print("        'Amount': '0.1 SOL',")
        print("        'Price': '$152.45',")
        print("        'Transaction': '5xG7d...'")
        print("    }")
        print(")")
        print("")
        print("# Send a system status alert")
        print("await alerts.send_trading_alert(")
        print("    'SYSTEM_STATUS',")
        print("    'Trading system online and operational'")
        print(")")
        print("")
        print("# Send a performance update")
        print("await alerts.send_trading_alert(")
        print("    'PERFORMANCE_UPDATE',")
        print("    'Daily P&L summary',")
        print("    {")
        print("        'Total Trades': '25',")
        print("        'Win Rate': '88%',")
        print("        'P&L': '+2.5 SOL'")
        print("    }")
        print(")")
        print("=" * 60)

    async def run_setup(self):
        """Main setup process."""
        try:
            success = await self.interactive_setup()

            if success:
                print("\n🎉 SETUP COMPLETE!")
                print("=" * 60)
                print("✅ Telegram bot configured")
                print("✅ Chat ID verified")
                print("✅ Test message sent")
                print("✅ Configuration saved to .env")
                print("=" * 60)

                show_examples = input("\n📚 Show usage examples? (Y/n): ").lower().strip()
                if show_examples != 'n':
                    self.show_usage_examples()

                return True
            else:
                print("\n❌ Setup failed!")
                return False

        except KeyboardInterrupt:
            print("\n\n🛑 Setup cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Setup error: {e}")
            return False

# Standalone alert functions for easy import
async def send_trade_alert(amount, price, transaction_hash, trade_type="BUY"):
    """Quick function to send trade execution alert."""
    alerts = TelegramAlertsSetup()
    await alerts.send_trading_alert(
        'TRADE_EXECUTED',
        f'{trade_type} order executed successfully',
        {
            'Amount': amount,
            'Price': price,
            'Transaction': transaction_hash[:10] + '...',
            'Type': trade_type
        }
    )

async def send_system_alert(status, message):
    """Quick function to send system status alert."""
    alerts = TelegramAlertsSetup()
    await alerts.send_trading_alert('SYSTEM_STATUS', f'{status}: {message}')

async def send_performance_alert(trades, win_rate, pnl):
    """Quick function to send performance update."""
    alerts = TelegramAlertsSetup()
    await alerts.send_trading_alert(
        'PERFORMANCE_UPDATE',
        'Trading session performance update',
        {
            'Total Trades': str(trades),
            'Win Rate': f'{win_rate}%',
            'P&L': pnl
        }
    )

def main():
    """Main function for command line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Telegram Alerts Setup for Williams Capital Management")
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    parser.add_argument('--test', action='store_true', help='Test existing configuration')
    parser.add_argument('--examples', action='store_true', help='Show usage examples')

    args = parser.parse_args()

    alerts = TelegramAlertsSetup()

    if args.setup:
        asyncio.run(alerts.run_setup())
    elif args.test:
        asyncio.run(alerts.test_existing_config())
    elif args.examples:
        alerts.show_usage_examples()
    else:
        # Default: run setup
        asyncio.run(alerts.run_setup())

if __name__ == "__main__":
    main()