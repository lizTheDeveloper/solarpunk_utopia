"""
Tests for Chunking Service

Tests file chunking, manifest generation, and Merkle tree creation.
"""

import pytest
from pathlib import Path
import tempfile
import os

from file_chunking.services import (
    ChunkingService, HashingService, MerkleTreeService
)


class TestChunkingService:
    """Test chunking service"""

    def test_chunk_small_file(self):
        """Test chunking a small file (single chunk)"""
        # Create test data (100KB)
        test_data = b"Test data " * 10240  # 100KB

        # Chunk the data
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "test.txt",
            "text/plain"
        )

        # Verify manifest
        assert manifest.fileName == "test.txt"
        assert manifest.fileSize == len(test_data)
        assert manifest.chunkCount == 1
        assert len(manifest.chunkHashes) == 1
        assert len(chunks_data) == 1

        # Verify chunk
        chunk_metadata, chunk_data = chunks_data[0]
        assert chunk_metadata.chunkIndex == 0
        assert chunk_metadata.chunkSize == len(test_data)
        assert chunk_data == test_data

        # Verify hash
        expected_hash = HashingService.hash_chunk_content(test_data)
        assert chunk_metadata.chunkHash == expected_hash

    def test_chunk_large_file(self):
        """Test chunking a large file (multiple chunks)"""
        # Create test data (2MB)
        test_data = b"X" * (2 * 1024 * 1024)

        # Chunk with 512KB chunks
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "large.bin",
            "application/octet-stream"
        )

        # Should create 4 chunks (2MB / 512KB)
        assert manifest.chunkCount == 4
        assert len(chunks_data) == 4

        # Verify each chunk
        reassembled = b""
        for i, (chunk_metadata, chunk_data) in enumerate(chunks_data):
            assert chunk_metadata.chunkIndex == i
            assert chunk_metadata.chunkSize == 512 * 1024
            reassembled += chunk_data

        # Verify reassembled data matches original
        assert reassembled == test_data

    def test_chunk_file_uneven_size(self):
        """Test chunking with uneven file size (last chunk smaller)"""
        # Create test data (1MB + 100KB)
        test_data = b"Y" * (1024 * 1024 + 100 * 1024)

        # Chunk with 512KB chunks
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "uneven.bin",
            "application/octet-stream"
        )

        # Should create 3 chunks: 512KB, 512KB, 100KB
        assert manifest.chunkCount == 3
        assert len(chunks_data) == 3

        # Verify chunk sizes
        assert chunks_data[0][0].chunkSize == 512 * 1024
        assert chunks_data[1][0].chunkSize == 512 * 1024
        assert chunks_data[2][0].chunkSize == 100 * 1024  # Last chunk smaller

    def test_merkle_tree_generation(self):
        """Test Merkle tree generation for chunks"""
        # Create test data
        test_data = b"Z" * (1024 * 1024)  # 1MB

        # Chunk
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "merkle.bin",
            "application/octet-stream"
        )

        # Build Merkle tree
        merkle_tree = MerkleTreeService.build_tree(manifest.chunkHashes)

        # Verify root hash matches manifest
        root_hash = MerkleTreeService.get_root_hash(merkle_tree)
        assert root_hash == manifest.merkleRoot

    def test_verify_chunks(self):
        """Test chunk verification against manifest"""
        # Create test data
        test_data = b"Verify" * 100000

        # Chunk
        chunking_service = ChunkingService(chunk_size=256 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "verify.bin",
            "application/octet-stream"
        )

        # Verify chunks
        is_valid, error = chunking_service.verify_chunks(chunks_data, manifest)
        assert is_valid
        assert error is None

    def test_chunk_size_validation(self):
        """Test chunk size validation"""
        # Too small
        with pytest.raises(ValueError):
            ChunkingService(chunk_size=100 * 1024)  # 100KB < 256KB

        # Too large
        with pytest.raises(ValueError):
            ChunkingService(chunk_size=2 * 1024 * 1024)  # 2MB > 1MB

        # Valid sizes
        ChunkingService(chunk_size=256 * 1024)  # 256KB (min)
        ChunkingService(chunk_size=512 * 1024)  # 512KB (default)
        ChunkingService(chunk_size=1024 * 1024)  # 1MB (max)

    def test_chunk_file_from_disk(self):
        """Test chunking a file from disk"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            test_data = b"File from disk test " * 10000
            tmp.write(test_data)
            tmp_path = tmp.name

        try:
            # Chunk the file
            chunking_service = ChunkingService(chunk_size=512 * 1024)
            manifest, chunks_data = chunking_service.chunk_file(tmp_path)

            # Verify
            assert manifest.fileName == Path(tmp_path).name
            assert manifest.fileSize == len(test_data)
            assert len(chunks_data) > 0

            # Verify reassembly
            reassembled = b"".join(chunk_data for _, chunk_data in chunks_data)
            assert reassembled == test_data

        finally:
            # Cleanup
            os.unlink(tmp_path)

    def test_file_hash_calculation(self):
        """Test file hash calculation"""
        test_data = b"Hash test data"

        chunking_service = ChunkingService()
        manifest, _ = chunking_service.chunk_bytes(
            test_data,
            "hash.txt",
            "text/plain"
        )

        # Verify file hash
        expected_hash = HashingService.hash_file_content(test_data)
        assert manifest.fileHash == expected_hash

    def test_tags_and_description(self):
        """Test manifest tags and description"""
        test_data = b"Tagged data"

        chunking_service = ChunkingService()
        manifest, _ = chunking_service.chunk_bytes(
            test_data,
            "tagged.txt",
            "text/plain",
            tags=["education", "protocol"],
            description="Test file with tags"
        )

        assert manifest.tags == ["education", "protocol"]
        assert manifest.description == "Test file with tags"
