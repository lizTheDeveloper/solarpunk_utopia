# Multi-AP Mesh Network Deployment Guide

Complete guide for deploying the Solarpunk multi-AP mesh network in a physical commune setting.

## Overview

This mesh network provides resilient, offline-first connectivity across multiple physical areas using:
- **Mode C (DTN-Only)**: Foundation layer, always works (store-and-forward via bridge nodes)
- **Mode A (BATMAN-adv)**: Optimum layer when available (multi-hop routing)

**Critical:** Mode C is mandatory. Mode A is optional. All apps must work in Mode C.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Mesh Network (10.44.0.0/16)              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Garden AP  │  │  Kitchen AP  │  │ Workshop AP  │     │
│  │ 10.44.1.0/24 │  │ 10.44.2.0/24 │  │ 10.44.3.0/24 │     │
│  │ SSID: Garden │  │ SSID: Kitchen│  │ SSID: Workshop│    │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ▲                 ▲                 ▲               │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                  Bridge Nodes                               │
│            (move between islands,                           │
│             carry bundles)                                  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware

**Access Points (4 minimum):**
- Raspberry Pi 4 (recommended) OR
- Old Android phones with AP mode

**Bridge Nodes (2+ recommended):**
- Android phones (users who move between areas)
- LineageOS or rooted Android for Mode A (optional)

**Power:**
- Solar + battery packs for outdoor APs
- Wall power for indoor APs
- Battery banks for portable APs

### Software

**AP Devices:**
- Raspberry Pi OS Lite OR
- Android with Termux

**Bridge Nodes:**
- Android 8.0+
- Solarpunk VF app installed
- (Optional) LineageOS with batman-adv for Mode A

## Deployment Steps

### Phase 1: Deploy Access Points

#### Option A: Raspberry Pi

1. **Prepare SD Card**
   ```bash
   # Download Raspberry Pi OS Lite
   # Flash to SD card with balenaEtcher
   # Boot and SSH in
   ```

2. **Run Deployment Script**
   ```bash
   # Copy config to Pi
   scp mesh_network/ap_configs/garden_ap.json pi@raspberrypi:/tmp/

   # Run deployment script
   sudo ./mesh_network/mode_a/scripts/deploy_ap_raspberry_pi.sh /tmp/garden_ap.json
   ```

3. **Deploy DTN Node**
   ```bash
   # Copy DTN software
   scp -r app/ pi@10.44.1.1:/home/pi/solarpunk_dtn/

   # Install dependencies
   ssh pi@10.44.1.1
   cd /home/pi/solarpunk_dtn
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Run DTN node
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Configure Autostart**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/solarpunk-dtn.service
   ```

   ```ini
   [Unit]
   Description=Solarpunk DTN Node
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/solarpunk_dtn
   ExecStart=/home/pi/solarpunk_dtn/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl enable solarpunk-dtn
   sudo systemctl start solarpunk-dtn
   ```

5. **Verify AP**
   ```bash
   # Check hostapd
   systemctl status hostapd

   # Check dnsmasq
   systemctl status dnsmasq

   # Check DTN node
   curl http://10.44.1.1:8000/health
   ```

6. **Repeat for Each Island**
   - Kitchen: Use `kitchen_ap.json`
   - Workshop: Use `workshop_ap.json`
   - Library: Use `library_ap.json`

#### Option B: Android Phone

See `docs/android_ap_setup.md` for detailed instructions.

### Phase 2: Configure Bridge Nodes

1. **Install Solarpunk App**
   - Install APK on Android phones
   - Or use Termux + Python backend

2. **Enable Bridge Mode**
   ```bash
   # In app settings or config file
   {
     "node_role": "bridge",
     "cache_budget_mb": 4096,
     "aggressive_forwarding": true
   }
   ```

3. **Start Bridge Service**
   - App automatically detects network changes
   - Triggers sync on AP transition
   - Carries bundles between islands

4. **Monitor Bridge Metrics**
   ```bash
   # Access bridge API
   curl http://localhost:8002/bridge/status
   curl http://localhost:8002/bridge/metrics
   ```

### Phase 3: Enable Mode A (Optional)

**Only for devices with:**
- Rooted Android (LineageOS recommended)
- Kernel with batman-adv support
- Advanced users

1. **Check Requirements**
   ```bash
   # On device
   lsmod | grep batman
   # If not found, kernel doesn't support it
   ```

2. **Setup BATMAN-adv**
   ```bash
   # Copy script to device
   adb push mesh_network/mode_a/scripts/setup_batman_adv.sh /sdcard/

   # Run as root
   adb shell
   su
   bash /sdcard/setup_batman_adv.sh wlan0 10.44.0.42
   ```

