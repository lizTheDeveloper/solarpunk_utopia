"""
Discovery and Search API Endpoints

Provides REST API for:
- Creating search queries
- Retrieving query results
- Managing indexes
- Cache statistics
"""

import sys
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

# Add app to path
app_path = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_path))

from ..models import (
    IndexType,
    SearchQuery,
    QueryFilter,
    QueryResult,
)
from ..services import (
    IndexBuilder,
    IndexPublisher,
    QueryHandler,
    ResponseBuilder,
    SpeculativeCacheManager,
)
from ..database import IndexCacheDB

router = APIRouter(prefix="/discovery", tags=["discovery"])


# Request/Response models for API
class SearchRequest(BaseModel):
    """Request model for creating a search query"""
    query: str
    filters: Optional[QueryFilter] = None
    max_results: int = 50
    timeout_minutes: int = 60


class SearchResultResponse(BaseModel):
    """Response model for search results"""
    query_id: str
    query: str
    results: List[QueryResult]
    total_results: int
    local_results: int
    cached_results: int
    status: str


class IndexPublishRequest(BaseModel):
    """Request model for manual index publishing"""
    index_type: Optional[IndexType] = None


# Dependency injection - these will be initialized at startup
_index_publisher: Optional[IndexPublisher] = None
_query_handler: Optional[QueryHandler] = None
_response_builder: Optional[ResponseBuilder] = None
_cache_manager: Optional[SpeculativeCacheManager] = None


def get_services():
    """Get initialized services"""
    global _index_publisher, _query_handler, _response_builder, _cache_manager

    if not _query_handler:
        raise HTTPException(status_code=503, detail="Discovery services not initialized")

    return {
        "publisher": _index_publisher,
        "query_handler": _query_handler,
        "response_builder": _response_builder,
        "cache_manager": _cache_manager,
    }


def init_discovery_services(
    node_id: str,
    node_public_key: str,
    bundle_service,
):
    """
    Initialize discovery services.

    Should be called during app startup.
    """
    global _index_publisher, _query_handler, _response_builder, _cache_manager

    _index_publisher = IndexPublisher(node_id, node_public_key, bundle_service)
    _query_handler = QueryHandler(node_id, node_public_key)
    _response_builder = ResponseBuilder(node_id, node_public_key, bundle_service)
    _cache_manager = SpeculativeCacheManager(max_cache_mb=100)


@router.post("/search", response_model=SearchResultResponse)
async def create_search(request: SearchRequest):
    """
    Create a new search query.

    The query will be published to the DTN network and processed by all nodes.
    Results from local data and cached indexes will be returned immediately.
    Additional results from remote nodes will arrive asynchronously.
    """
    services = get_services()
    query_handler = services["query_handler"]
    response_builder = services["response_builder"]

    try:
        # Generate query ID
        query_id = f"query:{uuid.uuid4()}"

        # Create search query
        query = SearchQuery(
            query_id=query_id,
            query_string=request.query,
            filters=request.filters,
            requester_node_id=query_handler.node_id,
            max_results=request.max_results,
            response_deadline=datetime.now(timezone.utc) + timedelta(minutes=request.timeout_minutes),
            created_at=datetime.now(timezone.utc),
        )

        # Process query locally
        results = await query_handler.process_query(query)

        # Build and publish response if we have results
        if results:
            await response_builder.build_and_publish_response(query, results)

        # Also publish query bundle for propagation to other nodes
        from app.models import BundleCreate, Topic, Priority, Audience
        from app.services import BundleService, CryptoService

        crypto_service = CryptoService()
        bundle_service = BundleService(crypto_service)

        bundle_create = BundleCreate(
            payload=query.to_payload(),
            payloadType="discovery:query",
            priority=Priority.NORMAL,
            audience=Audience.PUBLIC,
            topic=Topic.INVENTORY,
            tags=["discovery", "query"],
            hopLimit=10,
            expiresAt=query.response_deadline,
        )

        await bundle_service.create_bundle(bundle_create)

        # Count result types
        local_results = sum(1 for r in results if not r.is_cached)
        cached_results = sum(1 for r in results if r.is_cached)

        return SearchResultResponse(
            query_id=query_id,
            query=request.query,
            results=results,
            total_results=len(results),
            local_results=local_results,
            cached_results=cached_results,
            status="completed" if results else "pending",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/{query_id}/responses")
async def get_query_responses(query_id: str):
    """
    Get all responses for a query.

    Returns responses that have arrived from remote nodes.
    """
    services = get_services()
    response_builder = services["response_builder"]

    try:
        responses = await response_builder.get_query_responses(query_id)
        return {
            "query_id": query_id,
            "response_count": len(responses),
            "responses": responses,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get responses: {str(e)}")


@router.post("/indexes/publish", response_model=dict)
async def publish_indexes(request: IndexPublishRequest):
    """
    Manually trigger index publishing.

    If index_type is specified, only that type will be published.
    Otherwise, all index types will be published.
    """
    services = get_services()
    publisher = services["publisher"]

    if not publisher:
        raise HTTPException(status_code=503, detail="Index publisher not initialized")

    try:
        await publisher.publish_now(request.index_type)

        return {
            "status": "success",
            "message": f"Published {request.index_type.value if request.index_type else 'all'} indexes"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


@router.get("/indexes/stats")
async def get_index_stats():
    """Get statistics about index publishing"""
    services = get_services()
    publisher = services["publisher"]

    if not publisher:
        raise HTTPException(status_code=503, detail="Index publisher not initialized")

    try:
        stats = await publisher.get_publish_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    services = get_services()
    cache_manager = services["cache_manager"]

    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not initialized")

    try:
        stats = await cache_manager.get_cache_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/evict")
async def evict_stale_cache(max_age_hours: int = 24):
    """
    Evict stale cached indexes.

    Args:
        max_age_hours: Maximum age of indexes to keep
    """
    services = get_services()
    cache_manager = services["cache_manager"]

    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not initialized")

    try:
        count = await cache_manager.evict_stale_indexes(max_age_hours)
        return {
            "status": "success",
            "evicted_count": count,
            "max_age_hours": max_age_hours,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eviction failed: {str(e)}")


@router.delete("/cache")
async def clear_cache():
    """Clear all cached indexes"""
    services = get_services()
    cache_manager = services["cache_manager"]

    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not initialized")

    try:
        count = await cache_manager.clear_cache()
        return {
            "status": "success",
            "cleared_count": count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")


@router.get("/cache/indexes")
async def list_cached_indexes(index_type: Optional[IndexType] = None):
    """
    List all cached indexes.

    Args:
        index_type: Filter by index type (optional)
    """
    try:
        indexes = await IndexCacheDB.get_all_indexes(index_type, exclude_expired=True)
        return {
            "total_indexes": len(indexes),
            "index_type": index_type.value if index_type else "all",
            "indexes": indexes,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list indexes: {str(e)}")


@router.get("/stats")
async def get_discovery_stats():
    """Get overall discovery system statistics"""
    services = get_services()

    try:
        cache_stats = await services["cache_manager"].get_cache_stats()
        publish_stats = await services["publisher"].get_publish_stats()
        response_stats = await services["response_builder"].get_response_stats()

        return {
            "cache": cache_stats,
            "publishing": publish_stats,
            "responses": response_stats,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
