#!/usr/bin/env python3
"""
RPC Endpoint Testing Script
Tests all configured RPC endpoints to ensure they're working correctly.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List
import httpx
import base64
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RPCEndpointTester:
    """Test RPC endpoints for functionality and response times."""

    def __init__(self):
        """Initialize the RPC endpoint tester."""
        self.endpoints = {
            'helius': os.getenv('HELIUS_RPC_URL'),
            'quicknode': os.getenv('QUICKNODE_RPC_URL'),
            'fallback': os.getenv('FALLBACK_RPC_URL'),
        }

        # Debug: Print loaded URLs
        print(f"🔍 DEBUG: Loaded URLs:")
        for name, url in self.endpoints.items():
            print(f"  {name}: {url}")

        self.results = {}

    async def test_endpoint(self, name: str, url: str) -> Dict[str, Any]:
        """Test a single RPC endpoint."""
        logger.info(f"🔍 Testing {name} endpoint: {url}")

        result = {
            'name': name,
            'url': url,
            'available': False,
            'response_time': None,
            'block_height': None,
            'error': None
        }

        if not url:
            result['error'] = 'URL not configured'
            return result

        try:
            start_time = time.time()

            # Test basic RPC call - getSlot
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSlot",
                    "params": [{"commitment": "confirmed"}]
                }

                response = await client.post(url, json=payload)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        result['available'] = True
                        result['response_time'] = response_time
                        result['block_height'] = data['result']
                        logger.info(f"✅ {name}: Available (slot: {data['result']}, {response_time:.3f}s)")
                    else:
                        result['error'] = f"Invalid response: {data}"
                        logger.error(f"❌ {name}: Invalid response - {data}")
                else:
                    result['error'] = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ {name}: HTTP {response.status_code}")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ {name}: Error - {e}")

        return result

    async def test_transaction_submission(self, name: str, url: str) -> Dict[str, Any]:
        """Test transaction submission capability."""
        logger.info(f"🔍 Testing transaction submission for {name}")

        result = {
            'name': name,
            'can_submit': False,
            'error': None
        }

        if not url:
            result['error'] = 'URL not configured'
            return result

        try:
            # Create a dummy transaction (will fail but should return proper error)
            dummy_tx = base64.b64encode(b"dummy_transaction_data").decode('utf-8')

            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        dummy_tx,
                        {
                            "encoding": "base64",
                            "skipPreflight": True,
                            "maxRetries": 0
                        }
                    ]
                }

                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    # We expect an error for dummy transaction, but proper error format means endpoint works
                    if 'error' in data and 'code' in data['error']:
                        result['can_submit'] = True
                        logger.info(f"✅ {name}: Can accept transactions (returned proper error)")
                    elif 'result' in data:
                        # Unexpected success with dummy data - endpoint accepts transactions
                        result['can_submit'] = True
                        logger.info(f"✅ {name}: Accepts transactions")
                    else:
                        result['error'] = f"Unexpected response: {data}"
                        logger.error(f"❌ {name}: Unexpected response - {data}")
                else:
                    result['error'] = f"HTTP {response.status_code}"
                    logger.error(f"❌ {name}: HTTP {response.status_code}")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ {name}: Error - {e}")

        return result

    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all configured RPC endpoints."""
        logger.info("🚀 Starting RPC endpoint testing...")

        # Test basic connectivity
        connectivity_tasks = []
        for name, url in self.endpoints.items():
            if url:
                task = self.test_endpoint(name, url)
                connectivity_tasks.append(task)

        connectivity_results = await asyncio.gather(*connectivity_tasks, return_exceptions=True)

        # Test transaction submission
        submission_tasks = []
        for name, url in self.endpoints.items():
            if url:
                task = self.test_transaction_submission(name, url)
                submission_tasks.append(task)

        submission_results = await asyncio.gather(*submission_tasks, return_exceptions=True)

        # Compile results
        final_results = {
            'connectivity': [r for r in connectivity_results if not isinstance(r, Exception)],
            'transaction_submission': [r for r in submission_results if not isinstance(r, Exception)],
            'summary': {
                'total_endpoints': len([url for url in self.endpoints.values() if url]),
                'available_endpoints': 0,
                'fastest_endpoint': None,
                'recommended_primary': None
            }
        }

        # Calculate summary
        available = [r for r in final_results['connectivity'] if r.get('available')]
        final_results['summary']['available_endpoints'] = len(available)

        if available:
            # Find fastest endpoint
            fastest = min(available, key=lambda x: x.get('response_time', float('inf')))
            final_results['summary']['fastest_endpoint'] = fastest['name']

            # Recommend primary endpoint
            working_submission = [r for r in final_results['transaction_submission'] if r.get('can_submit')]
            if working_submission:
                # Prefer QuickNode if available and working
                quicknode_working = any(r['name'] == 'quicknode' for r in working_submission)
                if quicknode_working:
                    final_results['summary']['recommended_primary'] = 'quicknode'
                else:
                    final_results['summary']['recommended_primary'] = working_submission[0]['name']

        return final_results

    def print_results(self, results: Dict[str, Any]):
        """Print test results in a readable format."""
        print("\n" + "="*60)
        print("🔍 RPC ENDPOINT TEST RESULTS")
        print("="*60)

        print("\n📡 CONNECTIVITY TESTS:")
        for result in results['connectivity']:
            status = "✅ AVAILABLE" if result['available'] else "❌ UNAVAILABLE"
            name = result['name'].upper()

            if result['available']:
                print(f"  {status} {name}: {result['response_time']:.3f}s (slot: {result['block_height']})")
            else:
                print(f"  {status} {name}: {result.get('error', 'Unknown error')}")

        print("\n🚀 TRANSACTION SUBMISSION TESTS:")
        for result in results['transaction_submission']:
            status = "✅ CAN SUBMIT" if result['can_submit'] else "❌ CANNOT SUBMIT"
            name = result['name'].upper()

            if result['can_submit']:
                print(f"  {status} {name}: Ready for live trading")
            else:
                print(f"  {status} {name}: {result.get('error', 'Unknown error')}")

        print("\n📊 SUMMARY:")
        summary = results['summary']
        print(f"  Total Endpoints: {summary['total_endpoints']}")
        print(f"  Available: {summary['available_endpoints']}")
        print(f"  Fastest: {summary['fastest_endpoint'] or 'None'}")
        print(f"  Recommended Primary: {summary['recommended_primary'] or 'None'}")

        if summary['recommended_primary']:
            print(f"\n🎯 RECOMMENDATION: Use {summary['recommended_primary'].upper()} as primary RPC")
        else:
            print(f"\n⚠️  WARNING: No working RPC endpoints found!")

        print("="*60)

async def main():
    """Main test function."""
    tester = RPCEndpointTester()
    results = await tester.test_all_endpoints()
    tester.print_results(results)

    # Return exit code based on results
    if results['summary']['available_endpoints'] == 0:
        print("\n❌ CRITICAL: No RPC endpoints are working!")
        return 1
    elif results['summary']['recommended_primary'] is None:
        print("\n⚠️  WARNING: No endpoints can submit transactions!")
        return 1
    else:
        print("\n✅ SUCCESS: RPC endpoints are working correctly!")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
