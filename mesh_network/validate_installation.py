#!/usr/bin/env python3
"""
Validation Script: Multi-AP Mesh Network

Validates that all components are properly installed and functional.
Run this before physical deployment.
"""

import os
import sys
import json
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - NOT FOUND: {filepath}")
        return False


def check_json_valid(filepath: str, description: str) -> bool:
    """Check if JSON file is valid"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description} - INVALID JSON: {e}")
        return False


def check_script_executable(filepath: str, description: str) -> bool:
    """Check if script is executable"""
    if os.path.exists(filepath) and os.access(filepath, os.X_OK):
        print(f"✅ {description}")
        return True
    else:
        print(f"⚠️  {description} - NOT EXECUTABLE (run: chmod +x {filepath})")
        return False


def check_python_imports() -> bool:
    """Check if Python modules can be imported"""
    try:
        # Check bridge_node imports
        from bridge_node import (
            NetworkMonitor,
            SyncOrchestrator,
            BridgeMetrics,
            ModeDetector
        )
        print("✅ Python modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Python module import failed: {e}")
        print("   Run: pip install -r requirements.txt")
        return False


def main():
    """Run validation checks"""
    print("\n" + "="*60)
    print("Multi-AP Mesh Network - Installation Validation")
    print("="*60 + "\n")

    base_path = Path(__file__).parent
    all_passed = True

    # Check AP Configs
    print("📋 AP Configuration Templates:")
    all_passed &= check_json_valid(
        base_path / "ap_configs/garden_ap.json",
        "Garden AP config"
    )
    all_passed &= check_json_valid(
        base_path / "ap_configs/kitchen_ap.json",
        "Kitchen AP config"
    )
    all_passed &= check_json_valid(
        base_path / "ap_configs/workshop_ap.json",
        "Workshop AP config"
    )
    all_passed &= check_json_valid(
        base_path / "ap_configs/library_ap.json",
        "Library AP config"
    )
    print()

    # Check Bridge Node Services
    print("🌉 Bridge Node Services:")
    all_passed &= check_file_exists(
        base_path / "bridge_node/services/network_monitor.py",
        "NetworkMonitor service"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/services/sync_orchestrator.py",
        "SyncOrchestrator service"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/services/bridge_metrics.py",
        "BridgeMetrics service"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/services/mode_detector.py",
        "ModeDetector service"
    )
    print()

    # Check API
    print("🔌 Bridge API:")
    all_passed &= check_file_exists(
        base_path / "bridge_node/api/bridge_api.py",
        "Bridge API endpoints"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/main.py",
        "Bridge API application"
    )
    print()

    # Check Scripts
    print("📜 Mode A Scripts:")
    all_passed &= check_script_executable(
        base_path / "mode_a/scripts/setup_batman_adv.sh",
        "BATMAN-adv setup script"
    )
    all_passed &= check_script_executable(
        base_path / "mode_a/scripts/teardown_batman_adv.sh",
        "BATMAN-adv teardown script"
    )
    all_passed &= check_script_executable(
        base_path / "mode_a/scripts/deploy_ap_raspberry_pi.sh",
        "AP deployment script"
    )
    print()

    # Check Tests
    print("🧪 Test Suite:")
    all_passed &= check_file_exists(
        base_path / "bridge_node/tests/test_network_monitor.py",
        "NetworkMonitor tests"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/tests/test_sync_orchestrator.py",
        "SyncOrchestrator tests"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/tests/test_mode_detector.py",
        "ModeDetector tests"
    )
    all_passed &= check_file_exists(
        base_path / "bridge_node/tests/test_bridge_metrics.py",
        "BridgeMetrics tests"
    )
    print()

    # Check Documentation
    print("📚 Documentation:")
    all_passed &= check_file_exists(
        base_path / "README.md",
        "Main README"
    )
    all_passed &= check_file_exists(
        base_path / "docs/deployment_guide.md",
        "Deployment guide"
    )
    all_passed &= check_file_exists(
        base_path / "docs/mode_a_requirements.md",
        "Mode A requirements"
    )
    all_passed &= check_file_exists(
        base_path / "IMPLEMENTATION_SUMMARY.md",
        "Implementation summary"
    )
    print()

    # Check Python Imports
    print("🐍 Python Modules:")
    all_passed &= check_python_imports()
    print()

    # Summary
    print("="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("\nNext steps:")
        print("1. Review documentation: README.md")
        print("2. Read deployment guide: docs/deployment_guide.md")
        print("3. Run tests: pytest bridge_node/tests/ -v")
        print("4. Try example: python example_integration.py")
        print("5. Deploy to hardware when ready")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nPlease fix issues above before deployment")
        sys.exit(1)
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
