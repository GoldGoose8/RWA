#!/bin/bash
# Master test script for Docker integration tests

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

# Function to run a test script and report the result
run_test_script() {
    local script_name=$1
    local script_path="phase_4_deployment/tests/$script_name"
    
    log "INFO" "Running test script: $script_name"
    
    if [ -x "$script_path" ]; then
        if "$script_path"; then
            log "SUCCESS" "Test script passed: $script_name"
            return 0
        else
            log "FAILURE" "Test script failed: $script_name"
            return 1
        fi
    else
        log "ERROR" "Test script not found or not executable: $script_path"
        return 1
    fi
}

# Main function
main() {
    log "INFO" "Starting Docker integration tests..."
    
    # Change to the project root directory
    cd "$(dirname "$0")/../.."
    log "INFO" "Working directory: $(pwd)"
    
    # Set up test environment
    log "INFO" "Setting up test environment..."
    
    # Create test directories if they don't exist
    mkdir -p phase_4_deployment/tests/results
    
    # Make test scripts executable
    chmod +x phase_4_deployment/tests/test_*.sh
    
    # Test variables
    local test_passed=0
    local test_failed=0
    local test_results_file="phase_4_deployment/tests/results/docker_integration_test_results.txt"
    
    # Initialize test results file
    echo "Docker Integration Test Results - $(date)" > "$test_results_file"
    echo "===================================" >> "$test_results_file"
    
    # Run test scripts
    log "INFO" "Running test scripts..."
    
    # Test 1: Docker Build Tests
    if run_test_script "test_docker_build.sh"; then
        echo "✅ Docker Build Tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Docker Build Tests: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 2: Docker Runtime Tests
    if run_test_script "test_docker_runtime.sh"; then
        echo "✅ Docker Runtime Tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Docker Runtime Tests: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 3: PyO3 Functionality Tests
    if run_test_script "test_pyo3_functionality.sh"; then
        echo "✅ PyO3 Functionality Tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ PyO3 Functionality Tests: FAILED" >> "$test_results_file"
        test_failed=$((test_failed + 1))
    fi
    
    # Test 4: Integration Tests
    if run_test_script "test_integration.sh"; then
        echo "✅ Integration Tests: PASSED" >> "$test_results_file"
        test_passed=$((test_passed + 1))
    else
        echo "❌ Integration Tests: FAILED" >> "$test_results_file"
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
    
    # Generate HTML report
    log "INFO" "Generating HTML report..."
    
    cat > "phase_4_deployment/tests/results/docker_integration_test_report.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Docker Integration Test Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .test-results {
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .pass {
            color: #28a745;
            font-weight: bold;
        }
        .fail {
            color: #dc3545;
            font-weight: bold;
        }
        .details {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Docker Integration Test Report</h1>
        <p>Generated on $(date)</p>
        
        <div class="summary">
            <h2>Test Summary</h2>
            <p>
                <strong>Passed:</strong> $test_passed<br>
                <strong>Failed:</strong> $test_failed<br>
                <strong>Total:</strong> $((test_passed + test_failed))
            </p>
        </div>
        
        <div class="test-results">
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test</th>
                    <th>Result</th>
                </tr>
                <tr>
                    <td>Docker Build Tests</td>
                    <td class="$([ -f phase_4_deployment/tests/results/docker_build_test_results.txt ] && grep -q "Docker Build Tests: PASSED" "$test_results_file" && echo "pass" || echo "fail")">
                        $([ -f phase_4_deployment/tests/results/docker_build_test_results.txt ] && grep -q "Docker Build Tests: PASSED" "$test_results_file" && echo "PASSED" || echo "FAILED")
                    </td>
                </tr>
                <tr>
                    <td>Docker Runtime Tests</td>
                    <td class="$([ -f phase_4_deployment/tests/results/docker_runtime_test_results.txt ] && grep -q "Docker Runtime Tests: PASSED" "$test_results_file" && echo "pass" || echo "fail")">
                        $([ -f phase_4_deployment/tests/results/docker_runtime_test_results.txt ] && grep -q "Docker Runtime Tests: PASSED" "$test_results_file" && echo "PASSED" || echo "FAILED")
                    </td>
                </tr>
                <tr>
                    <td>PyO3 Functionality Tests</td>
                    <td class="$([ -f phase_4_deployment/tests/results/pyo3_functionality_test_results.txt ] && grep -q "PyO3 Functionality Tests: PASSED" "$test_results_file" && echo "pass" || echo "fail")">
                        $([ -f phase_4_deployment/tests/results/pyo3_functionality_test_results.txt ] && grep -q "PyO3 Functionality Tests: PASSED" "$test_results_file" && echo "PASSED" || echo "FAILED")
                    </td>
                </tr>
                <tr>
                    <td>Integration Tests</td>
                    <td class="$([ -f phase_4_deployment/tests/results/integration_test_results.txt ] && grep -q "Integration Tests: PASSED" "$test_results_file" && echo "pass" || echo "fail")">
                        $([ -f phase_4_deployment/tests/results/integration_test_results.txt ] && grep -q "Integration Tests: PASSED" "$test_results_file" && echo "PASSED" || echo "FAILED")
                    </td>
                </tr>
            </table>
        </div>
        
        <div class="test-details">
            <h2>Test Details</h2>
            
            <h3>Docker Build Tests</h3>
            <div class="details">
$([ -f phase_4_deployment/tests/results/docker_build_test_results.txt ] && cat phase_4_deployment/tests/results/docker_build_test_results.txt || echo "No results available")
            </div>
            
            <h3>Docker Runtime Tests</h3>
            <div class="details">
$([ -f phase_4_deployment/tests/results/docker_runtime_test_results.txt ] && cat phase_4_deployment/tests/results/docker_runtime_test_results.txt || echo "No results available")
            </div>
            
            <h3>PyO3 Functionality Tests</h3>
            <div class="details">
$([ -f phase_4_deployment/tests/results/pyo3_functionality_test_results.txt ] && cat phase_4_deployment/tests/results/pyo3_functionality_test_results.txt || echo "No results available")
            </div>
            
            <h3>Integration Tests</h3>
            <div class="details">
$([ -f phase_4_deployment/tests/results/integration_test_results.txt ] && cat phase_4_deployment/tests/results/integration_test_results.txt || echo "No results available")
            </div>
        </div>
    </div>
</body>
</html>
EOF
    
    log "INFO" "HTML report generated: phase_4_deployment/tests/results/docker_integration_test_report.html"
    
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
