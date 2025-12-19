"""
Chunking Service

Splits files into chunks and generates manifests.
"""

import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import FileManifest, ChunkMetadata, ChunkStatus
from .hashing_service import HashingService
from .merkle_tree_service import MerkleTreeService


class ChunkingService:
    """
    Service for chunking files and generating manifests.

    Handles:
    - Splitting files into fixed-size chunks
    - Hashing chunks and files
    - Generating file manifests with Merkle trees
    - Creating chunk metadata
    """

    # Default chunk size: 512KB (configurable between 256KB and 1MB)
    DEFAULT_CHUNK_SIZE = 512 * 1024

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """
        Initialize chunking service.

        Args:
            chunk_size: Size of each chunk in bytes (256KB - 1MB)

        Raises:
            ValueError: If chunk_size is outside valid range
        """
        min_size = 256 * 1024  # 256KB
        max_size = 1024 * 1024  # 1MB

        if chunk_size < min_size or chunk_size > max_size:
            raise ValueError(f"Chunk size must be between {min_size} and {max_size} bytes")

        self.chunk_size = chunk_size

    def chunk_file(
        self,
        file_path: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Tuple[FileManifest, List[Tuple[ChunkMetadata, bytes]]]:
        """
        Chunk a file and generate manifest.

        Args:
            file_path: Path to file to chunk
            tags: Optional tags for file categorization
            description: Optional file description
            created_by: Optional public key of creator

        Returns:
            Tuple of (FileManifest, List of (ChunkMetadata, chunk_data))

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Read file content
        with open(path, 'rb') as f:
            file_content = f.read()

        if len(file_content) == 0:
            raise ValueError(f"File is empty: {file_path}")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        # Hash complete file
        file_hash = HashingService.hash_file_content(file_content)

        # Split into chunks
        chunks_data = []
        chunk_hashes = []
        chunk_index = 0

        offset = 0
        while offset < len(file_content):
            # Extract chunk
            chunk_data = file_content[offset:offset + self.chunk_size]
            chunk_size = len(chunk_data)

            # Hash chunk
            chunk_hash = HashingService.hash_chunk_content(chunk_data)

            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunkHash=chunk_hash,
                chunkIndex=chunk_index,
                chunkSize=chunk_size,
                fileHash=file_hash,
                status=ChunkStatus.PENDING,
                createdAt=datetime.now(timezone.utc)
            )

            chunks_data.append((chunk_metadata, chunk_data))
            chunk_hashes.append(chunk_hash)

            chunk_index += 1
            offset += self.chunk_size

        # Build Merkle tree
        merkle_tree = MerkleTreeService.build_tree(chunk_hashes)
        merkle_root = MerkleTreeService.get_root_hash(merkle_tree)

        # Create file manifest
        manifest = FileManifest(
            fileHash=file_hash,
            fileName=path.name,
            fileSize=len(file_content),
            mimeType=mime_type,
            chunkSize=self.chunk_size,
            chunkCount=len(chunks_data),
            chunkHashes=chunk_hashes,
            merkleRoot=merkle_root,
            createdAt=datetime.now(timezone.utc),
            createdBy=created_by,
            tags=tags or [],
            description=description
        )

        return manifest, chunks_data

    def chunk_bytes(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str = "application/octet-stream",
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Tuple[FileManifest, List[Tuple[ChunkMetadata, bytes]]]:
        """
        Chunk bytes in memory and generate manifest.

        Useful for chunking data that's already loaded in memory.

        Args:
            file_content: File content as bytes
            file_name: Name of the file
            mime_type: MIME type of the file
            tags: Optional tags for file categorization
            description: Optional file description
            created_by: Optional public key of creator

        Returns:
            Tuple of (FileManifest, List of (ChunkMetadata, chunk_data))

        Raises:
            ValueError: If file_content is empty
        """
        if len(file_content) == 0:
            raise ValueError("File content is empty")

        # Hash complete file
        file_hash = HashingService.hash_file_content(file_content)

        # Split into chunks
        chunks_data = []
        chunk_hashes = []
        chunk_index = 0

        offset = 0
        while offset < len(file_content):
            # Extract chunk
            chunk_data = file_content[offset:offset + self.chunk_size]
            chunk_size = len(chunk_data)

            # Hash chunk
            chunk_hash = HashingService.hash_chunk_content(chunk_data)

            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunkHash=chunk_hash,
                chunkIndex=chunk_index,
                chunkSize=chunk_size,
                fileHash=file_hash,
                status=ChunkStatus.PENDING,
                createdAt=datetime.now(timezone.utc)
            )

            chunks_data.append((chunk_metadata, chunk_data))
            chunk_hashes.append(chunk_hash)

            chunk_index += 1
            offset += self.chunk_size

        # Build Merkle tree
        merkle_tree = MerkleTreeService.build_tree(chunk_hashes)
        merkle_root = MerkleTreeService.get_root_hash(merkle_tree)

        # Create file manifest
        manifest = FileManifest(
            fileHash=file_hash,
            fileName=file_name,
            fileSize=len(file_content),
            mimeType=mime_type,
            chunkSize=self.chunk_size,
            chunkCount=len(chunks_data),
            chunkHashes=chunk_hashes,
            merkleRoot=merkle_root,
            createdAt=datetime.now(timezone.utc),
            createdBy=created_by,
            tags=tags or [],
            description=description
        )

        return manifest, chunks_data

    def verify_chunks(
        self,
        chunks: List[Tuple[ChunkMetadata, bytes]],
        manifest: FileManifest
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify all chunks match their metadata and manifest.

        Args:
            chunks: List of (ChunkMetadata, chunk_data) tuples
            manifest: File manifest to verify against

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check chunk count
        if len(chunks) != manifest.chunkCount:
            return False, f"Chunk count mismatch: expected {manifest.chunkCount}, got {len(chunks)}"

        # Verify each chunk
        for i, (chunk_metadata, chunk_data) in enumerate(chunks):
            # Check index
            if chunk_metadata.chunkIndex != i:
                return False, f"Chunk index mismatch at position {i}"

            # Check size
            if len(chunk_data) != chunk_metadata.chunkSize:
                return False, f"Chunk size mismatch at index {i}"

            # Verify chunk hash
            actual_hash = HashingService.hash_chunk_content(chunk_data)
            if actual_hash != chunk_metadata.chunkHash:
                return False, f"Chunk hash mismatch at index {i}"

            # Check against manifest
            expected_hash = manifest.get_chunk_hash(i)
            if expected_hash != chunk_metadata.chunkHash:
                return False, f"Chunk hash doesn't match manifest at index {i}"

        return True, None

    def calculate_chunk_count(self, file_size: int) -> int:
        """
        Calculate how many chunks a file will produce.

        Args:
            file_size: Size of file in bytes

        Returns:
            Number of chunks
        """
        if file_size <= 0:
            return 0

        return (file_size + self.chunk_size - 1) // self.chunk_size
