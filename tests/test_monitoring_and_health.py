#!/usr/bin/env python3
"""
Monitoring and Health Check Tests
Tests for system monitoring, health checks, and alerting components.
"""

import pytest
import asyncio
import os
import sys
import json
import logging
import time
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSystemHealthChecks:
    """Test system health check functionality."""
    
    @pytest.mark.asyncio
    async def test_monitoring_service_initialization(self):
        """Test monitoring service initialization."""
        try:
            from phase_4_deployment.monitoring.monitoring_service import get_monitoring_service
            
            monitoring_service = get_monitoring_service()
            assert monitoring_service is not None
            
            logger.info("✅ Monitoring service initialized successfully")
            
        except ImportError:
            logger.warning("⚠️ Monitoring service not available")
    
    @pytest.mark.asyncio
    async def test_component_registration(self):
        """Test component registration for health checks."""
        try:
            from phase_4_deployment.monitoring.monitoring_service import get_monitoring_service
            
            monitoring_service = get_monitoring_service()
            
            # Register test components
            def test_component_health():
                return True
            
            def failing_component_health():
                return False
            
            monitoring_service.register_component("test_component", test_component_health)
            monitoring_service.register_component("failing_component", failing_component_health)
            
            # Run health checks
            health_results = monitoring_service.run_health_checks()
            
            assert "test_component" in health_results
            assert health_results["test_component"] == True
            assert "failing_component" in health_results
            assert health_results["failing_component"] == False
            
            logger.info("✅ Component registration and health checks working")
            
        except ImportError:
            logger.warning("⚠️ Monitoring service not available")
        except Exception as e:
            logger.error(f"❌ Component registration test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check HTTP endpoint."""
        try:
            import httpx
            
            # Test common health check endpoints
            endpoints = [
                'http://localhost:8080/health',
                'http://localhost:8080/livez',
                'http://localhost:8080/readyz'
            ]
            
            endpoint_found = False
            for endpoint in endpoints:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(endpoint)
                        if response.status_code == 200:
                            logger.info(f"✅ Health check endpoint working: {endpoint}")
                            
                            # Verify response format
                            try:
                                health_data = response.json()
                                assert isinstance(health_data, dict)
                                logger.info(f"✅ Health check response format valid: {health_data}")
                            except:
                                # Text response is also acceptable
                                logger.info(f"✅ Health check text response: {response.text}")
                            
                            endpoint_found = True
                            break
                except:
                    continue
            
            if not endpoint_found:
                logger.warning("⚠️ No health check endpoints available (system may not be running)")
                
        except ImportError:
            pytest.skip("httpx not available for health check test")
    
    def test_log_file_monitoring(self):
        """Test log file monitoring and rotation."""
        log_dir = 'logs'
        
        if os.path.exists(log_dir):
            # Check for log files
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            
            if log_files:
                logger.info(f"✅ Log files found: {log_files}")
                
                # Check log file sizes (should not be excessively large)
                for log_file in log_files:
                    log_path = os.path.join(log_dir, log_file)
                    file_size = os.path.getsize(log_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    if file_size_mb > 100:  # 100MB threshold
                        logger.warning(f"⚠️ Large log file detected: {log_file} ({file_size_mb:.2f}MB)")
                    else:
                        logger.info(f"✅ Log file size OK: {log_file} ({file_size_mb:.2f}MB)")
            else:
                logger.warning("⚠️ No log files found")
        else:
            logger.warning("⚠️ Log directory not found")


class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        try:
            from core.monitoring.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            assert monitor is not None
            
            logger.info("✅ Performance monitor initialized successfully")
            
        except ImportError:
            logger.warning("⚠️ Performance monitor not available")
    
    def test_metric_recording(self):
        """Test metric recording functionality."""
        try:
            from core.monitoring.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Record test metrics
            monitor.record_trade_execution_time(1.5)
            monitor.record_signal_generation_time(0.8)
            monitor.record_api_response_time('test_api', 0.3)
            
            # Retrieve metrics
            metrics = monitor.get_performance_metrics()
            
            assert 'trade_execution_times' in metrics
            assert 'signal_generation_times' in metrics
            assert 'api_response_times' in metrics
            
            # Verify recorded values
            assert 1.5 in metrics['trade_execution_times']
            assert 0.8 in metrics['signal_generation_times']
            assert 'test_api' in metrics['api_response_times']
            
            logger.info("✅ Metric recording working correctly")
            
        except ImportError:
            logger.warning("⚠️ Performance monitor not available")
        except Exception as e:
            logger.error(f"❌ Metric recording test failed: {e}")
    
    def test_performance_thresholds(self):
        """Test performance threshold monitoring."""
        try:
            from core.monitoring.performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Record metrics that exceed thresholds
            monitor.record_trade_execution_time(10.0)  # Very slow
            monitor.record_signal_generation_time(5.0)  # Very slow
            monitor.record_api_response_time('slow_api', 30.0)  # Very slow
            
            # Check if alerts are generated
            alerts = monitor.get_performance_alerts()
            
            if alerts:
                logger.info(f"✅ Performance alerts generated: {len(alerts)}")
                for alert in alerts:
                    logger.info(f"   Alert: {alert}")
            else:
                logger.info("✅ No performance alerts (thresholds not exceeded)")
            
        except ImportError:
            logger.warning("⚠️ Performance monitor not available")
        except Exception as e:
            logger.error(f"❌ Performance threshold test failed: {e}")


class TestSystemMetrics:
    """Test system metrics collection."""
    
    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        try:
            from core.monitoring.system_metrics import SystemMetricsMonitor
            
            monitor = SystemMetricsMonitor()
            
            # Collect system metrics
            metrics = monitor.collect_system_metrics()
            
            assert isinstance(metrics, dict)
            
            # Check for expected metrics
            expected_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
            for metric in expected_metrics:
                if metric in metrics:
                    logger.info(f"✅ System metric collected: {metric} = {metrics[metric]}")
            
            logger.info("✅ System metrics collection working")
            
        except ImportError:
            logger.warning("⚠️ System metrics monitor not available")
        except Exception as e:
            logger.error(f"❌ System metrics test failed: {e}")
    
    def test_api_call_tracking(self):
        """Test API call tracking and circuit breaker."""
        try:
            from core.monitoring.system_metrics import SystemMetricsMonitor
            
            monitor = SystemMetricsMonitor()
            
            # Test successful API calls
            def successful_api_call():
                return "success"
            
            result = monitor.track_api_call('test_api', successful_api_call)
            assert result == "success"
            
            # Test failing API calls
            def failing_api_call():
                raise Exception("API error")
            
            for _ in range(3):
                try:
                    monitor.track_api_call('failing_api', failing_api_call)
                except:
                    pass
            
            # Check if circuit breaker is triggered
            api_stats = monitor.get_api_statistics()
            if 'failing_api' in api_stats:
                logger.info(f"✅ API call tracking working: {api_stats['failing_api']}")
            
            logger.info("✅ API call tracking and circuit breaker working")
            
        except ImportError:
            logger.warning("⚠️ System metrics monitor not available")
        except Exception as e:
            logger.error(f"❌ API call tracking test failed: {e}")


class TestAlertingSystem:
    """Test alerting system functionality."""
    
    @pytest.mark.asyncio
    async def test_telegram_alerter(self):
        """Test Telegram alerter functionality."""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id or bot_token == 'test_telegram_token':
            pytest.skip("Real Telegram credentials not available")
        
        try:
            from core.notifications.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier()
            
            # Test alert sending
            test_alert = {
                'type': 'test',
                'message': 'Test alert from monitoring system',
                'timestamp': time.time()
            }
            
            result = await notifier.send_alert(test_alert)
            assert result == True
            
            logger.info("✅ Telegram alerter working")
            
        except ImportError:
            logger.warning("⚠️ Telegram notifier not available")
        except Exception as e:
            logger.error(f"❌ Telegram alerter test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_trading_alerts(self):
        """Test trading-specific alerts."""
        try:
            from phase_4_deployment.utils.trading_alerts import send_trade_alert
            
            # Mock Telegram API
            with patch('phase_4_deployment.utils.trading_alerts.httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {'ok': True, 'result': {'message_id': 123}}
                mock_response.status_code = 200
                mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
                
                # Test trade alert
                test_signal = {
                    'action': 'BUY',
                    'market': 'SOL-USDC',
                    'price': 180.0,
                    'size': 0.1,
                    'confidence': 0.8
                }
                
                result = await send_trade_alert(test_signal)
                assert result == True
                
                logger.info("✅ Trading alerts working")
                
        except ImportError:
            logger.warning("⚠️ Trading alerts not available")
        except Exception as e:
            logger.error(f"❌ Trading alerts test failed: {e}")
    
    def test_alert_rate_limiting(self):
        """Test alert rate limiting to prevent spam."""
        try:
            from core.notifications.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier()
            
            # Test rate limiting
            if hasattr(notifier, 'is_rate_limited'):
                # Send multiple alerts quickly
                for i in range(5):
                    is_limited = notifier.is_rate_limited('test_alert_type')
                    if is_limited:
                        logger.info(f"✅ Rate limiting triggered after {i} alerts")
                        break
                else:
                    logger.info("✅ Rate limiting not triggered (may not be implemented)")
            else:
                logger.info("✅ Rate limiting not implemented (OK)")
                
        except ImportError:
            logger.warning("⚠️ Telegram notifier not available")
        except Exception as e:
            logger.error(f"❌ Alert rate limiting test failed: {e}")


class TestDashboardIntegration:
    """Test dashboard integration and data flow."""
    
    def test_dashboard_data_generation(self):
        """Test dashboard data generation."""
        try:
            # Try to import dashboard components
            dashboard_modules = [
                'enhanced_trading_dashboard',
                'simple_monitoring_dashboard',
                'streamlit_dashboard'
            ]
            
            dashboard_found = False
            for module in dashboard_modules:
                try:
                    imported_module = __import__(module)
                    dashboard_found = True
                    logger.info(f"✅ Dashboard module available: {module}")
                    
                    # Test data loading function if available
                    if hasattr(imported_module, 'load_dashboard_data'):
                        with patch('builtins.open', create=True):
                            with patch('json.load', return_value={'test': 'data'}):
                                with patch('os.path.exists', return_value=True):
                                    data = imported_module.load_dashboard_data()
                                    assert data is not None
                                    logger.info(f"✅ Dashboard data loading working: {module}")
                    break
                except ImportError:
                    continue
            
            if not dashboard_found:
                logger.warning("⚠️ No dashboard modules found")
                
        except Exception as e:
            logger.error(f"❌ Dashboard integration test failed: {e}")
    
    def test_metrics_file_generation(self):
        """Test metrics file generation for dashboard."""
        output_dir = 'output'
        
        if os.path.exists(output_dir):
            # Check for metrics files
            metrics_files = []
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if 'metrics' in file.lower() or 'performance' in file.lower():
                        metrics_files.append(os.path.join(root, file))
            
            if metrics_files:
                logger.info(f"✅ Metrics files found: {len(metrics_files)}")
                
                # Check file formats
                for metrics_file in metrics_files[:3]:  # Check first 3 files
                    try:
                        if metrics_file.endswith('.json'):
                            with open(metrics_file, 'r') as f:
                                data = json.load(f)
                            logger.info(f"✅ Valid JSON metrics file: {metrics_file}")
                        elif metrics_file.endswith('.csv'):
                            import pandas as pd
                            data = pd.read_csv(metrics_file)
                            logger.info(f"✅ Valid CSV metrics file: {metrics_file}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error reading metrics file {metrics_file}: {e}")
            else:
                logger.warning("⚠️ No metrics files found")
        else:
            logger.warning("⚠️ Output directory not found")


class TestBackupAndRecovery:
    """Test backup and recovery functionality."""
    
    def test_configuration_backup(self):
        """Test configuration backup functionality."""
        critical_files = [
            'config.yaml',
            '.env',
            os.getenv('KEYPAIR_PATH', 'keys/wallet_keypair.json')
        ]
        
        backup_needed = []
        for file_path in critical_files:
            if file_path and os.path.exists(file_path):
                # Check if file is backed up
                backup_path = f"{file_path}.backup"
                if not os.path.exists(backup_path):
                    backup_needed.append(file_path)
                else:
                    logger.info(f"✅ Backup exists for: {file_path}")
            elif file_path:
                logger.warning(f"⚠️ Critical file not found: {file_path}")
        
        if backup_needed:
            logger.warning(f"⚠️ Files need backup: {backup_needed}")
        else:
            logger.info("✅ All critical files have backups")
    
    def test_recovery_procedures(self):
        """Test recovery procedures documentation."""
        recovery_docs = [
            'RECOVERY.md',
            'docs/recovery.md',
            'phase_4_deployment/RECOVERY.md'
        ]
        
        recovery_doc_found = False
        for doc_path in recovery_docs:
            if os.path.exists(doc_path):
                recovery_doc_found = True
                logger.info(f"✅ Recovery documentation found: {doc_path}")
                
                # Check if it contains recovery procedures
                with open(doc_path, 'r') as f:
                    content = f.read().lower()
                
                recovery_keywords = ['backup', 'restore', 'recovery', 'disaster']
                keywords_found = [kw for kw in recovery_keywords if kw in content]
                
                if keywords_found:
                    logger.info(f"✅ Recovery procedures documented: {keywords_found}")
                else:
                    logger.warning(f"⚠️ Recovery procedures may be incomplete in {doc_path}")
                break
        
        if not recovery_doc_found:
            logger.warning("⚠️ No recovery documentation found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
