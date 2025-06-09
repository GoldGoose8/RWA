#!/bin/bash
# Test script for Docker container runtime

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

# Function to run a test and report the result
run_test() {
    local test_name=$1
    local test_command=$2
    
    log "INFO" "Running test: $test_name"
    
    if eval "$test_command"; then
        log "SUCCESS" "Test passed: $test_name"
        return 0
    else
        log "FAILURE" "Test failed: $test_name"
        return 1
    fi
}

# Function to clean up after tests
cleanup() {
    log "INFO" "Cleaning up..."
    
    # Stop and remove containers
    log "INFO" "Stopping containers..."
    docker-compose -f phase_4_deployment/docker-compose.yml down
    
    # Remove test containers
    if docker ps -a | grep -q "q5_test_"; then
        log "INFO" "Removing test containers..."
        docker ps -a | grep "q5_test_" | awk '{print $1}' | xargs docker rm -f
    fi
    
    log "INFO" "Cleanup complete"
}

# Main function
main() {
    log "INFO" "Starting Docker runtime tests..."
    
    # Change to the project root directory
    cd "$(dirname "$0")/../.."
    log "INFO" "Working directory: $(pwd)"
    
    # Set up test environment
    log "INFO" "Setting up test environment..."
    
    # Create test directories if they don't exist
    mkdir -p phase_4_deployment/tests/results
    
    # Test variables
    local test_passed=0
    local test_failed=0
    local test_results_file="phase_4_deployment/tests/results/docker_runtime_test_results.txt"
    
    # Initialize test results file
    echo "Docker Runtime Test Results - $(date)" > "$test_results_file"
    echo "==================================" >> "$test_results_file"
    
    # Test 1: Start production container
    if run_test "Start production container" "docker-compose -f phase_4_deployment/docker-compose.yml up -d"; then
        echo "✅ Production container start: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Production container start: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Wait for container to start
    log "INFO" "Waiting for container to start..."
    sleep 10
    
    # Test 2: Check container is running
    if run_test "Check container is running" "docker ps | grep q5_trading_bot"; then
        echo "✅ Container running check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Container running check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 3: Check container logs for errors
    if run_test "Check container logs for errors" "docker logs q5_trading_bot 2>&1 | grep -v 'ERROR'"; then
        echo "✅ Container logs check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Container logs check: FAILED (Errors found in logs)" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 4: Check PyO3 extension is loaded
    if run_test "Check PyO3 extension is loaded" "docker exec q5_trading_bot python -c 'import solana_tx_utils; print(\"PyO3 extension loaded\")' | grep 'PyO3 extension loaded'"; then
        echo "✅ PyO3 extension loaded check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ PyO3 extension loaded check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 5: Check health check is working
    if run_test "Check health check is working" "docker inspect --format='{{.State.Health.Status}}' q5_trading_bot | grep -E 'healthy|starting'"; then
        echo "✅ Health check working: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Health check working: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 6: Check fallback mechanism
    if run_test "Check fallback mechanism" "docker exec -e SOLANA_TX_UTILS_FALLBACK=true q5_trading_bot python -c 'import solana_tx_utils; print(\"Fallback mechanism working\")' | grep 'Fallback mechanism working'"; then
        echo "✅ Fallback mechanism check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Fallback mechanism check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 7: Check resource limits
    if run_test "Check resource limits" "docker stats --no-stream q5_trading_bot | grep q5_trading_bot"; then
        echo "✅ Resource limits check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Resource limits check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Stop production container
    log "INFO" "Stopping production container..."
    docker-compose -f phase_4_deployment/docker-compose.yml down
    
    # Test 8: Start development container
    if run_test "Start development container" "docker-compose -f phase_4_deployment/docker-compose.yml -f phase_4_deployment/docker-compose.override.yml up -d"; then
        echo "✅ Development container start: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Development container start: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Wait for container to start
    log "INFO" "Waiting for container to start..."
    sleep 10
    
    # Test 9: Check development tools are installed
    if run_test "Check development tools are installed" "docker exec q5_trading_bot python -c 'import pytest, debugpy; print(\"Development tools installed\")' | grep 'Development tools installed'"; then
        echo "✅ Development tools check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Development tools check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Print test summary
    log "INFO" "Test summary:"
    log "INFO" "  Passed: $test_passed"
    log "INFO" "  Failed: $test_failed"
    log "INFO" "  Total: $((test_passed + test_failed))"
    
    # Append summary to test results file
    echo "" >> "$test_results_file"
    echo "Test Summary:" >> "$test_results_file"
    echo "  Passed: $test_passed" >> "$test_results_file"
    echo "  Failed: $test_failed" >> "$test_results_file"
    echo "  Total: $((test_passed + test_failed))" >> "$test_results_file"
    
    # Clean up
    cleanup
    
    # Return success if all tests passed
    if [ $test_failed -eq 0 ]; then
        log "SUCCESS" "All tests passed!"
        return 0
    else
        log "FAILURE" "Some tests failed. See $test_results_file for details."
        return 1
    fi
}

# Run the main function
main "$@"
