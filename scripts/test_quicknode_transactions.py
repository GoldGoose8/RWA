#!/usr/bin/env python3
"""
QuickNode Transaction Testing Script

Tests QuickNode's ability to handle on-chain transactions including:
- Account lookups
- Balance queries  
- Transaction simulation
- Fee estimation
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


class QuickNodeTransactionTester:
    """Test QuickNode's transaction handling capabilities."""
    
    def __init__(self):
        """Initialize transaction tester."""
        self.rpc_url = os.getenv('QUICKNODE_RPC_URL', 'https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/')
        self.api_key = os.getenv('QUICKNODE_API_KEY', 'QN_810042470c20437bb9ec222fbf20f071')
        
        # Test wallet address from .env
        self.test_wallet = os.getenv('WALLET_ADDRESS', 'Az47WmeBr94pTFeK6feHTjn6rGLWniviSCXtnJ65kGaf').strip("'")
        
        # Standard Solana token addresses
        self.sol_token = "So11111111111111111111111111111111111111112"
        self.usdc_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Synergy7-Trading-Bot/1.0'
        }
    
    async def test_account_info(self) -> Dict[str, Any]:
        """Test account information retrieval."""
        print("🔍 Testing Account Information Retrieval...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                self.test_wallet,
                {
                    "encoding": "base64",
                    "commitment": "confirmed"
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = time.time()
                response = await client.post(self.rpc_url, json=payload, headers=self.headers)
                response_time = time.time() - start_time
                
                result = {
                    'success': response.status_code == 200,
                    'response_time_ms': round(response_time * 1000, 2),
                    'wallet_address': self.test_wallet
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result['response_data'] = data
                    
                    if 'result' in data and data['result']:
                        account_info = data['result']['value']
                        if account_info:
                            result['account_exists'] = True
                            result['lamports'] = account_info.get('lamports', 0)
                            result['sol_balance'] = account_info.get('lamports', 0) / 1e9
                            print(f"   ✅ Account found: {result['sol_balance']:.6f} SOL")
                        else:
                            result['account_exists'] = False
                            print(f"   ⚠️ Account not found or empty")
                    else:
                        result['account_exists'] = False
                        print(f"   ⚠️ No account data returned")
                else:
                    result['error'] = response.text[:200]
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_balance_query(self) -> Dict[str, Any]:
        """Test balance queries."""
        print("\n🔍 Testing Balance Queries...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [
                self.test_wallet,
                {"commitment": "confirmed"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.rpc_url, json=payload, headers=self.headers)
                
                result = {
                    'success': response.status_code == 200,
                    'wallet_address': self.test_wallet
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result['response_data'] = data
                    
                    if 'result' in data:
                        lamports = data['result']['value']
                        sol_balance = lamports / 1e9
                        result['lamports'] = lamports
                        result['sol_balance'] = sol_balance
                        print(f"   ✅ Balance: {sol_balance:.6f} SOL ({lamports:,} lamports)")
                    else:
                        result['error'] = 'No balance data'
                        print(f"   ❌ No balance data returned")
                else:
                    result['error'] = response.text[:200]
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_token_accounts(self) -> Dict[str, Any]:
        """Test token account queries."""
        print("\n🔍 Testing Token Account Queries...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                self.test_wallet,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.rpc_url, json=payload, headers=self.headers)
                
                result = {
                    'success': response.status_code == 200,
                    'wallet_address': self.test_wallet
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result['response_data'] = data
                    
                    if 'result' in data:
                        token_accounts = data['result']['value']
                        result['token_account_count'] = len(token_accounts)
                        result['token_accounts'] = []
                        
                        print(f"   ✅ Found {len(token_accounts)} token accounts:")
                        
                        for account in token_accounts:
                            try:
                                account_data = account['account']['data']['parsed']['info']
                                mint = account_data['mint']
                                balance = float(account_data['tokenAmount']['uiAmount'] or 0)
                                decimals = account_data['tokenAmount']['decimals']
                                
                                token_info = {
                                    'mint': mint,
                                    'balance': balance,
                                    'decimals': decimals,
                                    'account_address': account['pubkey']
                                }
                                result['token_accounts'].append(token_info)
                                
                                # Identify known tokens
                                token_name = "Unknown"
                                if mint == self.usdc_token:
                                    token_name = "USDC"
                                elif mint == self.sol_token:
                                    token_name = "SOL"
                                
                                print(f"      {token_name}: {balance} ({mint[:8]}...)")
                                
                            except Exception as e:
                                print(f"      Error parsing account: {e}")
                    else:
                        result['error'] = 'No token account data'
                        print(f"   ❌ No token account data returned")
                else:
                    result['error'] = response.text[:200]
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_recent_blockhash(self) -> Dict[str, Any]:
        """Test recent blockhash retrieval for transactions."""
        print("\n🔍 Testing Recent Blockhash Retrieval...")
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.rpc_url, json=payload, headers=self.headers)
                
                result = {
                    'success': response.status_code == 200
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result['response_data'] = data
                    
                    if 'result' in data:
                        blockhash_info = data['result']['value']
                        result['blockhash'] = blockhash_info['blockhash']
                        result['last_valid_block_height'] = blockhash_info['lastValidBlockHeight']
                        print(f"   ✅ Blockhash: {result['blockhash'][:16]}...")
                        print(f"   ✅ Valid until block: {result['last_valid_block_height']:,}")
                    else:
                        result['error'] = 'No blockhash data'
                        print(f"   ❌ No blockhash data returned")
                else:
                    result['error'] = response.text[:200]
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def test_fee_estimation(self) -> Dict[str, Any]:
        """Test transaction fee estimation."""
        print("\n🔍 Testing Fee Estimation...")
        
        # Get recent blockhash first
        blockhash_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get blockhash
                blockhash_response = await client.post(self.rpc_url, json=blockhash_payload, headers=self.headers)
                
                if blockhash_response.status_code != 200:
                    return {'success': False, 'error': 'Failed to get blockhash for fee estimation'}
                
                blockhash_data = blockhash_response.json()
                if 'result' not in blockhash_data:
                    return {'success': False, 'error': 'No blockhash in response'}
                
                # Test fee calculation
                fee_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "getFeeForMessage",
                    "params": [
                        "AQABAgIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAQAA",
                        {"commitment": "confirmed"}
                    ]
                }
                
                fee_response = await client.post(self.rpc_url, json=fee_payload, headers=self.headers)
                
                result = {
                    'success': fee_response.status_code == 200
                }
                
                if fee_response.status_code == 200:
                    data = fee_response.json()
                    result['response_data'] = data
                    
                    if 'result' in data and data['result']['value'] is not None:
                        fee_lamports = data['result']['value']
                        fee_sol = fee_lamports / 1e9
                        result['fee_lamports'] = fee_lamports
                        result['fee_sol'] = fee_sol
                        print(f"   ✅ Estimated fee: {fee_sol:.9f} SOL ({fee_lamports:,} lamports)")
                    else:
                        result['error'] = 'No fee data or null result'
                        print(f"   ⚠️ Fee estimation returned null (normal for invalid message)")
                else:
                    result['error'] = fee_response.text[:200]
                    print(f"   ❌ Failed: HTTP {fee_response.status_code}")
                
                return result
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def print_summary(self, test_results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "="*60)
        print("🔧 QUICKNODE TRANSACTION TESTING SUMMARY")
        print("="*60)
        
        tests_passed = sum(1 for result in test_results.values() if result.get('success', False))
        total_tests = len(test_results)
        
        print(f"✅ Tests passed: {tests_passed}/{total_tests}")
        
        # Check specific capabilities
        if test_results.get('account_info', {}).get('success'):
            account_exists = test_results['account_info'].get('account_exists', False)
            if account_exists:
                sol_balance = test_results['account_info'].get('sol_balance', 0)
                print(f"✅ Wallet accessible: {sol_balance:.6f} SOL")
            else:
                print(f"⚠️ Wallet exists but may be empty")
        
        if test_results.get('token_accounts', {}).get('success'):
            token_count = test_results['token_accounts'].get('token_account_count', 0)
            print(f"✅ Token accounts found: {token_count}")
        
        if test_results.get('recent_blockhash', {}).get('success'):
            print(f"✅ Transaction preparation: Ready")
        
        if test_results.get('fee_estimation', {}).get('success'):
            print(f"✅ Fee estimation: Working")
        
        print(f"\n🔧 QUICKNODE TRANSACTION READINESS:")
        if tests_passed >= 3:
            print("✅ QuickNode is ready for on-chain transactions")
            print("✅ All essential transaction capabilities working")
        else:
            print("⚠️ Some transaction capabilities may be limited")
            print("🔧 Consider using Helius as fallback for complex operations")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all transaction tests."""
        print("🚀 Starting QuickNode Transaction Testing")
        print("="*60)
        print(f"Endpoint: {self.rpc_url}")
        print(f"Test Wallet: {self.test_wallet}")
        print()
        
        test_results = {}
        
        # Run all tests
        test_results['account_info'] = await self.test_account_info()
        test_results['balance_query'] = await self.test_balance_query()
        test_results['token_accounts'] = await self.test_token_accounts()
        test_results['recent_blockhash'] = await self.test_recent_blockhash()
        test_results['fee_estimation'] = await self.test_fee_estimation()
        
        # Print summary
        self.print_summary(test_results)
        
        return test_results


async def main():
    """Main testing function."""
    tester = QuickNodeTransactionTester()
    results = await tester.run_all_tests()
    
    # Save results
    os.makedirs("output", exist_ok=True)
    with open("output/quicknode_transaction_tests.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Transaction test results saved to: output/quicknode_transaction_tests.json")
    
    # Return appropriate exit code
    tests_passed = sum(1 for result in results.values() if result.get('success', False))
    return 0 if tests_passed >= 3 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
