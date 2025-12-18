#!/bin/bash
#
# Deploy Access Point on Raspberry Pi
#
# This script configures a Raspberry Pi as an AP island using a JSON config file.
# Installs and configures hostapd, dnsmasq, and network services.
#
# Usage: ./deploy_ap_raspberry_pi.sh <config_file>
#
# Example: ./deploy_ap_raspberry_pi.sh ../../ap_configs/garden_ap.json

set -e

CONFIG_FILE="$1"

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
        exit 1
    fi
}

check_config() {
    if [ -z "$CONFIG_FILE" ]; then
        log_error "Usage: $0 <config_file>"
        log_error "Example: $0 ../../ap_configs/garden_ap.json"
        exit 1
    fi

    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Config file not found: $CONFIG_FILE"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed"
        log_error "Install with: sudo apt-get install jq"
        exit 1
    fi

    log_info "Using config file: $CONFIG_FILE"
}

parse_config() {
    log_info "Parsing configuration..."

    # Network settings
    SSID=$(jq -r '.ssid' "$CONFIG_FILE")
    INTERFACE=$(jq -r '.hostapd.interface' "$CONFIG_FILE")
    CHANNEL=$(jq -r '.hostapd.channel' "$CONFIG_FILE")
    GATEWAY=$(jq -r '.network.gateway' "$CONFIG_FILE")
    SUBNET=$(jq -r '.network.subnet' "$CONFIG_FILE")
    DHCP_START=$(jq -r '.network.dhcp_range_start' "$CONFIG_FILE")
    DHCP_END=$(jq -r '.network.dhcp_range_end' "$CONFIG_FILE")

    log_info "SSID: $SSID"
    log_info "Interface: $INTERFACE"
    log_info "Gateway: $GATEWAY"
    log_info "Subnet: $SUBNET"
}

install_packages() {
    log_info "Installing required packages..."

    apt-get update
    apt-get install -y hostapd dnsmasq iptables jq

    # Stop services while we configure
    systemctl stop hostapd || true
    systemctl stop dnsmasq || true

    log_info "Packages installed"
}

configure_static_ip() {
    log_info "Configuring static IP on $INTERFACE..."

    # Backup existing config
    if [ -f /etc/dhcpcd.conf ]; then
        cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup
    fi

    # Add static IP configuration
    cat >> /etc/dhcpcd.conf <<EOF

# Solarpunk AP Configuration - $SSID
interface $INTERFACE
    static ip_address=$GATEWAY/24
    nohook wpa_supplicant
EOF

    log_info "Static IP configured: $GATEWAY"
}

configure_dnsmasq() {
    log_info "Configuring dnsmasq..."

    # Backup original
    if [ -f /etc/dnsmasq.conf ]; then
        mv /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
    fi

    # Create new config
    cat > /etc/dnsmasq.conf <<EOF
# Solarpunk Mesh Network - $SSID
interface=$INTERFACE
bind-interfaces
dhcp-range=$DHCP_START,$DHCP_END,12h
dhcp-authoritative
log-queries
log-facility=/var/log/dnsmasq.log

# Local domain
domain=solarpunk.local
local=/solarpunk.local/

# No upstream DNS (offline network)
no-resolv
EOF

    log_info "dnsmasq configured"
}

configure_hostapd() {
    log_info "Configuring hostapd..."

    # Create hostapd config from JSON
    cat > /etc/hostapd/hostapd.conf <<EOF
# Solarpunk Mesh Network - $SSID
interface=$INTERFACE
driver=$(jq -r '.hostapd.driver' "$CONFIG_FILE")
ssid=$SSID
hw_mode=$(jq -r '.hostapd.hw_mode' "$CONFIG_FILE")
channel=$CHANNEL
wmm_enabled=$(jq -r '.hostapd.wmm_enabled' "$CONFIG_FILE")
ieee80211n=$(jq -r '.hostapd.ieee80211n' "$CONFIG_FILE")
ht_capab=$(jq -r '.hostapd.ht_capab' "$CONFIG_FILE")
auth_algs=$(jq -r '.hostapd.auth_algs' "$CONFIG_FILE")

# Open network (no WPA)
# Security enforced at application layer
wpa=0

country_code=$(jq -r '.hostapd.country_code' "$CONFIG_FILE")
EOF

    # Tell system where to find hostapd config
    cat > /etc/default/hostapd <<EOF
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

    log_info "hostapd configured"
}

enable_ip_forwarding() {
    log_info "Enabling IP forwarding..."

    # Enable now
    echo 1 > /proc/sys/net/ipv4/ip_forward

    # Make persistent
    sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf || \
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

    log_info "IP forwarding enabled"
}

configure_firewall() {
    log_info "Configuring firewall..."

    # Flush existing rules
    iptables -F
    iptables -t nat -F

    # Allow established connections
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # Allow all on loopback
    iptables -A INPUT -i lo -j ACCEPT

    # Allow all from AP interface
    iptables -A INPUT -i "$INTERFACE" -j ACCEPT

    # Allow DTN sync (port 8000)
    iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

    # Allow VF node (port 8001)
    iptables -A INPUT -p tcp --dport 8001 -j ACCEPT

    # Save rules
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save
    else
        iptables-save > /etc/iptables/rules.v4
    fi

    log_info "Firewall configured"
}

enable_services() {
    log_info "Enabling services..."

    # Unmask and enable services
    systemctl unmask hostapd
    systemctl enable hostapd
    systemctl enable dnsmasq

    log_info "Services enabled"
}

start_services() {
    log_info "Starting services..."

    # Restart dhcpcd to apply static IP
    systemctl restart dhcpcd

    # Start AP services
    systemctl start hostapd
    systemctl start dnsmasq

    log_info "Services started"
}

show_status() {
    log_info "=== AP Deployment Complete ==="
    echo ""
    echo "SSID: $SSID"
    echo "Gateway: $GATEWAY"
    echo "DHCP Range: $DHCP_START - $DHCP_END"
    echo "Interface: $INTERFACE"
    echo ""
    log_info "Service Status:"
    systemctl status hostapd --no-pager -l || log_warn "hostapd not running"
    echo ""
    systemctl status dnsmasq --no-pager -l || log_warn "dnsmasq not running"
    echo ""
    log_info "Next steps:"
    echo "1. Deploy DTN node software at http://$GATEWAY:8000"
    echo "2. Deploy VF node software at http://$GATEWAY:8001"
    echo "3. Test connectivity from client device"
    echo ""
    echo "To view logs:"
    echo "  journalctl -u hostapd -f"
    echo "  journalctl -u dnsmasq -f"
}

main() {
    log_info "=== Raspberry Pi AP Deployment ==="
    echo ""

    check_root
    check_config
    parse_config
    install_packages
    configure_static_ip
    configure_dnsmasq
    configure_hostapd
    enable_ip_forwarding
    configure_firewall
    enable_services
    start_services
    show_status
}

main "$@"
