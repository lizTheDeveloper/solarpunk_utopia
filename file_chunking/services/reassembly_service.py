"""
Reassembly Service

Reassembles files from chunks with verification.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import FileManifest, ChunkMetadata
from ..database import ChunkRepository, ManifestRepository
from .chunk_storage_service import ChunkStorageService
from .hashing_service import HashingService
from .merkle_tree_service import MerkleTreeService

logger = logging.getLogger(__name__)


class ReassemblyService:
    """
    Service for reassembling files from chunks.

    Features:
    - Collect chunks in correct order
    - Verify each chunk hash
    - Verify final file hash
    - Support partial reassembly (resume downloads)
    """

    def __init__(self, chunk_storage: ChunkStorageService):
        """
        Initialize reassembly service.

        Args:
            chunk_storage: ChunkStorageService instance
        """
        self.chunk_storage = chunk_storage

    async def reassemble_file(
        self,
        file_hash: str,
        output_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Reassemble a file from its chunks.

        Args:
            file_hash: Hash of file to reassemble
            output_path: Where to save the reassembled file

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get file manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                return False, f"Manifest not found for file: {file_hash}"

            # Check if all chunks are available
            chunks = await ChunkRepository.get_by_file(file_hash)
            if len(chunks) != manifest.chunkCount:
                return False, f"Missing chunks: have {len(chunks)}, need {manifest.chunkCount}"

            # Sort chunks by index
            chunks.sort(key=lambda c: c.chunkIndex)

            # Verify we have all indices
            for i, chunk in enumerate(chunks):
                if chunk.chunkIndex != i:
                    return False, f"Missing chunk at index {i}"

            # Retrieve and verify all chunks
            chunk_data_list = []
            for i, chunk in enumerate(chunks):
                # Retrieve chunk data
                chunk_data = await self.chunk_storage.retrieve_chunk(chunk.chunkHash)
                if chunk_data is None:
                    return False, f"Failed to retrieve chunk at index {i}"

                # Verify chunk hash
                if not HashingService.verify_chunk_hash(chunk_data, chunk.chunkHash):
                    return False, f"Chunk hash verification failed at index {i}"

                # Verify against manifest
                expected_hash = manifest.get_chunk_hash(i)
                if expected_hash != chunk.chunkHash:
                    return False, f"Chunk hash mismatch with manifest at index {i}"

                chunk_data_list.append(chunk_data)

            # Reassemble file
            file_content = b''.join(chunk_data_list)

            # Verify file size
            if len(file_content) != manifest.fileSize:
                return False, f"File size mismatch: expected {manifest.fileSize}, got {len(file_content)}"

            # Verify file hash
            actual_hash = HashingService.hash_file_content(file_content)
            if actual_hash != file_hash:
                return False, f"File hash verification failed: expected {file_hash}, got {actual_hash}"

            # Write to output file
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path_obj, 'wb') as f:
                f.write(file_content)

            logger.info(f"Reassembled file {file_hash} to {output_path} ({len(file_content)} bytes)")
            return True, None

        except Exception as e:
            error_msg = f"Failed to reassemble file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def check_reassembly_readiness(
        self,
        file_hash: str
    ) -> Tuple[bool, Optional[str], Optional[List[int]]]:
        """
        Check if a file is ready to be reassembled.

        Args:
            file_hash: Hash of file to check

        Returns:
            Tuple of (is_ready, error_message, missing_chunk_indices)
        """
        try:
            # Get file manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                return False, f"Manifest not found for file: {file_hash}", None

            # Get all chunks
            chunks = await ChunkRepository.get_by_file(file_hash)

            # Build set of available chunk indices
            available_indices = set(chunk.chunkIndex for chunk in chunks)

            # Find missing chunks
            missing_indices = []
            for i in range(manifest.chunkCount):
                if i not in available_indices:
                    missing_indices.append(i)

            if missing_indices:
                return False, f"Missing {len(missing_indices)} chunks", missing_indices

            return True, None, []

        except Exception as e:
            error_msg = f"Failed to check reassembly readiness: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None

    async def get_missing_chunks(self, file_hash: str) -> List[str]:
        """
        Get list of missing chunk hashes for a file.

        Args:
            file_hash: Hash of file

        Returns:
            List of missing chunk hashes
        """
        try:
            # Get file manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                logger.warning(f"Manifest not found for file: {file_hash}")
                return []

            # Get stored chunks
            stored_chunks = await ChunkRepository.get_by_file(file_hash)
            stored_hashes = set(chunk.chunkHash for chunk in stored_chunks)

            # Find missing chunks
            missing_hashes = []
            for chunk_hash in manifest.chunkHashes:
                if chunk_hash not in stored_hashes:
                    missing_hashes.append(chunk_hash)

            return missing_hashes

        except Exception as e:
            logger.error(f"Failed to get missing chunks: {str(e)}")
            return []

    async def verify_partial_file(
        self,
        file_hash: str
    ) -> Tuple[int, int, List[int]]:
        """
        Verify partial file reassembly progress.

        Args:
            file_hash: Hash of file

        Returns:
            Tuple of (chunks_stored, total_chunks, failed_chunk_indices)
        """
        try:
            # Get file manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                return 0, 0, []

            # Get all chunks
            chunks = await ChunkRepository.get_by_file(file_hash)

            total_chunks = manifest.chunkCount
            chunks_stored = 0
            failed_indices = []

            # Verify each stored chunk
            for chunk in chunks:
                # Check if chunk data is valid
                is_valid = await self.chunk_storage.verify_chunk_integrity(chunk.chunkHash)

                if is_valid:
                    chunks_stored += 1
                else:
                    failed_indices.append(chunk.chunkIndex)
                    logger.warning(f"Chunk {chunk.chunkIndex} failed verification")

            return chunks_stored, total_chunks, failed_indices

        except Exception as e:
            logger.error(f"Failed to verify partial file: {str(e)}")
            return 0, 0, []

    async def reassemble_to_memory(self, file_hash: str) -> Optional[bytes]:
        """
        Reassemble file to memory instead of disk.

        Useful for smaller files or when you need the content directly.

        Args:
            file_hash: Hash of file to reassemble

        Returns:
            File content as bytes, or None if failed
        """
        try:
            # Get file manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                logger.error(f"Manifest not found for file: {file_hash}")
                return None

            # Get chunks
            chunks = await ChunkRepository.get_by_file(file_hash)
            if len(chunks) != manifest.chunkCount:
                logger.error(f"Missing chunks: have {len(chunks)}, need {manifest.chunkCount}")
                return None

            # Sort chunks by index
            chunks.sort(key=lambda c: c.chunkIndex)

            # Retrieve and verify all chunks
            chunk_data_list = []
            for i, chunk in enumerate(chunks):
                chunk_data = await self.chunk_storage.retrieve_chunk(chunk.chunkHash)
                if chunk_data is None:
                    logger.error(f"Failed to retrieve chunk at index {i}")
                    return None

                chunk_data_list.append(chunk_data)

            # Reassemble
            file_content = b''.join(chunk_data_list)

            # Verify file hash
            actual_hash = HashingService.hash_file_content(file_content)
            if actual_hash != file_hash:
                logger.error(f"File hash verification failed")
                return None

            return file_content

        except Exception as e:
            logger.error(f"Failed to reassemble to memory: {str(e)}")
            return None
