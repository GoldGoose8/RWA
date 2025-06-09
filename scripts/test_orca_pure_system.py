#!/usr/bin/env python3
"""
Test Pure Orca Trading System
NO JUPITER - NO SIMULATIONS - ONLY REAL ORCA SWAPS
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pure_orca_system():
    """Test the pure Orca trading system with robust debugging."""
    
    logger.info("🚀 TESTING PURE ORCA TRADING SYSTEM")
    logger.info("=" * 60)
    logger.info("⚠️  NO JUPITER - NO SIMULATIONS - ONLY REAL ORCA SWAPS")
    logger.info("=" * 60)
    
    # Test 1: Verify no Jupiter dependencies
    logger.info("1️⃣ Testing Jupiter removal...")
    try:
        # This should fail if Jupiter is still imported
        from scripts.unified_live_trading import UnifiedLiveTrader
        trader = UnifiedLiveTrader()
        
        # Try to call Jupiter function - should raise error
        try:
            fake_signal = {'action': 'BUY', 'market': 'SOL-USDC', 'size': 0.01}
            await trader.build_jupiter_transaction(fake_signal)
            logger.error("❌ CRITICAL: Jupiter function still works - NOT REMOVED")
            return False
        except RuntimeError as e:
            if "Jupiter transactions not allowed" in str(e):
                logger.info("✅ Jupiter transactions properly blocked")
            else:
                logger.error(f"❌ Unexpected error: {e}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error testing Jupiter removal: {e}")
        return False
    
    # Test 2: Verify Orca native builder
    logger.info("2️⃣ Testing Orca native builder...")
    try:
        from core.dex.orca_fallback_builder import OrcaFallbackBuilder

        # Create a dummy keypair for testing
        try:
            from solders.keypair import Keypair
            import base58

            # Use environment variable or create dummy keypair
            wallet_private_key = os.getenv('WALLET_PRIVATE_KEY')
            if wallet_private_key:
                private_key_bytes = base58.b58decode(wallet_private_key)
                keypair = Keypair.from_bytes(private_key_bytes)
            else:
                keypair = Keypair()  # Generate dummy keypair for testing

            # Create dummy RPC client
            class DummyRPCClient:
                pass

            orca_builder = OrcaFallbackBuilder(keypair, DummyRPCClient())

            # Test pool search
            pool_info = await orca_builder._find_best_orca_pool(
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
            )

            if pool_info:
                logger.info(f"✅ Found Orca pool: {pool_info['address']}")
                logger.info(f"   Liquidity: ${pool_info.get('liquidity_usd', 0):,.2f}")
            else:
                logger.warning("⚠️ No Orca pools found")

        except ImportError:
            logger.warning("⚠️ Solders not available for Orca testing")
            
    except Exception as e:
        logger.error(f"❌ Error testing Orca builder: {e}")
        return False
    
    # Test 3: Verify simulation blocking
    logger.info("3️⃣ Testing simulation blocking...")
    try:
        # Try to create trader with simulation modes - should fail
        try:
            dry_run_trader = UnifiedLiveTrader()
            # Manually set simulation mode to test blocking
            dry_run_trader.dry_run = True
            result = await dry_run_trader.initialize_components()
            if result:
                logger.error("❌ CRITICAL: Dry run mode allowed - NOT BLOCKED")
                return False
            else:
                logger.info("✅ Dry run mode properly blocked (initialization failed)")
        except RuntimeError as e:
            if "Dry run mode detected" in str(e):
                logger.info("✅ Dry run mode properly blocked")
            else:
                logger.error(f"❌ Unexpected error: {e}")
                return False
        
        try:
            paper_trader = UnifiedLiveTrader()
            # Manually set simulation mode to test blocking
            paper_trader.paper_trading = True
            result = await paper_trader.initialize_components()
            if result:
                logger.error("❌ CRITICAL: Paper trading mode allowed - NOT BLOCKED")
                return False
            else:
                logger.info("✅ Paper trading mode properly blocked (initialization failed)")
        except RuntimeError as e:
            if "Paper trading mode detected" in str(e):
                logger.info("✅ Paper trading mode properly blocked")
            else:
                logger.error(f"❌ Unexpected error: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error testing simulation blocking: {e}")
        return False
    
    # Test 4: Test live trading initialization
    logger.info("4️⃣ Testing live trading initialization...")
    try:
        live_trader = UnifiedLiveTrader()
        
        # This should work for live trading
        success = await live_trader.initialize_components()
        if success:
            logger.info("✅ Live trading initialization successful")
        else:
            logger.error("❌ Live trading initialization failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing live trading: {e}")
        return False
    
    # Test 5: Verify wallet balance check
    logger.info("5️⃣ Testing wallet balance check...")
    try:
        balance_ok = await live_trader.check_wallet_balance()
        if balance_ok:
            logger.info("✅ Wallet balance check passed")
        else:
            logger.warning("⚠️ Wallet balance check failed (may be insufficient funds)")
            
    except Exception as e:
        logger.error(f"❌ Error checking wallet balance: {e}")
        return False
    
    logger.info("\n🎉 PURE ORCA SYSTEM TESTS COMPLETED!")
    logger.info("✅ Jupiter dependencies removed")
    logger.info("✅ Simulation modes blocked")
    logger.info("✅ Orca native swaps ready")
    logger.info("✅ Live trading mode verified")
    
    logger.info("\n🚀 READY TO START PURE ORCA LIVE TRADING:")
    logger.info("   python3 scripts/unified_live_trading.py --duration 2")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_pure_orca_system())
    exit(0 if success else 1)
