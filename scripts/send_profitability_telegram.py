#!/usr/bin/env python3
"""
Automated Profitability Telegram Alert Script
Sends profitability analysis reports to the same Telegram chat as live trading alerts.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.analyze_live_metrics_profitability import LiveMetricsProfitabilityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def send_profitability_alert(detailed: bool = False, save_files: bool = True):
    """
    Send profitability analysis to Telegram.
    
    Args:
        detailed: Whether to send detailed report
        save_files: Whether to save report files
    """
    try:
        print("📊 Generating profitability analysis...")
        
        # Create analyzer
        analyzer = LiveMetricsProfitabilityAnalyzer()
        
        if not analyzer.telegram_enabled:
            print("❌ Telegram not configured - check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return False
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        
        # Save files if requested
        if save_files:
            timestamp = analyzer.analysis_timestamp.strftime("%Y%m%d_%H%M%S")
            report_file = f"output/profitability_telegram_report_{timestamp}.txt"
            json_file = f"output/profitability_telegram_metrics_{timestamp}.json"
            
            analyzer.save_analysis_report(report, report_file)
            analyzer.save_metrics_json(json_file)
            print(f"📄 Files saved: {report_file}, {json_file}")
        
        # Send to Telegram
        print("📱 Sending to Telegram...")
        success = await analyzer.send_telegram_profitability_alert(detailed=detailed)
        
        if success:
            print("✅ Profitability analysis sent to Telegram successfully!")
            
            # Print quick summary
            if analyzer.profitability_metrics:
                metrics = analyzer.profitability_metrics
                total_improvement = sum(rec.estimated_roi_improvement for rec in analyzer.recommendations)
                
                print("\n" + "="*50)
                print("🎯 TELEGRAM ALERT SUMMARY")
                print("="*50)
                print(f"📈 Current ROI: {metrics.current_roi_percent:+.3f}%")
                print(f"🚀 Potential Improvement: +{total_improvement:.2f}%")
                print(f"📊 Projected ROI: {metrics.current_roi_percent + total_improvement:+.2f}%")
                print(f"⭐ Top Recommendation: {analyzer.recommendations[0].recommendation if analyzer.recommendations else 'None'}")
                print(f"📱 Telegram Status: ✅ Sent to chat {analyzer.telegram_chat_id}")
                print("="*50)
            
            return True
        else:
            print("❌ Failed to send Telegram alert")
            return False
            
    except Exception as e:
        logger.error(f"Error sending profitability alert: {e}")
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Send profitability analysis to Telegram")
    parser.add_argument("--detailed", action="store_true", help="Send detailed report")
    parser.add_argument("--no-save", action="store_true", help="Don't save report files")
    parser.add_argument("--test", action="store_true", help="Test Telegram connection only")
    
    args = parser.parse_args()
    
    if args.test:
        # Test Telegram connection
        print("🧪 Testing Telegram connection...")
        analyzer = LiveMetricsProfitabilityAnalyzer()
        
        if analyzer.telegram_enabled:
            test_message = "🧪 *PROFITABILITY ANALYZER TEST*\n\nTelegram integration is working correctly!"
            success = await analyzer.send_telegram_message(test_message)
            if success:
                print("✅ Telegram test successful!")
            else:
                print("❌ Telegram test failed!")
        else:
            print("❌ Telegram not configured")
        return
    
    # Send profitability alert
    success = await send_profitability_alert(
        detailed=args.detailed,
        save_files=not args.no_save
    )
    
    if success:
        print("\n🎉 Profitability analysis delivered to Telegram!")
    else:
        print("\n💥 Failed to send profitability analysis")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
