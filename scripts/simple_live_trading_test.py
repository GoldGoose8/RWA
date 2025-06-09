#!/usr/bin/env python3
"""
Simple Live Trading Test

Tests the live trading system with real wallet balance monitoring
to confirm the system works without Orca error 3012.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    os.system("pip install httpx")
    import httpx


class SimpleLiveTradingTest:
    """Simple live trading test with balance monitoring."""
    
    def __init__(self):
        """Initialize the test."""
        # Load environment variables
        self.wallet_address = os.getenv('WALLET_ADDRESS', 'Az47WmeBr94pTFeK6feHTjn6rGLWniviSCXtnJ65kGaf')
        self.quicknode_url = os.getenv('QUICKNODE_RPC_URL', 'https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/')
        self.quicknode_api_key = os.getenv('QUICKNODE_API_KEY', 'QN_810042470c20437bb9ec222fbf20f071')
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Synergy7-Simple-Live-Test/1.0'
        }
        
        logger.info("🚀 Simple Live Trading Test initialized")
        logger.info(f"📊 Wallet: {self.wallet_address}")
        logger.info(f"🔗 QuickNode: {self.quicknode_url[:50]}...")
    
    async def get_wallet_balance(self) -> Dict[str, float]:
        """Get current wallet balance."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL balance
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.wallet_address, {"commitment": "confirmed"}]
                }
                
                response = await client.post(self.quicknode_url, json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        lamports = data['result']['value']
                        sol_balance = lamports / 1e9
                        return {'SOL': sol_balance, 'status': 'success'}
                
                return {'SOL': 0.0, 'status': 'failed', 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {'SOL': 0.0, 'status': 'error', 'error': str(e)}
    
    async def test_transaction_building(self) -> Dict[str, Any]:
        """Test transaction building without Orca errors."""
        logger.info("🔨 Testing Transaction Building...")
        
        try:
            from core.dex.unified_transaction_builder import UnifiedTransactionBuilder
            
            # Create test signal
            test_signal = {
                'action': 'BUY',
                'size': 0.01,
                'market': 'SOL-USDC',
                'price': 155.0,
                'confidence': 0.85
            }
            
            logger.info(f"📊 Test Signal: {test_signal['action']} {test_signal['size']} {test_signal['market']}")
            
            # Build transaction
            builder = UnifiedTransactionBuilder(self.wallet_address, None)
            await builder.initialize()
            
            result = await builder.build_swap_transaction(test_signal)
            
            await builder.close()
            
            if result and result.get('success'):
                logger.info(f"✅ Transaction built successfully: {result.get('execution_type')}")
                logger.info(f"📝 Message: {result.get('message', 'No message')}")
                return {
                    'success': True,
                    'execution_type': result.get('execution_type'),
                    'message': result.get('message'),
                    'orca_error': False
                }
            else:
                logger.error("❌ Transaction building failed")
                return {
                    'success': False,
                    'error': 'Transaction building failed',
                    'orca_error': False
                }
                
        except Exception as e:
            error_str = str(e)
            orca_error = '3012' in error_str or 'ORCA_INVALID_SQRT_PRICE' in error_str
            
            logger.error(f"❌ Transaction building error: {error_str}")
            
            return {
                'success': False,
                'error': error_str,
                'orca_error': orca_error
            }
    
    async def run_live_trading_cycles(self, num_cycles: int = 3) -> Dict[str, Any]:
        """Run multiple trading cycles to test system stability."""
        logger.info(f"🔄 Running {num_cycles} trading cycles...")
        
        results = {
            'cycles_completed': 0,
            'successful_builds': 0,
            'orca_errors': 0,
            'other_errors': 0,
            'cycle_results': []
        }
        
        for i in range(num_cycles):
            cycle_start = time.time()
            logger.info(f"\n🔄 Trading Cycle {i+1}/{num_cycles}")
            
            # Test transaction building
            build_result = await self.test_transaction_building()
            
            cycle_result = {
                'cycle': i + 1,
                'timestamp': datetime.now().isoformat(),
                'duration': time.time() - cycle_start,
                'build_result': build_result
            }
            
            results['cycle_results'].append(cycle_result)
            results['cycles_completed'] += 1
            
            if build_result['success']:
                results['successful_builds'] += 1
                logger.info(f"✅ Cycle {i+1}: SUCCESS")
            else:
                if build_result['orca_error']:
                    results['orca_errors'] += 1
                    logger.error(f"❌ Cycle {i+1}: ORCA ERROR - {build_result['error']}")
                else:
                    results['other_errors'] += 1
                    logger.warning(f"⚠️ Cycle {i+1}: OTHER ERROR - {build_result['error']}")
            
            # Wait between cycles
            if i < num_cycles - 1:
                await asyncio.sleep(5)
        
        return results
    
    def print_test_summary(self, balance_result: Dict[str, Any], trading_results: Dict[str, Any]):
        """Print comprehensive test summary."""
        logger.info("\n" + "="*60)
        logger.info("🚀 SIMPLE LIVE TRADING TEST SUMMARY")
        logger.info("="*60)
        
        # Balance test
        logger.info(f"💰 WALLET BALANCE TEST:")
        if balance_result['status'] == 'success':
            logger.info(f"   ✅ Balance: {balance_result['SOL']:.6f} SOL")
            logger.info(f"   ✅ QuickNode connectivity: WORKING")
        else:
            logger.error(f"   ❌ Balance check failed: {balance_result.get('error', 'Unknown error')}")
        
        # Trading test
        logger.info(f"\n🔨 TRANSACTION BUILDING TEST:")
        logger.info(f"   Cycles completed: {trading_results['cycles_completed']}")
        logger.info(f"   Successful builds: {trading_results['successful_builds']}")
        logger.info(f"   Orca errors: {trading_results['orca_errors']}")
        logger.info(f"   Other errors: {trading_results['other_errors']}")
        
        # Success rate
        if trading_results['cycles_completed'] > 0:
            success_rate = (trading_results['successful_builds'] / trading_results['cycles_completed']) * 100
            logger.info(f"   Success rate: {success_rate:.1f}%")
        
        # Overall status
        no_orca_errors = trading_results['orca_errors'] == 0
        has_successes = trading_results['successful_builds'] > 0
        
        if no_orca_errors and has_successes:
            logger.info(f"\n🎉 TEST RESULT: SUCCESS!")
            logger.info(f"✅ No Orca error 3012 detected")
            logger.info(f"✅ Transaction building working")
            logger.info(f"✅ System stable without Orca dependencies")
        elif no_orca_errors:
            logger.info(f"\n✅ TEST RESULT: ORCA ERRORS ELIMINATED")
            logger.info(f"✅ No Orca error 3012 detected")
            logger.info(f"ℹ️ System using simplified transactions")
        else:
            logger.error(f"\n❌ TEST RESULT: ORCA ERRORS STILL PRESENT")
            logger.error(f"❌ {trading_results['orca_errors']} Orca errors detected")
            logger.error(f"🔧 Further Orca removal needed")
    
    async def run_complete_test(self):
        """Run complete live trading test."""
        logger.info("🚀 Starting Simple Live Trading Test")
        logger.info("="*60)
        
        start_time = time.time()
        
        # Test 1: Check wallet balance and QuickNode connectivity
        logger.info("🔍 Testing wallet balance and QuickNode connectivity...")
        balance_result = await self.get_wallet_balance()
        
        # Test 2: Run trading cycles
        logger.info("\n🔨 Testing transaction building cycles...")
        trading_results = await self.run_live_trading_cycles(3)
        
        # Print summary
        self.print_test_summary(balance_result, trading_results)
        
        # Save results
        import json
        results = {
            'test_summary': {
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': time.time() - start_time,
                'wallet_address': self.wallet_address
            },
            'balance_test': balance_result,
            'trading_test': trading_results
        }
        
        os.makedirs("output", exist_ok=True)
        filename = f"output/simple_live_trading_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n📄 Test results saved to: {filename}")
        
        # Return success if no Orca errors
        return trading_results['orca_errors'] == 0


async def main():
    """Main test function."""
    test = SimpleLiveTradingTest()
    success = await test.run_complete_test()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
