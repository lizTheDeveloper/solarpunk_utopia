"""
Manifest Repository

Database access layer for file manifests.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from ..models import FileManifest
from .schema import get_db

logger = logging.getLogger(__name__)


class ManifestRepository:
    """
    Repository for file manifest operations.

    Handles CRUD operations for file manifests in the database.
    """

    @staticmethod
    async def create(manifest: FileManifest) -> None:
        """
        Create a new file manifest record.

        Args:
            manifest: FileManifest to store
        """
        db = await get_db()

        await db.execute("""
            INSERT INTO file_manifests (
                file_hash, file_name, file_size, mime_type,
                chunk_size, chunk_count, chunk_hashes, merkle_root,
                created_at, created_by, tags, description,
                is_complete, last_accessed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            manifest.fileHash,
            manifest.fileName,
            manifest.fileSize,
            manifest.mimeType,
            manifest.chunkSize,
            manifest.chunkCount,
            json.dumps(manifest.chunkHashes),
            manifest.merkleRoot,
            manifest.createdAt.isoformat(),
            manifest.createdBy,
            json.dumps(manifest.tags),
            manifest.description,
            0,  # is_complete
            None  # last_accessed
        ))

        await db.commit()
        logger.debug(f"Created manifest: {manifest.fileHash}")

    @staticmethod
    async def get(file_hash: str) -> Optional[FileManifest]:
        """
        Get manifest by file hash.

        Args:
            file_hash: Hash of file

        Returns:
            FileManifest or None if not found
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM file_manifests WHERE file_hash = ?
        """, (file_hash,))

        row = await cursor.fetchone()

        if row is None:
            return None

        # Update last_accessed
        await db.execute("""
            UPDATE file_manifests
            SET last_accessed = ?
            WHERE file_hash = ?
        """, (datetime.utcnow().isoformat(), file_hash))
        await db.commit()

        return ManifestRepository._row_to_manifest(row)

    @staticmethod
    async def list_all(limit: int = 100, offset: int = 0) -> List[FileManifest]:
        """
        List all manifests.

        Args:
            limit: Maximum number of manifests to return
            offset: Number of manifests to skip

        Returns:
            List of FileManifest
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM file_manifests
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = await cursor.fetchall()

        return [ManifestRepository._row_to_manifest(row) for row in rows]

    @staticmethod
    async def list_complete(limit: int = 100) -> List[FileManifest]:
        """
        List manifests for files that are completely stored locally.

        Args:
            limit: Maximum number of manifests to return

        Returns:
            List of FileManifest
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT * FROM file_manifests
            WHERE is_complete = 1
            ORDER BY last_accessed DESC
            LIMIT ?
        """, (limit,))

        rows = await cursor.fetchall()

        return [ManifestRepository._row_to_manifest(row) for row in rows]

    @staticmethod
    async def search_by_tags(tags: List[str], limit: int = 100) -> List[FileManifest]:
        """
        Search manifests by tags.

        Args:
            tags: List of tags to search for
            limit: Maximum number of manifests to return

        Returns:
            List of FileManifest that have any of the specified tags
        """
        db = await get_db()

        # Build LIKE clauses for each tag
        # Note: This is a simple search; for production, consider full-text search
        conditions = []
        params = []
        for tag in tags:
            conditions.append("tags LIKE ?")
            params.append(f'%"{tag}"%')

        where_clause = " OR ".join(conditions)
        params.append(limit)

        cursor = await db.execute(f"""
            SELECT * FROM file_manifests
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """, params)

        rows = await cursor.fetchall()

        return [ManifestRepository._row_to_manifest(row) for row in rows]

    @staticmethod
    async def update_complete_status(file_hash: str, is_complete: bool) -> None:
        """
        Update the is_complete flag for a manifest.

        Args:
            file_hash: Hash of file
            is_complete: Whether all chunks are stored locally
        """
        db = await get_db()

        await db.execute("""
            UPDATE file_manifests
            SET is_complete = ?
            WHERE file_hash = ?
        """, (1 if is_complete else 0, file_hash))

        await db.commit()
        logger.debug(f"Updated manifest {file_hash} complete status to {is_complete}")

    @staticmethod
    async def exists(file_hash: str) -> bool:
        """
        Check if manifest exists.

        Args:
            file_hash: Hash of file

        Returns:
            True if exists, False otherwise
        """
        db = await get_db()

        cursor = await db.execute("""
            SELECT COUNT(*) FROM file_manifests WHERE file_hash = ?
        """, (file_hash,))

        row = await cursor.fetchone()
        return row[0] > 0

    @staticmethod
    async def delete(file_hash: str) -> None:
        """
        Delete manifest and all associated chunks.

        Args:
            file_hash: Hash of file to delete
        """
        db = await get_db()

        # Foreign key cascade will delete associated chunks
        await db.execute("""
            DELETE FROM file_manifests WHERE file_hash = ?
        """, (file_hash,))

        await db.commit()
        logger.debug(f"Deleted manifest: {file_hash}")

    @staticmethod
    async def count() -> int:
        """
        Count total number of manifests.

        Returns:
            Number of manifests in database
        """
        db = await get_db()

        cursor = await db.execute("SELECT COUNT(*) FROM file_manifests")
        row = await cursor.fetchone()
        return row[0]

    @staticmethod
    def _row_to_manifest(row) -> FileManifest:
        """Convert database row to FileManifest"""
        return FileManifest(
            fileHash=row['file_hash'],
            fileName=row['file_name'],
            fileSize=row['file_size'],
            mimeType=row['mime_type'],
            chunkSize=row['chunk_size'],
            chunkCount=row['chunk_count'],
            chunkHashes=json.loads(row['chunk_hashes']),
            merkleRoot=row['merkle_root'],
            createdAt=datetime.fromisoformat(row['created_at']),
            createdBy=row['created_by'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            description=row['description']
        )
