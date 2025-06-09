#!/usr/bin/env python3
"""
Enhanced Live Metrics Analyzer - Profitability Focus
Analyzes current live trading metrics and provides specific recommendations for ROI improvement.
Estimates % increase in ROI with given recommendations and focuses entirely on profitability.
"""

import os
import json
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path
import argparse
import asyncio
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProfitabilityMetrics:
    """Container for profitability analysis"""
    current_roi_percent: float
    session_duration_hours: float
    total_trades: int
    avg_trade_size_sol: float
    avg_trade_size_usd: float
    total_fees_sol: float
    total_fees_usd: float
    fee_percentage_of_volume: float
    break_even_threshold: float
    profit_per_trade_needed: float
    current_balance_sol: float
    session_start_balance_sol: float
    balance_change_sol: float
    trades_per_hour: float
    fee_drag_per_hour: float

@dataclass
class RecommendationImpact:
    """Container for recommendation impact analysis"""
    recommendation: str
    description: str
    estimated_roi_improvement: float
    implementation_difficulty: str
    time_to_implement: str
    risk_level: str
    expected_monthly_roi: float
    confidence_level: float

class LiveMetricsProfitabilityAnalyzer:
    """Enhanced analyzer focused on live trading profitability and ROI improvement"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.live_production_dir = self.output_dir / "live_production"
        self.trades_dir = self.live_production_dir / "trades"
        self.opportunities_dir = self.live_production_dir / "opportunistic_trades"

        # Current session data
        self.session_start_balance = 3.100263  # SOL - from our session start
        self.current_balance = 3.096893  # SOL - from real_balance.json
        self.sol_price = 180.0  # USD per SOL

        # Telegram configuration
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)

        # Analysis results
        self.profitability_metrics: Optional[ProfitabilityMetrics] = None
        self.recommendations: List[RecommendationImpact] = []
        self.analysis_timestamp = datetime.now()

        if self.telegram_enabled:
            logger.info(f"✅ Telegram notifications enabled for chat {self.telegram_chat_id}")
        else:
            logger.warning("⚠️ Telegram notifications disabled - missing credentials")

    def load_current_balance(self) -> float:
        """Load current wallet balance from real_balance.json"""
        try:
            balance_file = Path("phase_4_deployment/output/real_balance.json")
            if balance_file.exists():
                with open(balance_file, 'r') as f:
                    balance_data = json.load(f)
                return balance_data.get('sol_balance', self.current_balance)
        except Exception as e:
            logger.warning(f"Could not load current balance: {e}")
        return self.current_balance

    def load_live_trades(self) -> List[Dict[str, Any]]:
        """Load all live trading data"""
        trades = []

        if not self.trades_dir.exists():
            logger.warning(f"Trades directory not found: {self.trades_dir}")
            return trades

        trade_files = sorted(glob.glob(str(self.trades_dir / "trade_*.json")))

        for trade_file in trade_files:
            try:
                with open(trade_file, 'r') as f:
                    trade_data = json.load(f)
                    trades.append(trade_data)
            except Exception as e:
                logger.warning(f"Failed to load trade file {trade_file}: {e}")

        logger.info(f"Loaded {len(trades)} live trades")
        return trades

    def load_opportunities(self) -> List[Dict[str, Any]]:
        """Load opportunistic trading opportunities"""
        opportunities = []

        if not self.opportunities_dir.exists():
            logger.warning(f"Opportunities directory not found: {self.opportunities_dir}")
            return opportunities

        opp_files = sorted(glob.glob(str(self.opportunities_dir / "opportunity_*.json")))

        for opp_file in opp_files:
            try:
                with open(opp_file, 'r') as f:
                    opp_data = json.load(f)
                    opportunities.append(opp_data)
            except Exception as e:
                logger.warning(f"Failed to load opportunity file {opp_file}: {e}")

        logger.info(f"Loaded {len(opportunities)} opportunities")
        return opportunities

    def calculate_profitability_metrics(self, trades: List[Dict[str, Any]]) -> ProfitabilityMetrics:
        """Calculate comprehensive profitability metrics"""

        # Update current balance
        current_balance = self.load_current_balance()
        balance_change = current_balance - self.session_start_balance
        current_roi = (balance_change / self.session_start_balance) * 100 if self.session_start_balance > 0 else 0

        # Calculate session duration
        if trades:
            first_trade_time = datetime.fromisoformat(trades[0]['timestamp'].replace('Z', '+00:00'))
            last_trade_time = datetime.fromisoformat(trades[-1]['timestamp'].replace('Z', '+00:00'))
            session_duration = (last_trade_time - first_trade_time).total_seconds() / 3600  # hours
        else:
            session_duration = 0

        # Trade analysis
        total_trades = len(trades)
        trade_sizes_sol = []
        total_fees_sol = 0

        for trade in trades:
            signal = trade.get('signal', {})
            size_sol = signal.get('size', 0)
            trade_sizes_sol.append(size_sol)

            # Estimate fees (approximately 0.000005 SOL per trade)
            estimated_fee = 0.000005
            total_fees_sol += estimated_fee

        avg_trade_size_sol = np.mean(trade_sizes_sol) if trade_sizes_sol else 0
        avg_trade_size_usd = avg_trade_size_sol * self.sol_price
        total_fees_usd = total_fees_sol * self.sol_price

        # Calculate volume and fee percentage
        total_volume_sol = sum(trade_sizes_sol)
        fee_percentage = (total_fees_sol / total_volume_sol * 100) if total_volume_sol > 0 else 0

        # Break-even analysis
        break_even_threshold = total_fees_sol / total_trades if total_trades > 0 else 0
        profit_per_trade_needed = break_even_threshold * 1.1  # 10% above break-even

        # Rate calculations
        trades_per_hour = total_trades / session_duration if session_duration > 0 else 0
        fee_drag_per_hour = total_fees_usd / session_duration if session_duration > 0 else 0

        return ProfitabilityMetrics(
            current_roi_percent=current_roi,
            session_duration_hours=session_duration,
            total_trades=total_trades,
            avg_trade_size_sol=avg_trade_size_sol,
            avg_trade_size_usd=avg_trade_size_usd,
            total_fees_sol=total_fees_sol,
            total_fees_usd=total_fees_usd,
            fee_percentage_of_volume=fee_percentage,
            break_even_threshold=break_even_threshold,
            profit_per_trade_needed=profit_per_trade_needed,
            current_balance_sol=current_balance,
            session_start_balance_sol=self.session_start_balance,
            balance_change_sol=balance_change,
            trades_per_hour=trades_per_hour,
            fee_drag_per_hour=fee_drag_per_hour
        )

    def generate_profitability_recommendations(self, metrics: ProfitabilityMetrics,
                                             opportunities: List[Dict[str, Any]]) -> List[RecommendationImpact]:
        """Generate specific recommendations for improving profitability"""
        recommendations = []

        # Recommendation 1: Reduce Trading Frequency
        if metrics.trades_per_hour > 5:  # High frequency trading
            freq_reduction_roi = (metrics.fee_drag_per_hour * 0.5) / (metrics.current_balance_sol * self.sol_price) * 100
            recommendations.append(RecommendationImpact(
                recommendation="Reduce Trading Frequency",
                description=f"Current: {metrics.trades_per_hour:.1f} trades/hour. Reduce to 2-3 trades/hour by increasing confidence threshold from current level to 0.8+",
                estimated_roi_improvement=freq_reduction_roi,
                implementation_difficulty="Easy",
                time_to_implement="5 minutes",
                risk_level="Low",
                expected_monthly_roi=freq_reduction_roi * 24 * 30,
                confidence_level=0.9
            ))

        # Recommendation 2: Increase Position Size (if profitable)
        if metrics.current_roi_percent > -0.05:  # Close to break-even
            position_increase_roi = 0.15  # Conservative estimate
            recommendations.append(RecommendationImpact(
                recommendation="Gradual Position Size Increase",
                description=f"Current avg: {metrics.avg_trade_size_usd:.2f} USD. Increase to 1% of wallet ({metrics.current_balance_sol * self.sol_price * 0.01:.2f} USD) per trade",
                estimated_roi_improvement=position_increase_roi,
                implementation_difficulty="Medium",
                time_to_implement="10 minutes",
                risk_level="Medium",
                expected_monthly_roi=position_increase_roi * 30,
                confidence_level=0.7
            ))

        # Recommendation 3: Optimize Signal Quality
        signal_quality_roi = 0.25
        recommendations.append(RecommendationImpact(
            recommendation="Improve Signal Quality",
            description="Add momentum confirmation and volume filters. Require 2+ indicators to align before trading",
            estimated_roi_improvement=signal_quality_roi,
            implementation_difficulty="Medium",
            time_to_implement="30 minutes",
            risk_level="Low",
            expected_monthly_roi=signal_quality_roi * 20,
            confidence_level=0.8
        ))

        # Recommendation 4: Market Timing Optimization
        timing_roi = 0.18
        recommendations.append(RecommendationImpact(
            recommendation="Market Timing Optimization",
            description="Focus trading during high volatility periods (US market hours 9:30-16:00 EST). Avoid low-volume periods",
            estimated_roi_improvement=timing_roi,
            implementation_difficulty="Easy",
            time_to_implement="15 minutes",
            risk_level="Low",
            expected_monthly_roi=timing_roi * 25,
            confidence_level=0.75
        ))

        # Recommendation 5: Fee Optimization
        if metrics.fee_percentage_of_volume > 0.1:
            fee_opt_roi = metrics.fee_percentage_of_volume * 0.3  # 30% fee reduction
            recommendations.append(RecommendationImpact(
                recommendation="Fee Optimization",
                description="Batch smaller trades, use limit orders when possible, optimize transaction timing",
                estimated_roi_improvement=fee_opt_roi,
                implementation_difficulty="Hard",
                time_to_implement="2 hours",
                risk_level="Low",
                expected_monthly_roi=fee_opt_roi * 30,
                confidence_level=0.6
            ))

        return sorted(recommendations, key=lambda x: x.estimated_roi_improvement, reverse=True)

    async def send_telegram_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram."""
        if not self.telegram_enabled:
            logger.debug(f"Telegram disabled, would send: {message[:100]}...")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()

                result = response.json()
                if result.get("ok"):
                    logger.info("✅ Telegram profitability report sent successfully")
                    return True
                else:
                    logger.error(f"❌ Telegram API error: {result.get('description')}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {e}")
            return False

    def format_telegram_summary(self) -> str:
        """Format a concise summary for Telegram."""
        if not self.profitability_metrics:
            return "❌ No profitability metrics available"

        metrics = self.profitability_metrics
        total_improvement = sum(rec.estimated_roi_improvement for rec in self.recommendations)

        # Performance status
        if metrics.current_roi_percent > 0:
            status_emoji = "✅"
            status = "PROFITABLE"
        elif metrics.current_roi_percent > -0.05:
            status_emoji = "⚠️"
            status = "NEAR BREAK-EVEN"
        else:
            status_emoji = "❌"
            status = "UNPROFITABLE"

        message = f"""
📊 *PROFITABILITY ANALYSIS REPORT*

{status_emoji} *Status*: {status}
📈 *Current ROI*: {metrics.current_roi_percent:+.3f}%
💰 *Balance Change*: {metrics.balance_change_sol:+.6f} SOL (${metrics.balance_change_sol * self.sol_price:+.2f})
⏱️ *Session*: {metrics.session_duration_hours:.1f}h | {metrics.total_trades} trades

🎯 *IMPROVEMENT POTENTIAL*: +{total_improvement:.2f}% ROI

🚀 *TOP RECOMMENDATIONS*:
"""

        # Add top 3 recommendations
        for i, rec in enumerate(self.recommendations[:3], 1):
            difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(rec.implementation_difficulty, "⚪")
            message += f"{i}. {difficulty_emoji} {rec.recommendation} (+{rec.estimated_roi_improvement:.2f}%)\n"

        message += f"""
⚡ *QUICK WINS*:
"""
        # Add easy implementations
        easy_recs = [r for r in self.recommendations if r.implementation_difficulty == "Easy"]
        if easy_recs:
            easy_total = sum(r.estimated_roi_improvement for r in easy_recs)
            message += f"🟢 Easy fixes: +{easy_total:.2f}% ROI\n"
            for rec in easy_recs[:2]:  # Top 2 easy fixes
                message += f"   • {rec.recommendation}\n"

        message += f"""
📅 *PROJECTIONS*:
Current: {metrics.current_roi_percent:+.2f}% → Potential: {metrics.current_roi_percent + total_improvement:+.2f}%
Monthly: {(metrics.current_roi_percent + total_improvement) * 30:.1f}%

🕒 *Analysis Time*: {self.analysis_timestamp.strftime('%H:%M:%S')}
"""

        return message

    def format_telegram_detailed_report(self) -> str:
        """Format a detailed report for Telegram (split into multiple messages if needed)."""
        if not self.profitability_metrics:
            return "❌ No profitability metrics available"

        metrics = self.profitability_metrics

        message = f"""
📊 *DETAILED PROFITABILITY ANALYSIS*

💸 *FEE IMPACT*:
• Total Fees: {metrics.total_fees_sol:.6f} SOL (${metrics.total_fees_usd:.2f})
• Fee Rate: ${metrics.fee_drag_per_hour:.2f}/hour
• Break-even: {metrics.break_even_threshold:.6f} SOL per trade

📏 *POSITION ANALYSIS*:
• Avg Trade: {metrics.avg_trade_size_sol:.6f} SOL (${metrics.avg_trade_size_usd:.2f})
• Wallet %: {(metrics.avg_trade_size_sol / metrics.current_balance_sol) * 100:.3f}%
• Trading Rate: {metrics.trades_per_hour:.1f} trades/hour

🎯 *ALL RECOMMENDATIONS*:
"""

        for i, rec in enumerate(self.recommendations, 1):
            difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(rec.implementation_difficulty, "⚪")
            risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(rec.risk_level, "⚪")

            message += f"""
{i}. {difficulty_emoji} *{rec.recommendation}*
   📈 ROI: +{rec.estimated_roi_improvement:.2f}%
   ⚡ Time: {rec.time_to_implement}
   ⚠️ Risk: {risk_emoji} {rec.risk_level}
   📅 Monthly: +{rec.expected_monthly_roi:.1f}%
   🎯 Confidence: {rec.confidence_level:.0%}
"""

        return message

    def analyze_opportunity_patterns(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in trading opportunities"""
        if not opportunities:
            return {}

        # Analyze opportunity frequency and quality
        confidence_scores = []
        opportunity_types = {}
        hourly_distribution = {}

        for opp in opportunities:
            confidence = opp.get('confidence', 0)
            confidence_scores.append(confidence)

            opp_type = opp.get('type', 'unknown')
            opportunity_types[opp_type] = opportunity_types.get(opp_type, 0) + 1

            # Extract hour from timestamp
            try:
                timestamp = opp.get('timestamp', '')
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
            except:
                continue

        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        best_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            'total_opportunities': len(opportunities),
            'avg_confidence': avg_confidence,
            'opportunity_types': opportunity_types,
            'best_trading_hours': best_hours,
            'high_confidence_opportunities': len([c for c in confidence_scores if c > 0.7])
        }

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive profitability analysis report"""

        # Load data
        trades = self.load_live_trades()
        opportunities = self.load_opportunities()

        # Calculate metrics
        self.profitability_metrics = self.calculate_profitability_metrics(trades)
        self.recommendations = self.generate_profitability_recommendations(self.profitability_metrics, opportunities)
        opportunity_analysis = self.analyze_opportunity_patterns(opportunities)

        report = []
        report.append("🎯 LIVE TRADING PROFITABILITY ANALYSIS & ROI OPTIMIZATION")
        report.append("=" * 70)
        report.append("")

        # Current Performance Summary
        report.append("📊 CURRENT PERFORMANCE SUMMARY")
        report.append("-" * 40)
        metrics = self.profitability_metrics

        # Performance status
        if metrics.current_roi_percent > 0:
            status = "✅ PROFITABLE"
            status_color = "🟢"
        elif metrics.current_roi_percent > -0.05:
            status = "⚠️ NEAR BREAK-EVEN"
            status_color = "🟡"
        else:
            status = "❌ UNPROFITABLE"
            status_color = "🔴"

        report.append(f"{status_color} Status: {status}")
        report.append(f"📈 Current ROI: {metrics.current_roi_percent:+.3f}%")
        report.append(f"💰 Balance Change: {metrics.balance_change_sol:+.6f} SOL (${metrics.balance_change_sol * self.sol_price:+.2f})")
        report.append(f"⏱️ Session Duration: {metrics.session_duration_hours:.1f} hours")
        report.append(f"📊 Total Trades: {metrics.total_trades}")
        report.append(f"🔄 Trading Rate: {metrics.trades_per_hour:.1f} trades/hour")
        report.append("")

        # Fee Analysis
        report.append("💸 FEE IMPACT ANALYSIS")
        report.append("-" * 30)
        report.append(f"💰 Total Fees: {metrics.total_fees_sol:.6f} SOL (${metrics.total_fees_usd:.2f})")
        report.append(f"📊 Fee % of Volume: {metrics.fee_percentage_of_volume:.3f}%")
        report.append(f"⏱️ Fee Drag Rate: ${metrics.fee_drag_per_hour:.2f}/hour")
        report.append(f"🎯 Break-even per Trade: {metrics.break_even_threshold:.6f} SOL")
        report.append(f"📈 Profit Needed per Trade: {metrics.profit_per_trade_needed:.6f} SOL")
        report.append("")

        # Position Size Analysis
        report.append("📏 POSITION SIZE ANALYSIS")
        report.append("-" * 35)
        wallet_percentage = (metrics.avg_trade_size_sol / metrics.current_balance_sol) * 100
        report.append(f"💰 Average Trade Size: {metrics.avg_trade_size_sol:.6f} SOL (${metrics.avg_trade_size_usd:.2f})")
        report.append(f"📊 % of Wallet per Trade: {wallet_percentage:.3f}%")
        report.append(f"🎯 Conservative Approach: {'✅ Yes' if wallet_percentage < 1 else '❌ No'}")
        report.append("")

        # Opportunity Analysis
        if opportunity_analysis:
            report.append("🔍 OPPORTUNITY ANALYSIS")
            report.append("-" * 30)
            report.append(f"📊 Total Opportunities: {opportunity_analysis['total_opportunities']}")
            report.append(f"🎯 Average Confidence: {opportunity_analysis['avg_confidence']:.2f}")
            report.append(f"⭐ High Confidence (>0.7): {opportunity_analysis['high_confidence_opportunities']}")

            if opportunity_analysis['best_trading_hours']:
                report.append("🕐 Best Trading Hours:")
                for hour, count in opportunity_analysis['best_trading_hours']:
                    report.append(f"   {hour:02d}:00 - {count} opportunities")
            report.append("")

        # ROI Improvement Recommendations
        report.append("🚀 ROI IMPROVEMENT RECOMMENDATIONS")
        report.append("=" * 50)

        total_estimated_improvement = sum(rec.estimated_roi_improvement for rec in self.recommendations)
        report.append(f"🎯 TOTAL ESTIMATED ROI IMPROVEMENT: +{total_estimated_improvement:.2f}%")
        report.append("")

        for i, rec in enumerate(self.recommendations, 1):
            report.append(f"#{i}. {rec.recommendation}")
            report.append(f"    📝 Description: {rec.description}")
            report.append(f"    📈 ROI Improvement: +{rec.estimated_roi_improvement:.2f}%")
            report.append(f"    ⚡ Implementation: {rec.implementation_difficulty} ({rec.time_to_implement})")
            report.append(f"    ⚠️ Risk Level: {rec.risk_level}")
            report.append(f"    📅 Monthly ROI Potential: +{rec.expected_monthly_roi:.1f}%")
            report.append(f"    🎯 Confidence: {rec.confidence_level:.0%}")
            report.append("")

        # Implementation Priority
        report.append("⚡ IMPLEMENTATION PRIORITY")
        report.append("-" * 35)

        easy_recs = [r for r in self.recommendations if r.implementation_difficulty == "Easy"]
        medium_recs = [r for r in self.recommendations if r.implementation_difficulty == "Medium"]
        hard_recs = [r for r in self.recommendations if r.implementation_difficulty == "Hard"]

        if easy_recs:
            report.append("🟢 IMMEDIATE (Easy Implementation):")
            for rec in easy_recs:
                report.append(f"   • {rec.recommendation} (+{rec.estimated_roi_improvement:.2f}% ROI)")

        if medium_recs:
            report.append("🟡 SHORT-TERM (Medium Implementation):")
            for rec in medium_recs:
                report.append(f"   • {rec.recommendation} (+{rec.estimated_roi_improvement:.2f}% ROI)")

        if hard_recs:
            report.append("🔴 LONG-TERM (Hard Implementation):")
            for rec in hard_recs:
                report.append(f"   • {rec.recommendation} (+{rec.estimated_roi_improvement:.2f}% ROI)")

        report.append("")

        return "\n".join(report)

    async def send_telegram_profitability_alert(self, detailed: bool = False) -> bool:
        """Send profitability analysis as Telegram alert."""
        if not self.telegram_enabled:
            logger.warning("Telegram not configured - skipping alert")
            return False

        try:
            # Send summary message
            summary_message = self.format_telegram_summary()
            success = await self.send_telegram_message(summary_message)

            if success and detailed:
                # Send detailed report if requested
                detailed_message = self.format_telegram_detailed_report()

                # Split message if too long (Telegram limit is 4096 characters)
                if len(detailed_message) > 4000:
                    # Split into chunks
                    chunks = []
                    lines = detailed_message.split('\n')
                    current_chunk = ""

                    for line in lines:
                        if len(current_chunk + line + '\n') > 4000:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = line + '\n'
                        else:
                            current_chunk += line + '\n'

                    if current_chunk:
                        chunks.append(current_chunk)

                    # Send each chunk
                    for i, chunk in enumerate(chunks):
                        if i > 0:
                            await asyncio.sleep(1)  # Small delay between messages
                        await self.send_telegram_message(chunk)
                else:
                    await self.send_telegram_message(detailed_message)

            return success

        except Exception as e:
            logger.error(f"Error sending Telegram profitability alert: {e}")
            return False

    async def generate_and_send_telegram_report(self, detailed: bool = False) -> bool:
        """Generate comprehensive report and send to Telegram."""
        try:
            # Generate the comprehensive report
            report = self.generate_comprehensive_report()

            # Send Telegram alert
            telegram_success = await self.send_telegram_profitability_alert(detailed=detailed)

            if telegram_success:
                logger.info("✅ Profitability analysis sent to Telegram successfully")
            else:
                logger.warning("⚠️ Failed to send Telegram alert")

            return telegram_success

        except Exception as e:
            logger.error(f"Error generating and sending Telegram report: {e}")
            return False

    def save_analysis_report(self, report: str, output_file: Optional[str] = None) -> str:
        """Save the analysis report to a file"""
        if output_file is None:
            timestamp = self.analysis_timestamp.strftime("%Y%m%d_%H%M%S")
            output_file = f"output/live_profitability_analysis_{timestamp}.txt"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Profitability analysis report saved to: {output_file}")
        return output_file

    def save_metrics_json(self, output_file: Optional[str] = None) -> str:
        """Save the metrics data as JSON for programmatic access"""
        if output_file is None:
            timestamp = self.analysis_timestamp.strftime("%Y%m%d_%H%M%S")
            output_file = f"output/live_profitability_metrics_{timestamp}.json"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Convert metrics to dict for JSON serialization
        metrics_dict = {
            'profitability_metrics': {
                'current_roi_percent': self.profitability_metrics.current_roi_percent,
                'session_duration_hours': self.profitability_metrics.session_duration_hours,
                'total_trades': self.profitability_metrics.total_trades,
                'avg_trade_size_sol': self.profitability_metrics.avg_trade_size_sol,
                'avg_trade_size_usd': self.profitability_metrics.avg_trade_size_usd,
                'total_fees_sol': self.profitability_metrics.total_fees_sol,
                'total_fees_usd': self.profitability_metrics.total_fees_usd,
                'fee_percentage_of_volume': self.profitability_metrics.fee_percentage_of_volume,
                'break_even_threshold': self.profitability_metrics.break_even_threshold,
                'profit_per_trade_needed': self.profitability_metrics.profit_per_trade_needed,
                'current_balance_sol': self.profitability_metrics.current_balance_sol,
                'session_start_balance_sol': self.profitability_metrics.session_start_balance_sol,
                'balance_change_sol': self.profitability_metrics.balance_change_sol,
                'trades_per_hour': self.profitability_metrics.trades_per_hour,
                'fee_drag_per_hour': self.profitability_metrics.fee_drag_per_hour
            },
            'recommendations': [
                {
                    'recommendation': rec.recommendation,
                    'description': rec.description,
                    'estimated_roi_improvement': rec.estimated_roi_improvement,
                    'implementation_difficulty': rec.implementation_difficulty,
                    'time_to_implement': rec.time_to_implement,
                    'risk_level': rec.risk_level,
                    'expected_monthly_roi': rec.expected_monthly_roi,
                    'confidence_level': rec.confidence_level
                }
                for rec in self.recommendations
            ],
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'total_estimated_improvement': sum(rec.estimated_roi_improvement for rec in self.recommendations)
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_dict, f, indent=2)

        logger.info(f"Profitability metrics saved to: {output_file}")
        return output_file

async def main_async():
    """Async main function for command-line execution with Telegram support"""
    parser = argparse.ArgumentParser(description="Analyze live trading metrics for profitability optimization")
    parser.add_argument("--output-dir", default="output", help="Output directory for data files")
    parser.add_argument("--save-report", action="store_true", help="Save report to file")
    parser.add_argument("--save-json", action="store_true", help="Save metrics as JSON")
    parser.add_argument("--report-file", help="Custom report file path")
    parser.add_argument("--json-file", help="Custom JSON file path")
    parser.add_argument("--telegram", action="store_true", help="Send report to Telegram")
    parser.add_argument("--telegram-detailed", action="store_true", help="Send detailed report to Telegram")
    parser.add_argument("--telegram-only", action="store_true", help="Only send to Telegram, don't print to console")

    args = parser.parse_args()

    # Create analyzer
    analyzer = LiveMetricsProfitabilityAnalyzer(output_dir=args.output_dir)

    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()

    # Send to Telegram if requested
    telegram_success = False
    if args.telegram or args.telegram_detailed or args.telegram_only:
        detailed = args.telegram_detailed or args.telegram_only
        telegram_success = await analyzer.send_telegram_profitability_alert(detailed=detailed)

        if telegram_success:
            print("✅ Profitability analysis sent to Telegram successfully")
        else:
            print("❌ Failed to send Telegram alert")

    # Print report to console (unless telegram-only)
    if not args.telegram_only:
        print(report)

    # Save files if requested
    if args.save_report:
        report_file = analyzer.save_analysis_report(report, args.report_file)
        print(f"\n📄 Report saved to: {report_file}")

    if args.save_json:
        json_file = analyzer.save_metrics_json(args.json_file)
        print(f"📊 Metrics saved to: {json_file}")

    # Print quick summary
    if analyzer.profitability_metrics and not args.telegram_only:
        metrics = analyzer.profitability_metrics
        total_improvement = sum(rec.estimated_roi_improvement for rec in analyzer.recommendations)

        print("\n" + "="*50)
        print("🎯 QUICK SUMMARY")
        print("="*50)
        print(f"Current ROI: {metrics.current_roi_percent:+.3f}%")
        print(f"Potential Improvement: +{total_improvement:.2f}%")
        print(f"Projected ROI: {metrics.current_roi_percent + total_improvement:+.2f}%")
        print(f"Top Recommendation: {analyzer.recommendations[0].recommendation if analyzer.recommendations else 'None'}")
        if telegram_success:
            print(f"📱 Telegram Alert: ✅ Sent successfully")
        print("="*50)

def main():
    """Synchronous main function wrapper"""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
