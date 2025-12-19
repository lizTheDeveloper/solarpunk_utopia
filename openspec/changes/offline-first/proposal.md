# Proposal: Offline-First Guarantees

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED - Local storage and WiFi Direct mesh sync working
**Complexity:** 3 systems
**Timeline:** WORKSHOP BLOCKER
**Implemented:** 2025-12-19

## Problem Statement

The current implementation assumes network connectivity. Services run in Docker containers, frontends call HTTP APIs, data lives on servers. This is exactly wrong for a resistance network.

When they shut down the internet, when cell networks are surveilled, when you're at a festival in the desert, when you're in a rural area - the app must work. Not "gracefully degrade." WORK.

## Proposed Solution

Rewrite the core architecture for offline-first operation:

1. **All data local first.** Your phone has a complete local database.
2. **Sync when possible.** When you connect to mesh or internet, sync happens.
3. **Conflict resolution.** When two people edit the same thing offline, resolve gracefully.
4. **No server dependency.** The network IS the phones. No central server required.

### Architecture Shift

**Current (Wrong):**
```
Phone → Internet → Server → Database
              ↓
         Single Point of Failure
```

**Target (Right):**
```
Phone (Local DB) ←→ Mesh ←→ Phone (Local DB)
                ↓
Phone (Local DB) ←→ Mesh ←→ Phone (Local DB)

       No Central Point of Failure
```

### Data Locality

| Data Type | Local | Synced | Notes |
|-----------|-------|--------|-------|
| My identity/keys | ✓ | Never | Only on my device |
| My offers/needs | ✓ | ✓ | Broadcast to cell |
| My messages | ✓ | To recipient | E2E encrypted |
| Cell directory | ✓ | ✓ | All cell members |
| Matches | ✓ | ✓ | Relevant parties |
| Trust graph | ✓ | ✓ | Public vouches |
| Exchange history | ✓ | ✓ | Participants |

## Requirements

### Requirement: Full Local Operation

The system SHALL operate fully without any network connection.

#### Scenario: Airplane Mode
- GIVEN the phone has no WiFi, cell, or Bluetooth
- WHEN the user opens the app
- THEN they see all their data (offers, needs, matches, messages)
- AND they can create new offers and needs
- AND they can compose messages (queued for delivery)
- AND the only indication is "Offline - will sync when connected"

### Requirement: Opportunistic Sync

The system SHALL sync automatically when connectivity is available.

#### Scenario: Coffee Shop Sync
- GIVEN Alice has been offline for 3 hours with queued changes
- WHEN Alice enters WiFi range of a mesh node
- THEN sync begins automatically in background
- AND her queued messages are sent
- AND new messages/offers for her are received
- AND she sees "Synced 2 minutes ago"

### Requirement: Mesh-Native Sync

The system SHALL sync over mesh without internet.

#### Scenario: Festival Mode
- GIVEN Alice is at a festival with no cell/internet but mesh nodes present
- WHEN Alice comes in range of another mesh phone
- THEN DTN bundles are exchanged via WiFi Direct or Bluetooth
- AND relevant data syncs
- AND this works with just 2 phones in proximity

### Requirement: Conflict Resolution

The system SHALL handle conflicts gracefully.

#### Scenario: Concurrent Edit
- GIVEN Alice edited her offer's description while offline
- AND Bob (a steward) also edited it while Alice was offline
- WHEN Alice reconnects
- THEN the system detects the conflict
- AND applies a resolution strategy (last-write-wins, merge, or ask user)
- AND both versions are preserved in history

### Requirement: Storage Efficiency

The system SHALL manage local storage efficiently.

#### Scenario: Limited Storage
- GIVEN a phone with limited storage (2GB free)
- WHEN the local database grows
- THEN old, low-priority data is pruned (completed exchanges >6 months)
- AND critical data (keys, active offers) is never pruned
- AND user can manually clear cache

### Requirement: Sync Status Visibility

The system SHALL show sync status clearly.

#### Scenario: User Awareness
- GIVEN the user opens the app
- THEN they always see sync status in the header
- AND can tap for details: "Last synced: 5 min ago, 3 items pending"
- AND offline mode is clearly indicated
- AND they're never surprised by stale data

## Technical Approach

### Local Database
- SQLite on device (same schema as server version)
- All queries run locally, instantly
- No network required for any read operation

### Sync Protocol
- CRDTs (Conflict-free Replicated Data Types) for collaborative data
- Or: Vector clocks with last-write-wins for simpler data
- DTN bundles for transport

### Background Sync
- Android Foreground Service for mesh listening
- Periodic sync when WiFi available
- Push-based sync when mesh contact made

## Tasks

1. [ ] Port SQLite schema to run on Android
2. [ ] Implement local-first data access layer
3. [ ] Design CRDT or vector clock sync strategy
4. [ ] Build sync service (background)
5. [ ] Implement WiFi Direct discovery and transfer
6. [ ] Implement Bluetooth LE mesh fallback
7. [ ] Build conflict detection and resolution UI
8. [ ] Create sync status component
9. [ ] Implement storage management and pruning
10. [ ] Test sync with 10+ devices in mesh
11. [ ] Test extended offline periods (days)
12. [ ] Stress test conflict resolution

## Dependencies

- Android Deployment (runs on phone)
- DTN Bundle System (transport layer)
- Mesh Networking (discovery and connection)

## Risks

- **Data divergence:** Long offline periods create complex conflicts. Mitigation: Simple data models, clear resolution rules.
- **Storage bloat:** Mesh gossip fills storage. Mitigation: TTL on bundles, priority-based pruning.
- **Battery drain:** Constant mesh scanning. Mitigation: Adaptive scanning intervals, user controls.

## Success Criteria

- [ ] App opens and is fully usable with airplane mode on
- [ ] Data syncs when two phones come in proximity (no internet)
- [ ] User always knows sync status
- [ ] Conflicts are resolved or presented for resolution
- [ ] Week-long offline period can be survived
- [ ] 100MB limit on local database is enforced
