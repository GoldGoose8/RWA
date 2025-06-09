#!/usr/bin/env python3
"""
Performance Analysis Script for Synergy7 Trading System

This script analyzes the results of load tests and generates performance reports.
"""

import os
import sys
import json
import yaml
import logging
import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance_analysis")

class PerformanceAnalyzer:
    """
    Analyzes performance test results.
    """

    def __init__(self, results_file: str, output_dir: str):
        """
        Initialize the analyzer.

        Args:
            results_file: Path to load test results file
            output_dir: Directory to store analysis results
        """
        self.results_file = Path(results_file)
        self.output_dir = Path(output_dir)
        self.results = None
        self.analysis = {
            "timestamp": datetime.now().isoformat(),
            "results_file": str(self.results_file),
            "summary": {},
            "bottlenecks": [],
            "recommendations": []
        }

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized performance analyzer with results: {results_file}, output: {output_dir}")

    def load_data(self) -> bool:
        """
        Load test results.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load test results
            if not self.results_file.exists():
                logger.error(f"Results file not found: {self.results_file}")
                # Create a minimal results structure for analysis
                self.results = {
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration": 0,
                    "transactions_per_second": 0,
                    "ramp_up": 0,
                    "transactions": {
                        "total": 0,
                        "successful": 0,
                        "failed": 0
                    },
                    "latency": {
                        "min": 0,
                        "max": 0,
                        "avg": 0,
                        "p50": 0,
                        "p90": 0,
                        "p95": 0,
                        "p99": 0
                    },
                    "throughput": {
                        "min": 0,
                        "max": 0,
                        "avg": 0
                    },
                    "errors": ["Results file not found"],
                    "success": False
                }
                logger.warning("Created minimal results structure for analysis")
                return True  # Return True to continue analysis with minimal data

            with open(self.results_file, "r") as f:
                self.results = json.load(f)

            logger.info("Data loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            # Create a minimal results structure for analysis
            self.results = {
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": 0,
                "transactions_per_second": 0,
                "ramp_up": 0,
                "transactions": {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                },
                "latency": {
                    "min": 0,
                    "max": 0,
                    "avg": 0,
                    "p50": 0,
                    "p90": 0,
                    "p95": 0,
                    "p99": 0
                },
                "throughput": {
                    "min": 0,
                    "max": 0,
                    "avg": 0
                },
                "errors": [f"Error loading data: {str(e)}"],
                "success": False
            }
            logger.warning("Created minimal results structure for analysis after error")
            return True  # Return True to continue analysis with minimal data

    def analyze(self) -> bool:
        """
        Analyze the test results.

        Returns:
            True if analysis successful, False otherwise
        """
        if not self.results:
            logger.error("No data to analyze")
            return False

        logger.info("Analyzing performance test results...")

        # Extract key metrics
        transactions = self.results.get("transactions", {})
        latency = self.results.get("latency", {})
        throughput = self.results.get("throughput", {})

        # Calculate summary metrics
        total_tx = transactions.get("total", 0)
        successful_tx = transactions.get("successful", 0)
        failed_tx = transactions.get("failed", 0)

        success_rate = (successful_tx / total_tx) * 100 if total_tx > 0 else 0
        error_rate = (failed_tx / total_tx) * 100 if total_tx > 0 else 0

        avg_latency = latency.get("avg", 0)
        p95_latency = latency.get("p95", 0)
        p99_latency = latency.get("p99", 0)

        avg_throughput = throughput.get("avg", 0)
        max_throughput = throughput.get("max", 0)

        target_tps = self.results.get("transactions_per_second", 0)
        throughput_achievement = (avg_throughput / target_tps) * 100 if target_tps > 0 else 0

        # Create summary
        self.analysis["summary"] = {
            "total_transactions": total_tx,
            "successful_transactions": successful_tx,
            "failed_transactions": failed_tx,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "p99_latency": p99_latency,
            "avg_throughput": avg_throughput,
            "max_throughput": max_throughput,
            "target_throughput": target_tps,
            "throughput_achievement": throughput_achievement
        }

        # Identify bottlenecks
        self._identify_bottlenecks()

        # Generate recommendations
        self._generate_recommendations()

        logger.info("Analysis completed")
        return True

    def _identify_bottlenecks(self):
        """Identify performance bottlenecks."""
        bottlenecks = []

        # Check throughput achievement
        throughput_achievement = self.analysis["summary"]["throughput_achievement"]
        if throughput_achievement < 90:
            bottlenecks.append({
                "type": "throughput",
                "description": f"System achieved only {throughput_achievement:.1f}% of target throughput",
                "severity": "high" if throughput_achievement < 70 else "medium"
            })

        # Check latency
        avg_latency = self.analysis["summary"]["avg_latency"]
        p99_latency = self.analysis["summary"]["p99_latency"]

        if avg_latency > 0.5:  # More than 500ms average latency
            bottlenecks.append({
                "type": "latency",
                "description": f"High average latency: {avg_latency:.3f} seconds",
                "severity": "high" if avg_latency > 1.0 else "medium"
            })

        if p99_latency > 2.0:  # More than 2s for p99 latency
            bottlenecks.append({
                "type": "latency",
                "description": f"High p99 latency: {p99_latency:.3f} seconds",
                "severity": "high" if p99_latency > 5.0 else "medium"
            })

        # Check error rate
        error_rate = self.analysis["summary"]["error_rate"]
        if error_rate > 5:  # More than 5% error rate
            bottlenecks.append({
                "type": "errors",
                "description": f"High error rate: {error_rate:.1f}%",
                "severity": "high" if error_rate > 10 else "medium"
            })

        self.analysis["bottlenecks"] = bottlenecks

    def _generate_recommendations(self):
        """Generate performance improvement recommendations."""
        recommendations = []

        # Based on bottlenecks
        for bottleneck in self.analysis["bottlenecks"]:
            if bottleneck["type"] == "throughput":
                recommendations.append("Optimize transaction processing to improve throughput")
                recommendations.append("Consider scaling horizontally by adding more processing nodes")

            if bottleneck["type"] == "latency":
                recommendations.append("Reduce API call overhead by implementing batching")
                recommendations.append("Optimize transaction preparation and signing process")
                recommendations.append("Consider using more efficient serialization methods")

            if bottleneck["type"] == "errors":
                recommendations.append("Implement more robust error handling and retry mechanisms")
                recommendations.append("Analyze error patterns to identify and fix common failure points")

        # General recommendations
        if not recommendations:
            recommendations.append("System performance is good, consider increasing load for stress testing")

        self.analysis["recommendations"] = recommendations

    def generate_report(self) -> str:
        """
        Generate a performance report.

        Returns:
            Path to the generated report file
        """
        report_file = self.output_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(report_file, "w") as f:
                json.dump(self.analysis, f, indent=2)

            logger.info(f"Performance report saved to {report_file}")
        except Exception as e:
            logger.error(f"Error saving performance report: {str(e)}")

        return str(report_file)

    def generate_charts(self) -> List[str]:
        """
        Generate performance charts.

        Returns:
            List of paths to generated chart files
        """
        if not self.results:
            logger.error("No data to generate charts")
            return []

        chart_files = []

        try:
            # Create throughput vs. latency chart
            fig, ax = plt.subplots(figsize=(10, 6))

            summary = self.analysis["summary"]

            # Bar chart for throughput and latency
            metrics = ["avg_throughput", "max_throughput", "target_throughput"]
            values = [summary[m] for m in metrics]
            labels = ["Avg Throughput", "Max Throughput", "Target Throughput"]

            ax.bar(labels, values, color=["blue", "green", "red"])
            ax.set_ylabel("Transactions per Second")
            ax.set_title("Throughput Performance")

            # Add success rate as text
            success_rate = summary["success_rate"]
            ax.text(0.5, 0.9, f"Success Rate: {success_rate:.1f}%",
                   transform=ax.transAxes, ha="center",
                   bbox=dict(facecolor="white", alpha=0.8))

            # Save chart
            throughput_chart = self.output_dir / f"throughput_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(throughput_chart)
            plt.close()

            chart_files.append(str(throughput_chart))

            # Create latency chart
            fig, ax = plt.subplots(figsize=(10, 6))

            # Bar chart for latency metrics
            metrics = ["avg_latency", "p95_latency", "p99_latency"]
            values = [summary[m] for m in metrics]
            labels = ["Avg Latency", "p95 Latency", "p99 Latency"]

            ax.bar(labels, values, color=["blue", "orange", "red"])
            ax.set_ylabel("Latency (seconds)")
            ax.set_title("Latency Performance")

            # Save chart
            latency_chart = self.output_dir / f"latency_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(latency_chart)
            plt.close()

            chart_files.append(str(latency_chart))

            logger.info(f"Generated {len(chart_files)} performance charts")
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")

        return chart_files

    def print_summary(self):
        """Print a summary of the performance analysis."""
        if not self.analysis or "summary" not in self.analysis:
            logger.error("No analysis to print")
            return

        summary = self.analysis["summary"]
        bottlenecks = self.analysis["bottlenecks"]
        recommendations = self.analysis["recommendations"]

        print("\n=== PERFORMANCE ANALYSIS SUMMARY ===\n")

        print("Transaction Metrics:")
        print(f"  Total Transactions: {summary['total_transactions']}")
        print(f"  Successful Transactions: {summary['successful_transactions']}")
        print(f"  Failed Transactions: {summary['failed_transactions']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Error Rate: {summary['error_rate']:.1f}%")

        print("\nLatency Metrics:")
        print(f"  Average Latency: {summary['avg_latency']:.3f} seconds")
        print(f"  p95 Latency: {summary['p95_latency']:.3f} seconds")
        print(f"  p99 Latency: {summary['p99_latency']:.3f} seconds")

        print("\nThroughput Metrics:")
        print(f"  Average Throughput: {summary['avg_throughput']:.2f} TPS")
        print(f"  Maximum Throughput: {summary['max_throughput']:.2f} TPS")
        print(f"  Target Throughput: {summary['target_throughput']:.2f} TPS")
        print(f"  Throughput Achievement: {summary['throughput_achievement']:.1f}%")

        if bottlenecks:
            print("\nIdentified Bottlenecks:")
            for i, bottleneck in enumerate(bottlenecks, 1):
                severity = bottleneck["severity"].upper()
                print(f"  {i}. [{severity}] {bottleneck['description']}")

        if recommendations:
            print("\nRecommendations:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")

        print("\n=====================================\n")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze performance test results for Synergy7 Trading System")
    parser.add_argument("results_file", help="Path to load test results file")
    parser.add_argument("--output", default="output/performance_analysis", help="Directory to store analysis results")
    parser.add_argument("--charts", action="store_true", help="Generate performance charts")

    args = parser.parse_args()

    # Create analyzer
    analyzer = PerformanceAnalyzer(args.results_file, args.output)

    # Load data
    if not analyzer.load_data():
        logger.error("Failed to load data")
        return 1

    # Analyze results
    if not analyzer.analyze():
        logger.error("Failed to analyze results")
        return 1

    # Print summary
    analyzer.print_summary()

    # Generate report
    report_file = analyzer.generate_report()
    logger.info(f"Performance report saved to {report_file}")

    # Generate charts if requested
    if args.charts:
        try:
            import matplotlib
            chart_files = analyzer.generate_charts()
            if chart_files:
                logger.info(f"Performance charts saved to: {', '.join(chart_files)}")
        except ImportError:
            logger.error("Could not generate charts: matplotlib not installed")
            logger.info("Install matplotlib with: pip install matplotlib")

    return 0

if __name__ == "__main__":
    sys.exit(main())
