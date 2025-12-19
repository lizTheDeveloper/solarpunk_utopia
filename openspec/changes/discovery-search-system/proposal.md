# Proposal: Discovery and Search System

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** ✅ IMPLEMENTED - Index publishing, query/response protocol, cache management complete
**Priority:** TIER 1 (Core Functionality)
**Complexity:** 3 systems (indexes, queries, responses)

---

## Problem Statement

In a mesh network where nodes don't store all data, users need to discover offers, needs, and knowledge without full replication. The system must support queries like "who has tomatoes available today?" or "who can teach beekeeping?" and route those queries to nodes that have relevant data, returning results via bundle propagation.

**Current state:** No discovery mechanism beyond local storage
**Desired state:** Rolling index system with query/response protocol

---

## Proposed Solution

Implement three types of index bundles (InventoryIndex, ServiceIndex, KnowledgeIndex) that nodes publish periodically to advertise what they have. Implement query bundles that propagate through the mesh, with nodes responding if they have matching data. Implement speculative index caching so bridge nodes can answer queries on behalf of disconnected nodes.

---

## Requirements

### Requirement: Index Bundles SHALL Advertise Local Data

Nodes SHALL periodically publish index bundles describing their local data.

#### Scenario: Node publishes inventory index

- GIVEN a node has local offers and needs
- WHEN the periodic index publisher runs (every 5-60 minutes)
- THEN the node SHALL create InventoryIndex bundle containing:
  - List of ResourceSpecs locally available
  - List of Listings (offer/need) with: id, category, location, quantity, expiry
  - Node's public key (for direct queries)
- AND SHALL set TTL to 1-7 days
- AND SHALL publish to DTN outbox with priority=normal

#### Scenario: Node publishes service index

- GIVEN a node has skill offers
- WHEN publishing ServiceIndex
- THEN it SHALL include: skills, available times, locations
- AND SHALL enable "who can teach X?" queries

#### Scenario: Node publishes knowledge index

- GIVEN a node has protocols, lessons, or files cached
- WHEN publishing KnowledgeIndex
- THEN it SHALL include: content hashes, titles, categories
- AND SHALL enable "what protocols exist for composting?" queries

### Requirement: Query Bundles SHALL Propagate Requests

Users SHALL be able to broadcast query bundles for discovery.

#### Scenario: User searches for tomatoes

- GIVEN a user needs tomatoes
- WHEN they search via UI
- THEN the system SHALL create query bundle:
  - `queryId`: unique identifier
  - `query`: "tomatoes" (keyword)
  - `filters`: {category: "Food", available: "within 24h"}
  - `requester`: user's Agent ID
  - `responseDeadline`: now + 1 hour
- AND SHALL publish with priority=normal, TTL=24h
- AND query SHALL propagate to other nodes

#### Scenario: Nodes respond to queries

- GIVEN a node receives a query bundle
- WHEN it has matching data in local VF database
- THEN it SHALL create response bundle:
  - `queryId`: matches original query
  - `results`: array of matching Listing references (bundleId)
  - `previews`: small snippets (title, location, quantity)
  - `source`: responding node's ID
- AND SHALL publish response bundle
- AND response SHALL route back to requester

### Requirement: Index Caching SHALL Enable Disconnected Discovery

Bridge nodes SHALL cache indexes to answer queries on behalf of disconnected nodes.

#### Scenario: Bridge node caches garden's index

- GIVEN a bridge node recently visited the Garden AP
- WHEN it received Garden's InventoryIndex
- THEN it SHALL cache the index (even if not subscribed)
- WHEN later visiting Kitchen AP and receiving query for garden produce
- THEN it SHALL respond with cached Garden index data
- AND SHALL indicate "cached from Garden, may be stale"

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Index bundle schemas (InventoryIndex, ServiceIndex, KnowledgeIndex)
2. Index publisher service (background, periodic)
3. Query bundle schema and creation UI
4. Query processor (match against local data)
5. Response bundle handler
6. Speculative index caching logic
7. UI for browsing results

---

## Success Criteria

- [ ] Index bundles published every 5-60 min (configurable)
- [ ] Indexes contain accurate local data
- [ ] Query bundles propagate across mesh
- [ ] Nodes respond to matching queries
- [ ] Responses route back to requester
- [ ] Results displayed in UI
- [ ] Bridge nodes cache indexes speculatively
- [ ] Cached indexes used to answer queries
- [ ] Query response time <2 min for nearby nodes
- [ ] Query response time <10 min across 3+ islands (via bridge)

---

## Dependencies

- DTN Bundle System (for publishing and propagation)
- ValueFlows Node (for local data to index)

---

## Constraints

- Indexes must be small (<50KB typical, <500KB max)
- Queries must not flood network (rate limiting)
- Stale cached indexes must be clearly marked

---

## Notes

This implements Section 6 "Discovery and Search (Index bundles)" from solarpunk_node_full_spec.md.
