#!/bin/bash
#
# Teardown BATMAN-adv mesh networking
#
# This script removes BATMAN-adv configuration and returns interface to normal mode.
#
# Usage: ./teardown_batman_adv.sh [interface]

set -e

WLAN_INTERFACE="${1:-wlan0}"
BATMAN_INTERFACE="bat0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        return 1
    fi
}

main() {
    log_info "=== BATMAN-adv Teardown ==="

    check_root

    # Remove interface from batman-adv
    if command -v batctl &> /dev/null; then
        log_info "Removing $WLAN_INTERFACE from batman-adv..."
        batctl meshif "$BATMAN_INTERFACE" interface del "$WLAN_INTERFACE" 2>/dev/null || log_warn "Interface not in batman mesh"
    fi

    # Bring down batman interface
    log_info "Bringing down $BATMAN_INTERFACE..."
    ip link set "$BATMAN_INTERFACE" down 2>/dev/null || log_warn "Batman interface already down"

    # Bring down wireless interface
    log_info "Bringing down $WLAN_INTERFACE..."
    ip link set "$WLAN_INTERFACE" down 2>/dev/null || log_warn "Wireless interface already down"

    # Set wireless back to managed mode
    log_info "Resetting $WLAN_INTERFACE to managed mode..."
    iw dev "$WLAN_INTERFACE" set type managed 2>/dev/null || \
        iwconfig "$WLAN_INTERFACE" mode managed 2>/dev/null || \
        log_warn "Could not reset to managed mode"

    # Bring wireless interface back up
    ip link set "$WLAN_INTERFACE" up

    # Unload batman module (optional)
    log_info "Unloading batman-adv module (optional)..."
    rmmod batman_adv 2>/dev/null || log_warn "batman-adv module not loaded or in use"

    log_info "Teardown complete"
    log_info "Wireless interface $WLAN_INTERFACE is now in managed mode"
}

main "$@"
