import json
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
import aiosqlite

from ..models import Bundle, QueueName, Priority
from .db import get_db


class QueueManager:
    """
    Manages bundle queues in SQLite database.

    Queues:
    - inbox: received bundles awaiting processing
    - outbox: locally-created bundles awaiting forwarding
    - pending: bundles awaiting opportunistic forwarding
    - delivered: acknowledged deliveries
    - expired: bundles dropped due to TTL expiration
    - quarantine: bundles with invalid signatures or policy violations
    """

    _lock: Optional[asyncio.Lock] = None
    _lock_event_loop = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the lock for the current event loop"""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop
            cls._lock = asyncio.Lock()
            cls._lock_event_loop = None
            return cls._lock

        # Check if we need a new lock for a different event loop
        if cls._lock is None or cls._lock_event_loop is not current_loop:
            cls._lock = asyncio.Lock()
            cls._lock_event_loop = current_loop

        return cls._lock

    @staticmethod
    def _bundle_to_row(bundle: Bundle, queue: QueueName) -> dict:
        """Convert Bundle to database row"""
        return {
            'bundleId': bundle.bundleId,
            'queue': queue.value,
            'createdAt': bundle.createdAt.isoformat(),
            'expiresAt': bundle.expiresAt.isoformat(),
            'priority': bundle.priority.value,
            'audience': bundle.audience.value,
            'topic': bundle.topic.value,
            'tags': json.dumps(bundle.tags),
            'payloadType': bundle.payloadType,
            'payload': json.dumps(bundle.payload),
            'hopLimit': bundle.hopLimit,
            'hopCount': bundle.hopCount,
            'receiptPolicy': bundle.receiptPolicy.value,
            'signature': bundle.signature,
            'authorPublicKey': bundle.authorPublicKey,
            'sizeBytes': len(json.dumps(bundle.payload)),
            'addedToQueueAt': datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def _row_to_bundle(row: aiosqlite.Row) -> Bundle:
        """Convert database row to Bundle"""
        return Bundle(
            bundleId=row['bundleId'],
            createdAt=datetime.fromisoformat(row['createdAt']),
            expiresAt=datetime.fromisoformat(row['expiresAt']),
            priority=Priority(row['priority']),
            audience=row['audience'],
            topic=row['topic'],
            tags=json.loads(row['tags']),
            payloadType=row['payloadType'],
            payload=json.loads(row['payload']),
            hopLimit=row['hopLimit'],
            hopCount=row['hopCount'],
            receiptPolicy=row['receiptPolicy'],
            signature=row['signature'],
            authorPublicKey=row['authorPublicKey']
        )

    @classmethod
    async def enqueue(cls, queue: QueueName, bundle: Bundle) -> bool:
        """
        Add bundle to queue.

        Uses INSERT with explicit conflict handling to prevent silent overwrites.
        If bundle already exists, it will be skipped (not replaced).
        Uses lock to prevent race conditions.

        Returns:
            True if bundle was added, False if it already existed
        """
        async with cls._get_lock():
            db = await get_db()
            row = QueueManager._bundle_to_row(bundle, queue)

            # Check if bundle already exists in ANY queue (bundleId is PRIMARY KEY)
            cursor = await db.execute("""
                SELECT queue FROM bundles WHERE bundleId = ?
            """, (bundle.bundleId,))
            existing = await cursor.fetchone()

            if existing:
                # Bundle already exists, skip (don't overwrite)
                existing_queue = existing['queue']
                import logging
                logging.getLogger(__name__).debug(
                    f"Bundle {bundle.bundleId} already exists in queue {existing_queue}, skipping enqueue to {queue.value}"
                )
                return False

            # Insert new bundle
            await db.execute("""
                INSERT INTO bundles (
                    bundleId, queue, createdAt, expiresAt, priority, audience,
                    topic, tags, payloadType, payload, hopLimit, hopCount,
                    receiptPolicy, signature, authorPublicKey, sizeBytes, addedToQueueAt
                ) VALUES (
                    :bundleId, :queue, :createdAt, :expiresAt, :priority, :audience,
                    :topic, :tags, :payloadType, :payload, :hopLimit, :hopCount,
                    :receiptPolicy, :signature, :authorPublicKey, :sizeBytes, :addedToQueueAt
                )
            """, row)
            await db.commit()
            return True

    @staticmethod
    async def dequeue(
        queue: QueueName,
        limit: int = 100,
        priority_filter: Optional[Priority] = None
    ) -> List[Bundle]:
        """
        Get bundles from queue, optionally filtered by priority.
        Results are ordered by priority (emergency first) then by createdAt.
        """
        db = await get_db()

        if priority_filter:
            cursor = await db.execute("""
                SELECT * FROM bundles
                WHERE queue = ? AND priority = ?
                ORDER BY
                    CASE priority
                        WHEN 'emergency' THEN 1
                        WHEN 'perishable' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    createdAt ASC
                LIMIT ?
            """, (queue.value, priority_filter.value, limit))
        else:
            cursor = await db.execute("""
                SELECT * FROM bundles
                WHERE queue = ?
                ORDER BY
                    CASE priority
                        WHEN 'emergency' THEN 1
                        WHEN 'perishable' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    createdAt ASC
                LIMIT ?
            """, (queue.value, limit))

        rows = await cursor.fetchall()
        return [QueueManager._row_to_bundle(row) for row in rows]

    @staticmethod
    async def move(bundle_id: str, from_queue: QueueName, to_queue: QueueName) -> bool:
        """Move bundle from one queue to another"""
        db = await get_db()

        # Update queue and addedToQueueAt
        cursor = await db.execute("""
            UPDATE bundles
            SET queue = ?, addedToQueueAt = ?
            WHERE bundleId = ? AND queue = ?
        """, (to_queue.value, datetime.now(timezone.utc).isoformat(), bundle_id, from_queue.value))

        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def get_bundle(bundle_id: str) -> Optional[Bundle]:
        """Get a specific bundle by ID"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT * FROM bundles WHERE bundleId = ?
        """, (bundle_id,))
        row = await cursor.fetchone()
        return QueueManager._row_to_bundle(row) if row else None

    @staticmethod
    async def delete(bundle_id: str) -> bool:
        """Delete a bundle from database"""
        db = await get_db()
        cursor = await db.execute("""
            DELETE FROM bundles WHERE bundleId = ?
        """, (bundle_id,))
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def list_queue(
        queue: QueueName,
        limit: int = 100,
        offset: int = 0
    ) -> List[Bundle]:
        """List bundles in a queue with pagination"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT * FROM bundles
            WHERE queue = ?
            ORDER BY
                CASE priority
                    WHEN 'emergency' THEN 1
                    WHEN 'perishable' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                createdAt ASC
            LIMIT ? OFFSET ?
        """, (queue.value, limit, offset))

        rows = await cursor.fetchall()
        return [QueueManager._row_to_bundle(row) for row in rows]

    @staticmethod
    async def count_queue(queue: QueueName) -> int:
        """Count bundles in a queue"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT COUNT(*) as count FROM bundles WHERE queue = ?
        """, (queue.value,))
        row = await cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    async def get_expired_bundles() -> List[Bundle]:
        """Get all expired bundles (across all queues except expired/quarantine)"""
        db = await get_db()
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute("""
            SELECT * FROM bundles
            WHERE expiresAt < ?
            AND queue NOT IN ('expired', 'quarantine')
        """, (now,))

        rows = await cursor.fetchall()
        return [QueueManager._row_to_bundle(row) for row in rows]

    @staticmethod
    async def get_total_cache_size() -> int:
        """Get total cache size in bytes"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT SUM(sizeBytes) as total FROM bundles
        """)
        row = await cursor.fetchone()
        return row['total'] if row and row['total'] else 0

    @staticmethod
    async def get_bundles_by_priority(priority: Priority, limit: int = 100) -> List[Bundle]:
        """Get all bundles of a specific priority"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT * FROM bundles
            WHERE priority = ?
            ORDER BY createdAt ASC
            LIMIT ?
        """, (priority.value, limit))

        rows = await cursor.fetchall()
        return [QueueManager._row_to_bundle(row) for row in rows]

    @staticmethod
    async def exists(bundle_id: str) -> bool:
        """Check if bundle exists in any queue"""
        db = await get_db()
        cursor = await db.execute("""
            SELECT 1 FROM bundles WHERE bundleId = ? LIMIT 1
        """, (bundle_id,))
        row = await cursor.fetchone()
        return row is not None

    @staticmethod
    async def exists_in_queues(bundle_id: str, queues: List[QueueName]) -> bool:
        """Check if bundle exists in specific queues"""
        db = await get_db()
        queue_values = [q.value for q in queues]
        placeholders = ','.join('?' * len(queue_values))
        cursor = await db.execute(f"""
            SELECT 1 FROM bundles
            WHERE bundleId = ? AND queue IN ({placeholders})
            LIMIT 1
        """, (bundle_id, *queue_values))
        row = await cursor.fetchone()
        return row is not None
