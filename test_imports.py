#!/usr/bin/env python3
"""
Test script to check all critical imports for the trading system.
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

def test_import(module_name, import_statement):
    """Test a single import and return result."""
    try:
        exec(import_statement)
        print(f"✅ {module_name}: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {module_name}: FAILED - {e}")
        return False

def main():
    """Test all critical imports."""
    print("🔍 Testing Critical Imports for Trading System")
    print("=" * 60)
    
    imports_to_test = [
        ("Solders Keypair", "from solders.keypair import Keypair"),
        ("Transaction Executor", "from phase_4_deployment.rpc_execution.transaction_executor import TransactionExecutor"),
        ("Orca Swap Builder", "from core.dex.orca_swap_builder import OrcaSwapBuilder"),
        ("Birdeye Scanner", "from phase_4_deployment.data_router.birdeye_scanner import BirdeyeScanner"),
        ("Signal Enricher", "from phase_4_deployment.signal_generator.signal_enricher import SignalEnricher"),
        ("Telegram Notifier", "from core.notifications.telegram_notifier import TelegramNotifier"),
        ("Helius Client", "from phase_4_deployment.rpc_execution.helius_client import HeliusClient"),
        ("Jito Bundle Client", "from phase_4_deployment.rpc_execution.jito_bundle_client import JitoBundleClient"),
    ]
    
    success_count = 0
    total_count = len(imports_to_test)
    
    for module_name, import_statement in imports_to_test:
        if test_import(module_name, import_statement):
            success_count += 1
    
    print("=" * 60)
    print(f"📊 Results: {success_count}/{total_count} imports successful")
    
    if success_count == total_count:
        print("🎉 All imports working! System ready for trading.")
        return True
    else:
        print("⚠️ Some imports failed. System needs fixes before trading.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
