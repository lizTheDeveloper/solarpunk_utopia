# Discovery and Search System - Usage Examples

This document provides practical examples of using the Discovery and Search System.

## Table of Contents

1. [Basic Search](#basic-search)
2. [Advanced Filtering](#advanced-filtering)
3. [Index Management](#index-management)
4. [Cache Operations](#cache-operations)
5. [Integration Examples](#integration-examples)

## Basic Search

### Example 1: Find Available Tomatoes

```python
import httpx
import asyncio

async def search_for_tomatoes():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/search",
            json={
                "query": "tomatoes",
                "max_results": 50,
                "timeout_minutes": 60
            }
        )

        data = response.json()

        print(f"Found {data['total_results']} results")
        print(f"Local results: {data['local_results']}")
        print(f"Cached results: {data['cached_results']}")

        for result in data['results']:
            print(f"\n{result['title']}")
            print(f"  Type: {result['result_type']}")
            print(f"  Category: {result['category']}")
            print(f"  Quantity: {result.get('quantity')} {result.get('unit')}")
            print(f"  From: {result.get('agent_name', 'Unknown')}")
            print(f"  Cached: {result['is_cached']}")

asyncio.run(search_for_tomatoes())
```

Output:
```
Found 3 results
Local results: 1
Cached results: 2

Fresh Garden Tomatoes
  Type: offer
  Category: food
  Quantity: 5.0 lbs
  From: Garden Collective
  Cached: False

Heirloom Tomatoes
  Type: offer
  Category: food
  Quantity: 3.0 lbs
  From: Urban Farm
  Cached: True
```

### Example 2: Search for Beekeeping Skills

```python
async def search_for_beekeeping():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/search",
            json={
                "query": "beekeeping",
                "filters": {
                    "category": "skills"
                },
                "max_results": 20
            }
        )

        data = response.json()

        for result in data['results']:
            print(f"\n{result['title']}")
            print(f"  Description: {result.get('description', 'N/A')}")
            print(f"  Teacher: {result.get('agent_name', 'Unknown')}")

asyncio.run(search_for_beekeeping())
```

## Advanced Filtering

### Example 3: Find Food Available Within 24 Hours

```python
async def find_urgent_food():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/search",
            json={
                "query": "",  # Empty query = return all
                "filters": {
                    "category": "food",
                    "listing_type": "offer",
                    "available_within_hours": 24
                },
                "max_results": 100
            }
        )

        data = response.json()

        print(f"Found {data['total_results']} food items available soon:")

        for result in data['results']:
            print(f"\n{result['title']} - {result.get('quantity')} {result.get('unit')}")
            if result.get('available_until'):
                print(f"  Available until: {result['available_until']}")

asyncio.run(find_urgent_food())
```

### Example 4: Location-Specific Search

```python
async def search_by_location(location_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/search",
            json={
                "query": "",
                "filters": {
                    "location_name": location_name
                },
                "max_results": 50
            }
        )

        data = response.json()

        print(f"Results at {location_name}:")

        for result in data['results']:
            print(f"  - {result['title']} ({result['category']})")

asyncio.run(search_by_location("Community Garden"))
```

## Index Management

### Example 5: Manually Trigger Index Publishing

```python
async def publish_all_indexes():
    """Publish all index types immediately"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/indexes/publish",
            json={}
        )

        print(response.json())
        # Output: {"status": "success", "message": "Published all indexes"}

asyncio.run(publish_all_indexes())
```

### Example 6: Publish Specific Index Type

```python
async def publish_inventory_index():
    """Publish only inventory index"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/indexes/publish",
            json={"index_type": "inventory"}
        )

        print(response.json())

asyncio.run(publish_inventory_index())
```

### Example 7: Check Publishing Schedule

```python
async def check_publish_schedule():
    """View when indexes were last published and when next"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/discovery/indexes/stats"
        )

        stats = response.json()

        for index_type, info in stats.items():
            print(f"\n{index_type.upper()} Index:")
            print(f"  Interval: {info['interval_minutes']} minutes")
            print(f"  Last published: {info['last_published_at']}")
            print(f"  Next publish: {info['next_publish_at']}")
            print(f"  Total publishes: {info['total_publishes']}")
            print(f"  Last entry count: {info['last_entry_count']}")

asyncio.run(check_publish_schedule())
```

Output:
```
INVENTORY Index:
  Interval: 10 minutes
  Last published: 2025-12-17T10:00:00Z
  Next publish: 2025-12-17T10:10:00Z
  Total publishes: 42
  Last entry count: 127

SERVICE Index:
  Interval: 30 minutes
  Last published: 2025-12-17T09:30:00Z
  Next publish: 2025-12-17T10:00:00Z
  Total publishes: 15
  Last entry count: 34
```

## Cache Operations

### Example 8: View Cache Statistics

```python
async def view_cache_stats():
    """Get detailed cache statistics"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/discovery/cache/stats"
        )

        stats = response.json()

        print(f"Cache Usage: {stats['usage_percent']:.2f}% of {stats['max_cache_mb']} MB")
        print(f"Total Indexes: {stats['total_indexes']}")
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Unique Nodes: {stats['unique_nodes']}")

        print("\nBy Index Type:")
        for index_type, info in stats['by_type'].items():
            print(f"  {index_type}: {info['count']} indexes, {info['total_entries']} entries")

asyncio.run(view_cache_stats())
```

### Example 9: List Cached Indexes

```python
async def list_cached_indexes():
    """List all cached indexes with details"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/discovery/cache/indexes"
        )

        data = response.json()

        print(f"Total cached indexes: {data['total_indexes']}\n")

        for index in data['indexes']:
            print(f"Node: {index['node_id']}")
            print(f"  Type: {index['index_type']}")
            print(f"  Entries: {len(index['entries'])}")
            print(f"  Generated: {index['generated_at']}")
            print(f"  Expires: {index['expires_at']}")
            print(f"  Cached: {index['cached_at']}")
            print()

asyncio.run(list_cached_indexes())
```

### Example 10: Evict Stale Indexes

```python
async def clean_cache():
    """Remove indexes older than 24 hours"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/discovery/cache/evict",
            params={"max_age_hours": 24}
        )

        data = response.json()
        print(f"Evicted {data['evicted_count']} stale indexes")

asyncio.run(clean_cache())
```

## Integration Examples

### Example 11: Building Custom Index

```python
from discovery_search.services import IndexBuilder
from datetime import datetime, timedelta

async def build_custom_index():
    """Build an index programmatically"""

    builder = IndexBuilder(
        node_id="my-node-123",
        node_public_key="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    )

    # Build inventory index
    inventory_index = await builder.build_inventory_index(ttl_days=3)

    print(f"Built inventory index:")
    print(f"  Total entries: {len(inventory_index.entries)}")
    print(f"  Offers: {inventory_index.total_offers}")
    print(f"  Needs: {inventory_index.total_needs}")
    print(f"  Categories: {inventory_index.categories}")
    print(f"  Expires: {inventory_index.expires_at}")

    # Convert to bundle payload
    payload = inventory_index.to_payload()
    print(f"\nPayload size: {len(str(payload))} bytes")

asyncio.run(build_custom_index())
```

### Example 12: Processing Query Programmatically

```python
from discovery_search.services import QueryHandler
from discovery_search.models import SearchQuery
from datetime import datetime, timedelta
import uuid

async def process_custom_query():
    """Process a query programmatically"""

    handler = QueryHandler(
        node_id="my-node-123",
        node_public_key="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    )

    # Create query
    query = SearchQuery(
        query_id=f"query:{uuid.uuid4()}",
        query_string="tomatoes",
        requester_node_id="other-node-456",
        max_results=50,
        response_deadline=datetime.utcnow() + timedelta(hours=1),
        created_at=datetime.utcnow(),
    )

    # Process query
    results = await handler.process_query(query)

    print(f"Found {len(results)} results")

    for result in results:
        print(f"\n{result.title}")
        print(f"  Type: {result.result_type}")
        print(f"  Source: {result.source_node_id}")
        print(f"  Cached: {result.is_cached}")

asyncio.run(process_custom_query())
```

### Example 13: Caching Index from Bundle

```python
from discovery_search.services import SpeculativeCacheManager
from discovery_search.models import InventoryIndex, InventoryIndexEntry
from datetime import datetime, timedelta

async def cache_peer_index():
    """Cache an index received from a peer"""

    cache_manager = SpeculativeCacheManager(max_cache_mb=100)

    # Create mock index from peer
    now = datetime.utcnow()

    entry = InventoryIndexEntry(
        listing_id="peer-listing-1",
        listing_type="offer",
        resource_spec_id="carrots",
        resource_name="Carrots",
        category="food",
        quantity=10.0,
        unit="lbs",
        agent_id="peer-agent-1",
        title="Fresh Carrots",
    )

    index = InventoryIndex(
        node_id="peer-node-789",
        node_public_key="-----BEGIN PUBLIC KEY-----\npeer\n-----END PUBLIC KEY-----",
        entries=[entry],
        generated_at=now,
        expires_at=now + timedelta(days=3),
        total_offers=1,
        total_needs=0,
        categories=["food"],
    )

    # Cache it
    success = await cache_manager.cache_index_bundle(
        bundle_id="b:sha256:test123",
        payload=index.to_payload(),
    )

    print(f"Cached: {success}")

    # Retrieve it
    cached = await cache_manager.get_cached_index(
        node_id="peer-node-789",
        index_type="inventory"
    )

    if cached:
        print(f"Retrieved cached index with {len(cached['entries'])} entries")

asyncio.run(cache_peer_index())
```

### Example 14: Monitoring System Health

```python
async def monitor_system():
    """Monitor discovery system health"""
    async with httpx.AsyncClient() as client:
        # Check overall health
        health = await client.get("http://localhost:8001/health")
        health_data = health.json()

        print("System Health:")
        print(f"  Status: {health_data['status']}")
        print(f"  Cache indexes: {health_data['cache']['total_indexes']}")
        print(f"  Cache usage: {health_data['cache']['usage_percent']:.2f}%")
        print(f"  Index publisher: {health_data['services']['index_publisher']}")

        # Get detailed stats
        stats = await client.get("http://localhost:8001/discovery/stats")
        stats_data = stats.json()

        print("\nDetailed Statistics:")
        print(f"  Total responses sent: {stats_data['responses']['total_responses']}")
        print(f"  Total results served: {stats_data['responses']['total_results']}")
        print(f"  Recent queries (24h): {stats_data['responses']['responses_last_24h']}")

asyncio.run(monitor_system())
```

### Example 15: Complete Discovery Flow

```python
async def complete_discovery_example():
    """
    Complete example: Publish index, receive query, send response
    """
    from discovery_search.services import (
        IndexBuilder,
        IndexPublisher,
        QueryHandler,
        ResponseBuilder,
    )
    from app.services import BundleService, CryptoService

    # Initialize services
    crypto = CryptoService()
    bundle_service = BundleService(crypto)
    node_id = crypto.get_public_key_fingerprint()
    node_public_key = crypto.get_public_key_pem()

    # Build and publish index
    builder = IndexBuilder(node_id, node_public_key)
    publisher = IndexPublisher(node_id, node_public_key, bundle_service)

    print("Step 1: Publishing indexes...")
    await publisher.publish_now()

    # Simulate receiving query
    print("\nStep 2: Receiving query...")
    query_handler = QueryHandler(node_id, node_public_key)
    response_builder = ResponseBuilder(node_id, node_public_key, bundle_service)

    query = SearchQuery(
        query_id=f"query:{uuid.uuid4()}",
        query_string="tomatoes",
        requester_node_id="remote-node",
        max_results=50,
        response_deadline=datetime.utcnow() + timedelta(hours=1),
        created_at=datetime.utcnow(),
    )

    # Process query
    print("Step 3: Processing query...")
    results = await query_handler.process_query(query)
    print(f"Found {len(results)} results")

    # Send response
    if results:
        print("Step 4: Sending response...")
        bundle_id = await response_builder.build_and_publish_response(query, results)
        print(f"Response published: {bundle_id}")

    print("\nDiscovery flow complete!")

asyncio.run(complete_discovery_example())
```

## Command Line Examples

Using `curl` for quick testing:

```bash
# Search for tomatoes
curl -X POST http://localhost:8001/discovery/search \
  -H "Content-Type: application/json" \
  -d '{"query": "tomatoes", "max_results": 50}'

# Search with filters
curl -X POST http://localhost:8001/discovery/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tomatoes",
    "filters": {
      "category": "food",
      "listing_type": "offer"
    }
  }'

# Publish indexes
curl -X POST http://localhost:8001/discovery/indexes/publish \
  -H "Content-Type: application/json" \
  -d '{}'

# View cache stats
curl http://localhost:8001/discovery/cache/stats | jq '.'

# List cached indexes
curl http://localhost:8001/discovery/cache/indexes | jq '.indexes[] | {node_id, index_type, entries: (.entries | length)}'

# System health
curl http://localhost:8001/health | jq '.'
```

## Best Practices

1. **Query Design**:
   - Use specific search terms for better results
   - Apply filters to narrow results
   - Set reasonable max_results (50-100)

2. **Index Publishing**:
   - Let automatic publishing handle routine updates
   - Manually publish after major data changes
   - Monitor publish schedule

3. **Cache Management**:
   - Monitor cache usage regularly
   - Evict stale indexes periodically (daily)
   - Adjust cache budget based on node role

4. **Error Handling**:
   - Always check response status
   - Handle empty results gracefully
   - Retry failed searches after delay

5. **Performance**:
   - Batch queries when possible
   - Cache frequently searched terms
   - Use filters to reduce result set
