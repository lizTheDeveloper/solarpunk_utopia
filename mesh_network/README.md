# Multi-AP Mesh Network (TIER 1)

Production-ready software components for Solarpunk commune mesh networking. Enables resilient, offline-first connectivity across multiple physical areas using store-and-forward DTN with optional multi-hop routing.

## Overview

This system implements a **layered mesh architecture**:

- **Mode C (DTN-Only)**: Foundation layer - always works, store-and-forward via bridge nodes
- **Mode A (BATMAN-adv)**: Optimum layer - multi-hop routing when hardware supports it
- **Mode B (Wi-Fi Direct)**: Future research - alternative for non-rooted devices

**Critical Design Principle:** All apps MUST work in Mode C. Mode A/B are optimizations.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Multi-AP Island Architecture                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Island 1 (Garden)      Island 2 (Kitchen)              │
│  ┌─────────────┐        ┌─────────────┐                │
│  │ AP: 10.44.1.1│        │ AP: 10.44.2.1│               │
│  │ DTN Node    │        │ DTN Node    │                │
│  │ 5-8 clients │        │ 10-15 clients│               │
│  └─────────────┘        └─────────────┘                │
│         ▲                      ▲                         │
│         │    Bridge Node       │                         │
│         │  ┌──────────────┐   │                         │
│         └──│  Carries      │───┘                         │
│            │  bundles      │                             │
│            │  10.44.0.42   │                             │
│            └──────────────┘                              │
│                                                          │
│  Mode C: Bridge walks between islands (store-forward)   │
│  Mode A: Direct routing over bat0 (when available)      │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. AP Configuration Templates

JSON templates for deploying Access Point islands:

- `ap_configs/garden_ap.json` - Outdoor garden area (10.44.1.0/24)
- `ap_configs/kitchen_ap.json` - Kitchen/dining (10.44.2.0/24)
- `ap_configs/workshop_ap.json` - Workshop/tools (10.44.3.0/24)
- `ap_configs/library_ap.json` - Library/knowledge (10.44.4.0/24)

Each template includes:
- Network configuration (SSID, subnet, DHCP)
- hostapd settings (channel, mode, capabilities)
- Service endpoints (DTN node, VF node)
- Deployment metadata (hardware, power, coverage)

### 2. Bridge Node Services

Python services for bridge node functionality:

**NetworkMonitor** (`bridge_node/services/network_monitor.py`):
- Detects WiFi network changes
- Identifies island transitions (SSID changes)
- Triggers callbacks on AP connection/disconnection

**SyncOrchestrator** (`bridge_node/services/sync_orchestrator.py`):
- Coordinates DTN bundle synchronization
- Pulls bundles from new island on arrival
- Pushes carried bundles to island
- Tracks sync performance and errors

**BridgeMetrics** (`bridge_node/services/bridge_metrics.py`):
- Tracks bridge effectiveness
- Records island visits and bundle transfers
- Calculates effectiveness score
- Exports metrics for analysis

**ModeDetector** (`bridge_node/services/mode_detector.py`):
- Detects Mode A (BATMAN-adv) availability
- Monitors mesh health (peers, routing)
- Triggers fallback to Mode C when needed
- Attempts recovery when Mode A becomes available

### 3. Bridge Management API

FastAPI endpoints (`bridge_node/api/bridge_api.py`):

```
GET  /bridge/status      - Overall bridge status
GET  /bridge/network     - Current network connection
GET  /bridge/metrics     - Comprehensive metrics
GET  /bridge/sync/stats  - Sync performance
GET  /bridge/mode        - Current mesh mode
POST /bridge/sync/manual - Trigger manual sync
POST /bridge/mode/control - Force mode change
GET  /bridge/health      - Service health check
```

### 4. Mode A Setup Scripts

Bash scripts for BATMAN-adv deployment:

- `mode_a/scripts/setup_batman_adv.sh` - Configure BATMAN-adv mesh
- `mode_a/scripts/teardown_batman_adv.sh` - Remove mesh configuration
- `mode_a/scripts/deploy_ap_raspberry_pi.sh` - Deploy AP on Raspberry Pi

### 5. Documentation

- `docs/deployment_guide.md` - Complete deployment guide
- `docs/mode_a_requirements.md` - Mode A requirements and setup
- `ap_configs/README.md` - AP configuration reference

### 6. Tests

Comprehensive test suite (`bridge_node/tests/`):

