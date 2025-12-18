"""
Chunk Storage Service

Handles physical storage of chunks on the filesystem with deduplication.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from ..models import ChunkMetadata, ChunkStatus
from ..database import ChunkRepository
from .hashing_service import HashingService

logger = logging.getLogger(__name__)


class ChunkStorageService:
    """
    Service for storing and retrieving chunks on filesystem.

    Features:
    - Content-addressed storage (chunks identified by hash)
    - Automatic deduplication (same content = same chunk)
    - Organized directory structure
    - Metadata tracking in database
    """

    def __init__(self, storage_path: str = None):
        """
        Initialize chunk storage service.

        Args:
            storage_path: Root path for chunk storage (defaults to data/chunks/)
        """
        if storage_path is None:
            # Default to data/chunks/ relative to file_chunking directory
            base_path = Path(__file__).parent.parent / "data" / "chunks"
        else:
            base_path = Path(storage_path)

        self.storage_path = base_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Chunk storage initialized at {self.storage_path}")

    def _get_chunk_path(self, chunk_hash: str) -> Path:
        """
        Get filesystem path for a chunk.

        Uses first 2 characters of hex hash for directory sharding
        to avoid too many files in one directory.

        Args:
            chunk_hash: Hash of chunk (format: chunk:sha256:...)

        Returns:
            Path to chunk file
        """
        # Extract hex hash
        hex_hash = HashingService.extract_hex_hash(chunk_hash)

        # Use first 2 chars for directory sharding
        shard = hex_hash[:2]
        shard_dir = self.storage_path / shard

        # Create shard directory if it doesn't exist
        shard_dir.mkdir(exist_ok=True)

        return shard_dir / hex_hash

    async def store_chunk(
        self,
        chunk_metadata: ChunkMetadata,
        chunk_data: bytes
    ) -> Tuple[bool, Optional[str]]:
        """
        Store chunk to filesystem and update database.

        Performs deduplication - if chunk already exists, just updates metadata.

        Args:
            chunk_metadata: Metadata for the chunk
            chunk_data: Raw chunk data

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify chunk hash
            if not HashingService.verify_chunk_hash(chunk_data, chunk_metadata.chunkHash):
                return False, "Chunk hash mismatch - data corrupted"

            # Get storage path
            chunk_path = self._get_chunk_path(chunk_metadata.chunkHash)

            # Check if chunk already exists (deduplication)
            if chunk_path.exists():
                logger.debug(f"Chunk {chunk_metadata.chunkHash} already exists (deduplicated)")

                # Check if metadata exists in database
                if await ChunkRepository.exists(chunk_metadata.chunkHash):
                    # Chunk already fully stored
                    return True, None
                else:
                    # File exists but metadata doesn't - add metadata
                    chunk_metadata.mark_stored(str(chunk_path))
                    await ChunkRepository.create(chunk_metadata)
                    return True, None

            # Write chunk to disk
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)

            # Update metadata
            chunk_metadata.mark_stored(str(chunk_path))
            chunk_metadata.mark_verified()

            # Save to database
            if await ChunkRepository.exists(chunk_metadata.chunkHash):
                # Update existing record
                await ChunkRepository.update_status(
                    chunk_metadata.chunkHash,
                    ChunkStatus.VERIFIED,
                    str(chunk_path)
                )
                await ChunkRepository.mark_verified(chunk_metadata.chunkHash)
            else:
                # Create new record
                await ChunkRepository.create(chunk_metadata)

            logger.info(f"Stored chunk {chunk_metadata.chunkHash} ({chunk_metadata.chunkSize} bytes)")
            return True, None

        except Exception as e:
            error_msg = f"Failed to store chunk: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def retrieve_chunk(self, chunk_hash: str) -> Optional[bytes]:
        """
        Retrieve chunk data from filesystem.

        Args:
            chunk_hash: Hash of chunk to retrieve

        Returns:
            Chunk data as bytes, or None if not found
        """
        try:
            # Get chunk metadata from database
            chunk_metadata = await ChunkRepository.get(chunk_hash)

            if chunk_metadata is None:
                logger.warning(f"Chunk {chunk_hash} not found in database")
                return None

            if chunk_metadata.status not in [ChunkStatus.STORED, ChunkStatus.VERIFIED]:
                logger.warning(f"Chunk {chunk_hash} not stored locally (status: {chunk_metadata.status})")
                return None

            # Get storage path
            chunk_path = self._get_chunk_path(chunk_hash)

            if not chunk_path.exists():
                logger.error(f"Chunk {chunk_hash} metadata exists but file missing at {chunk_path}")
                return None

            # Read chunk data
            with open(chunk_path, 'rb') as f:
                chunk_data = f.read()

            # Verify hash
            if not HashingService.verify_chunk_hash(chunk_data, chunk_hash):
                logger.error(f"Chunk {chunk_hash} failed verification - data corrupted")
                return None

            logger.debug(f"Retrieved chunk {chunk_hash} ({len(chunk_data)} bytes)")
            return chunk_data

        except Exception as e:
            logger.error(f"Failed to retrieve chunk {chunk_hash}: {str(e)}")
            return None

    async def chunk_exists(self, chunk_hash: str) -> bool:
        """
        Check if chunk is stored locally.

        Args:
            chunk_hash: Hash of chunk

        Returns:
            True if chunk is stored and verified, False otherwise
        """
        chunk_metadata = await ChunkRepository.get(chunk_hash)

        if chunk_metadata is None:
            return False

        if chunk_metadata.status not in [ChunkStatus.STORED, ChunkStatus.VERIFIED]:
            return False

        # Verify file actually exists
        chunk_path = self._get_chunk_path(chunk_hash)
        return chunk_path.exists()

    async def delete_chunk(self, chunk_hash: str) -> Tuple[bool, Optional[str]]:
        """
        Delete chunk from filesystem and database.

        Args:
            chunk_hash: Hash of chunk to delete

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get chunk path
            chunk_path = self._get_chunk_path(chunk_hash)

            # Delete file if exists
            if chunk_path.exists():
                chunk_path.unlink()
                logger.debug(f"Deleted chunk file: {chunk_path}")

            # Delete from database
            await ChunkRepository.delete(chunk_hash)

            logger.info(f"Deleted chunk: {chunk_hash}")
            return True, None

        except Exception as e:
            error_msg = f"Failed to delete chunk: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats
        """
        total_chunks = 0
        total_size = 0

        # Walk through storage directory
        for chunk_file in self.storage_path.rglob("*"):
            if chunk_file.is_file():
                total_chunks += 1
                total_size += chunk_file.stat().st_size

        return {
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "storage_path": str(self.storage_path)
        }

    async def verify_chunk_integrity(self, chunk_hash: str) -> bool:
        """
        Verify chunk data matches its hash.

        Args:
            chunk_hash: Hash of chunk to verify

        Returns:
            True if chunk is valid, False otherwise
        """
        chunk_data = await self.retrieve_chunk(chunk_hash)

        if chunk_data is None:
            return False

        return HashingService.verify_chunk_hash(chunk_data, chunk_hash)
