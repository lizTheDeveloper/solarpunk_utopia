import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..models import Priority, QueueName
from ..database import QueueManager
from ..database.db import get_db

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache budget manager for storage enforcement.

    Enforces storage budgets by:
    1. Tracking total cache size
    2. Evicting bundles when budget exceeded
    3. Following eviction policy: expired → low priority → oldest

    Budget management:
    - Warn at 95% capacity
    - Start eviction at 95% capacity
    - Reject new bundles at 100% capacity
    """

    def __init__(self, storage_budget_bytes: int = 2 * 1024 * 1024 * 1024):
        """
        Initialize cache service.

        Args:
            storage_budget_bytes: Maximum cache size in bytes (default: 2GB)
        """
        self.storage_budget_bytes = storage_budget_bytes
        self.warn_threshold = 0.95  # 95%
        self.evict_threshold = 0.95  # Start evicting at 95%
        self._cache_lock = asyncio.Lock()  # Lock to prevent race conditions

    async def get_current_cache_size(self) -> int:
        """Get current total cache size in bytes"""
        return await QueueManager.get_total_cache_size()

    async def get_cache_usage_percentage(self) -> float:
        """Get cache usage as percentage"""
        current_size = await self.get_current_cache_size()
        return (current_size / self.storage_budget_bytes) * 100

    async def is_over_budget(self) -> bool:
        """Check if cache is over budget"""
        current_size = await self.get_current_cache_size()
        return current_size >= self.storage_budget_bytes

    async def is_near_budget(self) -> bool:
        """Check if cache is near budget (95%)"""
        current_size = await self.get_current_cache_size()
        threshold = self.storage_budget_bytes * self.warn_threshold
        return current_size >= threshold

    async def enforce_budget(self) -> int:
        """
        Enforce storage budget by evicting bundles.

        Eviction policy:
        1. Delete expired bundles first
        2. Delete low-priority bundles
        3. Delete oldest bundles of same priority

        Returns:
            Number of bundles evicted
        """
        # Use lock to prevent race conditions during eviction
        async with self._cache_lock:
            return await self._enforce_budget_internal()

    async def can_accept_bundle(self, bundle_size_bytes: int) -> bool:
        """
        Check if we can accept a new bundle given its size.

        Args:
            bundle_size_bytes: Size of bundle to accept

        Returns:
            True if we have space, False otherwise
        """
        # Use lock to prevent race conditions when checking and evicting
        async with self._cache_lock:
            current_size = await self.get_current_cache_size()
            new_size = current_size + bundle_size_bytes

            if new_size > self.storage_budget_bytes:
                # Try to make space by evicting (will acquire lock, but we already have it)
                # So we need to call the internal logic without the lock
                evicted_count = await self._enforce_budget_internal()

                # Check again
                current_size = await self.get_current_cache_size()
                new_size = current_size + bundle_size_bytes

                return new_size <= self.storage_budget_bytes

            return True

    async def _enforce_budget_internal(self) -> int:
        """
        Internal enforce budget without acquiring lock (caller must hold lock).
        """
        if not await self.is_near_budget():
            return 0

        evicted_count = 0
        target_size = self.storage_budget_bytes * 0.90  # Target 90% after eviction

        # Step 1: Delete expired bundles
        expired_bundles = await QueueManager.list_queue(QueueName.EXPIRED, limit=1000)
        for bundle in expired_bundles:
            await QueueManager.delete(bundle.bundleId)
            evicted_count += 1

            current_size = await self.get_current_cache_size()
            if current_size <= target_size:
                logger.info(f"Cache budget enforced: evicted {evicted_count} bundles")
                return evicted_count

        # Step 2: Delete low-priority bundles (oldest first)
        low_priority_bundles = await self._get_oldest_bundles_by_priority(
            Priority.LOW,
            limit=1000
        )
        for bundle in low_priority_bundles:
            # Don't delete from outbox (locally created, not yet sent)
            db_queue = await self._get_bundle_queue(bundle.bundleId)
            if db_queue != QueueName.OUTBOX:
                await QueueManager.delete(bundle.bundleId)
                evicted_count += 1

                current_size = await self.get_current_cache_size()
                if current_size <= target_size:
                    logger.info(f"Cache budget enforced: evicted {evicted_count} bundles")
                    return evicted_count

        # Step 3: Delete oldest normal-priority bundles
        normal_priority_bundles = await self._get_oldest_bundles_by_priority(
            Priority.NORMAL,
            limit=1000
        )
        for bundle in normal_priority_bundles:
            db_queue = await self._get_bundle_queue(bundle.bundleId)
            if db_queue not in [QueueName.OUTBOX, QueueName.PENDING]:
                await QueueManager.delete(bundle.bundleId)
                evicted_count += 1

                current_size = await self.get_current_cache_size()
                if current_size <= target_size:
                    logger.info(f"Cache budget enforced: evicted {evicted_count} bundles")
                    return evicted_count

        logger.info(f"Cache budget enforced: evicted {evicted_count} bundles")
        return evicted_count

    async def _get_oldest_bundles_by_priority(
        self,
        priority: Priority,
        limit: int = 100
    ) -> list:
        """Get oldest bundles of a specific priority"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT * FROM bundles
            WHERE priority = ?
            ORDER BY createdAt ASC
            LIMIT ?
        """, (priority.value, limit))

        rows = await cursor.fetchall()
        from ..database.queues import QueueManager
        return [QueueManager._row_to_bundle(row) for row in rows]

    async def _get_bundle_queue(self, bundle_id: str) -> Optional[QueueName]:
        """Get the queue a bundle is currently in"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT queue FROM bundles WHERE bundleId = ?
        """, (bundle_id,))
        row = await cursor.fetchone()
        return QueueName(row['queue']) if row else None

    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        current_size = await self.get_current_cache_size()
        usage_pct = await self.get_cache_usage_percentage()

        # Count bundles per queue
        queue_counts = {}
        for queue in QueueName:
            count = await QueueManager.count_queue(queue)
            queue_counts[queue.value] = count

        return {
            'current_size_bytes': current_size,
            'budget_bytes': self.storage_budget_bytes,
            'usage_percentage': round(usage_pct, 2),
            'is_over_budget': await self.is_over_budget(),
            'is_near_budget': await self.is_near_budget(),
            'queue_counts': queue_counts
        }
