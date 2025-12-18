# DTN Bundle System - Solarpunk Mesh Network Backend

Complete DTN (Delay-Tolerant Networking) bundle transport layer for the Solarpunk mesh network.

## Overview

This is the foundational **TIER 0** transport layer for the Solarpunk commune network. All payloads (offers, needs, files, indexes, queries) move as signed bundles with TTL, priority, audience controls, and hop limits.

## Features

### 1. Bundle Data Model
- Content-addressed bundleId (sha256)
- Priority levels: emergency, perishable, normal, low
- Audience controls: public, local, trusted, private
- TTL with automatic expiration
- Ed25519 signing for authenticity
- Hop limit tracking to prevent loops

### 2. Queue Management (SQLite)
6 queues for bundle lifecycle:
- **inbox**: received bundles awaiting processing
- **outbox**: locally-created bundles awaiting forwarding
- **pending**: bundles awaiting opportunistic forwarding
- **delivered**: acknowledged deliveries
- **expired**: bundles dropped due to TTL expiration
- **quarantine**: bundles with invalid signatures or policy violations

### 3. TTL Enforcement
- Background service runs every 60 seconds
- Automatically moves expired bundles to expired queue
- TTL defaults by content type (emergency: 12h, knowledge: 270d, etc.)

### 4. Cache Budget Manager
- Storage budget enforcement (default: 2GB)
- Eviction policy: expired → low priority → oldest
- Prevents accepting bundles when over budget

### 5. Forwarding Engine
- Priority-based forwarding (emergency first)
- Audience enforcement (public, local, trusted, private)
- Hop limit tracking
- Trust score checking for trusted bundles

### 6. Signing and Verification
- Ed25519 keypair generation and storage
- All bundles cryptographically signed
- Signature verification on receipt
- Invalid signatures → quarantine

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main
```

The API will be available at http://localhost:8000

## Quick Start

### 1. Start the server

```bash
python -m app.main
```

### 2. Create a bundle

```bash
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"type": "offer", "content": "Fresh tomatoes available"},
    "payloadType": "vf:Listing",
    "priority": "perishable",
    "audience": "public",
    "topic": "mutual-aid",
    "tags": ["food", "perishable"]
  }'
