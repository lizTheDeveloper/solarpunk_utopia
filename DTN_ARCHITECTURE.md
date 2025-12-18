# DTN Bundle System - Architecture Diagram

Visual representation of the DTN Bundle System architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DTN Bundle System                             │
│                 (Solarpunk Mesh Network)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                        │
│                    (app/main.py - Port 8000)                     │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ Bundle  │         │  Sync   │         │ System  │
   │   API   │         │   API   │         │   API   │
   └─────────┘         └─────────┘         └─────────┘
```

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ /bundles       │  │ /sync          │  │ /health        │   │
│  │ - Create       │  │ - Index        │  │ /node/info     │   │
│  │ - List         │  │ - Pull/Push    │  │ /docs          │   │
│  │ - Receive      │  │ - Request      │  │                │   │
│  │ - Forward      │  │ - Stats        │  │                │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Bundle    │  │   Crypto   │  │    TTL     │  │  Cache   │ │
│  │  Service   │  │  Service   │  │  Service   │  │ Service  │ │
│  │            │  │            │  │            │  │          │ │
│  │ • Create   │  │ • Sign     │  │ • Enforce  │  │ • Budget │ │
│  │ • Validate │  │ • Verify   │  │ • Expire   │  │ • Evict  │ │
│  │ • Receive  │  │ • Keypair  │  │ • Clean    │  │ • Stats  │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
│                                                                  │
│  ┌────────────────────────────────────┐                         │
│  │      Forwarding Service             │                        │
│  │  • Priority ordering                │                        │
│  │  • Audience enforcement             │                        │
│  │  • Hop limit tracking               │                        │
│  └────────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Queue Manager                          │  │
│  │  • enqueue()  • dequeue()  • move()  • delete()          │  │
│  │  • list()     • exists()   • get_expired()               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   SQLite Database                         │  │
│  │                  (data/dtn_bundles.db)                    │  │
│  │                                                            │  │
│  │  Tables:                                                   │  │
│  │    • bundles (with indexes)                               │  │
│  │    • metadata                                             │  │
│  │                                                            │  │
│  │  Indexes:                                                  │  │
│  │    • queue                                                │  │
│  │    • priority                                             │  │
│  │    • expiresAt                                            │  │
│  │    • topic                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Queue Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Bundle Lifecycle                          │
└─────────────────────────────────────────────────────────────────┘

  LOCAL CREATION          PEER RECEPTION          FORWARDING
        │                       │                      │
        ▼                       ▼                      │
   ┌─────────┐            ┌─────────┐                │
   │ OUTBOX  │            │  INBOX  │                │
   └─────────┘            └─────────┘                │
        │                       │                      │
        │ First forward         │ Process              │
        ▼                       ▼                      │
   ┌─────────┐                                        │
   │ PENDING │◄───────────────────────────────────────┘
   └─────────┘                                    Awaiting
        │                                         next peer
        │ Receipt received
        ▼
   ┌──────────┐
   │DELIVERED │
   └──────────┘

  ERRORS & EXPIRATION
        │
        ├──────► ┌───────────┐  (Invalid signature)
        │        │ QUARANTINE│
        │        └───────────┘
        │
        └──────► ┌─────────┐   (TTL exceeded)
                 │ EXPIRED │
                 └─────────┘
                      │
                      │ After retention
                      ▼
                  [DELETED]
```

## Bundle Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                          Bundle                                  │
├─────────────────────────────────────────────────────────────────┤
│  bundleId: "b:sha256:..." (content-addressed)                   │
│  createdAt: "2025-12-17T10:00:00Z"                              │
│  expiresAt: "2025-12-20T00:00:00Z"  (TTL)                       │
│  priority: "emergency" | "perishable" | "normal" | "low"        │
│  audience: "public" | "local" | "trusted" | "private"           │
│  topic: "mutual-aid" | "knowledge" | "coordination" | ...       │
│  tags: ["food", "perishable"]                                   │
│  payloadType: "vf:Listing" (schema identifier)                  │
│  payload: { ... } (actual data)                                 │
│  hopLimit: 20                                                    │
│  hopCount: 0 (incremented on each forward)                      │
│  receiptPolicy: "none" | "requested" | "required"               │
│  signature: "..." (Ed25519)                                      │
│  authorPublicKey: "..." (Ed25519 public key PEM)                │
└─────────────────────────────────────────────────────────────────┘
```

## Priority Forwarding Order

```
┌─────────────────────────────────────────────────────────────────┐
│                   Forwarding Priority Queue                      │
└─────────────────────────────────────────────────────────────────┘

    HIGHEST PRIORITY
         │
         ▼
    ┌─────────────┐
    │  EMERGENCY  │  ← Never defer, always forward first
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │ PERISHABLE  │  ← Time-sensitive coordination
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │   NORMAL    │  ← General content
    │ trusted/    │
    │  private    │
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │   NORMAL    │  ← Public content
    │ public/     │
    │  local      │
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │     LOW     │  ← Background/bulk content
    └─────────────┘
         │
    LOWEST PRIORITY
