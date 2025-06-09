#!/usr/bin/env python3
"""
Debug Live Trading System - No Simulations
==========================================

Clean live trading system with comprehensive debugging and no fallback simulations.
Designed for Winsor Williams II hedge fund operations.
"""

import asyncio
import logging
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure enhanced logging
def setup_debug_logging():
    """Setup comprehensive debug logging."""
    try:
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create debug log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_log_file = logs_dir / f'debug_live_trading_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.DEBUG,  # Enhanced debug level
            format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            handlers=[
                logging.FileHandler(debug_log_file),
                logging.StreamHandler()
            ]
        )
        print(f"📝 Debug logging enabled: {debug_log_file}")
    except Exception as e:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        print(f"⚠️ Console-only logging: {e}")

setup_debug_logging()
logger = logging.getLogger(__name__)

class DebugLiveTrader:
    """Debug-enabled live trading system with no simulation fallbacks."""
    
    def __init__(self):
        """Initialize debug live trader."""
        logger.info("🚀 WINSOR WILLIAMS II - DEBUG LIVE TRADING SYSTEM")
        logger.info("🛡️ MEV-Protected • No Simulations • Full Debugging")
        
        # Environment variables
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.wallet_private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.quicknode_url = os.getenv('QUICKNODE_RPC_URL')
        self.jito_url = os.getenv('JITO_RPC_URL')
        
        # Trading configuration - LIVE ONLY
        self.dry_run = False
        self.paper_trading = False
        self.simulation_mode = False
        self.live_trading = True
        
        # Debug flags
        self.debug_transactions = True
        self.debug_signals = True
        self.debug_execution = True
        self.debug_rpc_calls = True
        
        # Components
        self.keypair = None
        self.unified_tx_builder = None
        self.executor = None
        self.telegram_notifier = None
        
        # Session tracking
        self.session_start_time = datetime.now()
        self.session_trades = 0
        self.session_start_balance = None
        
        logger.info(f"📍 Wallet: {self.wallet_address}")
        logger.info(f"🔧 Debug Mode: FULL")
        logger.info(f"⚡ Live Trading: {self.live_trading}")
        logger.info(f"🚫 No Simulations: True")
        
    async def validate_configuration(self):
        """Validate all configuration with detailed debugging."""
        logger.info("🔍 CONFIGURATION VALIDATION")
        logger.info("=" * 50)
        
        errors = []
        
        # Check wallet configuration
        if not self.wallet_address:
            errors.append("WALLET_ADDRESS not configured")
        else:
            logger.info(f"✅ Wallet Address: {self.wallet_address}")
            
        if not self.wallet_private_key:
            errors.append("WALLET_PRIVATE_KEY not configured")
        else:
            logger.info(f"✅ Private Key: {'*' * 20}...{self.wallet_private_key[-10:]}")
            
        # Check RPC endpoints
        if not self.helius_api_key:
            errors.append("HELIUS_API_KEY not configured")
        else:
            logger.info(f"✅ Helius API Key: {'*' * 20}...{self.helius_api_key[-10:]}")
            
        if not self.quicknode_url:
            errors.append("QUICKNODE_RPC_URL not configured")
        else:
            logger.info(f"✅ QuickNode URL: {self.quicknode_url[:50]}...")
            
        if not self.jito_url:
            errors.append("JITO_RPC_URL not configured")
        else:
            logger.info(f"✅ Jito URL: {self.jito_url}")
            
        # Check Jupiter configuration
        jupiter_quote = os.getenv('JUPITER_QUOTE_ENDPOINT')
        jupiter_swap = os.getenv('JUPITER_SWAP_ENDPOINT')
        jupiter_slippage = os.getenv('JUPITER_SLIPPAGE_BPS')
        jupiter_shared_accounts = os.getenv('JUPITER_USE_SHARED_ACCOUNTS')
        
        logger.info(f"✅ Jupiter Quote: {jupiter_quote}")
        logger.info(f"✅ Jupiter Swap: {jupiter_swap}")
        logger.info(f"✅ Jupiter Slippage: {jupiter_slippage} BPS")
        logger.info(f"✅ Jupiter Shared Accounts: {jupiter_shared_accounts}")
        
        if errors:
            logger.error("❌ CONFIGURATION ERRORS:")
            for error in errors:
                logger.error(f"   - {error}")
            return False
            
        logger.info("✅ CONFIGURATION VALIDATION PASSED")
        return True
        
    async def initialize_components(self):
        """Initialize all components with detailed debugging."""
        logger.info("🔧 COMPONENT INITIALIZATION")
        logger.info("=" * 50)
        
        try:
            # Initialize keypair
            logger.info("1️⃣ Initializing keypair...")
            from solders.keypair import Keypair
            import base58
            
            private_key_bytes = base58.b58decode(self.wallet_private_key)
            self.keypair = Keypair.from_bytes(private_key_bytes)
            logger.info(f"✅ Keypair initialized: {self.keypair.pubkey()}")
            
            # Initialize unified transaction builder
            logger.info("2️⃣ Initializing unified transaction builder...")
            from core.dex.unified_transaction_builder import UnifiedTransactionBuilder
            
            self.unified_tx_builder = UnifiedTransactionBuilder(
                wallet_address=self.wallet_address,
                keypair=self.keypair
            )
            await self.unified_tx_builder.initialize()
            logger.info("✅ Unified transaction builder initialized")
            
            # Initialize modern executor
            logger.info("3️⃣ Initializing modern transaction executor...")
            from phase_4_deployment.rpc_execution.modern_transaction_executor import ModernTransactionExecutor
            
            self.executor = ModernTransactionExecutor(
                config={
                    'primary_rpc': os.getenv('QUICKNODE_RPC_URL'),
                    'fallback_rpc': None,  # No fallback RPC - QuickNode only
                    'jito_rpc': self.jito_url,
                    'helius_api_key': None,  # Removed Helius
                    'quicknode_api_key': os.getenv('QUICKNODE_API_KEY'),
                    'timeout': 15.0,
                    'max_retries': 2,
                    'debug_mode': True  # Enable debug mode
                }
            )
            await self.executor.initialize()
            logger.info("✅ Modern transaction executor initialized")
            
            # Initialize telegram notifier
            logger.info("4️⃣ Initializing telegram notifier...")
            try:
                from core.notifications.telegram_notifier import TelegramNotifier
                self.telegram_notifier = TelegramNotifier()
                if self.telegram_notifier.enabled:
                    logger.info("✅ Telegram notifier initialized")
                else:
                    logger.warning("⚠️ Telegram notifier disabled")
            except Exception as e:
                logger.warning(f"⚠️ Telegram notifier error: {e}")
                self.telegram_notifier = None
                
            logger.info("✅ ALL COMPONENTS INITIALIZED")
            return True
            
        except Exception as e:
            logger.error(f"❌ Component initialization failed: {e}")
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
            return False
            
    async def get_wallet_balance(self):
        """Get wallet balance with debugging."""
        logger.debug("💰 Getting wallet balance...")
        
        try:
            from phase_4_deployment.rpc_execution.helius_client import HeliusClient
            
            client = HeliusClient(api_key=self.helius_api_key)
            balance_data = await client.get_balance(self.wallet_address)
            
            if isinstance(balance_data, dict) and 'balance_sol' in balance_data:
                balance = balance_data['balance_sol']
                logger.debug(f"✅ Wallet balance: {balance:.9f} SOL")
                return balance
            else:
                logger.error(f"❌ Invalid balance response: {balance_data}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting wallet balance: {e}")
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
            return None
            
    async def generate_debug_signal(self):
        """Generate a debug trading signal."""
        logger.info("🎯 GENERATING DEBUG TRADING SIGNAL")
        logger.info("=" * 50)
        
        # Get current SOL price
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://quote-api.jup.ag/v6/quote",
                    params={
                        "inputMint": "So11111111111111111111111111111111111111112",
                        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                        "amount": "1000000000",  # 1 SOL
                        "slippageBps": "100"
                    }
                )
                
                if response.status_code == 200:
                    quote_data = response.json()
                    sol_price = float(quote_data['outAmount']) / 1_000_000  # USDC has 6 decimals
                    logger.info(f"📊 Current SOL Price: ${sol_price:.2f}")
                else:
                    sol_price = 152.0  # Fallback price
                    logger.warning(f"⚠️ Using fallback SOL price: ${sol_price}")
                    
        except Exception as e:
            sol_price = 152.0
            logger.warning(f"⚠️ Price fetch error, using fallback: {e}")
            
        # Create debug signal
        signal = {
            'action': 'BUY',
            'market': 'SOL-USDC',
            'size': 0.1,  # Small test amount
            'price': sol_price,
            'confidence': 0.9,
            'timestamp': datetime.now().isoformat(),
            'source': 'debug_signal',
            'strategy': 'debug_test',
            'debug_mode': True
        }
        
        logger.info(f"🎯 Debug Signal Generated:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Market: {signal['market']}")
        logger.info(f"   Size: {signal['size']} SOL")
        logger.info(f"   Price: ${signal['price']:.2f}")
        logger.info(f"   Confidence: {signal['confidence']}")
        
        return signal
        
    async def execute_debug_trade(self, signal):
        """Execute a debug trade with full logging."""
        logger.info("⚡ EXECUTING DEBUG TRADE")
        logger.info("=" * 50)
        
        try:
            # Get balance before
            balance_before = await self.get_wallet_balance()
            logger.info(f"💰 Balance before: {balance_before:.9f} SOL")
            
            # Build transaction
            logger.info("🔨 Building transaction...")
            transaction_result = await self.unified_tx_builder.build_swap_transaction(signal)

            if not transaction_result or not transaction_result.get('success'):
                logger.error("❌ Transaction building failed")
                return None

            logger.info("✅ Transaction built successfully")
            logger.debug(f"📄 Transaction result: {type(transaction_result)}")

            # Execute transaction
            logger.info("🚀 Executing transaction...")

            # Fix: Properly handle transaction serialization
            transaction = transaction_result.get('transaction')
            logger.debug(f"📄 Transaction type: {type(transaction)}")

            try:
                if hasattr(transaction, 'serialize'):
                    # Serialize VersionedTransaction to bytes
                    transaction_bytes = bytes(transaction.serialize())
                    logger.debug(f"✅ Serialized VersionedTransaction: {len(transaction_bytes)} bytes")
                elif isinstance(transaction, bytes):
                    transaction_bytes = transaction
                    logger.debug(f"✅ Transaction already bytes: {len(transaction_bytes)} bytes")
                else:
                    # Try to convert to bytes
                    transaction_bytes = bytes(transaction)
                    logger.debug(f"✅ Converted to bytes: {len(transaction_bytes)} bytes")

                # Execute with proper bytes - use the correct method
                execution_result = await self.executor._execute_regular_transaction(
                    transaction_bytes,
                    opts={'debug_mode': True}
                )

            except Exception as serialization_error:
                logger.error(f"❌ Transaction serialization error: {serialization_error}")
                logger.error(f"📄 Transaction object: {transaction}")
                if isinstance(transaction_result, dict):
                    logger.error(f"📄 Transaction result keys: {list(transaction_result.keys())}")
                return None
            
            if execution_result and execution_result.get('success'):
                signature = execution_result.get('signature', 'N/A')
                logger.info(f"✅ Transaction executed: {signature}")
                
                # Wait for confirmation
                await asyncio.sleep(5)
                
                # Get balance after
                balance_after = await self.get_wallet_balance()
                logger.info(f"💰 Balance after: {balance_after:.9f} SOL")
                
                # Calculate change
                if balance_before and balance_after:
                    balance_change = balance_after - balance_before
                    logger.info(f"📊 Balance change: {balance_change:.9f} SOL")
                    
                return execution_result
            else:
                logger.error(f"❌ Transaction execution failed: {execution_result}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Debug trade execution error: {e}")
            logger.error(f"📄 Traceback: {traceback.format_exc()}")
            return None
            
    async def run_debug_session(self, duration_minutes=5):
        """Run a debug trading session."""
        logger.info("🚀 STARTING DEBUG TRADING SESSION")
        logger.info("=" * 60)
        logger.info(f"👤 Owner: Winsor Williams II")
        logger.info(f"🏢 Type: Hedge Fund Debug Session")
        logger.info(f"⏰ Duration: {duration_minutes} minutes")
        logger.info(f"🛡️ MEV Protection: Active")
        logger.info("=" * 60)
        
        # Validate configuration
        if not await self.validate_configuration():
            logger.error("❌ Configuration validation failed")
            return False
            
        # Initialize components
        if not await self.initialize_components():
            logger.error("❌ Component initialization failed")
            return False
            
        # Get initial balance
        self.session_start_balance = await self.get_wallet_balance()
        logger.info(f"💰 Session start balance: {self.session_start_balance:.9f} SOL")
        
        # Run trading cycles
        end_time = datetime.now().timestamp() + (duration_minutes * 60)
        cycle = 1
        
        while datetime.now().timestamp() < end_time:
            logger.info(f"🔄 CYCLE {cycle}")
            logger.info("-" * 30)
            
            try:
                # Generate signal
                signal = await self.generate_debug_signal()
                
                # Execute trade
                result = await self.execute_debug_trade(signal)
                
                if result:
                    self.session_trades += 1
                    logger.info(f"✅ Cycle {cycle} completed successfully")
                else:
                    logger.error(f"❌ Cycle {cycle} failed")
                    
                # Wait before next cycle
                await asyncio.sleep(30)  # 30 seconds between trades
                cycle += 1
                
            except Exception as e:
                logger.error(f"❌ Cycle {cycle} error: {e}")
                logger.error(f"📄 Traceback: {traceback.format_exc()}")
                await asyncio.sleep(10)
                
        # Session summary
        final_balance = await self.get_wallet_balance()
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        
        logger.info("🎯 DEBUG SESSION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"⏰ Duration: {session_duration:.1f} minutes")
        logger.info(f"📊 Trades executed: {self.session_trades}")
        logger.info(f"💰 Start balance: {self.session_start_balance:.9f} SOL")
        logger.info(f"💰 Final balance: {final_balance:.9f} SOL")
        
        if self.session_start_balance and final_balance:
            pnl = final_balance - self.session_start_balance
            logger.info(f"📈 Session P&L: {pnl:.9f} SOL")
            
        logger.info("=" * 60)
        return True

async def main():
    """Main debug trading function."""
    trader = DebugLiveTrader()
    
    try:
        # Run debug session
        success = await trader.run_debug_session(duration_minutes=10)
        
        if success:
            logger.info("🎉 Debug session completed successfully")
            return 0
        else:
            logger.error("❌ Debug session failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Debug session interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Debug session error: {e}")
        logger.error(f"📄 Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
