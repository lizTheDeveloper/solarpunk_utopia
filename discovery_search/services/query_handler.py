"""
Query Handler Service

Processes incoming search queries and matches against local data.
Searches both local VF database and cached indexes from peers.
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add paths
app_path = Path(__file__).parent.parent.parent / "app"
vf_path = Path(__file__).parent.parent.parent / "valueflows_node"
sys.path.insert(0, str(app_path))
sys.path.insert(0, str(vf_path))

from ..models import SearchQuery, QueryResult, IndexType
from ..database import get_discovery_db, IndexCacheDB

logger = logging.getLogger(__name__)


class QueryHandler:
    """
    Handles incoming search queries.

    Matches queries against:
    1. Local VF database (listings, protocols, lessons)
    2. Cached indexes from peer nodes
    """

    def __init__(self, node_id: str, node_public_key: str):
        """
        Initialize query handler.

        Args:
            node_id: This node's identifier
            node_public_key: This node's public key
        """
        self.node_id = node_id
        self.node_public_key = node_public_key

    async def process_query(
        self,
        query: SearchQuery,
        search_local: bool = True,
        search_cache: bool = True
    ) -> List[QueryResult]:
        """
        Process a search query and return matching results.

        Args:
            query: Search query to process
            search_local: Search local VF database
            search_cache: Search cached indexes

        Returns:
            List of matching results
        """
        results = []

        try:
            # Record query in history
            await self._record_query(query)

            # Search local data
            if search_local:
                local_results = await self._search_local(query)
                results.extend(local_results)
                logger.info(f"Found {len(local_results)} local results for query {query.query_id}")

            # Search cached indexes
            if search_cache:
                cached_results = await self._search_cached_indexes(query)
                results.extend(cached_results)
                logger.info(f"Found {len(cached_results)} cached results for query {query.query_id}")

            # Limit results
            if len(results) > query.max_results:
                results = results[:query.max_results]

            logger.info(f"Query {query.query_id}: {len(results)} total results")

        except Exception as e:
            logger.error(f"Error processing query {query.query_id}: {e}", exc_info=True)

        return results

    async def _search_local(self, query: SearchQuery) -> List[QueryResult]:
        """
        Search local VF database for matching listings/protocols/lessons.

        Args:
            query: Search query

        Returns:
            List of local results
        """
        results = []

        try:
            from valueflows_node.app.database import get_database
            from valueflows_node.app.repositories.vf.listing_repo import ListingRepository
            from valueflows_node.app.repositories.vf.resource_spec_repo import ResourceSpecRepository
            from valueflows_node.app.repositories.vf.agent_repo import AgentRepository
            from valueflows_node.app.repositories.vf.location_repo import LocationRepository
            from valueflows_node.app.repositories.vf.protocol_repo import ProtocolRepository
            from valueflows_node.app.repositories.vf.lesson_repo import LessonRepository

            db = get_database()
            db.connect()

            # Search listings
            listing_repo = ListingRepository(db.conn)
            resource_spec_repo = ResourceSpecRepository(db.conn)
            agent_repo = AgentRepository(db.conn)
            location_repo = LocationRepository(db.conn)

            # Get all active listings
            listings = listing_repo.find_by_status("active", limit=1000)

            for listing in listings:
                # Check if matches query
                if not self._matches_query(listing, query, "listing"):
                    continue

                # Get additional data
                resource_spec = resource_spec_repo.find_by_id(listing.resource_spec_id)
                if not resource_spec:
                    continue

                agent = agent_repo.find_by_id(listing.agent_id)

                location_name = None
                if listing.location_id:
                    location = location_repo.find_by_id(listing.location_id)
                    if location:
                        location_name = location.name

                # Create result
                result = QueryResult(
                    result_id=listing.id,
                    result_type=listing.listing_type.value,
                    title=listing.title or resource_spec.name,
                    description=listing.description,
                    category=resource_spec.category.value,
                    subcategory=resource_spec.subcategory,
                    source_node_id=self.node_id,
                    source_node_public_key=self.node_public_key,
                    agent_id=listing.agent_id,
                    agent_name=agent.name if agent else None,
                    location_id=listing.location_id,
                    location_name=location_name,
                    quantity=listing.quantity,
                    unit=listing.unit,
                    available_from=listing.available_from,
                    available_until=listing.available_until,
                    bundle_id=None,
                    is_cached=False,
                )

                results.append(result)

            # Search protocols
            protocol_repo = ProtocolRepository(db.conn)
            protocols = protocol_repo.find_all(limit=1000)

            for protocol in protocols:
                if not self._matches_query(protocol, query, "protocol"):
                    continue

                result = QueryResult(
                    result_id=protocol.id,
                    result_type="protocol",
                    title=protocol.name,
                    description=protocol.description if hasattr(protocol, 'description') else None,
                    category=protocol.category if hasattr(protocol, 'category') else "other",
                    source_node_id=self.node_id,
                    source_node_public_key=self.node_public_key,
                    is_cached=False,
                )

                results.append(result)

            # Search lessons
            lesson_repo = LessonRepository(db.conn)
            lessons = lesson_repo.find_all(limit=1000)

            for lesson in lessons:
                if not self._matches_query(lesson, query, "lesson"):
                    continue

                result = QueryResult(
                    result_id=lesson.id,
                    result_type="lesson",
                    title=lesson.title,
                    description=lesson.content[:200] if hasattr(lesson, 'content') and lesson.content else None,
                    category=lesson.category if hasattr(lesson, 'category') else "other",
                    source_node_id=self.node_id,
                    source_node_public_key=self.node_public_key,
                    is_cached=False,
                )

                results.append(result)

            db.close()

        except Exception as e:
            logger.error(f"Error searching local data: {e}", exc_info=True)

        return results

    async def _search_cached_indexes(self, query: SearchQuery) -> List[QueryResult]:
        """
        Search cached indexes from peer nodes.

        Args:
            query: Search query

        Returns:
            List of cached results
        """
        results = []

        try:
            # Get all cached indexes
            inventory_indexes = await IndexCacheDB.get_all_indexes(IndexType.INVENTORY)
            service_indexes = await IndexCacheDB.get_all_indexes(IndexType.SERVICE)
            knowledge_indexes = await IndexCacheDB.get_all_indexes(IndexType.KNOWLEDGE)

            # Search inventory indexes
            for index_data in inventory_indexes:
                for entry in index_data.get("entries", []):
                    if not self._matches_query_dict(entry, query):
                        continue

                    result = QueryResult(
                        result_id=entry["listing_id"],
                        result_type=entry["listing_type"],
                        title=entry.get("title") or entry["resource_name"],
                        description=entry.get("description"),
                        category=entry["category"],
                        subcategory=entry.get("subcategory"),
                        source_node_id=index_data["node_id"],
                        source_node_public_key=index_data["node_public_key"],
                        agent_id=entry["agent_id"],
                        agent_name=entry.get("agent_name"),
                        location_id=entry.get("location_id"),
                        location_name=entry.get("location_name"),
                        quantity=entry["quantity"],
                        unit=entry["unit"],
                        available_from=datetime.fromisoformat(entry["available_from"]) if entry.get("available_from") else None,
                        available_until=datetime.fromisoformat(entry["available_until"]) if entry.get("available_until") else None,
                        bundle_id=entry.get("bundle_id"),
                        is_cached=True,
                        cached_at=datetime.fromisoformat(index_data["cached_at"]),
                    )

                    results.append(result)

            # Search service indexes
            for index_data in service_indexes:
                for entry in index_data.get("entries", []):
                    if not self._matches_query_dict(entry, query):
                        continue

                    result = QueryResult(
                        result_id=entry["listing_id"],
                        result_type="service",
                        title=entry.get("title") or entry["skill_name"],
                        description=entry.get("description"),
                        category=entry["category"],
                        source_node_id=index_data["node_id"],
                        source_node_public_key=index_data["node_public_key"],
                        agent_id=entry["agent_id"],
                        agent_name=entry.get("agent_name"),
                        location_id=entry.get("location_id"),
                        location_name=entry.get("location_name"),
                        is_cached=True,
                        cached_at=datetime.fromisoformat(index_data["cached_at"]),
                    )

                    results.append(result)

            # Search knowledge indexes
            for index_data in knowledge_indexes:
                for entry in index_data.get("entries", []):
                    if not self._matches_query_dict(entry, query):
                        continue

                    result = QueryResult(
                        result_id=entry["content_id"],
                        result_type=entry["content_type"],
                        title=entry["title"],
                        description=entry.get("description"),
                        category=entry["category"],
                        source_node_id=index_data["node_id"],
                        source_node_public_key=index_data["node_public_key"],
                        is_cached=True,
                        cached_at=datetime.fromisoformat(index_data["cached_at"]),
                    )

                    results.append(result)

        except Exception as e:
            logger.error(f"Error searching cached indexes: {e}", exc_info=True)

        return results

    def _matches_query(self, obj: any, query: SearchQuery, obj_type: str) -> bool:
        """
        Check if an object matches the query.

        Args:
            obj: Object to check (listing, protocol, lesson)
            query: Search query
            obj_type: Type of object ("listing", "protocol", "lesson")

        Returns:
            True if matches
        """
        query_lower = query.query_string.lower()

        # Check text match
        if obj_type == "listing":
            text = f"{obj.title or ''} {obj.description or ''}".lower()
        elif obj_type == "protocol":
            text = f"{obj.name or ''} {getattr(obj, 'description', '') or ''}".lower()
        elif obj_type == "lesson":
            text = f"{obj.title or ''} {getattr(obj, 'content', '') or ''}".lower()
        else:
            text = ""

        if query_lower not in text:
            return False

        # Apply filters if present
        if query.filters:
            # Category filter
            if query.filters.category:
                obj_category = getattr(obj, 'category', None)
                if hasattr(obj_category, 'value'):
                    obj_category = obj_category.value
                if obj_category != query.filters.category:
                    return False

            # Listing type filter
            if query.filters.listing_type and obj_type == "listing":
                if obj.listing_type.value != query.filters.listing_type:
                    return False

        return True

    def _matches_query_dict(self, entry: dict, query: SearchQuery) -> bool:
        """Check if a dictionary entry matches the query"""
        query_lower = query.query_string.lower()

        # Check text match
        text = f"{entry.get('title', '')} {entry.get('description', '')} {entry.get('resource_name', '')} {entry.get('skill_name', '')}".lower()

        if query_lower not in text:
            return False

        # Apply filters
        if query.filters:
            # Category filter
            if query.filters.category and entry.get("category") != query.filters.category:
                return False

            # Listing type filter
            if query.filters.listing_type and entry.get("listing_type") != query.filters.listing_type:
                return False

        return True

    async def _record_query(self, query: SearchQuery):
        """Record query in history database"""
        try:
            db = await get_discovery_db()

            await db.execute("""
                INSERT OR IGNORE INTO query_history (
                    query_id, query_string, query_data,
                    requester_node_id, requester_agent_id,
                    created_at, response_deadline, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query.query_id,
                query.query_string,
                json.dumps(query.to_payload()),
                query.requester_node_id,
                query.requester_agent_id,
                query.created_at.isoformat(),
                query.response_deadline.isoformat(),
                "pending",
            ))

            await db.commit()

        except Exception as e:
            logger.error(f"Error recording query: {e}")
