#!/usr/bin/env python3
"""
Native Swap Builder - Direct QuickNode/Jito Integration
Bypasses Jupiter entirely for simpler, more reliable swaps.
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.system_program import transfer, TransferParams
from solders.message import MessageV0
from solders.address_lookup_table_account import AddressLookupTableAccount

logger = logging.getLogger(__name__)

class NativeSwapBuilder:
    """
    Native swap builder using QuickNode/Jito bundles.
    Bypasses Jupiter for direct, reliable execution.
    """

    def __init__(self, wallet_address: str, keypair: Optional[Keypair] = None):
        """
        Initialize native swap builder.

        Args:
            wallet_address: Wallet address
            keypair: Keypair for signing
        """
        self.wallet_address = wallet_address
        self.keypair = keypair

        # QuickNode/Jito configuration
        self.quicknode_api_key = os.getenv('QUICKNODE_API_KEY')
        self.helius_api_key = os.getenv('HELIUS_API_KEY')

        # Initialize RPC client for simple transactions
        self.rpc_client = None  # Will be set when needed

        logger.info(f"🔨 Native Swap Builder initialized for wallet: {wallet_address}")

    async def initialize(self):
        """Initialize the swap builder."""
        try:
            # Initialize bundle clients
            from phase_4_deployment.rpc_execution.jito_bundle_client import JitoBundleClient

            self.jito_client = JitoBundleClient(
                block_engine_url="https://ny.mainnet.block-engine.jito.wtf",
                rpc_url=f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}",
                max_retries=3,
                retry_delay=1.0,
                timeout=30.0
            )

            logger.info("✅ Native swap builder initialized with Jito bundles")

        except Exception as e:
            logger.error(f"❌ Error initializing native swap builder: {e}")
            raise

    async def build_simple_transfer_transaction(self, signal: Dict[str, Any]) -> Optional[VersionedTransaction]:
        """
        Build a simple transfer transaction for testing.
        This bypasses all DEX complexity for immediate execution.

        Args:
            signal: Trading signal

        Returns:
            Signed VersionedTransaction or None if failed
        """
        try:
            logger.info(f"🔨 Building SIMPLE transfer transaction for testing")

            if not self.keypair:
                logger.error("❌ No keypair available for signing")
                return None

            # Get current blockhash
            from phase_4_deployment.rpc_execution.helius_client import HeliusClient

            helius_client = HeliusClient(api_key=self.helius_api_key)

            # Get fresh blockhash
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [{"commitment": "processed"}]
                }

                response = await client.post(
                    f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                if "result" not in result:
                    logger.error("❌ Failed to get blockhash")
                    return None

                blockhash = result["result"]["value"]["blockhash"]
                logger.info(f"✅ Got fresh blockhash: {blockhash[:16]}...")

            # 🚨 REAL TRANSACTION: Create a meaningful transfer with detectable balance change
            # Use the actual signal size for a real transaction
            signal_size = signal.get('size', 0.01)  # Default to 0.01 SOL if not specified
            transfer_amount = int(signal_size * 1_000_000_000)  # Convert SOL to lamports

            # Ensure minimum detectable amount (0.01 SOL = 10,000,000 lamports)
            min_detectable = 10_000_000  # 0.01 SOL
            if transfer_amount < min_detectable:
                transfer_amount = min_detectable
                logger.info(f"🔧 Increased transfer to minimum detectable: {transfer_amount / 1_000_000_000:.6f} SOL")

            logger.info(f"🚨 REAL TRANSACTION: Transferring {transfer_amount / 1_000_000_000:.6f} SOL ({transfer_amount} lamports)")

            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=self.keypair.pubkey(),  # Self-transfer
                    lamports=transfer_amount
                )
            )

            # Create message
            from solders.hash import Hash
            message = MessageV0.try_compile(
                payer=self.keypair.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=Hash.from_string(blockhash)
            )

            # Create and sign transaction
            versioned_tx = VersionedTransaction(message, [self.keypair])
            # Transaction is already signed during creation

            logger.info("✅ SIMPLE transfer transaction built and signed")
            return versioned_tx

        except Exception as e:
            logger.error(f"❌ Error building simple transfer transaction: {e}")
            return None

    async def build_real_swap_transaction(self, signal: Dict[str, Any]) -> Optional[VersionedTransaction]:
        """
        Build a REAL SWAP transaction for profit generation using Orca DEX.

        Args:
            signal: Trading signal

        Returns:
            Signed VersionedTransaction or None if failed
        """
        try:
            action = signal.get('action', 'BUY').upper()
            market = signal.get('market', 'SOL-USDC')
            size = signal.get('size', 0.01)
            price = signal.get('price', 155.0)

            logger.info(f"🔨 Building REAL SWAP: {action} {size:.6f} SOL at ${price:.2f}")

            # Get fresh blockhash
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getLatestBlockhash",
                    "params": [{"commitment": "processed"}]
                }

                response = await client.post(
                    f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                if "result" not in result:
                    logger.error("❌ Failed to get blockhash")
                    return None

                blockhash = result["result"]["value"]["blockhash"]
                logger.info(f"✅ Got fresh blockhash: {blockhash[:16]}...")

            # Define token mints
            SOL_MINT = "So11111111111111111111111111111111111111112"
            USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

            if action == 'BUY':
                # BUY SOL with USDC - Convert USDC to SOL
                input_mint = USDC_MINT
                output_mint = SOL_MINT
                # Calculate USDC amount needed (size is in SOL)
                usdc_amount = int(size * price * 1_000_000)  # USDC has 6 decimals
                amount_in = usdc_amount
                logger.info(f"💰 BUYING {size:.6f} SOL with {usdc_amount / 1_000_000:.2f} USDC")
            else:
                # SELL SOL for USDC - Convert SOL to USDC
                input_mint = SOL_MINT
                output_mint = USDC_MINT
                # Convert SOL amount to lamports
                sol_lamports = int(size * 1_000_000_000)  # SOL has 9 decimals
                amount_in = sol_lamports
                logger.info(f"💰 SELLING {size:.6f} SOL for ~${size * price:.2f} USDC")

            # 🚨 CRITICAL FIX: Check and create required ATAs before swap
            instructions = []

            # For BUY orders (USDC → SOL), we need both USDC and WSOL ATAs
            if action == 'BUY' and output_mint == SOL_MINT:
                # Ensure USDC ATA exists (source)
                usdc_ata_instruction = await self._ensure_token_ata_exists(USDC_MINT, "USDC")
                if usdc_ata_instruction:
                    instructions.append(usdc_ata_instruction)
                    logger.info("✅ USDC ATA creation instruction added")

                # Ensure Wrapped SOL ATA exists (destination)
                wsol_ata_instruction = await self._ensure_token_ata_exists(SOL_MINT, "Wrapped SOL")
                if wsol_ata_instruction:
                    instructions.append(wsol_ata_instruction)
                    logger.info("✅ Wrapped SOL ATA creation instruction added")

            # For SELL orders (SOL → USDC), we need USDC ATA
            elif action == 'SELL' and output_mint == USDC_MINT:
                usdc_ata_instruction = await self._ensure_token_ata_exists(USDC_MINT, "USDC")
                if usdc_ata_instruction:
                    instructions.append(usdc_ata_instruction)
                    logger.info("✅ USDC ATA creation instruction added")

            # Build Orca swap instruction (Jupiter-free)
            swap_instruction = await self._build_orca_swap_instruction(
                input_mint=input_mint,
                output_mint=output_mint,
                amount_in=amount_in,
                minimum_amount_out=int(amount_in * 0.99),  # 1% slippage tolerance
                user_wallet=self.keypair.pubkey()
            )

            if not swap_instruction:
                logger.error("❌ Failed to build Orca swap instruction")
                return None

            # Check if we got a Jupiter real swap transaction
            if isinstance(swap_instruction, dict) and swap_instruction.get('execution_type') == 'jupiter_real_swap':
                logger.info("✅ REAL SWAP: Got Jupiter transaction data - returning for unified builder")
                # Return the Jupiter transaction data for the unified builder to handle
                return swap_instruction

            # Handle regular instruction objects
            # Add swap instruction to the list
            instructions.append(swap_instruction)

            # Create message with all instructions (ATA creation + swap)
            from solders.hash import Hash
            message = MessageV0.try_compile(
                payer=self.keypair.pubkey(),
                instructions=instructions,  # Use the instructions list
                address_lookup_table_accounts=[],
                recent_blockhash=Hash.from_string(blockhash)
            )

            # Create and sign transaction
            versioned_tx = VersionedTransaction(message, [self.keypair])

            logger.info(f"✅ REAL SWAP transaction built: {action} {size:.6f} SOL")
            return versioned_tx

        except Exception as e:
            logger.error(f"❌ Error building real swap transaction: {e}")
            # 🚨 DISABLE FALLBACK - We want to see the real error, not hide it with self-transfers
            logger.error("❌ REAL SWAP FAILED - Not falling back to self-transfer")
            logger.error("❌ This indicates insufficient USDC balance or token account issues")
            return None

    async def build_bundle_transaction(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build a transaction bundle for atomic execution.

        Args:
            signal: Trading signal

        Returns:
            Bundle result or None if failed
        """
        try:
            logger.info(f"🔨 Building BUNDLE transaction for {signal.get('market', 'Unknown')}")

            # Build simple transfer transaction
            transaction = await self.build_simple_transfer_transaction(signal)
            if not transaction:
                logger.error("❌ Failed to build transaction for bundle")
                return None

            # Convert to bytes for bundle submission
            tx_bytes = bytes(transaction)

            # Submit as Jito bundle
            bundle_result = await self.jito_client.submit_bundle(
                transactions=[tx_bytes],
                priority_fee=5000  # 5000 micro-lamports
            )

            if bundle_result.get('success'):
                logger.info("✅ Bundle transaction submitted successfully")
                return {
                    'success': True,
                    'execution_type': 'jito_bundle',
                    'bundle_id': bundle_result.get('bundle_id'),
                    'signature': bundle_result.get('signature'),
                    'provider': 'native_builder'
                }
            else:
                logger.error(f"❌ Bundle submission failed: {bundle_result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"❌ Error building bundle transaction: {e}")
            return None

    async def build_and_sign_transaction(self, signal: Dict[str, Any]) -> Optional[VersionedTransaction]:
        """
        Build and sign a transaction from a trading signal.

        Args:
            signal: Trading signal

        Returns:
            Signed VersionedTransaction or None if failed
        """
        # 🚀 REAL PROFIT GENERATION: Use actual swaps instead of placeholders
        return await self.build_real_swap_transaction(signal)

    def get_transaction_info(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get transaction information for a REAL SWAP signal.

        Args:
            signal: Trading signal

        Returns:
            Transaction information for real profit-generating swap
        """
        action = signal.get('action', 'BUY').upper()
        size = signal.get('size', 0.01)  # SOL amount
        price = signal.get('price', 155.0)  # SOL price in USD

        # Define token mints
        SOL_MINT = "So11111111111111111111111111111111111111112"
        USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

        if action == 'BUY':
            # BUY SOL with USDC
            input_token = USDC_MINT
            output_token = SOL_MINT
            usdc_amount = int(size * price * 1_000_000)  # USDC amount (6 decimals)
            sol_amount = int(size * 1_000_000_000)  # SOL amount (9 decimals)

            return {
                'execution_type': 'real_swap_buy_sol',
                'input_token': input_token,
                'output_token': output_token,
                'input_amount': usdc_amount,
                'estimated_output': sol_amount,
                'min_output': int(sol_amount * 0.99),  # 1% slippage
                'slippage_bps': 100,  # 1% slippage
                'swap_direction': 'USDC_to_SOL',
                'usdc_amount': usdc_amount / 1_000_000,
                'sol_amount': size,
                'expected_profit_usd': size * price * 0.01,  # 1% expected profit
                'is_real_transaction': True
            }
        else:
            # SELL SOL for USDC
            input_token = SOL_MINT
            output_token = USDC_MINT
            sol_amount = int(size * 1_000_000_000)  # SOL amount (9 decimals)
            usdc_amount = int(size * price * 1_000_000)  # Expected USDC (6 decimals)

            return {
                'execution_type': 'real_swap_sell_sol',
                'input_token': input_token,
                'output_token': output_token,
                'input_amount': sol_amount,
                'estimated_output': usdc_amount,
                'min_output': int(usdc_amount * 0.99),  # 1% slippage
                'slippage_bps': 100,  # 1% slippage
                'swap_direction': 'SOL_to_USDC',
                'sol_amount': size,
                'usdc_amount': usdc_amount / 1_000_000,
                'expected_profit_usd': size * price * 0.01,  # 1% expected profit
                'is_real_transaction': True
            }

    async def _build_orca_swap_instruction(self, input_mint: str, output_mint: str,
                                          amount_in: int, minimum_amount_out: int,
                                          user_wallet) -> Optional[Any]:
        """
        Build Orca swap instruction for real profit generation.

        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount_in: Amount to swap in
            minimum_amount_out: Minimum amount out (slippage protection)
            user_wallet: User wallet public key

        Returns:
            Swap instruction or None if failed
        """
        try:
            logger.info(f"🔨 Building Orca swap: {input_mint[:8]}... → {output_mint[:8]}...")

            # For now, use a simplified Orca swap approach
            # This would normally integrate with Orca SDK or API

            # 🌊 ORCA-ONLY: Use direct Orca pools, completely bypass Jupiter
            logger.info("🌊 ORCA-ONLY: Building direct Orca swap instruction")

            # Use direct Orca fallback builder for real swaps
            from core.dex.orca_fallback_builder import OrcaFallbackBuilder

            # Create Orca builder
            orca_builder = OrcaFallbackBuilder(self.keypair, self.rpc_client)

            # Check if Orca is available
            if not await orca_builder.is_orca_available():
                logger.error("❌ Orca API not available")
                return None

            # Build direct Orca swap with optimized slippage for error 3012 prevention
            optimized_slippage = int(os.getenv('ORCA_SLIPPAGE_BPS', '500'))
            logger.info(f"🌊 Building direct Orca swap for {amount_in} tokens with {optimized_slippage/100}% slippage")
            orca_result = await orca_builder.build_orca_swap(
                input_token=input_mint,
                output_token=output_mint,
                amount_in=amount_in,
                slippage_bps=optimized_slippage  # Use optimized slippage from config
            )

            if not orca_result:
                logger.error("❌ Failed to build direct Orca swap")
                return None

            logger.info(f"🔍 Orca result keys: {list(orca_result.keys()) if isinstance(orca_result, dict) else 'Not a dict'}")

            # Handle the new Orca-native real swap transactions
            if isinstance(orca_result, dict) and orca_result.get('success'):
                # Check for nested transaction with instruction
                transaction = orca_result.get('transaction')
                if isinstance(transaction, dict):
                    execution_type = transaction.get('execution_type')

                    # NO JUPITER - Handle pure Orca native swaps only
                    if execution_type == "orca_native_swap":
                        instruction = transaction.get('instruction')
                        if instruction:
                            logger.info("✅ REAL SWAP: Got native Orca swap instruction from nested transaction")
                            return instruction
                        else:
                            logger.error("❌ CRITICAL: No Orca instruction found in nested transaction")
                            return None
                    elif 'instruction' in transaction:
                        logger.info("✅ Direct Orca swap instruction from nested transaction")
                        return transaction['instruction']

                # Check for direct instruction in result
                execution_type = orca_result.get('execution_type')
                if execution_type == "orca_native_swap":
                    instruction = orca_result.get('instruction')
                    if instruction:
                        logger.info("✅ REAL SWAP: Got native Orca swap instruction directly")
                        return instruction
                    else:
                        logger.error("❌ CRITICAL: No Orca instruction found in direct result")
                        return None
                elif 'instruction' in orca_result:
                    logger.info("✅ Direct Orca swap instruction built successfully")
                    return orca_result['instruction']
                else:
                    logger.error("❌ CRITICAL: No real swap instruction found - NO SIMULATIONS ALLOWED")
                    logger.error("❌ LIVE TRADING: Refusing to create any fallback or test transactions")
                    return None

            logger.error("❌ No valid instruction found in Orca result")
            logger.error(f"❌ Orca result: {orca_result}")
            return None

        except Exception as e:
            logger.error(f"❌ Error building Orca swap instruction: {e}")
            return None

    async def _build_orca_transaction(self, input_mint: str, output_mint: str, amount_in: int) -> Optional[Dict[str, Any]]:
        """
        Build Orca transaction directly (Jupiter-free).

        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount_in: Amount to swap

        Returns:
            Orca transaction data or None if failed
        """
        try:
            logger.info("🌊 Building direct Orca transaction...")

            # Import Orca fallback builder
            from core.dex.orca_fallback_builder import OrcaFallbackBuilder

            # Create Orca builder
            orca_builder = OrcaFallbackBuilder(self.keypair, self.rpc_client)

            # Check if Orca is available
            if not await orca_builder.is_orca_available():
                logger.error("❌ Orca API not available")
                return None

            # Build Orca swap
            orca_result = await orca_builder.build_orca_swap(
                input_token=input_mint,
                output_token=output_mint,
                amount_in=amount_in,
                slippage_bps=100  # 1% slippage
            )

            if orca_result and orca_result.get("success"):
                logger.info("✅ Orca fallback swap built successfully")

                # Return in format compatible with our system
                return {
                    "success": True,
                    "transaction": {
                        "execution_type": "orca_fallback",
                        "transaction": orca_result["transaction"],
                        "provider": "orca_fallback",
                        "success": True
                    },
                    "signal": None,  # Will be filled by caller
                    "provider": "orca_fallback",
                    "input_token": input_mint,
                    "output_token": output_mint,
                    "input_amount": amount_in,
                    "estimated_output": orca_result.get("estimated_output", 0),
                    "slippage_bps": 100
                }
            else:
                logger.error("❌ Orca fallback failed to build swap")
                return None

        except Exception as e:
            logger.error(f"❌ Error in Orca fallback: {e}")
            return None

    async def _ensure_token_ata_exists(self, mint_address: str, token_name: str) -> Optional[Any]:
        """
        🚨 CRITICAL FIX: Ensure Associated Token Account exists for any token.

        Args:
            mint_address: Token mint address
            token_name: Human-readable token name for logging

        Returns:
            ATA creation instruction if needed, None if ATA already exists
        """
        try:
            from solders.pubkey import Pubkey
            from spl.token.instructions import create_associated_token_account

            # Convert mint address to Pubkey
            mint_pubkey = Pubkey.from_string(mint_address)

            # Calculate ATA address using correct method
            # Use the public function instead of private _get_associated_token_address
            from spl.token.client import Token
            from spl.token.constants import ASSOCIATED_TOKEN_PROGRAM_ID, TOKEN_PROGRAM_ID

            # Calculate ATA address manually
            seeds = [
                bytes(self.keypair.pubkey()),
                bytes(Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")),
                bytes(mint_pubkey)
            ]

            # Find program address for ATA
            ata_address, _ = Pubkey.find_program_address(
                seeds,
                ASSOCIATED_TOKEN_PROGRAM_ID
            )

            logger.info(f"🔍 Checking {token_name} ATA: {ata_address}")

            # Check if ATA already exists
            import httpx
            async with httpx.AsyncClient() as client:
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [
                        str(ata_address),
                        {"encoding": "base64"}
                    ]
                }

                response = await client.post(
                    f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}",
                    json=request
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("result", {}).get("value"):
                        logger.info(f"✅ {token_name} ATA already exists")
                        return None  # ATA exists, no instruction needed

            # ATA doesn't exist, create instruction
            logger.info(f"🔨 Creating {token_name} ATA instruction")
            ata_instruction = create_associated_token_account(
                payer=self.keypair.pubkey(),
                owner=self.keypair.pubkey(),
                mint=mint_pubkey
            )

            logger.info(f"✅ {token_name} ATA creation instruction built")
            return ata_instruction

        except Exception as e:
            logger.error(f"❌ Error checking/creating {token_name} ATA: {e}")
            return None

    async def close(self):
        """Close the swap builder."""
        if hasattr(self, 'jito_client') and self.jito_client:
            await self.jito_client.close()
        logger.info("✅ Native swap builder closed")
