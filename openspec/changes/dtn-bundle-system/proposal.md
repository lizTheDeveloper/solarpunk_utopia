# Proposal: DTN Bundle System (Full)

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** Draft
**Priority:** TIER 0 (Foundation)
**Complexity:** 5 systems (bundle format, queues, routing, caching, signing)

---

## Problem Statement

Solar Punk communes need reliable message and data transport across multiple Wi-Fi AP "islands" without depending on internet connectivity or centralized infrastructure. Messages must propagate via store-and-forward as people move between locations (garden, kitchen, workshop, library). The system must handle time-sensitive coordination (perishable food offers, emergency requests) while respecting cache budgets and battery constraints.

**Current state:** No transport layer
**Desired state:** Complete DTN (Delay-Tolerant Networking) bundle system with TTL, priority queues, cache budgets, speculative caching, and trust-based forwarding

---

## Proposed Solution

Implement a complete DTN bundle layer as the core transport mechanism for all data in the Solarpunk mesh network. All payloads (offers, needs, files, indexes, queries) move as signed bundles with TTL, priority, audience controls, and hop limits. Nodes implement cache budgets and forwarding policies based on role (citizen, bridge, AP, library).

---

## Requirements

### Requirement: Bundle Format SHALL Be Defined

The system SHALL transport all data as structured bundles with metadata and payload.

#### Scenario: Node creates and serializes bundle

- GIVEN an agent wants to publish an offer or need
- WHEN the system creates a bundle
- THEN the bundle SHALL contain:
  - `bundleId`: content-addressed identifier (sha256)
  - `createdAt`: ISO 8601 timestamp
  - `expiresAt`: ISO 8601 timestamp (TTL)
  - `priority`: enum (emergency, perishable, normal, low)
  - `audience`: enum (public, local, trusted, private)
  - `topic`: subject category (mutual-aid, knowledge, coordination)
  - `tags`: array of strings for filtering
  - `payloadType`: schema identifier (vf:Listing, vf:Event, query:Search, etc.)
  - `payload`: typed data object
  - `hopLimit`: integer (default 20)
  - `receiptPolicy`: enum (none, requested, required)
  - `signature`: cryptographic signature of bundle

#### Scenario: Bundle is content-addressed

- GIVEN a bundle has been created
- WHEN the system calculates bundleId
- THEN bundleId SHALL be `b:sha256:{hash}` where hash is sha256 of canonical JSON

### Requirement: Queue Management SHALL Be Implemented

The system SHALL maintain separate queues for bundle lifecycle management.

#### Scenario: Bundles flow through queues

- GIVEN bundles are being received and forwarded
- WHEN the system processes bundles
- THEN the following queues SHALL exist:
  - `inbox`: received bundles awaiting processing
  - `outbox`: locally-created bundles awaiting forwarding
  - `pending`: bundles awaiting opportunistic forwarding
  - `delivered`: acknowledged deliveries (if receipts enabled)
  - `expired`: bundles dropped due to TTL expiration
  - `quarantine`: bundles with invalid signatures or policy violations

#### Scenario: Expired bundles are removed

- GIVEN a bundle in any queue
- WHEN current time > bundle.expiresAt
- THEN the bundle SHALL be moved to `expired` queue
- AND SHALL NOT be forwarded
- AND SHALL be deleted after audit retention period

### Requirement: TTL Defaults SHALL Be Defined by Content Type

The system SHALL assign appropriate TTL based on bundle content and priority.

#### Scenario: Emergency content has short TTL

- GIVEN a bundle with priority=emergency
- WHEN TTL is not explicitly set
- THEN expiresAt SHALL be createdAt + 6 to 24 hours

#### Scenario: Perishable food offers have appropriate TTL

- GIVEN a bundle with topic=mutual-aid AND tags includes "food" or "perishable"
- WHEN TTL is not explicitly set
- THEN expiresAt SHALL be createdAt + 24 to 72 hours

#### Scenario: Knowledge content has long TTL

- GIVEN a bundle with topic=knowledge (protocols, lessons)
- WHEN TTL is not explicitly set
- THEN expiresAt SHALL be createdAt + 180 to 365 days

### Requirement: Cache Budgets SHALL Be Enforced

Each node SHALL respect storage, bandwidth, and battery budgets based on role.

#### Scenario: Node enforces storage budget

- GIVEN a node has storage budget of 2GB
- WHEN total bundle cache exceeds 1.9GB (95% threshold)
- THEN the node SHALL:
  - Delete expired bundles first
  - Delete low-priority bundles next
  - Delete bundles exceeding hopLimit
  - Delete oldest bundles of same priority
- AND SHALL NOT accept new bundles if at 100% capacity

#### Scenario: Node enforces bandwidth budget

- GIVEN a node has bandwidth budget of 100MB/hour
- WHEN bandwidth usage exceeds 90MB in current hour
- THEN the node SHALL:
  - Defer low-priority forwarding
  - Complete emergency/perishable forwarding only
  - Reset budget at hour boundary

