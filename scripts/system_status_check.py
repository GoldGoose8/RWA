#!/usr/bin/env python3
"""
Comprehensive System Status Check for Synergy7 Trading System
Provides a complete overview of system health, components, and dashboard status.
"""

import asyncio
import json
import os
import sys
import subprocess
import requests
from datetime import datetime
from pathlib import Path
import psutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class SystemStatusChecker:
    """Comprehensive system status checker."""

    def __init__(self):
        """Initialize the system status checker."""
        self.status = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'UNKNOWN',
            'components': {},
            'dashboards': {},
            'data_sources': {},
            'system_resources': {},
            'recommendations': []
        }

    def check_system_resources(self):
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            self.status['system_resources'] = {
                'cpu_usage_percent': cpu_percent,
                'memory_usage_percent': memory.percent,
                'disk_usage_percent': disk.percent,
                'available_memory_gb': round(memory.available / (1024**3), 2),
                'status': 'HEALTHY' if cpu_percent < 80 and memory.percent < 80 else 'WARNING'
            }

            if cpu_percent > 80:
                self.status['recommendations'].append("High CPU usage detected - consider optimizing processes")
            if memory.percent > 80:
                self.status['recommendations'].append("High memory usage detected - consider restarting services")

        except Exception as e:
            self.status['system_resources'] = {'status': 'ERROR', 'error': str(e)}

    def check_core_components(self):
        """Check core system components."""
        components = {}

        # Check configuration
        try:
            import yaml
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            components['configuration'] = {
                'status': 'HEALTHY',
                'details': 'Configuration loaded successfully'
            }
        except Exception as e:
            components['configuration'] = {
                'status': 'ERROR',
                'details': f'Configuration error: {str(e)}'
            }

        # Check risk management
        try:
            # Check if risk management files exist
            risk_files = [
                'core/risk/position_sizer.py',
                'core/risk/portfolio_risk_manager.py',
                'core/risk/circuit_breaker.py'
            ]
            missing_files = [f for f in risk_files if not os.path.exists(f)]
            if missing_files:
                components['risk_management'] = {
                    'status': 'WARNING',
                    'details': f'Missing risk files: {missing_files}'
                }
            else:
                components['risk_management'] = {
                    'status': 'HEALTHY',
                    'details': 'Risk management files present'
                }
        except Exception as e:
            components['risk_management'] = {
                'status': 'ERROR',
                'details': f'Risk management error: {str(e)}'
            }

        # Check trading scripts
        try:
            # Check if main trading scripts exist
            trading_scripts = [
                'scripts/unified_live_trading.py',
                'scripts/execute_10_minute_session.py',
                'phase_4_deployment/unified_dashboard/app.py'
            ]
            missing_scripts = [f for f in trading_scripts if not os.path.exists(f)]
            if missing_scripts:
                components['trading_system'] = {
                    'status': 'WARNING',
                    'details': f'Missing scripts: {missing_scripts}'
                }
            else:
                components['trading_system'] = {
                    'status': 'HEALTHY',
                    'details': 'Trading system scripts present'
                }
        except Exception as e:
            components['trading_system'] = {
                'status': 'ERROR',
                'details': f'Trading system error: {str(e)}'
            }

        self.status['components'] = components

    def check_data_sources(self):
        """Check data source availability and freshness."""
        data_sources = {}

        sources = {
            'enhanced_live_trading': 'output/enhanced_live_trading/latest_metrics.json',
            'production': 'output/live_production/dashboard/latest_metrics.json',
            'paper_trading': 'output/paper_trading/dashboard/latest_metrics.json',
            'wallet': 'output/wallet/wallet_balance.json'
        }

        for name, path in sources.items():
            if os.path.exists(path):
                try:
                    # Check file age
                    file_age = datetime.now().timestamp() - os.path.getmtime(path)

                    # Load and validate data
                    with open(path, 'r') as f:
                        data = json.load(f)

                    status = 'HEALTHY' if file_age < 3600 else 'STALE'  # 1 hour threshold

                    data_sources[name] = {
                        'status': status,
                        'path': path,
                        'age_minutes': round(file_age / 60, 1),
                        'data_points': len(data) if isinstance(data, dict) else 0
                    }

                except Exception as e:
                    data_sources[name] = {
                        'status': 'ERROR',
                        'path': path,
                        'error': str(e)
                    }
            else:
                data_sources[name] = {
                    'status': 'MISSING',
                    'path': path
                }

        self.status['data_sources'] = data_sources

    def check_dashboard_status(self):
        """Check dashboard accessibility and status."""
        dashboards = {}

        # Check if dashboard scripts exist
        dashboard_scripts = {
            'enhanced_trading': 'enhanced_trading_dashboard.py',
            'monitoring': 'simple_monitoring_dashboard.py',
            'production': 'scripts/update_dashboard_for_production.py'
        }

        for name, script in dashboard_scripts.items():
            if os.path.exists(script):
                dashboards[f'{name}_script'] = {
                    'status': 'AVAILABLE',
                    'path': script
                }
            else:
                dashboards[f'{name}_script'] = {
                    'status': 'MISSING',
                    'path': script
                }

        # Check if dashboards are running
        dashboard_ports = {
            'enhanced_trading': 8504,
            'monitoring': 8503
        }

        for name, port in dashboard_ports.items():
            try:
                response = requests.get(f'http://localhost:{port}', timeout=5)
                dashboards[f'{name}_service'] = {
                    'status': 'RUNNING',
                    'port': port,
                    'url': f'http://localhost:{port}'
                }
            except requests.exceptions.RequestException:
                dashboards[f'{name}_service'] = {
                    'status': 'NOT_RUNNING',
                    'port': port
                }

        # Check Streamlit availability
        try:
            result = subprocess.run(['streamlit', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                dashboards['streamlit'] = {
                    'status': 'AVAILABLE',
                    'version': result.stdout.strip()
                }
            else:
                dashboards['streamlit'] = {
                    'status': 'ERROR',
                    'error': 'Streamlit command failed'
                }
        except Exception as e:
            dashboards['streamlit'] = {
                'status': 'ERROR',
                'error': str(e)
            }

        self.status['dashboards'] = dashboards

    def calculate_overall_health(self):
        """Calculate overall system health score."""
        health_scores = []

        # System resources
        if self.status['system_resources'].get('status') == 'HEALTHY':
            health_scores.append(1.0)
        elif self.status['system_resources'].get('status') == 'WARNING':
            health_scores.append(0.7)
        else:
            health_scores.append(0.0)

        # Components
        component_health = []
        for comp in self.status['components'].values():
            component_health.append(1.0 if comp['status'] == 'HEALTHY' else 0.0)

        if component_health:
            health_scores.append(sum(component_health) / len(component_health))

        # Data sources
        data_health = []
        for source in self.status['data_sources'].values():
            if source['status'] == 'HEALTHY':
                data_health.append(1.0)
            elif source['status'] == 'STALE':
                data_health.append(0.5)
            else:
                data_health.append(0.0)

        if data_health:
            health_scores.append(sum(data_health) / len(data_health))

        # Calculate overall score
        overall_score = sum(health_scores) / len(health_scores) if health_scores else 0.0

        if overall_score >= 0.8:
            self.status['overall_health'] = 'HEALTHY'
        elif overall_score >= 0.6:
            self.status['overall_health'] = 'WARNING'
        else:
            self.status['overall_health'] = 'CRITICAL'

        self.status['health_score'] = round(overall_score * 100, 1)

    def generate_recommendations(self):
        """Generate system recommendations."""
        # Check for missing data sources
        missing_sources = [name for name, data in self.status['data_sources'].items()
                          if data['status'] == 'MISSING']
        if missing_sources:
            self.status['recommendations'].append(f"Missing data sources: {', '.join(missing_sources)}")

        # Check for stale data
        stale_sources = [name for name, data in self.status['data_sources'].items()
                        if data['status'] == 'STALE']
        if stale_sources:
            self.status['recommendations'].append(f"Stale data sources: {', '.join(stale_sources)}")

        # Check for non-running dashboards
        not_running = [name for name, data in self.status['dashboards'].items()
                      if 'service' in name and data['status'] == 'NOT_RUNNING']
        if not_running:
            self.status['recommendations'].append(f"Start dashboard services: {', '.join(not_running)}")

        # Check component errors
        error_components = [name for name, data in self.status['components'].items()
                           if data['status'] == 'ERROR']
        if error_components:
            self.status['recommendations'].append(f"Fix component errors: {', '.join(error_components)}")

    def run_comprehensive_check(self):
        """Run comprehensive system status check."""
        print("🔍 Running Comprehensive System Status Check")
        print("="*60)

        self.check_system_resources()
        self.check_core_components()
        self.check_data_sources()
        self.check_dashboard_status()
        self.calculate_overall_health()
        self.generate_recommendations()

        return self.status

    def print_status_report(self):
        """Print formatted status report."""
        status = self.status

        # Header
        health_icon = "🟢" if status['overall_health'] == 'HEALTHY' else "🟡" if status['overall_health'] == 'WARNING' else "🔴"
        print(f"\n{health_icon} SYSTEM STATUS: {status['overall_health']} ({status['health_score']}%)")
        print("="*60)

        # System Resources
        print("💻 SYSTEM RESOURCES:")
        resources = status['system_resources']
        if 'cpu_usage_percent' in resources:
            print(f"   CPU: {resources['cpu_usage_percent']}%")
            print(f"   Memory: {resources['memory_usage_percent']}%")
            print(f"   Disk: {resources['disk_usage_percent']}%")

        # Components
        print("\n🔧 CORE COMPONENTS:")
        for name, comp in status['components'].items():
            icon = "✅" if comp['status'] == 'HEALTHY' else "❌"
            print(f"   {icon} {name.replace('_', ' ').title()}: {comp['status']}")

        # Data Sources
        print("\n📊 DATA SOURCES:")
        for name, source in status['data_sources'].items():
            if source['status'] == 'HEALTHY':
                icon = "✅"
            elif source['status'] == 'STALE':
                icon = "🟡"
            else:
                icon = "❌"
            print(f"   {icon} {name.replace('_', ' ').title()}: {source['status']}")

        # Dashboards
        print("\n📈 DASHBOARDS:")
        for name, dash in status['dashboards'].items():
            if 'service' in name:
                icon = "🟢" if dash['status'] == 'RUNNING' else "🔴"
                print(f"   {icon} {name.replace('_', ' ').title()}: {dash['status']}")
                if dash['status'] == 'RUNNING':
                    print(f"      URL: {dash.get('url', 'N/A')}")

        # Recommendations
        if status['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in status['recommendations']:
                print(f"   • {rec}")

        print("="*60)


def main():
    """Main function to run system status check."""
    checker = SystemStatusChecker()
    status = checker.run_comprehensive_check()
    checker.print_status_report()

    # Save detailed report
    report_path = f"output/system_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(status, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_path}")

    return status


if __name__ == "__main__":
    main()
