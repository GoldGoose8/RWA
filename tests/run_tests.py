#!/usr/bin/env python3
"""
Run all tests for the Synergy7 Trading System.
"""

import unittest
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_runner")

def run_tests():
    """Run all tests in the tests directory."""
    # Get the directory containing this script
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add parent directory to path
    sys.path.append(os.path.dirname(tests_dir))
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(tests_dir, pattern="test_*.py")
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Print summary
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Return success/failure
    return len(result.errors) == 0 and len(result.failures) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
