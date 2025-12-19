"""
Unit tests for discovery models
"""

import pytest
from datetime import datetime, timedelta, timezone

from ..models import (
    IndexType,
    InventoryIndex,
    InventoryIndexEntry,
    ServiceIndex,
    ServiceIndexEntry,
    KnowledgeIndex,
    KnowledgeIndexEntry,
    SearchQuery,
    SearchResponse,
    QueryResult,
    QueryFilter,
)


class TestInventoryIndex:
    """Test InventoryIndex model"""

    def test_create_inventory_index(self):
        """Test creating an inventory index"""
        now = datetime.now(timezone.utc)
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
            node_id="node-123",
            node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        assert index.node_id == "node-123"
        assert len(index.entries) == 1
        assert index.total_offers == 1
        assert index.index_type == IndexType.INVENTORY

    def test_inventory_index_serialization(self):
        """Test serializing and deserializing inventory index"""
        now = datetime.now(timezone.utc)
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
            node_id="node-123",
            node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_offers=1,
            total_needs=0,
            categories=["food"],
        )

        # Serialize
        payload = index.to_payload()

        assert payload["index_type"] == "inventory"
        assert payload["node_id"] == "node-123"
        assert len(payload["entries"]) == 1

        # Deserialize
        index2 = InventoryIndex.from_payload(payload)

        assert index2.node_id == index.node_id
        assert len(index2.entries) == len(index.entries)
        assert index2.entries[0].listing_id == entry.listing_id


class TestServiceIndex:
    """Test ServiceIndex model"""

    def test_create_service_index(self):
        """Test creating a service index"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=7)

        entry = ServiceIndexEntry(
            listing_id="service-1",
            service_type="beekeeping",
            skill_name="Beekeeping",
            category="skills",
            agent_id="agent-1",
        )

        index = ServiceIndex(
            node_id="node-123",
            node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_services=1,
            service_types=["beekeeping"],
        )

        assert index.index_type == IndexType.SERVICE
        assert len(index.entries) == 1
        assert index.total_services == 1


class TestKnowledgeIndex:
    """Test KnowledgeIndex model"""

    def test_create_knowledge_index(self):
        """Test creating a knowledge index"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)

        entry = KnowledgeIndexEntry(
            content_id="protocol-1",
            content_type="protocol",
            title="Composting Guide",
            category="agriculture",
        )

        index = KnowledgeIndex(
            node_id="node-123",
            node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            entries=[entry],
            generated_at=now,
            expires_at=expires,
            total_protocols=1,
            total_lessons=0,
            total_files=0,
            categories=["agriculture"],
        )

        assert index.index_type == IndexType.KNOWLEDGE
        assert len(index.entries) == 1


class TestSearchQuery:
    """Test SearchQuery model"""

    def test_create_search_query(self):
        """Test creating a search query"""
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=1)

        query = SearchQuery(
            query_id="query-1",
            query_string="tomatoes",
            requester_node_id="node-123",
            max_results=50,
            response_deadline=deadline,
            created_at=now,
        )

        assert query.query_id == "query-1"
        assert query.query_string == "tomatoes"
        assert query.max_results == 50

    def test_search_query_with_filters(self):
        """Test search query with filters"""
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=1)

        filters = QueryFilter(
            category="food",
            listing_type="offer",
            available_within_hours=24,
        )

        query = SearchQuery(
            query_id="query-1",
            query_string="tomatoes",
            filters=filters,
            requester_node_id="node-123",
            max_results=50,
            response_deadline=deadline,
            created_at=now,
        )

        assert query.filters is not None
        assert query.filters.category == "food"
        assert query.filters.listing_type == "offer"

    def test_search_query_serialization(self):
        """Test serializing and deserializing search query"""
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=1)

        query = SearchQuery(
            query_id="query-1",
            query_string="tomatoes",
            requester_node_id="node-123",
            max_results=50,
            response_deadline=deadline,
            created_at=now,
        )

        # Serialize
        payload = query.to_payload()

        assert payload["query_id"] == "query-1"
        assert payload["query_string"] == "tomatoes"

        # Deserialize
        query2 = SearchQuery.from_payload(payload)

        assert query2.query_id == query.query_id
        assert query2.query_string == query.query_string


class TestSearchResponse:
    """Test SearchResponse model"""

    def test_create_search_response(self):
        """Test creating a search response"""
        now = datetime.now(timezone.utc)

        result = QueryResult(
            result_id="listing-1",
            result_type="offer",
            title="Fresh Tomatoes",
            category="food",
            source_node_id="node-456",
            source_node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
        )

        response = SearchResponse(
            query_id="query-1",
            response_id="resp-1",
            results=[result],
            total_results=1,
            responder_node_id="node-456",
            responder_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            created_at=now,
            local_results=1,
            cached_results=0,
        )

        assert response.query_id == "query-1"
        assert len(response.results) == 1
        assert response.total_results == 1
        assert response.local_results == 1
        assert response.cached_results == 0

    def test_search_response_serialization(self):
        """Test serializing and deserializing search response"""
        now = datetime.now(timezone.utc)

        result = QueryResult(
            result_id="listing-1",
            result_type="offer",
            title="Fresh Tomatoes",
            category="food",
            source_node_id="node-456",
            source_node_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
        )

        response = SearchResponse(
            query_id="query-1",
            response_id="resp-1",
            results=[result],
            total_results=1,
            responder_node_id="node-456",
            responder_public_key="-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----",
            created_at=now,
            local_results=1,
            cached_results=0,
        )

        # Serialize
        payload = response.to_payload()

        assert payload["query_id"] == "query-1"
        assert len(payload["results"]) == 1

        # Deserialize
        response2 = SearchResponse.from_payload(payload)

        assert response2.query_id == response.query_id
        assert len(response2.results) == len(response.results)
