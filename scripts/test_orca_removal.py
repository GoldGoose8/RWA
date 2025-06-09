#!/usr/bin/env python3
"""
Test Orca Removal Verification

Verifies that all Orca dependencies have been successfully removed
and the system can operate without Orca error 3012.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class OrcaRemovalVerifier:
    """Verify Orca removal is complete."""
    
    def __init__(self):
        """Initialize verifier."""
        self.test_results = {}
        
    def test_orca_imports_removed(self) -> Dict[str, Any]:
        """Test that Orca imports are removed."""
        print("🔍 Testing Orca Import Removal...")
        
        tests = {
            'orca_client_removed': True,
            'orca_fallback_removed': True,
            'orca_swap_builder_removed': True,
            'dex_init_updated': True
        }
        
        # Test that Orca imports fail
        try:
            from core.dex.orca_client import OrcaClient
            tests['orca_client_removed'] = False
            print("   ❌ OrcaClient still importable")
        except ImportError:
            print("   ✅ OrcaClient import removed")
        
        try:
            from core.dex.orca_fallback_builder import OrcaFallbackBuilder
            tests['orca_fallback_removed'] = False
            print("   ❌ OrcaFallbackBuilder still importable")
        except ImportError:
            print("   ✅ OrcaFallbackBuilder import removed")
        
        try:
            from core.dex.orca_swap_builder import OrcaSwapBuilder
            tests['orca_swap_builder_removed'] = False
            print("   ❌ OrcaSwapBuilder still importable")
        except ImportError:
            print("   ✅ OrcaSwapBuilder import removed")
        
        # Test that DEX module works without Orca
        try:
            from core.dex import UnifiedTransactionBuilder, COMMON_TOKENS, get_token_mint
            print("   ✅ DEX module imports work without Orca")
        except ImportError as e:
            tests['dex_init_updated'] = False
            print(f"   ❌ DEX module import failed: {e}")
        
        passed = sum(tests.values())
        total = len(tests)
        
        return {
            'success': passed == total,
            'passed_tests': passed,
            'total_tests': total,
            'details': tests
        }
    
    async def test_simplified_builder(self) -> Dict[str, Any]:
        """Test simplified builder functionality."""
        print("\n🔍 Testing Simplified Builder...")
        
        try:
            from core.dex.simplified_native_builder import SimplifiedNativeBuilder
            
            # Create test builder
            builder = SimplifiedNativeBuilder("test_wallet", None)
            await builder.initialize()
            
            # Test transaction building
            test_signal = {
                'action': 'BUY',
                'size': 0.01,
                'market': 'SOL-USDC'
            }
            
            result = await builder.build_transaction(test_signal)
            
            success = (
                result is not None and
                result.get('success', False) and
                result.get('execution_type') == 'simplified_native'
            )
            
            if success:
                print("   ✅ Simplified builder works correctly")
                print(f"   ✅ Result: {result.get('message', 'No message')}")
            else:
                print("   ❌ Simplified builder failed")
            
            return {
                'success': success,
                'result': result,
                'builder_status': builder.get_status()
            }
            
        except Exception as e:
            print(f"   ❌ Simplified builder error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def test_unified_transaction_builder(self) -> Dict[str, Any]:
        """Test unified transaction builder without Orca."""
        print("\n🔍 Testing Unified Transaction Builder...")
        
        try:
            from core.dex.unified_transaction_builder import UnifiedTransactionBuilder
            
            # Create test builder
            builder = UnifiedTransactionBuilder("test_wallet", None)
            await builder.initialize()
            
            # Test transaction building
            test_signal = {
                'action': 'BUY',
                'size': 0.01,
                'market': 'SOL-USDC',
                'price': 150.0
            }
            
            result = await builder.build_swap_transaction(test_signal)
            
            success = (
                result is not None and
                result.get('success', False) and
                result.get('execution_type') == 'simplified_native'
            )
            
            if success:
                print("   ✅ Unified builder works without Orca")
                print(f"   ✅ Execution type: {result.get('execution_type')}")
                print(f"   ✅ Message: {result.get('message', 'No message')}")
            else:
                print("   ❌ Unified builder failed")
            
            await builder.close()
            
            return {
                'success': success,
                'result': result
            }
            
        except Exception as e:
            print(f"   ❌ Unified builder error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_environment_cleanup(self) -> Dict[str, Any]:
        """Test that Orca environment variables are cleaned up."""
        print("\n🔍 Testing Environment Cleanup...")
        
        orca_env_vars = [
            'ORCA_API_URL',
            'ORCA_SLIPPAGE_BPS',
            'ORCA_PRIORITY_FEE',
            'ORCA_DIRECT_ROUTES_ONLY',
            'ORCA_MIN_OUTPUT_BUFFER',
            'ORCA_MAX_PRICE_IMPACT'
        ]
        
        remaining_vars = []
        for var in orca_env_vars:
            if os.getenv(var):
                remaining_vars.append(var)
        
        if remaining_vars:
            print(f"   ⚠️ Remaining Orca env vars: {remaining_vars}")
        else:
            print("   ✅ All Orca environment variables removed")
        
        return {
            'success': len(remaining_vars) == 0,
            'remaining_vars': remaining_vars,
            'cleaned_vars': len(orca_env_vars) - len(remaining_vars)
        }
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("🗑️ ORCA REMOVAL VERIFICATION SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        
        print(f"📊 Tests: {passed_tests}/{total_tests} passed")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {status} {test_name.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ORCA REMOVAL COMPLETE!")
            print("✅ All Orca dependencies successfully removed")
            print("✅ Simplified transaction builder working")
            print("✅ System ready to operate without Orca error 3012")
            print("\n🚀 The system should now run without Orca-related errors!")
        else:
            print(f"\n⚠️ ORCA REMOVAL INCOMPLETE")
            print("🔧 Some issues remain - check failed tests above")
    
    async def run_all_tests(self):
        """Run all Orca removal verification tests."""
        print("🚀 Starting Orca Removal Verification")
        print("="*60)
        
        # Run all tests
        self.test_results['import_removal'] = self.test_orca_imports_removed()
        self.test_results['simplified_builder'] = await self.test_simplified_builder()
        self.test_results['unified_builder'] = await self.test_unified_transaction_builder()
        self.test_results['environment_cleanup'] = self.test_environment_cleanup()
        
        # Print summary
        self.print_summary()
        
        return self.test_results


async def main():
    """Main verification function."""
    verifier = OrcaRemovalVerifier()
    results = await verifier.run_all_tests()
    
    # Save results
    import json
    os.makedirs("output", exist_ok=True)
    with open("output/orca_removal_verification.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Verification results saved to: output/orca_removal_verification.json")
    
    # Return appropriate exit code
    all_passed = all(result.get('success', False) for result in results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
