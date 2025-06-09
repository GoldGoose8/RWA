#!/bin/bash
# Test script for PyO3 extension functionality

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

    log "INFO" "Cleanup complete"
}

# We'll use the docker_test.py script that we created earlier
log "INFO" "Using docker_test.py for PyO3 functionality tests"

# Main function
main() {
    log "INFO" "Starting PyO3 functionality tests..."

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
    local test_results_file="phase_4_deployment/tests/results/pyo3_functionality_test_results.txt"

    # Initialize test results file
    echo "PyO3 Functionality Test Results - $(date)" > "$test_results_file"
    echo "=====================================" >> "$test_results_file"

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

    # Test 2: Run PyO3 functionality tests in container
    if run_test "Run PyO3 functionality tests" "docker cp phase_4_deployment/tests/docker_test.py q5_trading_bot:/app/ && docker exec -e SOLANA_TX_UTILS_FALLBACK=true -e DOCKER_CONTAINER=true q5_trading_bot python /app/docker_test.py"; then
        echo "✅ PyO3 functionality tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ PyO3 functionality tests: FAILED" >> "$test_results_file"
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
