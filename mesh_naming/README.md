# Multiverse Mesh Naming - `.multiversemesh` namespace

Human-readable names for the solarpunk mesh network. No more IP addresses!

## Quick Start

### Claim Your Name

```bash
# Claim a name
./mesh_cli.py claim alice

# With community
./mesh_cli.py claim alice --community food-coop

# Check your identity
./mesh_cli.py whoami
```

Output:
```
🌐 Your Multiverse Mesh Identity
==================================================
Mesh Name:    alice.multiversemesh
Node Name:    alice

Services:
  DTN:        dtn://alice.multiversemesh/
  Offers:     dtn://alice.multiversemesh/offers
  Needs:      dtn://alice.multiversemesh/needs
  AI:         dtn://alice.multiversemesh/ai/inference
```

### Discover Other Nodes

```bash
./mesh_cli.py discover
```

Output:
```
🔍 Discovering .multiversemesh nodes...

Found 3 node(s):

📍 bob.multiversemesh
   IP:         192.168.1.10
   Node:       bob
   DTN:        http://192.168.1.10:8000
   ValueFlows: http://192.168.1.10:8001
   AI:         http://192.168.1.10:8005

📍 food-coop.community.multiversemesh
   IP:         192.168.1.15
   Node:       food-coop
   Community:  community
   DTN:        http://192.168.1.15:8000
   ...
```

### Look Up a Name

```bash
./mesh_cli.py lookup bob
```

### Resolve DTN URIs

```bash
./mesh_cli.py resolve dtn://bob.multiversemesh/offers
```

Output:
```
✅ Resolved:
   http://192.168.1.10:8001/vf/offers
```

## How It Works

### mDNS Service Discovery

Uses Zeroconf/Avahi to broadcast your mesh identity on the local network:

- **Service Type**: `_multiversemesh._tcp.local.`
- **Properties**: mesh_name, node_name, ports, community
- **Auto-discovery**: Finds other nodes broadcasting the same service

### Name Format

```
{node}.multiversemesh                    # Individual node
{node}.{community}.multiversemesh        # Community member
```

Examples:
- `alice.multiversemesh`
- `bob.food-coop.multiversemesh`
- `bridge-01.multiversemesh`

### DTN URI Scheme

Maps human names to service endpoints:

```
dtn://alice.multiversemesh/offers
  → http://192.168.1.10:8001/vf/offers

dtn://bob.multiversemesh/ai/inference
  → http://192.168.1.20:8005/inference

dtn://food-coop.community.multiversemesh/needs
  → http://192.168.1.15:8001/vf/needs
```

## Integration

### Start Announcing (Standalone)

```bash
./mesh_cli.py announce
```

This broadcasts your services on the network so others can discover you.

### Programmatic Use

```python
from mesh_dns import get_mesh_naming

# Get mesh naming service
mesh = get_mesh_naming()

# Your mesh name
print(mesh.mesh_fqdn)  # "alice.multiversemesh"

# Announce services
mesh.announce(
    dtn_port=8000,
    valueflows_port=8001,
    ai_port=8005,
)

# Discover nodes
nodes = mesh.discover()

# Look up a name
node = mesh.resolve("bob.multiversemesh")
if node:
    print(f"Bob is at {node['ip']}")

# Resolve DTN URI
url = mesh.resolve_dtn_uri("dtn://bob.multiversemesh/offers")
# url = "http://192.168.1.10:8001/vf/offers"
```

### Auto-Announce with Services

The main service launcher will automatically announce if configured:

```bash
# Set your mesh name
export MESH_NAME=alice
export COMMUNITY_NAME=food-coop  # Optional

# Start services (auto-announces)
./run_all_services.sh
```

## Configuration

### Environment Variables

```bash
# Your mesh identity
export MESH_NAME="alice"
export COMMUNITY_NAME="food-coop"  # Optional
```

### Config File

`~/.config/multiversemesh/identity`:
```bash
MESH_NAME=alice
COMMUNITY_NAME=food-coop
```

## Requirements

```bash
pip install zeroconf structlog
```

### Platform Support

- **Linux**: Works with Avahi (usually pre-installed)
- **macOS**: Works with Bonjour (built-in)
- **Android/Termux**: Install `pkg install avahi-daemon`
- **Windows**: Works with Bonjour service

## Troubleshooting

### No nodes discovered

1. **Check mDNS/Avahi is running:**
   ```bash
   # Linux
   sudo systemctl status avahi-daemon

   # Start if needed
   sudo systemctl start avahi-daemon
   ```

2. **Check firewall allows mDNS (port 5353 UDP):**
   ```bash
   sudo ufw allow 5353/udp
   ```

3. **Check you're on the same network:**
   mDNS only works on local networks, not across routers.

### Name conflicts

If two nodes claim the same name, mDNS will append a number:
- First: `alice.multiversemesh`
- Second: `alice-2.multiversemesh`

Choose unique names to avoid conflicts!

### zeroconf not installed

```bash
pip install zeroconf
```

## Use Cases

### 1. Human-Friendly Offers

Instead of:
```
Check offers at http://192.168.1.10:8001/vf/offers
```

Now:
```
Check offers at dtn://alice.multiversemesh/offers
```

### 2. Community Directories

```bash
# Find all food-coop members
./mesh_cli.py discover | grep food-coop
```

### 3. Automatic Peering

Services can auto-discover and connect to peers:
```python
nodes = mesh.discover()
for node in nodes:
    if node.get('community') == 'food-coop':
        # Connect to community peer
        sync_with_peer(node['ip'], node['ports']['dtn'])
```

### 4. DTN Routing

```python
# Send bundle to alice
send_bundle(
    destination="dtn://alice.multiversemesh/inbox",
    payload=my_data
)
```

The DTN system resolves the name and routes accordingly!

## Security Notes

- **Local network only**: mDNS doesn't cross routers (by design)
- **No authentication**: Names are not verified (trust your LAN)
- **For mesh use**: Deploy across mesh with custom DNS later
- **Names are public**: Anyone on your network can see them

For internet-scale federation, use DNS + DNSSEC later.

## Philosophy

**Names over numbers.** Humans shouldn't have to remember IP addresses.

The `.multiversemesh` namespace makes the mesh feel like a community, not a computer network. You know **who** you're connecting to, not just **what IP**.

It's the difference between:
- "Connect to 192.168.1.10" ❌
- "Connect to alice.multiversemesh" ✅

Much more human. 🌱
