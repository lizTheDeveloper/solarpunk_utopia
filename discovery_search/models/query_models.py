"""
Query and Response Models for Discovery System

Defines the query/response protocol for distributed search.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class QueryFilter(BaseModel):
    """
    Filters for search queries.

    Allows structured filtering of search results.
    """
    # Category filters
    category: Optional[str] = None  # e.g., "food", "skills"
    subcategory: Optional[str] = None

    # Type filters
    listing_type: Optional[str] = None  # "offer" or "need"
    content_type: Optional[str] = None  # "protocol", "lesson", "file"

    # Location filters
    location_id: Optional[str] = None
    location_name: Optional[str] = None

    # Time filters
    available_within_hours: Optional[int] = None  # Must be available within N hours
    available_after: Optional[datetime] = None
    available_before: Optional[datetime] = None

    # Quantity filters
    min_quantity: Optional[float] = None
    max_quantity: Optional[float] = None

    # Tags
    tags: List[str] = Field(default_factory=list)


class SearchQuery(BaseModel):
    """
    Search query bundle payload.

    Represents a distributed search request that propagates through the mesh.
    """
    query_id: str  # Unique identifier for this query
    query_string: str  # Free-text search string (e.g., "tomatoes")
    filters: Optional[QueryFilter] = None

    # Requester info
    requester_node_id: str  # Node that initiated query
    requester_agent_id: Optional[str] = None  # User who initiated query

    # Query parameters
    max_results: int = 50  # Maximum results to return
    response_deadline: datetime  # When responses should stop being sent

    # Query metadata
    created_at: datetime
    hop_count: int = 0  # Tracks propagation distance

    def to_payload(self) -> Dict[str, Any]:
        """Convert to bundle payload format"""
        return {
            "query_id": self.query_id,
            "query_string": self.query_string,
            "filters": self.filters.model_dump(mode='json') if self.filters else None,
            "requester_node_id": self.requester_node_id,
            "requester_agent_id": self.requester_agent_id,
            "max_results": self.max_results,
            "response_deadline": self.response_deadline.isoformat(),
            "created_at": self.created_at.isoformat(),
            "hop_count": self.hop_count,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SearchQuery":
        """Create from bundle payload"""
        return cls(
            query_id=payload["query_id"],
            query_string=payload["query_string"],
            filters=QueryFilter(**payload["filters"]) if payload.get("filters") else None,
            requester_node_id=payload["requester_node_id"],
            requester_agent_id=payload.get("requester_agent_id"),
            max_results=payload.get("max_results", 50),
            response_deadline=datetime.fromisoformat(payload["response_deadline"]),
            created_at=datetime.fromisoformat(payload["created_at"]),
            hop_count=payload.get("hop_count", 0),
        )


class QueryResult(BaseModel):
    """
    Single result in a search response.

    Contains preview data and bundle reference for full object.
    """
    # Result identification
    result_id: str  # listing_id, content_id, etc.
    result_type: str  # "offer", "need", "service", "protocol", "lesson", "file"

    # Preview data
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None

    # Source
    source_node_id: str  # Node that has this data
    source_node_public_key: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

    # Location
    location_id: Optional[str] = None
    location_name: Optional[str] = None

    # Quantity (if applicable)
    quantity: Optional[float] = None
    unit: Optional[str] = None

    # Availability (if applicable)
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Bundle reference for full data
    bundle_id: Optional[str] = None

    # Result metadata
    relevance_score: float = 1.0  # For ranking (future use)
    is_cached: bool = False  # True if from speculative cache
    cached_at: Optional[datetime] = None  # When it was cached


class SearchResponse(BaseModel):
    """
    Search response bundle payload.

    Contains results for a specific query.
    """
    query_id: str  # References original query
    response_id: str  # Unique identifier for this response

    # Results
    results: List[QueryResult] = Field(default_factory=list)
    total_results: int = 0  # Total matching results (may be truncated)

    # Source
    responder_node_id: str  # Node sending this response
    responder_public_key: str

    # Response metadata
    created_at: datetime
    includes_cached_results: bool = False  # True if any results are from cache

    # Statistics
    local_results: int = 0  # Results from local data
    cached_results: int = 0  # Results from speculative cache

    def to_payload(self) -> Dict[str, Any]:
        """Convert to bundle payload format"""
        return {
            "query_id": self.query_id,
            "response_id": self.response_id,
            "results": [result.model_dump(mode='json') for result in self.results],
            "total_results": self.total_results,
            "responder_node_id": self.responder_node_id,
            "responder_public_key": self.responder_public_key,
            "created_at": self.created_at.isoformat(),
            "includes_cached_results": self.includes_cached_results,
            "local_results": self.local_results,
            "cached_results": self.cached_results,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "SearchResponse":
        """Create from bundle payload"""
        return cls(
            query_id=payload["query_id"],
            response_id=payload["response_id"],
            results=[QueryResult(**result) for result in payload["results"]],
            total_results=payload.get("total_results", 0),
            responder_node_id=payload["responder_node_id"],
            responder_public_key=payload["responder_public_key"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            includes_cached_results=payload.get("includes_cached_results", False),
            local_results=payload.get("local_results", 0),
            cached_results=payload.get("cached_results", 0),
        )
