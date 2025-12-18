"""
File Chunking System - Data Models

Defines the core data structures for content-addressed file chunking:
- ChunkMetadata: Individual chunk information
- FileManifest: File-level metadata with chunk references
- ChunkRequest: Request for missing chunks
- ChunkResponse: Response with chunk data
- FileDownloadStatus: Track file download progress
"""

from .chunk import ChunkMetadata, ChunkStatus
from .manifest import FileManifest, MerkleNode
from .request import ChunkRequest, ChunkResponse, FileRequest, ManifestRequest
from .download import FileDownloadStatus, DownloadStatus, DownloadProgress

__all__ = [
    "ChunkMetadata",
    "ChunkStatus",
    "FileManifest",
    "MerkleNode",
    "ChunkRequest",
    "ChunkResponse",
    "FileRequest",
    "ManifestRequest",
    "FileDownloadStatus",
    "DownloadStatus",
    "DownloadProgress",
]
