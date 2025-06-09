#!/usr/bin/env python3
"""
Test Telegram Alerts

This script tests the Telegram alert system to ensure it's properly configured
and working for the 24-hour test.
"""

import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_telegram_alerts")

# Import monitoring modules
from utils.monitoring import setup_telegram_alerts, get_monitoring_service

async def test_telegram_alerts():
    """Test Telegram alerts."""
    # Load environment variables
    load_dotenv(".env.paper")

    # Get Telegram credentials
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not telegram_bot_token or telegram_bot_token == "your_telegram_bot_token_here":
        logger.error("Telegram bot token not configured or is set to default value")
        logger.info("Please set TELEGRAM_BOT_TOKEN in .env.paper")
        return False

    if not telegram_chat_id or telegram_chat_id == "your_telegram_chat_id_here":
        logger.error("Telegram chat ID not configured or is set to default value")
        logger.info("Please set TELEGRAM_CHAT_ID in .env.paper")
        return False

    logger.info(f"Using Telegram bot token: {telegram_bot_token[:5]}...{telegram_bot_token[-5:]}")
    logger.info(f"Using Telegram chat ID: {telegram_chat_id}")

    # Set up alert handler
    alert_handler = setup_telegram_alerts(telegram_bot_token, telegram_chat_id, rate_limit_seconds=10)

    # Get monitoring service
    monitoring = get_monitoring_service()

    # Register alert handlers
    monitoring.register_alert_handler("test_alert", alert_handler)

    # Send test alerts
    logger.info("Sending test alerts...")

    # Test component unhealthy alert
    monitoring._trigger_alert("test_alert", {
        "alert_type": "component_unhealthy",
        "component": "test_component",
        "timestamp": datetime.now().isoformat()
    })

    # Wait for alert to be sent
    await asyncio.sleep(2)

    # Test low balance alert
    monitoring._trigger_alert("test_alert", {
        "alert_type": "low_balance",
        "wallet": "test_wallet",
        "balance": 0.5,
        "timestamp": datetime.now().isoformat()
    })

    # Wait for alert to be sent
    await asyncio.sleep(2)

    # Test transaction error alert
    monitoring._trigger_alert("test_alert", {
        "alert_type": "transaction_error",
        "type": "swap",
        "error": "Test error message",
        "timestamp": datetime.now().isoformat()
    })

    # Wait for alert to be sent
    await asyncio.sleep(2)

    # Test circuit breaker alert
    monitoring._trigger_alert("test_alert", {
        "alert_type": "circuit_breaker_open",
        "api": "birdeye",
        "timestamp": datetime.now().isoformat()
    })

    # Wait for alert to be sent
    await asyncio.sleep(2)

    # Test system resources alert
    monitoring._trigger_alert("test_alert", {
        "alert_type": "system_resources",
        "resource": "memory",
        "usage": "90%",
        "threshold": "80%",
        "timestamp": datetime.now().isoformat()
    })

    logger.info("Test alerts sent. Please check your Telegram for messages.")
    logger.info("If you received the alerts, the Telegram alert system is working correctly.")

    return True

async def main():
    """Main function."""
    logger.info("Testing Telegram alerts...")

    success = await test_telegram_alerts()

    if success:
        logger.info("Telegram alert test completed. Please check your Telegram for messages.")
    else:
        logger.error("Telegram alert test failed. Please check the configuration.")

if __name__ == "__main__":
    asyncio.run(main())
