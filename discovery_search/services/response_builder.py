"""
Response Builder Service

Creates response bundles for queries and publishes them to DTN network.
"""

import sys
import logging
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List

# Add app to path
app_path = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_path))

from ..models import SearchQuery, SearchResponse, QueryResult
from ..database import get_discovery_db

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """
    Builds and publishes search response bundles.

    Creates responses for queries with matching results.
    """

    def __init__(self, node_id: str, node_public_key: str, bundle_service):
        """
        Initialize response builder.

        Args:
            node_id: This node's identifier
            node_public_key: This node's public key
            bundle_service: BundleService for publishing responses
        """
        self.node_id = node_id
        self.node_public_key = node_public_key
        self.bundle_service = bundle_service

    async def build_and_publish_response(
        self,
        query: SearchQuery,
        results: List[QueryResult]
    ) -> str:
        """
        Build a response bundle and publish it to DTN network.

        Args:
            query: Original search query
            results: Matching results to include

        Returns:
            Bundle ID of published response
        """
        from app.models import BundleCreate, Topic, Priority, Audience

        try:
            # Generate response ID
            response_id = f"resp:{uuid.uuid4()}"

            # Count result types
            local_results = sum(1 for r in results if not r.is_cached)
            cached_results = sum(1 for r in results if r.is_cached)

            # Create response
            response = SearchResponse(
                query_id=query.query_id,
                response_id=response_id,
                results=results,
                total_results=len(results),
                responder_node_id=self.node_id,
                responder_public_key=self.node_public_key,
                created_at=datetime.utcnow(),
                includes_cached_results=(cached_results > 0),
                local_results=local_results,
                cached_results=cached_results,
            )

            # Convert to bundle payload
            payload = response.to_payload()

            # Create bundle
            bundle_create = BundleCreate(
                payload=payload,
                payloadType="discovery:response",
                priority=Priority.NORMAL,
                audience=Audience.PUBLIC,
                topic=Topic.INVENTORY,
                tags=["discovery", "response", query.query_id],
                hopLimit=20,
            )

            bundle = await self.bundle_service.create_bundle(bundle_create)

            logger.info(
                f"Published response {response_id} for query {query.query_id}: "
                f"{len(results)} results ({local_results} local, {cached_results} cached)"
            )

            # Record response in database
            await self._record_response(response, bundle.bundleId)

            # Update query history
            await self._update_query_history(query.query_id, len(results))

            return bundle.bundleId

        except Exception as e:
            logger.error(f"Error building response for query {query.query_id}: {e}", exc_info=True)
            raise

    async def _record_response(self, response: SearchResponse, bundle_id: str):
        """Record response in database"""
        try:
            db = await get_discovery_db()

            await db.execute("""
                INSERT INTO response_tracking (
                    response_id, query_id, responder_node_id,
                    response_data, created_at, received_at,
                    result_count, local_results, cached_results
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                response.response_id,
                response.query_id,
                response.responder_node_id,
                json.dumps(response.to_payload()),
                response.created_at.isoformat(),
                datetime.utcnow().isoformat(),
                response.total_results,
                response.local_results,
                response.cached_results,
            ))

            await db.commit()

        except Exception as e:
            logger.error(f"Error recording response: {e}")

    async def _update_query_history(self, query_id: str, result_count: int):
        """Update query history with response"""
        try:
            db = await get_discovery_db()

            await db.execute("""
                UPDATE query_history
                SET responses_received = responses_received + 1,
                    total_results = total_results + ?
                WHERE query_id = ?
            """, (result_count, query_id))

            await db.commit()

        except Exception as e:
            logger.error(f"Error updating query history: {e}")

    async def get_query_responses(self, query_id: str) -> List[dict]:
        """
        Get all responses for a query.

        Args:
            query_id: Query identifier

        Returns:
            List of response data
        """
        try:
            db = await get_discovery_db()

            cursor = await db.execute("""
                SELECT response_data, created_at, result_count,
                       local_results, cached_results, responder_node_id
                FROM response_tracking
                WHERE query_id = ?
                ORDER BY created_at ASC
            """, (query_id,))

            rows = await cursor.fetchall()

            responses = []
            for row in rows:
                response_data = json.loads(row["response_data"])
                response_data["db_created_at"] = row["created_at"]
                response_data["result_count"] = row["result_count"]
                responses.append(response_data)

            return responses

        except Exception as e:
            logger.error(f"Error getting query responses: {e}")
            return []

    async def get_response_stats(self) -> dict:
        """Get statistics about responses"""
        try:
            db = await get_discovery_db()

            # Total responses
            cursor = await db.execute("""
                SELECT COUNT(*) as total_responses,
                       SUM(result_count) as total_results,
                       SUM(local_results) as total_local,
                       SUM(cached_results) as total_cached
                FROM response_tracking
            """)

            row = await cursor.fetchone()

            stats = {
                "total_responses": row["total_responses"] or 0,
                "total_results": row["total_results"] or 0,
                "total_local_results": row["total_local"] or 0,
                "total_cached_results": row["total_cached"] or 0,
            }

            # Recent responses
            cursor = await db.execute("""
                SELECT COUNT(*) as recent_count
                FROM response_tracking
                WHERE created_at > datetime('now', '-24 hours')
            """)

            row = await cursor.fetchone()
            stats["responses_last_24h"] = row["recent_count"] or 0

            return stats

        except Exception as e:
            logger.error(f"Error getting response stats: {e}")
            return {}
