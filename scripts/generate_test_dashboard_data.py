#!/usr/bin/env python3
"""
Generate Test Data for Dashboard Testing
Creates realistic test data for dashboard metrics validation.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def generate_wallet_data():
    """Generate test wallet data."""
    wallet_data = {
        "address": "J2FkQP683JsCsABxTCx7iGisdQZQPgFDMSvgPhGPE3bz",
        "balance": 500.0,
        "balance_usd": 500.0 * 180.0,  # Assuming SOL price of $180
        "last_updated": datetime.now().isoformat(),
        "transactions_count": 25,
        "total_volume": 12500.0
    }
    
    # Save wallet data
    os.makedirs('output/wallet', exist_ok=True)
    with open('output/wallet/wallet_balance.json', 'w') as f:
        json.dump(wallet_data, f, indent=2)
    
    print("✅ Generated wallet test data")
    return wallet_data

def generate_enhanced_live_trading_data():
    """Generate test enhanced live trading data."""
    # Generate latest metrics
    metrics = {
        "session_start": (datetime.now() - timedelta(hours=2)).isoformat(),
        "cycles_completed": 24,
        "cycles_successful": 22,
        "trades_attempted": 8,
        "trades_executed": 6,
        "trades_rejected": 2,
        "total_pnl": 15.75,
        "total_fees": 2.34,
        "success_rate": 75.0,
        "avg_trade_size": 125.50,
        "current_balance": 515.75,
        "last_updated": datetime.now().isoformat()
    }
    
    # Save enhanced live trading metrics
    os.makedirs('output/enhanced_live_trading', exist_ok=True)
    with open('output/enhanced_live_trading/latest_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Generate cycle data
    cycles_dir = 'output/enhanced_live_trading/cycles'
    os.makedirs(cycles_dir, exist_ok=True)
    
    for i in range(5):  # Generate last 5 cycles
        cycle_time = datetime.now() - timedelta(minutes=i*15)
        cycle_data = {
            "cycle_id": f"cycle_{cycle_time.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": cycle_time.isoformat(),
            "status": "completed" if random.random() > 0.1 else "failed",
            "market_regime": random.choice(["trending_up", "ranging", "volatile"]),
            "regime_confidence": round(random.uniform(0.6, 0.95), 3),
            "signals_generated": random.randint(1, 3),
            "trade_executed": random.random() > 0.3,
            "position_size": round(random.uniform(0.05, 0.15), 4),
            "var_95": round(random.uniform(0.01, 0.03), 4),
            "execution_time": round(random.uniform(0.5, 2.5), 2)
        }
        
        filename = f"cycle_{cycle_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(os.path.join(cycles_dir, filename), 'w') as f:
            json.dump(cycle_data, f, indent=2)
    
    # Generate trade data
    trades_dir = 'output/enhanced_live_trading/trades'
    os.makedirs(trades_dir, exist_ok=True)
    
    for i in range(6):  # Generate 6 trades
        trade_time = datetime.now() - timedelta(minutes=i*30)
        trade_data = {
            "trade_id": f"trade_{trade_time.strftime('%Y%m%d_%H%M%S')}",
            "timestamp": trade_time.isoformat(),
            "market": "SOL/USDC",
            "side": random.choice(["buy", "sell"]),
            "entry_price": round(random.uniform(175, 185), 2),
            "exit_price": round(random.uniform(175, 185), 2),
            "position_size": round(random.uniform(0.05, 0.15), 4),
            "pnl": round(random.uniform(-5, 10), 2),
            "fees": round(random.uniform(0.1, 0.5), 2),
            "duration_minutes": random.randint(5, 45),
            "signal_strength": round(random.uniform(0.6, 0.9), 3)
        }
        
        filename = f"trade_{trade_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(os.path.join(trades_dir, filename), 'w') as f:
            json.dump(trade_data, f, indent=2)
    
    print("✅ Generated enhanced live trading test data")
    return metrics

def generate_production_data():
    """Generate test production data."""
    production_metrics = {
        "deployment_start": (datetime.now() - timedelta(hours=6)).isoformat(),
        "total_runtime_hours": 6.0,
        "total_trades": 12,
        "successful_trades": 9,
        "failed_trades": 3,
        "total_pnl": 28.45,
        "total_volume": 2150.0,
        "max_drawdown": -8.20,
        "sharpe_ratio": 1.85,
        "win_rate": 75.0,
        "avg_trade_duration": 25.5,
        "last_updated": datetime.now().isoformat()
    }
    
    # Save production metrics
    os.makedirs('output/live_production/dashboard', exist_ok=True)
    with open('output/live_production/dashboard/latest_metrics.json', 'w') as f:
        json.dump(production_metrics, f, indent=2)
    
    print("✅ Generated production test data")
    return production_metrics

def generate_paper_trading_data():
    """Generate test paper trading data."""
    paper_metrics = {
        "session_start": (datetime.now() - timedelta(hours=4)).isoformat(),
        "mode": "paper_trading",
        "initial_balance": 1000.0,
        "current_balance": 1045.30,
        "total_pnl": 45.30,
        "trades_executed": 15,
        "win_rate": 66.7,
        "max_drawdown": -12.50,
        "total_fees": 7.85,
        "avg_trade_size": 85.20,
        "last_updated": datetime.now().isoformat()
    }
    
    # Save paper trading metrics
    os.makedirs('output/paper_trading/dashboard', exist_ok=True)
    with open('output/paper_trading/dashboard/latest_metrics.json', 'w') as f:
        json.dump(paper_metrics, f, indent=2)
    
    print("✅ Generated paper trading test data")
    return paper_metrics

def generate_system_metrics():
    """Generate system health metrics."""
    system_metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": round(random.uniform(10, 30), 1),
        "memory_usage": round(random.uniform(40, 70), 1),
        "disk_usage": round(random.uniform(1, 5), 1),
        "network_latency": round(random.uniform(10, 50), 1),
        "api_response_times": {
            "helius": round(random.uniform(100, 300), 1),
            "birdeye": round(random.uniform(200, 500), 1)
        },
        "error_count_last_hour": random.randint(0, 3),
        "uptime_hours": round(random.uniform(20, 100), 1)
    }
    
    # Save system metrics
    os.makedirs('output/system', exist_ok=True)
    with open('output/system/health_metrics.json', 'w') as f:
        json.dump(system_metrics, f, indent=2)
    
    print("✅ Generated system health test data")
    return system_metrics

def main():
    """Generate all test data for dashboard testing."""
    print("🔄 Generating Test Data for Dashboard Testing")
    print("="*60)
    
    # Generate all test data
    wallet_data = generate_wallet_data()
    enhanced_data = generate_enhanced_live_trading_data()
    production_data = generate_production_data()
    paper_data = generate_paper_trading_data()
    system_data = generate_system_metrics()
    
    # Generate summary report
    summary = {
        "generation_time": datetime.now().isoformat(),
        "data_sources": {
            "wallet": "output/wallet/wallet_balance.json",
            "enhanced_live_trading": "output/enhanced_live_trading/latest_metrics.json",
            "production": "output/live_production/dashboard/latest_metrics.json",
            "paper_trading": "output/paper_trading/dashboard/latest_metrics.json",
            "system": "output/system/health_metrics.json"
        },
        "test_metrics": {
            "total_pnl": enhanced_data["total_pnl"] + production_data["total_pnl"],
            "total_trades": enhanced_data["trades_executed"] + production_data["total_trades"],
            "wallet_balance": wallet_data["balance"],
            "system_health": "healthy"
        }
    }
    
    with open('output/dashboard_test_data_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("="*60)
    print("✅ Test Data Generation Complete!")
    print(f"📊 Summary saved to: output/dashboard_test_data_summary.json")
    print(f"💰 Total PnL: ${summary['test_metrics']['total_pnl']:.2f}")
    print(f"📈 Total Trades: {summary['test_metrics']['total_trades']}")
    print(f"💳 Wallet Balance: {summary['test_metrics']['wallet_balance']:.2f} SOL")
    
    return summary

if __name__ == "__main__":
    main()
