"""
Tests for Storage and Reassembly

Tests chunk storage, retrieval, deduplication, and file reassembly.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

from file_chunking.services import (
    ChunkingService, ChunkStorageService, ReassemblyService,
    HashingService
)
from file_chunking.database import init_db, close_db, ChunkRepository, ManifestRepository
from file_chunking.models import ChunkStatus


class TestChunkStorage:
    """Test chunk storage service"""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Setup
        await init_db()

        # Create temporary storage directory
        self.temp_storage = tempfile.mkdtemp()

        yield

        # Teardown
        await close_db()

        # Cleanup temp storage
        import shutil
        if os.path.exists(self.temp_storage):
            shutil.rmtree(self.temp_storage)

    @pytest.mark.asyncio
    async def test_store_and_retrieve_chunk(self):
        """Test storing and retrieving a chunk"""
        # Create test data
        test_data = b"Test chunk data"

        # Create chunk metadata
        chunking_service = ChunkingService()
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data,
            "test.txt",
            "text/plain"
        )

        chunk_metadata, chunk_data = chunks_data[0]

        # Store chunk
        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)
        success, error = await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        assert success
        assert error is None

        # Retrieve chunk
        retrieved_data = await chunk_storage.retrieve_chunk(chunk_metadata.chunkHash)

        assert retrieved_data == chunk_data

    @pytest.mark.asyncio
    async def test_chunk_deduplication(self):
        """Test that identical chunks are deduplicated"""
        # Create two identical chunks
        test_data = b"Duplicate data"

        chunking_service = ChunkingService()

        # Chunk first file
        manifest1, chunks1 = chunking_service.chunk_bytes(
            test_data, "file1.txt", "text/plain"
        )

        # Chunk second file (same content)
        manifest2, chunks2 = chunking_service.chunk_bytes(
            test_data, "file2.txt", "text/plain"
        )

        # Chunks should have same hash
        assert chunks1[0][0].chunkHash == chunks2[0][0].chunkHash

        # Store both
        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        await chunk_storage.store_chunk(chunks1[0][0], chunks1[0][1])
        await chunk_storage.store_chunk(chunks2[0][0], chunks2[0][1])

        # Both should succeed (deduplication handled internally)
        assert await chunk_storage.chunk_exists(chunks1[0][0].chunkHash)

    @pytest.mark.asyncio
    async def test_chunk_verification(self):
        """Test chunk integrity verification"""
        # Create test data
        test_data = b"Verify integrity"

        chunking_service = ChunkingService()
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "verify.txt", "text/plain"
        )

        chunk_metadata, chunk_data = chunks_data[0]

        # Store chunk
        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)
        await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        # Verify integrity
        is_valid = await chunk_storage.verify_chunk_integrity(chunk_metadata.chunkHash)
        assert is_valid

    @pytest.mark.asyncio
    async def test_storage_stats(self):
        """Test storage statistics"""
        # Store some chunks
        test_data = b"Stats test " * 1000

        chunking_service = ChunkingService()
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "stats.txt", "text/plain"
        )

        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        for chunk_metadata, chunk_data in chunks_data:
            await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        # Get stats
        stats = await chunk_storage.get_storage_stats()

        assert stats['total_chunks'] == len(chunks_data)
        assert stats['total_size_bytes'] > 0


class TestReassembly:
    """Test file reassembly service"""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Setup
        await init_db()

        # Create temporary directories
        self.temp_storage = tempfile.mkdtemp()
        self.temp_output = tempfile.mkdtemp()

        yield

        # Teardown
        await close_db()

        # Cleanup
        import shutil
        if os.path.exists(self.temp_storage):
            shutil.rmtree(self.temp_storage)
        if os.path.exists(self.temp_output):
            shutil.rmtree(self.temp_output)

    @pytest.mark.asyncio
    async def test_reassemble_small_file(self):
        """Test reassembling a small file (single chunk)"""
        # Create test data
        test_data = b"Small file content for reassembly"

        # Chunk file
        chunking_service = ChunkingService()
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "small.txt", "text/plain"
        )

        # Store manifest and chunks
        await ManifestRepository.create(manifest)

        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        for chunk_metadata, chunk_data in chunks_data:
            await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        # Mark manifest as complete
        await ManifestRepository.update_complete_status(manifest.fileHash, True)

        # Reassemble
        reassembly_service = ReassemblyService(chunk_storage)
        output_path = os.path.join(self.temp_output, "reassembled.txt")

        success, error = await reassembly_service.reassemble_file(
            manifest.fileHash,
            output_path
        )

        assert success
        assert error is None

        # Verify reassembled file
        with open(output_path, 'rb') as f:
            reassembled_data = f.read()

        assert reassembled_data == test_data

    @pytest.mark.asyncio
    async def test_reassemble_large_file(self):
        """Test reassembling a large file (multiple chunks)"""
        # Create test data (2MB)
        test_data = b"L" * (2 * 1024 * 1024)

        # Chunk file
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "large.bin", "application/octet-stream"
        )

        # Store manifest and chunks
        await ManifestRepository.create(manifest)

        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        for chunk_metadata, chunk_data in chunks_data:
            await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        await ManifestRepository.update_complete_status(manifest.fileHash, True)

        # Reassemble
        reassembly_service = ReassemblyService(chunk_storage)
        output_path = os.path.join(self.temp_output, "large.bin")

        success, error = await reassembly_service.reassemble_file(
            manifest.fileHash,
            output_path
        )

        assert success

        # Verify reassembled file
        with open(output_path, 'rb') as f:
            reassembled_data = f.read()

        assert reassembled_data == test_data

        # Verify hash
        actual_hash = HashingService.hash_file_content(reassembled_data)
        assert actual_hash == manifest.fileHash

    @pytest.mark.asyncio
    async def test_reassembly_with_missing_chunks(self):
        """Test reassembly fails when chunks are missing"""
        # Create test data
        test_data = b"M" * (1024 * 1024)

        # Chunk file
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "missing.bin", "application/octet-stream"
        )

        # Store manifest
        await ManifestRepository.create(manifest)

        # Store only SOME chunks (not all)
        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        # Store only first chunk
        await chunk_storage.store_chunk(chunks_data[0][0], chunks_data[0][1])

        # Try to reassemble (should fail)
        reassembly_service = ReassemblyService(chunk_storage)
        output_path = os.path.join(self.temp_output, "missing.bin")

        success, error = await reassembly_service.reassemble_file(
            manifest.fileHash,
            output_path
        )

        assert not success
        assert error is not None

    @pytest.mark.asyncio
    async def test_check_reassembly_readiness(self):
        """Test checking if file is ready to reassemble"""
        # Create test data
        test_data = b"R" * (1024 * 1024)

        # Chunk file
        chunking_service = ChunkingService(chunk_size=512 * 1024)
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "ready.bin", "application/octet-stream"
        )

        # Store manifest
        await ManifestRepository.create(manifest)

        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)
        reassembly_service = ReassemblyService(chunk_storage)

        # Check readiness (no chunks stored yet)
        is_ready, error, missing = await reassembly_service.check_reassembly_readiness(
            manifest.fileHash
        )

        assert not is_ready
        assert len(missing) == len(chunks_data)

        # Store all chunks
        for chunk_metadata, chunk_data in chunks_data:
            await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        # Check readiness again
        is_ready, error, missing = await reassembly_service.check_reassembly_readiness(
            manifest.fileHash
        )

        assert is_ready
        assert len(missing) == 0

    @pytest.mark.asyncio
    async def test_reassemble_to_memory(self):
        """Test reassembling file to memory"""
        # Create test data
        test_data = b"Memory test data"

        # Chunk file
        chunking_service = ChunkingService()
        manifest, chunks_data = chunking_service.chunk_bytes(
            test_data, "memory.txt", "text/plain"
        )

        # Store manifest and chunks
        await ManifestRepository.create(manifest)

        chunk_storage = ChunkStorageService(storage_path=self.temp_storage)

        for chunk_metadata, chunk_data in chunks_data:
            await chunk_storage.store_chunk(chunk_metadata, chunk_data)

        # Reassemble to memory
        reassembly_service = ReassemblyService(chunk_storage)
        reassembled_data = await reassembly_service.reassemble_to_memory(manifest.fileHash)

        assert reassembled_data == test_data
