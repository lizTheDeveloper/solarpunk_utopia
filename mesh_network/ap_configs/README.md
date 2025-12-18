# AP Configuration Templates

This directory contains JSON configuration templates for Access Point (AP) "islands" in the Solarpunk mesh network.

## Available Configurations

- `garden_ap.json` - Outdoor garden area (10.44.1.0/24)
- `kitchen_ap.json` - Kitchen/dining area (10.44.2.0/24)
- `workshop_ap.json` - Workshop/maker space (10.44.3.0/24)
- `library_ap.json` - Library/knowledge hub (10.44.4.0/24)

## Configuration Structure

Each AP configuration includes:

### Network Settings
- **SSID**: Unique identifier (e.g., "SolarpunkGarden")
- **Subnet**: Isolated /24 subnet (10.44.X.0/24)
- **Gateway**: AP address (10.44.X.1)
- **DHCP Range**: Client addresses (10.44.X.10 - 10.44.X.250)

### hostapd Settings
- **Interface**: Wireless interface (usually wlan0)
- **Channel**: Non-overlapping channels (1, 6, 11)
- **Mode**: 802.11g/n for compatibility
- **Security**: Open network (WPA disabled for community access)

### dnsmasq Settings
- **DHCP Server**: Automatic IP assignment
- **DNS**: Local DNS resolution
- **Lease Time**: 12-hour leases

### Services
- **DTN Node**: Bundle synchronization (port 8000)
- **VF Node**: ValueFlows API (port 8001)

### Deployment Info
- **Hardware**: Target device (Raspberry Pi 4)
- **Power**: Power source (solar, wall, battery)
- **Coverage**: Physical area served
- **Expected Users**: Capacity planning

### Metadata
- **Island ID**: Unique identifier for the island
- **Island Type**: Indoor/outdoor classification
- **Priority Categories**: Content categories for this location
- **Schema Version**: Configuration format version

## Usage

### Raspberry Pi Deployment

1. Copy the appropriate config file to the target device
2. Use the `deploy_ap_raspberry_pi.sh` script (see `../mode_a/scripts/`)
3. The script will:
   - Install hostapd and dnsmasq
   - Generate hostapd.conf from JSON template
   - Generate dnsmasq.conf from JSON template
   - Configure network interfaces
   - Enable IP forwarding (for Mode A if needed)
   - Start services

### Android AP Deployment

For Android devices used as APs:

1. Root access required for full control
2. Use Termux + custom scripts
3. Or use Android's built-in AP mode (limited configuration)
4. See `docs/android_ap_setup.md` for detailed instructions

## Network Architecture

```
10.44.0.0/16 - Overall mesh network space
├── 10.44.1.0/24 - Garden Island
├── 10.44.2.0/24 - Kitchen Island
├── 10.44.3.0/24 - Workshop Island
└── 10.44.4.0/24 - Library Island

Mode C (DTN-Only):
- Islands operate independently
- Bridge nodes carry bundles between islands
- No IP routing between subnets

Mode A (BATMAN-adv):
- bat0 interface bridges islands
- Multi-hop routing over mesh
- Addresses from 10.44.0.0/16
- Graceful fallback to Mode C
```

## Channel Planning

To minimize interference, APs use non-overlapping 2.4GHz channels:

- Garden: Channel 6
- Kitchen: Channel 11
- Workshop: Channel 1
- Library: Channel 6 (physically separated from Garden)

## Security Notes

**Open Network Design:**
- No WPA/WPA2 (facilitates easy community access)
- Security enforced at application layer (bundle signatures)
- Audience enforcement controls data distribution
- Trust scores limit exposure to untrusted peers

**Physical Security:**
- APs should be in semi-public community spaces
- Not suitable for sensitive personal data
- Use for commune coordination only

## Adding New Islands

To add a new AP island:

1. Copy an existing template
2. Assign next available subnet (10.44.X.0/24)
3. Choose non-overlapping channel
4. Update SSID and location metadata
5. Configure priority categories for the location
6. Deploy using setup scripts

## See Also

- `../mode_a/scripts/` - Deployment scripts
- `../docs/deployment_guide.md` - Complete deployment guide
- `../bridge_node/` - Bridge node configuration
