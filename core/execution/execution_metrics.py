#!/usr/bin/env python3
"""
Execution Metrics for Synergy7 Trading System

This module provides comprehensive metrics collection and analysis
for execution performance monitoring and optimization.
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import sqlite3
import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetric:
    """Represents a single execution metric."""
    timestamp: datetime
    order_id: str
    execution_time: float
    success: bool
    method: str
    transaction_type: str
    value_traded: Optional[float] = None
    fees_paid: Optional[float] = None
    slippage: Optional[float] = None
    error_message: Optional[str] = None


class ExecutionMetrics:
    """
    Comprehensive execution metrics collection and analysis system.
    
    Tracks performance metrics including:
    - Execution times and success rates
    - Method performance comparison
    - Value and fee tracking
    - Real-time performance monitoring
    - Historical analysis and trends
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the execution metrics system."""
        self.config = config or {}
        
        # Database configuration
        self.db_path = self.config.get('metrics_db_path', 'output/execution_metrics.db')
        
        # In-memory metrics storage
        self.recent_metrics: deque = deque(maxlen=1000)  # Last 1000 executions
        self.method_metrics: Dict[str, List[ExecutionMetric]] = defaultdict(list)
        
        # Real-time statistics
        self.current_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'total_value_traded': 0.0,
            'total_fees_paid': 0.0,
            'last_execution_time': None,
            'session_start_time': datetime.now()
        }
        
        # Performance windows for analysis
        self.performance_windows = {
            '1min': deque(maxlen=60),    # Last 60 seconds
            '5min': deque(maxlen=300),   # Last 5 minutes
            '1hour': deque(maxlen=3600), # Last hour
            '1day': deque(maxlen=86400)  # Last day
        }
        
        # Configuration
        self.metrics_retention_days = self.config.get('metrics_retention_days', 30)
        self.cleanup_interval = self.config.get('cleanup_interval', 3600)  # 1 hour
        
        logger.info("📊 ExecutionMetrics initialized")

    async def initialize(self):
        """Initialize the metrics system and database."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Initialize database
            await self._init_database()
            
            # Load recent metrics from database
            await self._load_recent_metrics()
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            
            logger.info("✅ ExecutionMetrics initialized with database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ExecutionMetrics: {e}")
            return False

    async def _init_database(self):
        """Initialize the SQLite database for metrics persistence."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS execution_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        order_id TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        success BOOLEAN NOT NULL,
                        method TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        value_traded REAL,
                        fees_paid REAL,
                        slippage REAL,
                        error_message TEXT
                    )
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON execution_metrics(timestamp)
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_method ON execution_metrics(method)
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metrics_success ON execution_metrics(success)
                ''')
                
                await db.commit()
                
            logger.info("✅ Metrics database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize metrics database: {e}")
            raise

    async def _load_recent_metrics(self):
        """Load recent metrics from database."""
        try:
            # Load last 1000 metrics
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM execution_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                ''') as cursor:
                    rows = await cursor.fetchall()
                    
                    for row in rows:
                        metric = self._row_to_metric(row)
                        self.recent_metrics.appendleft(metric)
                        
                        # Update method metrics
                        self.method_metrics[metric.method].append(metric)
                        
                        # Update current stats
                        self._update_current_stats(metric)
            
            logger.info(f"📊 Loaded {len(self.recent_metrics)} recent metrics")
            
        except Exception as e:
            logger.error(f"❌ Failed to load recent metrics: {e}")

    def _row_to_metric(self, row) -> ExecutionMetric:
        """Convert database row to ExecutionMetric object."""
        return ExecutionMetric(
            timestamp=datetime.fromisoformat(row[1]),
            order_id=row[2],
            execution_time=row[3],
            success=bool(row[4]),
            method=row[5],
            transaction_type=row[6],
            value_traded=row[7],
            fees_paid=row[8],
            slippage=row[9],
            error_message=row[10]
        )

    async def record_execution(self, order, execution_result: Dict[str, Any] = None):
        """Record an execution metric."""
        try:
            # Extract metric data from order
            metric = ExecutionMetric(
                timestamp=datetime.now(),
                order_id=order.order_id,
                execution_time=order.execution_time or 0.0,
                success=order.status.value == 'completed',
                method=execution_result.get('execution_method', 'unknown') if execution_result else 'unknown',
                transaction_type=order.signal.get('action', 'unknown'),
                value_traded=order.actual_value,
                fees_paid=order.fees_paid,
                slippage=order.slippage,
                error_message=order.error_message
            )
            
            # Add to in-memory storage
            self.recent_metrics.append(metric)
            self.method_metrics[metric.method].append(metric)
            
            # Add to performance windows
            current_time = time.time()
            for window in self.performance_windows.values():
                window.append((current_time, metric))
            
            # Update current stats
            self._update_current_stats(metric)
            
            # Persist to database
            await self._save_metric_to_db(metric)
            
            logger.debug(f"📊 Recorded execution metric: {metric.order_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to record execution metric: {e}")

    def _update_current_stats(self, metric: ExecutionMetric):
        """Update current statistics with new metric."""
        self.current_stats['total_executions'] += 1
        
        if metric.success:
            self.current_stats['successful_executions'] += 1
        else:
            self.current_stats['failed_executions'] += 1
        
        self.current_stats['total_execution_time'] += metric.execution_time
        
        if metric.value_traded:
            self.current_stats['total_value_traded'] += metric.value_traded
        
        if metric.fees_paid:
            self.current_stats['total_fees_paid'] += metric.fees_paid
        
        self.current_stats['last_execution_time'] = metric.timestamp.isoformat()

    async def _save_metric_to_db(self, metric: ExecutionMetric):
        """Save metric to database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO execution_metrics (
                        timestamp, order_id, execution_time, success, method,
                        transaction_type, value_traded, fees_paid, slippage, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp.isoformat(),
                    metric.order_id,
                    metric.execution_time,
                    metric.success,
                    metric.method,
                    metric.transaction_type,
                    metric.value_traded,
                    metric.fees_paid,
                    metric.slippage,
                    metric.error_message
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to save metric to database: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current execution statistics."""
        total_executions = self.current_stats['total_executions']
        successful_executions = self.current_stats['successful_executions']
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        avg_execution_time = (self.current_stats['total_execution_time'] / total_executions) if total_executions > 0 else 0
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': self.current_stats['failed_executions'],
            'success_rate_pct': round(success_rate, 2),
            'average_execution_time': round(avg_execution_time, 3),
            'total_value_traded': round(self.current_stats['total_value_traded'], 6),
            'total_fees_paid': round(self.current_stats['total_fees_paid'], 6),
            'last_execution_time': self.current_stats['last_execution_time'],
            'session_start_time': self.current_stats['session_start_time'].isoformat(),
            'session_duration_minutes': round(
                (datetime.now() - self.current_stats['session_start_time']).total_seconds() / 60, 2
            )
        }

    def get_method_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics by execution method."""
        method_stats = {}
        
        for method, metrics in self.method_metrics.items():
            if not metrics:
                continue
            
            successful = [m for m in metrics if m.success]
            failed = [m for m in metrics if not m.success]
            
            execution_times = [m.execution_time for m in metrics]
            
            method_stats[method] = {
                'total_executions': len(metrics),
                'successful_executions': len(successful),
                'failed_executions': len(failed),
                'success_rate_pct': round((len(successful) / len(metrics)) * 100, 2),
                'average_execution_time': round(statistics.mean(execution_times), 3) if execution_times else 0,
                'median_execution_time': round(statistics.median(execution_times), 3) if execution_times else 0,
                'min_execution_time': round(min(execution_times), 3) if execution_times else 0,
                'max_execution_time': round(max(execution_times), 3) if execution_times else 0,
                'total_value_traded': round(sum(m.value_traded for m in metrics if m.value_traded), 6),
                'total_fees_paid': round(sum(m.fees_paid for m in metrics if m.fees_paid), 6)
            }
        
        return method_stats

    def get_window_performance(self, window: str = '5min') -> Dict[str, Any]:
        """Get performance statistics for a specific time window."""
        if window not in self.performance_windows:
            return {}
        
        current_time = time.time()
        window_data = self.performance_windows[window]
        
        # Filter to actual window duration
        window_seconds = {
            '1min': 60,
            '5min': 300,
            '1hour': 3600,
            '1day': 86400
        }.get(window, 300)
        
        cutoff_time = current_time - window_seconds
        recent_metrics = [metric for timestamp, metric in window_data if timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                'window': window,
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'success_rate_pct': 0,
                'average_execution_time': 0,
                'executions_per_minute': 0
            }
        
        successful = [m for m in recent_metrics if m.success]
        execution_times = [m.execution_time for m in recent_metrics]
        
        return {
            'window': window,
            'total_executions': len(recent_metrics),
            'successful_executions': len(successful),
            'failed_executions': len(recent_metrics) - len(successful),
            'success_rate_pct': round((len(successful) / len(recent_metrics)) * 100, 2),
            'average_execution_time': round(statistics.mean(execution_times), 3) if execution_times else 0,
            'executions_per_minute': round((len(recent_metrics) / (window_seconds / 60)), 2)
        }

    async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over the specified number of hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('''
                    SELECT * FROM execution_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp
                ''', (cutoff_time.isoformat(),)) as cursor:
                    rows = await cursor.fetchall()
                    
                    metrics = [self._row_to_metric(row) for row in rows]
            
            if not metrics:
                return {'hours': hours, 'total_executions': 0}
            
            # Group by hour
            hourly_stats = defaultdict(lambda: {'successful': 0, 'failed': 0, 'execution_times': []})
            
            for metric in metrics:
                hour_key = metric.timestamp.strftime('%Y-%m-%d %H:00')
                if metric.success:
                    hourly_stats[hour_key]['successful'] += 1
                else:
                    hourly_stats[hour_key]['failed'] += 1
                hourly_stats[hour_key]['execution_times'].append(metric.execution_time)
            
            # Calculate trends
            trend_data = []
            for hour, stats in sorted(hourly_stats.items()):
                total = stats['successful'] + stats['failed']
                success_rate = (stats['successful'] / total * 100) if total > 0 else 0
                avg_time = statistics.mean(stats['execution_times']) if stats['execution_times'] else 0
                
                trend_data.append({
                    'hour': hour,
                    'total_executions': total,
                    'successful_executions': stats['successful'],
                    'failed_executions': stats['failed'],
                    'success_rate_pct': round(success_rate, 2),
                    'average_execution_time': round(avg_time, 3)
                })
            
            return {
                'hours': hours,
                'total_executions': len(metrics),
                'hourly_trends': trend_data
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance trends: {e}")
            return {'hours': hours, 'total_executions': 0, 'error': str(e)}

    async def _cleanup_task(self):
        """Periodic cleanup task for old metrics."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"❌ Error in metrics cleanup task: {e}")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics from database."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.metrics_retention_days)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'DELETE FROM execution_metrics WHERE timestamp < ?',
                    (cutoff_date.isoformat(),)
                )
                deleted_count = cursor.rowcount
                await db.commit()
                
                if deleted_count > 0:
                    logger.info(f"🧹 Cleaned up {deleted_count} old metrics")
                    
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old metrics: {e}")

    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics to file."""
        try:
            data = {
                'current_stats': self.get_current_stats(),
                'method_performance': self.get_method_performance(),
                'recent_metrics': [asdict(m) for m in list(self.recent_metrics)[-100:]]  # Last 100
            }
            
            if format.lower() == 'json':
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"📊 Exported metrics to: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Failed to export metrics: {e}")
            raise
