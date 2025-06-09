#!/usr/bin/env python3
"""
Enhanced Telegram Notifier for Live Trading System
Sends real-time notifications for trades, alerts, and system status.
NOW WITH DUAL CHAT SUPPORT: Trade alerts go to BOTH chats automatically!
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Enhanced Telegram notifier with dual chat support for live trading system."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram notifier."""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.primary_chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.secondary_chat_id = "-1002232263415"  # Additional chat for trade alerts

        # Backward compatibility
        self.chat_id = self.primary_chat_id

        # Check if credentials are available
        self.enabled = bool(self.bot_token and self.primary_chat_id)
        self.dual_enabled = bool(self.bot_token and self.primary_chat_id and self.secondary_chat_id)

        if not self.enabled:
            logger.warning("Telegram credentials not found - notifications disabled")
        else:
            logger.info(f"Telegram notifier initialized for chat {self.primary_chat_id}")
            if self.dual_enabled:
                logger.info(f"Dual chat support enabled: secondary chat {self.secondary_chat_id}")

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Rate limiting - optimized for production
        self.last_notification_time = {}
        self.rate_limits = {
            'trade_executed': 5,      # 5 seconds between trade notifications
            'trade_rejected': 30,     # 30 seconds between rejection notifications
            'error': 60,              # 1 minute between error notifications
            'pnl_milestone_profit': 300,  # 5 minutes between profit milestones
            'pnl_milestone_loss': 60,     # 1 minute between loss milestones
            'default': 30             # 30 seconds default
        }

        # PnL tracking
        self.session_start_balance = None
        self.last_balance = None
        self.total_fees_paid = 0.0
        self.trade_count = 0

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    def set_session_start_balance(self, balance: float):
        """Set the session start balance for PnL tracking."""
        self.session_start_balance = balance
        self.last_balance = balance
        logger.info(f"Session start balance set: {balance:.6f} SOL")

    def update_balance(self, new_balance: float):
        """Update current balance for PnL tracking."""
        self.last_balance = new_balance

    def add_trade_fee(self, fee_amount: float):
        """Add transaction fee to total fees paid."""
        self.total_fees_paid += fee_amount

    def calculate_session_pnl(self, current_balance: float, current_price: float) -> Dict[str, float]:
        """Calculate session PnL metrics with proper ROI calculation."""
        if self.session_start_balance is None:
            return {
                'pnl_sol': 0.0,
                'pnl_usd': 0.0,
                'pnl_percent': 0.0,
                'roi_percent': 0.0,
                'fees_sol': self.total_fees_paid,
                'fees_usd': self.total_fees_paid * current_price
            }

        # Calculate raw PnL
        pnl_sol = current_balance - self.session_start_balance
        pnl_usd = pnl_sol * current_price

        # Calculate percentage change (simple return)
        pnl_percent = (pnl_sol / self.session_start_balance) * 100 if self.session_start_balance > 0 else 0.0

        # Calculate proper ROI accounting for fees
        net_pnl_sol = pnl_sol - self.total_fees_paid
        net_pnl_usd = net_pnl_sol * current_price

        # ROI = (Net Profit / Initial Investment) * 100
        initial_investment_usd = self.session_start_balance * current_price
        roi_percent = (net_pnl_usd / initial_investment_usd) * 100 if initial_investment_usd > 0 else 0.0

        return {
            'pnl_sol': pnl_sol,
            'pnl_usd': pnl_usd,
            'pnl_percent': pnl_percent,
            'roi_percent': roi_percent,  # 🔧 FIXED: Proper ROI calculation
            'net_pnl_sol': net_pnl_sol,
            'net_pnl_usd': net_pnl_usd,
            'fees_sol': self.total_fees_paid,
            'fees_usd': self.total_fees_paid * current_price,
            'start_balance': self.session_start_balance,
            'current_balance': current_balance
        }

    def _should_send_notification(self, notification_type: str) -> bool:
        """Check if notification should be sent based on rate limiting."""
        if not self.enabled:
            return False

        now = datetime.now()
        last_time = self.last_notification_time.get(notification_type)

        if last_time is None:
            self.last_notification_time[notification_type] = now
            return True

        # Get rate limit for this notification type
        rate_limit = self.rate_limits.get(notification_type, self.rate_limits['default'])

        time_diff = (now - last_time).total_seconds()
        if time_diff >= rate_limit:
            self.last_notification_time[notification_type] = now
            return True

        return False

    async def send_message_to_chat(self, message: str, chat_id: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to a specific Telegram chat."""
        if not self.enabled:
            logger.debug(f"Telegram disabled, would send to {chat_id}: {message[:50]}...")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = await self.http_client.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.debug(f"Telegram message sent successfully to {chat_id}")
                return True
            else:
                logger.error(f"Telegram API error for {chat_id}: {result.get('description')}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram message to {chat_id}: {e}")
            return False

    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to primary Telegram chat (backward compatibility)."""
        return await self.send_message_to_chat(message, self.primary_chat_id, parse_mode)

    async def send_message_dual(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to both primary and secondary chats."""
        if not self.enabled:
            return False

        # Send to primary chat
        primary_success = await self.send_message_to_chat(message, self.primary_chat_id, parse_mode)

        # Send to secondary chat if enabled
        secondary_success = True
        if self.dual_enabled:
            secondary_success = await self.send_message_to_chat(message, self.secondary_chat_id, parse_mode)

        # Return True if at least one succeeded
        return primary_success or secondary_success

    async def notify_trade_executed(self, trade_data: Dict[str, Any]) -> bool:
        """Send notification for executed trade with PnL metrics."""
        if not self._should_send_notification("trade_executed"):
            return False

        try:
            signal = trade_data.get('signal', {})
            position_data = trade_data.get('position_data', {})
            tx_result = trade_data.get('transaction_result', {})

            action = signal.get('action', 'UNKNOWN')
            size_sol = position_data.get('position_size_sol', 0)
            size_usd = position_data.get('position_size_usd', 0)
            confidence = signal.get('confidence', 0)
            signature = tx_result.get('signature', 'N/A')
            execution_time = tx_result.get('execution_time', 0)
            current_price = signal.get('price', 180.0)

            # Update trade count and fees
            self.trade_count += 1
            estimated_fee = 0.000005  # ~5000 lamports
            self.add_trade_fee(estimated_fee)

            # Get current wallet balance and calculate PnL
            current_balance = position_data.get('total_wallet_sol', 0)
            if current_balance > 0:
                self.update_balance(current_balance)

            # 🔧 FIXED: Use actual SOL price from signal data
            try:
                # Use the actual price from the signal data
                if current_price <= 50.0:  # Only update if price seems invalid
                    current_price = 154.0  # Current SOL price range
            except:
                current_price = 154.0

            pnl_metrics = self.calculate_session_pnl(current_balance, current_price)

            # Format PnL display with proper ROI
            pnl_emoji = "📈" if pnl_metrics['net_pnl_usd'] >= 0 else "📉"
            pnl_sign = "+" if pnl_metrics['net_pnl_usd'] >= 0 else ""
            roi_emoji = "🚀" if pnl_metrics['roi_percent'] >= 0 else "📉"

            # Format message with enhanced metrics
            emoji = "🟢" if action == "BUY" else "🔴"
            message = f"""
{emoji} *TRADE EXECUTED* {emoji}

*Action*: {action}
*Size*: {size_sol:.4f} SOL (${size_usd:.2f})
*Price*: ${current_price:.2f}
*Confidence*: {confidence:.1%}
*Execution Time*: {execution_time:.3f}s

{pnl_emoji} *Session PnL*: {pnl_sign}{pnl_metrics['pnl_sol']:+.6f} SOL (${pnl_metrics['pnl_usd']:+.2f})
{roi_emoji} *Net ROI*: {pnl_metrics['roi_percent']:+.2f}% (after fees)
💸 *Fees Paid*: {pnl_metrics['fees_sol']:.6f} SOL (${pnl_metrics['fees_usd']:.2f})
💰 *Balance*: {current_balance:.6f} SOL
🔢 *Trade #*: {self.trade_count}

*Signature*: `{signature[:16]}...{signature[-16:] if len(signature) > 32 else signature}`

*Time*: {datetime.now().strftime('%H:%M:%S')}
"""

            # ENHANCED: Send trade alerts to BOTH chats
            return await self.send_message_dual(message)

        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
            return False

    async def notify_trade_rejected(self, signal: Dict[str, Any], reason: str) -> bool:
        """Send notification for rejected trade."""
        if not self._should_send_notification("trade_rejected"):
            return False

        try:
            action = signal.get('action', 'UNKNOWN')
            size = signal.get('size', 0)

            message = f"""
⚠️ *TRADE REJECTED* ⚠️

*Action*: {action}
*Size*: {size:.4f} SOL
*Reason*: {reason}

*Time*: {datetime.now().strftime('%H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending rejection notification: {e}")
            return False

    async def notify_session_started(self, duration_hours: Optional[float] = None, start_balance: Optional[float] = None) -> bool:
        """Send notification when trading session starts."""
        try:
            duration_text = f"for {duration_hours} hours" if duration_hours else "indefinitely"

            # Initialize PnL tracking
            if start_balance is not None:
                self.set_session_start_balance(start_balance)

            balance_text = f"\n💰 *Starting Balance*: {start_balance:.6f} SOL" if start_balance else ""

            message = f"""
🚀 *RWA LIVE TRADING SYSTEM STARTED* 🚀

*Session Duration*: {duration_text}
*Start Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Mode*: Production Trading{balance_text}
*Strategy*: opportunistic_volatility_breakout
*Wallet*: 9wPBNe...UB6tkc

Ready to execute real USDC ↔ WSOL swaps! 💰
📊 Live PnL tracking enabled
🔗 Verified on-chain transactions
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending session start notification: {e}")
            return False

    async def notify_session_ended(self, metrics: Dict[str, Any], final_balance: Optional[float] = None, avg_price: Optional[float] = None) -> bool:
        """Send notification when trading session ends with PnL summary."""
        try:
            cycles_completed = metrics.get('cycles_completed', 0)
            trades_executed = metrics.get('trades_executed', 0)
            trades_rejected = metrics.get('trades_rejected', 0)
            session_duration = metrics.get('session_duration_minutes', 0)

            success_rate = (trades_executed / (trades_executed + trades_rejected) * 100) if (trades_executed + trades_rejected) > 0 else 0

            # Calculate final PnL if balance provided
            pnl_text = ""
            if final_balance is not None and avg_price is not None:
                final_pnl = self.calculate_session_pnl(final_balance, avg_price)
                pnl_emoji = "📈" if final_pnl['net_pnl_usd'] >= 0 else "📉"
                pnl_sign = "+" if final_pnl['net_pnl_usd'] >= 0 else ""
                roi_emoji = "🚀" if final_pnl['roi_percent'] >= 0 else "📉"

                # Calculate hourly rates for both gross and net PnL
                hourly_rate_gross = final_pnl['pnl_usd'] / (session_duration / 60) if session_duration > 0 else 0
                hourly_rate_net = final_pnl['net_pnl_usd'] / (session_duration / 60) if session_duration > 0 else 0

                pnl_text = f"""
{pnl_emoji} *Final PnL*: {pnl_sign}{final_pnl['pnl_sol']:+.6f} SOL (${final_pnl['pnl_usd']:+.2f})
{roi_emoji} *Net ROI*: {final_pnl['roi_percent']:+.2f}% (after fees)
💰 *Final Balance*: {final_balance:.6f} SOL
💸 *Total Fees*: {final_pnl['fees_sol']:.6f} SOL (${final_pnl['fees_usd']:.2f})
⏱️ *Hourly Rate*: ${hourly_rate_net:+.2f}/hour (net)
📈 *Gross Hourly*: ${hourly_rate_gross:+.2f}/hour
"""

            message = f"""
🏁 *TRADING SESSION COMPLETED* 🏁

*Duration*: {session_duration:.1f} minutes
*Cycles*: {cycles_completed}
*Trades Executed*: {trades_executed}
*Trades Rejected*: {trades_rejected}
*Success Rate*: {success_rate:.1f}%{pnl_text}
*End Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending session end notification: {e}")
            return False

    async def notify_error(self, error_message: str, component: str = "System") -> bool:
        """Send notification for system errors."""
        if not self._should_send_notification("error"):
            return False

        try:
            message = f"""
🚨 *SYSTEM ERROR* 🚨

*Component*: {component}
*Error*: {error_message}

*Time*: {datetime.now().strftime('%H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False

    async def notify_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send daily trading summary."""
        try:
            total_trades = summary_data.get('total_trades', 0)
            successful_trades = summary_data.get('successful_trades', 0)
            total_volume = summary_data.get('total_volume_usd', 0)
            pnl = summary_data.get('total_pnl_usd', 0)

            success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
            pnl_emoji = "📈" if pnl >= 0 else "📉"

            message = f"""
📊 *DAILY TRADING SUMMARY* 📊

*Total Trades*: {total_trades}
*Successful*: {successful_trades} ({success_rate:.1f}%)
*Volume*: ${total_volume:.2f}
*P&L*: {pnl_emoji} ${pnl:.2f}

*Date*: {datetime.now().strftime('%Y-%m-%d')}
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.enabled:
            logger.warning("Telegram not configured")
            return False

        test_message = f"""
🧪 *TEST MESSAGE* 🧪

Synergy7 Enhanced Trading System
Connection test successful!

*Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return await self.send_message(test_message)

    async def notify_pnl_milestone(self, pnl_metrics: Dict[str, float], milestone_type: str = "profit") -> bool:
        """Send notification for PnL milestones (profit targets, loss limits, etc.)."""
        if not self._should_send_notification(f"pnl_milestone_{milestone_type}"):
            return False

        try:
            pnl_emoji = "🎉" if milestone_type == "profit" else "⚠️"
            milestone_text = "PROFIT TARGET REACHED" if milestone_type == "profit" else "LOSS LIMIT REACHED"

            roi_emoji = "🚀" if pnl_metrics.get('roi_percent', 0) >= 0 else "📉"

            message = f"""
{pnl_emoji} *{milestone_text}* {pnl_emoji}

📊 *Session PnL*: {pnl_metrics['pnl_sol']:+.6f} SOL (${pnl_metrics['pnl_usd']:+.2f})
{roi_emoji} *Net ROI*: {pnl_metrics.get('roi_percent', 0):+.2f}% (after fees)
💸 *Fees Paid*: {pnl_metrics.get('fees_sol', 0):.6f} SOL (${pnl_metrics.get('fees_usd', 0):.2f})
💰 *Current Balance*: {pnl_metrics['current_balance']:.6f} SOL
🎯 *Starting Balance*: {pnl_metrics['start_balance']:.6f} SOL

*Time*: {datetime.now().strftime('%H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            logger.error(f"Error sending PnL milestone notification: {e}")
            return False


# Global instance for easy access
_telegram_notifier = None

def get_telegram_notifier() -> TelegramNotifier:
    """Get the global Telegram notifier instance."""
    global _telegram_notifier

    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()

    return _telegram_notifier
