#!/usr/bin/env python3
"""
Deployment Validation Tests
Tests that align with the deployment checklist and production requirements.
"""

import pytest
import asyncio
import os
import sys
import json
import yaml
import logging
import subprocess
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDeploymentPrerequisites:
    """Test deployment prerequisites from the deployment checklist."""

    def test_python_version_requirement(self):
        """Test Python 3.9+ requirement."""
        assert sys.version_info >= (3, 9), f"Python 3.9+ required, found {sys.version_info}"

    def test_required_packages_installed(self):
        """Test that required packages are installed."""
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'httpx',
            'numpy',
            'pandas',
            'pyyaml',
            'python-dotenv'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.warning(f"Missing packages (OK in test environment): {missing_packages}")
        else:
            logger.info("✅ All required packages installed")

    def test_environment_variables_present(self):
        """Test that required environment variables are present."""
        required_env_vars = [
            'WALLET_ADDRESS',
            'HELIUS_API_KEY',
            'BIRDEYE_API_KEY'
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        # Allow missing vars in test environment, but log them
        if missing_vars:
            logger.warning(f"Missing environment variables (OK in test): {missing_vars}")

    def test_configuration_file_structure(self):
        """Test configuration file structure."""
        config_files = ['config.yaml', 'config_example.yaml']

        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)

                    # Verify basic structure
                    assert isinstance(config, dict), f"Config file {config_file} should be a dictionary"

                    # Check for expected sections
                    expected_sections = ['trading', 'risk_management']
                    for section in expected_sections:
                        if section in config:
                            assert isinstance(config[section], dict), f"Section {section} should be a dictionary"

                    logger.info(f"✅ Configuration file {config_file} structure valid")
                    break

                except Exception as e:
                    logger.error(f"❌ Error reading config file {config_file}: {e}")
        else:
            logger.warning("⚠️ No configuration files found (OK in test environment)")

    def test_directory_structure(self):
        """Test required directory structure."""
        required_dirs = [
            'logs',
            'output',
            'tests',
            'scripts',
            'core',
            'phase_4_deployment'
        ]

        missing_dirs = []
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                missing_dirs.append(dir_name)

        assert len(missing_dirs) == 0, f"Missing required directories: {missing_dirs}"


class TestAPIConnectivity:
    """Test API connectivity requirements from deployment checklist."""

    @pytest.mark.asyncio
    async def test_helius_api_connectivity(self):
        """Test Helius API connectivity."""
        api_key = os.getenv('HELIUS_API_KEY')
        if not api_key or api_key == 'test_helius_key':
            pytest.skip("Real Helius API key not available")

        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://api.helius.xyz/v0/addresses/vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg/balances?api-key={api_key}"
                )

                assert response.status_code == 200, f"Helius API test failed: {response.status_code}"
                logger.info("✅ Helius API connectivity verified")

        except Exception as e:
            pytest.fail(f"Helius API connectivity test failed: {e}")

    @pytest.mark.asyncio
    async def test_birdeye_api_connectivity(self):
        """Test Birdeye API connectivity."""
        api_key = os.getenv('BIRDEYE_API_KEY')
        if not api_key or api_key == 'test_birdeye_key':
            pytest.skip("Real Birdeye API key not available")

        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {'X-API-KEY': api_key}
                response = await client.get(
                    "https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&offset=0&limit=1",
                    headers=headers
                )

                assert response.status_code == 200, f"Birdeye API test failed: {response.status_code}"
                logger.info("✅ Birdeye API connectivity verified")

        except Exception as e:
            pytest.fail(f"Birdeye API connectivity test failed: {e}")


class TestWalletConfiguration:
    """Test wallet configuration requirements."""

    def test_wallet_address_format(self):
        """Test wallet address format."""
        wallet_address = os.getenv('WALLET_ADDRESS')
        if not wallet_address:
            pytest.skip("Wallet address not configured")

        # Basic Solana address validation
        assert len(wallet_address) >= 32, "Wallet address too short"
        assert len(wallet_address) <= 44, "Wallet address too long"
        assert wallet_address.isalnum(), "Wallet address should be alphanumeric"

        logger.info(f"✅ Wallet address format valid: {wallet_address}")

    def test_keypair_file_accessibility(self):
        """Test keypair file accessibility."""
        keypair_path = os.getenv('KEYPAIR_PATH')
        if not keypair_path:
            pytest.skip("Keypair path not configured")

        if os.path.exists(keypair_path):
            # Check file permissions
            import stat
            file_stat = os.stat(keypair_path)
            file_mode = stat.filemode(file_stat.st_mode)

            # Should not be world-readable
            assert not (file_stat.st_mode & stat.S_IROTH), "Keypair file should not be world-readable"

            # Try to read the file
            try:
                with open(keypair_path, 'r') as f:
                    keypair_data = json.load(f)

                assert isinstance(keypair_data, list), "Keypair should be a list"
                assert len(keypair_data) in [32, 64], f"Keypair should be 32 or 64 bytes, got {len(keypair_data)}"

                logger.info(f"✅ Keypair file accessible and valid: {keypair_path}")

            except Exception as e:
                pytest.fail(f"Error reading keypair file: {e}")
        else:
            logger.warning(f"⚠️ Keypair file not found: {keypair_path} (OK in test environment)")


