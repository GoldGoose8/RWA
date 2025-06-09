#!/usr/bin/env python3
"""
QuickNode Proper Configuration Script

Configures QuickNode endpoint according to their official documentation
and best practices for Solana RPC connections.
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


class QuickNodeConfigurator:
    """Proper QuickNode configuration based on official documentation."""
    
    def __init__(self):
        """Initialize configurator."""
        # From your QuickNode dashboard endpoint 505883
        self.endpoint_url = "https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/"
        self.api_key = "QN_810042470c20437bb9ec222fbf20f071"
        
        # QuickNode-specific configuration
        self.config = {
            # Basic RPC configuration
            'rpc_url': self.endpoint_url,
            'api_key': self.api_key,
            'timeout': 30.0,
            'max_retries': 3,
            'retry_delay': 1.0,
            
            # QuickNode-specific headers
            'headers': {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Synergy7-Trading-Bot/1.0'
            },
            
            # Connection settings
            'max_connections': 20,
            'max_keepalive_connections': 5,
            'keepalive_expiry': 30,
            
            # Rate limiting (QuickNode specific)
            'rate_limit_per_second': 100,  # QuickNode allows higher rates
            'burst_limit': 200,
            
            # Commitment levels
            'default_commitment': 'confirmed',
            'finalized_commitment': 'finalized',
            'processed_commitment': 'processed'
        }
    
    async def test_basic_connection(self) -> Dict[str, Any]:
        """Test basic connection to QuickNode endpoint."""
        print("🔍 Testing Basic QuickNode Connection...")
        
        # Standard Solana RPC health check
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getHealth",
            "params": []
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=self.config['timeout'],
                limits=httpx.Limits(
                    max_connections=self.config['max_connections'],
                    max_keepalive_connections=self.config['max_keepalive_connections'],
                    keepalive_expiry=self.config['keepalive_expiry']
                )
            ) as client:
                
                start_time = time.time()
                response = await client.post(
                    self.config['rpc_url'],
                    json=payload,
                    headers=self.config['headers']
                )
                response_time = time.time() - start_time
                
                result = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time * 1000, 2),
                    'endpoint': self.config['rpc_url']
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['response_data'] = data
                        result['has_result'] = 'result' in data
                        print(f"   ✅ SUCCESS: {response.status_code} ({response_time:.3f}s)")
                        print(f"   📊 Response: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError:
                        result['error'] = 'Invalid JSON response'
                        print(f"   ⚠️ Invalid JSON response")
                else:
                    result['error'] = response.text[:500]
                    print(f"   ❌ FAILED: {response.status_code}")
                    print(f"   📄 Response: {response.text[:200]}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ CONNECTION ERROR: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'endpoint': self.config['rpc_url']
            }
    
    async def test_solana_methods(self) -> Dict[str, Any]:
        """Test essential Solana RPC methods."""
        print("\n🔍 Testing Solana RPC Methods...")
        
        methods = {
            'getVersion': {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion",
                "params": []
            },
            'getSlot': {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getSlot",
                "params": []
            },
            'getLatestBlockhash': {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "getLatestBlockhash",
                "params": [{"commitment": "confirmed"}]
            },
            'getEpochInfo': {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "getEpochInfo",
                "params": []
            },
            'getFees': {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "getFees",
                "params": []
            }
        }
        
        results = {}
        
        async with httpx.AsyncClient(
            timeout=self.config['timeout'],
            limits=httpx.Limits(
                max_connections=self.config['max_connections'],
                max_keepalive_connections=self.config['max_keepalive_connections']
            )
        ) as client:
            
            for method_name, payload in methods.items():
                print(f"   Testing {method_name}...")
                
                try:
                    start_time = time.time()
                    response = await client.post(
                        self.config['rpc_url'],
                        json=payload,
                        headers=self.config['headers']
                    )
                    response_time = time.time() - start_time
                    
                    result = {
                        'success': response.status_code == 200,
                        'status_code': response.status_code,
                        'response_time_ms': round(response_time * 1000, 2)
                    }
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            result['response_data'] = data
                            result['has_result'] = 'result' in data
                            result['has_error'] = 'error' in data
                            
                            if 'error' in data:
                                print(f"   ❌ {method_name}: RPC Error - {data['error']}")
                            else:
                                print(f"   ✅ {method_name}: SUCCESS ({response_time:.3f}s)")
                                
                        except json.JSONDecodeError:
                            result['error'] = 'Invalid JSON'
                            print(f"   ❌ {method_name}: Invalid JSON")
                    else:
                        result['error'] = response.text[:200]
                        print(f"   ❌ {method_name}: HTTP {response.status_code}")
                    
                    results[method_name] = result
                    
                    # Small delay between requests to respect rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    results[method_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"   ❌ {method_name}: {str(e)}")
        
        return results
    
    async def test_transaction_simulation(self) -> Dict[str, Any]:
        """Test transaction simulation capabilities."""
        print("\n🔍 Testing Transaction Simulation...")
        
        # Simple transfer simulation (won't actually execute)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "simulateTransaction",
            "params": [
                "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAMHBsgN27lcgB6H2WQvFgyZuJYHa46puOQo9yQ8CVQbd9uHXZaGT2cvhRs7reawctIXtX1s3kTqM9YV+/wCp20C7Wj2aiuk5TReAXo+VTVg8QTHjs0UjNMMKCvpzZ+ABAgEBARU=",
                {
                    "encoding": "base64",
                    "commitment": "confirmed"
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.config['timeout']) as client:
                response = await client.post(
                    self.config['rpc_url'],
                    json=payload,
                    headers=self.config['headers']
                )
                
                result = {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'simulation_supported': False
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['response_data'] = data
                        
                        # Check if simulation is supported
                        if 'result' in data:
                            result['simulation_supported'] = True
                            print(f"   ✅ Transaction simulation: SUPPORTED")
                        elif 'error' in data:
                            # Some errors are expected for invalid transactions
                            result['simulation_supported'] = True
                            print(f"   ✅ Transaction simulation: SUPPORTED (with expected error)")
                        else:
                            print(f"   ⚠️ Transaction simulation: UNKNOWN")
                    except json.JSONDecodeError:
                        result['error'] = 'Invalid JSON'
                        print(f"   ❌ Transaction simulation: Invalid JSON")
                else:
                    result['error'] = response.text[:200]
                    print(f"   ❌ Transaction simulation: HTTP {response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Transaction simulation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'simulation_supported': False
            }
    
    def generate_optimized_config(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized configuration based on test results."""
        print("\n🔧 Generating Optimized Configuration...")
        
        # Analyze test results
        basic_connection_works = test_results.get('basic_connection', {}).get('success', False)
        working_methods = [
            method for method, result in test_results.get('solana_methods', {}).items()
            if result.get('success', False) and not result.get('has_error', False)
        ]
        simulation_works = test_results.get('transaction_simulation', {}).get('simulation_supported', False)
        
        # Calculate average response time
        response_times = []
        for category in test_results.values():
            if isinstance(category, dict):
                if 'response_time_ms' in category:
                    response_times.append(category['response_time_ms'])
                elif isinstance(category, dict):
                    for result in category.values():
                        if isinstance(result, dict) and 'response_time_ms' in result:
                            response_times.append(result['response_time_ms'])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Generate optimized config
        optimized_config = {
            'endpoint_status': 'working' if basic_connection_works else 'failed',
            'working_methods': working_methods,
            'simulation_supported': simulation_works,
            'avg_response_time_ms': round(avg_response_time, 2),
            
            # Optimized settings
            'recommended_timeout': max(30, int(avg_response_time / 1000) + 10) if avg_response_time > 0 else 30,
            'recommended_retries': 3 if basic_connection_works else 5,
            'recommended_retry_delay': 1.0 if avg_response_time < 1000 else 2.0,
            
            # Environment variables to update
            'env_updates': {
                'QUICKNODE_RPC_URL': self.config['rpc_url'],
                'QUICKNODE_API_KEY': self.config['api_key'],
                'QUICKNODE_TIMEOUT': max(30, int(avg_response_time / 1000) + 10) if avg_response_time > 0 else 30,
                'QUICKNODE_MAX_RETRIES': 3 if basic_connection_works else 5,
                'QUICKNODE_RETRY_DELAY': 1.0 if avg_response_time < 1000 else 2.0,
                'QUICKNODE_ENABLED': 'true' if basic_connection_works else 'false',
                'PRIMARY_RPC': 'quicknode' if basic_connection_works else 'helius'
            }
        }
        
        return optimized_config
    
    def print_summary(self, test_results: Dict[str, Any], optimized_config: Dict[str, Any]):
        """Print configuration summary."""
        print("\n" + "="*60)
        print("🔧 QUICKNODE CONFIGURATION SUMMARY")
        print("="*60)
        
        basic_works = test_results.get('basic_connection', {}).get('success', False)
        working_methods = len(optimized_config.get('working_methods', []))
        total_methods = len(test_results.get('solana_methods', {}))
        
        if basic_works:
            print("✅ QuickNode endpoint is WORKING")
            print(f"✅ {working_methods}/{total_methods} RPC methods working")
            print(f"📊 Average response time: {optimized_config['avg_response_time_ms']}ms")
            
            if optimized_config['simulation_supported']:
                print("✅ Transaction simulation supported")
            
            print(f"\n🔧 RECOMMENDED SETTINGS:")
            print(f"   Timeout: {optimized_config['recommended_timeout']}s")
            print(f"   Max Retries: {optimized_config['recommended_retries']}")
            print(f"   Retry Delay: {optimized_config['recommended_retry_delay']}s")
            
            print(f"\n📝 UPDATE YOUR .env FILE:")
            for key, value in optimized_config['env_updates'].items():
                print(f"   {key}={value}")
                
        else:
            print("❌ QuickNode endpoint is NOT WORKING")
            print("\n🔧 TROUBLESHOOTING STEPS:")
            print("1. Verify endpoint URL in QuickNode dashboard")
            print("2. Check API key is correct and active")
            print("3. Ensure endpoint is for Solana Mainnet")
            print("4. Check network connectivity")
            print("5. Contact QuickNode support if issues persist")
            
            print(f"\n📝 FALLBACK CONFIGURATION:")
            print("   PRIMARY_RPC=helius")
            print("   QUICKNODE_ENABLED=false")
    
    async def run_full_configuration(self) -> Dict[str, Any]:
        """Run complete QuickNode configuration."""
        print("🚀 Starting QuickNode Configuration")
        print("="*60)
        print(f"Endpoint: {self.config['rpc_url']}")
        print(f"API Key: {self.config['api_key']}")
        print()
        
        test_results = {}
        
        # Test basic connection
        test_results['basic_connection'] = await self.test_basic_connection()
        
        # Test Solana methods
        test_results['solana_methods'] = await self.test_solana_methods()
        
        # Test transaction simulation
        test_results['transaction_simulation'] = await self.test_transaction_simulation()
        
        # Generate optimized configuration
        optimized_config = self.generate_optimized_config(test_results)
        
        # Print summary
        self.print_summary(test_results, optimized_config)
        
        return {
            'test_results': test_results,
            'optimized_config': optimized_config
        }


async def main():
    """Main configuration function."""
    configurator = QuickNodeConfigurator()
    results = await configurator.run_full_configuration()
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/quicknode_configuration.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Configuration results saved to: output/quicknode_configuration.json")
    
    # Return appropriate exit code
    basic_works = results['test_results'].get('basic_connection', {}).get('success', False)
    return 0 if basic_works else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
