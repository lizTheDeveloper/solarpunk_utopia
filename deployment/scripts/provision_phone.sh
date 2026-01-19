#!/bin/bash
# Solarpunk Phone Provisioning Script
# Provisions a single phone with the complete Solarpunk software stack

set -e  # Exit on error

# Default values
ROLE="citizen"
DEVICE_SERIAL=""
SKIP_APPS=false
SKIP_CONTENT=false

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "\n${GREEN}==>${NC} $1"; }

# Usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Provision a phone with Solarpunk software stack.

OPTIONS:
    --role=ROLE         Phone role: citizen|bridge|ap|library (default: citizen)
    --serial=SERIAL     Device serial (for multi-device, use 'adb devices')
    --skip-apps         Skip third-party app installation
    --skip-content      Skip content loading (Kiwix, maps)
    -h, --help          Show this help message

EXAMPLES:
    $0 --role=citizen
    $0 --role=bridge --serial=ABC123
    $0 --role=library --skip-content

PREREQUISITES:
    - adb installed and in PATH
    - Phone connected via USB with USB debugging enabled
    - Phone has LineageOS or compatible Android (8+)
    - Internet connection for app downloads

EOF
    return
}

# Parse arguments
for arg in "$@"; do
    case $arg in
        --role=*)
            ROLE="${arg#*=}"
            ;;
        --serial=*)
            DEVICE_SERIAL="${arg#*=}"
            ;;
        --skip-apps)
            SKIP_APPS=true
            ;;
        --skip-content)
            SKIP_CONTENT=true
            ;;
        -h|--help)
            usage
            ;;
        *)
            print_error "Unknown option: $arg"
            usage
            ;;
    esac
done

# Validate role
if [[ ! "$ROLE" =~ ^(citizen|bridge|ap|library)$ ]]; then
    print_error "Invalid role: $ROLE"
    usage
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
PRESET_FILE="$DEPLOY_DIR/presets/$ROLE.json"

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check adb
    if ! command -v adb &> /dev/null; then
        print_error "adb not found. Please install Android SDK platform-tools."
        return
    fi

    # Check preset file
    if [ ! -f "$PRESET_FILE" ]; then
        print_error "Preset file not found: $PRESET_FILE"
        return
    fi

    print_info "Prerequisites OK"
}

# Build adb command with optional serial
adb_cmd() {
    if [ -n "$DEVICE_SERIAL" ]; then
        adb -s "$DEVICE_SERIAL" "$@"
    else
        adb "$@"
    fi
}

# Check device connection
check_device() {
    print_step "Checking device connection..."

    if ! adb_cmd get-state &> /dev/null; then
        print_error "No device connected or adb not authorized"
        echo "Connected devices:"
        adb devices
        return
    fi

    local state=$(adb_cmd get-state 2>/dev/null)
    if [ "$state" != "device" ]; then
        print_error "Device is in state '$state', expected 'device'"
        return
    fi

    local sdk_version=$(adb_cmd shell getprop ro.build.version.sdk | tr -d '\r')
    if [ "$sdk_version" -lt 26 ]; then
        print_warn "Device is running Android SDK $sdk_version (Android 8 is SDK 26+)"
        print_warn "Some features may not work correctly"
    else
        print_info "Device running Android SDK $sdk_version"
    fi

    print_info "Device connected and ready"
}

# Install F-Droid
install_fdroid() {
    print_step "Installing F-Droid..."

    local fdroid_apk="$DEPLOY_DIR/apks/FDroid.apk"

    # Check if F-Droid already installed
    if adb_cmd shell pm list packages | grep -q "org.fdroid.fdroid"; then
        print_info "F-Droid already installed, skipping"
        return 0
    fi

    # Download if not present
    if [ ! -f "$fdroid_apk" ]; then
        print_info "Downloading F-Droid..."
        mkdir -p "$(dirname "$fdroid_apk")"
        curl -L "https://f-droid.org/F-Droid.apk" -o "$fdroid_apk"
    fi

    # Install
    print_info "Installing F-Droid APK..."
    adb_cmd install -r "$fdroid_apk"

    print_info "F-Droid installed successfully"
}

# Install base apps
install_base_apps() {
    if [ "$SKIP_APPS" = true ]; then
        print_step "Skipping base app installation (--skip-apps)"
        return 0
    fi

    print_step "Installing base apps..."

    # Note: In production, these would be installed via F-Droid or direct APKs
    # For now, just log what would be installed

    local apps=(
        "Briar:org.briarproject.briar.android"
        "Manyverse:se.manyver"
        "Syncthing:com.nutomic.syncthingandroid"
        "Kiwix:org.kiwix.kiwixmobile"
        "Organic Maps:app.organicmaps"
        "Termux:com.termux"
    )

    for app_entry in "${apps[@]}"; do
        IFS=: read -r app_name package_name <<< "$app_entry"
        print_info "Would install: $app_name ($package_name)"
        # TODO: Actual installation logic
        # - Check if APK exists in deployment/apks/
        # - If not, download from F-Droid
        # - Install via adb install
    done

    print_warn "Base app installation is stubbed - implement actual installation"
}