- `test_network_monitor.py` - Network detection tests
- `test_sync_orchestrator.py` - Sync coordination tests
- `test_mode_detector.py` - Mode detection and fallback tests
- `test_bridge_metrics.py` - Metrics tracking tests

## Quick Start

### Deploy an AP (Raspberry Pi)

```bash
# 1. Copy config to Pi
scp ap_configs/garden_ap.json pi@raspberrypi:/tmp/

# 2. Run deployment script
ssh pi@raspberrypi
sudo ./deploy_ap_raspberry_pi.sh /tmp/garden_ap.json

# 3. Deploy DTN node software
# (Copy and run DTN app as shown in deployment guide)
```

### Run Bridge Node

```bash
# Install dependencies
pip install -r requirements.txt

# Run bridge node service
cd bridge_node
python main.py

# Access API
curl http://localhost:8002/bridge/status
```

### Setup Mode A (Optional)

```bash
# On rooted Android or Linux with batman-adv
sudo ./mode_a/scripts/setup_batman_adv.sh wlan0 10.44.0.42

# Verify mesh
batctl meshif bat0 neighbors
```

## Integration with DTN

Bridge node integrates with existing DTN Bundle System (`/app/api/sync.py`):

**Sync Endpoints Used:**
- `GET /sync/pull` - Pull bundles for forwarding
- `POST /sync/push` - Push received bundles
- `GET /sync/index` - Get bundle index for negotiation

**Integration Points:**
```python
# Bridge node triggers sync on AP transition
old_network = NetworkInfo(ssid="SolarpunkGarden", ...)
new_network = NetworkInfo(ssid="SolarpunkKitchen", ...)

# Orchestrator coordinates sync
sync_op = await sync_orchestrator.sync_on_ap_transition(
    old_network,
    new_network
)

# Metrics track effectiveness
bridge_metrics.record_sync(
    island_id="kitchen",
    bundles_received=sync_op.bundles_received,
    bundles_sent=sync_op.bundles_sent,
    from_island="garden"
)
```

## Configuration

### Bridge Node Config

```python
# In bridge_node/main.py
await initialize_services(
    node_id="bridge_node_1",        # Unique bridge ID
    dtn_base_url="http://localhost:8000"  # Local DTN node
)
```

### Network Monitor

```python
from mesh_network.bridge_node import NetworkMonitor

monitor = NetworkMonitor(poll_interval=5.0)  # Check every 5s

async def on_transition(old_net, new_net):
    print(f"Moved from {old_net.island_id} to {new_net.island_id}")

monitor.on_ap_transition = on_transition
await monitor.start()
```

### Sync Orchestrator

```python
from mesh_network.bridge_node import SyncOrchestrator

orchestrator = SyncOrchestrator(
    dtn_base_url="http://localhost:8000",
    sync_timeout=300,           # 5 min timeout
    max_bundles_per_sync=100    # Batch size
)
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest bridge_node/tests/ -v

# Run specific test file
pytest bridge_node/tests/test_network_monitor.py -v

# Run with coverage
pytest bridge_node/tests/ --cov=bridge_node --cov-report=html
```

## Deployment Checklist

- [ ] 3+ AP islands deployed (Garden, Kitchen, Workshop minimum)
- [ ] Each AP has DTN node running (port 8000)
- [ ] Bridge nodes configured (2+ recommended)
- [ ] Mode C tested and working (all apps functional)
- [ ] Bundle propagation measured (<10 min between islands)
- [ ] Mode A setup tested (if devices support it)
- [ ] Fallback behavior verified (Mode A → Mode C)
- [ ] Metrics collected and reviewed
- [ ] Network handles 20+ concurrent users

## Performance Targets

**Mode C (DTN-Only):**
- Bundle propagation: <10 minutes between islands
- Bridge effectiveness score: >0.5
- Sync success rate: >90%

**Mode A (BATMAN-adv):**
- Multi-hop latency: <100ms per hop
- Throughput: >10 Mbps (single hop)
- Fallback time: <30 seconds when mesh fails

**Overall:**
- Network uptime: >95%
- AP coverage: 30-50m radius per AP
- Battery life (bridge nodes): 8+ hours active use

## Technology Stack

- **Python 3.12** - Bridge node services and API
- **FastAPI** - REST API framework
- **asyncio** - Async network monitoring and sync
- **httpx** - HTTP client for DTN sync
- **pytest** - Testing framework
- **hostapd** - AP daemon (Raspberry Pi)
- **dnsmasq** - DHCP server
- **BATMAN-adv** - Mesh routing (Mode A)
- **batctl** - BATMAN control utility

