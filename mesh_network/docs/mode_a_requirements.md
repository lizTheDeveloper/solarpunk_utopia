# Mode A (BATMAN-adv) Requirements

Complete guide to Mode A requirements, setup, and limitations.

## Overview

Mode A provides multi-hop mesh routing using BATMAN-adv (Better Approach To Mobile Ad-hoc Networking - advanced).

**Critical:** Mode A is optional. Mode C (DTN-only) must always work. Mode A provides speedup when available.

## What is BATMAN-adv?

BATMAN-adv is a kernel-space mesh routing protocol that:
- Creates a virtual network interface (bat0)
- Routes packets across multiple wireless hops
- Automatically discovers mesh peers
- Handles node mobility and changing topology
- Provides near-instant connectivity (no store-and-forward delay)

## Requirements

### Hardware Requirements

**Wireless Interface:**
- Must support ad-hoc (IBSS) mode
- Most WiFi chips support this
- Check with: `iw list | grep "Supported interface modes"`

**Computing Power:**
- Minimal CPU overhead (kernel-level routing)
- Any Raspberry Pi or Android phone works
- More RAM helpful for large meshes (100+ nodes)

### Software Requirements

**Linux Kernel:**
- Kernel 3.2+ (batman-adv mainlined in 3.2)
- batman-adv module (CONFIG_BATMAN_ADV=m or =y)
- Check with: `modprobe batman_adv && lsmod | grep batman`

**Userspace Tools:**
- batctl (batman control utility)
- Install: `apt-get install batctl` (Debian/Ubuntu)

**Network Tools:**
- iproute2 (ip command)
- wireless-tools or iw (WiFi management)

### Android-Specific Requirements

**Root Access Required:**
- LineageOS (recommended) OR
- Rooted stock Android
- Custom kernel with batman-adv support

**Why Root is Needed:**
- Load kernel modules (`modprobe`)
- Create virtual interfaces
- Set ad-hoc mode
- Configure routing

**Kernel Modules:**
- Most stock Android kernels don't include batman-adv
- LineageOS often includes it
- May need custom kernel compilation

## Supported Devices

### Confirmed Working

**Raspberry Pi:**
- All models (Pi 3, 4, Zero W)
- Raspberry Pi OS includes batman-adv
- Built-in WiFi or USB adapter

**Android (LineageOS):**
- Pixel 3/4/5 (if LineageOS available)
- OnePlus devices (kernel often has batman-adv)
- Check LineageOS device list

### Not Supported

