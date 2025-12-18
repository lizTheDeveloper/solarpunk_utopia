# Discovery and Search System (TIER 1)

A complete production-ready discovery and search system for delay-tolerant mesh networks. Enables users to find offers, needs, services, and knowledge across disconnected islands without full data replication.

## Overview

The Discovery and Search System implements three core mechanisms:

1. **Index Bundle Publishing**: Nodes periodically publish compact indexes advertising their local data
2. **Query/Response Protocol**: Distributed search queries propagate through the mesh with responses routed back
3. **Speculative Index Caching**: Bridge nodes cache peer indexes to answer queries for offline nodes

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Discovery & Search System                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Index      │  │    Query     │  │   Response   │      │
│  │  Publisher   │  │   Handler    │  │   Builder    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         │         ┌────────┴────────┐        │               │
│         │         │  Cache Manager  │        │               │
│         │         └────────┬────────┘        │               │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                  │
│                    ┌───────┴────────┐                        │
│                    │   DTN Bundles  │                        │
│                    └────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Features

### System 1: Index Publishing (1.0 systems)

Three types of indexes advertise local data:

- **InventoryIndex**: Offers and needs for physical resources
  - Published every 10 minutes (configurable)
  - Contains: resource specs, quantities, locations, agents
  - TTL: 3 days

- **ServiceIndex**: Skills and labor offers
  - Published every 30 minutes (configurable)
  - Contains: skill types, availability, agents
  - TTL: 7 days

- **KnowledgeIndex**: Protocols, lessons, and files
  - Published every 60 minutes (configurable)
  - Contains: content types, titles, categories, hashes
  - TTL: 30 days

### System 2: Query/Response Protocol (1.2 systems)

- **Query Bundles**: Broadcast search requests
  - Free-text search with optional filters
  - Category, location, time constraints
  - Hop limit and TTL controls
  - Query ID for response correlation

- **Response Bundles**: Return matching results
  - Preview data for UI display
  - Bundle references for full data
  - Source node identification
  - Cached vs. local result tracking

### System 3: Speculative Caching (0.8 systems)

- **Automatic Index Caching**: Bridge nodes cache all indexes
- **Offline Discovery**: Answer queries for disconnected peers
- **Freshness Tracking**: Mark stale cached results
- **Budget Management**: LRU eviction when cache full (100MB default)

## Installation

The system is located at `/Users/annhoward/src/solarpunk_utopia/discovery_search/`

### Dependencies

- Python 3.12+
- FastAPI
- aiosqlite
- pydantic

Already integrated with:
- DTN Bundle System (`/Users/annhoward/src/solarpunk_utopia/app/`)
- ValueFlows Node (`/Users/annhoward/src/solarpunk_utopia/valueflows_node/`)

### Setup

1. The database is automatically initialized on first run
2. Indexes are published automatically based on configured intervals
3. Incoming bundles are processed every 30 seconds

## Usage

### Running the System

```bash
# Standalone mode
cd /Users/annhoward/src/solarpunk_utopia/discovery_search
python -m discovery_search.main

# Access API at http://localhost:8001
# API docs at http://localhost:8001/docs
```

### API Endpoints

#### Search for Resources

```bash
# Simple search
curl -X POST http://localhost:8001/discovery/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tomatoes",
    "max_results": 50,
    "timeout_minutes": 60
  }'

# Search with filters
curl -X POST http://localhost:8001/discovery/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tomatoes",
    "filters": {
      "category": "food",
      "listing_type": "offer",
      "available_within_hours": 24
    },
    "max_results": 50
  }'
```

Response:
```json
{
  "query_id": "query:123e4567-e89b-12d3-a456-426614174000",
  "query": "tomatoes",
  "results": [
    {
      "result_id": "listing-1",
      "result_type": "offer",
      "title": "Fresh Garden Tomatoes",
      "description": "Organic heirloom tomatoes",
      "category": "food",
      "source_node_id": "node-abc",
      "agent_name": "Garden Collective",
      "quantity": 5.0,
      "unit": "lbs",
      "is_cached": false
    }
  ],
  "total_results": 1,
  "local_results": 1,
  "cached_results": 0,
  "status": "completed"
}
```

