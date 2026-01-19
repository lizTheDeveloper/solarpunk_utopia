#!/bin/bash
#
# Setup BATMAN-adv mesh networking (Mode A)
#
# This script configures a device to participate in BATMAN-adv mesh routing.
# Requires: Rooted Android with LineageOS or Linux with batman-adv kernel support
#
# Usage: ./setup_batman_adv.sh [interface] [mesh_address]
#
# Example: ./setup_batman_adv.sh wlan0 10.44.0.42

set -e

# Configuration
WLAN_INTERFACE="${1:-wlan0}"
MESH_ADDRESS="${2:-10.44.0.$(shuf -i 10-250 -n 1)}"  # Random if not specified
BATMAN_INTERFACE="bat0"
MESH_ESSID="solarpunk-mesh-adhoc"
MESH_CHANNEL="6"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

check_batman_module() {
    log_info "Checking for batman-adv kernel module..."

    if lsmod | grep -q batman_adv; then
        log_info "batman-adv module already loaded"
        return 0
    fi

    log_info "Loading batman-adv module..."
    if modprobe batman_adv; then
        log_info "batman-adv module loaded successfully"
        return 0
    else
        log_error "Failed to load batman-adv module"
        log_error "Your kernel may not have batman-adv support"
        log_error "On LineageOS: Kernel must be compiled with CONFIG_BATMAN_ADV=m"
        return 1
    fi
}

install_batctl() {
    log_info "Checking for batctl..."

    if command -v batctl &> /dev/null; then
        log_info "batctl found: $(batctl -v)"
        return 0
    fi

    log_warn "batctl not found, attempting to install..."

    # Try different package managers
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y batctl
    elif command -v apk &> /dev/null; then
        apk add batctl
    elif command -v pkg &> /dev/null; then
        # Termux on Android
        pkg install batctl
    else
        log_error "Could not install batctl automatically"
        log_error "Please install batctl manually"
        return 1
    fi

    log_info "batctl installed successfully"
}

setup_wireless_interface() {
    log_info "Configuring wireless interface: $WLAN_INTERFACE"

    # Bring interface down
    ip link set "$WLAN_INTERFACE" down

    # Set to ad-hoc mode
    log_info "Setting interface to ad-hoc mode..."
    if ! iw dev "$WLAN_INTERFACE" set type ibss; then
        log_warn "Failed to set ad-hoc mode with iw, trying iwconfig..."
        iwconfig "$WLAN_INTERFACE" mode ad-hoc || {
            log_error "Failed to set ad-hoc mode"
            return 1
        }
    fi

    # Set ESSID for ad-hoc network
    log_info "Setting mesh ESSID: $MESH_ESSID"
    iw dev "$WLAN_INTERFACE" ibss join "$MESH_ESSID" 2437 || {
        iwconfig "$WLAN_INTERFACE" essid "$MESH_ESSID" || {
            log_error "Failed to set ESSID"
            return 1
        }
    }

    # Set channel
    log_info "Setting channel: $MESH_CHANNEL"
    iwconfig "$WLAN_INTERFACE" channel "$MESH_CHANNEL" || log_warn "Failed to set channel (may already be set)"

    # Bring interface up
    ip link set "$WLAN_INTERFACE" up

    # Wait for interface to be ready
    sleep 2

    log_info "Wireless interface configured"
}

create_batman_interface() {
    log_info "Creating batman-adv interface: $BATMAN_INTERFACE"

    # Add wireless interface to batman-adv
    log_info "Adding $WLAN_INTERFACE to batman-adv..."
    batctl meshif "$BATMAN_INTERFACE" interface add "$WLAN_INTERFACE" || {
        log_error "Failed to add interface to batman-adv"
        return 1
    }

    # Enable aggregation for better performance
    batctl meshif "$BATMAN_INTERFACE" aggregation 1 || log_warn "Could not enable aggregation"

    # Enable bridge loop avoidance
    batctl meshif "$BATMAN_INTERFACE" bridge_loop_avoidance 1 || log_warn "Could not enable BLA"

    # Enable distributed ARP table
    batctl meshif "$BATMAN_INTERFACE" distributed_arp_table 1 || log_warn "Could not enable DAT"

    # Bring batman interface up
    ip link set "$BATMAN_INTERFACE" up

    log_info "Batman interface created"
}

assign_ip_address() {
    log_info "Assigning IP address: $MESH_ADDRESS/16"

    # Assign IP to batman interface
    ip addr add "$MESH_ADDRESS/16" dev "$BATMAN_INTERFACE" || {
        log_warn "IP address may already be assigned"
    }

    log_info "IP address configured"
}

enable_ip_forwarding() {
    log_info "Enabling IP forwarding..."

    echo 1 > /proc/sys/net/ipv4/ip_forward

    # Make it persistent (if sysctl is available)
    if [ -f /etc/sysctl.conf ]; then
        if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
            echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
        fi
    fi

    log_info "IP forwarding enabled"
}

show_status() {
    log_info "BATMAN-adv mesh status:"
    echo ""
    echo "Interface: $BATMAN_INTERFACE"
    batctl meshif "$BATMAN_INTERFACE" interface || log_warn "Could not get interface info"
    echo ""
    echo "Mesh neighbors:"
    batctl meshif "$BATMAN_INTERFACE" neighbors || log_warn "Could not get neighbors"
    echo ""
    echo "IP configuration:"
    ip addr show "$BATMAN_INTERFACE"
    echo ""
    log_info "Setup complete!"
    echo ""
    echo "Your mesh address: $MESH_ADDRESS"
    echo "Batman interface: $BATMAN_INTERFACE"
    echo "Wireless interface: $WLAN_INTERFACE"
    echo ""
    echo "To verify mesh connectivity:"
    echo "  batctl meshif $BATMAN_INTERFACE neighbors"
    echo "  batctl meshif $BATMAN_INTERFACE originators"
    echo ""
    echo "DTN node should now be reachable at: http://$MESH_ADDRESS:8000"
}

main() {
    log_info "=== BATMAN-adv Mesh Setup (Mode A) ==="
    log_info "Wireless Interface: $WLAN_INTERFACE"
    log_info "Mesh Address: $MESH_ADDRESS"
    echo ""

    check_root
    check_batman_module
    install_batctl
    setup_wireless_interface
    create_batman_interface
    assign_ip_address
    enable_ip_forwarding
    show_status
}

main "$@"