**Stock Android:**
- Unrooted phones (can't load modules)
- Locked bootloader (can't root)
- Proprietary kernels without batman-adv

**iOS:**
- No kernel access
- No module loading
- Use Mode C only

### How to Check Your Device

```bash
# On device (requires root)
su
lsmod | grep batman_adv

# If not loaded, try loading
modprobe batman_adv

# Check if loaded
lsmod | grep batman_adv

# If successful, batman-adv is available
```

## Setup Process

### 1. Load Kernel Module

```bash
# Load batman-adv
sudo modprobe batman_adv

# Make it persistent (add to /etc/modules)
echo "batman_adv" | sudo tee -a /etc/modules
```

### 2. Configure Wireless Interface

```bash
# Set interface to ad-hoc mode
sudo ip link set wlan0 down
sudo iw dev wlan0 set type ibss
sudo iw dev wlan0 ibss join solarpunk-mesh-adhoc 2437

# Or with iwconfig
sudo iwconfig wlan0 mode ad-hoc
sudo iwconfig wlan0 essid solarpunk-mesh-adhoc
sudo iwconfig wlan0 channel 6

sudo ip link set wlan0 up
```

### 3. Add Interface to BATMAN

```bash
# Add wireless interface to batman mesh
sudo batctl meshif bat0 interface add wlan0

# Enable batman features
sudo batctl meshif bat0 aggregation 1
sudo batctl meshif bat0 bridge_loop_avoidance 1
sudo batctl meshif bat0 distributed_arp_table 1

# Bring up batman interface
sudo ip link set bat0 up
```

### 4. Assign IP Address

```bash
# Assign address from mesh range
sudo ip addr add 10.44.0.42/16 dev bat0
```

### 5. Verify Mesh

```bash
# Check neighbors (direct WiFi peers)
batctl meshif bat0 neighbors

# Check originators (all mesh nodes, including multi-hop)
batctl meshif bat0 originators

# Check routing table
batctl meshif bat0 routing_table
```

### Automated Setup

Use the provided script:

```bash
sudo ./mesh_network/mode_a/scripts/setup_batman_adv.sh wlan0 10.44.0.42
```

## Network Topology

### Ad-Hoc Mode

All mesh nodes join the same ad-hoc network:
- ESSID: `solarpunk-mesh-adhoc`
- Channel: 6 (or chosen non-interfering channel)
- No encryption (batman-adv handles routing, not security)

### Mesh Formation

```
┌──────────────────────────────────────────┐
│         BATMAN-adv Mesh Network          │
│            (10.44.0.0/16)                │
├──────────────────────────────────────────┤
│                                          │
│  Node A (10.44.0.10) ←→ Node B (10.44.0.11)
│       ↕                      ↕           │
│  Node C (10.44.0.12) ←→ Node D (10.44.0.13)
│                                          │
│  All nodes can reach each other          │
│  Multi-hop routing automatic             │
└──────────────────────────────────────────┘
```

### Routing Example

```
Garden AP (10.44.0.10)
    ↓ (WiFi)
Bridge Node (10.44.0.42)
    ↓ (WiFi)
Kitchen AP (10.44.0.11)

# From Garden, can reach Kitchen via bridge
ping 10.44.0.11  # Routes through 10.44.0.42
```

## Integration with DTN

### DTN Over Mesh

```python
# DTN node uses bat0 interface for sync
# No changes needed - DTN uses IP routing

# Sync with remote island
sync_url = f"http://10.44.2.1:8000/sync/pull"
# If bat0 routing available, this works instantly
# If not, falls back to Mode C (store-and-forward)
```

### Fallback Detection

Mode detector checks:
1. Is batman-adv loaded?
2. Is bat0 interface up?
3. Can we see mesh peers?

If any fail → fallback to Mode C

```python
# Mode detector handles this automatically
from mesh_network.bridge_node import ModeDetector

detector = ModeDetector()
await detector.start()

# Callbacks notify when mode changes
detector.on_mode_a_available = lambda: print("Mode A available!")
detector.on_mode_a_unavailable = lambda: print("Fell back to Mode C")
```

## Performance Characteristics

### Latency

**Mode A (BATMAN):**
- Near-instant sync (<1 second)
- Direct routing when in range
- Multi-hop when needed (add ~50ms per hop)

**Mode C (DTN):**
- Delayed sync (depends on bridge node movement)
- Typical: 1-10 minutes
- Worst case: Hours (if bridge nodes don't visit)

### Throughput

**Mode A:**
- Full WiFi bandwidth (20-50 Mbps typical)
- Decreases with hop count
- Good for file transfers

**Mode C:**
- Limited by sync windows
- Good for small bundles
- Files chunk and reassemble

### Battery Impact

**Mode A:**
- Higher power (constant WiFi scanning)
- Ad-hoc mode keeps radio active
- Expect 20-40% faster battery drain

**Mode C:**
- Lower power (connect, sync, disconnect)
- Normal WiFi power usage
- Better for all-day bridge walks

## Limitations

### Coverage

- Limited by WiFi range (~50m per hop)
- Buildings block signal
- Needs line-of-sight for outdoor coverage
- May not span large communes without many nodes

### Reliability

- Mesh can fragment (nodes out of range)
- Mobile nodes cause topology changes
- Can be unpredictable in practice
- **This is why Mode C fallback is critical**

### Complexity

- Requires root access (Android)
- Kernel modules (not always available)
- Ad-hoc mode configuration
- More troubleshooting needed

### Security

- Ad-hoc network is open
- Anyone can join mesh
- No encryption at WiFi layer
- Security must be at application layer

## Troubleshooting

### Module Won't Load

```bash
# Check if module exists
modinfo batman_adv

# If not found, kernel doesn't have it
# Options:
# 1. Install kernel with batman-adv
# 2. Compile custom kernel
# 3. Use Mode C only
```

### No Neighbors Visible

```bash
# Check ad-hoc mode set
iw dev wlan0 info | grep type
# Should say "IBSS" or similar

# Check ESSID matches
iw dev wlan0 info | grep ssid

# Check channel matches
iw dev wlan0 info | grep channel

# Verify other nodes are running
```

### bat0 Interface Not Created

```bash
# Check if interface added
batctl meshif bat0 interface

# If empty, add it
batctl meshif bat0 interface add wlan0

# Bring up interface
ip link set bat0 up
```

### Routing Not Working

```bash
# Check originators
batctl meshif bat0 originators
# Should see other mesh nodes

# Check routing table
batctl meshif bat0 routing_table

# Test connectivity
ping <other_node_ip>

# Check logs
dmesg | grep batman
```

## Mode A vs Mode C Decision Tree

```
Can you root device?
├─ No → Use Mode C
└─ Yes
    └─ Does kernel have batman-adv?
        ├─ No → Use Mode C (or compile custom kernel)
        └─ Yes
            └─ Are enough devices available?
                ├─ No → Use Mode C (mesh won't cover area)
                └─ Yes → Try Mode A, keep Mode C as fallback
```

## When to Use Mode A

**Good fit when:**
- Many rooted devices available
- LineageOS or custom ROM community
- Technical users comfortable with root
- Compact physical area (<200m across)
- Want instant sync

**Not a good fit when:**
- Stock Android phones only
- Users not comfortable with root
- Large physical area (>500m)
- Prefer simplicity over speed
- Mode C propagation is fast enough

## When Mode C is Better

**Use Mode C when:**
- Stock Android devices
- Large physical area
- Intermittent connectivity OK
- Simplicity preferred
- Battery life important
- Less technical users

## Hybrid Approach (Recommended)

**Best practice:**
1. Deploy Mode C first (always works)
2. Verify all apps work in Mode C
3. Add Mode A to subset of devices (advanced users)
4. Use Mode A for speedup when available
5. Rely on Mode C fallback for reliability

This gives:
- Reliability of Mode C (always works)
- Speed of Mode A (when available)
- Graceful degradation (automatic fallback)

## Resources

**BATMAN-adv Documentation:**
- https://www.open-mesh.org/projects/batman-adv/wiki
- Kernel documentation: `Documentation/networking/batman-adv.rst`

**Community Support:**
- open-mesh.org mailing lists
- #batman-adv on IRC

**Device Compatibility:**
- LineageOS device list: https://wiki.lineageos.org/devices/
- XDA Developers forums (check if kernel has batman-adv)

**Testing Tools:**
- `batctl` - batman control utility
- `iperf3` - measure throughput
- `mtr` - multi-hop trace route
- WiFi Analyzer - check channel interference (Android app)
