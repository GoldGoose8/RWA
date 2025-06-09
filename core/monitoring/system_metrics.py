"""
System Metrics Monitoring for Synergy7 Enhanced Trading System.

This module monitors system performance, API health, and operational metrics
with real-time alerting and comprehensive logging.
"""

import os
import sys
import asyncio
import logging
import json
import psutil
import httpx
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from collections import deque, defaultdict

# Configure specialized logger
logger = logging.getLogger('system')

class SystemMetricsMonitor:
    """
    Comprehensive system metrics monitoring with alerting.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the system metrics monitor."""
        self.config = config
        self.monitoring_config = config.get('monitoring', {})

        # Monitoring settings
        self.enabled = self.monitoring_config.get('system_metrics_enabled', True)
        self.update_interval = self.monitoring_config.get('update_interval', 60)
        self.api_check_interval = self.monitoring_config.get('api_check_interval', 300)

        # Alert thresholds
        self.thresholds = {
            'memory_usage_warning': 80,
            'memory_usage_critical': 90,
            'cpu_usage_warning': 75,
            'cpu_usage_critical': 90,
            'disk_usage_warning': 85,
            'disk_usage_critical': 95,
            'api_response_time_warning': 2000,  # ms
            'api_response_time_critical': 5000,  # ms
            'error_rate_warning': 5,  # %
            'error_rate_critical': 10  # %
        }

        # Metrics storage
        self.system_metrics = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.api_metrics = deque(maxlen=288)  # 24 hours at 5-minute intervals
        self.error_metrics = deque(maxlen=1440)

        # API endpoints to monitor
        self.api_endpoints = {
            'helius': {
                'url': f"https://rpc.helius.xyz/?api-key={os.environ.get('HELIUS_API_KEY', '')}",
                'method': 'POST',
                'payload': {"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                'timeout': 10
            },
            'birdeye': {
                'url': "https://public-api.birdeye.so/defi/tokenlist",
                'method': 'GET',
                'headers': {"X-API-KEY": os.environ.get('BIRDEYE_API_KEY', '')},
                'timeout': 10
            }
        }

        # Monitoring state
        self.is_monitoring = False
        self.last_api_check = datetime.min

        logger.info("System Metrics Monitor initialized")

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics."""
        try:
            timestamp = datetime.now()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            memory_metrics = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'used_pct': memory.percent,
                'free_pct': round((memory.available / memory.total) * 100, 2),
                'swap_total_gb': round(swap.total / (1024**3), 2),
                'swap_used_pct': swap.percent
            }

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]

            cpu_metrics = {
                'usage_pct': cpu_percent,
                'cores_logical': cpu_count,
                'cores_physical': psutil.cpu_count(logical=False),
                'load_avg_1m': load_avg[0],
                'load_avg_5m': load_avg[1],
                'load_avg_15m': load_avg[2],
                'load_avg_pct': (load_avg[0] / cpu_count) * 100 if cpu_count > 0 else 0
            }

            # Disk metrics
            disk = psutil.disk_usage('.')
            disk_io = psutil.disk_io_counters()

            disk_metrics = {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'used_pct': round((disk.used / disk.total) * 100, 2),
                'read_bytes': disk_io.read_bytes if disk_io else 0,
                'write_bytes': disk_io.write_bytes if disk_io else 0,
                'read_count': disk_io.read_count if disk_io else 0,
                'write_count': disk_io.write_count if disk_io else 0
            }

            # Network metrics
            network = psutil.net_io_counters()

            network_metrics = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv,
                'errin': network.errin,
                'errout': network.errout,
                'dropin': network.dropin,
                'dropout': network.dropout
            }

            # Process-specific metrics
            try:
                process = psutil.Process()
                process_metrics = {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': round(process.memory_info().rss / (1024**2), 2),
                    'memory_pct': process.memory_percent(),
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0,
                    'open_files': len(process.open_files()),
                    'connections': len(process.connections()),
                    'status': process.status()
                }
            except Exception as e:
                logger.warning(f"Error collecting process metrics: {str(e)}")
                process_metrics = {}

            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time

            system_info = {
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'boot_time': datetime.fromtimestamp(boot_time).isoformat(),
                'platform': sys.platform,
                'python_version': sys.version.split()[0]
            }

            # Compile all metrics
            metrics = {
                'timestamp': timestamp.isoformat(),
                'memory': memory_metrics,
                'cpu': cpu_metrics,
                'disk': disk_metrics,
                'network': network_metrics,
                'process': process_metrics,
                'system': system_info
            }

            # Store metrics
            self.system_metrics.append(metrics)

            # Log key metrics
            logger.info(f"System Metrics - CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, Disk: {disk_metrics['used_pct']:.1f}%")

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return {}

    async def check_api_health(self) -> Dict[str, Any]:
        """Check health of external APIs."""
        try:
            api_results = {}

            for api_name, api_config in self.api_endpoints.items():
                start_time = time.time()

                try:
                    async with httpx.AsyncClient() as client:
                        if api_config['method'] == 'POST':
                            response = await client.post(
                                api_config['url'],
                                json=api_config.get('payload', {}),
                                headers=api_config.get('headers', {}),
                                timeout=api_config['timeout']
                            )
                        else:
                            response = await client.get(
                                api_config['url'],
                                headers=api_config.get('headers', {}),
                                timeout=api_config['timeout']
                            )

                        response_time = (time.time() - start_time) * 1000  # Convert to ms

                        api_results[api_name] = {
                            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                            'status_code': response.status_code,
                            'response_time_ms': round(response_time, 2),
                            'timestamp': datetime.now().isoformat(),
                            'error': None
                        }

                        # Log API status
                        status_emoji = "✅" if response.status_code == 200 else "❌"
                        logger.info(f"API Health {api_name}: {status_emoji} {response.status_code} ({response_time:.0f}ms)")

                except Exception as e:
                    response_time = (time.time() - start_time) * 1000

                    api_results[api_name] = {
                        'status': 'error',
                        'status_code': None,
                        'response_time_ms': round(response_time, 2),
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    }

                    logger.error(f"API Health {api_name}: ❌ Error - {str(e)}")

            # Store API metrics
            api_metrics = {
                'timestamp': datetime.now().isoformat(),
                'apis': api_results
            }
            self.api_metrics.append(api_metrics)

            return api_metrics

        except Exception as e:
            logger.error(f"Error checking API health: {str(e)}")
            return {}

    def analyze_log_errors(self) -> Dict[str, Any]:
        """Analyze recent log files for errors and warnings."""
        try:
            log_analysis = {
                'timestamp': datetime.now().isoformat(),
                'error_counts': defaultdict(int),
                'warning_counts': defaultdict(int),
                'recent_errors': [],
                'error_rate_pct': 0.0
            }

            # Analyze main log file
            main_log_path = Path('logs/synergy7.log')
            if main_log_path.exists():
                try:
                    # Read last 1000 lines
                    with open(main_log_path, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-1000:] if len(lines) > 1000 else lines

                    total_lines = len(recent_lines)
                    error_lines = 0
                    warning_lines = 0

                    for line in recent_lines:
                        if 'ERROR' in line:
                            error_lines += 1
                            log_analysis['error_counts']['total'] += 1

                            # Extract error type
                            if 'API' in line:
                                log_analysis['error_counts']['api'] += 1
                            elif 'Database' in line or 'DB' in line:
                                log_analysis['error_counts']['database'] += 1
                            elif 'Network' in line:
                                log_analysis['error_counts']['network'] += 1
                            else:
                                log_analysis['error_counts']['other'] += 1

                            # Store recent errors (last 10)
                            if len(log_analysis['recent_errors']) < 10:
                                log_analysis['recent_errors'].append(line.strip())

                        elif 'WARNING' in line:
                            warning_lines += 1
                            log_analysis['warning_counts']['total'] += 1

                    # Calculate error rate
                    if total_lines > 0:
                        log_analysis['error_rate_pct'] = (error_lines / total_lines) * 100
                        log_analysis['warning_rate_pct'] = (warning_lines / total_lines) * 100

                except Exception as e:
                    logger.warning(f"Error analyzing main log file: {str(e)}")

            # Store error metrics
            self.error_metrics.append(log_analysis)

            # Log analysis summary
            if log_analysis['error_counts']['total'] > 0:
                logger.warning(f"Log Analysis - Errors: {log_analysis['error_counts']['total']}, Rate: {log_analysis['error_rate_pct']:.2f}%")

            return log_analysis

        except Exception as e:
            logger.error(f"Error analyzing log errors: {str(e)}")
            return {}

    def check_alert_conditions(self, system_metrics: Dict[str, Any],
                             api_metrics: Dict[str, Any],
                             error_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions in system metrics."""
        alerts = []

        try:
            # Memory alerts
            if system_metrics.get('memory', {}).get('used_pct', 0) > self.thresholds['memory_usage_critical']:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'metric': 'memory_usage',
                    'message': f"Critical memory usage: {system_metrics['memory']['used_pct']:.1f}%",
                    'value': system_metrics['memory']['used_pct'],
                    'threshold': self.thresholds['memory_usage_critical']
                })
            elif system_metrics.get('memory', {}).get('used_pct', 0) > self.thresholds['memory_usage_warning']:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'metric': 'memory_usage',
                    'message': f"High memory usage: {system_metrics['memory']['used_pct']:.1f}%",
                    'value': system_metrics['memory']['used_pct'],
                    'threshold': self.thresholds['memory_usage_warning']
                })

            # CPU alerts
            if system_metrics.get('cpu', {}).get('usage_pct', 0) > self.thresholds['cpu_usage_critical']:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'metric': 'cpu_usage',
                    'message': f"Critical CPU usage: {system_metrics['cpu']['usage_pct']:.1f}%",
                    'value': system_metrics['cpu']['usage_pct'],
                    'threshold': self.thresholds['cpu_usage_critical']
                })
            elif system_metrics.get('cpu', {}).get('usage_pct', 0) > self.thresholds['cpu_usage_warning']:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'metric': 'cpu_usage',
                    'message': f"High CPU usage: {system_metrics['cpu']['usage_pct']:.1f}%",
                    'value': system_metrics['cpu']['usage_pct'],
                    'threshold': self.thresholds['cpu_usage_warning']
                })

            # Disk alerts
            if system_metrics.get('disk', {}).get('used_pct', 0) > self.thresholds['disk_usage_critical']:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'metric': 'disk_usage',
                    'message': f"Critical disk usage: {system_metrics['disk']['used_pct']:.1f}%",
                    'value': system_metrics['disk']['used_pct'],
                    'threshold': self.thresholds['disk_usage_critical']
                })
            elif system_metrics.get('disk', {}).get('used_pct', 0) > self.thresholds['disk_usage_warning']:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'metric': 'disk_usage',
                    'message': f"High disk usage: {system_metrics['disk']['used_pct']:.1f}%",
                    'value': system_metrics['disk']['used_pct'],
                    'threshold': self.thresholds['disk_usage_warning']
                })

            # API alerts
            for api_name, api_data in api_metrics.get('apis', {}).items():
                if api_data['status'] == 'error':
                    alerts.append({
                        'type': 'api',
                        'severity': 'high',
                        'metric': 'api_health',
                        'message': f"API {api_name} is down: {api_data.get('error', 'Unknown error')}",
                        'value': 0,
                        'threshold': 1,
                        'api_name': api_name
                    })
                elif api_data.get('response_time_ms', 0) > self.thresholds['api_response_time_critical']:
                    alerts.append({
                        'type': 'api',
                        'severity': 'high',
                        'metric': 'api_response_time',
                        'message': f"API {api_name} slow response: {api_data['response_time_ms']:.0f}ms",
                        'value': api_data['response_time_ms'],
                        'threshold': self.thresholds['api_response_time_critical'],
                        'api_name': api_name
                    })

            # Error rate alerts
            error_rate = error_metrics.get('error_rate_pct', 0)
            if error_rate > self.thresholds['error_rate_critical']:
                alerts.append({
                    'type': 'system',
                    'severity': 'critical',
                    'metric': 'error_rate',
                    'message': f"Critical error rate: {error_rate:.2f}%",
                    'value': error_rate,
                    'threshold': self.thresholds['error_rate_critical']
                })
            elif error_rate > self.thresholds['error_rate_warning']:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning',
                    'metric': 'error_rate',
                    'message': f"High error rate: {error_rate:.2f}%",
                    'value': error_rate,
                    'threshold': self.thresholds['error_rate_warning']
                })

            return alerts

        except Exception as e:
            logger.error(f"Error checking alert conditions: {str(e)}")
            return []

    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run one complete monitoring cycle."""
        try:
            cycle_results = {
                'timestamp': datetime.now().isoformat(),
                'system_metrics': {},
                'api_metrics': {},
                'error_metrics': {},
                'alerts': []
            }

            # Collect system metrics
            cycle_results['system_metrics'] = self.collect_system_metrics()

            # Check API health (less frequently)
            current_time = datetime.now()
            if (current_time - self.last_api_check).total_seconds() >= self.api_check_interval:
                cycle_results['api_metrics'] = await self.check_api_health()
                self.last_api_check = current_time
            else:
                # Use last API metrics
                cycle_results['api_metrics'] = self.api_metrics[-1] if self.api_metrics else {}

            # Analyze log errors
            cycle_results['error_metrics'] = self.analyze_log_errors()

            # Check for alerts
            cycle_results['alerts'] = self.check_alert_conditions(
                cycle_results['system_metrics'],
                cycle_results['api_metrics'],
                cycle_results['error_metrics']
            )

            # Log cycle summary
            alert_count = len(cycle_results['alerts'])
            if alert_count > 0:
                logger.warning(f"Monitoring cycle completed with {alert_count} alerts")
            else:
                logger.debug("Monitoring cycle completed successfully")

            return cycle_results

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}")
            return {}

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        try:
            current_time = datetime.now()

            # Latest metrics
            latest_system = self.system_metrics[-1] if self.system_metrics else {}
            latest_api = self.api_metrics[-1] if self.api_metrics else {}
            latest_errors = self.error_metrics[-1] if self.error_metrics else {}

            return {
                'timestamp': current_time.isoformat(),
                'monitoring_status': 'active' if self.is_monitoring else 'inactive',
                'data_points': {
                    'system_metrics': len(self.system_metrics),
                    'api_metrics': len(self.api_metrics),
                    'error_metrics': len(self.error_metrics)
                },
                'current_status': {
                    'system_health': 'healthy' if latest_system else 'unknown',
                    'api_health': 'healthy' if latest_api else 'unknown',
                    'error_rate': latest_errors.get('error_rate_pct', 0)
                },
                'latest_metrics': {
                    'memory_usage_pct': latest_system.get('memory', {}).get('used_pct', 0),
                    'cpu_usage_pct': latest_system.get('cpu', {}).get('usage_pct', 0),
                    'disk_usage_pct': latest_system.get('disk', {}).get('used_pct', 0)
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics summary: {str(e)}")
            return {}
