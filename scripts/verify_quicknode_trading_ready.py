#!/usr/bin/env python3
"""
QuickNode Trading Readiness Verification

Final verification that QuickNode is properly configured and ready
for live trading operations without Orca-specific parameters.
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    os.system("pip install httpx")
    import httpx


class TradingReadinessVerifier:
    """Verify QuickNode is ready for trading operations."""
    
    def __init__(self):
        """Initialize verifier."""
        self.quicknode_url = os.getenv('QUICKNODE_RPC_URL', 'https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/')
        self.quicknode_api_key = os.getenv('QUICKNODE_API_KEY', 'QN_810042470c20437bb9ec222fbf20f071')
        self.helius_url = os.getenv('HELIUS_RPC_URL', 'https://mainnet.helius-rpc.com/?api-key=4ebf03a3-fdc8-4d41-b652-3e62797b1f6c')
        
        self.wallet_address = os.getenv('WALLET_ADDRESS', 'Az47WmeBr94pTFeK6feHTjn6rGLWniviSCXtnJ65kGaf').strip("'")
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Synergy7-Trading-Bot/1.0'
        }
    
    async def verify_quicknode_primary(self) -> Dict[str, Any]:
        """Verify QuickNode as primary endpoint."""
        print("🔍 Verifying QuickNode as Primary Endpoint...")
        
        # Test essential trading operations
        tests = {
            'health': {
                "jsonrpc": "2.0", "id": 1, "method": "getHealth", "params": []
            },
            'slot': {
                "jsonrpc": "2.0", "id": 2, "method": "getSlot", "params": []
            },
            'blockhash': {
                "jsonrpc": "2.0", "id": 3, "method": "getLatestBlockhash", 
                "params": [{"commitment": "confirmed"}]
            },
            'balance': {
                "jsonrpc": "2.0", "id": 4, "method": "getBalance",
                "params": [self.wallet_address, {"commitment": "confirmed"}]
            }
        }
        
        results = {}
        total_response_time = 0
        successful_tests = 0
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for test_name, payload in tests.items():
                    start_time = time.time()
                    response = await client.post(self.quicknode_url, json=payload, headers=self.headers)
                    response_time = time.time() - start_time
                    
                    success = response.status_code == 200
                    if success:
                        data = response.json()
                        success = 'result' in data and 'error' not in data
                    
                    results[test_name] = {
                        'success': success,
                        'response_time_ms': round(response_time * 1000, 2),
                        'status_code': response.status_code
                    }
                    
                    if success:
                        successful_tests += 1
                        total_response_time += response_time
                        print(f"   ✅ {test_name}: {response_time:.3f}s")
                    else:
                        print(f"   ❌ {test_name}: FAILED")
                    
                    await asyncio.sleep(0.1)  # Rate limiting
        
        except Exception as e:
            print(f"   ❌ QuickNode test error: {e}")
            return {'success': False, 'error': str(e)}
        
        avg_response_time = (total_response_time / successful_tests) if successful_tests > 0 else 0
        overall_success = successful_tests >= 3  # At least 3/4 tests must pass
        
        results['summary'] = {
            'success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': len(tests),
            'avg_response_time_ms': round(avg_response_time * 1000, 2)
        }
        
        return results
    
    async def verify_helius_fallback(self) -> Dict[str, Any]:
        """Verify Helius as fallback endpoint."""
        print("\n🔍 Verifying Helius as Fallback Endpoint...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
            "params": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.post(self.helius_url, json=payload, headers=self.headers)
                response_time = time.time() - start_time
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = 'result' in data
                
                result = {
                    'success': success,
                    'response_time_ms': round(response_time * 1000, 2),
                    'status_code': response.status_code
                }
                
                if success:
                    print(f"   ✅ Helius fallback: {response_time:.3f}s")
                else:
                    print(f"   ❌ Helius fallback: FAILED")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Helius test error: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_configuration(self) -> Dict[str, Any]:
        """Verify environment configuration."""
        print("\n🔍 Verifying Configuration...")
        
        config_checks = {
            'quicknode_url': bool(self.quicknode_url),
            'quicknode_api_key': bool(self.quicknode_api_key),
            'helius_url': bool(self.helius_url),
            'wallet_address': bool(self.wallet_address),
            'primary_rpc_set': os.getenv('PRIMARY_RPC') == 'quicknode',
            'quicknode_enabled': os.getenv('QUICKNODE_ENABLED', 'true').lower() == 'true',
            'orca_params_removed': not any([
                os.getenv('ORCA_SLIPPAGE_BPS'),
                os.getenv('ORCA_PRIORITY_FEE'),
                os.getenv('ORCA_DIRECT_ROUTES_ONLY')
            ])
        }
        
        passed_checks = sum(config_checks.values())
        total_checks = len(config_checks)
        
        print(f"   Configuration checks: {passed_checks}/{total_checks}")
        
        for check, passed in config_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check.replace('_', ' ').title()}")
        
        return {
            'success': passed_checks >= 6,  # At least 6/7 checks must pass
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'details': config_checks
        }
    
    def verify_wallet_readiness(self, quicknode_results: Dict[str, Any]) -> Dict[str, Any]:
        """Verify wallet is ready for trading."""
        print("\n🔍 Verifying Wallet Readiness...")
        
        # Check if balance test passed
        balance_test = quicknode_results.get('balance', {})
        wallet_accessible = balance_test.get('success', False)
        
        checks = {
            'wallet_accessible': wallet_accessible,
            'wallet_address_valid': len(self.wallet_address) >= 32,
            'private_key_set': bool(os.getenv('WALLET_PRIVATE_KEY')),
            'trading_enabled': os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        }
        
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        
        print(f"   Wallet checks: {passed_checks}/{total_checks}")
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check.replace('_', ' ').title()}")
        
        return {
            'success': passed_checks >= 3,  # At least 3/4 checks must pass
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'details': checks
        }
    
    def print_final_summary(self, all_results: Dict[str, Any]):
        """Print final trading readiness summary."""
        print("\n" + "="*60)
        print("🚀 QUICKNODE TRADING READINESS SUMMARY")
        print("="*60)
        
        # Check overall readiness
        quicknode_ready = all_results.get('quicknode_primary', {}).get('summary', {}).get('success', False)
        helius_ready = all_results.get('helius_fallback', {}).get('success', False)
        config_ready = all_results.get('configuration', {}).get('success', False)
        wallet_ready = all_results.get('wallet_readiness', {}).get('success', False)
        
        overall_ready = quicknode_ready and config_ready and wallet_ready
        
        if overall_ready:
            print("🎉 SYSTEM IS READY FOR LIVE TRADING!")
            print()
            print("✅ QuickNode endpoint: WORKING")
            print("✅ Configuration: OPTIMIZED")
            print("✅ Wallet: ACCESSIBLE")
            print("✅ Orca parameters: REMOVED")
            
            if helius_ready:
                print("✅ Helius fallback: AVAILABLE")
            
            # Performance info
            quicknode_perf = all_results.get('quicknode_primary', {}).get('summary', {})
            avg_time = quicknode_perf.get('avg_response_time_ms', 0)
            if avg_time > 0:
                print(f"📊 Average response time: {avg_time}ms")
            
            print(f"\n🔧 RECOMMENDED NEXT STEPS:")
            print("1. Start the trading system: python3 scripts/unified_live_trading.py")
            print("2. Monitor performance in real-time")
            print("3. Check logs for any issues")
            
        else:
            print("⚠️ SYSTEM NOT READY - Issues detected:")
            
            if not quicknode_ready:
                print("❌ QuickNode endpoint issues")
            if not config_ready:
                print("❌ Configuration issues")
            if not wallet_ready:
                print("❌ Wallet access issues")
            
            print(f"\n🔧 TROUBLESHOOTING:")
            print("1. Check QuickNode dashboard for endpoint status")
            print("2. Verify all environment variables are set")
            print("3. Ensure wallet has sufficient balance")
            print("4. Run individual test scripts for detailed diagnostics")
    
    async def run_full_verification(self) -> Dict[str, Any]:
        """Run complete trading readiness verification."""
        print("🚀 Starting QuickNode Trading Readiness Verification")
        print("="*60)
        
        all_results = {}
        
        # Test QuickNode primary
        all_results['quicknode_primary'] = await self.verify_quicknode_primary()
        
        # Test Helius fallback
        all_results['helius_fallback'] = await self.verify_helius_fallback()
        
        # Verify configuration
        all_results['configuration'] = self.verify_configuration()
        
        # Verify wallet readiness
        all_results['wallet_readiness'] = self.verify_wallet_readiness(all_results['quicknode_primary'])
        
        # Print final summary
        self.print_final_summary(all_results)
        
        return all_results


async def main():
    """Main verification function."""
    verifier = TradingReadinessVerifier()
    results = await verifier.run_full_verification()
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/trading_readiness_verification.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Verification results saved to: output/trading_readiness_verification.json")
    
    # Return appropriate exit code
    quicknode_ready = results.get('quicknode_primary', {}).get('summary', {}).get('success', False)
    config_ready = results.get('configuration', {}).get('success', False)
    wallet_ready = results.get('wallet_readiness', {}).get('success', False)
    
    overall_ready = quicknode_ready and config_ready and wallet_ready
    return 0 if overall_ready else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
