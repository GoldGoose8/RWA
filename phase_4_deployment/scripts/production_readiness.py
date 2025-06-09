#!/usr/bin/env python3
"""
Production Readiness Checker for Q5 Trading System

This script checks the production readiness of the Q5 Trading System
and provides a score and recommendations for improvement.
"""

import os
import sys
import json
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('production_readiness')

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class ProductionReadinessChecker:
    """
    Checker for production readiness of the Q5 Trading System.
    """

    def __init__(self, base_dir: str = None):
        """
        Initialize the ProductionReadinessChecker.

        Args:
            base_dir: Base directory of the Q5 Trading System
        """
        # Use the provided base directory or default to /Users/Quantzavant/HedgeFund
        self.base_dir = base_dir or '/Users/Quantzavant/HedgeFund'

        print(f"Base directory: {self.base_dir}")

        # Set paths
        self.phase_4_dir = os.path.join(self.base_dir, 'phase_4_deployment')
        self.env_file = os.path.join(self.base_dir, '.env')
        self.config_file = os.path.join(self.base_dir, 'config.yaml')

        # Check results
        self.results = {
            'security': {'score': 0, 'max_score': 10, 'checks': []},
            'configuration': {'score': 0, 'max_score': 10, 'checks': []},
            'dependencies': {'score': 0, 'max_score': 10, 'checks': []},
            'testing': {'score': 0, 'max_score': 10, 'checks': []},
            'monitoring': {'score': 0, 'max_score': 10, 'checks': []},
            'deployment': {'score': 0, 'max_score': 10, 'checks': []}
        }

        # Recommendations
        self.recommendations = []

    def check_security(self) -> None:
        """Check security aspects."""
        category = 'security'

        # Check if wallet is securely stored
        wallet_address = self._get_env_var('WALLET_ADDRESS')
        if wallet_address:
            wallet_file = os.path.join(self.phase_4_dir, 'keys', f"{wallet_address}.wallet")
            if os.path.exists(wallet_file):
                self._add_check(category, 'Wallet is securely stored', True, 3)
            else:
                self._add_check(category, 'Wallet is not securely stored', False, 3)
                self.recommendations.append(
                    "Run 'python wallet_sync/migrate_wallet.py' to securely store wallet credentials"
                )
        else:
            self._add_check(category, 'No wallet address found', False, 3)
            self.recommendations.append("Set WALLET_ADDRESS in .env file")

        # Check if private key is exposed in .env
        private_key = self._get_env_var('WALLET_PRIVATE_KEY')
        if private_key and private_key != "***SECURELY_STORED***":
            self._add_check(category, 'Private key is exposed in .env file', False, 3)
            self.recommendations.append(
                "Run 'python scripts/secure_env.py' to secure sensitive information in .env file"
            )
        else:
            self._add_check(category, 'Private key is not exposed in .env file', True, 3)

        # Check if API keys are exposed in version control
        gitignore_file = os.path.join(self.base_dir, '.gitignore')
        if os.path.exists(gitignore_file):
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()

            if '.env' in gitignore_content:
                self._add_check(category, '.env file is ignored in version control', True, 2)
            else:
                self._add_check(category, '.env file is not ignored in version control', False, 2)
                self.recommendations.append("Add '.env' to .gitignore file")

            if 'keys/' in gitignore_content:
                self._add_check(category, 'Keys directory is ignored in version control', True, 2)
            else:
                self._add_check(category, 'Keys directory is not ignored in version control', False, 2)
                self.recommendations.append("Add 'keys/' to .gitignore file")
        else:
            self._add_check(category, '.gitignore file not found', False, 4)
            self.recommendations.append("Create .gitignore file and add '.env' and 'keys/' to it")

    def check_configuration(self) -> None:
        """Check configuration aspects."""
        category = 'configuration'

        # Check if config.yaml exists
        if os.path.exists(self.config_file):
            self._add_check(category, 'config.yaml file exists', True, 2)

            # Check if config.yaml has required sections
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)

                required_sections = ['mode', 'solana', 'wallet', 'risk', 'execution', 'monitoring']
                missing_sections = [section for section in required_sections if section not in config]

                if not missing_sections:
                    self._add_check(category, 'config.yaml has all required sections', True, 3)
                else:
                    self._add_check(category, f'config.yaml missing sections: {", ".join(missing_sections)}', False, 3)
                    self.recommendations.append(f"Add missing sections to config.yaml: {', '.join(missing_sections)}")
            except Exception as e:
                self._add_check(category, f'Error parsing config.yaml: {str(e)}', False, 3)
                self.recommendations.append("Fix config.yaml format")
        else:
            self._add_check(category, 'config.yaml file not found', False, 2)
            self.recommendations.append("Create config.yaml file")

        # Check if .env file exists
        if os.path.exists(self.env_file):
            self._add_check(category, '.env file exists', True, 2)

            # Check if .env has required variables
            required_vars = ['SOLANA_RPC_URL', 'HELIUS_API_KEY', 'WALLET_ADDRESS']
            missing_vars = []

            for var in required_vars:
                if not self._get_env_var(var):
                    missing_vars.append(var)

            if not missing_vars:
                self._add_check(category, '.env has all required variables', True, 3)
            else:
                self._add_check(category, f'.env missing variables: {", ".join(missing_vars)}', False, 3)
                self.recommendations.append(f"Add missing variables to .env file: {', '.join(missing_vars)}")
        else:
            self._add_check(category, '.env file not found', False, 2)
            self.recommendations.append("Create .env file")

    def check_dependencies(self) -> None:
        """Check dependencies."""
        category = 'dependencies'

        # Run dependency checker script
        dependency_checker = os.path.join(self.phase_4_dir, 'check_dependencies.py')
        if os.path.exists(dependency_checker):
            self._add_check(category, 'Dependency checker script exists', True, 2)

            try:
                result = subprocess.run(
                    [sys.executable, dependency_checker],
                    capture_output=True,
                    text=True,
                    check=False
                )

                if "All dependencies are installed" in result.stdout:
                    self._add_check(category, 'All dependencies are installed', True, 5)
                else:
                    missing_deps = []
                    for line in result.stdout.splitlines():
                        if "❌ Missing" in line:
                            package = line.split('-')[0].strip()
                            missing_deps.append(package)

                    if missing_deps:
                        self._add_check(category, f'Missing dependencies: {", ".join(missing_deps)}', False, 5)
                        self.recommendations.append(f"Install missing dependencies: pip install {' '.join(missing_deps)}")
                    else:
                        self._add_check(category, 'Dependency check inconclusive', False, 5)
                        self.recommendations.append("Run 'python check_dependencies.py' to check dependencies")
            except Exception as e:
                self._add_check(category, f'Error running dependency checker: {str(e)}', False, 5)
                self.recommendations.append("Fix dependency checker script")
        else:
            self._add_check(category, 'Dependency checker script not found', False, 2)
            self.recommendations.append("Create dependency checker script")

        # Check if requirements.txt or pyproject.toml exists
        if os.path.exists(os.path.join(self.base_dir, 'requirements.txt')):
            self._add_check(category, 'requirements.txt file exists', True, 3)
        elif os.path.exists(os.path.join(self.base_dir, 'pyproject.toml')):
            self._add_check(category, 'pyproject.toml file exists', True, 3)
        else:
            self._add_check(category, 'No dependency manifest found', False, 3)
            self.recommendations.append("Create requirements.txt or pyproject.toml file")

    def check_testing(self) -> None:
        """Check testing aspects."""
        category = 'testing'

        # Check if simulation test script exists
        simulation_test = os.path.join(self.phase_4_dir, 'run_simulation_test.sh')
        if os.path.exists(simulation_test):
            self._add_check(category, 'Simulation test script exists', True, 3)
        else:
            self._add_check(category, 'Simulation test script not found', False, 3)
            self.recommendations.append("Create simulation test script")

        # Check if verification script exists
        verification_script_paths = [
            os.path.join(self.phase_4_dir, 'verify_simulation.py'),
            os.path.join(self.phase_4_dir, 'verify_simulation.sh'),
            os.path.join(self.phase_4_dir, 'scripts', 'verify_simulation.py'),
            os.path.join(self.base_dir, 'scripts', 'verify_simulation.py')
        ]
        if any(os.path.exists(path) for path in verification_script_paths):
            self._add_check(category, 'Verification script exists', True, 3)
        else:
            self._add_check(category, 'Verification script not found', False, 3)
            self.recommendations.append("Create verification script")

        # Check if unit tests exist
        tests_dir = os.path.join(self.base_dir, 'tests')
        if os.path.exists(tests_dir) and os.path.isdir(tests_dir):
            test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
            if test_files:
                self._add_check(category, f'Unit tests exist ({len(test_files)} files)', True, 4)
            else:
                self._add_check(category, 'No unit test files found', False, 4)
                self.recommendations.append("Create unit tests in tests/ directory")
        else:
            self._add_check(category, 'Tests directory not found', False, 4)
            self.recommendations.append("Create tests/ directory with unit tests")

    def check_monitoring(self) -> None:
        """Check monitoring aspects."""
        category = 'monitoring'

        # Check if monitoring is enabled in config
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)

            if 'monitoring' in config and config['monitoring'].get('enabled', False):
                self._add_check(category, 'Monitoring is enabled in config', True, 3)

                # Check monitoring configuration
                monitoring_config = config['monitoring']
                required_monitoring = ['update_interval', 'log_level']
                missing_monitoring = [field for field in required_monitoring if field not in monitoring_config]

                if not missing_monitoring:
                    self._add_check(category, 'Monitoring configuration is complete', True, 2)
                else:
                    self._add_check(category, f'Monitoring configuration missing fields: {", ".join(missing_monitoring)}', False, 2)
                    self.recommendations.append(f"Add missing monitoring fields to config.yaml: {', '.join(missing_monitoring)}")
            else:
                self._add_check(category, 'Monitoring is not enabled in config', False, 3)
                self.recommendations.append("Enable monitoring in config.yaml")
        except Exception:
            self._add_check(category, 'Could not check monitoring configuration', False, 3)

        # Check if Telegram alerts are configured
        telegram_token = self._get_env_var('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = self._get_env_var('TELEGRAM_CHAT_ID')

        if telegram_token and telegram_chat_id:
            self._add_check(category, 'Telegram alerts are configured', True, 3)
        else:
            self._add_check(category, 'Telegram alerts are not configured', False, 3)
            self.recommendations.append("Configure Telegram alerts in .env file")

        # Check if dashboard exists
        dashboard_app = os.path.join(self.phase_4_dir, 'gui_dashboard', 'app.py')
        if os.path.exists(dashboard_app):
            self._add_check(category, 'Dashboard application exists', True, 2)
        else:
            self._add_check(category, 'Dashboard application not found', False, 2)
            self.recommendations.append("Create dashboard application")

    def check_deployment(self) -> None:
        """Check deployment aspects."""
        category = 'deployment'

        # Check if Docker files exist
        dockerfile = os.path.join(self.phase_4_dir, 'docker_deploy', 'Dockerfile')
        if os.path.exists(dockerfile):
            self._add_check(category, 'Dockerfile exists', True, 3)
        else:
            self._add_check(category, 'Dockerfile not found', False, 3)
            self.recommendations.append("Create Dockerfile for deployment")

        # Check if launch script exists
        launch_script = os.path.join(self.phase_4_dir, 'launch_all.sh')
        if os.path.exists(launch_script):
            self._add_check(category, 'Launch script exists', True, 3)
        else:
            self._add_check(category, 'Launch script not found', False, 3)
            self.recommendations.append("Create launch script")

        # Check if circuit breaker is implemented
        circuit_breaker = os.path.join(self.phase_4_dir, 'core', 'circuit_breaker.py')
        if os.path.exists(circuit_breaker):
            self._add_check(category, 'Circuit breaker is implemented', True, 2)
        else:
            self._add_check(category, 'Circuit breaker not implemented', False, 2)
            self.recommendations.append("Implement circuit breaker for resilience")

        # Check if secure wallet is implemented
        secure_wallet = os.path.join(self.phase_4_dir, 'wallet_sync', 'secure_wallet.py')
        if os.path.exists(secure_wallet):
            self._add_check(category, 'Secure wallet is implemented', True, 2)
        else:
            self._add_check(category, 'Secure wallet not implemented', False, 2)
            self.recommendations.append("Implement secure wallet management")

    def run_all_checks(self) -> None:
        """Run all checks."""
        self.check_security()
        self.check_configuration()
        self.check_dependencies()
        self.check_testing()
        self.check_monitoring()
        self.check_deployment()

    def get_overall_score(self) -> Tuple[int, int]:
        """
        Get overall score.

        Returns:
            Tuple of (score, max_score)
        """
        score = sum(category['score'] for category in self.results.values())
        max_score = sum(category['max_score'] for category in self.results.values())
        return score, max_score

    def print_report(self) -> None:
        """Print the readiness report."""
        print(f"\n{BLUE}======================================{NC}")
        print(f"{BLUE}Q5 TRADING SYSTEM - PRODUCTION READINESS REPORT{NC}")
        print(f"{BLUE}======================================{NC}\n")

        # Print category scores
        for category, data in self.results.items():
            score_pct = (data['score'] / data['max_score']) * 100
            if score_pct >= 80:
                color = GREEN
            elif score_pct >= 50:
                color = YELLOW
            else:
                color = RED

            print(f"{color}{category.upper()}: {data['score']}/{data['max_score']} ({score_pct:.1f}%){NC}")

            # Print checks
            for check in data['checks']:
                status = f"{GREEN}✓{NC}" if check['passed'] else f"{RED}✗{NC}"
                print(f"  {status} {check['description']} ({check['points']} points)")

            print()

        # Print overall score
        score, max_score = self.get_overall_score()
        score_pct = (score / max_score) * 100

        if score_pct >= 80:
            color = GREEN
            rating = "HIGH"
        elif score_pct >= 60:
            color = YELLOW
            rating = "MEDIUM"
        else:
            color = RED
            rating = "LOW"

        print(f"{BLUE}======================================{NC}")
        print(f"{color}OVERALL SCORE: {score}/{max_score} ({score_pct:.1f}%){NC}")
        print(f"{color}PRODUCTION READINESS: {rating}{NC}")
        print(f"{BLUE}======================================{NC}\n")

        # Print recommendations
        if self.recommendations:
            print(f"{YELLOW}RECOMMENDATIONS:{NC}")
            for i, recommendation in enumerate(self.recommendations, 1):
                print(f"{YELLOW}{i}. {recommendation}{NC}")
            print()

    def _add_check(self, category: str, description: str, passed: bool, points: int) -> None:
        """
        Add a check result.

        Args:
            category: Check category
            description: Check description
            passed: Whether the check passed
            points: Points for the check
        """
        self.results[category]['checks'].append({
            'description': description,
            'passed': passed,
            'points': points
        })

        if passed:
            self.results[category]['score'] += points

    def _get_env_var(self, name: str) -> str:
        """
        Get environment variable from .env file.

        Args:
            name: Variable name

        Returns:
            Variable value or empty string if not found
        """
        if not os.path.exists(self.env_file):
            return ""

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith(f"{name}="):
                        value = line[len(f"{name}="):]
                        return value.strip('"\'')

        return ""

def main():
    """Main function."""
    checker = ProductionReadinessChecker()
    checker.run_all_checks()
    checker.print_report()

    # Return exit code based on score
    score, max_score = checker.get_overall_score()
    score_pct = (score / max_score) * 100

    if score_pct >= 60:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
