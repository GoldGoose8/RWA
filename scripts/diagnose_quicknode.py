#!/usr/bin/env python3
"""
QuickNode Connection Diagnostic Tool
Diagnoses and fixes QuickNode connectivity issues
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

class QuickNodeDiagnostic:
    """Comprehensive QuickNode diagnostic tool."""
    
    def __init__(self):
        """Initialize diagnostic tool."""
        self.api_key = os.getenv('QUICKNODE_API_KEY', 'QN_810042470c20437bb9ec222fbf20f071')
        self.rpc_url = os.getenv('QUICKNODE_RPC_URL', 'https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/')
        
        # Test payloads
        self.test_payloads = {
            'health': {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth",
                "params": []
            },
            'version': {
                "jsonrpc": "2.0", 
                "id": 2,
                "method": "getVersion",
                "params": []
            },
            'slot': {
                "jsonrpc": "2.0",
                "id": 3, 
                "method": "getSlot",
                "params": []
            },
            'blockhash': {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "getLatestBlockhash",
                "params": [{"commitment": "confirmed"}]
            }
        }
        
    async def test_basic_connectivity(self) -> Dict[str, Any]:
        """Test basic HTTP connectivity to QuickNode."""
        print("🔍 Testing Basic Connectivity...")
        print(f"   URL: {self.rpc_url}")
        print(f"   API Key: {self.api_key}")
        
        results = {}
        
        try:
            # Test with different timeout values
            for timeout in [5, 10, 30, 60]:
                print(f"\n   Testing with {timeout}s timeout...")
                
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        start_time = time.time()
                        response = await client.post(
                            self.rpc_url,
                            json=self.test_payloads['health'],
                            headers={"Content-Type": "application/json"}
                        )
                        response_time = time.time() - start_time
                        
                        results[f'timeout_{timeout}'] = {
                            'status_code': response.status_code,
                            'response_time': round(response_time, 3),
                            'success': response.status_code == 200,
                            'response_size': len(response.content),
                            'headers': dict(response.headers)
                        }
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                results[f'timeout_{timeout}']['response_data'] = data
                                print(f"   ✅ SUCCESS ({response_time:.3f}s): {response.status_code}")
                                break  # Success, no need to test longer timeouts
                            except json.JSONDecodeError:
                                results[f'timeout_{timeout}']['error'] = 'Invalid JSON response'
                                print(f"   ⚠️ Invalid JSON ({response_time:.3f}s): {response.status_code}")
                        else:
                            print(f"   ❌ FAILED ({response_time:.3f}s): {response.status_code} - {response.text[:100]}")
                            
                except asyncio.TimeoutError:
                    print(f"   ⏰ TIMEOUT: {timeout}s exceeded")
                    results[f'timeout_{timeout}'] = {'error': 'timeout', 'timeout_value': timeout}
                except Exception as e:
                    print(f"   ❌ ERROR: {str(e)}")
                    results[f'timeout_{timeout}'] = {'error': str(e)}
                    
        except Exception as e:
            results['general_error'] = str(e)
            
        return results
    
    async def test_all_methods(self) -> Dict[str, Any]:
        """Test all RPC methods."""
        print("\n🔍 Testing RPC Methods...")
        
        results = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for method_name, payload in self.test_payloads.items():
                print(f"   Testing {method_name}...")
                
                try:
                    start_time = time.time()
                    response = await client.post(
                        self.rpc_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    response_time = time.time() - start_time
                    
                    result = {
                        'status_code': response.status_code,
                        'response_time': round(response_time, 3),
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            result['response_data'] = data
                            result['has_result'] = 'result' in data
                            result['has_error'] = 'error' in data
                            print(f"   ✅ {method_name}: SUCCESS ({response_time:.3f}s)")
                        except json.JSONDecodeError:
                            result['error'] = 'Invalid JSON'
                            print(f"   ❌ {method_name}: Invalid JSON")
                    else:
                        result['error'] = response.text[:200]
                        print(f"   ❌ {method_name}: {response.status_code}")
                        
                    results[method_name] = result
                    
                except Exception as e:
                    results[method_name] = {'error': str(e), 'success': False}
                    print(f"   ❌ {method_name}: {str(e)}")
                    
        return results
    
    async def test_alternative_endpoints(self) -> Dict[str, Any]:
        """Test alternative endpoint configurations."""
        print("\n🔍 Testing Alternative Endpoints...")
        
        # Alternative endpoint patterns
        base_url = self.rpc_url.rstrip('/')
        alternatives = [
            self.rpc_url,  # Original
            f"{base_url}/",  # With trailing slash
            f"{base_url}",   # Without trailing slash
            f"https://green-thrilling-silence.solana-mainnet.quiknode.pro/{self.api_key}/",  # API key in path
            f"https://api.quicknode.com/v1/solana/mainnet/{self.api_key}",  # Different format
        ]
        
        results = {}
        
        for i, url in enumerate(alternatives):
            print(f"   Testing alternative {i+1}: {url}")
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        url,
                        json=self.test_payloads['health'],
                        headers={"Content-Type": "application/json"}
                    )
                    
                    result = {
                        'url': url,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            result['response_data'] = data
                            print(f"   ✅ Alternative {i+1}: SUCCESS")
                        except:
                            result['error'] = 'Invalid JSON'
                            print(f"   ⚠️ Alternative {i+1}: Invalid JSON")
                    else:
                        print(f"   ❌ Alternative {i+1}: {response.status_code}")
                        
                    results[f'alternative_{i+1}'] = result
                    
            except Exception as e:
                results[f'alternative_{i+1}'] = {'url': url, 'error': str(e), 'success': False}
                print(f"   ❌ Alternative {i+1}: {str(e)}")
                
        return results
    
    async def test_helius_fallback(self) -> Dict[str, Any]:
        """Test Helius as fallback."""
        print("\n🔍 Testing Helius Fallback...")
        
        helius_url = os.getenv('HELIUS_RPC_URL', 'https://mainnet.helius-rpc.com/?api-key=4ebf03a3-fdc8-4d41-b652-3e62797b1f6c')
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    helius_url,
                    json=self.test_payloads['health'],
                    headers={"Content-Type": "application/json"}
                )
                
                result = {
                    'url': helius_url,
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['response_data'] = data
                        print(f"   ✅ Helius: SUCCESS")
                    except:
                        result['error'] = 'Invalid JSON'
                        print(f"   ⚠️ Helius: Invalid JSON")
                else:
                    print(f"   ❌ Helius: {response.status_code}")
                    
                return result
                
        except Exception as e:
            print(f"   ❌ Helius: {str(e)}")
            return {'url': helius_url, 'error': str(e), 'success': False}
    
    def print_summary(self, all_results: Dict[str, Any]):
        """Print diagnostic summary."""
        print("\n" + "="*60)
        print("🔧 QUICKNODE DIAGNOSTIC SUMMARY")
        print("="*60)
        
        # Check if any test passed
        any_success = False
        for category, results in all_results.items():
            if isinstance(results, dict):
                for test, result in results.items():
                    if isinstance(result, dict) and result.get('success', False):
                        any_success = True
                        break
        
        if any_success:
            print("✅ SOME TESTS PASSED - QuickNode connectivity is possible")
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("1. Use the working endpoint configuration")
            print("2. Increase timeout values in your application")
            print("3. Implement proper retry logic")
        else:
            print("❌ ALL TESTS FAILED - QuickNode connectivity issues detected")
            print("\n🔧 RECOMMENDED ACTIONS:")
            print("1. Verify your QuickNode API key and endpoint URL")
            print("2. Check QuickNode dashboard for service status")
            print("3. Use Helius as primary endpoint temporarily")
            print("4. Contact QuickNode support if issues persist")
        
        # Show working alternatives
        working_endpoints = []
        for category, results in all_results.items():
            if isinstance(results, dict):
                for test, result in results.items():
                    if isinstance(result, dict) and result.get('success', False):
                        url = result.get('url', 'Unknown')
                        working_endpoints.append(url)
        
        if working_endpoints:
            print(f"\n✅ WORKING ENDPOINTS ({len(working_endpoints)}):")
            for url in set(working_endpoints):  # Remove duplicates
                print(f"   {url}")
    
    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run complete diagnostic suite."""
        print("🚀 Starting QuickNode Diagnostic Suite")
        print("="*60)
        
        all_results = {}
        
        # Test basic connectivity
        all_results['connectivity'] = await self.test_basic_connectivity()
        
        # Test RPC methods
        all_results['rpc_methods'] = await self.test_all_methods()
        
        # Test alternatives
        all_results['alternatives'] = await self.test_alternative_endpoints()
        
        # Test Helius fallback
        all_results['helius_fallback'] = await self.test_helius_fallback()
        
        # Print summary
        self.print_summary(all_results)
        
        return all_results

async def main():
    """Main diagnostic function."""
    diagnostic = QuickNodeDiagnostic()
    results = await diagnostic.run_full_diagnostic()
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/quicknode_diagnostic.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Full diagnostic results saved to: output/quicknode_diagnostic.json")
    
    # Return appropriate exit code
    any_success = any(
        result.get('success', False) 
        for category in results.values() 
        if isinstance(category, dict)
        for result in category.values()
        if isinstance(result, dict)
    )
    
    return 0 if any_success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
