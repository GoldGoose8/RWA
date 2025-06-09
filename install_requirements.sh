#!/bin/bash

# RWA Trading System - Requirements Installation Script
# =====================================================
# Installs all required dependencies with proper version compatibility
# Ensures solders 0.26.0 + solana 0.36.7 compatibility
# =====================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check Python version
check_python_version() {
    print_header "Checking Python Version"
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Python version: $PYTHON_VERSION"
        
        # Check if Python 3.9+
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
            print_success "Python 3.9+ detected - compatible with Solana ecosystem"
        else
            print_error "Python 3.9+ required for Solana dependencies"
            print_error "Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.9 or higher."
        exit 1
    fi
}

# Check pip version
check_pip_version() {
    print_header "Checking pip Version"
    
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
        print_status "pip version: $PIP_VERSION"
        
        # Upgrade pip if needed
        print_status "Upgrading pip to latest version..."
        python3 -m pip install --upgrade pip
        print_success "pip upgraded successfully"
    else
        print_error "pip3 not found. Please install pip."
        exit 1
    fi
}

# Install core Solana ecosystem packages first
install_solana_ecosystem() {
    print_header "Installing Solana Ecosystem Packages"
    
    print_status "Installing solders 0.26.0 (Solana Rust bindings)..."
    pip3 install solders==0.26.0
    
    print_status "Installing solana 0.36.7 (Solana Python SDK)..."
    pip3 install solana==0.36.7
    
    print_status "Installing anchorpy (Anchor framework client)..."
    pip3 install "anchorpy>=0.20.1"
    
    print_success "Solana ecosystem packages installed successfully"
}

# Install core system dependencies
install_core_dependencies() {
    print_header "Installing Core System Dependencies"
    
    print_status "Installing HTTP and networking libraries..."
    pip3 install \
        "httpx>=0.28.0" \
        "aiohttp>=3.9.0" \
        "websockets>=12.0" \
        "requests>=2.31.0"
    
    print_status "Installing configuration and environment libraries..."
    pip3 install \
        "pyyaml>=6.0.1" \
        "python-dotenv>=1.0.0" \
        "toml>=0.10.2"
    
    print_status "Installing cryptography libraries..."
    pip3 install \
        "base58>=2.1.1" \
        "cryptography>=41.0.0" \
        "pynacl>=1.5.0"
    
    print_success "Core dependencies installed successfully"
}

# Install data processing libraries
install_data_processing() {
    print_header "Installing Data Processing Libraries"
    
    print_status "Installing core data libraries..."
    pip3 install \
        "numpy>=1.24.0,<2.0.0" \
        "pandas>=2.0.0" \
        "scipy>=1.11.0"
    
    print_status "Installing financial analysis libraries..."
    pip3 install \
        "ta>=0.10.2" \
        "scikit-learn>=1.3.0"
    
    # Try to install vectorbt (optional, may fail on some systems)
    print_status "Installing vectorbt (optional)..."
    pip3 install "vectorbt>=0.25.0" || print_warning "vectorbt installation failed (optional package)"
    
    print_success "Data processing libraries installed successfully"
}

# Install visualization libraries
install_visualization() {
    print_header "Installing Visualization Libraries"
    
    print_status "Installing dashboard and plotting libraries..."
    pip3 install \
        "streamlit>=1.28.0" \
        "plotly>=5.17.0" \
        "matplotlib>=3.7.0" \
        "seaborn>=0.12.0"
    
    print_success "Visualization libraries installed successfully"
}

# Install async and utility libraries
install_utilities() {
    print_header "Installing Utility Libraries"
    
    print_status "Installing async utilities..."
    pip3 install \
        "asyncio-mqtt>=0.16.0" \
        "aiofiles>=23.0.0" \
        "tenacity>=8.2.0"
    
    print_status "Installing monitoring and logging..."
    pip3 install \
        "loguru>=0.7.0" \
        "prometheus-client>=0.19.0" \
        "psutil>=5.9.0"
    
    print_status "Installing CLI and formatting utilities..."
    pip3 install \
        "tqdm>=4.66.0" \
        "click>=8.1.0" \
        "rich>=13.0.0"
    
    print_status "Installing date/time utilities..."
    pip3 install \
        "python-dateutil>=2.8.0" \
        "pytz>=2023.3"
    
    print_success "Utility libraries installed successfully"
}

# Install optional packages
install_optional() {
    print_header "Installing Optional Packages"
    
    print_status "Installing Telegram bot support..."
    pip3 install "python-telegram-bot>=20.0" || print_warning "Telegram bot installation failed (optional)"
    
    print_status "Installing development tools..."
    pip3 install \
        "pytest>=7.4.0" \
        "pytest-asyncio>=0.21.0" \
        "pytest-cov>=4.1.0" \
        "pytest-mock>=3.11.0" \
        "black>=23.0.0" \
        "isort>=5.12.0" \
        "flake8>=6.0.0" \
        "mypy>=1.5.0" || print_warning "Some development tools installation failed (optional)"
    
    print_success "Optional packages installation completed"
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"
    
    print_status "Running requirements validation..."
    if python3 scripts/validate_requirements.py; then
        print_success "All requirements validated successfully!"
    else
        print_warning "Some validation issues found - check output above"
    fi
}

# Main installation process
main() {
    print_header "RWA Trading System - Requirements Installation"
    echo "This script will install all required dependencies for the RWA Trading System"
    echo "Compatible with solders 0.26.0 + solana 0.36.7"
    echo ""
    
    # Check prerequisites
    check_python_version
    check_pip_version
    
    # Install packages in order of dependency
    install_solana_ecosystem
    install_core_dependencies
    install_data_processing
    install_visualization
    install_utilities
    install_optional
    
    # Verify everything works
    verify_installation
    
    print_header "Installation Complete"
    print_success "All dependencies installed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure your .env file with API keys"
    echo "2. Run: python3 scripts/validate_live_config.py"
    echo "3. Run: python3 scripts/test_live_endpoints.py"
    echo "4. Start trading: python3 scripts/unified_live_trading.py"
    echo ""
    print_warning "Remember to configure your API keys before live trading!"
}

# Run main function
main "$@"
