"""
Chunk Repository

Database access layer for chunk metadata.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from ..models import ChunkMetadata, ChunkStatus
from .schema import get_db

logger = logging.getLogger(__name__)


class ChunkRepository:
    """
    Repository for chunk metadata operations.

    Handles CRUD operations for chunks in the database.
    """

    @staticmethod
    async def create(chunk: ChunkMetadata) -> None:
        """
        Create a new chunk record.

        Args:
            chunk: ChunkMetadata to store
        """
        db = await get_db()

        await db.execute("""
            INSERT INTO chunks (
                chunk_hash, chunk_index, chunk_size, file_hash,
                status, storage_path, created_at, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk.chunkHash,
            chunk.chunkIndex,
            chunk.chunkSize,
            chunk.fileHash,
            chunk.status.value,
            chunk.storagePath,
            chunk.createdAt.isoformat(),
            chunk.verifiedAt.isoformat() if chunk.verifiedAt else None
        ))

        await db.commit()
        logger.debug(f"Created chunk: {chunk.chunkHash}")

    @staticmethod
    async def get(chunk_hash: str) -> Optional[ChunkMetadata]:
        """
        Get chunk by hash.

        Args:
            chunk_hash: Hash of chunk to retrieve

        Returns:
            ChunkMetadata or None if not found
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM chunks WHERE chunk_hash = ?
        """, (chunk_hash,))

        row = await cursor.fetchone()

        if row is None:
            return None

        return ChunkRepository._row_to_chunk(row)

    @staticmethod
    async def get_by_file(file_hash: str) -> List[ChunkMetadata]:
        """
        Get all chunks for a file.

        Args:
            file_hash: Hash of file

        Returns:
            List of ChunkMetadata ordered by chunk_index
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM chunks
            WHERE file_hash = ?
            ORDER BY chunk_index ASC
        """, (file_hash,))

        rows = await cursor.fetchall()

        return [ChunkRepository._row_to_chunk(row) for row in rows]

    @staticmethod
    async def get_by_status(status: ChunkStatus, limit: int = 100) -> List[ChunkMetadata]:
        """
        Get chunks by status.

        Args:
            status: Status to filter by
            limit: Maximum number of chunks to return

        Returns:
            List of ChunkMetadata
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM chunks
            WHERE status = ?
            LIMIT ?
        """, (status.value, limit))

        rows = await cursor.fetchall()

        return [ChunkRepository._row_to_chunk(row) for row in rows]

    @staticmethod
    async def update_status(
        chunk_hash: str,
        status: ChunkStatus,
        storage_path: Optional[str] = None
    ) -> None:
        """
        Update chunk status and optionally storage path.

        Args:
            chunk_hash: Hash of chunk to update
            status: New status
            storage_path: Optional storage path
        """
        db = await get_db()

        if storage_path:
            await db.execute("""
                UPDATE chunks
                SET status = ?, storage_path = ?
                WHERE chunk_hash = ?
            """, (status.value, storage_path, chunk_hash))
        else:
            await db.execute("""
                UPDATE chunks
                SET status = ?
                WHERE chunk_hash = ?
            """, (status.value, chunk_hash))

        await db.commit()
        logger.debug(f"Updated chunk {chunk_hash} status to {status.value}")

    @staticmethod
    async def mark_verified(chunk_hash: str) -> None:
        """
        Mark chunk as verified.

        Args:
            chunk_hash: Hash of chunk to mark verified
        """
        db = await get_db()

        await db.execute("""
            UPDATE chunks
            SET status = ?, verified_at = ?
            WHERE chunk_hash = ?
        """, (ChunkStatus.VERIFIED.value, datetime.utcnow().isoformat(), chunk_hash))

        await db.commit()
        logger.debug(f"Marked chunk {chunk_hash} as verified")

    @staticmethod
    async def exists(chunk_hash: str) -> bool:
        """
        Check if chunk exists in database.

        Args:
            chunk_hash: Hash of chunk to check

        Returns:
            True if exists, False otherwise
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT COUNT(*) FROM chunks WHERE chunk_hash = ?
        """, (chunk_hash,))

        row = await cursor.fetchone()
        return row[0] > 0

    @staticmethod
    async def delete(chunk_hash: str) -> None:
        """
        Delete chunk from database.

        Args:
            chunk_hash: Hash of chunk to delete
        """
        db = await get_db()

        await db.execute("""
            DELETE FROM chunks WHERE chunk_hash = ?
        """, (chunk_hash,))

        await db.commit()
        logger.debug(f"Deleted chunk: {chunk_hash}")

    @staticmethod
    async def count_by_file(file_hash: str) -> int:
        """
        Count chunks for a file.

        Args:
            file_hash: Hash of file

        Returns:
            Number of chunks
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT COUNT(*) FROM chunks WHERE file_hash = ?
        """, (file_hash,))

        row = await cursor.fetchone()
        return row[0]

    @staticmethod
    async def count_stored_chunks(file_hash: str) -> int:
        """
        Count how many chunks are stored locally for a file.

        Args:
            file_hash: Hash of file

        Returns:
            Number of stored chunks
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT COUNT(*) FROM chunks
            WHERE file_hash = ? AND status = ?
        """, (file_hash, ChunkStatus.STORED.value))

        row = await cursor.fetchone()
        return row[0]

    @staticmethod
    def _row_to_chunk(row) -> ChunkMetadata:
        """Convert database row to ChunkMetadata"""
        return ChunkMetadata(
            chunkHash=row['chunk_hash'],
            chunkIndex=row['chunk_index'],
            chunkSize=row['chunk_size'],
            fileHash=row['file_hash'],
            status=ChunkStatus(row['status']),
            storagePath=row['storage_path'],
            createdAt=datetime.fromisoformat(row['created_at']),
            verifiedAt=datetime.fromisoformat(row['verified_at']) if row['verified_at'] else None
        )
