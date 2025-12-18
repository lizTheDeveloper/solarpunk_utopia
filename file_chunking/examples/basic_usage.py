"""
Basic Usage Examples for File Chunking System

Demonstrates core functionality:
- Chunking files
- Storing chunks
- Reassembling files
- Publishing to DTN
- Requesting files
"""

import asyncio
import tempfile
from pathlib import Path

from file_chunking.services import (
    ChunkingService,
    ChunkStorageService,
    ReassemblyService,
    ChunkPublisherService,
    ChunkRequestService,
    LibraryCacheService
)
from file_chunking.database import (
    init_db, close_db,
    ManifestRepository,
    ChunkRepository
)


async def example_1_chunk_and_store_file():
    """
    Example 1: Chunk a file and store chunks locally.
    """
    print("\n" + "="*60)
    print("Example 1: Chunk and Store File")
    print("="*60)

    # Initialize database
    await init_db()

    # Create sample file
    sample_data = b"This is sample educational content. " * 1000  # ~36KB
    sample_file = "permaculture_intro.txt"

    # Initialize services
    chunking_service = ChunkingService(chunk_size=256 * 1024)  # 256KB chunks
    chunk_storage = ChunkStorageService()

    # Chunk the file
    print(f"\nChunking file: {sample_file}")
    manifest, chunks_data = chunking_service.chunk_bytes(
        file_content=sample_data,
        file_name=sample_file,
        mime_type="text/plain",
        tags=["education", "permaculture", "introduction"],
        description="Introduction to permaculture principles"
    )

    print(f"✓ File chunked successfully")
    print(f"  - File hash: {manifest.fileHash}")
    print(f"  - File size: {manifest.fileSize} bytes")
    print(f"  - Chunk count: {manifest.chunkCount}")
    print(f"  - Chunk size: {manifest.chunkSize} bytes")
    print(f"  - Merkle root: {manifest.merkleRoot}")

    # Save manifest to database
    await ManifestRepository.create(manifest)
    print(f"\n✓ Manifest saved to database")

    # Store chunks
    print(f"\nStoring {len(chunks_data)} chunk(s)...")
    for i, (chunk_metadata, chunk_data) in enumerate(chunks_data):
        success, error = await chunk_storage.store_chunk(chunk_metadata, chunk_data)
        if success:
            print(f"  ✓ Chunk {i}: {chunk_metadata.chunkHash[:20]}... ({chunk_metadata.chunkSize} bytes)")
        else:
            print(f"  ✗ Chunk {i} failed: {error}")

    # Mark manifest as complete
    await ManifestRepository.update_complete_status(manifest.fileHash, True)
    print(f"\n✓ All chunks stored successfully")

    # Get storage stats
    stats = await chunk_storage.get_storage_stats()
    print(f"\nStorage Statistics:")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Total size: {stats['total_size_mb']:.2f} MB")

    await close_db()
    return manifest.fileHash


async def example_2_reassemble_file(file_hash: str):
    """
    Example 2: Reassemble a file from stored chunks.
    """
    print("\n" + "="*60)
    print("Example 2: Reassemble File")
    print("="*60)

    await init_db()

    # Initialize services
    chunk_storage = ChunkStorageService()
    reassembly_service = ReassemblyService(chunk_storage)

    # Check if file is ready to reassemble
    print(f"\nChecking reassembly readiness for {file_hash[:30]}...")
    is_ready, error, missing_indices = await reassembly_service.check_reassembly_readiness(file_hash)

    if not is_ready:
        print(f"✗ File not ready: {error}")
        print(f"  Missing chunks: {missing_indices}")
        await close_db()
        return

    print(f"✓ File is ready to reassemble")

    # Get manifest
    manifest = await ManifestRepository.get(file_hash)
    print(f"\nReassembling file: {manifest.fileName}")
    print(f"  - Total chunks: {manifest.chunkCount}")
    print(f"  - File size: {manifest.fileSize} bytes")

    # Create temporary output file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        output_path = tmp.name

    # Reassemble file
    print(f"\nReassembling to: {output_path}")
    success, error = await reassembly_service.reassemble_file(file_hash, output_path)

    if success:
        print(f"✓ File reassembled successfully")

        # Verify reassembled file
        with open(output_path, 'rb') as f:
            reassembled_data = f.read()

        from file_chunking.services import HashingService
        actual_hash = HashingService.hash_file_content(reassembled_data)

        if actual_hash == file_hash:
            print(f"✓ Hash verification passed")
            print(f"  - Size: {len(reassembled_data)} bytes")
        else:
            print(f"✗ Hash verification failed!")

        # Cleanup
        import os
        os.unlink(output_path)
    else:
        print(f"✗ Reassembly failed: {error}")

    await close_db()