```

### 3. List bundles

```bash
curl http://localhost:8000/bundles?queue=outbox
```

### 4. Get sync index

```bash
curl http://localhost:8000/sync/index?queue=pending
```

### 5. Check health

```bash
curl http://localhost:8000/health
```

## API Documentation

Once the server is running, visit:
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Bundle Management

- **POST /bundles** - Create new bundle
  - Automatically signs bundle with node's private key
  - Calculates content-addressed bundleId
  - Stores in outbox queue

- **GET /bundles** - List bundles in queue
  - Query params: `queue`, `limit`, `offset`
  - Returns bundles ordered by priority

- **GET /bundles/{bundle_id}** - Get specific bundle

- **POST /bundles/receive** - Receive bundle from peer
  - Validates signature
  - Checks TTL and hop limit
  - Valid → inbox, invalid → quarantine

- **POST /bundles/{bundle_id}/forward** - Check if bundle can be forwarded
  - Enforces audience restrictions
  - Checks trust score

- **POST /bundles/{bundle_id}/to-pending** - Move to pending queue

- **POST /bundles/{bundle_id}/mark-delivered** - Mark as delivered

- **GET /bundles/stats/queues** - Get queue statistics

- **GET /bundles/stats/forwarding** - Get forwarding statistics

### Sync Protocol

- **GET /sync/index** - Get lightweight bundle index
  - Returns bundleId, priority, timestamps, size
  - Used for sync negotiation

- **POST /sync/request** - Request specific bundles by ID
  - Enforces audience restrictions
  - Returns only bundles peer can receive

- **POST /sync/push** - Receive multiple bundles from peer
  - Batch version of receive
  - Checks cache budget

- **GET /sync/pull** - Pull bundles ready for forwarding
  - Returns bundles ordered by priority
  - Filtered by audience enforcement

- **GET /sync/stats** - Get comprehensive sync statistics

### Node Info

- **GET /** - Root endpoint with system info

- **GET /health** - Health check
  - Cache usage
  - Service status

- **GET /node/info** - Node information
  - Public key
  - Node fingerprint

## Architecture

```
app/
├── models/
│   ├── bundle.py          # Bundle data model with TTL calculation
│   ├── priority.py        # Priority, Audience, Topic enums
│   └── queue.py           # Queue names enum
├── database/
│   ├── db.py              # SQLite database initialization
│   └── queues.py          # Queue management operations
├── services/
│   ├── crypto_service.py  # Ed25519 signing and verification
│   ├── bundle_service.py  # Bundle creation and validation
│   ├── ttl_service.py     # Background TTL enforcement
│   ├── cache_service.py   # Cache budget management
│   └── forwarding_service.py  # Priority-based forwarding
├── api/
│   ├── bundles.py         # Bundle endpoints
│   └── sync.py            # Sync protocol endpoints
└── main.py                # FastAPI app with background services
```

## Data Storage

All data is stored in SQLite at `data/dtn_bundles.db`:
- Bundles table with indexes for efficient queries
- Metadata table for cache tracking

Ed25519 keypair stored at:
- `data/keys/node_private.pem` (owner-only permissions)
- `data/keys/node_public.pem`

## TTL Defaults

From the spec (Section 4.3):

| Content Type | TTL |
|--------------|-----|
| Emergency | 12 hours |
| Perishable food | 48 hours |
| Time-sensitive needs | 48 hours |
| Tool lending | 30 days |
| Skill offers | 60 days |
| Coordination | 7 days |
| Inventory | 30 days |
| Knowledge/protocols | 270 days |
| Indexes | 3 days |

## Forwarding Priority Order

1. **emergency** - never defer, always forward immediately
2. **perishable** - time-sensitive coordination
3. **normal** (trusted/private) - authenticated content
4. **normal** (public/local) - general content
5. **low** - background/bulk content

## Audience Enforcement

- **public**: Anyone may carry (no restrictions)
- **local**: Only within community boundary (peer_is_local=true)
- **trusted**: Only nodes with trust score ≥ 0.7
- **private**: Encrypted direct delivery (not yet implemented)

## Cache Budget

Default: 2GB storage budget

Eviction policy when over 95% capacity:
1. Delete expired bundles first
2. Delete low-priority bundles
3. Delete oldest normal-priority bundles
4. Preserve outbox (locally created) bundles

## Background Services

### TTL Enforcement Service
- Runs every 60 seconds
- Finds expired bundles across all queues
- Moves them to expired queue
- Logs count of moved bundles

### Cache Budget Manager
- Runs on-demand when accepting new bundles
- Enforces storage limits
- Evicts bundles following priority policy

## Testing

### Manual Testing

```bash
# 1. Create a bundle
curl -X POST http://localhost:8000/bundles \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"message": "Emergency: Fire in garden"},
    "payloadType": "alert:Emergency",
    "priority": "emergency",
    "audience": "public",
    "topic": "coordination",
    "tags": ["emergency", "fire"]
  }'

# 2. List bundles
curl http://localhost:8000/bundles?queue=outbox

# 3. Move to pending
curl -X POST http://localhost:8000/bundles/{bundle_id}/to-pending

# 4. Check forwarding stats
curl http://localhost:8000/bundles/stats/forwarding

# 5. Simulate receiving bundle from peer
# (Use bundle JSON from step 1)
curl -X POST http://localhost:8000/bundles/receive \
  -H "Content-Type: application/json" \
  -d '{...bundle json...}'

# 6. Check health
curl http://localhost:8000/health
```

### Test Script

A test script `test_dtn_system.py` is provided for automated testing.

## Success Criteria

From the proposal:

- [x] Bundle format fully specified and documented
- [x] All 6 queues implemented and functional
- [x] TTL defaults applied correctly per content type
- [x] Cache budgets enforced (storage)
- [x] Forwarding rules respect priority and audience
- [x] All bundles are signed and verified
- [x] Invalid signatures go to quarantine
- [x] HTTP API functional for sync between nodes

## Next Steps

This backend is ready for:
1. **Android integration** - Connect Android app to this API
2. **Peer discovery** - mDNS/network scanning
3. **Sync protocol** - Implement full sync workflow
4. **ValueFlows layer** - Build on top of bundles
5. **Agent layer** - AI agents for matching/scheduling

## Spec References

- Proposal: `openspec/changes/dtn-bundle-system/proposal.md`
- Tasks: `openspec/changes/dtn-bundle-system/tasks.md`
- Spec: `solarpunk_node_full_spec.md` (Section 4: DTN Bundle Layer)

## License

Part of the Solarpunk commune network project.