3. **Verify Mesh**
   ```bash
   batctl meshif bat0 neighbors
   batctl meshif bat0 originators
   ```

4. **Test Routing**
   ```bash
   # From Garden device (10.44.1.42)
   # Ping Kitchen gateway through mesh
   ping 10.44.2.1
   ```

5. **Fallback Testing**
   - System should automatically detect if Mode A fails
   - Falls back to Mode C gracefully
   - Test by disabling batman interface

### Phase 4: Validation

#### Test Mode C (Required)

1. **Disable All Routing**
   ```bash
   # Make sure no Mode A routing
   # Islands should be isolated except via bridge nodes
   ```

2. **Test Store-and-Forward**
   - User A on Garden creates offer
   - Bridge node visits Garden (syncs)
   - Bridge node visits Kitchen (syncs)
   - User B on Kitchen sees offer
   - Measure propagation time (should be <10 min)

3. **Test All Apps**
   - Offers/needs creation
   - Queries and responses
   - File chunking and retrieval
   - Agent proposals
   - All should work in Mode C

#### Test Mode A (If Available)

1. **Test Multi-Hop Routing**
   ```bash
   # From Garden
   ping 10.44.2.1  # Kitchen gateway
   ping 10.44.3.1  # Workshop gateway
   ```

2. **Test DTN Over Mesh**
   ```bash
   # From Garden
   curl http://10.44.2.1:8000/sync/index
   # Should get Kitchen's bundle index
   ```

3. **Test Fallback**
   ```bash
   # Disable batman on one device
   sudo ./teardown_batman_adv.sh

   # System should fall back to Mode C
   # Check logs for fallback detection
   ```

4. **Measure Speedup**
   - Compare bundle propagation time
   - Mode A should be near-instant
   - Mode C should be <10 min via bridge walks

#### Test Bridge Effectiveness

1. **Multiple Bridge Walks**
   - Have bridge nodes visit multiple islands
   - Check metrics at `/bridge/metrics`
   - Effectiveness score should increase

2. **Island Coverage**
   - Bridge nodes should visit all 4 islands
   - Check transport matrix shows all pairs

3. **Bundle Volume**
   - Create 20+ bundles across islands
   - Verify they propagate via bridges

## Network Topology Planning

### Channel Selection

Use non-overlapping 2.4GHz channels:
- Channel 1, 6, 11 are standard
- Avoid overlap to minimize interference

### Physical Placement

**Garden AP:**
- Outdoor rated enclosure
- Solar panel + weather-proof battery
- Mount 2-3m high for coverage
- SSID: SolarpunkGarden

**Kitchen AP:**
- Central location in building
- Wall power preferred
- Near food prep/sharing area
- SSID: SolarpunkKitchen

**Workshop AP:**
- Tool storage area
- Wall power
- Near workbenches
- SSID: SolarpunkWorkshop

**Library AP:**
- Reading/learning space
- Wall power
- Near documentation
- SSID: SolarpunkLibrary

### Coverage Optimization

- Each AP covers ~30-50m radius
- Overlap at edges is OK (different channels)
- Bridge nodes handle inter-island communication
- Test coverage with WiFi analyzer app

## Monitoring and Maintenance

### AP Health Checks

```bash
# On each AP
systemctl status hostapd
systemctl status dnsmasq
curl http://<gateway>:8000/health

# Check logs
journalctl -u hostapd -f
journalctl -u dnsmasq -f
journalctl -u solarpunk-dtn -f
```

### Bridge Node Monitoring

```bash
# Check bridge status
curl http://localhost:8002/bridge/status

# Get metrics
curl http://localhost:8002/bridge/metrics

# Export metrics
curl "http://localhost:8002/bridge/metrics/export?filepath=/sdcard/metrics.json"
```

### Mode Status

```bash
# Check current mode
curl http://localhost:8002/bridge/mode

# Force Mode C (testing)
curl -X POST http://localhost:8002/bridge/mode/control \
  -H "Content-Type: application/json" \
  -d '{"action": "force_mode_c"}'

# Attempt Mode A
curl -X POST http://localhost:8002/bridge/mode/control \
  -H "Content-Type: application/json" \
  -d '{"action": "attempt_mode_a"}'
```

### Log Analysis

**Look for:**
- AP transitions (bridge nodes moving)
- Sync operations (bundles transferred)
- Mode changes (A ↔ C fallback)
- Errors or failures

**Key metrics:**
- Bundle propagation time (<10 min target)
- Sync success rate (>90% target)
- Bridge effectiveness score (>0.5 target)
- Network uptime (>95% target)

## Troubleshooting

### AP Not Broadcasting

