#!/bin/bash
# Solarpunk Phone Testing Script
# Validates a provisioned phone

# Note: Don't use 'set -e' - we want to show errors but not exit the terminal

DEVICE_SERIAL=""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_pass() { echo -e "${GREEN}✓${NC} $1"; }
print_fail() { echo -e "${RED}✗${NC} $1"; }
print_warn() { echo -e "${YELLOW}!${NC} $1"; }

# Parse arguments
for arg in "$@"; do
    case $arg in
        --serial=*)
            DEVICE_SERIAL="${arg#*=}"
            ;;
    esac
done

# Build adb command
adb_cmd() {
    if [ -n "$DEVICE_SERIAL" ]; then
        adb -s "$DEVICE_SERIAL" "$@"
    else
        adb "$@"
    fi
}

# Test functions
test_device_connected() {
    if adb_cmd get-state &> /dev/null; then
        print_pass "Device connected"
        return 0
    else
        print_fail "Device not connected"
        return
    fi
}

test_android_version() {
    local sdk_version=$(adb_cmd shell getprop ro.build.version.sdk | tr -d '\r')
    if [ "$sdk_version" -ge 26 ]; then
        print_pass "Android SDK $sdk_version (8.0+)"
        return 0
    else
        print_warn "Android SDK $sdk_version (below 8.0)"
        return
    fi
}

test_solarpunk_app_installed() {
    if adb_cmd shell pm list packages | grep -q "org.solarpunk"; then
        print_pass "Solarpunk app installed"
        return 0
    else
        print_fail "Solarpunk app not installed"
        return
    fi
}

test_preset_exists() {
    if adb_cmd shell "[ -f /sdcard/solarpunk/preset.json ] && echo exists" | grep -q exists; then
        print_pass "Preset configuration exists"
        return 0
    else
        print_fail "Preset configuration missing"
        return
    fi
}

test_battery_level() {
    local battery=$(adb_cmd shell dumpsys battery | grep level | awk '{print $2}')
    if [ "$battery" -gt 50 ]; then
        print_pass "Battery level: ${battery}%"
        return 0
    else
        print_warn "Low battery: ${battery}%"
        return
    fi
}

test_storage_available() {
    local storage_mb=$(adb_cmd shell df /sdcard | tail -1 | awk '{print int($4/1024)}')
    if [ "$storage_mb" -gt 500 ]; then
        print_pass "Storage available: ${storage_mb}MB"
        return 0
    else
        print_warn "Low storage: ${storage_mb}MB"
        return
    fi
}

test_wifi_enabled() {
    local wifi_state=$(adb_cmd shell dumpsys wifi | grep "Wi-Fi is" | awk '{print $3}')
    if [ "$wifi_state" = "enabled" ]; then
        print_pass "WiFi enabled"
        return 0
    else
        print_warn "WiFi disabled"
        return
    fi
}

# Main test suite
main() {
    echo "========================================"
    echo "  Solarpunk Phone Validation"
    if [ -n "$DEVICE_SERIAL" ]; then
        echo "  Device: $DEVICE_SERIAL"
    fi
    echo "========================================"
    echo ""

    local tests_passed=0
    local tests_total=0

    # Run tests
    ((tests_total++)); test_device_connected && ((tests_passed++)) || true
    ((tests_total++)); test_android_version && ((tests_passed++)) || true
    ((tests_total++)); test_solarpunk_app_installed && ((tests_passed++)) || true
    ((tests_total++)); test_preset_exists && ((tests_passed++)) || true
    ((tests_total++)); test_battery_level && ((tests_passed++)) || true
    ((tests_total++)); test_storage_available && ((tests_passed++)) || true
    ((tests_total++)); test_wifi_enabled && ((tests_passed++)) || true

    echo ""
    echo "========================================"
    echo "  Results: $tests_passed/$tests_total passed"
    echo "========================================"

    if [ "$tests_passed" -eq "$tests_total" ]; then
        echo -e "${GREEN}Phone is ready for deployment!${NC}"
        exit 0
    else
        echo -e "${YELLOW}Some tests failed. Review above.${NC}"
        return
    fi
}

main
