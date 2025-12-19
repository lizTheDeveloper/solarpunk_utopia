"""
Index Publisher Service

Periodically publishes index bundles to DTN network.
Runs as background service with configurable intervals.
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

# Add app to path for DTN integration
app_path = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_path))

from ..models import IndexType
from .index_builder import IndexBuilder
from ..database import get_discovery_db

logger = logging.getLogger(__name__)


class IndexPublisher:
    """
    Background service for periodic index publishing.

    Publishes three types of indexes at different intervals:
    - InventoryIndex: Every 10 minutes (default)
    - ServiceIndex: Every 30 minutes (default)
    - KnowledgeIndex: Every 60 minutes (default)
    """

    def __init__(
        self,
        node_id: str,
        node_public_key: str,
        bundle_service,
        inventory_interval_minutes: int = 10,
        service_interval_minutes: int = 30,
        knowledge_interval_minutes: int = 60,
    ):
        """
        Initialize index publisher.

        Args:
            node_id: This node's identifier
            node_public_key: This node's public key
            bundle_service: BundleService instance for publishing
            inventory_interval_minutes: How often to publish inventory index
            service_interval_minutes: How often to publish service index
            knowledge_interval_minutes: How often to publish knowledge index
        """
        self.node_id = node_id
        self.node_public_key = node_public_key
        self.bundle_service = bundle_service

        self.inventory_interval = timedelta(minutes=inventory_interval_minutes)
        self.service_interval = timedelta(minutes=service_interval_minutes)
        self.knowledge_interval = timedelta(minutes=knowledge_interval_minutes)

        self.index_builder = IndexBuilder(node_id, node_public_key)

        self._running = False
        self._tasks = []

    async def start(self):
        """Start the publisher background tasks"""
        if self._running:
            logger.warning("Index publisher already running")
            return

        self._running = True
        logger.info("Starting index publisher...")

        # Start publisher tasks for each index type
        self._tasks = [
            asyncio.create_task(self._publish_loop(IndexType.INVENTORY, self.inventory_interval)),
            asyncio.create_task(self._publish_loop(IndexType.SERVICE, self.service_interval)),
            asyncio.create_task(self._publish_loop(IndexType.KNOWLEDGE, self.knowledge_interval)),
        ]

        logger.info("Index publisher started")

    async def stop(self):
        """Stop the publisher background tasks"""
        if not self._running:
            return

        logger.info("Stopping index publisher...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks = []
        logger.info("Index publisher stopped")

    async def _publish_loop(self, index_type: IndexType, interval: timedelta):
        """
        Background loop for publishing a specific index type.

        Args:
            index_type: Type of index to publish
            interval: How often to publish
        """
        logger.info(f"Starting {index_type.value} index publisher (interval: {interval})")

        while self._running:
            try:
                # Publish index
                await self.publish_index(index_type)

                # Wait for next publish
                await asyncio.sleep(interval.total_seconds())

            except asyncio.CancelledError:
                logger.info(f"{index_type.value} index publisher cancelled")
                break
            except Exception as e:
                logger.error(f"Error in {index_type.value} index publisher: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(60)

    async def publish_index(self, index_type: IndexType) -> Optional[str]:
        """
        Build and publish a single index.

        Args:
            index_type: Type of index to publish

        Returns:
            Bundle ID if successful, None otherwise
        """
        from app.models import BundleCreate, Topic, Priority, Audience

        try:
            logger.info(f"Publishing {index_type.value} index...")

            # Build index
            if index_type == IndexType.INVENTORY:
                index = await self.index_builder.build_inventory_index()
            elif index_type == IndexType.SERVICE:
                index = await self.index_builder.build_service_index()
            elif index_type == IndexType.KNOWLEDGE:
                index = await self.index_builder.build_knowledge_index()
            else:
                logger.error(f"Unknown index type: {index_type}")
                return None

            # Convert to bundle payload
            payload = index.to_payload()

            # Determine payload type for bundle
            payload_type = f"discovery:index:{index_type.value}"

            # Create bundle
            bundle_create = BundleCreate(
                payload=payload,
                payloadType=payload_type,
                priority=Priority.NORMAL,
                audience=Audience.PUBLIC,
                topic=Topic.INVENTORY if index_type == IndexType.INVENTORY else Topic.KNOWLEDGE,
                tags=["index", index_type.value, "discovery"],
                hopLimit=20,
                expiresAt=index.expires_at,
            )

            bundle = await self.bundle_service.create_bundle(bundle_create)

            logger.info(
                f"Published {index_type.value} index: {bundle.bundleId} "
                f"({len(index.entries)} entries, expires {index.expires_at})"
            )

            # Update publish schedule
            await self._update_publish_schedule(
                index_type,
                bundle.bundleId,
                len(index.entries)
            )

            return bundle.bundleId

        except Exception as e:
            logger.error(f"Error publishing {index_type.value} index: {e}", exc_info=True)
            return None

    async def _update_publish_schedule(
        self,
        index_type: IndexType,
        bundle_id: str,
        entry_count: int
    ):
        """Update publish schedule in database"""
        try:
            db = await get_discovery_db()
            now = datetime.now(timezone.utc)

            # Get interval for this type
            if index_type == IndexType.INVENTORY:
                interval_minutes = self.inventory_interval.total_seconds() / 60
            elif index_type == IndexType.SERVICE:
                interval_minutes = self.service_interval.total_seconds() / 60
            else:
                interval_minutes = self.knowledge_interval.total_seconds() / 60

            next_publish = now + timedelta(minutes=interval_minutes)

            await db.execute("""
                UPDATE index_publish_schedule
                SET last_published_at = ?,
                    next_publish_at = ?,
                    total_publishes = total_publishes + 1,
                    last_entry_count = ?,
                    last_bundle_id = ?
                WHERE index_type = ?
            """, (
                now.isoformat(),
                next_publish.isoformat(),
                entry_count,
                bundle_id,
                index_type.value,
            ))

            await db.commit()

        except Exception as e:
            logger.error(f"Error updating publish schedule: {e}")

    async def publish_now(self, index_type: Optional[IndexType] = None):
        """
        Manually trigger index publishing.

        Args:
            index_type: Specific type to publish, or None for all types
        """
        if index_type:
            await self.publish_index(index_type)
        else:
            await self.publish_index(IndexType.INVENTORY)
            await self.publish_index(IndexType.SERVICE)
            await self.publish_index(IndexType.KNOWLEDGE)

    async def get_publish_stats(self) -> dict:
        """Get publishing statistics"""
        try:
            db = await get_discovery_db()

            cursor = await db.execute("""
                SELECT index_type, interval_minutes, last_published_at,
                       next_publish_at, total_publishes, last_entry_count,
                       last_bundle_id, enabled
                FROM index_publish_schedule
            """)

            rows = await cursor.fetchall()

            stats = {}
            for row in rows:
                stats[row["index_type"]] = {
                    "interval_minutes": row["interval_minutes"],
                    "last_published_at": row["last_published_at"],
                    "next_publish_at": row["next_publish_at"],
                    "total_publishes": row["total_publishes"],
                    "last_entry_count": row["last_entry_count"],
                    "last_bundle_id": row["last_bundle_id"],
                    "enabled": bool(row["enabled"]),
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting publish stats: {e}")
            return {}
