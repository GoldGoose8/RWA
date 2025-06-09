#!/usr/bin/env python3
"""
Transaction Executor for Synergy7 Trading System

This module provides a high-level interface for transaction execution,
abstracting the complexity of different execution methods and providing
a unified API for the execution engine.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction type enumeration."""
    SWAP = "swap"
    TRANSFER = "transfer"
    BUNDLE = "bundle"
    NATIVE = "native"
    JUPITER = "jupiter"


class ExecutionMethod(Enum):
    """Execution method enumeration."""
    IMMEDIATE = "immediate"
    BUNDLE = "bundle"
    JITO_BUNDLE = "jito_bundle"
    QUICKNODE_BUNDLE = "quicknode_bundle"
    REGULAR_RPC = "regular_rpc"


class TransactionExecutor:
    """
    High-level transaction executor that provides a unified interface
    for executing different types of transactions using various methods.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the transaction executor."""
        self.config = config or {}

        # Components (will be injected)
        self.modern_executor = None
        self.unified_tx_builder = None
        self.rpc_manager = None  # Robust RPC manager for endpoint handling

        # Execution preferences - prioritize reliable methods
        self.preferred_method = ExecutionMethod.REGULAR_RPC  # Start with most reliable
        self.fallback_methods = [
            ExecutionMethod.BUNDLE,
            ExecutionMethod.JITO_BUNDLE,
            ExecutionMethod.QUICKNODE_BUNDLE
        ]
        
        # Performance tracking
        self.execution_metrics = {
            'total_transactions': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'method_usage': {},
            'average_execution_time': 0.0,
            'last_execution': None
        }
        
        # Configuration
        self.timeout = self.config.get('transaction_timeout', 30.0)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        
        logger.info("🔧 TransactionExecutor initialized")

    async def initialize(self, modern_executor=None, unified_tx_builder=None, rpc_manager=None):
        """Initialize the transaction executor with required components."""
        try:
            self.modern_executor = modern_executor
            self.unified_tx_builder = unified_tx_builder

            # Initialize robust RPC manager if not provided
            if rpc_manager:
                self.rpc_manager = rpc_manager
            else:
                from core.execution.robust_rpc_manager import RobustRpcManager
                self.rpc_manager = RobustRpcManager(self.config)

            if not self.modern_executor:
                raise ValueError("Modern executor is required")

            if not self.unified_tx_builder:
                raise ValueError("Unified transaction builder is required")

            # Force initial health check of endpoints
            await self.rpc_manager.force_health_check()

            logger.info("✅ TransactionExecutor initialized with robust RPC management")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize TransactionExecutor: {e}")
            return False

    async def execute_transaction(self, 
                                transaction: Union[str, bytes, Dict[str, Any]],
                                tx_type: TransactionType = TransactionType.SWAP,
                                method: Optional[ExecutionMethod] = None,
                                opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a transaction using the specified or preferred method.
        
        Args:
            transaction: Transaction data (serialized or dict)
            tx_type: Type of transaction
            method: Preferred execution method (optional)
            opts: Additional execution options
            
        Returns:
            Execution result dictionary
        """
        start_time = time.time()
        self.execution_metrics['total_transactions'] += 1
        
        try:
            # Determine execution method
            execution_method = method or self.preferred_method
            
            logger.info(f"⚡ Executing {tx_type.value} transaction via {execution_method.value}")
            
            # Execute with retries
            result = await self._execute_with_retries(
                transaction, tx_type, execution_method, opts
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update metrics
            if result and result.get('success', False):
                self.execution_metrics['successful_transactions'] += 1
                logger.info(f"✅ Transaction executed successfully in {execution_time:.2f}s")
            else:
                self.execution_metrics['failed_transactions'] += 1
                logger.error(f"❌ Transaction failed after {execution_time:.2f}s")
            
            # Update method usage stats
            method_name = execution_method.value
            if method_name not in self.execution_metrics['method_usage']:
                self.execution_metrics['method_usage'][method_name] = 0
            self.execution_metrics['method_usage'][method_name] += 1
            
            # Update average execution time
            total_txs = self.execution_metrics['successful_transactions'] + self.execution_metrics['failed_transactions']
            if total_txs > 0:
                current_avg = self.execution_metrics['average_execution_time']
                self.execution_metrics['average_execution_time'] = (
                    (current_avg * (total_txs - 1) + execution_time) / total_txs
                )
            
            self.execution_metrics['last_execution'] = datetime.now().isoformat()
            
            # Add execution metadata to result
            if result:
                result['execution_time'] = execution_time
                result['execution_method'] = execution_method.value
                result['transaction_type'] = tx_type.value
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.execution_metrics['failed_transactions'] += 1
            
            logger.error(f"❌ Transaction execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'execution_method': execution_method.value if 'execution_method' in locals() else 'unknown',
                'transaction_type': tx_type.value
            }

    async def _execute_with_retries(self,
                                  transaction: Union[str, bytes, Dict[str, Any]],
                                  tx_type: TransactionType,
                                  method: ExecutionMethod,
                                  opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction with retry logic and fallback methods."""
        last_error = None
        methods_to_try = [method] + self.fallback_methods
        
        for attempt in range(self.max_retries):
            for current_method in methods_to_try:
                try:
                    logger.info(f"🔄 Attempt {attempt + 1}/{self.max_retries} using {current_method.value}")
                    
                    # Execute using the current method
                    result = await self._execute_single(transaction, tx_type, current_method, opts)
                    
                    if result and result.get('success', False):
                        return result
                    else:
                        last_error = result.get('error', 'Unknown error') if result else 'No result'
                        logger.warning(f"⚠️ Method {current_method.value} failed: {last_error}")
                        
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"⚠️ Method {current_method.value} error: {e}")
                    continue
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
        return {
            'success': False,
            'error': f"All execution methods failed. Last error: {last_error}",
            'attempts': self.max_retries,
            'methods_tried': [m.value for m in methods_to_try]
        }

    async def _execute_single(self,
                            transaction: Union[str, bytes, Dict[str, Any]],
                            tx_type: TransactionType,
                            method: ExecutionMethod,
                            opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a single transaction using the specified method."""
        try:
            if method == ExecutionMethod.IMMEDIATE:
                return await self._execute_immediate(transaction, opts)
            elif method == ExecutionMethod.BUNDLE:
                return await self._execute_bundle(transaction, opts)
            elif method == ExecutionMethod.JITO_BUNDLE:
                return await self._execute_jito_bundle(transaction, opts)
            elif method == ExecutionMethod.QUICKNODE_BUNDLE:
                return await self._execute_quicknode_bundle(transaction, opts)
            elif method == ExecutionMethod.REGULAR_RPC:
                return await self._execute_regular_rpc(transaction, opts)
            else:
                return {'success': False, 'error': f'Unknown execution method: {method.value}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Execution method {method.value} failed: {str(e)}'}

    async def _execute_immediate(self, transaction: Union[str, bytes, Dict[str, Any]], 
                               opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction immediately using modern executor."""
        try:
            if hasattr(self.modern_executor, 'execute_transaction_with_bundles'):
                return await self.modern_executor.execute_transaction_with_bundles(transaction, opts)
            else:
                return {'success': False, 'error': 'Modern executor not available'}
        except Exception as e:
            return {'success': False, 'error': f'Immediate execution failed: {str(e)}'}

    async def _execute_bundle(self, transaction: Union[str, bytes, Dict[str, Any]], 
                            opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction as a bundle."""
        try:
            # Try QuickNode bundle first, then Jito bundle
            if hasattr(self.modern_executor, '_execute_quicknode_bundle'):
                result = await self.modern_executor._execute_quicknode_bundle([transaction])
                if result and result.get('success', False):
                    return result
            
            # Fallback to Jito bundle
            if hasattr(self.modern_executor, '_execute_jito_bundle'):
                return await self.modern_executor._execute_jito_bundle([transaction])
            
            return {'success': False, 'error': 'No bundle execution methods available'}
            
        except Exception as e:
            return {'success': False, 'error': f'Bundle execution failed: {str(e)}'}

    async def _execute_jito_bundle(self, transaction: Union[str, bytes, Dict[str, Any]], 
                                 opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction using Jito bundle."""
        try:
            if hasattr(self.modern_executor, '_execute_jito_bundle'):
                return await self.modern_executor._execute_jito_bundle([transaction])
            else:
                return {'success': False, 'error': 'Jito bundle execution not available'}
        except Exception as e:
            return {'success': False, 'error': f'Jito bundle execution failed: {str(e)}'}

    async def _execute_quicknode_bundle(self, transaction: Union[str, bytes, Dict[str, Any]], 
                                      opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction using QuickNode bundle."""
        try:
            if hasattr(self.modern_executor, '_execute_quicknode_bundle'):
                return await self.modern_executor._execute_quicknode_bundle([transaction])
            else:
                return {'success': False, 'error': 'QuickNode bundle execution not available'}
        except Exception as e:
            return {'success': False, 'error': f'QuickNode bundle execution failed: {str(e)}'}

    async def _execute_regular_rpc(self, transaction: Union[str, bytes, Dict[str, Any]], 
                                 opts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute transaction using regular RPC."""
        try:
            if hasattr(self.modern_executor, '_execute_regular_transaction'):
                return await self.modern_executor._execute_regular_transaction(transaction, opts)
            else:
                return {'success': False, 'error': 'Regular RPC execution not available'}
        except Exception as e:
            return {'success': False, 'error': f'Regular RPC execution failed: {str(e)}'}

    async def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading signal by building and executing the transaction.
        
        Args:
            signal: Trading signal containing action, market, size, etc.
            
        Returns:
            Execution result dictionary
        """
        try:
            logger.info(f"🎯 Executing signal: {signal['action']} {signal['market']} {signal['size']}")
            
            # Build transaction using unified builder
            transaction = await self.unified_tx_builder.build_and_sign_transaction(signal)
            
            if not transaction:
                return {'success': False, 'error': 'Failed to build transaction from signal'}
            
            # Determine transaction type based on signal
            tx_type = TransactionType.SWAP  # Most signals are swaps
            if signal.get('action') == 'TRANSFER':
                tx_type = TransactionType.TRANSFER
            
            # Execute the transaction
            result = await self.execute_transaction(transaction, tx_type)
            
            # Add signal information to result
            if result:
                result['signal'] = signal
                result['signal_id'] = signal.get('id', 'unknown')
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to execute signal: {e}")
            return {
                'success': False,
                'error': str(e),
                'signal': signal
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current execution metrics."""
        total_txs = self.execution_metrics['successful_transactions'] + self.execution_metrics['failed_transactions']
        success_rate = (self.execution_metrics['successful_transactions'] / total_txs * 100) if total_txs > 0 else 0

        metrics = {
            'total_transactions': self.execution_metrics['total_transactions'],
            'successful_transactions': self.execution_metrics['successful_transactions'],
            'failed_transactions': self.execution_metrics['failed_transactions'],
            'success_rate_pct': round(success_rate, 2),
            'method_usage': self.execution_metrics['method_usage'],
            'average_execution_time': round(self.execution_metrics['average_execution_time'], 3),
            'last_execution': self.execution_metrics['last_execution'],
            'preferred_method': self.preferred_method.value,
            'fallback_methods': [m.value for m in self.fallback_methods]
        }

        # Add RPC endpoint status if available
        if self.rpc_manager:
            metrics['rpc_status'] = self.rpc_manager.get_status()

        return metrics

    def set_preferred_method(self, method: ExecutionMethod):
        """Set the preferred execution method."""
        self.preferred_method = method
        logger.info(f"🔧 Preferred execution method set to: {method.value}")

    def add_fallback_method(self, method: ExecutionMethod):
        """Add a fallback execution method."""
        if method not in self.fallback_methods:
            self.fallback_methods.append(method)
            logger.info(f"🔧 Added fallback method: {method.value}")

    def remove_fallback_method(self, method: ExecutionMethod):
        """Remove a fallback execution method."""
        if method in self.fallback_methods:
            self.fallback_methods.remove(method)
            logger.info(f"🔧 Removed fallback method: {method.value}")
