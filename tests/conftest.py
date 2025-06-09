"""
Global test configuration and fixtures.
"""

import os
import sys
import pytest
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Return a test configuration."""
    return {
        "test_mode": True,
        "dry_run": True,
        "market_microstructure": {
            "markets": ["SOL-USDC", "JTO-USDC"]
        },
        "risk_management": {
            "max_position_size": 0.1,
            "max_exposure": 0.5,
            "update_interval_ms": 1000,
            "publish_interval_ms": 1000,
            "metrics_interval_ms": 5000
        },
        "strategy_runner": {
            "update_interval_ms": 1000,
            "publish_interval_ms": 1000
        },
        "transaction_execution": {
            "update_interval_ms": 1000,
            "publish_interval_ms": 1000,
            "simulation_enabled": True,
            "dry_run": True
        },
        "rpc": {
            "endpoint": "https://api.mainnet-beta.solana.com"
        }
    }

# Mock market data
@pytest.fixture
def mock_market_data():
    """Return mock market data."""
    return {
        "order_books": {
            "SOL-USDC": {
                "bids": [
                    {"price": 100.0, "size": 1.0},
                    {"price": 99.0, "size": 2.0}
                ],
                "asks": [
                    {"price": 101.0, "size": 1.0},
                    {"price": 102.0, "size": 2.0}
                ],
                "metrics": {
                    "mid_price": 100.5,
                    "spread": 1.0,
                    "spread_pct": 0.01,
                    "bid_ask_imbalance": 0.5
                }
            },
            "JTO-USDC": {
                "bids": [
                    {"price": 10.0, "size": 1.0},
                    {"price": 9.9, "size": 2.0}
                ],
                "asks": [
                    {"price": 10.1, "size": 1.0},
                    {"price": 10.2, "size": 2.0}
                ],
                "metrics": {
                    "mid_price": 10.05,
                    "spread": 0.1,
                    "spread_pct": 0.01,
                    "bid_ask_imbalance": 0.5
                }
            }
        }
    }

# Test environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["DRY_RUN"] = "true"
    
    # Create output directory if it doesn't exist
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    yield
    
    # Clean up after tests
    logger.info("Cleaning up test environment")

# Skip slow tests by default
def pytest_addoption(parser):
    """Add command-line options to pytest."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--run-integration", action="store_true", default=False, help="run integration tests"
    )
    parser.addoption(
        "--run-e2e", action="store_true", default=False, help="run end-to-end tests"
    )

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")

def pytest_collection_modifyitems(config, items):
    """Modify collected test items."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
    
    if not config.getoption("--run-e2e"):
        skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)