#### Manually Publish Indexes

```bash
# Publish all indexes now
curl -X POST http://localhost:8001/discovery/indexes/publish \
  -H "Content-Type: application/json" \
  -d '{}'

# Publish specific index type
curl -X POST http://localhost:8001/discovery/indexes/publish \
  -H "Content-Type: application/json" \
  -d '{"index_type": "inventory"}'
```

#### View Cache Statistics

```bash
curl http://localhost:8001/discovery/cache/stats
```

Response:
```json
{
  "by_type": {
    "inventory": {
      "count": 5,
      "total_entries": 127,
      "total_bytes": 45231
    },
    "service": {
      "count": 3,
      "total_entries": 42,
      "total_bytes": 12456
    }
  },
  "total_indexes": 8,
  "total_entries": 169,
  "total_bytes": 57687,
  "unique_nodes": 5,
  "max_cache_bytes": 104857600,
  "usage_percent": 0.055
}
```

#### List Cached Indexes

```bash
# All indexes
curl http://localhost:8001/discovery/cache/indexes

# Filter by type
curl http://localhost:8001/discovery/cache/indexes?index_type=inventory
```

#### Evict Stale Indexes

```bash
curl -X POST http://localhost:8001/discovery/cache/evict?max_age_hours=24
```

### Integration with DTN

The system automatically processes incoming bundles:

```python
from discovery_search.bundle_processor import DiscoveryBundleProcessor

# In your DTN bundle receiver
processor = DiscoveryBundleProcessor(
    query_handler=query_handler,
    response_builder=response_builder,
    cache_manager=cache_manager,
)

# Process each incoming bundle
for bundle in inbox_bundles:
    await processor.process_bundle(bundle)
```

## Configuration

### Index Publishing Intervals

Configure in `IndexPublisher` initialization:

```python
publisher = IndexPublisher(
    node_id=node_id,
    node_public_key=node_public_key,
    bundle_service=bundle_service,
    inventory_interval_minutes=10,  # Default: 10
    service_interval_minutes=30,    # Default: 30
    knowledge_interval_minutes=60,  # Default: 60
)
```

### Cache Budget

Configure in `SpeculativeCacheManager`:

```python
cache_manager = SpeculativeCacheManager(
    max_cache_mb=100  # Default: 100 MB
)
```

## Data Models

### InventoryIndex

```python
{
  "index_type": "inventory",
  "node_id": "node-abc",
  "node_public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "entries": [
    {
      "listing_id": "listing-1",
      "listing_type": "offer",
      "resource_spec_id": "tomatoes",
      "resource_name": "Tomatoes",
      "category": "food",
      "quantity": 5.0,
      "unit": "lbs",
      "agent_id": "agent-1",
      "agent_name": "Garden Collective",
      "title": "Fresh Tomatoes",
      "available_until": "2025-12-20T12:00:00Z"
    }
  ],
  "generated_at": "2025-12-17T10:00:00Z",
  "expires_at": "2025-12-20T10:00:00Z",
  "total_offers": 10,
  "total_needs": 3,
  "categories": ["food", "seeds", "tools"]
}
```

### SearchQuery

```python
{
  "query_id": "query-123",
  "query_string": "tomatoes",
  "filters": {
    "category": "food",
    "listing_type": "offer",
    "available_within_hours": 24
  },
  "requester_node_id": "node-xyz",
  "max_results": 50,
  "response_deadline": "2025-12-17T11:00:00Z",
  "created_at": "2025-12-17T10:00:00Z"
}
```

### SearchResponse

```python
{
  "query_id": "query-123",
  "response_id": "resp-456",
  "results": [...],
  "total_results": 5,
  "responder_node_id": "node-abc",
  "created_at": "2025-12-17T10:01:00Z",
  "includes_cached_results": true,
  "local_results": 2,
  "cached_results": 3
}
```

## Performance

### Query Response Times

Based on proposal requirements:

- **Nearby nodes** (<2 hops): <2 minutes
- **Across islands** (3+ hops via bridge): <10 minutes

### Index Sizes

