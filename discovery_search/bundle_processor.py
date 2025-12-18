"""
Bundle Processor for Discovery System

Processes incoming DTN bundles related to discovery:
- Index bundles (cache speculatively)
- Query bundles (process and respond)
- Response bundles (aggregate results)
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add app to path
app_path = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_path))

from .models import SearchQuery, SearchResponse
from .services import (
    QueryHandler,
    ResponseBuilder,
    SpeculativeCacheManager,
)

logger = logging.getLogger(__name__)


class DiscoveryBundleProcessor:
    """
    Processes discovery-related bundles from DTN inbox.

    Should be integrated with the DTN bundle receiver to handle
    incoming index, query, and response bundles.
    """

    def __init__(
        self,
        query_handler: QueryHandler,
        response_builder: ResponseBuilder,
        cache_manager: SpeculativeCacheManager,
    ):
        """
        Initialize bundle processor.

        Args:
            query_handler: Query processing service
            response_builder: Response building service
            cache_manager: Index caching service
        """
        self.query_handler = query_handler
        self.response_builder = response_builder
        self.cache_manager = cache_manager

    async def process_bundle(self, bundle) -> bool:
        """
        Process a received bundle.

        Args:
            bundle: Bundle object from DTN inbox

        Returns:
            True if bundle was processed
        """
        payload_type = bundle.payloadType

        try:
            # Index bundles
            if payload_type.startswith("discovery:index:"):
                await self._process_index_bundle(bundle)
                return True

            # Query bundles
            elif payload_type == "discovery:query":
                await self._process_query_bundle(bundle)
                return True

            # Response bundles
            elif payload_type == "discovery:response":
                await self._process_response_bundle(bundle)
                return True

            # Not a discovery bundle
            return False

        except Exception as e:
            logger.error(f"Error processing discovery bundle {bundle.bundleId}: {e}", exc_info=True)
            return False

    async def _process_index_bundle(self, bundle):
        """
        Process an index bundle.

        Caches the index speculatively for answering future queries.
        """
        try:
            payload = bundle.payload

            # Check if we should cache this index
            if await self.cache_manager.should_cache_index(payload):
                await self.cache_manager.cache_index_bundle(
                    bundle_id=bundle.bundleId,
                    payload=payload,
                )
                logger.info(f"Cached index bundle {bundle.bundleId}")
            else:
                logger.debug(f"Skipped caching index bundle {bundle.bundleId}")

        except Exception as e:
            logger.error(f"Error processing index bundle: {e}", exc_info=True)

    async def _process_query_bundle(self, bundle):
        """
        Process a query bundle.

        Matches query against local data and cached indexes,
        then publishes response if matches found.
        """
        try:
            payload = bundle.payload

            # Parse query
            query = SearchQuery.from_payload(payload)

            logger.info(f"Processing query {query.query_id}: '{query.query_string}'")

            # Process query
            results = await self.query_handler.process_query(query)

            # If we have results, build and publish response
            if results:
                await self.response_builder.build_and_publish_response(query, results)
                logger.info(f"Published response for query {query.query_id}: {len(results)} results")
            else:
                logger.info(f"No results for query {query.query_id}")

        except Exception as e:
            logger.error(f"Error processing query bundle: {e}", exc_info=True)

    async def _process_response_bundle(self, bundle):
        """
        Process a response bundle.

        Aggregates results for queries we initiated.
        """
        try:
            payload = bundle.payload

            # Parse response
            response = SearchResponse.from_payload(payload)

            logger.info(
                f"Received response {response.response_id} for query {response.query_id}: "
                f"{response.total_results} results from {response.responder_node_id}"
            )

            # TODO: Store response for query initiator to retrieve
            # For now, just log it

        except Exception as e:
            logger.error(f"Error processing response bundle: {e}", exc_info=True)


async def process_inbox_bundles(
    query_handler: QueryHandler,
    response_builder: ResponseBuilder,
    cache_manager: SpeculativeCacheManager,
):
    """
    Process all discovery bundles in DTN inbox.

    This function should be called periodically or on bundle receipt.
    """
    from app.database import QueueManager
    from app.models import QueueName

    processor = DiscoveryBundleProcessor(
        query_handler,
        response_builder,
        cache_manager,
    )

    try:
        # Get bundles from inbox
        bundles = await QueueManager.list_queue(QueueName.INBOX, limit=100)

        for bundle in bundles:
            # Process if it's a discovery bundle
            await processor.process_bundle(bundle)

    except Exception as e:
        logger.error(f"Error processing inbox bundles: {e}", exc_info=True)
