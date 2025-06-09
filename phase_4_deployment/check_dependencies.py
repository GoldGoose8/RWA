#!/usr/bin/env python3
"""
Dependency Checker for Q5 Trading System

This script checks if all required Python packages are installed
and provides instructions for installing missing packages.
"""

import importlib
import sys
import subprocess
from typing import List, Tuple

# List of required packages
REQUIRED_PACKAGES = [
    ("httpx", "HTTP client for async requests"),
    ("pandas", "Data analysis library"),
    ("numpy", "Numerical computing library"),
    ("plotly", "Interactive visualization library"),
    ("yaml", "YAML parser"),
    ("streamlit", "Dashboard framework"),
    ("solana", "Solana blockchain library"),
    ("base58", "Base58 encoding/decoding"),
    ("asyncio", "Asynchronous I/O library")
]

def check_package(package_name: str) -> bool:
    """
    Check if a package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        True if installed, False otherwise
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def get_missing_packages() -> List[Tuple[str, str]]:
    """
    Get a list of missing packages.
    
    Returns:
        List of tuples (package_name, description) for missing packages
    """
    missing = []
    for package, description in REQUIRED_PACKAGES:
        if not check_package(package):
            missing.append((package, description))
    return missing

def print_status():
    """Print the status of all required packages."""
    print("\n=== Q5 Trading System Dependency Checker ===\n")
    
    all_installed = True
    for package, description in REQUIRED_PACKAGES:
        is_installed = check_package(package)
        status = "✅ Installed" if is_installed else "❌ Missing"
        print(f"{package:15} - {status:12} - {description}")
        if not is_installed:
            all_installed = False
    
    return all_installed

def generate_install_command(missing_packages: List[Tuple[str, str]]) -> str:
    """
    Generate pip install command for missing packages.
    
    Args:
        missing_packages: List of missing packages
        
    Returns:
        Pip install command string
    """
    package_names = [package for package, _ in missing_packages]
    return f"pip install {' '.join(package_names)}"

def main():
    """Main function."""
    all_installed = print_status()
    
    if all_installed:
        print("\n✅ All dependencies are installed! You're ready to run the Q5 Trading System.")
    else:
        missing_packages = get_missing_packages()
        install_cmd = generate_install_command(missing_packages)
        
        print("\n❌ Some dependencies are missing.")
        print("\nTo install missing packages, run:")
        print(f"\n    {install_cmd}")
        print("\nAfter installing, run this script again to verify.")
        
        # Ask if user wants to install now
        if sys.stdout.isatty():  # Only ask if running in interactive terminal
            response = input("\nDo you want to install missing packages now? (y/n): ")
            if response.lower() == 'y':
                print(f"\nRunning: {install_cmd}")
                subprocess.call(install_cmd, shell=True)
                
                # Check again after installation
                print("\nChecking dependencies again...")
                all_installed = print_status()
                
                if all_installed:
                    print("\n✅ All dependencies are now installed! You're ready to run the Q5 Trading System.")
                else:
                    print("\n❌ Some dependencies are still missing. Please install them manually.")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