Typical sizes (actual varies by data):

- InventoryIndex with 100 entries: ~30-50 KB
- ServiceIndex with 50 entries: ~15-25 KB
- KnowledgeIndex with 30 entries: ~10-20 KB

All indexes are kept under 500 KB maximum.

### Cache Performance

- Cache lookup: O(1) with SQLite indexes
- Query matching: O(n) where n = total cached entries
- Eviction: O(log n) for LRU tracking

## Testing

### Run Unit Tests

```bash
cd /Users/annhoward/src/solarpunk_utopia/discovery_search
pytest tests/test_models.py -v
```

### Run Integration Tests

```bash
pytest tests/test_integration.py -v
```

### Test Coverage

- Model serialization/deserialization
- Index building from VF data
- Query matching logic
- Cache management
- End-to-end discovery flow

## Database Schema

### cached_indexes

Stores peer indexes for offline discovery:

```sql
CREATE TABLE cached_indexes (
    id INTEGER PRIMARY KEY,
    index_type TEXT NOT NULL,
    node_id TEXT NOT NULL,
    node_public_key TEXT NOT NULL,
    bundle_id TEXT NOT NULL,
    index_data TEXT NOT NULL,  -- JSON
    generated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    cached_at TEXT NOT NULL,
    entry_count INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL,
    UNIQUE(node_id, index_type)
);
```

### query_history

Tracks queries we've processed:

```sql
CREATE TABLE query_history (
    id INTEGER PRIMARY KEY,
    query_id TEXT UNIQUE NOT NULL,
    query_string TEXT NOT NULL,
    requester_node_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    responses_received INTEGER DEFAULT 0,
    total_results INTEGER DEFAULT 0
);
```

### response_tracking

Tracks responses we've sent/received:

```sql
CREATE TABLE response_tracking (
    id INTEGER PRIMARY KEY,
    response_id TEXT UNIQUE NOT NULL,
    query_id TEXT NOT NULL,
    responder_node_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    local_results INTEGER DEFAULT 0,
    cached_results INTEGER DEFAULT 0
);
```

## Troubleshooting

### No Results Found

1. Check if local VF database has data
2. Check if any indexes are cached: `GET /discovery/cache/stats`
3. Verify query string matches data
4. Check query filters aren't too restrictive

### Indexes Not Publishing

1. Check publisher is running: `GET /health`
2. Check publish schedule: `GET /discovery/indexes/stats`
3. Manually trigger: `POST /discovery/indexes/publish`
4. Check logs for errors

### Cache Not Working

1. Check cache budget: `GET /discovery/cache/stats`
2. Check if indexes expired: they auto-evict when expired
3. Verify incoming bundles are being processed
4. Check bundle processor loop is running

## Production Deployment

### Recommended Configuration

For production deployment:

1. **Index Publishing**:
   - Inventory: 5-10 minutes (high volatility)
   - Service: 30-60 minutes (medium volatility)
   - Knowledge: 60-120 minutes (low volatility)

2. **Cache Budget**:
   - Mobile nodes: 50-100 MB
   - Bridge nodes: 200-500 MB
   - Fixed nodes: 1-2 GB

3. **Query Settings**:
   - Max results: 50-100
   - Timeout: 30-60 minutes
   - Hop limit: 10-15

### Monitoring

Key metrics to monitor:

- Cache usage percentage
- Index publish success rate
- Query response time
- Results per query (local vs cached)
- Stale index evictions

### Security Considerations

- All indexes are signed with Ed25519
- Bundle signatures verified on receipt
- Public key included in all indexes
- No private data in indexes (encrypted bundles separate)

## Future Enhancements

Potential improvements (not in TIER 1):

- Advanced query operators (AND, OR, NOT)
- Geospatial proximity search
- Fuzzy text matching
- Result ranking by relevance
- Query result subscription (push updates)
- Index compression
- Differential index updates

## Support

For issues or questions:

1. Check logs at `/var/log/discovery_search.log`
2. Verify system health: `GET /health`
3. Check statistics: `GET /discovery/stats`
4. Review test cases for examples

## License

Part of the Solarpunk Mesh Network project.
