#!/usr/bin/env python3
"""
Order Manager for Synergy7 Trading System

This module provides order management functionality including order tracking,
persistence, and lifecycle management for the execution engine.
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    REJECTED = "rejected"


class OrderPriority(Enum):
    """Order priority enumeration."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Order:
    """Represents a trading order."""
    order_id: str
    signal: Dict[str, Any]
    status: OrderStatus
    priority: OrderPriority
    created_at: datetime
    updated_at: datetime
    execution_attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    transaction_result: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    estimated_value: Optional[float] = None
    actual_value: Optional[float] = None
    fees_paid: Optional[float] = None
    slippage: Optional[float] = None


class OrderManager:
    """
    Manages the lifecycle of trading orders including persistence,
    tracking, and reporting.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the order manager."""
        self.config = config or {}
        
        # Database configuration
        self.db_path = self.config.get('db_path', 'output/orders.db')
        self.db_connection = None
        
        # In-memory order tracking
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        # Configuration
        self.max_history_size = self.config.get('max_history_size', 10000)
        self.cleanup_interval = self.config.get('cleanup_interval', 3600)  # 1 hour
        self.order_timeout = self.config.get('order_timeout', 300)  # 5 minutes
        
        # Statistics
        self.stats = {
            'total_orders': 0,
            'completed_orders': 0,
            'failed_orders': 0,
            'cancelled_orders': 0,
            'average_execution_time': 0.0,
            'total_value_traded': 0.0,
            'total_fees_paid': 0.0
        }
        
        logger.info("📋 OrderManager initialized")

    async def initialize(self):
        """Initialize the order manager and database."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Initialize database
            await self._init_database()
            
            # Load existing orders from database
            await self._load_orders_from_db()
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            
            logger.info("✅ OrderManager initialized with database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OrderManager: {e}")
            return False

    async def _init_database(self):
        """Initialize the SQLite database for order persistence."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id TEXT PRIMARY KEY,
                        signal TEXT NOT NULL,
                        status TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        execution_attempts INTEGER DEFAULT 0,
                        max_attempts INTEGER DEFAULT 3,
                        error_message TEXT,
                        transaction_result TEXT,
                        execution_time REAL,
                        estimated_value REAL,
                        actual_value REAL,
                        fees_paid REAL,
                        slippage REAL
                    )
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)
                ''')
                
                await db.commit()
                
            logger.info("✅ Order database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    async def _load_orders_from_db(self):
        """Load existing orders from database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 1000') as cursor:
                    rows = await cursor.fetchall()
                    
                    for row in rows:
                        order = self._row_to_order(row)
                        
                        # Add to appropriate collection
                        if order.status in [OrderStatus.PENDING, OrderStatus.EXECUTING]:
                            self.active_orders[order.order_id] = order
                        else:
                            self.order_history.append(order)
            
            logger.info(f"📋 Loaded {len(self.active_orders)} active orders and {len(self.order_history)} historical orders")
            
        except Exception as e:
            logger.error(f"❌ Failed to load orders from database: {e}")

    def _row_to_order(self, row) -> Order:
        """Convert database row to Order object."""
        return Order(
            order_id=row[0],
            signal=json.loads(row[1]),
            status=OrderStatus(row[2]),
            priority=OrderPriority(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            execution_attempts=row[6],
            max_attempts=row[7],
            error_message=row[8],
            transaction_result=json.loads(row[9]) if row[9] else None,
            execution_time=row[10],
            estimated_value=row[11],
            actual_value=row[12],
            fees_paid=row[13],
            slippage=row[14]
        )

    async def register_order(self, order: Union[Order, Dict[str, Any]]) -> bool:
        """Register a new order."""
        try:
            # Convert dict to Order if needed
            if isinstance(order, dict):
                order = Order(**order)
            
            # Add to active orders
            self.active_orders[order.order_id] = order
            
            # Persist to database
            await self._save_order_to_db(order)
            
            # Update statistics
            self.stats['total_orders'] += 1
            
            logger.info(f"📝 Registered order: {order.order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register order: {e}")
            return False

    async def update_order(self, order: Order) -> bool:
        """Update an existing order."""
        try:
            # Update timestamp
            order.updated_at = datetime.now()
            
            # Update in memory
            if order.order_id in self.active_orders:
                self.active_orders[order.order_id] = order
            
            # Persist to database
            await self._save_order_to_db(order)
            
            # Move to history if completed
            if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, 
                              OrderStatus.CANCELLED, OrderStatus.TIMEOUT]:
                if order.order_id in self.active_orders:
                    del self.active_orders[order.order_id]
                
                self.order_history.append(order)
                
                # Update statistics
                if order.status == OrderStatus.COMPLETED:
                    self.stats['completed_orders'] += 1
                    if order.execution_time:
                        # Update average execution time
                        total_completed = self.stats['completed_orders']
                        current_avg = self.stats['average_execution_time']
                        self.stats['average_execution_time'] = (
                            (current_avg * (total_completed - 1) + order.execution_time) / total_completed
                        )
                    
                    if order.actual_value:
                        self.stats['total_value_traded'] += order.actual_value
                    
                    if order.fees_paid:
                        self.stats['total_fees_paid'] += order.fees_paid
                        
                elif order.status == OrderStatus.FAILED:
                    self.stats['failed_orders'] += 1
                elif order.status == OrderStatus.CANCELLED:
                    self.stats['cancelled_orders'] += 1
            
            logger.debug(f"📝 Updated order: {order.order_id} - {order.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update order: {e}")
            return False

    async def _save_order_to_db(self, order: Order):
        """Save order to database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO orders (
                        order_id, signal, status, priority, created_at, updated_at,
                        execution_attempts, max_attempts, error_message, transaction_result,
                        execution_time, estimated_value, actual_value, fees_paid, slippage
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order.order_id,
                    json.dumps(order.signal),
                    order.status.value,
                    order.priority.value,
                    order.created_at.isoformat(),
                    order.updated_at.isoformat(),
                    order.execution_attempts,
                    order.max_attempts,
                    order.error_message,
                    json.dumps(order.transaction_result) if order.transaction_result else None,
                    order.execution_time,
                    order.estimated_value,
                    order.actual_value,
                    order.fees_paid,
                    order.slippage
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to save order to database: {e}")

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        # Check active orders first
        if order_id in self.active_orders:
            return self.active_orders[order_id]
        
        # Check history
        for order in self.order_history:
            if order.order_id == order_id:
                return order
        
        # Check database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return self._row_to_order(row)
        except Exception as e:
            logger.error(f"❌ Failed to get order from database: {e}")
        
        return None

    async def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get all orders with a specific status."""
        orders = []
        
        # Check active orders
        for order in self.active_orders.values():
            if order.status == status:
                orders.append(order)
        
        # Check history
        for order in self.order_history:
            if order.status == status:
                orders.append(order)
        
        return orders

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            order = await self.get_order(order_id)
            if not order:
                logger.warning(f"⚠️ Order not found: {order_id}")
                return False
            
            if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
                logger.warning(f"⚠️ Cannot cancel order in status: {order.status.value}")
                return False
            
            order.status = OrderStatus.CANCELLED
            await self.update_order(order)
            
            logger.info(f"❌ Cancelled order: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel order: {e}")
            return False

    async def get_active_orders(self) -> List[Order]:
        """Get all active orders."""
        return list(self.active_orders.values())

    async def get_recent_orders(self, limit: int = 100) -> List[Order]:
        """Get recent orders (both active and historical)."""
        all_orders = list(self.active_orders.values()) + self.order_history
        all_orders.sort(key=lambda x: x.created_at, reverse=True)
        return all_orders[:limit]

    async def _cleanup_task(self):
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_orders()
                await self._cleanup_timed_out_orders()
                
            except Exception as e:
                logger.error(f"❌ Error in cleanup task: {e}")

    async def _cleanup_old_orders(self):
        """Clean up old orders from memory."""
        try:
            if len(self.order_history) > self.max_history_size:
                # Keep only the most recent orders
                self.order_history.sort(key=lambda x: x.created_at, reverse=True)
                self.order_history = self.order_history[:self.max_history_size]
                logger.debug(f"🧹 Cleaned up old orders, keeping {len(self.order_history)} in memory")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old orders: {e}")

    async def _cleanup_timed_out_orders(self):
        """Mark timed out orders as failed."""
        try:
            current_time = datetime.now()
            timeout_threshold = current_time - timedelta(seconds=self.order_timeout)
            
            timed_out_orders = []
            for order in self.active_orders.values():
                if (order.status in [OrderStatus.PENDING, OrderStatus.EXECUTING] and
                    order.created_at < timeout_threshold):
                    timed_out_orders.append(order)
            
            for order in timed_out_orders:
                order.status = OrderStatus.TIMEOUT
                order.error_message = f"Order timed out after {self.order_timeout} seconds"
                await self.update_order(order)
                logger.warning(f"⏰ Order timed out: {order.order_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup timed out orders: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get order management statistics."""
        active_count = len(self.active_orders)
        history_count = len(self.order_history)
        
        return {
            'total_orders': self.stats['total_orders'],
            'active_orders': active_count,
            'completed_orders': self.stats['completed_orders'],
            'failed_orders': self.stats['failed_orders'],
            'cancelled_orders': self.stats['cancelled_orders'],
            'historical_orders': history_count,
            'average_execution_time': round(self.stats['average_execution_time'], 3),
            'total_value_traded': round(self.stats['total_value_traded'], 6),
            'total_fees_paid': round(self.stats['total_fees_paid'], 6),
            'success_rate_pct': round(
                (self.stats['completed_orders'] / max(1, self.stats['total_orders'])) * 100, 2
            )
        }
