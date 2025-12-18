# Implementation Tasks: Discovery and Search System

**Proposal:** discovery-search-system
**Complexity:** 3 systems

---

## Task Breakdown

### System 1: Index Generation and Publishing (1.0 systems)

**Task 1.1: Define index bundle schemas**
- InventoryIndex: ResourceSpecs, Listings
- ServiceIndex: Skills, availability
- KnowledgeIndex: Protocols, Lessons, file hashes
- **Complexity:** 0.2 systems

**Task 1.2: Implement index generator**
- Query local VF database
- Generate compact index data
- Sign index bundle
- **Complexity:** 0.4 systems

**Task 1.3: Implement periodic index publisher**
- Background service runs every 5-60 min
- Publishes InventoryIndex, ServiceIndex, KnowledgeIndex
- Configurable frequency per node role
- **Complexity:** 0.4 systems

### System 2: Query and Response Protocol (1.2 systems)

**Task 2.1: Define query bundle schema**
- Fields: queryId, query string, filters, requester, responseDeadline
- **Complexity:** 0.1 systems

**Task 2.2: Implement query creation UI**
- Search bar with filters
- Publish query bundle
- **Complexity:** 0.3 systems

**Task 2.3: Implement query processor**
- Receive query bundles
- Match against local VF database
- Generate response bundle if matches found
- **Complexity:** 0.4 systems

**Task 2.4: Implement response handler**
- Receive response bundles
- Match to original query
- Display results in UI
- **Complexity:** 0.4 systems

### System 3: Speculative Index Caching (0.8 systems)

**Task 3.1: Implement index cache**
- Store received indexes with timestamp
- Track freshness
- **Complexity:** 0.3 systems

**Task 3.2: Implement cache-based query responses**
- When query matches cached index, respond
- Mark response as "cached, may be stale"
- **Complexity:** 0.3 systems

**Task 3.3: Implement cache eviction**
- Remove stale indexes (>24h old)
- Respect cache budget
- **Complexity:** 0.2 systems

---

## Validation Checklist

- [ ] Index bundles generated correctly
- [ ] Indexes published periodically
- [ ] Query bundles created and propagated
- [ ] Nodes respond to matching queries
- [ ] Responses route back to requester
- [ ] Results displayed in UI
- [ ] Cached indexes used to respond
- [ ] Stale markers shown in UI
- [ ] Cache eviction works

---

## Total Complexity: 3 Systems
