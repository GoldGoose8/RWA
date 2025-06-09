#!/usr/bin/env python3
"""
Report PnL Script

This script triggers the PnL reporter to calculate and send PnL metrics via Telegram.
It can be run without stopping the running system.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("report_pnl")

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import PnL reporter
from utils.pnl_reporter import PnLReporter

async def main():
    """Main function."""
    logger.info("Starting PnL report...")

    # Get Telegram credentials (hardcoded for testing)
    # Note: In production, these should be loaded from environment variables
    telegram_bot_token = "8081711336:AAHkahgcFf3Fy5V9Bdy8dB5AyE4o-8BsyrQ"
    telegram_chat_id = "5135869709"

    # Create PnL reporter
    reporter = PnLReporter(telegram_bot_token, telegram_chat_id)

    # Report PnL
    success = await reporter.report_pnl()

    # Close HTTP client
    await reporter.close()

    if success:
        logger.info("PnL report sent successfully")
    else:
        logger.error("Failed to send PnL report")

if __name__ == "__main__":
    asyncio.run(main())