```bash
# Check interface
ip addr show wlan0

# Restart hostapd
sudo systemctl restart hostapd

# Check config
sudo cat /etc/hostapd/hostapd.conf

# Check for errors
sudo journalctl -u hostapd -n 50
```

### DHCP Not Assigning IPs

```bash
# Check dnsmasq
sudo systemctl status dnsmasq

# Check leases
cat /var/lib/misc/dnsmasq.leases

# Restart dnsmasq
sudo systemctl restart dnsmasq
```

### Bridge Not Syncing

```bash
# Check network connection
curl http://localhost:8002/bridge/network

# Check sync stats
curl http://localhost:8002/bridge/sync/stats

# Trigger manual sync
curl -X POST http://localhost:8002/bridge/sync/manual

# Check DTN node reachable
curl http://<gateway>:8000/health
```

### Mode A Not Working

```bash
# Check batman module
lsmod | grep batman_adv

# Check interface
ip addr show bat0

# Check neighbors
batctl meshif bat0 neighbors

# Re-run setup
sudo ./setup_batman_adv.sh wlan0
```

### Bundles Not Propagating

1. **Check DTN node running on APs**
   ```bash
   curl http://10.44.1.1:8000/health
   curl http://10.44.2.1:8000/health
   ```

2. **Check bridge nodes visiting islands**
   ```bash
   curl http://localhost:8002/bridge/metrics
   # Look for island_stats showing visits
   ```

3. **Check bundle queues**
   ```bash
   curl http://localhost:8000/bundles/stats
   # Should show bundles in forwarding queue
   ```

4. **Force sync**
   ```bash
   curl -X POST http://localhost:8002/bridge/sync/manual
   ```

## Security Considerations

### Open Network Design

- No WPA/WPA2 (facilitates community access)
- Security at application layer (bundle signatures)
- Audience enforcement controls distribution
- Trust scores limit untrusted peer exposure

### Physical Security

- APs in semi-public community spaces
- Not suitable for sensitive personal data
- Use only for commune coordination
- Consider camera monitoring for expensive APs

### Access Control

- Application-level authentication (VF nodes)
- Bundle signatures prevent tampering
- Trust scores prevent spam/abuse
- Rate limiting on sync endpoints

## Performance Tuning

### AP Optimization

```bash
# hostapd.conf tweaks
wmm_enabled=1              # QoS
ieee80211n=1               # 802.11n
ht_capab=[HT40][SHORT-GI]  # 40MHz channels
```

### Bridge Optimization

```python
# config.json
{
  "cache_budget_mb": 4096,      # Larger cache for more bundles
  "max_bundles_per_sync": 100,  # Batch size
  "sync_timeout": 300           # 5 min timeout
}
```

### DTN Optimization

- Priority-based forwarding (emergency first)
- Aggressive TTL enforcement (drop expired)
- Cache eviction (oldest first)

## Scaling

### Adding Islands

1. Create new AP config (next subnet: 10.44.X.0/24)
2. Deploy AP with script
3. Bridge nodes automatically discover new island
4. Update channel plan to avoid interference

### Adding Bridge Nodes

1. Install app on more phones
2. Enable bridge role
3. More bridges = faster propagation
4. Monitor overlap to avoid redundancy

### Load Balancing

- Multiple APs per island (same SSID, different channels)
- Client roaming between APs
- DTN nodes sync with each other
- Round-robin sync for multiple DTN nodes

## Backup and Recovery

### AP Configuration Backup

```bash
# Backup configs
cp /etc/hostapd/hostapd.conf /backup/
cp /etc/dnsmasq.conf /backup/

# Backup DTN data
tar -czf /backup/dtn_data.tar.gz /home/pi/solarpunk_dtn/data/
```

### Bridge Metrics Export

```bash
# Export metrics regularly
curl "http://localhost:8002/bridge/metrics/export?filepath=/backup/metrics_$(date +%Y%m%d).json"
```

### Disaster Recovery

1. Keep spare Raspberry Pis with OS flashed
2. Store AP configs in git repo
3. Document network topology
4. Train multiple people on deployment

## Next Steps

After successful deployment:

1. **Monitor for 1 week** - Verify stability
2. **Gather metrics** - Bundle propagation times, coverage
3. **User feedback** - Are apps working? Coverage gaps?
4. **Iterate** - Adjust AP placement, add bridges
5. **Document** - Record your specific setup
6. **Scale** - Add more islands as commune grows

## Support

- Check logs first (journalctl, app logs)
- Review this guide's troubleshooting section
- Test Mode C baseline (simplest config)
- Isolate problem (AP vs bridge vs DTN vs app)
- Document issue for community knowledge base
