#!/bin/bash

# Q5 System Production Deployment Script
# This script deploys the Q5 trading system to production using Helius as the RPC provider

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
print_header "Checking required tools"

REQUIRED_TOOLS=("python3" "pip" "docker" "docker-compose")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if command_exists "$tool"; then
        echo -e "${GREEN}✓ $tool is installed${NC}"
    else
        echo -e "${RED}✗ $tool is not installed${NC}"
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo -e "${RED}Please install the missing tools before proceeding:${NC}"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo -e "${RED}  - $tool${NC}"
    done
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${YELLOW}Python version: $PYTHON_VERSION${NC}"

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo -e "${RED}Error: .env file not found in the parent directory${NC}"
    exit 1
fi

# Verify API keys in .env
print_header "Verifying API keys"

# Source the .env file
source ../.env

# Check Helius API key
if [ -z "$HELIUS_API_KEY" ]; then
    echo -e "${RED}Error: HELIUS_API_KEY not found in .env file${NC}"
    exit 1
else
    echo -e "${GREEN}✓ HELIUS_API_KEY found${NC}"
fi

# Check wallet address
if [ -z "$WALLET_ADDRESS" ]; then
    echo -e "${RED}Error: WALLET_ADDRESS not found in .env file${NC}"
    exit 1
else
    echo -e "${GREEN}✓ WALLET_ADDRESS found${NC}"
fi

# Run Helius integration test
print_header "Running Helius integration test"
./run_helius_test.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Helius integration test failed${NC}"
    echo -e "${RED}Please fix the issues before proceeding to production deployment${NC}"
    exit 1
fi

# Create production configuration
print_header "Creating production configuration"

# Create production directory if it doesn't exist
mkdir -p production

# Copy configuration files
cp ../config.yaml production/
cp configs/helius_config.yaml production/

# Update production config
sed -i.bak 's/DRY_RUN=true/DRY_RUN=false/' production/config.yaml
sed -i.bak 's/simulation: false/simulation: false/' production/config.yaml
sed -i.bak 's/live_trading: false/live_trading: true/' production/config.yaml

echo -e "${GREEN}✓ Production configuration created${NC}"

# Build Docker image
print_header "Building Docker image"

# Create Dockerfile if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DRY_RUN=false

# Create output directory
RUN mkdir -p output

# Expose ports
EXPOSE 8501

# Run the application
CMD ["./launch_all.sh"]
EOF

    echo -e "${GREEN}✓ Dockerfile created${NC}"
fi

# Create docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ]; then
    cat > docker-compose.yml << EOF
version: '3'

services:
  q5system:
    build: .
    container_name: q5_trading_bot
    restart: unless-stopped
    volumes:
      - ./production:/app/production
      - ./output:/app/output
    ports:
      - "8501:8501"
    environment:
      - HELIUS_API_KEY=${HELIUS_API_KEY}
      - BIRDEYE_API_KEY=${BIRDEYE_API_KEY}
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - WALLET_ADDRESS=${WALLET_ADDRESS}
      - HELIUS_RPC_URL=https://rpc.helius.xyz/?api-key=${HELIUS_API_KEY}
      - FALLBACK_RPC_URL=https://api.mainnet-beta.solana.com
      - DRY_RUN=false
EOF

    echo -e "${GREEN}✓ docker-compose.yml created${NC}"
fi

# Build the Docker image
docker build -t q5system:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Final confirmation
print_header "Ready for production deployment"
echo -e "${YELLOW}The system is now ready for production deployment.${NC}"
echo -e "${YELLOW}To start the system in production mode, run:${NC}"
echo -e "${GREEN}docker-compose up -d${NC}"
echo -e "${YELLOW}To view logs:${NC}"
echo -e "${GREEN}docker-compose logs -f${NC}"
echo -e "${YELLOW}To stop the system:${NC}"
echo -e "${GREEN}docker-compose down${NC}"

echo -e "\n${GREEN}Production deployment preparation completed successfully!${NC}"
echo -e "${YELLOW}Timestamp: $(date)${NC}"

# Exit with success
exit 0
