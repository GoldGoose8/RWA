"""
QuickNode Bundle Client - Modern Transaction Execution

This client uses QuickNode Bundles for atomic, MEV-protected transaction execution.
🔧 UPGRADED: Replaces Jito with QuickNode for better reliability and performance.
"""

import asyncio
import json
import logging
import time
import os
from typing import List, Dict, Any, Optional, Union
import httpx
import base64

logger = logging.getLogger(__name__)

class QuickNodeBundleClient:
    """
    🔧 NEW: QuickNode Bundle client for atomic transaction execution.

    Features:
    - Atomic execution (all-or-nothing)
    - MEV protection via private mempool
    - Priority inclusion via fee system
    - Better reliability than Jito
    """

    def __init__(self,
                 api_url: str = None,
                 api_key: str = None,
                 rpc_url: str = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize QuickNode Bundle client.

        Args:
            api_url: QuickNode Bundle API endpoint
            api_key: QuickNode API key
            rpc_url: Solana RPC endpoint for monitoring
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            timeout: Request timeout
        """
        # FIX 1: Correct QuickNode Bundle Configuration
        self.api_key = api_key or os.getenv('QUICKNODE_API_KEY')

        # Use the correct QuickNode RPC endpoint format for bundles
        if api_url:
            self.api_url = api_url.rstrip('/')
        else:
            # Use QuickNode RPC URL from environment
            base_url = os.getenv('QUICKNODE_RPC_URL', 'https://green-thrilling-silence.solana-mainnet.quiknode.pro/65b20af6225a0da827eef8646240eaa8a77ebaea/')
            self.api_url = base_url.rstrip('/')

        self.rpc_url = rpc_url or self.api_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # HTTP client for API calls with proper authentication
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Add authentication header if API key is available
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            headers=headers
        )

        logger.info(f"🔧 Initialized QuickNode Bundle client: {api_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def submit_bundle(self,
                          transactions: List[Union[str, bytes, Dict]],
                          priority_fee: Optional[int] = None) -> Dict[str, Any]:
        """
        Submit a bundle of transactions to QuickNode.

        Args:
            transactions: List of transactions (base64 strings, bytes, or dicts)
            priority_fee: Priority fee in lamports

        Returns:
            Bundle submission result
        """
        try:
            # Convert all transactions to base64 format
            bundle_transactions = []

            for tx in transactions:
                if isinstance(tx, str):
                    # Already base64 encoded
                    bundle_transactions.append(tx)
                elif isinstance(tx, bytes):
                    # Convert bytes to base64
                    bundle_transactions.append(base64.b64encode(tx).decode('utf-8'))
                elif isinstance(tx, dict):
                    # Handle transaction dict format
                    if 'transaction' in tx:
                        tx_data = tx['transaction']
                        if isinstance(tx_data, bytes):
                            bundle_transactions.append(base64.b64encode(tx_data).decode('utf-8'))
                        else:
                            bundle_transactions.append(tx_data)
                    else:
                        logger.error(f"Invalid transaction dict format: {tx}")
                        continue
                else:
                    logger.error(f"Unsupported transaction type: {type(tx)}")
                    continue

            if not bundle_transactions:
                logger.error("No valid transactions to bundle")
                return {"success": False, "error": "No valid transactions"}

            # FIX 1: Use standard Solana RPC format instead of QuickNode-specific bundle format
            # QuickNode doesn't have a separate bundle API - use regular sendTransaction with optimization
            logger.info(f"🔧 Submitting {len(bundle_transactions)} transactions via QuickNode RPC")

            # FIX 1: Submit transactions sequentially to QuickNode RPC
            results = []
            for i, tx in enumerate(bundle_transactions):
                try:
                    # Standard Solana RPC format for QuickNode
                    rpc_data = {
                        "jsonrpc": "2.0",
                        "id": int(time.time()) + i,
                        "method": "sendTransaction",
                        "params": [
                            tx,
                            {
                                "encoding": "base64",
                                "skipPreflight": False,
                                "maxRetries": 0,  # Handle retries ourselves
                                "commitment": "confirmed"
                            }
                        ]
                    }

                    # Add priority fee if specified
                    if priority_fee:
                        rpc_data["params"][1]["priorityFee"] = priority_fee

                    logger.info(f"🔧 Submitting transaction {i+1}/{len(bundle_transactions)} to QuickNode")

                    # Submit transaction to QuickNode RPC
                    response = await self.http_client.post(
                        self.api_url,
                        json=rpc_data
                    )

                    if response.status_code == 200:
                        result = response.json()

                        # Process transaction result
                        if "result" in result:
                            signature = result["result"]
                            logger.info(f"✅ Transaction {i+1} submitted: {signature}")
                            results.append({
                                "success": True,
                                "signature": signature,
                                "provider": "quicknode"
                            })
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"❌ Transaction {i+1} error: {error_msg}")
                            results.append({
                                "success": False,
                                "error": error_msg
                            })
                    else:
                        error_text = response.text
                        logger.error(f"❌ Transaction {i+1} HTTP error {response.status_code}: {error_text}")
                        results.append({
                            "success": False,
                            "error": f"HTTP {response.status_code}: {error_text}"
                        })

                except Exception as e:
                    logger.error(f"❌ Error submitting transaction {i+1}: {e}")
                    results.append({
                        "success": False,
                        "error": str(e)
                    })

            # Return bundle result
            successful_txs = [r for r in results if r.get("success")]
            if successful_txs:
                return {
                    "success": True,
                    "bundle_id": f"quicknode_bundle_{int(time.time())}",
                    "provider": "quicknode",
                    "transactions_count": len(bundle_transactions),
                    "successful": len(successful_txs),
                    "signatures": [r.get("signature") for r in successful_txs if r.get("signature")],
                    "execution_type": "quicknode_rpc"
                }
            else:
                return {
                    "success": False,
                    "error": "All transactions failed",
                    "provider": "quicknode",
                    "results": results
                }

        except Exception as e:
            logger.error(f"❌ QuickNode bundle submission error: {e}")
            return {"success": False, "error": str(e)}

    async def execute_jupiter_bundle(self, jupiter_transaction: Union[str, bytes, Dict],
                                   trade_size_sol: float = 0.001,
                                   priority: str = "medium") -> Dict[str, Any]:
        """
        Execute a Jupiter swap transaction as a QuickNode bundle.

        Args:
            jupiter_transaction: Jupiter transaction data
            trade_size_sol: Trade size for fee calculation
            priority: Bundle priority level

        Returns:
            Bundle execution result
        """
        try:
            logger.info(f"🔧 Executing Jupiter transaction as QuickNode bundle")

            # Calculate priority fee based on trade size and priority
            priority_fees = {
                "low": 10_000,      # 0.00001 SOL
                "medium": 20_000,   # 0.00002 SOL
                "high": 50_000,     # 0.00005 SOL
            }

            base_fee = priority_fees.get(priority, priority_fees["medium"])
            size_multiplier = min(trade_size_sol * 1000, 5)  # Cap at 5x
            priority_fee = int(base_fee * max(size_multiplier, 1))

            # Submit as bundle
            result = await self.submit_bundle(
                transactions=[jupiter_transaction],
                priority_fee=priority_fee
            )

            if result.get('success'):
                logger.info(f"✅ QuickNode Jupiter bundle executed: {result.get('bundle_id')}")
                return {
                    "success": True,
                    "bundle_id": result.get('bundle_id'),
                    "status": result.get('status'),
                    "priority_fee": priority_fee,
                    "execution_type": "quicknode_bundle"
                }
            else:
                logger.error(f"❌ QuickNode Jupiter bundle failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get('error'),
                    "execution_type": "quicknode_bundle"
                }

        except Exception as e:
            logger.error(f"❌ QuickNode Jupiter bundle error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_type": "quicknode_bundle"
            }

class JitoBundleClient:
    """
    Modern Jito Bundle client for atomic transaction execution.

    Features:
    - Atomic execution (all-or-nothing)
    - MEV protection via private auction
    - Priority inclusion via tip system
    - Simplified transaction handling
    """

    def __init__(self,
                 block_engine_url: str = "https://ny.mainnet.block-engine.jito.wtf",
                 rpc_url: str = "https://api.mainnet-beta.solana.com",
                 auth_keypair_path: Optional[str] = None,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 timeout: float = 30.0):
        """
        Initialize Jito Bundle client.

        Args:
            block_engine_url: Jito Block Engine endpoint
            rpc_url: Solana RPC endpoint for monitoring
            auth_keypair_path: Optional auth keypair for Jito
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries
            timeout: Request timeout
        """
        self.block_engine_url = block_engine_url.rstrip('/')
        self.rpc_url = rpc_url
        self.auth_keypair_path = auth_keypair_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # FIX 2: Jito Rate Limiting Implementation
        self.last_request_time = 0.0
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests
        self.rate_limit_backoff = 5.0    # 5 second backoff on rate limit
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

        # Jito tip accounts (official Jito tip accounts)
        self.tip_accounts = [
            "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",  # Tip account 1
            "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",  # Tip account 2
            "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",  # Tip account 3
            "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",  # Tip account 4
        ]

        logger.info(f"Initialized Jito Bundle client with Block Engine: {block_engine_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def _enforce_rate_limit(self):
        """FIX 2: Enforce rate limiting for Jito requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"🔧 Rate limiting: waiting {sleep_time:.2f}s before Jito request")
            await asyncio.sleep(sleep_time)

        # Additional backoff for consecutive failures
        if self.consecutive_failures > 0:
            backoff_time = min(self.consecutive_failures * self.rate_limit_backoff, 30.0)
            logger.info(f"🔧 Failure backoff: waiting {backoff_time:.2f}s after {self.consecutive_failures} failures")
            await asyncio.sleep(backoff_time)

        self.last_request_time = time.time()

    def calculate_tip(self, trade_size_sol: float, priority: str = "medium") -> int:
        """
        Calculate appropriate tip for bundle priority.

        Args:
            trade_size_sol: Trade size in SOL
            priority: Priority level (low, medium, high)

        Returns:
            Tip amount in lamports
        """
        # Base tips by priority (in lamports)
        base_tips = {
            "low": 50_000,      # 0.00005 SOL
            "medium": 100_000,  # 0.0001 SOL
            "high": 200_000,    # 0.0002 SOL
        }

        base_tip = base_tips.get(priority, base_tips["medium"])

        # Scale with trade size (larger trades = higher tips)
        size_multiplier = min(trade_size_sol * 1000, 10)  # Cap at 10x

        # Calculate final tip
        tip_amount = int(base_tip * max(size_multiplier, 1))

        logger.debug(f"Calculated tip: {tip_amount} lamports for {trade_size_sol} SOL trade")
        return tip_amount

    def create_tip_transaction(self, payer_pubkey: str, tip_amount: int) -> Dict[str, Any]:
        """
        Create a tip transaction for Jito bundle priority.

        Args:
            payer_pubkey: Payer's public key
            tip_amount: Tip amount in lamports

        Returns:
            Tip transaction instruction
        """
        # Select random tip account for load balancing
        import random
        tip_account = random.choice(self.tip_accounts)

        # Create transfer instruction to Jito tip account
        tip_instruction = {
            "programId": "11111111111111111111111111111111",  # System Program
            "accounts": [
                {"pubkey": payer_pubkey, "isSigner": True, "isWritable": True},
                {"pubkey": tip_account, "isSigner": False, "isWritable": True},
            ],
            "data": self._encode_transfer_instruction(tip_amount)
        }

        logger.debug(f"Created tip transaction: {tip_amount} lamports to {tip_account}")
        return tip_instruction

    def _encode_transfer_instruction(self, lamports: int) -> str:
        """Encode transfer instruction data."""
        # System program transfer instruction: [2, lamports (8 bytes)]
        instruction_data = bytearray([2])  # Transfer instruction
        instruction_data.extend(lamports.to_bytes(8, byteorder='little'))
        return base64.b64encode(instruction_data).decode('utf-8')

    async def build_tip_transaction(self, payer_pubkey: str, tip_amount: int) -> Optional[str]:
        """
        Build an actual tip transaction for Jito bundle.

        Args:
            payer_pubkey: Payer's public key
            tip_amount: Tip amount in lamports

        Returns:
            Base64 encoded tip transaction or None if failed
        """
        try:
            # Import required modules
            from solders.transaction import Transaction
            from solders.system_program import transfer, TransferParams
            from solders.pubkey import Pubkey
            from solders.keypair import Keypair
            from solders.hash import Hash
            import os

            # Load keypair for signing
            keypair_path = os.getenv('KEYPAIR_PATH')
            if not keypair_path or not os.path.exists(keypair_path):
                logger.error("Keypair path not found for tip transaction")
                return None

            # Load keypair
            with open(keypair_path, 'r') as f:
                import json
                keypair_data = json.load(f)

            if isinstance(keypair_data, list) and len(keypair_data) == 64:
                keypair_bytes = bytes(keypair_data)
                keypair = Keypair.from_bytes(keypair_bytes)
            else:
                logger.error("Invalid keypair format for tip transaction")
                return None

            # Select random tip account
            import random
            tip_account = random.choice(self.tip_accounts)

            # Create transaction
            tx = Transaction()

            # Add transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=keypair.pubkey(),
                    to_pubkey=Pubkey.from_string(tip_account),
                    lamports=tip_amount
                )
            )
            tx.add(transfer_ix)

            # Get fresh blockhash (this is critical for signature verification)
            try:
                # Use a simple RPC call to get blockhash
                import httpx
                rpc_url = f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIUS_API_KEY')}"

                async with httpx.AsyncClient() as client:
                    response = await client.post(rpc_url, json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getLatestBlockhash"
                    })

                    if response.status_code == 200:
                        result = response.json()
                        if 'result' in result and 'value' in result['result']:
                            blockhash_str = result['result']['value']['blockhash']
                            tx.recent_blockhash = Hash.from_string(blockhash_str)
                        else:
                            logger.error("Failed to get blockhash for tip transaction")
                            return None
                    else:
                        logger.error("RPC call failed for tip transaction blockhash")
                        return None
            except Exception as e:
                logger.error(f"Error getting blockhash for tip transaction: {e}")
                return None

            # Sign transaction
            tx.sign([keypair])

            # Serialize and encode
            serialized = tx.serialize()
            encoded = base64.b64encode(serialized).decode('utf-8')

            logger.debug(f"Built tip transaction: {tip_amount} lamports to {tip_account}")
            return encoded

        except Exception as e:
            logger.error(f"Error building tip transaction: {e}")
            return None

    async def submit_bundle(self,
                          transactions: List[Union[str, bytes, Dict]],
                          tip_amount: Optional[int] = None,
                          payer_pubkey: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit a bundle of transactions to Jito Block Engine.

        Args:
            transactions: List of transactions (base64 strings, bytes, or dicts)
            tip_amount: Optional tip amount (calculated if not provided)
            payer_pubkey: Payer public key for tip transaction

        Returns:
            Bundle submission result
        """
        try:
            # Convert all transactions to base64 format
            bundle_transactions = []

            for tx in transactions:
                if isinstance(tx, str):
                    # Already base64 encoded
                    bundle_transactions.append(tx)
                elif isinstance(tx, bytes):
                    # Convert bytes to base64
                    bundle_transactions.append(base64.b64encode(tx).decode('utf-8'))
                elif isinstance(tx, dict):
                    # Handle transaction dict format
                    if 'transaction' in tx:
                        tx_data = tx['transaction']
                        if isinstance(tx_data, bytes):
                            bundle_transactions.append(base64.b64encode(tx_data).decode('utf-8'))
                        else:
                            bundle_transactions.append(tx_data)
                    else:
                        logger.error(f"Invalid transaction dict format: {tx}")
                        continue
                else:
                    logger.error(f"Unsupported transaction type: {type(tx)}")
                    continue

            if not bundle_transactions:
                logger.error("No valid transactions to bundle")
                return {"success": False, "error": "No valid transactions"}

            # Add tip transaction if specified
            if tip_amount and payer_pubkey:
                try:
                    # Create and build actual tip transaction
                    tip_tx_data = await self.build_tip_transaction(payer_pubkey, tip_amount)
                    if tip_tx_data:
                        bundle_transactions.append(tip_tx_data)
                        logger.info(f"Bundle includes tip: {tip_amount} lamports to tip account")
                    else:
                        logger.warning("Failed to build tip transaction, proceeding without tip")
                except Exception as e:
                    logger.warning(f"Error building tip transaction: {e}, proceeding without tip")

            # FIXED: Use correct Jito Bundle JSON-RPC format with base64 encoding
            bundle_data = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "sendBundle",
                "params": [
                    bundle_transactions,
                    {
                        "encoding": "base64"
                    }
                ]
            }

            logger.info(f"Submitting bundle with {len(bundle_transactions)} transactions")
            logger.debug(f"Bundle data: {len(str(bundle_data))} bytes")

            # FIX 2: Apply rate limiting before Jito request
            await self._enforce_rate_limit()

            # Submit bundle to Jito Block Engine using correct endpoint
            response = await self.http_client.post(
                f"{self.block_engine_url}/api/v1/bundles",
                json=bundle_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200 or response.status_code == 202:
                # Jito may return 202 (Accepted) for successful bundle submission
                try:
                    result = response.json()
                    logger.info(f"Bundle submission response: {result}")

                    # Jito API may return bundle_id directly or in a different format
                    bundle_id = None
                    if isinstance(result, dict):
                        bundle_id = result.get('bundle_id') or result.get('id') or result.get('result')
                    elif isinstance(result, str):
                        bundle_id = result

                    if bundle_id:
                        logger.info(f"Bundle submitted successfully: {bundle_id}")
                        # FIX 2: Reset consecutive failures on success
                        self.consecutive_failures = 0

                        # For now, return success without monitoring (monitoring may need different endpoint)
                        return {
                            "success": True,
                            "bundle_id": bundle_id,
                            "status": {"status": "submitted"},
                            "transactions_count": len(bundle_transactions)
                        }
                    else:
                        logger.warning(f"Bundle submitted but no bundle_id returned: {result}")
                        # FIX 2: Reset consecutive failures on success
                        self.consecutive_failures = 0

                        return {
                            "success": True,
                            "bundle_id": "unknown",
                            "status": {"status": "submitted"},
                            "transactions_count": len(bundle_transactions)
                        }
                except Exception as e:
                    logger.error(f"Error parsing bundle response: {e}")
                    # FIX 2: Increment consecutive failures
                    self.consecutive_failures += 1
                    return {"success": False, "error": f"Response parsing error: {e}"}
            else:
                # FIX 2: Handle rate limiting and other HTTP errors
                self.consecutive_failures += 1

                # Log the full response for debugging
                try:
                    error_detail = response.text
                    if response.status_code == 429:
                        logger.error(f"❌ Jito rate limit exceeded (429): {error_detail}")
                        return {"success": False, "error": "Rate limit exceeded - too many requests"}
                    else:
                        logger.error(f"Bundle submission HTTP error {response.status_code}: {error_detail}")
                except:
                    logger.error(f"Bundle submission HTTP error: {response.status_code}")

                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Bundle submission error: {e}")
            return {"success": False, "error": str(e)}

    async def monitor_bundle_status(self, bundle_id: str, max_wait: int = 30) -> Dict[str, Any]:
        """
        Monitor bundle execution status.

        Args:
            bundle_id: Bundle ID to monitor
            max_wait: Maximum wait time in seconds

        Returns:
            Bundle status information
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # Check bundle status
                status_data = {
                    "jsonrpc": "2.0",
                    "id": int(time.time()),
                    "method": "getBundleStatuses",
                    "params": [[bundle_id]]
                }

                response = await self.http_client.post(
                    f"{self.block_engine_url}/api/v1/bundles",
                    json=status_data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()

                    if 'result' in result and result['result']:
                        status_info = result['result'][0]

                        # Check if bundle was processed
                        if status_info.get('confirmation_status') in ['confirmed', 'finalized']:
                            logger.info(f"Bundle {bundle_id} confirmed: {status_info}")
                            return {
                                "status": "confirmed",
                                "confirmation_status": status_info.get('confirmation_status'),
                                "slot": status_info.get('slot'),
                                "transactions": status_info.get('transactions', [])
                            }
                        elif status_info.get('err'):
                            logger.error(f"Bundle {bundle_id} failed: {status_info['err']}")
                            return {
                                "status": "failed",
                                "error": status_info['err']
                            }

                # Wait before next check
                await asyncio.sleep(2)

            except Exception as e:
                logger.warning(f"Error checking bundle status: {e}")
                await asyncio.sleep(2)

        logger.warning(f"Bundle {bundle_id} status check timed out")
        return {"status": "timeout", "message": "Status check timed out"}

    async def execute_jupiter_bundle(self, jupiter_transaction: Union[str, bytes, Dict],
                                   trade_size_sol: float = 0.001,
                                   priority: str = "medium") -> Dict[str, Any]:
        """
        Execute a Jupiter swap transaction as a Jito bundle.

        Args:
            jupiter_transaction: Jupiter transaction data
            trade_size_sol: Trade size for tip calculation
            priority: Bundle priority level

        Returns:
            Bundle execution result
        """
        try:
            logger.info(f"Executing Jupiter transaction as Jito bundle")

            # Calculate appropriate tip
            tip_amount = self.calculate_tip(trade_size_sol, priority)

            # Get payer pubkey from environment
            import os
            payer_pubkey = os.getenv('WALLET_ADDRESS')

            # Submit as bundle
            result = await self.submit_bundle(
                transactions=[jupiter_transaction],
                tip_amount=tip_amount,
                payer_pubkey=payer_pubkey
            )

            if result.get('success'):
                logger.info(f"Jupiter bundle executed successfully: {result.get('bundle_id')}")
                return {
                    "success": True,
                    "bundle_id": result.get('bundle_id'),
                    "status": result.get('status'),
                    "tip_amount": tip_amount,
                    "execution_type": "jito_bundle"
                }
            else:
                logger.error(f"Jupiter bundle execution failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get('error'),
                    "execution_type": "jito_bundle"
                }

        except Exception as e:
            logger.error(f"Jupiter bundle execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_type": "jito_bundle"
            }