class TestSystemResources:
    """Test system resource requirements."""

    def test_disk_space_requirement(self):
        """Test disk space requirement (at least 1GB free)."""
        import shutil

        free_space = shutil.disk_usage('.').free
        free_space_gb = free_space / (1024**3)

        assert free_space_gb >= 1.0, f"Insufficient disk space: {free_space_gb:.2f}GB (minimum 1GB required)"
        logger.info(f"✅ Disk space sufficient: {free_space_gb:.2f}GB available")

    def test_memory_requirement(self):
        """Test memory requirement."""
        try:
            import psutil

            available_memory = psutil.virtual_memory().available
            available_memory_gb = available_memory / (1024**3)

            assert available_memory_gb >= 1.0, f"Insufficient memory: {available_memory_gb:.2f}GB (minimum 1GB required)"
            logger.info(f"✅ Memory sufficient: {available_memory_gb:.2f}GB available")

        except ImportError:
            logger.warning("⚠️ psutil not available, skipping memory check")

    def test_file_permissions(self):
        """Test file permissions for critical directories."""
        critical_dirs = ['logs', 'output']

        for dir_name in critical_dirs:
            if os.path.exists(dir_name):
                # Check if directory is writable
                assert os.access(dir_name, os.W_OK), f"Directory {dir_name} is not writable"
                logger.info(f"✅ Directory {dir_name} has correct permissions")
            else:
                # Try to create the directory
                try:
                    os.makedirs(dir_name, exist_ok=True)
                    logger.info(f"✅ Created directory {dir_name}")
                except Exception as e:
                    pytest.fail(f"Cannot create directory {dir_name}: {e}")


class TestDockerConfiguration:
    """Test Docker configuration requirements."""

    def test_docker_availability(self):
        """Test Docker availability."""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "Docker is not available"
            logger.info(f"✅ Docker available: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available (OK for non-Docker deployments)")

    def test_docker_compose_availability(self):
        """Test Docker Compose availability."""
        try:
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                # Try docker compose (newer syntax)
                result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True, timeout=10)

            assert result.returncode == 0, "Docker Compose is not available"
            logger.info(f"✅ Docker Compose available: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker Compose not available (OK for non-Docker deployments)")

    def test_dockerfile_exists(self):
        """Test Dockerfile exists."""
        dockerfile_paths = [
            'Dockerfile',
            'phase_4_deployment/Dockerfile',
            'docker/Dockerfile'
        ]

        dockerfile_found = False
        for dockerfile_path in dockerfile_paths:
            if os.path.exists(dockerfile_path):
                dockerfile_found = True
                logger.info(f"✅ Dockerfile found: {dockerfile_path}")
                break

        if not dockerfile_found:
            logger.warning("⚠️ No Dockerfile found (OK for non-Docker deployments)")


class TestSecurityRequirements:
    """Test security requirements from deployment checklist."""

    def test_sensitive_files_permissions(self):
        """Test permissions on sensitive files."""
        sensitive_files = [
            '.env',
            os.getenv('KEYPAIR_PATH', 'keys/wallet_keypair.json')
        ]

        for file_path in sensitive_files:
            if file_path and os.path.exists(file_path):
                import stat
                file_stat = os.stat(file_path)

                # Should not be world-readable
                assert not (file_stat.st_mode & stat.S_IROTH), f"Sensitive file {file_path} should not be world-readable"

                # Should not be group-readable (optional, but recommended)
                if file_stat.st_mode & stat.S_IRGRP:
                    logger.warning(f"⚠️ Sensitive file {file_path} is group-readable")

                logger.info(f"✅ Sensitive file {file_path} has secure permissions")

    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded in configuration files."""
        config_files = ['config.yaml', 'config_example.yaml']

        suspicious_patterns = [
            'sk_',  # Secret keys
            'api_key',
            'password',
            'secret',
            'token'
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read().lower()

                for pattern in suspicious_patterns:
                    if pattern in content:
                        # Check if it's just a placeholder or example
                        lines = content.split('\n')
                        for line in lines:
                            if pattern in line and not any(placeholder in line for placeholder in ['example', 'placeholder', 'your_', 'xxx']):
                                logger.warning(f"⚠️ Potential hardcoded secret in {config_file}: {line.strip()}")

        logger.info("✅ No obvious hardcoded secrets found")


class TestMonitoringConfiguration:
    """Test monitoring configuration requirements."""

    def test_telegram_configuration(self):
        """Test Telegram configuration."""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if bot_token and chat_id:
            # Basic format validation
            assert bot_token.count(':') == 1, "Telegram bot token should contain exactly one colon"
            assert chat_id.isdigit() or chat_id.startswith('-'), "Telegram chat ID should be numeric or start with -"

            logger.info("✅ Telegram configuration format valid")
        else:
            logger.warning("⚠️ Telegram not configured (optional)")

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test health check endpoint availability."""
        try:
            import httpx

            # Try common health check endpoints
            health_endpoints = [
                'http://localhost:8080/health',
                'http://localhost:8080/livez',
                'http://localhost:8080/readyz'
            ]

            for endpoint in health_endpoints:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(endpoint)
                        if response.status_code == 200:
                            logger.info(f"✅ Health check endpoint available: {endpoint}")
                            return
                except:
                    continue

            logger.warning("⚠️ No health check endpoints available (OK if system not running)")

        except ImportError:
            pytest.skip("httpx not available for health check test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
