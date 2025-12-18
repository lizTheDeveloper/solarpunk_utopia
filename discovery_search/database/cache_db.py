"""
Index Cache Database Operations

Handles storage and retrieval of cached indexes from peer nodes.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiosqlite

from ..models import IndexType, InventoryIndex, ServiceIndex, KnowledgeIndex
from .db import get_discovery_db


class IndexCacheDB:
    """
    Database operations for index cache management.

    Handles:
    - Storing received indexes
    - Retrieving cached indexes for query matching
    - Evicting stale indexes
    - Cache statistics
    """

    @staticmethod
    async def store_index(
        index_type: IndexType,
        node_id: str,
        node_public_key: str,
        bundle_id: str,
        index_data: Dict[str, Any],
        generated_at: datetime,
        expires_at: datetime,
        entry_count: int,
        size_bytes: int
    ) -> None:
        """
        Store or update a cached index.

        Uses UPSERT to replace existing index from same node.
        """
        db = await get_discovery_db()

        now = datetime.utcnow()

        await db.execute("""
            INSERT OR REPLACE INTO cached_indexes (
                index_type, node_id, node_public_key, bundle_id,
                index_data, generated_at, expires_at, cached_at,
                entry_count, size_bytes, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            index_type.value,
            node_id,
            node_public_key,
            bundle_id,
            json.dumps(index_data),
            generated_at.isoformat(),
            expires_at.isoformat(),
            now.isoformat(),
            entry_count,
            size_bytes,
            1
        ))

        await db.commit()

    @staticmethod
    async def get_index(
        node_id: str,
        index_type: IndexType
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached index for a specific node.

        Returns None if not found or expired.
        """
        db = await get_discovery_db()

        cursor = await db.execute("""
            SELECT index_data, expires_at, cached_at
            FROM cached_indexes
            WHERE node_id = ? AND index_type = ?
        """, (node_id, index_type.value))

        row = await cursor.fetchone()

        if not row:
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires_at:
            # Delete expired index
            await db.execute("""
                DELETE FROM cached_indexes
                WHERE node_id = ? AND index_type = ?
            """, (node_id, index_type.value))
            await db.commit()
            return None

        index_data = json.loads(row["index_data"])
        index_data["cached_at"] = row["cached_at"]

        return index_data

    @staticmethod
    async def get_all_indexes(
        index_type: Optional[IndexType] = None,
        exclude_expired: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all cached indexes.

        Args:
            index_type: Filter by type (None for all types)
            exclude_expired: Exclude expired indexes

        Returns:
            List of index data dictionaries
        """
        db = await get_discovery_db()

        query = "SELECT * FROM cached_indexes WHERE 1=1"
        params = []

        if index_type:
            query += " AND index_type = ?"
            params.append(index_type.value)

        if exclude_expired:
            query += " AND expires_at > ?"
            params.append(datetime.utcnow().isoformat())

        cursor = await db.execute(query, tuple(params))
        rows = await cursor.fetchall()

        results = []
        for row in rows:
            index_data = json.loads(row["index_data"])
            index_data["cached_at"] = row["cached_at"]
            index_data["node_id"] = row["node_id"]
            index_data["bundle_id"] = row["bundle_id"]
            results.append(index_data)

        return results

    @staticmethod
    async def evict_stale_indexes(max_age_hours: int = 24) -> int:
        """
        Evict indexes older than max_age_hours.

        Returns:
            Number of indexes evicted
        """
        db = await get_discovery_db()

        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(hours=max_age_hours)

        cursor = await db.execute("""
            DELETE FROM cached_indexes
            WHERE expires_at < ?
        """, (threshold.isoformat(),))

        await db.commit()

        return cursor.rowcount

    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        db = await get_discovery_db()

        # Get total counts by type
        cursor = await db.execute("""
            SELECT index_type, COUNT(*) as count, SUM(entry_count) as total_entries,
                   SUM(size_bytes) as total_bytes
            FROM cached_indexes
            WHERE expires_at > ?
            GROUP BY index_type
        """, (datetime.utcnow().isoformat(),))

        rows = await cursor.fetchall()

        stats = {
            "by_type": {},
            "total_indexes": 0,
            "total_entries": 0,
            "total_bytes": 0,
        }

        for row in rows:
            index_type = row["index_type"]
            stats["by_type"][index_type] = {
                "count": row["count"],
                "total_entries": row["total_entries"] or 0,
                "total_bytes": row["total_bytes"] or 0,
            }
            stats["total_indexes"] += row["count"]
            stats["total_entries"] += row["total_entries"] or 0
            stats["total_bytes"] += row["total_bytes"] or 0

        # Get unique nodes
        cursor = await db.execute("""
            SELECT COUNT(DISTINCT node_id) as unique_nodes
            FROM cached_indexes
            WHERE expires_at > ?
        """, (datetime.utcnow().isoformat(),))

        row = await cursor.fetchone()
        stats["unique_nodes"] = row["unique_nodes"]

        return stats

    @staticmethod
    async def clear_cache() -> int:
        """
        Clear all cached indexes.

        Returns:
            Number of indexes cleared
        """
        db = await get_discovery_db()

        cursor = await db.execute("DELETE FROM cached_indexes")
        await db.commit()

        return cursor.rowcount