async def example_3_library_cache():
    """
    Example 3: Use library cache for popular files.
    """
    print("\n" + "="*60)
    print("Example 3: Library Cache Management")
    print("="*60)

    await init_db()

    # Initialize services
    chunk_storage = ChunkStorageService()
    library_cache = LibraryCacheService(
        chunk_storage=chunk_storage,
        cache_budget_bytes=10 * 1024 * 1024 * 1024  # 10GB
    )

    # Create and store a sample file
    print("\nCreating sample educational file...")
    sample_data = b"Educational content for the community. " * 5000  # ~200KB

    chunking_service = ChunkingService()
    manifest, chunks_data = chunking_service.chunk_bytes(
        sample_data,
        "community_guide.pdf",
        "application/pdf",
        tags=["education", "community", "popular"]
    )

    await ManifestRepository.create(manifest)

    for chunk_metadata, chunk_data in chunks_data:
        await chunk_storage.store_chunk(chunk_metadata, chunk_data)

    await ManifestRepository.update_complete_status(manifest.fileHash, True)

    print(f"✓ Sample file created: {manifest.fileName}")
    print(f"  - File hash: {manifest.fileHash}")

    # Add to library cache
    print(f"\nAdding to library cache...")
    success, error = await library_cache.add_to_cache(
        manifest.fileHash,
        tags=["education", "popular"]
    )

    if success:
        print(f"✓ File added to library cache")
    else:
        print(f"✗ Failed to add to cache: {error}")

    # Get cache stats
    print(f"\nCache Statistics:")
    stats = await library_cache.get_cache_stats()
    print(f"  - Total files: {stats['total_files']}")
    print(f"  - Total size: {stats['total_size_mb']:.2f} MB")
    print(f"  - Budget: {stats['budget_gb']:.2f} GB")
    print(f"  - Usage: {stats['usage_percentage']:.2f}%")

    # List cached files
    print(f"\nCached Files:")
    cached_files = await library_cache.get_cached_files(limit=10)
    for cached_file in cached_files:
        print(f"  - {cached_file['file_name']}")
        print(f"    Hash: {cached_file['file_hash'][:30]}...")
        print(f"    Size: {cached_file['file_size'] / 1024:.2f} KB")
        print(f"    Access count: {cached_file['access_count']}")
        print(f"    Priority score: {cached_file['priority_score']:.2f}")

    await close_db()


async def example_4_dtn_integration():
    """
    Example 4: Publish chunks to DTN network.

    Note: Requires DTN bundle system to be running.
    """
    print("\n" + "="*60)
    print("Example 4: DTN Integration (Publishing)")
    print("="*60)

    await init_db()

    # Create sample file
    sample_data = b"Knowledge to share with the network. " * 1000

    chunking_service = ChunkingService()
    manifest, chunks_data = chunking_service.chunk_bytes(
        sample_data,
        "shared_knowledge.txt",
        "text/plain",
        tags=["knowledge", "sharing"]
    )

    await ManifestRepository.create(manifest)

    chunk_storage = ChunkStorageService()
    for chunk_metadata, chunk_data in chunks_data:
        await chunk_storage.store_chunk(chunk_metadata, chunk_data)

    await ManifestRepository.update_complete_status(manifest.fileHash, True)

    print(f"✓ File prepared: {manifest.fileName}")
    print(f"  - Chunks: {manifest.chunkCount}")

    # Initialize DTN services (requires DTN system to be running)
    try:
        from app.services import CryptoService, BundleService

        print(f"\nInitializing DTN services...")
        crypto_service = CryptoService()
        bundle_service = BundleService(crypto_service)

        chunk_publisher = ChunkPublisherService(bundle_service, chunk_storage)

        # Publish manifest
        print(f"\nPublishing manifest...")
        manifest_bundle_id = await chunk_publisher.publish_manifest(manifest)

        if manifest_bundle_id:
            print(f"✓ Manifest published")
            print(f"  - Bundle ID: {manifest_bundle_id}")

        # Publish all chunks
        print(f"\nPublishing {manifest.chunkCount} chunks...")
        chunk_bundle_ids = await chunk_publisher.publish_all_chunks(manifest.fileHash)

        print(f"✓ Published {len(chunk_bundle_ids)} chunk bundles")
        for i, bundle_id in enumerate(chunk_bundle_ids[:3]):  # Show first 3
            print(f"  - Chunk {i}: {bundle_id}")
        if len(chunk_bundle_ids) > 3:
            print(f"  ... and {len(chunk_bundle_ids) - 3} more")

    except ImportError:
        print(f"\n⚠ DTN bundle system not available")
        print(f"  This example requires the DTN bundle system to be running")
        print(f"  See /Users/annhoward/src/solarpunk_utopia/app/main.py")

    await close_db()


async def main():
    """
    Run all examples.
    """
    print("\n" + "="*60)
    print("FILE CHUNKING SYSTEM - USAGE EXAMPLES")
    print("="*60)

    # Example 1: Chunk and store
    file_hash = await example_1_chunk_and_store_file()

    # Example 2: Reassemble
    await example_2_reassemble_file(file_hash)

    # Example 3: Library cache
    await example_3_library_cache()

    # Example 4: DTN integration
    await example_4_dtn_integration()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