```

## Audience Enforcement

```
┌─────────────────────────────────────────────────────────────────┐
│                    Audience Enforcement                          │
└─────────────────────────────────────────────────────────────────┘

PUBLIC          ┌─────────────┐
Audience ──────►│  Any Peer   │ ← Forward to anyone
                └─────────────┘

LOCAL           ┌─────────────┐
Audience ──────►│ Local Peers │ ← Check: peer_is_local == true
                └─────────────┘

TRUSTED         ┌─────────────┐
Audience ──────►│Trusted Peers│ ← Check: trust_score >= 0.7
                └─────────────┘

PRIVATE         ┌─────────────┐
Audience ──────►│  Recipient  │ ← Encrypted direct delivery
                │     Only    │   (not yet implemented)
                └─────────────┘
```

## Background Services

```
┌─────────────────────────────────────────────────────────────────┐
│                    Background Services                           │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  TTL Enforcement Service                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Every 60 seconds:                                    │ │
│  │    1. Find bundles where expiresAt < now             │ │
│  │    2. Move to EXPIRED queue                          │ │
│  │    3. Log count of expired bundles                   │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Cache Budget Service                                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  On-demand (when accepting bundles):                 │ │
│  │    1. Check cache usage vs budget                    │ │
│  │    2. If >= 95%, start eviction:                     │ │
│  │       a. Delete expired bundles                      │ │
│  │       b. Delete low-priority bundles                 │ │
│  │       c. Delete oldest bundles                       │ │
│  │    3. Accept bundle if under budget                  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Cryptographic Signing

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ed25519 Signing Flow                          │
└─────────────────────────────────────────────────────────────────┘

BUNDLE CREATION                        BUNDLE RECEPTION

┌──────────────┐                       ┌──────────────┐
│ Create Bundle│                       │Receive Bundle│
└──────┬───────┘                       └──────┬───────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                       ┌──────────────┐
│ Canonical    │                       │ Extract      │
│ JSON (sorted)│                       │ Signature    │
└──────┬───────┘                       └──────┬───────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                       ┌──────────────┐
│ Sign with    │                       │ Verify with  │
│ Private Key  │                       │ Public Key   │
└──────┬───────┘                       └──────┬───────┘
       │                                      │
       ▼                                      ├──► Valid
┌──────────────┐                             │    │
│ Calculate    │                             │    ▼
│ bundleId     │                             │ To INBOX
│ (SHA-256)    │                             │
└──────┬───────┘                             └──► Invalid
       │                                           │
       ▼                                           ▼
┌──────────────┐                            To QUARANTINE
│ To OUTBOX    │
└──────────────┘
```

## TTL Calculation

```
┌─────────────────────────────────────────────────────────────────┐
│                      TTL Calculation                             │
└─────────────────────────────────────────────────────────────────┘

Priority-Based:
  emergency    ──────► 12 hours
  perishable   ──────► 48 hours
  normal       ──────► 7 days
  low          ──────► 3 days

Tag-Based Overrides:
  "food" OR "perishable"  ──────► 48 hours
  "index"                 ──────► 3 days

Topic-Based:
  mutual-aid   ──────► 48 hours
  coordination ──────► 7 days
  inventory    ──────► 30 days
  knowledge    ──────► 270 days
  education    ──────► 270 days

Explicit:
  expiresAt provided ──────► Use provided value
```

## Sync Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                      Peer Sync Protocol                          │
└─────────────────────────────────────────────────────────────────┘

NODE A                              NODE B
   │                                   │
   │  GET /sync/index                  │
   ├──────────────────────────────────►│
   │                                   │
   │  [bundleId, priority, expires]    │
   │◄──────────────────────────────────┤
   │                                   │
   │  Compare with local bundles       │
   │                                   │
   │  POST /sync/request               │
   │  [list of bundleIds needed]       │
   ├──────────────────────────────────►│
   │                                   │
   │  [bundles with audience check]    │
   │◄──────────────────────────────────┤
   │                                   │
   │  Validate & store in INBOX        │
   │                                   │
   │  POST /sync/push (optional)       │
   │  [bundles to send to peer]        │
   ├──────────────────────────────────►│
   │                                   │
   │  [acceptance results]             │
   │◄──────────────────────────────────┤
   │                                   │
```

## Node Roles (Future)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Node Roles                                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│   CITIZEN    │  │   BRIDGE     │  │      AP      │  │ LIBRARY  │
│              │  │              │  │              │  │          │
│ Cache: 256MB │  │ Cache: 2-8GB │  │ Cache: 8GB+  │  │ Cache:   │
│ TTL: Strict  │  │ Aggressive   │  │ Portal host  │  │ Tens GB  │
│ Forward:     │  │ forwarding   │  │ Index pub    │  │          │
│  Local+Time  │  │ Emergency    │  │ High uptime  │  │ File     │
│  sensitive   │  │ priority     │  │              │  │ chunks   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────┘
```

---

**Architecture Version**: 1.0
**Created**: 2025-12-17
**Status**: Complete ✅