#### Scenario: Node respects battery profile

- GIVEN a node has battery profile set to "balanced"
- WHEN battery level < 20%
- THEN the node SHALL:
  - Stop speculative caching
  - Forward emergency priority only
  - Reduce sync frequency
- WHEN battery level < 10%
- THEN the node SHALL enter low-power mode (receive only)

### Requirement: Forwarding Rules SHALL Be Implemented

Nodes SHALL forward bundles according to priority and audience.

#### Scenario: Emergency bundles are forwarded first

- GIVEN a node has pending bundles to forward
- WHEN the node has forwarding opportunity
- THEN bundles SHALL be forwarded in this order:
  1. priority=emergency (never defer)
  2. priority=perishable AND tags includes time-sensitive coordination
  3. priority=normal, audience=trusted/private
  4. priority=normal, audience=public/local
  5. priority=low

#### Scenario: Audience restrictions are enforced

- GIVEN a bundle with audience=private
- WHEN considering forwarding to peer
- THEN the bundle SHALL only be forwarded if:
  - Peer is explicit recipient (encrypted direct delivery)
- AND SHALL NOT be forwarded to untrusted peers

#### Scenario: Hop limit prevents loops

- GIVEN a bundle has hopLimit=5
- WHEN the bundle has been forwarded 5 times
- THEN the bundle SHALL NOT be forwarded again
- AND SHALL be moved to expired queue

### Requirement: Speculative Caching SHALL Be Supported

Nodes MAY cache bundles they are not subscribed to if high utility.

#### Scenario: Bridge node caches emergency bundles

- GIVEN a bridge node with role=bridge
- WHEN it receives a bundle with priority=emergency
- THEN it SHALL cache the bundle even if not subscribed
- AND SHALL forward aggressively to all peers

#### Scenario: Library node caches knowledge

- GIVEN a library node with role=library
- WHEN it receives a bundle with topic=knowledge
- THEN it SHALL cache the bundle for long-term storage
- AND SHALL serve to queries even if not originally subscribed

#### Scenario: Speculative cache respects budgets

- GIVEN speculative caching is enabled
- WHEN cache budget is exceeded
- THEN speculative bundles SHALL be evicted before subscribed bundles

### Requirement: Trust and Signing SHALL Be Enforced

All bundles SHALL be cryptographically signed and verified.

#### Scenario: Bundle signature is verified on receipt

- GIVEN a bundle is received from peer
- WHEN the system validates the bundle
- THEN the signature SHALL be verified against authoring agent's public key
- AND if signature is invalid, bundle SHALL move to quarantine
- AND quarantined bundles SHALL NOT be forwarded

#### Scenario: Trust threshold affects forwarding

- GIVEN a bundle with audience=trusted
- WHEN considering forwarding to peer
- THEN peer SHALL have trust score ≥ configured threshold
- AND trust MAY be calculated via:
  - Manual trust lists, OR
  - Web-of-trust scoring, OR
  - Steward-issued membership tokens

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Bundle format schema and serialization (JSON)
2. Queue management system (SQLite or filesystem)
3. TTL enforcement service (background process)
4. Cache budget manager
5. Forwarding policy engine
6. Cryptographic signing and verification (Ed25519)
7. Trust management system
8. Android service integration

---

## Success Criteria

- [ ] Bundle format fully specified and documented
- [ ] All 6 queues implemented and functional
- [ ] TTL defaults applied correctly per content type
- [ ] Cache budgets enforced (storage, bandwidth, battery)
- [ ] Forwarding rules respect priority and audience
- [ ] Speculative caching works for emergency/knowledge
- [ ] All bundles are signed and verified
- [ ] Invalid signatures go to quarantine
- [ ] Trust thresholds prevent unauthorized forwarding
- [ ] System handles 1000+ bundles without performance degradation
- [ ] Bundle propagation tested across 3+ AP islands
- [ ] Emergency bundle reaches all nodes in <5 min (via bridge walks)

---

## Dependencies

- Cryptographic library: libsodium or equivalent for Ed25519 signing
- Storage: SQLite for queue management or efficient filesystem structure
- Android: Background service for queue processing and forwarding
- Network: Wi-Fi scanning and connection management

---

## Constraints

- **Battery:** Forwarding must be battery-aware (configurable profiles)
- **Storage:** Citizen nodes may have only 256MB-1GB cache
- **Trust:** Must support zero-knowledge operation (no central authority)
- **Privacy:** Private/trusted bundles must not leak to public

---

## Notes

This is the foundational transport layer. All other systems (ValueFlows, agents, file chunking) depend on DTN bundles working correctly. Priority is correctness and reliability over performance optimization.

The spec calls this "DTN Bundle Layer (Core Transport)" from Section 4 of solarpunk_node_full_spec.md.
