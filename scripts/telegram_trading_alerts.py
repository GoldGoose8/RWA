#!/usr/bin/env python3
"""
Telegram Trading Alerts Integration
===================================

Easy-to-use Telegram alerts for Williams Capital Management trading system.
Designed for integration with live trading operations.

Usage Examples:
    from scripts.telegram_trading_alerts import TradingAlerts
    
    alerts = TradingAlerts()
    await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d...")
    await alerts.system_online()
    await alerts.session_summary(25, 88, "+2.5 SOL")
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TradingAlerts:
    """Professional trading alerts for Williams Capital Management."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        load_dotenv(self.project_root / '.env')
        
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            print("⚠️ Telegram alerts not configured. Run: python3 scripts/telegram_alerts_setup.py")
    
    async def _send_message(self, message):
        """Send message to Telegram."""
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f'https://api.telegram.org/bot{self.bot_token}/sendMessage',
                    json={
                        'chat_id': self.chat_id,
                        'text': message,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': True
                    }
                )
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram alert error: {e}")
            return False
    
    def _format_header(self):
        """Format message header."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return (
            "🏢 <b>Williams Capital Management</b>\n"
            f"👤 <b>Winsor Williams II</b>\n"
            f"⏰ <code>{timestamp}</code>\n\n"
        )
    
    async def trade_executed(self, amount, price, tx_hash, trade_type="BUY", success=True):
        """Send trade execution alert."""
        icon = "✅" if success else "❌"
        status = "EXECUTED" if success else "FAILED"
        
        message = (
            f"{self._format_header()}"
            f"💰 <b>TRADE {status}</b>\n\n"
            f"{icon} <b>Type:</b> <code>{trade_type}</code>\n"
            f"💎 <b>Amount:</b> <code>{amount}</code>\n"
            f"💲 <b>Price:</b> <code>{price}</code>\n"
            f"🔗 <b>TX:</b> <code>{tx_hash[:10]}...</code>\n\n"
            "🛡️ <i>MEV-Protected Trading System</i>"
        )
        
        return await self._send_message(message)
    
    async def system_online(self):
        """Send system online alert."""
        message = (
            f"{self._format_header()}"
            "🟢 <b>SYSTEM ONLINE</b>\n\n"
            "✅ Trading engine started\n"
            "✅ MEV protection active\n"
            "✅ RPC connections established\n"
            "✅ Risk management enabled\n\n"
            "🚀 <i>Ready for live trading operations</i>"
        )
        
        return await self._send_message(message)
    
    async def system_offline(self, reason="Manual shutdown"):
        """Send system offline alert."""
        message = (
            f"{self._format_header()}"
            "🔴 <b>SYSTEM OFFLINE</b>\n\n"
            f"📝 <b>Reason:</b> <code>{reason}</code>\n\n"
            "⏸️ <i>Trading operations suspended</i>"
        )
        
        return await self._send_message(message)
    
    async def session_summary(self, total_trades, win_rate, pnl, duration_hours=None):
        """Send trading session summary."""
        message = (
            f"{self._format_header()}"
            "📊 <b>SESSION SUMMARY</b>\n\n"
            f"📈 <b>Total Trades:</b> <code>{total_trades}</code>\n"
            f"🎯 <b>Win Rate:</b> <code>{win_rate}%</code>\n"
            f"💰 <b>P&L:</b> <code>{pnl}</code>\n"
        )
        
        if duration_hours:
            message += f"⏱️ <b>Duration:</b> <code>{duration_hours}h</code>\n"
            
        message += "\n🏆 <i>Professional trading performance</i>"
        
        return await self._send_message(message)
    
    async def risk_alert(self, alert_type, message, severity="MEDIUM"):
        """Send risk management alert."""
        icons = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "🚨"}
        icon = icons.get(severity, "⚠️")
        
        alert_message = (
            f"{self._format_header()}"
            f"{icon} <b>RISK ALERT - {severity}</b>\n\n"
            f"📋 <b>Type:</b> <code>{alert_type}</code>\n"
            f"📝 <b>Details:</b> {message}\n\n"
            "🛡️ <i>Risk management system active</i>"
        )
        
        return await self._send_message(alert_message)
    
    async def balance_update(self, sol_balance, usd_value, change_sol=None):
        """Send wallet balance update."""
        message = (
            f"{self._format_header()}"
            "💼 <b>WALLET UPDATE</b>\n\n"
            f"💎 <b>SOL Balance:</b> <code>{sol_balance}</code>\n"
            f"💵 <b>USD Value:</b> <code>${usd_value:,.2f}</code>\n"
        )
        
        if change_sol:
            change_icon = "📈" if change_sol > 0 else "📉"
            message += f"{change_icon} <b>Change:</b> <code>{change_sol:+.6f} SOL</code>\n"
            
        message += "\n💰 <i>Live wallet monitoring</i>"
        
        return await self._send_message(message)
    
    async def mev_protection_alert(self, status, details=None):
        """Send MEV protection status alert."""
        icon = "🛡️" if status == "ACTIVE" else "⚠️"
        
        message = (
            f"{self._format_header()}"
            f"{icon} <b>MEV PROTECTION {status}</b>\n\n"
        )
        
        if details:
            message += f"📝 <b>Details:</b> {details}\n\n"
            
        if status == "ACTIVE":
            message += "✅ <i>Jito bundles protecting transactions</i>"
        else:
            message += "⚠️ <i>Transactions may be vulnerable to MEV</i>"
            
        return await self._send_message(message)
    
    async def performance_milestone(self, milestone_type, value):
        """Send performance milestone alert."""
        milestones = {
            "PROFIT_TARGET": "🎯 Profit target reached",
            "TRADE_COUNT": "📊 Trade milestone achieved", 
            "WIN_STREAK": "🔥 Win streak record",
            "DAILY_GOAL": "🏆 Daily goal completed"
        }
        
        title = milestones.get(milestone_type, "🎉 Milestone achieved")
        
        message = (
            f"{self._format_header()}"
            f"🎉 <b>MILESTONE ACHIEVED</b>\n\n"
            f"{title}\n"
            f"📈 <b>Value:</b> <code>{value}</code>\n\n"
            "🏆 <i>Exceptional trading performance</i>"
        )
        
        return await self._send_message(message)
    
    async def custom_alert(self, title, details, icon="🔔"):
        """Send custom alert."""
        message = (
            f"{self._format_header()}"
            f"{icon} <b>{title}</b>\n\n"
            f"{details}\n\n"
            "🏢 <i>Williams Capital Management</i>"
        )
        
        return await self._send_message(message)

# Quick functions for easy import
async def notify_trade(amount, price, tx_hash, trade_type="BUY"):
    """Quick trade notification."""
    alerts = TradingAlerts()
    return await alerts.trade_executed(amount, price, tx_hash, trade_type)

async def notify_system_status(online=True, reason=None):
    """Quick system status notification."""
    alerts = TradingAlerts()
    if online:
        return await alerts.system_online()
    else:
        return await alerts.system_offline(reason or "System shutdown")

async def notify_session_end(trades, win_rate, pnl):
    """Quick session summary notification."""
    alerts = TradingAlerts()
    return await alerts.session_summary(trades, win_rate, pnl)

# Example usage
async def demo_alerts():
    """Demonstrate alert functionality."""
    alerts = TradingAlerts()
    
    if not alerts.enabled:
        print("❌ Telegram not configured. Run setup first.")
        return
    
    print("📱 Sending demo alerts...")
    
    # System online
    await alerts.system_online()
    await asyncio.sleep(2)
    
    # Trade executed
    await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d8k2m9...")
    await asyncio.sleep(2)
    
    # Balance update
    await alerts.balance_update("15.45", 2356.78, -0.05)
    await asyncio.sleep(2)
    
    # Session summary
    await alerts.session_summary(25, 88, "+2.5 SOL", 4.5)
    
    print("✅ Demo alerts sent!")

if __name__ == "__main__":
    # Run demo if called directly
    asyncio.run(demo_alerts())
