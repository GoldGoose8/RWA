#!/usr/bin/env python3
"""
Scheduled Profitability Telegram Alert
Simple script to send profitability analysis to Telegram on a schedule.
Can be run via cron or manually.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_scheduled_profitability_alert():
    """Send scheduled profitability analysis to Telegram."""
    try:
        # Import here to avoid issues
        from scripts.analyze_live_metrics_profitability import LiveMetricsProfitabilityAnalyzer
        
        print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Starting profitability analysis...")
        
        # Create analyzer
        analyzer = LiveMetricsProfitabilityAnalyzer()
        
        if not analyzer.telegram_enabled:
            print("❌ Telegram not configured - exiting")
            return False
        
        # Generate and send report
        success = await analyzer.generate_and_send_telegram_report(detailed=False)
        
        if success:
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Profitability alert sent to Telegram!")
            
            # Log summary
            if analyzer.profitability_metrics:
                metrics = analyzer.profitability_metrics
                total_improvement = sum(rec.estimated_roi_improvement for rec in analyzer.recommendations)
                
                print(f"📈 ROI: {metrics.current_roi_percent:+.3f}% | Potential: +{total_improvement:.2f}%")
                print(f"📊 Trades: {metrics.total_trades} | Duration: {metrics.session_duration_hours:.1f}h")
                
            return True
        else:
            print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Failed to send Telegram alert")
            return False
            
    except Exception as e:
        logger.error(f"Error in scheduled profitability alert: {e}")
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function for scheduled execution."""
    print("🚀 Scheduled Profitability Telegram Alert")
    print("=" * 50)
    
    # Run the async function
    success = asyncio.run(send_scheduled_profitability_alert())
    
    if success:
        print("🎉 Scheduled profitability alert completed successfully!")
        sys.exit(0)
    else:
        print("💥 Scheduled profitability alert failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
