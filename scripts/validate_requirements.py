#!/usr/bin/env python3
"""
Requirements Validation Script
==============================

Validates that all required packages are installed with correct versions,
especially focusing on Solana ecosystem compatibility (solders + solana-py).
"""

import sys
import subprocess
import importlib
import pkg_resources
from typing import Dict, List, Tuple, Optional
from pathlib import Path

def get_installed_version(package_name: str) -> Optional[str]:
    """Get the installed version of a package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None

def check_solana_compatibility() -> Dict[str, any]:
    """Check Solana ecosystem package compatibility."""
    print("🔍 Checking Solana ecosystem compatibility...")
    
    results = {
        "compatible": False,
        "solders_version": None,
        "solana_version": None,
        "anchorpy_version": None,
        "issues": [],
        "recommendations": []
    }
    
    # Check solders version
    solders_version = get_installed_version("solders")
    if solders_version:
        results["solders_version"] = solders_version
        print(f"  ✅ solders: {solders_version}")
    else:
        results["issues"].append("solders not installed")
        print(f"  ❌ solders: Not installed")
    
    # Check solana version
    solana_version = get_installed_version("solana")
    if solana_version:
        results["solana_version"] = solana_version
        print(f"  ✅ solana: {solana_version}")
    else:
        results["issues"].append("solana not installed")
        print(f"  ❌ solana: Not installed")
    
    # Check anchorpy version
    anchorpy_version = get_installed_version("anchorpy")
    if anchorpy_version:
        results["anchorpy_version"] = anchorpy_version
        print(f"  ✅ anchorpy: {anchorpy_version}")
    else:
        results["issues"].append("anchorpy not installed")
        print(f"  ❌ anchorpy: Not installed")
    
    # Check compatibility
    if solders_version and solana_version:
        # Known compatible versions
        compatible_combinations = [
            ("0.26.0", "0.36.7"),
            ("0.25.0", "0.36.6"),
            ("0.24.0", "0.36.0"),
        ]
        
        is_compatible = False
        for solders_v, solana_v in compatible_combinations:
            if solders_version.startswith(solders_v) and solana_version.startswith(solana_v):
                is_compatible = True
                break
        
        if is_compatible:
            results["compatible"] = True
            print(f"  ✅ Compatibility: solders {solders_version} + solana {solana_version} are compatible")
        else:
            results["issues"].append(f"Potential compatibility issue: solders {solders_version} + solana {solana_version}")
            results["recommendations"].append("Update to solders 0.26.0 + solana 0.36.7 for best compatibility")
            print(f"  ⚠️ Compatibility: solders {solders_version} + solana {solana_version} may have issues")
    
    return results

def check_critical_packages() -> Dict[str, any]:
    """Check critical packages for trading system."""
    print("\n🔍 Checking critical packages...")
    
    critical_packages = {
        "httpx": ">=0.28.0",
        "pandas": ">=2.0.0",
        "numpy": ">=1.24.0,<2.0.0",
        "streamlit": ">=1.28.0",
        "plotly": ">=5.17.0",
        "python-dotenv": ">=1.0.0",
        "pyyaml": ">=6.0.1",
        "base58": ">=2.1.1",
        "aiohttp": ">=3.9.0",
        "websockets": ">=12.0",
    }
    
    results = {
        "all_installed": True,
        "packages": {},
        "missing": [],
        "outdated": []
    }
    
    for package, version_spec in critical_packages.items():
        installed_version = get_installed_version(package)
        
        if installed_version:
            results["packages"][package] = installed_version
            print(f"  ✅ {package}: {installed_version}")
            
            # Check if version meets requirements (basic check)
            if ">=" in version_spec:
                min_version = version_spec.split(">=")[1].split(",")[0]
                try:
                    if pkg_resources.parse_version(installed_version) < pkg_resources.parse_version(min_version):
                        results["outdated"].append(f"{package} {installed_version} < {min_version}")
                        print(f"    ⚠️ Version {installed_version} is below minimum {min_version}")
                except:
                    pass  # Skip version comparison if parsing fails
        else:
            results["missing"].append(package)
            results["all_installed"] = False
            print(f"  ❌ {package}: Not installed")
    
    return results

def check_optional_packages() -> Dict[str, any]:
    """Check optional packages."""
    print("\n🔍 Checking optional packages...")
    
    optional_packages = {
        "python-telegram-bot": "Telegram alerts",
        "prometheus-client": "Metrics collection",
        "psutil": "System monitoring",
        "loguru": "Advanced logging",
        "tenacity": "Retry logic",
        "rich": "Rich text formatting",
        "tqdm": "Progress bars"
    }
    
    results = {
        "packages": {},
        "missing": []
    }
    
    for package, description in optional_packages.items():
        installed_version = get_installed_version(package)
        
        if installed_version:
            results["packages"][package] = installed_version
            print(f"  ✅ {package}: {installed_version} ({description})")
        else:
            results["missing"].append(package)
            print(f"  ⏭️ {package}: Not installed ({description})")
    
    return results

def test_imports() -> Dict[str, any]:
    """Test critical imports."""
    print("\n🔍 Testing critical imports...")
    
    critical_imports = [
        ("solders.keypair", "Keypair"),
        ("solders.pubkey", "Pubkey"),
        ("solders.transaction", "Transaction"),
        ("solana.rpc.api", "Client"),
        ("solana.rpc.async_api", "AsyncClient"),
        ("base58", None),
        ("httpx", None),
        ("pandas", "pd"),
        ("numpy", "np"),
        ("streamlit", "st"),
        ("plotly.express", "px"),
        ("yaml", None),
        ("dotenv", "load_dotenv"),
    ]
    
    results = {
        "all_imports_successful": True,
        "successful": [],
        "failed": []
    }
    
    for module_path, alias in critical_imports:
        try:
            if alias:
                exec(f"import {module_path} as {alias}")
            else:
                exec(f"import {module_path}")
            results["successful"].append(module_path)
            print(f"  ✅ {module_path}")
        except ImportError as e:
            results["failed"].append((module_path, str(e)))
            results["all_imports_successful"] = False
            print(f"  ❌ {module_path}: {e}")
    
    return results

def generate_install_commands(missing_packages: List[str]) -> List[str]:
    """Generate pip install commands for missing packages."""
    if not missing_packages:
        return []
    
    # Group packages for efficient installation
    core_packages = []
    optional_packages = []
    
    for package in missing_packages:
        if package in ["solders", "solana", "anchorpy", "httpx", "pandas", "numpy", "streamlit", "plotly"]:
            core_packages.append(package)
        else:
            optional_packages.append(package)
    
    commands = []
    if core_packages:
        commands.append(f"pip install {' '.join(core_packages)}")
    if optional_packages:
        commands.append(f"pip install {' '.join(optional_packages)}")
    
    return commands

def main():
    """Main validation function."""
    print("🚀 RWA Trading System - Requirements Validation")
    print("=" * 60)
    print("Checking package installations and compatibility...")
    
    # Check Solana ecosystem
    solana_results = check_solana_compatibility()
    
    # Check critical packages
    critical_results = check_critical_packages()
    
    # Check optional packages
    optional_results = check_optional_packages()
    
    # Test imports
    import_results = test_imports()
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    # Overall status
    all_good = (
        solana_results["compatible"] and
        critical_results["all_installed"] and
        import_results["all_imports_successful"]
    )
    
    if all_good:
        print("🎉 All requirements validated successfully!")
        print("✅ System ready for live trading")
    else:
        print("⚠️ Some issues found - review and fix before live trading")
    
    # Detailed results
    if solana_results["issues"]:
        print(f"\n❌ Solana Ecosystem Issues:")
        for issue in solana_results["issues"]:
            print(f"  • {issue}")
    
    if critical_results["missing"]:
        print(f"\n❌ Missing Critical Packages:")
        for package in critical_results["missing"]:
            print(f"  • {package}")
    
    if critical_results["outdated"]:
        print(f"\n⚠️ Outdated Packages:")
        for package in critical_results["outdated"]:
            print(f"  • {package}")
    
    if import_results["failed"]:
        print(f"\n❌ Failed Imports:")
        for module, error in import_results["failed"]:
            print(f"  • {module}: {error}")
    
    # Installation commands
    all_missing = critical_results["missing"] + solana_results.get("missing_packages", [])
    if all_missing:
        print(f"\n💡 Installation Commands:")
        commands = generate_install_commands(all_missing)
        for cmd in commands:
            print(f"  {cmd}")
    
    # Recommendations
    if solana_results["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in solana_results["recommendations"]:
            print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    exit(main())
