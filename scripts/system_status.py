#!/usr/bin/env python3
"""
System Status Summary
=====================

Comprehensive status check for the RWA Trading System.
Shows configuration, connectivity, and readiness for live trading.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n🔧 {title}")
    print("-" * 40)

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_section("Dependencies Status")
    
    try:
        import solders
        print(f"✅ solders: {solders.__version__}")
    except ImportError:
        print("❌ solders: Not installed")
        return False
    
    try:
        import solana
        try:
            version = solana.__version__
        except AttributeError:
            version = "installed"
        print(f"✅ solana: {version}")
    except ImportError:
        print("❌ solana: Not installed")
        return False
    
    try:
        import streamlit
        print(f"✅ streamlit: {streamlit.__version__}")
    except ImportError:
        print("❌ streamlit: Not installed")
        return False
    
    try:
        import pandas
        print(f"✅ pandas: {pandas.__version__}")
    except ImportError:
        print("❌ pandas: Not installed")
        return False
    
    try:
        import numpy
        print(f"✅ numpy: {numpy.__version__}")
    except ImportError:
        print("❌ numpy: Not installed")
        return False
    
    return True

def check_configuration():
    """Check configuration status."""
    print_section("Configuration Status")
    
    # Load environment variables
    load_dotenv()
    
    config_status = {}
    
    # Check Helius
    helius_url = os.getenv("HELIUS_RPC_URL")
    helius_key = os.getenv("HELIUS_API_KEY")
    if helius_url and helius_key and "your_" not in helius_url:
        print("✅ Helius RPC: Configured")
        config_status["helius"] = True
    else:
        print("❌ Helius RPC: Not configured")
        config_status["helius"] = False
    
    # Check QuickNode
    quicknode_url = os.getenv("QUICKNODE_RPC_URL")
    quicknode_key = os.getenv("QUICKNODE_API_KEY")
    if quicknode_url and quicknode_key and "your-" not in quicknode_url:
        print("✅ QuickNode RPC: Configured")
        config_status["quicknode"] = True
    else:
        print("⚠️ QuickNode RPC: Not configured (optional)")
        config_status["quicknode"] = False
    
    # Check Wallet
    wallet_address = os.getenv("WALLET_ADDRESS")
    wallet_key = os.getenv("WALLET_PRIVATE_KEY")
    keypair_path = os.getenv("KEYPAIR_PATH")
    
    if wallet_address and wallet_key and "your_" not in wallet_address:
        print(f"✅ Wallet: {wallet_address}")
        if keypair_path and Path(keypair_path).exists():
            print(f"✅ Keypair file: {keypair_path}")
        else:
            print("⚠️ Keypair file: Not found")
        config_status["wallet"] = True
    else:
        print("❌ Wallet: Not configured")
        config_status["wallet"] = False
    
    # Check Jito
    jito_url = os.getenv("JITO_RPC_URL")
    if jito_url:
        print("✅ Jito: Configured")
        config_status["jito"] = True
    else:
        print("❌ Jito: Not configured")
        config_status["jito"] = False
    
    return config_status

def check_wallet_balance():
    """Check wallet balance."""
    print_section("Wallet Balance")
    
    wallet_address = os.getenv("WALLET_ADDRESS")
    if not wallet_address or "your_" in wallet_address:
        print("❌ Wallet not configured")
        return 0
    
    try:
        from solders.pubkey import Pubkey
        from solana.rpc.api import Client
        
        # Try Helius first
        helius_url = os.getenv("HELIUS_RPC_URL")
        if helius_url and "your_" not in helius_url:
            client = Client(helius_url)
            pubkey = Pubkey.from_string(wallet_address)
            balance_response = client.get_balance(pubkey)
            balance_lamports = balance_response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            print(f"💰 Balance: {balance_sol:.9f} SOL")
            print(f"📍 Address: {wallet_address}")
            
            if balance_sol == 0:
                print("⚠️ Wallet needs funding for trading")
            elif balance_sol < 0.1:
                print("⚠️ Low balance - consider adding more SOL")
            else:
                print("✅ Wallet sufficiently funded")
            
            return balance_sol
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return 0

def check_files():
    """Check important files exist."""
    print_section("File Status")
    
    important_files = [
        ".env",
        "config.yaml", 
        "config/live_production.yaml",
        "requirements.txt",
        "scripts/validate_live_config.py",
        "scripts/test_live_endpoints.py",
        "scripts/unified_live_trading.py"
    ]
    
    all_exist = True
    for file_path in important_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Main status check function."""
    print_header("RWA Trading System - Status Summary")
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check configuration
    config_status = check_configuration()
    
    # Check wallet balance
    balance = check_wallet_balance()
    
    # Check files
    files_ok = check_files()
    
    # Overall status
    print_header("Overall System Status")
    
    ready_for_trading = (
        deps_ok and
        config_status.get("helius", False) and
        config_status.get("wallet", False) and
        config_status.get("jito", False) and
        files_ok and
        balance > 0
    )
    
    if ready_for_trading:
        print("🎉 SYSTEM READY FOR LIVE TRADING!")
        print("✅ All dependencies installed")
        print("✅ Configuration complete")
        print("✅ Wallet funded and ready")
        print("✅ All required files present")
        print("\n🚀 Next step: python3 scripts/unified_live_trading.py")
        
    else:
        print("⚠️ SYSTEM NOT READY - Issues to resolve:")
        
        if not deps_ok:
            print("❌ Install missing dependencies")
        
        if not config_status.get("helius", False):
            print("❌ Configure Helius RPC")
            
        if not config_status.get("wallet", False):
            print("❌ Configure trading wallet")
            
        if not config_status.get("jito", False):
            print("❌ Configure Jito endpoint")
            
        if balance == 0:
            print("❌ Fund trading wallet with SOL")
            
        if not files_ok:
            print("❌ Missing required files")
        
        print("\n🔧 Recommended actions:")
        if not config_status.get("quicknode", False):
            print("1. Get QuickNode RPC endpoint (recommended)")
        if balance == 0:
            print("2. Fund wallet with 1-2 SOL for testing")
        print("3. Run: python3 scripts/validate_live_config.py")
        print("4. Run: python3 scripts/test_live_endpoints.py")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
