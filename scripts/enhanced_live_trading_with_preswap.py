#!/usr/bin/env python3
"""
Enhanced Live Trading System with Pre-Trade Balance Verification
===============================================================

This system automatically verifies and prepares the correct token balances
before executing any trade, ensuring smooth execution.
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/enhanced_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PreTradeBalanceManager:
    """Manages token balances before trade execution."""
    
    def __init__(self, wallet_address, private_key):
        self.wallet_address = wallet_address
        self.private_key = private_key
        self.sol_price = 151.0  # Will be updated dynamically
        
    async def get_token_balances(self):
        """Get current SOL and USDC balances."""
        try:
            from solders.pubkey import Pubkey
            from solana.rpc.api import Client
            
            # Get RPC client
            rpc_url = os.getenv('HELIUS_RPC_URL', 'https://api.mainnet-beta.solana.com')
            client = Client(rpc_url)
            
            # Get SOL balance
            pubkey = Pubkey.from_string(self.wallet_address)
            sol_response = client.get_balance(pubkey)
            sol_balance = sol_response.value / 1_000_000_000
            
            # Get USDC balance
            usdc_account = os.getenv('WALLET_USDC_ACCOUNT')
            usdc_balance = 0.0
            
            if usdc_account:
                try:
                    usdc_pubkey = Pubkey.from_string(usdc_account)
                    usdc_response = client.get_token_account_balance(usdc_pubkey)
                    if usdc_response.value:
                        usdc_raw = int(usdc_response.value.amount)
                        usdc_decimals = usdc_response.value.decimals
                        usdc_balance = usdc_raw / (10 ** usdc_decimals)
                except Exception as e:
                    logger.warning(f"Could not get USDC balance: {e}")
            
            return {
                'sol': sol_balance,
                'usdc': usdc_balance,
                'total_usd_value': (sol_balance * self.sol_price) + usdc_balance
            }
            
        except Exception as e:
            logger.error(f"Error getting token balances: {e}")
            return {'sol': 0, 'usdc': 0, 'total_usd_value': 0}
    
    async def prepare_trade_balance(self, trade_action, trade_amount_sol, trade_amount_usd):
        """Prepare the correct token balance for the trade."""
        logger.info(f"🔧 PREPARING BALANCE for {trade_action} trade")
        logger.info(f"   Trade Amount: {trade_amount_sol:.6f} SOL (${trade_amount_usd:.2f})")
        
        # Get current balances
        balances = await self.get_token_balances()
        logger.info(f"   Current SOL: {balances['sol']:.6f}")
        logger.info(f"   Current USDC: {balances['usdc']:.6f}")
        
        if trade_action == "BUY":
            # Need USDC to buy SOL
            required_usdc = trade_amount_usd * 1.02  # Add 2% buffer for slippage
            
            if balances['usdc'] < required_usdc:
                # Need to convert SOL to USDC
                usdc_needed = required_usdc - balances['usdc']
                sol_to_convert = (usdc_needed / self.sol_price) * 1.05  # Add 5% buffer
                
                logger.info(f"🔄 INSUFFICIENT USDC: Need {required_usdc:.2f}, have {balances['usdc']:.2f}")
                logger.info(f"🔄 Converting {sol_to_convert:.6f} SOL to USDC...")
                
                # Execute SOL → USDC swap
                swap_success = await self.execute_preparation_swap("SOL_TO_USDC", sol_to_convert)
                if not swap_success:
                    logger.error("❌ Failed to prepare USDC balance")
                    return False
                    
        elif trade_action == "SELL":
            # Need SOL to sell for USDC
            required_sol = trade_amount_sol * 1.02  # Add 2% buffer
            
            if balances['sol'] < required_sol:
                # Need to convert USDC to SOL
                sol_needed = required_sol - balances['sol']
                usdc_to_convert = (sol_needed * self.sol_price) * 1.05  # Add 5% buffer
                
                logger.info(f"🔄 INSUFFICIENT SOL: Need {required_sol:.6f}, have {balances['sol']:.6f}")
                logger.info(f"🔄 Converting {usdc_to_convert:.2f} USDC to SOL...")
                
                # Execute USDC → SOL swap
                swap_success = await self.execute_preparation_swap("USDC_TO_SOL", usdc_to_convert)
                if not swap_success:
                    logger.error("❌ Failed to prepare SOL balance")
                    return False
        
        logger.info("✅ Balance preparation complete")
        return True
    
    async def execute_preparation_swap(self, swap_type, amount):
        """Execute a preparation swap to get the right token balance."""
        try:
            logger.info(f"🔄 Executing preparation swap: {swap_type} amount: {amount}")
            
            # Import the simple swap functionality
            from scripts.simple_usdc_to_sol_swap import execute_swap
            
            if swap_type == "SOL_TO_USDC":
                # Convert SOL to USDC
                result = await execute_swap(
                    amount_sol=amount,
                    direction="sol_to_usdc",
                    wallet_address=self.wallet_address,
                    private_key=self.private_key
                )
            elif swap_type == "USDC_TO_SOL":
                # Convert USDC to SOL
                result = await execute_swap(
                    amount_usdc=amount,
                    direction="usdc_to_sol", 
                    wallet_address=self.wallet_address,
                    private_key=self.private_key
                )
            
            if result and result.get('success'):
                logger.info(f"✅ Preparation swap successful: {result.get('signature', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Preparation swap failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in preparation swap: {e}")
            return False

class EnhancedLiveTrader:
    """Enhanced live trader with pre-trade balance management."""
    
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.balance_manager = PreTradeBalanceManager(self.wallet_address, self.private_key)
        self.session_start_time = datetime.now()
        self.trade_count = 0
        
    async def execute_enhanced_trade(self, signal):
        """Execute a trade with pre-trade balance verification."""
        self.trade_count += 1
        
        logger.info(f"🚀 ENHANCED TRADE #{self.trade_count}")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Amount: {signal['size']:.6f} SOL")
        logger.info(f"   Value: ${signal.get('position_info', {}).get('position_size_usd', 0):.2f}")
        
        # Step 1: Prepare the correct token balance
        trade_amount_sol = signal['size']
        trade_amount_usd = signal.get('position_info', {}).get('position_size_usd', 0)
        
        balance_ready = await self.balance_manager.prepare_trade_balance(
            signal['action'], 
            trade_amount_sol, 
            trade_amount_usd
        )
        
        if not balance_ready:
            logger.error("❌ Could not prepare balance for trade")
            return {'success': False, 'error': 'Balance preparation failed'}
        
        # Step 2: Wait a moment for balance to settle
        logger.info("⏳ Waiting for balance to settle...")
        await asyncio.sleep(3)
        
        # Step 3: Execute the actual trade
        logger.info("🚀 Executing main trade...")
        
        try:
            # Import and use the existing trading system
            from scripts.unified_live_trading import execute_trade_with_unified_builder
            
            result = await execute_trade_with_unified_builder(signal)
            
            if result and result.get('success'):
                logger.info(f"✅ Enhanced trade successful!")
                logger.info(f"   Signature: {result.get('signature', 'N/A')}")
                return result
            else:
                logger.error(f"❌ Enhanced trade failed: {result}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error executing enhanced trade: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_enhanced_trading_session(self, duration_minutes=30):
        """Run an enhanced trading session with balance management."""
        logger.info("🚀 STARTING ENHANCED LIVE TRADING WITH BALANCE MANAGEMENT")
        logger.info("=" * 70)
        logger.info(f"⏰ Session Duration: {duration_minutes} minutes")
        logger.info(f"💰 Wallet: {self.wallet_address}")
        
        # Get initial balances
        initial_balances = await self.balance_manager.get_token_balances()
        logger.info(f"💰 Initial SOL: {initial_balances['sol']:.6f}")
        logger.info(f"💰 Initial USDC: {initial_balances['usdc']:.6f}")
        logger.info(f"💰 Total Value: ${initial_balances['total_usd_value']:.2f}")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        try:
            # Import the signal generation from existing system
            from scripts.unified_live_trading import generate_trading_signal
            
            cycle = 0
            while datetime.now() < end_time:
                cycle += 1
                logger.info(f"🔄 Enhanced Trading Cycle #{cycle}")
                
                # Generate trading signal
                signal = await generate_trading_signal()
                
                if signal and signal.get('confidence', 0) > 0.6:
                    # Execute enhanced trade with balance management
                    result = await self.execute_enhanced_trade(signal)
                    
                    if result and result.get('success'):
                        logger.info(f"✅ Cycle #{cycle} trade successful")
                    else:
                        logger.warning(f"⚠️ Cycle #{cycle} trade failed")
                else:
                    logger.info(f"📊 Cycle #{cycle}: No strong signal (confidence: {signal.get('confidence', 0) if signal else 0:.3f})")
                
                # Wait before next cycle
                await asyncio.sleep(30)  # 30 second cycles
        
        except KeyboardInterrupt:
            logger.info("🛑 Trading session interrupted by user")
        except Exception as e:
            logger.error(f"❌ Trading session error: {e}")
        
        # Final balances
        final_balances = await self.balance_manager.get_token_balances()
        logger.info("📊 ENHANCED TRADING SESSION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"💰 Final SOL: {final_balances['sol']:.6f}")
        logger.info(f"💰 Final USDC: {final_balances['usdc']:.6f}")
        logger.info(f"💰 Final Value: ${final_balances['total_usd_value']:.2f}")
        logger.info(f"📈 Value Change: ${final_balances['total_usd_value'] - initial_balances['total_usd_value']:.2f}")
        logger.info(f"🔢 Total Trades: {self.trade_count}")

async def main():
    """Main function."""
    trader = EnhancedLiveTrader()
    await trader.run_enhanced_trading_session(duration_minutes=30)

if __name__ == "__main__":
    asyncio.run(main())
