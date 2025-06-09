# Synergy7 Configuration Management

This document outlines the configuration management approach for the Synergy7 trading system, focusing on eliminating hard-coded values and ensuring all configuration is externalized.

## Configuration Sources

The Synergy7 system uses multiple configuration sources with a clear precedence order:

1. **Command-line arguments** (highest precedence)
2. **Environment variables** (from `.env` file or system environment)
3. **Configuration files** (YAML files in the `config/` directory)
4. **Default values** (lowest precedence, defined in code)

## Directory Structure

```
/config/
  ├── config.yaml             # Base configuration
  ├── token_registry.yaml     # Token address registry
  ├── environments/           # Environment-specific configurations
  │   ├── production.yaml     # Production environment
  │   ├── development.yaml    # Development environment
  │   └── testing.yaml        # Testing environment
  ├── components/             # Component-specific configurations
  │   └── ...
  └── schemas/                # JSON Schema validation files
      └── config_schema.json  # Schema for config.yaml
```

## Environment Variables

Environment variables are defined in the `.env` file and loaded at runtime. A template `.env.example` file is provided with documentation for all available variables.

Key environment variable categories:

- **API Keys**: `HELIUS_API_KEY`, `BIRDEYE_API_KEY`, etc.
- **RPC Endpoints**: `HELIUS_RPC_URL`, `FALLBACK_RPC_URL`, etc.
- **Trading Mode**: `TRADING_MODE`, `PAPER_TRADING`, etc.
- **Risk Management**: `MAX_POSITION_SIZE`, `STOP_LOSS_PCT`, etc.
- **Transaction Settings**: `SLIPPAGE_TOLERANCE`, `MAX_TRANSACTION_FEE`, etc.
- **Timing Configuration**: `TRADING_CYCLE_INTERVAL_SECONDS`, etc.
- **Test Configuration**: `TEST_MARKET`, `TEST_SIZE`, etc.

## Token Registry

Token addresses are stored in `config/token_registry.yaml` with separate sections for mainnet, devnet, and testnet. This eliminates hard-coded token addresses in the code.

Example:
```yaml
mainnet:
  SOL: "So11111111111111111111111111111111111111112"
  USDC: "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
  # ...
devnet:
  SOL: "So11111111111111111111111111111111111111112"
  USDC: "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
  # ...
```

## Configuration Validation

Configuration is validated using JSON Schema and custom validation logic to ensure correctness:

1. **Schema Validation**: Validates the structure of configuration files
2. **Semantic Validation**: Validates the values of configuration parameters
3. **Cross-Validation**: Validates relationships between configuration parameters

## Best Practices

1. **No Hard-Coding**: All configurable values should be externalized
2. **Default Values**: Provide sensible defaults for all configuration parameters
3. **Documentation**: Document all configuration parameters with descriptions and examples
4. **Validation**: Validate all configuration parameters at startup
5. **Logging**: Log the effective configuration at startup
6. **Security**: Sensitive configuration (API keys, private keys) should be stored securely

## Eliminated Hard-Coded Values

The following hard-coded values have been eliminated from the codebase:

1. **Token Addresses**: Moved to `config/token_registry.yaml`
2. **Transaction Parameters**: 
   - Slippage tolerance: Now from `SLIPPAGE_TOLERANCE` environment variable
   - Lamports for test transactions: Now from `MIN_TEST_LAMPORTS` environment variable
3. **RPC URLs**: Now from environment variables
4. **Test Signals**: All values now from environment variables
5. **Timing Values**: 
   - Trading cycle interval: Now from `TRADING_CYCLE_INTERVAL_SECONDS` environment variable
   - Error retry delay: Now from `ERROR_RETRY_DELAY_SECONDS` environment variable
6. **Paper Trading Simulation**: Default values now from environment variables

## Usage in Code

Example of accessing configuration in code:

```python
# Get values from environment with defaults
rpc_url = os.getenv("HELIUS_RPC_URL", "https://api.mainnet-beta.solana.com")
slippage_bps = int(float(os.getenv("SLIPPAGE_TOLERANCE", "0.01")) * 10000)
min_lamports = int(os.getenv("MIN_TEST_LAMPORTS", "1000"))

# Load token registry
token_registry = load_token_registry("config/token_registry.yaml")

# Get token address based on network
token_address = token_registry[network][token_symbol]
```

## Configuration Management Classes

The system includes several classes for managing configuration:

1. **ConfigManager**: Loads and manages configuration from files
2. **EnvManager**: Loads and manages environment variables
3. **ModeManager**: Manages trading modes (live, paper, backtest, simulation)
4. **TokenRegistry**: Manages token addresses for different networks

## Validation Script

A validation script (`scripts/validate_config.py`) is provided to validate the configuration:

```bash
python scripts/validate_config.py --config config.yaml --env .env
```

This script checks for common configuration issues and provides suggestions for fixing them.