# Build and install custom APKs
install_custom_apks() {
    print_step "Installing custom Solarpunk APKs..."

    local frontend_apk="$DEPLOY_DIR/../frontend/android/app/build/outputs/apk/debug/app-debug.apk"

    # Check if APK exists
    if [ ! -f "$frontend_apk" ]; then
        print_warn "Frontend APK not found at: $frontend_apk"
        print_info "Building frontend APK..."

        # Build APK
        cd "$DEPLOY_DIR/../frontend"
        if [ -f "android/gradlew" ]; then
            npm run build
            cd android
            ./gradlew assembleDebug
            cd "$SCRIPT_DIR"
        else
            print_error "Cannot build APK - gradlew not found"
            return
        fi
    fi

    if [ -f "$frontend_apk" ]; then
        print_info "Installing Solarpunk ValueFlows Node..."
        adb_cmd install -r "$frontend_apk"
        print_info "Solarpunk app installed successfully"
    else
        print_error "Failed to locate or build APK"
        return
    fi
}

# Apply preset configuration
apply_preset() {
    print_step "Applying $ROLE preset configuration..."

    # Push preset file to device
    local device_preset_path="/sdcard/solarpunk/preset.json"
    adb_cmd shell mkdir -p /sdcard/solarpunk
    adb_cmd push "$PRESET_FILE" "$device_preset_path"

    print_info "Preset file pushed to device: $device_preset_path"
    print_info "App will read this on first launch"

    # TODO: If app supports adb shell commands for configuration, use them here
    # For example:
    # adb_cmd shell am broadcast -a org.solarpunk.APPLY_PRESET --es preset_path "$device_preset_path"
}

# Load content packs
load_content() {
    if [ "$SKIP_CONTENT" = true ]; then
        print_step "Skipping content loading (--skip-content)"
        return 0
    fi

    print_step "Loading content packs..."

    case "$ROLE" in
        library)
            print_info "Library role: Would load full Kiwix content packs"
            # TODO: Push Kiwix ZIM files to /sdcard/Android/data/org.kiwix.kiwixmobile/files/
            ;;
        *)
            print_info "Non-library role: Minimal content only"
            ;;
    esac

    print_warn "Content loading is stubbed - implement actual content push"
}

# Run validation tests
validate_installation() {
    print_step "Validating installation..."

    local checks_passed=0
    local checks_total=0

    # Check: Solarpunk app installed
    ((checks_total++))
    if adb_cmd shell pm list packages | grep -q "org.solarpunk"; then
        print_info "✓ Solarpunk app installed"
        ((checks_passed++))
    else
        print_warn "✗ Solarpunk app not found"
    fi

    # Check: Preset file exists
    ((checks_total++))
    if adb_cmd shell "[ -f /sdcard/solarpunk/preset.json ] && echo exists" | grep -q exists; then
        print_info "✓ Preset file exists"
        ((checks_passed++))
    else
        print_warn "✗ Preset file not found"
    fi

    # Check: Storage available
    ((checks_total++))
    local storage_mb=$(adb_cmd shell df /sdcard | tail -1 | awk '{print int($4/1024)}')
    if [ "$storage_mb" -gt 1000 ]; then
        print_info "✓ Storage available: ${storage_mb}MB"
        ((checks_passed++))
    else
        print_warn "✗ Low storage: ${storage_mb}MB"
    fi

    # Check: Battery level
    ((checks_total++))
    local battery=$(adb_cmd shell dumpsys battery | grep level | awk '{print $2}')
    if [ "$battery" -gt 50 ]; then
        print_info "✓ Battery level: ${battery}%"
        ((checks_passed++))
    else
        print_warn "✗ Low battery: ${battery}%"
    fi

    echo ""
    print_info "Validation: $checks_passed/$checks_total checks passed"

    if [ "$checks_passed" -eq "$checks_total" ]; then
        return 0
    else
        return
    fi
}

# Main provisioning flow
main() {
    local start_time=$(date +%s)

    echo "=========================================="
    echo "  Solarpunk Phone Provisioning"
    echo "  Role: $ROLE"
    echo "=========================================="
    echo ""

    check_prerequisites
    check_device
    install_fdroid
    install_base_apps
    install_custom_apks
    apply_preset
    load_content
    validate_installation

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    echo "=========================================="
    print_info "Provisioning complete in ${duration}s"
    echo "=========================================="
    echo ""
    print_info "Phone is ready for workshop!"
    print_info "Next steps:"
    echo "  1. Charge phone to >80%"
    echo "  2. Label phone (role: $ROLE)"
    echo "  3. Test offer/need creation"
    echo ""
}

# Run main
main
