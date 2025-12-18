"""
Integration tests for discovery system

Tests the complete query/response flow.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from ..models import (
    IndexType,
    InventoryIndex,
    InventoryIndexEntry,
    SearchQuery,
    QueryFilter,
)
from ..services import (
    QueryHandler,
    ResponseBuilder,
    SpeculativeCacheManager,
)
from ..database import init_discovery_db, close_discovery_db, IndexCacheDB


@pytest.fixture
async def discovery_db():
    """Initialize test database"""
    await init_discovery_db()
    yield
    await close_discovery_db()


@pytest.fixture
def node_info():
    """Test node information"""
    return {
        "node_id": "test-node-123",
        "node_public_key": "-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
    }


class MockBundleService:
    """Mock bundle service for testing"""

    def __init__(self):
        self.created_bundles = []

    async def create_bundle(self, bundle_create):
        """Mock bundle creation"""
        from app.models import Bundle

        bundle = Bundle(
            bundleId=f"b:sha256:test-{len(self.created_bundles)}",
            createdAt=datetime.utcnow(),
            expiresAt=bundle_create.expiresAt or datetime.utcnow() + timedelta(days=1),
            priority=bundle_create.priority,
            audience=bundle_create.audience,
            topic=bundle_create.topic,
            tags=bundle_create.tags,
            payloadType=bundle_create.payloadType,
            payload=bundle_create.payload,
            hopLimit=bundle_create.hopLimit,
            hopCount=0,
            receiptPolicy=bundle_create.receiptPolicy,
            signature="test-signature",
            authorPublicKey="test-key",
        )

        self.created_bundles.append(bundle)
        return bundle


@pytest.mark.asyncio
class TestCacheManager:
    """Test speculative cache manager"""

    async def test_cache_index(self, discovery_db, node_info):
        """Test caching an index"""
        cache_manager = SpeculativeCacheManager(max_cache_mb=10)

        # Create test index
        now = datetime.utcnow()
        expires = now + timedelta(days=3)

        entry = InventoryIndexEntry(
            listing_id="listing-1",
            listing_type="offer",
            resource_spec_id="tomatoes",
            resource_name="Tomatoes",
            category="food",
            quantity=5.0,
            unit="lbs",
            agent_id="agent-1",
        )

        index = InventoryIndex(
            node_id="peer-node-456",
            node_public_key="-----BEGIN PUBLIC KEY-----\npeer\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        # Cache it
        payload = index.to_payload()
        success = await cache_manager.cache_index_bundle(
            bundle_id="b:sha256:test",
            payload=payload,
        )

        assert success

        # Retrieve it
        cached = await cache_manager.get_cached_index(
            node_id="peer-node-456",
            index_type=IndexType.INVENTORY,
        )

        assert cached is not None
        assert cached["node_id"] == "peer-node-456"

    async def test_cache_eviction(self, discovery_db):
        """Test cache eviction"""
        cache_manager = SpeculativeCacheManager(max_cache_mb=10)

        # Create old index
        old_time = datetime.utcnow() - timedelta(days=2)
        old_expires = old_time + timedelta(hours=1)  # Expired

        entry = InventoryIndexEntry(
            listing_id="listing-1",
            listing_type="offer",
            resource_spec_id="tomatoes",
            resource_name="Tomatoes",
            category="food",
            quantity=5.0,
            unit="lbs",
            agent_id="agent-1",
        )

        index = InventoryIndex(
            node_id="old-node",
            node_public_key="-----BEGIN PUBLIC KEY-----\nold\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=old_time,
            expires_at=old_expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        # Try to cache expired index (should not cache)
        payload = index.to_payload()
        success = await cache_manager.cache_index_bundle(
            bundle_id="b:sha256:old",
            payload=payload,
        )

        assert not success  # Should not cache expired index

    async def test_cache_stats(self, discovery_db, node_info):
        """Test cache statistics"""
        cache_manager = SpeculativeCacheManager(max_cache_mb=10)

        # Create and cache test index
        now = datetime.utcnow()
        expires = now + timedelta(days=3)

        entry = InventoryIndexEntry(
            listing_id="listing-1",
            listing_type="offer",
            resource_spec_id="tomatoes",
            resource_name="Tomatoes",
            category="food",
            quantity=5.0,
            unit="lbs",
            agent_id="agent-1",
        )

        index = InventoryIndex(
            node_id="test-node",
            node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        await cache_manager.cache_index_bundle(
            bundle_id="b:sha256:test",
            payload=index.to_payload(),
        )

        # Get stats
        stats = await cache_manager.get_cache_stats()

        assert stats["total_indexes"] >= 1
        assert "by_type" in stats
        assert "inventory" in stats["by_type"]


@pytest.mark.asyncio
class TestQueryResponse:
    """Test query and response flow"""

    async def test_query_without_results(self, discovery_db, node_info):
        """Test query that finds no results"""
        query_handler = QueryHandler(
            node_id=node_info["node_id"],
            node_public_key=node_info["node_public_key"],
        )

        # Create query
        query = SearchQuery(
            query_id="query-1",
            query_string="nonexistent",
            requester_node_id=node_info["node_id"],
            max_results=50,
            response_deadline=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )

        # Process query (should find no results since DB is empty)
        results = await query_handler.process_query(query, search_local=False, search_cache=True)

        assert len(results) == 0

    async def test_query_with_cached_results(self, discovery_db, node_info):
        """Test query that finds results in cache"""
        cache_manager = SpeculativeCacheManager(max_cache_mb=10)
        query_handler = QueryHandler(
            node_id=node_info["node_id"],
            node_public_key=node_info["node_public_key"],
        )

        # Cache a test index
        now = datetime.utcnow()
        expires = now + timedelta(days=3)

        entry = InventoryIndexEntry(
            listing_id="listing-1",
            listing_type="offer",
            resource_spec_id="tomatoes",
            resource_name="Tomatoes",
            category="food",
            quantity=5.0,
            unit="lbs",
            agent_id="agent-1",
            title="Fresh Tomatoes",
        )

        index = InventoryIndex(
            node_id="peer-node",
            node_public_key="-----BEGIN PUBLIC KEY-----\npeer\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        await cache_manager.cache_index_bundle(
            bundle_id="b:sha256:test",
            payload=index.to_payload(),
        )

        # Query for tomatoes
        query = SearchQuery(
            query_id="query-1",
            query_string="tomatoes",
            requester_node_id=node_info["node_id"],
            max_results=50,
            response_deadline=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )

        # Process query
        results = await query_handler.process_query(query, search_local=False, search_cache=True)

        assert len(results) == 1
        assert results[0].result_id == "listing-1"
        assert results[0].is_cached is True
        assert "tomatoes" in results[0].title.lower()

    async def test_response_builder(self, discovery_db, node_info):
        """Test building and publishing response"""
        bundle_service = MockBundleService()
        response_builder = ResponseBuilder(
            node_id=node_info["node_id"],
            node_public_key=node_info["node_public_key"],
            bundle_service=bundle_service,
        )

        # Create query
        query = SearchQuery(
            query_id="query-1",
            query_string="tomatoes",
            requester_node_id="requester-node",
            max_results=50,
            response_deadline=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )

        # Create mock results
        from ..models import QueryResult

        results = [
            QueryResult(
                result_id="listing-1",
                result_type="offer",
                title="Fresh Tomatoes",
                category="food",
                source_node_id=node_info["node_id"],
                source_node_public_key=node_info["node_public_key"],
            )
        ]

        # Build and publish response
        bundle_id = await response_builder.build_and_publish_response(query, results)

        assert bundle_id is not None
        assert len(bundle_service.created_bundles) == 1

        # Check bundle
        bundle = bundle_service.created_bundles[0]
        assert bundle.payloadType == "discovery:response"
        assert bundle.payload["query_id"] == "query-1"
        assert len(bundle.payload["results"]) == 1


@pytest.mark.asyncio
class TestEndToEnd:
    """End-to-end integration tests"""

    async def test_full_discovery_flow(self, discovery_db, node_info):
        """Test complete discovery flow from cache to query to response"""
        # Setup services
        cache_manager = SpeculativeCacheManager(max_cache_mb=10)
        bundle_service = MockBundleService()
        query_handler = QueryHandler(
            node_id=node_info["node_id"],
            node_public_key=node_info["node_public_key"],
        )
        response_builder = ResponseBuilder(
            node_id=node_info["node_id"],
            node_public_key=node_info["node_public_key"],
            bundle_service=bundle_service,
        )

        # Step 1: Cache an index from peer
        now = datetime.utcnow()
        expires = now + timedelta(days=3)

        entry = InventoryIndexEntry(
            listing_id="listing-1",
            listing_type="offer",
            resource_spec_id="tomatoes",
            resource_name="Tomatoes",
            category="food",
            quantity=5.0,
            unit="lbs",
            agent_id="agent-1",
            title="Fresh Garden Tomatoes",
            description="Organic heirloom tomatoes",
        )

        index = InventoryIndex(
            node_id="garden-node",
            node_public_key="-----BEGIN PUBLIC KEY-----\ngarden\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        await cache_manager.cache_index_bundle(
            bundle_id="b:sha256:garden-index",
            payload=index.to_payload(),
        )

        # Step 2: Receive query from another node
        query = SearchQuery(
            query_id="query-tomatoes",
            query_string="tomatoes",
            requester_node_id="kitchen-node",
            max_results=50,
            response_deadline=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )

        # Step 3: Process query (should find cached result)
        results = await query_handler.process_query(query)

        assert len(results) >= 1
        tomato_results = [r for r in results if "tomatoes" in r.title.lower()]
        assert len(tomato_results) >= 1

        # Step 4: Build and publish response
        bundle_id = await response_builder.build_and_publish_response(query, results)

        assert bundle_id is not None
        assert len(bundle_service.created_bundles) == 1

        # Verify response bundle
        bundle = bundle_service.created_bundles[0]
        assert bundle.payload["query_id"] == "query-tomatoes"
        assert bundle.payload["total_results"] >= 1
        assert bundle.payload["includes_cached_results"] is True
