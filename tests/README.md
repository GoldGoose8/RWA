# Synergy7 Trading System Tests

This directory contains comprehensive tests for the Synergy7 Trading System. The tests have been completely updated to reflect the current production-ready system architecture.

## 🚀 **UPDATED TEST SYSTEM (May 26, 2025)**

The test system has been completely redesigned to match the current live trading system with Jito-primary execution and Orca DEX integration:

### **New Test Suites**

1. **Production Live Trading Tests** (`test_production_live_trading.py`)
   - Tests for production-ready live trading system with Jito Bundle execution
   - Unified live trader functionality with Orca DEX integration
   - Environment validation and configuration
   - Wallet balance checking and transaction execution
   - Jito Bundle transaction validation

2. **Signal Generation System Tests** (`test_signal_generation_system.py`)
   - Birdeye scanner integration tests
   - Whale watcher functionality tests with enhanced signal processing
   - Signal enricher and composite scoring tests
   - Signal filtering and validation tests
   - Market regime detection integration

3. **Transaction Execution System Tests** (`test_transaction_execution_system.py`)
   - Orca swap transaction builder tests (replacing Jupiter)
   - Jito Bundle client and execution tests
   - Transaction signing and keypair loading tests
   - Helius client tests for non-trading operations
   - Fallback execution system tests

4. **Risk Management System Tests** (`test_risk_management_system.py`)
   - Production position sizer tests with VaR/CVaR calculations
   - Portfolio risk assessment tests with correlation analysis
   - Telegram alert system tests with enhanced notifications
   - System monitoring and circuit breaker tests
   - Position flattening system tests

5. **Full System Integration Tests** (`test_full_system_integration.py`)
   - End-to-end trading pipeline tests
   - Error handling and recovery tests
   - Performance and scalability tests
   - Configuration validation tests

### **Test Types**

- **Unit Tests**: Individual component testing in isolation
- **Integration Tests**: Component interaction testing
- **System Tests**: Complete system functionality testing
- **Performance Tests**: System performance and scalability testing
- **End-to-End Tests**: Full trading pipeline testing

## Directory Structure

```
tests/
├── conftest.py                # Global test configuration and fixtures
├── unit/                      # Unit tests
│   ├── core/                  # Unit tests for core components
│   │   ├── strategies/        # Unit tests for strategies
│   │   ├── engine/            # Unit tests for engine components
│   │   ├── risk/              # Unit tests for risk management components
│   │   ├── data/              # Unit tests for data ingestion components
│   │   └── execution/         # Unit tests for execution components
│   └── shared/                # Unit tests for shared components
│       ├── utils/             # Unit tests for utility functions
│       ├── rust/              # Unit tests for Rust integration
│       └── solana_utils/      # Unit tests for Solana utilities
├── integration/               # Integration tests
│   ├── core/                  # Integration tests for core components
│   └── shared/                # Integration tests for shared components
├── functional/                # Functional tests
│   ├── core/                  # Functional tests for core components
│   └── shared/                # Functional tests for shared components
├── performance/               # Performance tests
│   ├── core/                  # Performance tests for core components
│   └── shared/                # Performance tests for shared components
└── e2e/                       # End-to-end tests
    ├── core/                  # End-to-end tests for core components
    └── shared/                # End-to-end tests for shared components
```

## 🧪 **Running Tests**

### **Comprehensive Test Runner (RECOMMENDED)**

```bash
# Run all updated tests with detailed reporting
python3 tests/run_comprehensive_tests.py

# List available test suites
python3 tests/run_comprehensive_tests.py --list

# Run specific test suite
python3 tests/run_comprehensive_tests.py --suite production_live_trading
```

### **Individual Test Suites**

```bash
# Production live trading tests (Jito Bundle + Orca DEX)
pytest tests/test_production_live_trading.py -v

# Signal generation system tests (Enhanced whale watching + market regime)
pytest tests/test_signal_generation_system.py -v

# Transaction execution system tests (Orca DEX integration)
pytest tests/test_transaction_execution_system.py -v

# Risk management system tests (VaR/CVaR + portfolio risk)
pytest tests/test_risk_management_system.py -v

# Full system integration tests (End-to-end pipeline)
pytest tests/test_full_system_integration.py -v

# Current system integration tests (Live system validation)
pytest tests/test_current_system_integration.py -v

# Deployment validation tests (Production readiness)
pytest tests/test_deployment_validation.py -v

# Monitoring and health tests (System monitoring)
pytest tests/test_monitoring_and_health.py -v
```

### **Legacy Tests (Still Available)**

```bash
# Wallet security tests
pytest tests/test_wallet_security.py -v

# Helius integration tests
pytest tests/test_helius_integration.py -v

# Transaction executor tests
pytest tests/test_transaction_executor.py -v
```

### **Quick Test Commands**

```bash
# Run critical tests only
pytest tests/test_production_live_trading.py tests/test_full_system_integration.py -v

# Run with coverage
pytest tests/ --cov=core --cov=phase_4_deployment --cov=scripts

# Run specific test function
pytest tests/test_production_live_trading.py::TestProductionLiveTrading::test_wallet_balance_check -v
```

### Running Tests with Markers

```bash
# Run tests marked as slow
pytest -m slow --run-slow

# Run tests marked as integration
pytest -m integration --run-integration

# Run tests marked as e2e
pytest -m e2e --run-e2e
```

## Environment Variables

The tests require the following environment variables to be set:

- `HELIUS_API_KEY`: Your Helius API key
- `WALLET_ADDRESS`: Your Solana wallet address
- `BIRDEYE_API_KEY`: Your Birdeye API key (for some tests)

## Writing Tests

### Test Naming Conventions

- Test files should be named `test_*.py`.
- Test classes should be named `Test*`.
- Test functions should be named `test_*`.

### Test Fixtures

Global test fixtures are defined in `conftest.py`. These fixtures are available to all tests.

### Test Markers

Tests can be marked with the following markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.functional`: Functional tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.slow`: Slow tests

### Test Dependencies

Tests may require the following dependencies:

- `pytest`: Testing framework
- `pytest-asyncio`: Async support for pytest
- `pytest-mock`: Mocking support for pytest
- `pytest-cov`: Coverage support for pytest

Install these dependencies with:

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

## Test Coverage

To run tests with coverage:

```bash
pytest --cov=core --cov=shared
```

To generate a coverage report:

```bash
pytest --cov=core --cov=shared --cov-report=html
```

The coverage report will be generated in the `htmlcov` directory.

## Legacy Tests

The following legacy tests are still available:

- `test_helius_integration.py`: Tests for the Helius RPC integration
- `test_jito_integration.py`: Tests for the Jito RPC integration
- `test_solders.py`: Tests for Solana Solders integration
- `test_solders_fix.py`: Tests for Solders fixes and workarounds
- `test_transaction.py`: Tests for transaction creation and signing
- `test_tx_creation.py`: Tests for transaction building
- `verify_simulation.py`: Script to verify simulation results

## Continuous Integration

These tests are designed to be run as part of the CI/CD pipeline to ensure that all components work correctly before deployment.
