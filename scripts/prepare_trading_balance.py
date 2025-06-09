#!/usr/bin/env python3
"""
Trading Balance Preparation Utility
===================================

Prepares the wallet with the correct token balances for trading.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_current_balances():
    """Get current SOL and USDC balances."""
    try:
        # Use existing HeliusClient instead of direct solana.rpc.api.Client
        from phase_4_deployment.rpc_execution.helius_client import HeliusClient

        wallet_address = os.getenv('WALLET_ADDRESS')
        usdc_account = os.getenv('WALLET_USDC_ACCOUNT')
        helius_api_key = os.getenv('HELIUS_API_KEY')

        client = HeliusClient(api_key=helius_api_key)

        # Get SOL balance
        balance_data = await client.get_balance(wallet_address)
        if isinstance(balance_data, dict) and 'balance_sol' in balance_data:
            sol_balance = balance_data['balance_sol']
        else:
            logger.warning(f"⚠️ Could not get SOL balance: {balance_data}")
            sol_balance = 0.0

        # Get USDC balance
        usdc_balance = 0.0
        if usdc_account:
            try:
                usdc_data = await client.get_token_account_balance(usdc_account)
                if usdc_data and 'balance' in usdc_data:
                    usdc_balance = float(usdc_data['balance'])
            except Exception as e:
                logger.warning(f"Could not get USDC balance: {e}")

        # Close the client
        await client.close()

        return sol_balance, usdc_balance

    except Exception as e:
        logger.error(f"Error getting balances: {e}")
        return 0, 0

async def prepare_balanced_portfolio(target_usdc_percentage=50):
    """Prepare a balanced portfolio with specified USDC percentage."""
    logger.info("🔧 PREPARING BALANCED TRADING PORTFOLIO")
    logger.info("=" * 50)
    
    # Get current balances
    sol_balance, usdc_balance = await get_current_balances()
    
    # Get current SOL price (approximate)
    sol_price = 151.0  # You can make this dynamic
    
    # Calculate current portfolio value
    sol_value_usd = sol_balance * sol_price
    total_value_usd = sol_value_usd + usdc_balance
    current_usdc_percentage = (usdc_balance / total_value_usd * 100) if total_value_usd > 0 else 0
    
    logger.info(f"💰 Current Portfolio:")
    logger.info(f"   SOL: {sol_balance:.6f} (${sol_value_usd:.2f})")
    logger.info(f"   USDC: {usdc_balance:.6f} (${usdc_balance:.2f})")
    logger.info(f"   Total: ${total_value_usd:.2f}")
    logger.info(f"   USDC %: {current_usdc_percentage:.1f}%")
    logger.info()
    
    # Calculate target balances
    target_usdc_value = total_value_usd * (target_usdc_percentage / 100)
    target_sol_value = total_value_usd * ((100 - target_usdc_percentage) / 100)
    target_sol_amount = target_sol_value / sol_price
    
    logger.info(f"🎯 Target Portfolio ({target_usdc_percentage}% USDC):")
    logger.info(f"   SOL: {target_sol_amount:.6f} (${target_sol_value:.2f})")
    logger.info(f"   USDC: {target_usdc_value:.6f} (${target_usdc_value:.2f})")
    logger.info()
    
    # Determine what swap is needed
    usdc_difference = target_usdc_value - usdc_balance
    
    if abs(usdc_difference) < 10:  # Less than $10 difference
        logger.info("✅ Portfolio is already balanced (within $10)")
        return True
    
    if usdc_difference > 0:
        # Need more USDC, sell SOL
        sol_to_sell = usdc_difference / sol_price
        logger.info(f"🔄 REBALANCING: Selling {sol_to_sell:.6f} SOL for ${usdc_difference:.2f} USDC")
        
        # Execute SOL → USDC swap
        success = await execute_rebalance_swap("SOL_TO_USDC", sol_to_sell)
        
    else:
        # Need more SOL, sell USDC
        usdc_to_sell = abs(usdc_difference)
        logger.info(f"🔄 REBALANCING: Selling ${usdc_to_sell:.2f} USDC for SOL")
        
        # Execute USDC → SOL swap
        success = await execute_rebalance_swap("USDC_TO_SOL", usdc_to_sell)
    
    if success:
        logger.info("✅ Portfolio rebalancing complete!")
        
        # Show final balances
        final_sol, final_usdc = await get_current_balances()
        final_total = (final_sol * sol_price) + final_usdc
        final_usdc_pct = (final_usdc / final_total * 100) if final_total > 0 else 0
        
        logger.info(f"📊 Final Portfolio:")
        logger.info(f"   SOL: {final_sol:.6f} (${final_sol * sol_price:.2f})")
        logger.info(f"   USDC: {final_usdc:.6f} (${final_usdc:.2f})")
        logger.info(f"   USDC %: {final_usdc_pct:.1f}%")
        
        return True
    else:
        logger.error("❌ Portfolio rebalancing failed")
        return False

async def execute_rebalance_swap(swap_type, amount):
    """Execute a rebalancing swap."""
    try:
        logger.info(f"🔄 Executing {swap_type} swap for amount: {amount}")
        
        # Use the simple swap script
        if swap_type == "SOL_TO_USDC":
            # Convert SOL to USDC
            from scripts.simple_usdc_to_sol_swap import main as swap_main
            
            # Temporarily modify sys.argv to pass the reverse flag
            original_argv = sys.argv.copy()
            sys.argv = ['simple_usdc_to_sol_swap.py', '--reverse', '--amount', str(amount)]
            
            try:
                result = await swap_main()
                return result
            finally:
                sys.argv = original_argv
                
        elif swap_type == "USDC_TO_SOL":
            # Convert USDC to SOL
            from scripts.simple_usdc_to_sol_swap import main as swap_main
            
            # Temporarily modify sys.argv
            original_argv = sys.argv.copy()
            sys.argv = ['simple_usdc_to_sol_swap.py', '--amount', str(amount)]
            
            try:
                result = await swap_main()
                return result
            finally:
                sys.argv = original_argv
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error in rebalance swap: {e}")
        return False

async def quick_usdc_preparation(usdc_amount=500):
    """Quickly prepare a specific amount of USDC for trading."""
    logger.info(f"🔧 QUICK USDC PREPARATION: ${usdc_amount}")
    logger.info("=" * 50)
    
    sol_balance, usdc_balance = await get_current_balances()
    
    if usdc_balance >= usdc_amount:
        logger.info(f"✅ Already have sufficient USDC: ${usdc_balance:.2f}")
        return True
    
    usdc_needed = usdc_amount - usdc_balance
    sol_price = 151.0
    sol_to_convert = (usdc_needed / sol_price) * 1.05  # Add 5% buffer
    
    logger.info(f"💰 Current USDC: ${usdc_balance:.2f}")
    logger.info(f"💰 USDC Needed: ${usdc_needed:.2f}")
    logger.info(f"🔄 Converting {sol_to_convert:.6f} SOL to USDC...")
    
    success = await execute_rebalance_swap("SOL_TO_USDC", sol_to_convert)
    
    if success:
        logger.info("✅ USDC preparation complete!")
        return True
    else:
        logger.error("❌ USDC preparation failed")
        return False

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare trading balance')
    parser.add_argument('--balance', action='store_true', help='Create balanced 50/50 portfolio')
    parser.add_argument('--usdc', type=float, help='Prepare specific USDC amount')
    parser.add_argument('--percentage', type=int, default=50, help='Target USDC percentage (default: 50)')
    
    args = parser.parse_args()
    
    if args.usdc:
        await quick_usdc_preparation(args.usdc)
    elif args.balance:
        await prepare_balanced_portfolio(args.percentage)
    else:
        # Default: prepare $500 USDC for trading
        await quick_usdc_preparation(500)

if __name__ == "__main__":
    asyncio.run(main())
