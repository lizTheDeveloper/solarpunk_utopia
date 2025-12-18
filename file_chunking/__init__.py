"""
File Chunking System (TIER 1)

Complete production system for content-addressed file chunking with DTN integration.

Features:
- Content-addressed storage (SHA-256)
- File chunking (256KB-1MB chunks)
- Merkle tree verification
- DTN bundle distribution
- Opportunistic retrieval
- Library node caching
- Resume partial downloads

System 1: Content-Addressed Storage (1.0 systems)
- SHA-256 content addressing
- Store chunks locally (SQLite + filesystem)
- Chunk metadata database
- Deduplication

System 2: Chunking Engine (1.2 systems)
- Split files into 256KB-1MB chunks
- Generate manifest with chunk hashes
- Merkle tree for verification
- Support for large files (100MB+)

System 3: Opportunistic Retrieval (0.8 systems)
- Request missing chunks via DTN bundles
- Reassembly with verification
- Resume partial downloads
- Library nodes serve popular chunks
"""

__version__ = "1.0.0"
__author__ = "Solarpunk Community"

from .models import (
    ChunkMetadata, ChunkStatus,
    FileManifest, MerkleNode,
    ChunkRequest, ChunkResponse, FileRequest,
    FileDownloadStatus, DownloadProgress
)

from .services import (
    HashingService,
    ChunkingService,
    MerkleTreeService,
    ChunkStorageService,
    ReassemblyService,
    ChunkPublisherService,
    ChunkRequestService,
    LibraryCacheService
)

from .database import (
    init_db, close_db,
    ChunkRepository,
    ManifestRepository,
    DownloadRepository
)

__all__ = [
    # Models
    "ChunkMetadata", "ChunkStatus",
    "FileManifest", "MerkleNode",
    "ChunkRequest", "ChunkResponse", "FileRequest",
    "FileDownloadStatus", "DownloadStatus", "DownloadProgress",

    # Services
    "HashingService",
    "ChunkingService",
    "MerkleTreeService",
    "ChunkStorageService",
    "ReassemblyService",
    "ChunkPublisherService",
    "ChunkRequestService",
    "LibraryCacheService",

    # Database
    "init_db", "close_db",
    "ChunkRepository",
    "ManifestRepository",
    "DownloadRepository",
]
