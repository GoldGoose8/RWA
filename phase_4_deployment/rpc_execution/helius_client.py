#!/usr/bin/env python3
"""
Helius RPC Client

This module provides a client for interacting with Helius RPC services.
"""

import os
import json
import time
import logging
import asyncio
import httpx
import yaml
import websockets
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# Import our PyO3-based package
try:
    from shared.solana_utils.tx_utils import (
        Transaction, VersionedTransaction,
        serialize_transaction, deserialize_transaction,
        encode_base58, decode_base58,
        encode_base64, decode_base64
    )
    USING_RUST_UTILS = True
except ImportError:
    # Fallback to solders if solana_tx_utils is not available
    from solders.transaction import Transaction, VersionedTransaction
    import base64
    import base58
    USING_RUST_UTILS = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'output', 'helius_client_log.txt'
        )),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('helius_client')

# Import the RpcClientInterface if available
try:
    from rpc_execution.transaction_executor import RpcClientInterface
    USING_INTERFACE = True
except ImportError:
    USING_INTERFACE = False
    RpcClientInterface = object  # Use object as a fallback base class

class HeliusClient(RpcClientInterface):
    """
    Client for interacting with Helius RPC services.

    Implements the RpcClientInterface for use with the TransactionExecutor.
    """

    def __init__(self,
                 rpc_url: str = None,
                 fallback_rpc_url: str = None,  # No public RPC fallback
                 api_key: str = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize the HeliusClient.

        Args:
            rpc_url: Helius RPC URL
            fallback_rpc_url: Fallback RPC URL if Helius fails
            api_key: Helius API key
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
            timeout: Timeout for HTTP requests in seconds
        """
        # Use environment variables if not provided
        self.api_key = api_key or os.getenv("HELIUS_API_KEY")

        # Construct RPC URL with API key if not provided
        if rpc_url is None:
            self.rpc_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"
        else:
            self.rpc_url = rpc_url

        self.fallback_rpc_url = fallback_rpc_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        # Updated base API URL according to documentation
        self.base_api_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=timeout)

        # Initialize metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_requests': 0,
            'avg_response_time': 0.0,
            'last_request_time': 0.0,
            'last_updated': time.time()
        }

        logger.info(f"Initialized Helius client with RPC URL: {self.rpc_url}")

    async def send_transaction(self,
                              signed_tx: Union[bytes, str, Transaction, VersionedTransaction],
                              opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a transaction using Helius RPC.

        Args:
            signed_tx: Signed transaction as bytes, base64/base58 string, or Transaction/VersionedTransaction object
            opts: Optional transaction options

        Returns:
            Dict containing the response data
        """
        # Update metrics
        self.metrics['total_requests'] += 1
        start_time = time.time()

        # CRITICAL FIX: Force base58 encoding for Helius to prevent signature verification failures
        # Helius RPC requires base58 encoding for transaction signatures to be verified correctly
        encoding = 'base58'  # Always use base58 for Helius regardless of opts

        # Process the transaction based on its type
        if isinstance(signed_tx, (Transaction, VersionedTransaction)):
            # Serialize the transaction object
            try:
                if USING_RUST_UTILS:
                    # Use our PyO3-based package for serialization
                    tx_bytes = signed_tx.serialize()
                    is_versioned = isinstance(signed_tx, VersionedTransaction)
                    encoded_tx = serialize_transaction(tx_bytes, encoding, is_versioned)
                else:
                    # Fallback to solders
                    tx_bytes = signed_tx.serialize()
                    if encoding == 'base64':
                        encoded_tx = base64.b64encode(tx_bytes).decode('utf-8')
                    else:  # base58
                        encoded_tx = base58.b58encode(tx_bytes).decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to serialize transaction: {str(e)}")
                return {
                    'success': False,
                    'error': f"Failed to serialize transaction: {str(e)}",
                    'provider': None
                }
        elif isinstance(signed_tx, bytes):
            # Encode the raw bytes
            if USING_RUST_UTILS:
                # Use our PyO3-based package for encoding
                if encoding == 'base64':
                    encoded_tx = encode_base64(signed_tx)
                else:  # base58
                    encoded_tx = encode_base58(signed_tx)
            else:
                # Fallback to standard libraries
                if encoding == 'base64':
                    encoded_tx = base64.b64encode(signed_tx).decode('utf-8')
                else:  # base58
                    encoded_tx = base58.b58encode(signed_tx).decode('utf-8')
        else:
            # Assume it's already an encoded string
            # We'll trust the caller to provide the correct encoding
            encoded_tx = signed_tx

        # Check if we should skip simulation (preflight)
        skip_simulation = opts.get('skip_simulation', False) if opts else False
        skip_preflight = opts.get('skip_preflight', skip_simulation) if opts else skip_simulation

        if skip_simulation:
            logger.info("Skipping transaction simulation (preflight) as requested")

        # Prepare request payload
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                encoded_tx,
                {
                    "encoding": encoding,
                    "skipPreflight": skip_preflight,
                    "maxRetries": opts.get('max_retries', 0) if opts else 0,
                    "commitment": opts.get('commitment', 'confirmed') if opts else 'confirmed'
                }
            ]
        }

        # Try to send via Helius with retries
        for attempt in range(self.max_retries):
            try:
                # Send request
                response = await self.http_client.post(
                    self.rpc_url,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                if 'result' in result:
                    signature = result['result']



                    # Update metrics
                    self.metrics['successful_requests'] += 1
                    self.metrics['last_request_time'] = time.time() - start_time
                    self.metrics['avg_response_time'] = (
                        (self.metrics['avg_response_time'] * (self.metrics['successful_requests'] - 1)) +
                        self.metrics['last_request_time']
                    ) / self.metrics['successful_requests']

                    logger.info(f"Transaction sent successfully via Helius: {signature}")
                    return {
                        'success': True,
                        'signature': signature,
                        'provider': 'helius',
                        'response_time': self.metrics['last_request_time']
                    }
                else:
                    logger.warning(f"Helius RPC error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error sending transaction via Helius: {str(e)}")

            # Wait before retrying
            await asyncio.sleep(self.retry_delay)

        # Update metrics
        self.metrics['failed_requests'] += 1

        # Try fallback RPC if available
        if self.fallback_rpc_url:
            logger.info("Trying fallback RPC...")
            try:
                response = await self.http_client.post(
                    self.fallback_rpc_url,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                if 'result' in result:
                    signature = result['result']



                    # Update metrics
                    self.metrics['fallback_requests'] += 1
                    self.metrics['last_request_time'] = time.time() - start_time

                    logger.info(f"Transaction sent successfully via fallback RPC: {signature}")
                    return {
                        'success': True,
                        'signature': signature,
                        'provider': 'fallback',
                        'response_time': self.metrics['last_request_time']
                    }
                else:
                    logger.error(f"Fallback RPC error: {result.get('error')}")
            except Exception as e:
                logger.error(f"Error sending transaction via fallback RPC: {str(e)}")

        return {
            'success': False,
            'error': 'Failed to send transaction via all available RPC endpoints',
            'provider': None
        }

    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """
        Get the status of a transaction.

        Args:
            signature: Transaction signature

        Returns:
            Dict containing the transaction status
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignatureStatuses",
            "params": [
                [signature],
                {"searchTransactionHistory": True}
            ]
        }

        try:
            response = await self.http_client.post(
                self.rpc_url,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if 'result' in result:
                return {
                    'success': True,
                    'status': result['result'],
                    'provider': 'helius'
                }
            else:
                logger.warning(f"Failed to get transaction status: {result.get('error')}")

                # Try fallback RPC if available
                if self.fallback_rpc_url:
                    try:
                        response = await self.http_client.post(
                            self.fallback_rpc_url,
                            json=payload
                        )
                        response.raise_for_status()
                        result = response.json()

                        if 'result' in result:
                            return {
                                'success': True,
                                'status': result['result'],
                                'provider': 'fallback'
                            }
                    except Exception as e:
                        logger.error(f"Error getting transaction status via fallback RPC: {str(e)}")

                return {
                    'success': False,
                    'error': result.get('error'),
                    'provider': None
                }
        except Exception as e:
            logger.error(f"Error getting transaction status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': None
            }

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get the SOL balance of an address.

        Args:
            address: Wallet address

        Returns:
            Dict containing the balance information
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }

        try:
            response = await self.http_client.post(
                self.rpc_url,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if 'result' in result:
                # Convert lamports to SOL
                balance_lamports = result['result']['value']
                balance_sol = balance_lamports / 1_000_000_000

                return {
                    'success': True,
                    'balance_lamports': balance_lamports,
                    'balance_sol': balance_sol,
                    'provider': 'helius'
                }
            else:
                logger.warning(f"Failed to get balance: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error'),
                    'provider': None
                }
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': None
            }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.

        Returns:
            Dict containing metrics data
        """
        self.metrics['last_updated'] = time.time()
        return self.metrics

    async def simulate_transaction(self,
                                transaction: str,
                                opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simulate a transaction.

        Args:
            transaction: Serialized transaction
            opts: Simulation options

        Returns:
            Dict containing simulation result
        """
        # Determine encoding from options
        encoding = opts.get('encoding', 'base58') if opts else 'base58'

        # Prepare request payload
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "simulateTransaction",
            "params": [
                transaction,
                {
                    "encoding": encoding,
                    "commitment": opts.get('commitment', 'confirmed') if opts else 'confirmed',
                    "sigVerify": opts.get('sig_verify', False) if opts else False,
                    "replaceRecentBlockhash": opts.get('replace_recent_blockhash', False) if opts else False,
                    "accounts": opts.get('accounts', None) if opts else None
                }
            ]
        }

        # Remove None values from params
        params_dict = payload["params"][1]
        payload["params"][1] = {k: v for k, v in params_dict.items() if v is not None}

        try:
            response = await self.http_client.post(
                self.rpc_url,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if 'result' in result:
                return {
                    'success': True,
                    'result': result['result'],
                    'provider': 'helius'
                }
            else:
                logger.warning(f"Failed to simulate transaction: {result.get('error')}")

                # Try fallback RPC if available
                if self.fallback_rpc_url:
                    try:
                        response = await self.http_client.post(
                            self.fallback_rpc_url,
                            json=payload
                        )
                        response.raise_for_status()
                        result = response.json()

                        if 'result' in result:
                            return {
                                'success': True,
                                'result': result['result'],
                                'provider': 'fallback'
                            }
                    except Exception as e:
                        logger.error(f"Error simulating transaction via fallback RPC: {str(e)}")

                return {
                    'success': False,
                    'error': result.get('error'),
                    'provider': None
                }
        except Exception as e:
            logger.error(f"Error simulating transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'provider': None
            }

    async def get_recent_blockhash(self) -> Optional[str]:
        """
        Get a recent blockhash.

        Returns:
            Recent blockhash or None if the call failed
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "confirmed"}]
        }

        try:
            response = await self.http_client.post(
                self.rpc_url,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if 'result' in result and 'value' in result['result'] and 'blockhash' in result['result']['value']:
                blockhash = result['result']['value']['blockhash']
                logger.info(f"Got recent blockhash: {blockhash}")
                return blockhash
            else:
                logger.warning(f"Failed to get recent blockhash: {result.get('error')}")

                # Try fallback RPC if available
                if self.fallback_rpc_url:
                    try:
                        response = await self.http_client.post(
                            self.fallback_rpc_url,
                            json=payload
                        )
                        response.raise_for_status()
                        result = response.json()

                        if 'result' in result and 'value' in result['result'] and 'blockhash' in result['result']['value']:
                            blockhash = result['result']['value']['blockhash']
                            logger.info(f"Got recent blockhash from fallback: {blockhash}")
                            return blockhash
                    except Exception as e:
                        logger.error(f"Error getting recent blockhash from fallback: {str(e)}")

                return None
        except Exception as e:
            logger.error(f"Error getting recent blockhash: {str(e)}")
            return None

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self.http_client.aclose()

async def main():
    """Main function to demonstrate the client."""
    # Example usage
    client = HeliusClient()

    # Example transaction (this is just a placeholder)
    example_tx = base58.b58encode(b"example_transaction").decode('utf-8')

    # Send transaction with base58 encoding
    result = await client.send_transaction(example_tx, {'encoding': 'base58'})
    print(f"Transaction result: {result}")

    # Example with base64 encoding
    example_tx_base64 = base64.b64encode(b"example_transaction").decode('utf-8')
    result_base64 = await client.send_transaction(example_tx_base64, {'encoding': 'base64'})
    print(f"Transaction result (base64): {result_base64}")

    # Get metrics
    metrics = client.get_metrics()
    print(f"Client metrics: {metrics}")

    # Close client
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
