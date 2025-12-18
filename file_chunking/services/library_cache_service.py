"""
Library Cache Service

Manages caching of popular files for library nodes.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from ..database import ManifestRepository, ChunkRepository
from ..database.schema import get_db
from .chunk_storage_service import ChunkStorageService
from .chunk_publisher_service import ChunkPublisherService
from .hashing_service import HashingService

logger = logging.getLogger(__name__)


class LibraryCacheService:
    """
    Service for managing library node file cache.

    Features:
    - Track popular files
    - Automatic caching based on access patterns
    - Cache eviction based on priority scores
    - Pre-publish popular content
    """

    def __init__(
        self,
        chunk_storage: ChunkStorageService,
        chunk_publisher: Optional[ChunkPublisherService] = None,
        cache_budget_bytes: int = 10 * 1024 * 1024 * 1024  # 10GB default
    ):
        """
        Initialize library cache service.

        Args:
            chunk_storage: ChunkStorageService instance
            chunk_publisher: Optional ChunkPublisherService for pre-publishing
            cache_budget_bytes: Maximum cache size in bytes (default 10GB)
        """
        self.chunk_storage = chunk_storage
        self.chunk_publisher = chunk_publisher
        self.cache_budget_bytes = cache_budget_bytes

    async def add_to_cache(
        self,
        file_hash: str,
        tags: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a file to library cache.

        Args:
            file_hash: Hash of file to cache
            tags: Optional tags for categorization

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get manifest
            manifest = await ManifestRepository.get(file_hash)
            if not manifest:
                return False, f"Manifest not found for {file_hash}"

            # Check if already in cache
            if await self._is_in_cache(file_hash):
                # Update access count
                await self._increment_access_count(file_hash)
                return True, None

            # Check cache budget
            if not await self._check_cache_budget(manifest.fileSize):
                # Evict files to make room
                await self._evict_files(manifest.fileSize)

            # Add to cache
            db = await get_db()

            await db.execute("""
                INSERT INTO library_cache (
                    file_hash, file_name, file_size, mime_type,
                    access_count, cached_at, tags, priority_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_hash,
                manifest.fileName,
                manifest.fileSize,
                manifest.mimeType,
                1,  # Initial access count
                datetime.utcnow().isoformat(),
                ",".join(tags) if tags else ",".join(manifest.tags),
                self._calculate_priority_score(manifest.fileSize, 1, manifest.tags)
            ))

            await db.commit()

            logger.info(f"Added {manifest.fileName} to library cache")
            return True, None

        except Exception as e:
            error_msg = f"Failed to add to cache: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def get_cached_files(self, limit: int = 100) -> List[dict]:
        """
        Get list of cached files.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of cached file info
        """
        try:
            db = await get_db()

            cursor = await db.execute("""
                SELECT * FROM library_cache
                ORDER BY access_count DESC, last_accessed DESC
                LIMIT ?
            """, (limit,))

            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get cached files: {str(e)}")
            return []

    async def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            db = await get_db()

            # Count files
            cursor = await db.execute("SELECT COUNT(*) FROM library_cache")
            row = await cursor.fetchone()
            total_files = row[0]

            # Sum file sizes
            cursor = await db.execute("SELECT SUM(file_size) FROM library_cache")
            row = await cursor.fetchone()
            total_size = row[0] or 0

            # Calculate usage percentage
            usage_percentage = (total_size / self.cache_budget_bytes) * 100 if self.cache_budget_bytes > 0 else 0

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "total_size_gb": total_size / (1024 * 1024 * 1024),
                "budget_bytes": self.cache_budget_bytes,
                "budget_gb": self.cache_budget_bytes / (1024 * 1024 * 1024),
                "usage_percentage": usage_percentage,
                "is_over_budget": total_size > self.cache_budget_bytes
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}

    async def pre_publish_cached_files(self) -> int:
        """
        Pre-publish all cached files (manifests and chunks).

        Useful for library nodes to make content immediately available.

        Returns:
            Number of files published
        """
        if not self.chunk_publisher:
            logger.warning("Cannot pre-publish: no chunk publisher configured")
            return 0

        try:
            cached_files = await self.get_cached_files(limit=1000)
            published_count = 0

            for cached_file in cached_files:
                file_hash = cached_file['file_hash']

                # Publish manifest
                manifest_bundle_id = await self.chunk_publisher.republish_manifest(file_hash)

                if manifest_bundle_id:
                    # Publish all chunks
                    chunk_bundle_ids = await self.chunk_publisher.publish_all_chunks(file_hash)

                    if chunk_bundle_ids:
                        published_count += 1
                        logger.info(f"Pre-published {cached_file['file_name']} ({len(chunk_bundle_ids)} chunks)")

            logger.info(f"Pre-published {published_count} cached files")
            return published_count

        except Exception as e:
            logger.error(f"Failed to pre-publish cached files: {str(e)}")
            return 0

    async def _is_in_cache(self, file_hash: str) -> bool:
        """Check if file is in cache"""
        try:
            db = await get_db()

            cursor = await db.execute("""
                SELECT COUNT(*) FROM library_cache WHERE file_hash = ?
            """, (file_hash,))

            row = await cursor.fetchone()
            return row[0] > 0

        except Exception as e:
            logger.error(f"Failed to check cache: {str(e)}")
            return False

    async def _increment_access_count(self, file_hash: str) -> None:
        """Increment access count for cached file"""
        try:
            db = await get_db()

            # Get current access count
            cursor = await db.execute("""
                SELECT access_count, file_size FROM library_cache WHERE file_hash = ?
            """, (file_hash,))

            row = await cursor.fetchone()
            if not row:
                return

            access_count = row[0] + 1
            file_size = row[1]

            # Calculate new priority score
            # TODO: Get tags from manifest
            priority_score = self._calculate_priority_score(file_size, access_count, [])

            # Update
            await db.execute("""
                UPDATE library_cache
                SET access_count = ?, last_accessed = ?, priority_score = ?
                WHERE file_hash = ?
            """, (access_count, datetime.utcnow().isoformat(), priority_score, file_hash))

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to increment access count: {str(e)}")

    async def _check_cache_budget(self, required_bytes: int) -> bool:
        """Check if there's enough space in cache budget"""
        stats = await self.get_cache_stats()
        current_size = stats.get('total_size_bytes', 0)
        return (current_size + required_bytes) <= self.cache_budget_bytes

    async def _evict_files(self, required_bytes: int) -> None:
        """
        Evict files to make room for new content.

        Evicts files with lowest priority scores first.
        """
        try:
            db = await get_db()

            # Get files ordered by priority score (lowest first)
            cursor = await db.execute("""
                SELECT file_hash, file_name, file_size
                FROM library_cache
                ORDER BY priority_score ASC
            """)

            rows = await cursor.fetchall()

            freed_bytes = 0

            for row in rows:
                if freed_bytes >= required_bytes:
                    break

                file_hash = row[0]
                file_name = row[1]
                file_size = row[2]

                # Remove from cache
                await db.execute("""
                    DELETE FROM library_cache WHERE file_hash = ?
                """, (file_hash,))

                freed_bytes += file_size

                logger.info(f"Evicted {file_name} from cache ({file_size} bytes)")

            await db.commit()

            logger.info(f"Evicted {freed_bytes} bytes from cache")

        except Exception as e:
            logger.error(f"Failed to evict files: {str(e)}")

    def _calculate_priority_score(
        self,
        file_size: int,
        access_count: int,
        tags: List[str]
    ) -> float:
        """
        Calculate priority score for cache eviction.

        Higher score = higher priority = less likely to be evicted

        Factors:
        - Access count (more accesses = higher priority)
        - File size (smaller files = higher priority per byte)
        - Tags (education/knowledge content = higher priority)
        """
        # Base score from access count
        score = access_count * 10.0

        # Adjust for file size (prefer smaller files)
        # Divide by MB to normalize
        size_mb = file_size / (1024 * 1024)
        if size_mb > 0:
            score = score / (size_mb ** 0.5)  # Square root to soften the penalty

        # Boost for important tags
        if tags:
            tag_set = set(t.lower() for t in tags)
            if "education" in tag_set or "protocol" in tag_set:
                score *= 2.0
            if "permaculture" in tag_set or "knowledge" in tag_set:
                score *= 1.5

        return score
