#!/bin/bash

# Q5 System Docker Deployment Script
# This script deploys the Q5 trading system using Docker

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

REQUIRED_TOOLS=("docker" "docker-compose")
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

# Check DRY_RUN setting
if [ "$DRY_RUN" = "false" ]; then
    echo -e "${YELLOW}WARNING: DRY_RUN is set to false. This will execute real transactions!${NC}"
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Deployment aborted.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ DRY_RUN is set to true. No real transactions will be executed.${NC}"
fi

# Run Helius integration test
print_header "Running Helius integration test"
./run_helius_test.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Helius integration test failed${NC}"
    echo -e "${RED}Please fix the issues before proceeding to production deployment${NC}"
    exit 1
fi

# Build Docker image
print_header "Building Docker image"

# Build the Docker image
docker-compose build

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Start the container
print_header "Starting production deployment"
echo -e "${YELLOW}Starting the system in production mode...${NC}"
docker-compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to start Docker container${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker container started successfully${NC}"

# Print container status
print_header "Container Status"
docker-compose ps

# Print dashboard URL
print_header "Dashboard URL"
echo -e "${YELLOW}Dashboard URL: http://localhost:8501${NC}"
echo -e "${YELLOW}Please allow a few minutes for the system to initialize${NC}"

# Print logs command
echo -e "${YELLOW}To view logs:${NC}"
echo -e "${GREEN}docker-compose logs -f${NC}"
echo -e "${YELLOW}To stop the system:${NC}"
echo -e "${GREEN}docker-compose down${NC}"

echo -e "\n${GREEN}Production deployment completed successfully!${NC}"
echo -e "${YELLOW}Timestamp: $(date)${NC}"

# Exit with success
exit 0
