#!/usr/bin/env python3
"""
Find pydantic versions with ARM binary wheels available.
"""

import json
import urllib.request
import sys


def check_version_wheels(package, version, arch="aarch64"):
    """Check if a specific version has ARM wheels."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        wheels = [
            url_info
            for url_info in data["urls"]
            if url_info["packagetype"] == "bdist_wheel"
        ]

        arm_wheels = [
            w for w in wheels
            if "aarch64" in w["filename"] or "arm" in w["filename"] or "any" in w["filename"]
        ]

        return len(arm_wheels) > 0, arm_wheels

    except Exception as e:
        return False, []


def get_recent_versions(package, limit=20):
    """Get recent versions of a package."""
    url = f"https://pypi.org/pypi/{package}/json"

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())

        versions = list(data["releases"].keys())
        # Filter to only 2.x versions and sort
        v2_versions = [v for v in versions if v.startswith("2.")]
        v2_versions.sort(reverse=True)

        return v2_versions[:limit]

    except Exception as e:
        print(f"Error fetching versions: {e}")
        return []


def main():
    print("=" * 70)
    print("Finding pydantic versions with ARM binary wheels")
    print("=" * 70)
    print()

    # Check pydantic-core first
    print("Checking pydantic-core versions...")
    print("-" * 70)

    core_versions = get_recent_versions("pydantic-core", 15)

    working_core_versions = []
    for version in core_versions:
        has_wheels, wheels = check_version_wheels("pydantic-core", version)
        if has_wheels:
            working_core_versions.append(version)
            wheel_names = [w["filename"] for w in wheels[:2]]
            print(f"✅ pydantic-core {version}")
            for wname in wheel_names:
                print(f"   - {wname}")
        else:
            print(f"❌ pydantic-core {version} (no ARM wheels)")

    print()
    print("=" * 70)
    print("Checking pydantic versions...")
    print("-" * 70)

    pydantic_versions = get_recent_versions("pydantic", 15)

    for version in pydantic_versions:
        has_wheels, wheels = check_version_wheels("pydantic", version)
        if has_wheels:
            print(f"✅ pydantic {version}")
            wheel_names = [w["filename"] for w in wheels[:1]]
            for wname in wheel_names:
                print(f"   - {wname}")
        else:
            print(f"❌ pydantic {version} (no wheels)")

    print()
    print("=" * 70)
    print("RECOMMENDED FOR TERMUX:")
    print("=" * 70)

    if working_core_versions:
        latest_working = working_core_versions[0]
        print(f"✅ pydantic-core {latest_working} has ARM wheels")
        print(f"✅ Use: pip install --only-binary :all: pydantic-core=={latest_working}")
        print()

        # Find compatible pydantic version
        for pyd_ver in pydantic_versions[:5]:
            has_wheels, _ = check_version_wheels("pydantic", pyd_ver)
            if has_wheels:
                print(f"✅ pydantic {pyd_ver} (compatible)")
                print(f"   pip install --only-binary :all: pydantic=={pyd_ver}")
                break
    else:
        print("❌ No recent versions have ARM wheels")
        print("   This is unusual - check PyPI directly")


if __name__ == "__main__":
    main()
