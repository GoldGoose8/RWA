#!/bin/bash
# Production Deployment Script for Q5 Trading System

# Exit on error
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

# Set the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Parse command line arguments
SKIP_VERIFICATION=false
SKIP_SIMULATION=false
SKIP_BUILD=false
FORCE_FALLBACK=false
ENVIRONMENT="production"

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-verification)
            SKIP_VERIFICATION=true
            shift
            ;;
        --skip-simulation)
            SKIP_SIMULATION=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force-fallback)
            FORCE_FALLBACK=true
            shift
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "INFO" "Starting production deployment process..."
log "INFO" "Environment: $ENVIRONMENT"
log "INFO" "Skip verification: $SKIP_VERIFICATION"
log "INFO" "Skip simulation: $SKIP_SIMULATION"
log "INFO" "Skip build: $SKIP_BUILD"
log "INFO" "Force fallback: $FORCE_FALLBACK"

# Step 1: Set up environment
log "INFO" "Setting up environment..."

# Copy environment file
ENV_FILE="../configs/environments/env.$ENVIRONMENT"
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "../.env"
    log "INFO" "Copied environment file: $ENV_FILE -> ../.env"
else
    log "ERROR" "Environment file not found: $ENV_FILE"
    exit 1
fi

# Load environment variables
source "../.env"

# Set fallback flags if needed
if [ "$FORCE_FALLBACK" = true ]; then
    export CARBON_CORE_FALLBACK=true
    export SOLANA_TX_UTILS_FALLBACK=true
    log "INFO" "Forced fallback mode enabled"
fi

# Step 2: Verify production readiness
if [ "$SKIP_VERIFICATION" = false ]; then
    log "INFO" "Verifying production readiness..."
    
    # Run verification script
    python3 scripts/verify_production.py --config "../config.yaml" --output "production_verification.json"
    
    # Check verification result
    VERIFICATION_RESULT=$?
    if [ $VERIFICATION_RESULT -ne 0 ]; then
        log "ERROR" "Production verification failed"
        log "INFO" "See production_verification.json for details"
        exit 1
    fi
    
    log "INFO" "Production verification passed"
else
    log "WARNING" "Skipping production verification"
fi

# Step 3: Build Carbon Core
if [ "$SKIP_BUILD" = false ]; then
    log "INFO" "Building Carbon Core..."
    
    # Run build script
    cd ..
    ./build_carbon_core.sh
    cd "$ROOT_DIR"
    
    # Check if build was successful
    if [ -f "../bin/carbon_core" ] && [ -x "../bin/carbon_core" ]; then
        log "INFO" "Carbon Core built successfully"
    else
        if [ "$FORCE_FALLBACK" = true ]; then
            log "WARNING" "Carbon Core build failed, but fallback is enabled"
        else
            log "ERROR" "Carbon Core build failed"
            exit 1
        fi
    fi
else
    log "WARNING" "Skipping Carbon Core build"
fi

# Step 4: Run simulation test
if [ "$SKIP_SIMULATION" = false ]; then
    log "INFO" "Running simulation test..."
    
    # Run simulation script
    python3 scripts/simulation_test.py --config "../config.yaml" --output "simulation_results.json"
    
    # Check simulation result
    SIMULATION_RESULT=$?
    if [ $SIMULATION_RESULT -ne 0 ]; then
        log "ERROR" "Simulation test failed"
        log "INFO" "See simulation_results.json for details"
        exit 1
    fi
    
    log "INFO" "Simulation test passed"
else
    log "WARNING" "Skipping simulation test"
fi

# Step 5: Build Docker image
log "INFO" "Building Docker image..."

# Build Docker image
docker build -t q5-trading-system:latest -f docker_deploy/Dockerfile ..

# Check if build was successful
if [ $? -ne 0 ]; then
    log "ERROR" "Docker build failed"
    exit 1
fi

log "INFO" "Docker image built successfully"

# Step 6: Deploy with Docker Compose
log "INFO" "Deploying with Docker Compose..."

# Stop any running containers
docker-compose down

# Start containers
docker-compose up -d

# Check if deployment was successful
if [ $? -ne 0 ]; then
    log "ERROR" "Docker Compose deployment failed"
    exit 1
fi

log "INFO" "Docker Compose deployment successful"

# Step 7: Verify deployment
log "INFO" "Verifying deployment..."

# Wait for services to start
sleep 10

# Check if containers are running
RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" | wc -l)
EXPECTED_CONTAINERS=$(docker-compose config --services | wc -l)

if [ "$RUNNING_CONTAINERS" -ne "$EXPECTED_CONTAINERS" ]; then
    log "ERROR" "Not all containers are running"
    docker-compose ps
    exit 1
fi

log "INFO" "All containers are running"

# Check health endpoints
HEALTH_SERVER_PORT=${HEALTH_SERVER_PORT:-8080}
HEALTH_ENDPOINT="http://localhost:$HEALTH_SERVER_PORT/health"

# Wait for health endpoint to be available
RETRIES=10
RETRY_DELAY=5
HEALTH_CHECK_SUCCESS=false

for i in $(seq 1 $RETRIES); do
    log "INFO" "Checking health endpoint (attempt $i/$RETRIES)..."
    
    if curl -s "$HEALTH_ENDPOINT" | grep -q "healthy"; then
        HEALTH_CHECK_SUCCESS=true
        break
    fi
    
    log "WARNING" "Health check failed, retrying in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done

if [ "$HEALTH_CHECK_SUCCESS" = false ]; then
    log "ERROR" "Health check failed after $RETRIES attempts"
    exit 1
fi

log "INFO" "Health check passed"

# Step 8: Final steps
log "INFO" "Deployment completed successfully!"
log "INFO" "System is now running in $ENVIRONMENT mode"
log "INFO" "Dashboard available at: http://localhost:${STREAMLIT_PORT:-8501}"
log "INFO" "Health endpoint available at: $HEALTH_ENDPOINT"

# Print fallback status
if [ "$FORCE_FALLBACK" = true ] || [ "$CARBON_CORE_FALLBACK" = true ] || [ "$SOLANA_TX_UTILS_FALLBACK" = true ]; then
    log "WARNING" "System is running with fallbacks enabled:"
    [ "$CARBON_CORE_FALLBACK" = true ] && log "WARNING" "- Carbon Core: Using Python fallback"
    [ "$SOLANA_TX_UTILS_FALLBACK" = true ] && log "WARNING" "- Solana TX Utils: Using Python fallback"
fi

log "INFO" "To monitor the system, use: docker-compose logs -f"
log "INFO" "To stop the system, use: docker-compose down"
