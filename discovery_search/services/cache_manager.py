"""
Speculative Cache Manager

Manages the cache of peer indexes for offline discovery.
Bridge nodes cache indexes from visited nodes and use them to answer queries.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from ..models import IndexType, InventoryIndex, ServiceIndex, KnowledgeIndex
from ..database import IndexCacheDB

logger = logging.getLogger(__name__)


class SpeculativeCacheManager:
    """
    Manages speculative caching of peer indexes.

    Responsibilities:
    - Store received index bundles
    - Manage cache freshness
    - Evict stale indexes
    - Enforce cache budget
    """

    def __init__(self, max_cache_mb: int = 100):
        """
        Initialize cache manager.

        Args:
            max_cache_mb: Maximum cache size in MB
        """
        self.max_cache_bytes = max_cache_mb * 1024 * 1024

    async def cache_index_bundle(
        self,
        bundle_id: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Cache an index bundle from a peer node.

        Args:
            bundle_id: Bundle identifier
            payload: Index bundle payload

        Returns:
            True if cached successfully
        """
        try:
            # Determine index type
            index_type_str = payload.get("index_type")
            if not index_type_str:
                logger.warning(f"Bundle {bundle_id} has no index_type")
                return False

            index_type = IndexType(index_type_str)

            # Parse index based on type
            if index_type == IndexType.INVENTORY:
                index = InventoryIndex.from_payload(payload)
            elif index_type == IndexType.SERVICE:
                index = ServiceIndex.from_payload(payload)
            elif index_type == IndexType.KNOWLEDGE:
                index = KnowledgeIndex.from_payload(payload)
            else:
                logger.warning(f"Unknown index type: {index_type}")
                return False

            # Check if index is expired
            if datetime.utcnow() > index.expires_at:
                logger.info(f"Not caching expired index from {index.node_id}")
                return False

            # Calculate size
            import json
            size_bytes = len(json.dumps(payload).encode('utf-8'))

            # Check cache budget before storing
            await self._enforce_cache_budget(size_bytes)

            # Store in cache
            await IndexCacheDB.store_index(
                index_type=index_type,
                node_id=index.node_id,
                node_public_key=index.node_public_key,
                bundle_id=bundle_id,
                index_data=payload,
                generated_at=index.generated_at,
                expires_at=index.expires_at,
                entry_count=len(index.entries),
                size_bytes=size_bytes,
            )

            logger.info(
                f"Cached {index_type.value} index from {index.node_id}: "
                f"{len(index.entries)} entries, {size_bytes} bytes"
            )

            return True

        except Exception as e:
            logger.error(f"Error caching index bundle {bundle_id}: {e}", exc_info=True)
            return False

    async def get_cached_index(
        self,
        node_id: str,
        index_type: IndexType
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached index.

        Args:
            node_id: Node identifier
            index_type: Type of index

        Returns:
            Index data or None if not found/expired
        """
        try:
            return await IndexCacheDB.get_index(node_id, index_type)
        except Exception as e:
            logger.error(f"Error retrieving cached index: {e}")
            return None

    async def evict_stale_indexes(self, max_age_hours: int = 24) -> int:
        """
        Evict indexes older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of indexes evicted
        """
        try:
            count = await IndexCacheDB.evict_stale_indexes(max_age_hours)
            if count > 0:
                logger.info(f"Evicted {count} stale indexes")
            return count
        except Exception as e:
            logger.error(f"Error evicting stale indexes: {e}")
            return 0

    async def _enforce_cache_budget(self, new_bytes: int):
        """
        Enforce cache budget by evicting oldest entries if necessary.

        Args:
            new_bytes: Size of new index to be added
        """
        try:
            stats = await IndexCacheDB.get_cache_stats()
            current_bytes = stats.get("total_bytes", 0)

            # Check if we need to evict
            if current_bytes + new_bytes > self.max_cache_bytes:
                bytes_to_free = (current_bytes + new_bytes) - self.max_cache_bytes
                logger.info(
                    f"Cache budget exceeded: {current_bytes + new_bytes} > {self.max_cache_bytes}. "
                    f"Need to free {bytes_to_free} bytes"
                )

                # For now, just evict stale indexes
                # TODO: Implement LRU eviction if needed
                await self.evict_stale_indexes(max_age_hours=12)

        except Exception as e:
            logger.error(f"Error enforcing cache budget: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            stats = await IndexCacheDB.get_cache_stats()

            # Add budget information
            stats["max_cache_bytes"] = self.max_cache_bytes
            stats["max_cache_mb"] = self.max_cache_bytes / (1024 * 1024)

            current_bytes = stats.get("total_bytes", 0)
            stats["usage_percent"] = (current_bytes / self.max_cache_bytes * 100) if self.max_cache_bytes > 0 else 0
            stats["is_over_budget"] = current_bytes > self.max_cache_bytes

            return stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

    async def clear_cache(self) -> int:
        """
        Clear all cached indexes.

        Returns:
            Number of indexes cleared
        """
        try:
            count = await IndexCacheDB.clear_cache()
            logger.info(f"Cleared {count} cached indexes")
            return count
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def should_cache_index(self, bundle_payload: Dict[str, Any]) -> bool:
        """
        Determine if an index bundle should be cached.

        Args:
            bundle_payload: Index bundle payload

        Returns:
            True if should cache
        """
        # Always cache indexes speculatively
        # This enables bridge nodes to answer queries for disconnected nodes

        # Check if index is expired
        expires_at_str = bundle_payload.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.utcnow() > expires_at:
                return False

        return True