## Directory Structure

```
mesh_network/
├── ap_configs/              # AP configuration templates
│   ├── garden_ap.json
│   ├── kitchen_ap.json
│   ├── workshop_ap.json
│   ├── library_ap.json
│   └── README.md
├── bridge_node/             # Bridge node software
│   ├── services/            # Core services
│   │   ├── network_monitor.py
│   │   ├── sync_orchestrator.py
│   │   ├── bridge_metrics.py
│   │   └── mode_detector.py
│   ├── api/                 # FastAPI endpoints
│   │   └── bridge_api.py
│   ├── tests/               # Test suite
│   │   ├── test_network_monitor.py
│   │   ├── test_sync_orchestrator.py
│   │   ├── test_mode_detector.py
│   │   └── test_bridge_metrics.py
│   └── main.py              # Application entry point
├── mode_a/                  # Mode A (BATMAN-adv)
│   └── scripts/
│       ├── setup_batman_adv.sh
│       ├── teardown_batman_adv.sh
│       └── deploy_ap_raspberry_pi.sh
├── docs/                    # Documentation
│   ├── deployment_guide.md
│   └── mode_a_requirements.md
└── README.md               # This file
```

## API Examples

### Get Bridge Status

```bash
curl http://localhost:8002/bridge/status
```

Response:
```json
{
  "is_active": true,
  "current_island": "kitchen",
  "current_mode": "mode_c",
  "network_connected": true,
  "sync_in_progress": false,
  "effectiveness_score": 0.72
}
```

### Get Bridge Metrics

```bash
curl http://localhost:8002/bridge/metrics
```

Response:
```json
{
  "node_id": "bridge_node_1",
  "uptime_hours": 4.2,
  "effectiveness_score": 0.72,
  "totals": {
    "syncs": 15,
    "bundles_received": 73,
    "bundles_sent": 68,
    "islands_visited": 4,
    "island_pairs": 6
  },
  "current_island": "kitchen",
  "island_stats": {
    "garden": {"visits": 4, "bundles_received": 20},
    "kitchen": {"visits": 5, "bundles_received": 25}
  },
  "transport_matrix": {
    "garden": {"kitchen": 18, "workshop": 12},
    "kitchen": {"garden": 15, "library": 10}
  }
}
```

### Trigger Manual Sync

```bash
curl -X POST http://localhost:8002/bridge/sync/manual
```

### Check Mode Status

```bash
curl http://localhost:8002/bridge/mode
```

Response:
```json
{
  "current_mode": "mode_c",
  "mode_c_available": true,
  "mode_a_available": false,
  "mode_a_failures": 3,
  "last_check": {
    "mode": "mode_a",
    "available": false,
    "details": "batman-adv module not loaded"
  }
}
```

## Troubleshooting

### Bridge Not Detecting Network Changes

```bash
# Check network monitor service
curl http://localhost:8002/bridge/health

# Check current network
curl http://localhost:8002/bridge/network

# Restart bridge service
# (Stop and start main.py)
```

### Bundles Not Syncing

```bash
# Check sync stats
curl http://localhost:8002/bridge/sync/stats

# Trigger manual sync
curl -X POST http://localhost:8002/bridge/sync/manual

# Check DTN node accessible
curl http://<gateway>:8000/health
```

### Mode A Not Available

```bash
# Check mode status
curl http://localhost:8002/bridge/mode

# Try to enable Mode A
curl -X POST http://localhost:8002/bridge/mode/control \
  -H "Content-Type: application/json" \
  -d '{"action": "attempt_mode_a"}'

# Check kernel module
lsmod | grep batman_adv
```

See `docs/deployment_guide.md` for comprehensive troubleshooting.

## Contributing

When adding features:

1. **Maintain Mode C compatibility** - Never break DTN-only operation
2. **Add tests** - All new services need test coverage
3. **Update documentation** - Keep deployment guide current
4. **Consider battery impact** - Bridge nodes run on battery
5. **Handle errors gracefully** - Network failures are expected

## License

Part of the Solarpunk VF system. Built for resilient commune coordination.

## See Also

- `/app/` - DTN Bundle System (core messaging)
- `/app/api/sync.py` - DTN sync endpoints
- `openspec/changes/multi-ap-mesh-network/` - Original proposal
- Section 3 of `solarpunk_node_full_spec.md` - Network architecture spec
- Section 8 of `solarpunk_node_full_spec.md` - Phones as routers spec
