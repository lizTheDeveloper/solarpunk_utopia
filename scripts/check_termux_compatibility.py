#!/usr/bin/env python3
"""
Check if Python packages are compatible with Termux (no Rust/maturin required).

This script analyzes requirements.txt and checks if packages would build successfully
on Termux/Android without requiring Rust compiler or maturin.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Packages known to require Rust/maturin (incomplete list - add as discovered)
RUST_PACKAGES = {
    "anthropic": "Uses tokenizers which requires Rust",
    "tokenizers": "Requires Rust compiler and maturin",
    "pydantic": "v2.x requires pydantic-core which uses Rust (v1.10.x is pure Python)",
    "pydantic-core": "Requires Rust compiler",
    "cryptography": "Requires Rust (but available via pkg on Termux)",
    "bcrypt": "Requires compilation (but available via pkg on Termux)",
}

# Packages available via Termux pkg repository (no pip build needed)
TERMUX_PKG_AVAILABLE = {
    "cryptography": "python-cryptography",
    "bcrypt": "python-bcrypt",
    "numpy": "python-numpy",
    "pillow": "python-pillow",
}


def parse_requirements(req_file: Path) -> List[Tuple[str, str]]:
    """Parse requirements.txt and return list of (package, version) tuples."""
    packages = []

    if not req_file.exists():
        return packages

    for line in req_file.read_text().splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Parse package==version format
        if "==" in line:
            package, version = line.split("==", 1)
            packages.append((package.strip(), version.strip()))
        else:
            packages.append((line.strip(), "latest"))

    return packages


def check_package_compatibility(package: str, version: str) -> Dict[str, any]:
    """Check if a package is compatible with Termux."""
    result = {
        "package": package,
        "version": version,
        "compatible": True,
        "warnings": [],
        "solutions": [],
    }

    # Check if package requires Rust
    if package in RUST_PACKAGES:
        result["compatible"] = False
        result["warnings"].append(f"⚠️  {RUST_PACKAGES[package]}")

        # Check if available via Termux pkg
        if package in TERMUX_PKG_AVAILABLE:
            result["solutions"].append(
                f"✓ Available via pkg: pkg install {TERMUX_PKG_AVAILABLE[package]}"
            )
        else:
            result["solutions"].append("✗ Not available via pkg - must remove or replace")

    # Special handling for pydantic
    if package == "pydantic":
        if version.startswith("2."):
            result["compatible"] = False
            result["warnings"].append("⚠️  Pydantic v2 requires pydantic-core (Rust)")
            result["solutions"].append("✓ Downgrade to pydantic==1.10.13 (pure Python)")
            result["solutions"].append("✗ Or use pkg install python-pydantic (if available)")
        elif version.startswith("1."):
            result["compatible"] = True
            result["warnings"].append("✓ Pydantic v1 is pure Python (no Rust needed)")

    return result


def main():
    """Main entry point."""
    print("=" * 60)
    print("Termux Compatibility Checker")
    print("=" * 60)
    print()

    # Check both requirements files
    repo_root = Path(__file__).parent.parent
    req_files = [
        repo_root / "requirements.txt",
        repo_root / "requirements-termux.txt",
    ]

    all_compatible = True

    for req_file in req_files:
        if not req_file.exists():
            continue

        print(f"Checking: {req_file.name}")
        print("-" * 60)

        packages = parse_requirements(req_file)

        for package, version in packages:
            result = check_package_compatibility(package, version)

            if not result["compatible"]:
                all_compatible = False
                print(f"❌ {package}=={version}")
                for warning in result["warnings"]:
                    print(f"   {warning}")
                for solution in result["solutions"]:
                    print(f"   {solution}")
            else:
                print(f"✅ {package}=={version}")
                for warning in result["warnings"]:
                    print(f"   {warning}")

        print()

    # Summary
    print("=" * 60)
    if all_compatible:
        print("✅ All packages are Termux compatible!")
        print()
        print("Installation should work with:")
        print("  pkg install python git")
        print("  pip install -r requirements.txt")
        return 0
    else:
        print("❌ Some packages are NOT Termux compatible")
        print()
        print("Recommendations:")
        print("  1. Use requirements-termux.txt instead of requirements.txt")
        print("  2. Install binary packages via pkg before pip:")
        print("     pkg install python-cryptography python-bcrypt")
        print("  3. Remove or replace incompatible packages")
        return 1


if __name__ == "__main__":
    sys.exit(main())
