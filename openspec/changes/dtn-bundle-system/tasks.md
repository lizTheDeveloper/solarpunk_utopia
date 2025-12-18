# Implementation Tasks: DTN Bundle System

**Proposal:** dtn-bundle-system
**Complexity:** 5 systems

---

## Task Breakdown

### System 1: Bundle Format and Serialization

**Task 1.1: Define bundle schema**
- Create JSON schema for bundle format
- Document all fields and constraints
- Create TypeScript/Kotlin types
- **Complexity:** 0.3 systems

**Task 1.2: Implement bundle creation**
- `createBundle(payload, options)` function
- Auto-generate bundleId (sha256 of canonical JSON)
- Auto-assign TTL based on priority/topic/tags
- Signature generation (Ed25519)
- **Complexity:** 0.4 systems

**Task 1.3: Implement bundle validation**
- Schema validation
- Signature verification
- TTL validation
- HopLimit validation
- **Complexity:** 0.3 systems

### System 2: Queue Management

**Task 2.1: Design queue storage**
- Choose: SQLite tables OR filesystem directories
- Design indexes for efficient queries (by priority, expiresAt, topic)
- **Complexity:** 0.2 systems

**Task 2.2: Implement queue operations**
- `enqueue(queueName, bundle)`
- `dequeue(queueName, filter?)`
- `move(bundleId, fromQueue, toQueue)`
- `list(queueName, filter?, limit?)`
- `delete(bundleId)`
- **Complexity:** 0.4 systems

**Task 2.3: Implement queue transitions**
- Received bundle → inbox
- Created bundle → outbox
- Outbox → pending (after first forward attempt)
- Pending → delivered (if receipt received)
- Any queue → expired (if TTL exceeded)
- Invalid signature → quarantine
- **Complexity:** 0.4 systems

### System 3: TTL and Cache Management

**Task 3.1: Implement TTL enforcement service**
- Background process checks expiresAt every 60 seconds
- Moves expired bundles to expired queue
- Configurable audit retention (default 7 days, then delete)
- **Complexity:** 0.3 systems

**Task 3.2: Implement cache budget manager**
- Track total storage used
- Calculate per-bundle size
- Enforce storage budget (evict when >95%)
- Eviction order: expired → low-priority → oldest
- **Complexity:** 0.4 systems

**Task 3.3: Implement bandwidth budget tracking**
- Track bytes sent/received per hour
- Reset counter every hour
- Defer low-priority forwarding when >90% budget
- **Complexity:** 0.2 systems

**Task 3.4: Implement battery-aware behavior**
- Read Android battery level
- Apply battery profile (aggressive / balanced / conservative)
- Reduce activity when battery low
- Enter low-power mode when <10%
- **Complexity:** 0.3 systems

### System 4: Forwarding and Routing

**Task 4.1: Implement priority-based forwarding**
- Sort pending queue by priority
- Emergency always forwards immediately
- Respect bandwidth budget for lower priorities
- **Complexity:** 0.4 systems

**Task 4.2: Implement audience enforcement**
- Check audience field before forwarding
- Public: forward to anyone
- Local: forward only within trust boundary
- Trusted: check peer trust score
- Private: encrypted direct delivery only
- **Complexity:** 0.4 systems

**Task 4.3: Implement hop limit tracking**
- Increment hopCount on each forward
- Drop bundles when hopCount ≥ hopLimit
- **Complexity:** 0.2 systems

**Task 4.4: Implement speculative caching logic**
- Define utility function (emergency + hot bundles)
- Cache high-utility bundles even if not subscribed
- Evict speculative before subscribed when budget exceeded
- **Complexity:** 0.3 systems

### System 5: Cryptographic Trust

**Task 5.1: Implement signing infrastructure**
- Generate Ed25519 keypair per node
- Store private key securely (Android Keystore)
- Sign bundles on creation
- **Complexity:** 0.4 systems

**Task 5.2: Implement signature verification**
- Verify signature on bundle receipt
- Move invalid signatures to quarantine
- Track verification failures per peer (detect attacks)
- **Complexity:** 0.3 systems

**Task 5.3: Implement trust management**
- Support manual trust lists (allowlist/blocklist)
- Optional: web-of-trust scoring
- Optional: steward-issued membership tokens
- **Complexity:** 0.4 systems

---

## Android Integration Tasks

**Task A1: Create DTN Bundle Service**
- Android foreground service
- Runs continuously in background
- Processes queues every 10-60 seconds
- **Complexity:** 0.3 systems

**Task A2: Implement peer discovery**
- Scan for Wi-Fi networks
- Connect to Solarpunk APs
- Discover peers on local network (mDNS)
- **Complexity:** 0.4 systems

**Task A3: Implement bundle exchange protocol**
- HTTP POST /bundles/receive (receive bundles from peers)
- HTTP GET /bundles/list (advertise available bundles)
- HTTP POST /bundles/request (request specific bundles)
- **Complexity:** 0.4 systems

**Task A4: Implement sync on connection**
- When joining new AP, announce presence
- Exchange bundle indexes
- Request missing bundles by priority
- Respect bandwidth budget
- **Complexity:** 0.4 systems

---

## Testing Tasks

**Task T1: Unit tests**
- Bundle creation and validation
- Queue operations
- TTL enforcement
- Cache eviction
- Signature verification
- **Complexity:** 0.3 systems

**Task T2: Integration tests**
- Multi-node forwarding
- Priority ordering
- Audience enforcement
- Hop limit enforcement
- **Complexity:** 0.4 systems

**Task T3: Field tests**
- 3+ phones on 3+ APs
- Bridge node walks between islands
- Measure propagation time
- Verify emergency bundles reach all nodes
- **Complexity:** 0.3 systems

---

## Validation Checklist

- [ ] Bundle schema documented and implemented
- [ ] All queue operations working (enqueue, dequeue, move, list, delete)
- [ ] TTL enforcement runs every 60s, moves expired bundles
- [ ] Storage budget enforced, eviction works correctly
- [ ] Bandwidth budget tracked per hour
- [ ] Battery-aware behavior reduces activity when low
- [ ] Priority-based forwarding (emergency first)
- [ ] Audience enforcement (public, local, trusted, private)
- [ ] Hop limit prevents infinite loops
- [ ] Speculative caching works for emergency/knowledge
- [ ] Ed25519 signing on bundle creation
- [ ] Signature verification on receipt, quarantine on failure
- [ ] Trust system prevents unauthorized forwarding
- [ ] Android service runs in background
- [ ] Peer discovery works on local network
- [ ] Bundle exchange protocol functional
- [ ] Sync on AP connection works
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass (multi-node scenarios)
- [ ] Field test: emergency bundle propagates to all nodes in <5 min

---

## Total Complexity: 5 Systems

- Bundle format: 1.0 systems
- Queue management: 1.0 systems
- TTL and cache: 1.2 systems
- Forwarding and routing: 1.3 systems
- Cryptographic trust: 1.1 systems
- Android integration: 1.5 systems (includes peer discovery and sync)
- Testing: 1.0 systems

**Note:** Overlapping tasks mean actual total ≈ 5 systems as estimated.
