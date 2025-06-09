#!/bin/bash
# Test script for Docker image build process

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
    
    # Remove test containers
    if docker ps -a | grep -q "q5_test_"; then
        log "INFO" "Removing test containers..."
        docker ps -a | grep "q5_test_" | awk '{print $1}' | xargs docker rm -f
    fi
    
    # Remove test images
    if docker images | grep -q "q5_test_"; then
        log "INFO" "Removing test images..."
        docker images | grep "q5_test_" | awk '{print $3}' | xargs docker rmi -f
    fi
    
    log "INFO" "Cleanup complete"
}

# Main function
main() {
    log "INFO" "Starting Docker build tests..."
    
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
    local test_results_file="phase_4_deployment/tests/results/docker_build_test_results.txt"
    
    # Initialize test results file
    echo "Docker Build Test Results - $(date)" > "$test_results_file"
    echo "=================================" >> "$test_results_file"
    
    # Test 1: Build development image
    if run_test "Build development image" "docker-compose -f phase_4_deployment/docker-compose.yml -f phase_4_deployment/docker-compose.override.yml build --no-cache"; then
        echo "✅ Development image build: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Development image build: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 2: Build production image
    if run_test "Build production image" "docker-compose -f phase_4_deployment/docker-compose.yml build --no-cache"; then
        echo "✅ Production image build: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Production image build: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 3: Check image size
    if run_test "Check image size" "docker images | grep q5_trading_bot | awk '{print \$7}' | grep -v 'GB'"; then
        echo "✅ Image size check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Image size check: FAILED (Image is too large)" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 4: Check for PyO3 extension in the image
    if run_test "Check for PyO3 extension" "docker run --rm q5_trading_bot python -c 'import solana_tx_utils; print(\"PyO3 extension found\")' | grep 'PyO3 extension found'"; then
        echo "✅ PyO3 extension check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ PyO3 extension check: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 5: Check multi-stage build (image should not contain build tools)
    if run_test "Check multi-stage build" "docker run --rm q5_trading_bot bash -c 'if command -v rustc &> /dev/null; then exit 1; else exit 0; fi'"; then
        echo "✅ Multi-stage build check: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Multi-stage build check: FAILED (Build tools found in final image)" >> "$test_results_file"
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
