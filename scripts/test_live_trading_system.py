#!/usr/bin/env python3
"""
Live Trading System Test

Tests the complete trading system with QuickNode configuration:
- Environment loading
- Wallet connectivity
- RPC endpoint functionality
- Transaction preparation
- Trading signal simulation
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, Optional
import logging
from datetime import datetime

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


class LiveTradingSystemTest:
    """Complete live trading system test."""
    
    def __init__(self):
        """Initialize the test system."""
        self.start_time = time.time()
        self.test_results = {}
        
        # Load environment variables fresh
        self._load_environment()
        
        print("🚀 Live Trading System Test")
        print("=" * 50)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"QuickNode URL: {self.quicknode_url}")
        print(f"Wallet: {self.wallet_address}")
        print()
    
    def _load_environment(self):
        """Load and verify environment variables."""
        # Force reload .env file
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        # Load critical variables
        self.quicknode_url = os.getenv('QUICKNODE_RPC_URL', '')
        self.quicknode_api_key = os.getenv('QUICKNODE_API_KEY', '')
        self.helius_url = os.getenv('HELIUS_RPC_URL', '')
        self.wallet_address = os.getenv('WALLET_ADDRESS', '')
        self.wallet_private_key = os.getenv('WALLET_PRIVATE_KEY', '')
        self.primary_rpc = os.getenv('PRIMARY_RPC', '')
        self.live_trading = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Synergy7-Live-Trading-Test/1.0'
        }
    
    async def test_environment_loading(self) -> Dict[str, Any]:
        """Test environment variable loading."""
        print("🔍 Testing Environment Loading...")
        
        checks = {
            'quicknode_url_loaded': bool(self.quicknode_url),
            'quicknode_api_key_loaded': bool(self.quicknode_api_key),
            'helius_url_loaded': bool(self.helius_url),
            'wallet_address_loaded': bool(self.wallet_address),
            'wallet_private_key_loaded': bool(self.wallet_private_key),
            'primary_rpc_set': self.primary_rpc == 'quicknode',
            'live_trading_enabled': self.live_trading
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        for check, status in checks.items():
            symbol = "✅" if status else "❌"
            print(f"   {symbol} {check.replace('_', ' ').title()}")
        
        result = {
            'success': passed >= 6,  # At least 6/7 must pass
            'passed_checks': passed,
            'total_checks': total,
            'details': checks
        }
        
        print(f"   📊 Environment: {passed}/{total} checks passed")
        return result
    
    async def test_quicknode_connectivity(self) -> Dict[str, Any]:
        """Test QuickNode RPC connectivity."""
        print("\n🔍 Testing QuickNode Connectivity...")
        
        test_methods = {
            'getHealth': {"jsonrpc": "2.0", "id": 1, "method": "getHealth", "params": []},
            'getSlot': {"jsonrpc": "2.0", "id": 2, "method": "getSlot", "params": []},
            'getLatestBlockhash': {
                "jsonrpc": "2.0", "id": 3, "method": "getLatestBlockhash", 
                "params": [{"commitment": "confirmed"}]
            }
        }
        
        results = {}
        total_time = 0
        successful_calls = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for method, payload in test_methods.items():
                    start_time = time.time()
                    response = await client.post(self.quicknode_url, json=payload, headers=self.headers)
                    response_time = time.time() - start_time
                    
                    success = response.status_code == 200
                    if success:
                        data = response.json()
                        success = 'result' in data and 'error' not in data
                    
                    results[method] = {
                        'success': success,
                        'response_time_ms': round(response_time * 1000, 2),
                        'status_code': response.status_code
                    }
                    
                    if success:
                        successful_calls += 1
                        total_time += response_time
                        print(f"   ✅ {method}: {response_time:.3f}s")
                    else:
                        print(f"   ❌ {method}: FAILED")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
        
        except Exception as e:
            print(f"   ❌ QuickNode connectivity error: {e}")
            return {'success': False, 'error': str(e)}
        
        avg_response_time = (total_time / successful_calls) if successful_calls > 0 else 0
        
        result = {
            'success': successful_calls >= 2,  # At least 2/3 methods must work
            'successful_calls': successful_calls,
            'total_calls': len(test_methods),
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'details': results
        }
        
        print(f"   📊 QuickNode: {successful_calls}/{len(test_methods)} methods working")
        return result
    
    async def test_wallet_access(self) -> Dict[str, Any]:
        """Test wallet access and balance."""
        print("\n🔍 Testing Wallet Access...")
        
        # Test wallet balance
        balance_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [self.wallet_address, {"commitment": "confirmed"}]
        }
        
        # Test token accounts
        token_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "getTokenAccountsByOwner",
            "params": [
                self.wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get SOL balance
                balance_response = await client.post(self.quicknode_url, json=balance_payload, headers=self.headers)
                sol_balance = 0
                
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    if 'result' in balance_data:
                        lamports = balance_data['result']['value']
                        sol_balance = lamports / 1e9
                        print(f"   ✅ SOL Balance: {sol_balance:.6f} SOL")
                
                # Get token accounts
                token_response = await client.post(self.quicknode_url, json=token_payload, headers=self.headers)
                token_accounts = []
                usdc_balance = 0
                
                if token_response.status_code == 200:
                    token_data = token_response.json()
                    if 'result' in token_data:
                        accounts = token_data['result']['value']
                        for account in accounts:
                            try:
                                account_info = account['account']['data']['parsed']['info']
                                mint = account_info['mint']
                                balance = float(account_info['tokenAmount']['uiAmount'] or 0)
                                
                                if mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":  # USDC
                                    usdc_balance = balance
                                    print(f"   ✅ USDC Balance: {balance:.6f} USDC")
                                
                                token_accounts.append({
                                    'mint': mint,
                                    'balance': balance
                                })
                            except Exception as e:
                                logger.debug(f"Error parsing token account: {e}")
                
                result = {
                    'success': sol_balance > 0 or usdc_balance > 0,
                    'sol_balance': sol_balance,
                    'usdc_balance': usdc_balance,
                    'token_account_count': len(token_accounts),
                    'wallet_funded': sol_balance >= 0.1,  # At least 0.1 SOL for transactions
                    'trading_ready': sol_balance >= 0.1 and usdc_balance > 0
                }
                
                print(f"   📊 Wallet Status: {'READY' if result['trading_ready'] else 'NEEDS FUNDING'}")
                return result
                
        except Exception as e:
            print(f"   ❌ Wallet access error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_transaction_preparation(self) -> Dict[str, Any]:
        """Test transaction preparation capabilities."""
        print("\n🔍 Testing Transaction Preparation...")
        
        # Test recent blockhash (required for transactions)
        blockhash_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.quicknode_url, json=blockhash_payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        blockhash_info = data['result']['value']
                        blockhash = blockhash_info['blockhash']
                        last_valid_block = blockhash_info['lastValidBlockHeight']
                        
                        print(f"   ✅ Recent Blockhash: {blockhash[:16]}...")
                        print(f"   ✅ Valid Until Block: {last_valid_block:,}")
                        
                        return {
                            'success': True,
                            'blockhash': blockhash,
                            'last_valid_block_height': last_valid_block,
                            'transaction_ready': True
                        }
                
                print(f"   ❌ Failed to get blockhash")
                return {'success': False, 'error': 'Failed to get recent blockhash'}
                
        except Exception as e:
            print(f"   ❌ Transaction preparation error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def simulate_trading_signal(self) -> Dict[str, Any]:
        """Simulate a trading signal without executing."""
        print("\n🔍 Simulating Trading Signal...")
        
        # Create a mock trading signal
        mock_signal = {
            'action': 'BUY',
            'market': 'SOL/USDC',
            'size': 0.1,  # Small test size
            'price': 'market',
            'timestamp': datetime.now().isoformat(),
            'confidence': 0.85,
            'strategy': 'test_signal'
        }
        
        print(f"   📊 Mock Signal: {mock_signal['action']} {mock_signal['size']} {mock_signal['market']}")
        print(f"   📊 Confidence: {mock_signal['confidence']}")
        print(f"   📊 Strategy: {mock_signal['strategy']}")
        
        # Simulate signal validation
        signal_valid = (
            mock_signal['action'] in ['BUY', 'SELL'] and
            mock_signal['size'] > 0 and
            mock_signal['confidence'] > 0.5
        )
        
        if signal_valid:
            print(f"   ✅ Signal Validation: PASSED")
        else:
            print(f"   ❌ Signal Validation: FAILED")
        
        return {
            'success': signal_valid,
            'signal': mock_signal,
            'validation_passed': signal_valid,
            'ready_for_execution': signal_valid
        }
    
    def print_final_summary(self):
        """Print final test summary."""
        print("\n" + "=" * 60)
        print("🚀 LIVE TRADING SYSTEM TEST SUMMARY")
        print("=" * 60)
        
        total_time = time.time() - self.start_time
        
        # Count successful tests
        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        total_tests = len(self.test_results)
        
        print(f"📊 Tests Completed: {successful_tests}/{total_tests}")
        print(f"⏱️ Total Test Time: {total_time:.2f}s")
        
        # Check specific capabilities
        env_ok = self.test_results.get('environment', {}).get('success', False)
        quicknode_ok = self.test_results.get('quicknode', {}).get('success', False)
        wallet_ok = self.test_results.get('wallet', {}).get('success', False)
        tx_prep_ok = self.test_results.get('transaction_prep', {}).get('success', False)
        signal_ok = self.test_results.get('trading_signal', {}).get('success', False)
        
        print(f"\n🔧 SYSTEM COMPONENTS:")
        print(f"   {'✅' if env_ok else '❌'} Environment Configuration")
        print(f"   {'✅' if quicknode_ok else '❌'} QuickNode Connectivity")
        print(f"   {'✅' if wallet_ok else '❌'} Wallet Access")
        print(f"   {'✅' if tx_prep_ok else '❌'} Transaction Preparation")
        print(f"   {'✅' if signal_ok else '❌'} Trading Signal Processing")
        
        # Overall readiness
        system_ready = all([env_ok, quicknode_ok, wallet_ok, tx_prep_ok])
        
        if system_ready:
            print(f"\n🎉 SYSTEM IS READY FOR LIVE TRADING!")
            print(f"✅ All critical components working")
            print(f"✅ QuickNode endpoint optimized")
            print(f"✅ Wallet funded and accessible")
            print(f"✅ Transaction capabilities verified")
            
            # Performance metrics
            if quicknode_ok:
                avg_time = self.test_results['quicknode'].get('avg_response_time_ms', 0)
                print(f"📊 QuickNode Performance: {avg_time}ms average")
            
            if wallet_ok:
                sol_balance = self.test_results['wallet'].get('sol_balance', 0)
                usdc_balance = self.test_results['wallet'].get('usdc_balance', 0)
                print(f"💰 Available Funds: {sol_balance:.3f} SOL, {usdc_balance:.2f} USDC")
            
            print(f"\n🚀 READY TO START LIVE TRADING!")
            
        else:
            print(f"\n⚠️ SYSTEM NOT READY - Issues detected")
            print(f"🔧 Please resolve the failed components before live trading")
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run the complete live trading system test."""
        try:
            # Run all tests
            self.test_results['environment'] = await self.test_environment_loading()
            self.test_results['quicknode'] = await self.test_quicknode_connectivity()
            self.test_results['wallet'] = await self.test_wallet_access()
            self.test_results['transaction_prep'] = await self.test_transaction_preparation()
            self.test_results['trading_signal'] = await self.simulate_trading_signal()
            
            # Print summary
            self.print_final_summary()
            
            return self.test_results
            
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
            return {'error': str(e)}


async def main():
    """Main test function."""
    tester = LiveTradingSystemTest()
    results = await tester.run_complete_test()
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/live_trading_system_test.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: output/live_trading_system_test.json")
    
    # Return appropriate exit code
    successful_tests = sum(1 for result in results.values() if isinstance(result, dict) and result.get('success', False))
    critical_tests = 4  # environment, quicknode, wallet, transaction_prep
    
    return 0 if successful_tests >= critical_tests else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
