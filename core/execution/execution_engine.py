#!/usr/bin/env python3
"""
Production Execution Engine for Synergy7 Trading System

This module provides the main execution engine that coordinates all trading execution
activities including order management, transaction execution, and performance monitoring.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


# Use Order class and OrderStatus from order_manager


class ExecutionEngine:
    """
    Production-ready execution engine for live trading.
    
    Coordinates all execution activities including:
    - Order queue management
    - Transaction execution via modern executor
    - Performance monitoring and metrics
    - Error handling and recovery
    - Integration with unified transaction builder
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the execution engine."""
        self.config = config or {}
        self.running = False
        self.paused = False
        
        # Components (will be injected)
        self.modern_executor = None
        self.unified_tx_builder = None
        self.order_manager = None
        self.metrics = None
        
        # Execution state
        self.pending_orders: List = []
        self.active_orders: Dict = {}
        self.completed_orders: List = []
        
        # Performance tracking
        self.execution_stats = {
            'total_orders': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0,
            'last_execution_time': None
        }
        
        # Configuration
        self.max_concurrent_executions = self.config.get('max_concurrent_executions', 3)
        self.execution_timeout = self.config.get('execution_timeout', 30.0)
        self.retry_delay = self.config.get('retry_delay', 2.0)
        
        logger.info("🚀 ExecutionEngine initialized for live trading")

    async def initialize(self, modern_executor=None, unified_tx_builder=None, 
                        order_manager=None, metrics=None):
        """Initialize the execution engine with required components."""
        try:
            # Inject dependencies
            self.modern_executor = modern_executor
            self.unified_tx_builder = unified_tx_builder
            self.order_manager = order_manager
            self.metrics = metrics
            
            # Validate required components
            if not self.modern_executor:
                raise ValueError("Modern executor is required for live trading")
            
            if not self.unified_tx_builder:
                raise ValueError("Unified transaction builder is required")
            
            # Initialize metrics if not provided
            if not self.metrics:
                from core.execution.execution_metrics import ExecutionMetrics
                self.metrics = ExecutionMetrics()
                await self.metrics.initialize()

            # Initialize order manager if not provided
            if not self.order_manager:
                from core.execution.order_manager import OrderManager
                self.order_manager = OrderManager()
                await self.order_manager.initialize()

            logger.info("✅ ExecutionEngine initialized with all components")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize ExecutionEngine: {e}")
            return False

    async def start(self):
        """Start the execution engine."""
        if self.running:
            logger.warning("⚠️ ExecutionEngine already running")
            return
        
        logger.info("🚀 Starting ExecutionEngine...")
        self.running = True
        
        # Start the execution loop
        asyncio.create_task(self._execution_loop())
        logger.info("✅ ExecutionEngine started")

    async def stop(self):
        """Stop the execution engine."""
        logger.info("🛑 Stopping ExecutionEngine...")
        self.running = False
        
        # Wait for active executions to complete
        while self.active_orders:
            logger.info(f"⏳ Waiting for {len(self.active_orders)} active executions to complete...")
            await asyncio.sleep(1.0)
        
        logger.info("✅ ExecutionEngine stopped")

    async def pause(self):
        """Pause execution (complete active orders but don't start new ones)."""
        logger.info("⏸️ Pausing ExecutionEngine...")
        self.paused = True

    async def resume(self):
        """Resume execution."""
        logger.info("▶️ Resuming ExecutionEngine...")
        self.paused = False

    async def submit_order(self, signal: Dict[str, Any]) -> str:
        """
        Submit a trading signal for execution.
        
        Args:
            signal: Trading signal containing action, market, size, etc.
            
        Returns:
            order_id: Unique identifier for the submitted order
        """
        try:
            # Generate unique order ID
            order_id = f"order_{int(time.time() * 1000)}_{len(self.pending_orders)}"
            
            # Create execution order
            from core.execution.order_manager import Order, OrderStatus, OrderPriority
            order = Order(
                order_id=order_id,
                signal=signal,
                status=OrderStatus.PENDING,
                priority=OrderPriority.NORMAL,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add to pending queue
            self.pending_orders.append(order)
            
            # Update metrics
            self.execution_stats['total_orders'] += 1
            
            # Register with order manager
            if self.order_manager:
                await self.order_manager.register_order(order)
            
            logger.info(f"📝 Order submitted: {order_id} - {signal['action']} {signal['market']} {signal['size']}")
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Failed to submit order: {e}")
            raise

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an order."""
        try:
            # Check active orders
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                return self._order_to_dict(order)
            
            # Check pending orders
            for order in self.pending_orders:
                if order.order_id == order_id:
                    return self._order_to_dict(order)
            
            # Check completed orders
            for order in self.completed_orders:
                if order.order_id == order_id:
                    return self._order_to_dict(order)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get order status: {e}")
            return None

    def _order_to_dict(self, order) -> Dict[str, Any]:
        """Convert ExecutionOrder to dictionary."""
        return {
            'order_id': order.order_id,
            'signal': order.signal,
            'status': order.status.value,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'execution_attempts': order.execution_attempts,
            'error_message': order.error_message,
            'transaction_result': order.transaction_result,
            'execution_time': order.execution_time
        }

    async def _execution_loop(self):
        """Main execution loop."""
        logger.info("🔄 ExecutionEngine loop started")
        
        while self.running:
            try:
                # Skip if paused
                if self.paused:
                    await asyncio.sleep(0.1)
                    continue
                
                # Check for pending orders to execute
                if (self.pending_orders and 
                    len(self.active_orders) < self.max_concurrent_executions):
                    
                    # Get next pending order
                    order = self.pending_orders.pop(0)
                    
                    # Start execution
                    asyncio.create_task(self._execute_order(order))
                
                # Brief sleep to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error in execution loop: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("🔄 ExecutionEngine loop stopped")

    async def _execute_order(self, order):
        """Execute a single order."""
        try:
            # Move to active orders
            self.active_orders[order.order_id] = order
            from core.execution.order_manager import OrderStatus
            order.status = OrderStatus.EXECUTING
            order.updated_at = datetime.now()
            order.execution_attempts += 1
            
            logger.info(f"⚡ Executing order {order.order_id} (attempt {order.execution_attempts})")
            
            # Record start time
            start_time = time.time()
            
            # Execute the order with timeout
            try:
                result = await asyncio.wait_for(
                    self._perform_execution(order),
                    timeout=self.execution_timeout
                )
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Update order with results
                order.transaction_result = result
                order.execution_time = execution_time
                
                if result and result.get('success', False):
                    order.status = OrderStatus.COMPLETED
                    self.execution_stats['successful_executions'] += 1
                    logger.info(f"✅ Order {order.order_id} completed in {execution_time:.2f}s")
                else:
                    order.status = OrderStatus.FAILED
                    order.error_message = result.get('error', 'Unknown error') if result else 'No result'
                    self.execution_stats['failed_executions'] += 1
                    logger.error(f"❌ Order {order.order_id} failed: {order.error_message}")

            except asyncio.TimeoutError:
                order.status = OrderStatus.TIMEOUT
                order.error_message = f"Execution timeout after {self.execution_timeout}s"
                self.execution_stats['failed_executions'] += 1
                logger.error(f"⏰ Order {order.order_id} timed out")
                
        except Exception as e:
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            self.execution_stats['failed_executions'] += 1
            logger.error(f"❌ Error executing order {order.order_id}: {e}")
        
        finally:
            # Update timestamps
            order.updated_at = datetime.now()
            
            # Move to completed orders
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]
            self.completed_orders.append(order)
            
            # Update metrics
            if self.metrics:
                await self.metrics.record_execution(order)
            
            # Update order manager
            if self.order_manager:
                await self.order_manager.update_order(order)
            
            # Check if retry is needed
            if (order.status in [OrderStatus.FAILED, OrderStatus.TIMEOUT] and
                order.execution_attempts < order.max_attempts):

                logger.info(f"🔄 Retrying order {order.order_id} in {self.retry_delay}s")
                await asyncio.sleep(self.retry_delay)

                # Reset status and re-queue
                order.status = OrderStatus.PENDING
                self.pending_orders.append(order)

    async def _perform_execution(self, order) -> Dict[str, Any]:
        """Perform the actual execution of an order."""
        try:
            signal = order.signal
            
            # Build transaction using unified builder
            logger.info(f"🔨 Building transaction for order {order.order_id}")
            transaction = await self.unified_tx_builder.build_and_sign_transaction(signal)
            
            if not transaction:
                return {'success': False, 'error': 'Failed to build transaction'}
            
            # Execute transaction using modern executor
            logger.info(f"⚡ Executing transaction for order {order.order_id}")
            
            if hasattr(self.modern_executor, 'execute_transaction_with_bundles'):
                result = await self.modern_executor.execute_transaction_with_bundles(transaction)
            else:
                return {'success': False, 'error': 'Modern executor not available'}
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error performing execution for order {order.order_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get current execution statistics."""
        total_executions = self.execution_stats['successful_executions'] + self.execution_stats['failed_executions']
        success_rate = (self.execution_stats['successful_executions'] / total_executions * 100) if total_executions > 0 else 0
        
        return {
            'total_orders': self.execution_stats['total_orders'],
            'successful_executions': self.execution_stats['successful_executions'],
            'failed_executions': self.execution_stats['failed_executions'],
            'success_rate_pct': round(success_rate, 2),
            'pending_orders': len(self.pending_orders),
            'active_orders': len(self.active_orders),
            'completed_orders': len(self.completed_orders),
            'average_execution_time': self.execution_stats['average_execution_time'],
            'last_execution_time': self.execution_stats['last_execution_time'],
            'engine_status': 'running' if self.running else 'stopped',
            'engine_paused': self.paused
        }
