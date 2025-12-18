import asyncio
import logging
from typing import Optional

from ..models import QueueName
from ..database import QueueManager

logger = logging.getLogger(__name__)


class TTLService:
    """
    Background service for TTL enforcement.

    Runs periodically to:
    1. Find expired bundles
    2. Move them to expired queue
    3. Delete old expired bundles after retention period
    """

    def __init__(
        self,
        check_interval_seconds: int = 60,
        retention_days: int = 7
    ):
        """
        Initialize TTL service.

        Args:
            check_interval_seconds: How often to check for expired bundles
            retention_days: How long to keep expired bundles for audit
        """
        self.check_interval_seconds = check_interval_seconds
        self.retention_days = retention_days
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the TTL enforcement service"""
        if self._running:
            logger.warning("TTL service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"TTL service started (check interval: {self.check_interval_seconds}s)")

    async def stop(self) -> None:
        """Stop the TTL enforcement service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("TTL service stopped")

    async def _run_loop(self) -> None:
        """Main loop for TTL enforcement"""
        while self._running:
            try:
                await self._enforce_ttl()
            except Exception as e:
                logger.error(f"Error in TTL enforcement: {e}", exc_info=True)

            # Wait for next check
            await asyncio.sleep(self.check_interval_seconds)

    async def _enforce_ttl(self) -> None:
        """
        Enforce TTL by moving expired bundles to expired queue.

        This method:
        1. Finds all expired bundles (across all active queues)
        2. Moves them to expired queue
        3. Logs the count
        """
        expired_bundles = await QueueManager.get_expired_bundles()

        if not expired_bundles:
            return

        moved_count = 0
        for bundle in expired_bundles:
            # Determine current queue from database
            db_bundle = await QueueManager.get_bundle(bundle.bundleId)
            if db_bundle:
                # Get current queue
                from ..database.db import get_db
                db = await get_db()
                cursor = await db.execute(
                    "SELECT queue FROM bundles WHERE bundleId = ?",
                    (bundle.bundleId,)
                )
                row = await cursor.fetchone()
                if row:
                    current_queue = QueueName(row['queue'])
                    # Move to expired queue
                    success = await QueueManager.move(
                        bundle.bundleId,
                        current_queue,
                        QueueName.EXPIRED
                    )
                    if success:
                        moved_count += 1

        if moved_count > 0:
            logger.info(f"Moved {moved_count} expired bundles to expired queue")

    async def enforce_once(self) -> int:
        """
        Manually trigger TTL enforcement once.

        Returns:
            Number of bundles moved to expired queue
        """
        expired_bundles = await QueueManager.get_expired_bundles()
        moved_count = 0

        for bundle in expired_bundles:
            db_bundle = await QueueManager.get_bundle(bundle.bundleId)
            if db_bundle:
                from ..database.db import get_db
                db = await get_db()
                cursor = await db.execute(
                    "SELECT queue FROM bundles WHERE bundleId = ?",
                    (bundle.bundleId,)
                )
                row = await cursor.fetchone()
                if row:
                    current_queue = QueueName(row['queue'])
                    success = await QueueManager.move(
                        bundle.bundleId,
                        current_queue,
                        QueueName.EXPIRED
                    )
                    if success:
                        moved_count += 1

        return moved_count
