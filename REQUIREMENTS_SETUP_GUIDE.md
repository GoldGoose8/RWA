# Requirements Setup Guide
## RWA Trading System - Comprehensive Dependencies

This guide covers the complete setup of all dependencies for the RWA Trading System with proper version compatibility.

## 🚨 Critical Version Compatibility

### Solana Ecosystem Compatibility Matrix

| solders | solana | anchorpy | Status | Notes |
|---------|--------|----------|--------|-------|
| 0.26.0  | 0.36.7 | 0.20.1+  | ✅ **RECOMMENDED** | Latest stable (2025) |
| 0.25.0  | 0.36.6 | 0.20.0+  | ✅ Stable | Previous stable |
| 0.24.0  | 0.36.0 | 0.19.0+  | ⚠️ Older | May have issues |

**⚠️ CRITICAL:** Always install solders and solana together. Never mix versions from different compatibility groups.

## 📋 Installation Methods

### Method 1: Automated Installation (Recommended)

```bash
# Make installation script executable
chmod +x install_requirements.sh

# Run automated installation
./install_requirements.sh
```

This script will:
- Check Python 3.9+ compatibility
- Install Solana ecosystem packages with correct versions
- Install all core and optional dependencies
- Validate the installation

### Method 2: Manual Installation

```bash
# 1. Install Solana ecosystem (EXACT versions)
pip3 install solders==0.26.0 solana==0.36.7 anchorpy>=0.20.1

# 2. Install core dependencies
pip3 install httpx>=0.28.0 aiohttp>=3.9.0 websockets>=12.0
pip3 install pyyaml>=6.0.1 python-dotenv>=1.0.0 base58>=2.1.1

# 3. Install data processing
pip3 install "numpy>=1.24.0,<2.0.0" pandas>=2.0.0 scipy>=1.11.0

# 4. Install visualization
pip3 install streamlit>=1.28.0 plotly>=5.17.0 matplotlib>=3.7.0

# 5. Install utilities
pip3 install loguru>=0.7.0 tenacity>=8.2.0 tqdm>=4.66.0
```

### Method 3: Requirements File Installation

```bash
# Install from requirements.txt
pip3 install -r requirements.txt
```

## 🔍 Validation and Testing

### Step 1: Validate Requirements

```bash
python3 scripts/validate_requirements.py
```

This will check:
- ✅ Solana ecosystem compatibility
- ✅ All critical packages installed
- ✅ Import functionality
- ✅ Version compatibility

### Step 2: Validate Configuration

```bash
python3 scripts/validate_live_config.py
```

### Step 3: Test Endpoints

```bash
python3 scripts/test_live_endpoints.py
```

## 📦 Package Categories

### Core Solana Ecosystem
```
solders==0.26.0              # Rust bindings for Solana
solana==0.36.7               # Python SDK for Solana
anchorpy>=0.20.1             # Anchor framework client
```

### HTTP and Networking
```
httpx>=0.28.0                # Modern async HTTP client
aiohttp>=3.9.0               # Async HTTP framework
websockets>=12.0             # WebSocket support
requests>=2.31.0             # Sync HTTP client
```

### Data Processing
```
numpy>=1.24.0,<2.0.0        # Numerical computing
pandas>=2.0.0                # Data manipulation
scipy>=1.11.0                # Scientific computing
ta>=0.10.2                   # Technical analysis
scikit-learn>=1.3.0          # Machine learning
```

### Visualization
```
streamlit>=1.28.0            # Dashboard framework
plotly>=5.17.0               # Interactive plots
matplotlib>=3.7.0            # Static plots
seaborn>=0.12.0              # Statistical visualization
```

### Configuration
```
pyyaml>=6.0.1                # YAML parsing
python-dotenv>=1.0.0         # Environment variables
toml>=0.10.2                 # TOML support
```

### Cryptography
```
base58>=2.1.1                # Base58 encoding
cryptography>=41.0.0         # Crypto operations
pynacl>=1.5.0                # NaCl crypto library
```

### Monitoring
```
loguru>=0.7.0                # Advanced logging
prometheus-client>=0.19.0    # Metrics collection
psutil>=5.9.0                # System monitoring
python-telegram-bot>=20.0    # Telegram alerts
```

### Development Tools
```
pytest>=7.4.0               # Testing framework
black>=23.0.0                # Code formatting
mypy>=1.5.0                  # Type checking
flake8>=6.0.0                # Linting
```

## 🐍 Python Version Requirements

- **Minimum:** Python 3.9
- **Recommended:** Python 3.11+
- **Tested:** Python 3.9, 3.10, 3.11, 3.12

### Check Python Version
```bash
python3 --version
# Should show 3.9.0 or higher
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Solana Package Conflicts
```bash
# Uninstall conflicting versions
pip3 uninstall solders solana anchorpy

# Reinstall with exact versions
pip3 install solders==0.26.0 solana==0.36.7 anchorpy>=0.20.1
```

#### 2. NumPy Version Conflicts
```bash
# Install specific NumPy version
pip3 install "numpy>=1.24.0,<2.0.0"
```

#### 3. Rust Compilation Issues (solders)
```bash
# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Or use pre-compiled wheels
pip3 install --only-binary=all solders==0.26.0
```

#### 4. Permission Issues
```bash
# Use user installation
pip3 install --user -r requirements.txt
```

### Verification Commands

```bash
# Check installed versions
pip3 list | grep -E "(solders|solana|anchorpy)"

# Test critical imports
python3 -c "from solders.keypair import Keypair; print('✅ solders OK')"
python3 -c "from solana.rpc.api import Client; print('✅ solana OK')"
python3 -c "import anchorpy; print('✅ anchorpy OK')"
```

## 🚀 Quick Start After Installation

1. **Validate Installation:**
   ```bash
   python3 scripts/validate_requirements.py
   ```

2. **Configure Environment:**
   ```bash
   # Edit .env file with your API keys
   python3 scripts/setup_live_config.py
   ```

3. **Test System:**
   ```bash
   python3 scripts/validate_live_config.py
   python3 scripts/test_live_endpoints.py
   ```

4. **Start Trading:**
   ```bash
   python3 scripts/unified_live_trading.py
   ```

## 📚 Additional Resources

- **Solana Python Docs:** https://michaelhly.github.io/solana-py/
- **Solders Documentation:** https://kevinheavey.github.io/solders/
- **AnchorPy Docs:** https://kevinheavey.github.io/anchorpy/
- **Streamlit Docs:** https://docs.streamlit.io/

## ⚠️ Important Notes

1. **Always install solders and solana together** - they have tight version coupling
2. **Pin NumPy to <2.0.0** - NumPy 2.0 has breaking changes
3. **Use Python 3.9+** - Required for Solana ecosystem
4. **Test after installation** - Run validation scripts before trading
5. **Keep dependencies updated** - But test compatibility first

---

**Remember:** This system handles real money. Always validate your installation thoroughly before live trading!
