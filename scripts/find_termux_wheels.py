#!/usr/bin/env python3
"""
Check if binary wheels exist for packages on Termux architectures.

Termux common architectures:
- aarch64 (ARM 64-bit) - most common on modern Android
- armv7l (ARM 32-bit)
- x86_64 (Android emulator)
"""

import json
import urllib.request
import sys


def check_wheel_availability(package: str, version: str, arch: str = "aarch64"):
    """Check if binary wheel exists for package on given architecture."""
    # Map Termux arch to Python platform tags
    platform_tags = {
        "aarch64": "manylinux_2_17_aarch64.manylinux2014_aarch64",
        "armv7l": "manylinux_2_17_armv7l.manylinux2014_armv7l",
        "x86_64": "manylinux_2_17_x86_64.manylinux2014_x86_64",
    }

    platform_tag = platform_tags.get(arch, platform_tags["aarch64"])

    # Check PyPI JSON API
    url = f"https://pypi.org/pypi/{package}/{version}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        # Check for wheels
        wheels = [
            url_info
            for url_info in data["urls"]
            if url_info["packagetype"] == "bdist_wheel"
        ]

        # Check for compatible wheels
        compatible_wheels = [
            w
            for w in wheels
            if arch in w["filename"] or "any" in w["filename"]
        ]

        return {
            "package": package,
            "version": version,
            "arch": arch,
            "total_wheels": len(wheels),
            "compatible_wheels": len(compatible_wheels),
            "has_binary": len(compatible_wheels) > 0,
            "wheel_files": [w["filename"] for w in compatible_wheels[:3]],
        }

    except Exception as e:
        return {
            "package": package,
            "version": version,
            "arch": arch,
            "error": str(e),
            "has_binary": False,
        }


def main():
    """Check binary wheel availability for problematic packages."""
    packages = [
        ("pydantic", "2.10.5"),
        ("pydantic-core", "2.27.2"),  # Latest pydantic-core
        ("pydantic", "1.10.13"),  # Pure Python version
    ]

    print("=" * 70)
    print("Binary Wheel Availability Check for Termux")
    print("=" * 70)
    print()

    for arch in ["aarch64", "x86_64"]:
        print(f"Architecture: {arch} (Termux)")
        print("-" * 70)

        for package, version in packages:
            result = check_wheel_availability(package, version, arch)

            if result.get("error"):
                print(f"❌ {package}=={version}: Error - {result['error']}")
            elif result["has_binary"]:
                print(f"✅ {package}=={version}: {result['compatible_wheels']} wheels")
                for wheel in result.get("wheel_files", []):
                    print(f"   - {wheel}")
            else:
                print(f"❌ {package}=={version}: No binary wheels (requires build)")

        print()


if __name__ == "__main__":
    main()
