#!/bin/bash
# Deploy Q5_System with PyO3 extension in production

# Exit on error, but allow for proper error handling
set -e

# Function to log messages with timestamp
log() {
    local level=$1
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $@"
}

# Function to handle errors
handle_error() {
    log "ERROR" "An error occurred on line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

log "INFO" "Starting deployment of Q5_System with PyO3 extension..."

# Load environment variables
if [ -f .env ]; then
    log "INFO" "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    log "WARN" "No .env file found, using environment variables from current shell"
fi

# Check required environment variables
log "INFO" "Checking required environment variables..."
REQUIRED_VARS=("HELIUS_API_KEY" "WALLET_ADDRESS" "BIRDEYE_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log "ERROR" "Missing required environment variables: ${MISSING_VARS[*]}"
    log "ERROR" "Please set them in the .env file"
    exit 1
fi

# Check Docker is installed and running
log "INFO" "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log "ERROR" "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    log "ERROR" "Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Check Docker Compose is installed
log "INFO" "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    log "ERROR" "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to the deployment directory
cd "$(dirname "$0")"
log "INFO" "Changed directory to $(pwd)"

# Set PyO3 extension fallback option
if [ "${SOLANA_TX_UTILS_FALLBACK:-false}" = "true" ]; then
    log "WARN" "PyO3 extension fallback is enabled. Will use solders fallback if native extension fails."
else
    log "INFO" "PyO3 extension fallback is disabled. Will require native extension."
fi

# Build the Docker image
log "INFO" "Building Docker image..."
docker-compose build

# Verify the build was successful
if [ $? -ne 0 ]; then
    log "ERROR" "Docker build failed. Please check the build logs."
    exit 1
fi

# Start the containers
log "INFO" "Starting Docker containers..."
docker-compose up -d

# Verify the containers are running
if [ $? -ne 0 ]; then
    log "ERROR" "Failed to start Docker containers. Please check the logs."
    exit 1
fi

# Wait for the container to be healthy
log "INFO" "Waiting for container to be healthy..."
CONTAINER_NAME="q5_trading_bot"
TIMEOUT=60
INTERVAL=5
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "container_not_found")

    if [ "$HEALTH" = "healthy" ]; then
        log "INFO" "Container is healthy!"
        break
    elif [ "$HEALTH" = "container_not_found" ]; then
        log "ERROR" "Container $CONTAINER_NAME not found."
        exit 1
    elif [ "$HEALTH" = "unhealthy" ]; then
        log "ERROR" "Container is unhealthy. Check logs with: docker-compose logs"
        exit 1
    fi

    log "INFO" "Waiting for container to be healthy... ($ELAPSED/$TIMEOUT seconds)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    log "WARN" "Timeout waiting for container to be healthy. Check logs with: docker-compose logs"
fi

log "INFO" "Deployment complete! Container is running."
log "INFO" "Check logs with: docker-compose logs -f"
log "INFO" "Access dashboard at: http://localhost:8501"
