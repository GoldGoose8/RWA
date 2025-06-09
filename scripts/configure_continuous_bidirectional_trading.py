#!/usr/bin/env python3
"""
Configure Continuous Bidirectional Trading System
=================================================

Ensures the system is properly configured for:
- Continuous 24/7 trading operation
- Bidirectional SOL ↔ USDC autoswap trading
- Automatic balance management
- Proper signal generation for both BUY and SELL
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv, set_key

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

class ContinuousBidirectionalTradingConfigurator:
    """Configures the system for continuous bidirectional trading."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / 'config.yaml'
        self.env_file = self.project_root / '.env'
        
    def analyze_current_configuration(self):
        """Analyze current system configuration."""
        print("🔍 ANALYZING CURRENT CONFIGURATION")
        print("=" * 60)
        
        # Check environment variables
        print("📋 Environment Variables:")
        trading_enabled = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        paper_trading = os.getenv('PAPER_TRADING', 'false').lower() == 'true'
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        print(f"   LIVE_TRADING: {trading_enabled} ✅" if trading_enabled else f"   LIVE_TRADING: {trading_enabled} ❌")
        print(f"   PAPER_TRADING: {paper_trading} ❌" if paper_trading else f"   PAPER_TRADING: {paper_trading} ✅")
        print(f"   DRY_RUN: {dry_run} ❌" if dry_run else f"   DRY_RUN: {dry_run} ✅")
        
        # Check wallet configuration
        print("\n💰 Wallet Configuration:")
        wallet_address = os.getenv('WALLET_ADDRESS')
        wallet_private_key = os.getenv('WALLET_PRIVATE_KEY')
        usdc_account = os.getenv('WALLET_USDC_ACCOUNT')
        
        print(f"   Wallet Address: {'✅ Configured' if wallet_address else '❌ Missing'}")
        print(f"   Private Key: {'✅ Configured' if wallet_private_key else '❌ Missing'}")
        print(f"   USDC Account: {'✅ Configured' if usdc_account else '❌ Missing'}")
        
        # Check trading parameters
        print("\n⚙️ Trading Parameters:")
        max_trades_per_day = os.getenv('MAX_TRADES_PER_DAY', '20')
        min_trade_interval = os.getenv('MIN_TRADE_INTERVAL', '300')
        confidence_threshold = os.getenv('CONFIDENCE_THRESHOLD', '0.8')
        
        print(f"   Max Trades/Day: {max_trades_per_day}")
        print(f"   Min Trade Interval: {min_trade_interval}s")
        print(f"   Confidence Threshold: {confidence_threshold}")
        
        return {
            'live_trading': trading_enabled,
            'paper_trading': paper_trading,
            'dry_run': dry_run,
            'wallet_configured': bool(wallet_address and wallet_private_key),
            'usdc_account': bool(usdc_account)
        }
    
    def check_bidirectional_trading_setup(self):
        """Check if bidirectional trading is properly configured."""
        print("\n🔄 BIDIRECTIONAL TRADING ANALYSIS")
        print("=" * 60)
        
        # Check strategy configuration
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            strategies = config.get('strategies', {})
            print("📊 Strategy Configuration:")
            
            for strategy_name, strategy_config in strategies.items():
                if isinstance(strategy_config, dict):
                    enabled = strategy_config.get('enabled', False)
                    weight = strategy_config.get('weight', 0)
                    print(f"   {strategy_name}: {'✅ Enabled' if enabled else '❌ Disabled'} (weight: {weight})")
            
            # Check execution settings
            execution = config.get('execution', {})
            print(f"\n⚡ Execution Configuration:")
            print(f"   Real Swaps: {'✅ Enabled' if execution.get('use_real_swaps') else '❌ Disabled'}")
            print(f"   Jito Bundles: {'✅ Enabled' if execution.get('use_jito') else '❌ Disabled'}")
            print(f"   Placeholders: {'✅ Disabled' if execution.get('disable_placeholders') else '❌ Enabled'}")
            
            # Check trading settings
            trading = config.get('trading', {})
            print(f"\n📈 Trading Configuration:")
            print(f"   Trading Enabled: {'✅ Yes' if trading.get('enabled') else '❌ No'}")
            print(f"   Max Trades/Day: {trading.get('max_trades_per_day', 'Not set')}")
            print(f"   Min Trade Interval: {trading.get('min_trade_interval', 'Not set')}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Error reading config: {e}")
            return False
    
    def configure_continuous_operation(self):
        """Configure the system for continuous operation."""
        print("\n🔧 CONFIGURING CONTINUOUS OPERATION")
        print("=" * 60)
        
        # Update environment variables for continuous trading
        updates = {
            'LIVE_TRADING': 'true',
            'PAPER_TRADING': 'false',
            'DRY_RUN': 'false',
            'SIMULATION': 'false',
            'USE_REAL_SWAPS': 'true',
            'DISABLE_PLACEHOLDERS': 'true',
            'CIRCUIT_BREAKER_ENABLED': 'true',
            'ADAPTIVE_WEIGHTING_ENABLED': 'true',
            'MARKET_REGIME_ENABLED': 'true',
            'WHALE_WATCHING_ENABLED': 'true',
            'MONITORING_ENABLED': 'true',
            'TELEGRAM_ALERTS': 'true'
        }
        
        for key, value in updates.items():
            set_key(self.env_file, key, value)
            print(f"   ✅ {key} = {value}")
        
        print("\n✅ Continuous operation configured!")
    
    def display_bidirectional_trading_logic(self):
        """Display how bidirectional trading works."""
        print("\n🔄 BIDIRECTIONAL TRADING LOGIC")
        print("=" * 60)
        print("The system automatically trades in both directions:")
        print()
        print("📈 BUY SIGNALS (SOL ← USDC):")
        print("   • Price momentum down (buy low)")
        print("   • Whale accumulation detected")
        print("   • Mean reversion opportunity")
        print("   • Exchange outflow (bullish)")
        print()
        print("📉 SELL SIGNALS (SOL → USDC):")
        print("   • Price momentum up (sell high)")
        print("   • Whale distribution detected")
        print("   • Volatility breakout upward")
        print("   • Exchange inflow (bearish)")
        print()
        print("🔄 AUTOMATIC BALANCE MANAGEMENT:")
        print("   • Pre-trade balance verification")
        print("   • Automatic token account creation")
        print("   • SOL ↔ USDC conversion as needed")
        print("   • 90% active capital allocation")
        print()
        print("⏰ CONTINUOUS OPERATION:")
        print("   • 24/7 trading cycles")
        print("   • 60-second cycle intervals")
        print("   • Real-time signal generation")
        print("   • Automatic position sizing")
    
    def display_trading_parameters(self):
        """Display current trading parameters."""
        print("\n⚙️ TRADING PARAMETERS")
        print("=" * 60)
        
        params = {
            'Max Trades/Day': os.getenv('MAX_TRADES_PER_DAY', '20'),
            'Max Trades/Hour': os.getenv('MAX_TRADES_PER_HOUR', '6'),
            'Min Trade Interval': f"{os.getenv('MIN_TRADE_INTERVAL', '300')}s",
            'Confidence Threshold': os.getenv('CONFIDENCE_THRESHOLD', '0.8'),
            'Max Position Size': f"{float(os.getenv('MAX_POSITION_SIZE_PCT', '0.8')) * 100}%",
            'Active Capital': f"{float(os.getenv('WALLET_ACTIVE_TRADING_PCT', '0.9')) * 100}%",
            'Slippage Tolerance': f"{float(os.getenv('SLIPPAGE_TOLERANCE', '0.01')) * 100}%",
            'Priority Fee': f"{os.getenv('PRIORITY_FEE_LAMPORTS', '10000')} lamports"
        }
        
        for param, value in params.items():
            print(f"   {param}: {value}")
    
    def run_configuration_check(self):
        """Run complete configuration check and setup."""
        print("🚀 CONTINUOUS BIDIRECTIONAL TRADING CONFIGURATOR")
        print("=" * 70)
        
        # Step 1: Analyze current configuration
        current_config = self.analyze_current_configuration()
        
        # Step 2: Check bidirectional setup
        bidirectional_ok = self.check_bidirectional_trading_setup()
        
        # Step 3: Configure for continuous operation
        self.configure_continuous_operation()
        
        # Step 4: Display trading logic
        self.display_bidirectional_trading_logic()
        
        # Step 5: Display parameters
        self.display_trading_parameters()
        
        # Step 6: Final status
        print("\n🎯 CONFIGURATION STATUS")
        print("=" * 60)
        
        if current_config['live_trading'] and current_config['wallet_configured']:
            print("✅ System is configured for continuous bidirectional trading!")
            print("🚀 Ready to start: python3 scripts/unified_live_trading.py")
        else:
            print("⚠️ Additional configuration needed:")
            if not current_config['live_trading']:
                print("   • Enable live trading")
            if not current_config['wallet_configured']:
                print("   • Configure wallet credentials")
        
        print("\n💡 RECOMMENDED NEXT STEPS:")
        print("1. Fund wallet: python3 scripts/fund_native_wallet.py --instructions")
        print("2. Check balance: python3 scripts/check_native_wallet_balance.py")
        print("3. Start trading: python3 scripts/unified_live_trading.py")
        print("4. Monitor dashboard: ./start_winsor_dashboard.sh")

def main():
    """Main function."""
    configurator = ContinuousBidirectionalTradingConfigurator()
    configurator.run_configuration_check()

if __name__ == "__main__":
    main()
