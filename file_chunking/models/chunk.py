"""
Chunk Data Models

Defines individual chunk metadata and status tracking.
Each chunk is content-addressed with SHA-256.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ChunkStatus(str, Enum):
    """Status of a chunk in the system"""
    STORED = "stored"  # Chunk is stored locally
    REQUESTED = "requested"  # Chunk has been requested but not yet received
    PENDING = "pending"  # Chunk is needed but not yet requested
    VERIFIED = "verified"  # Chunk received and hash verified


class ChunkMetadata(BaseModel):
    """
    Metadata for a single file chunk.

    Each chunk is content-addressed using SHA-256.
    Chunks are stored separately and referenced by their hash.
    """
    chunkHash: str  # SHA-256 hash of chunk content (format: chunk:sha256:...)
    chunkIndex: int  # Position in file (0-indexed)
    chunkSize: int  # Size in bytes
    fileHash: str  # Hash of the complete file this chunk belongs to
    status: ChunkStatus = ChunkStatus.PENDING
    storagePath: Optional[str] = None  # Local filesystem path if stored
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    verifiedAt: Optional[datetime] = None

    @field_validator('chunkHash')
    @classmethod
    def validate_chunk_hash(cls, v: str) -> str:
        """Validate chunk hash format"""
        if not v.startswith('chunk:sha256:'):
            raise ValueError('chunkHash must start with chunk:sha256:')
        if len(v) != 77:  # "chunk:sha256:" (13) + 64 hex chars
            raise ValueError('chunkHash must be 77 characters (chunk:sha256: + 64 hex)')
        return v

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        if len(v) != 76:  # "file:sha256:" (12) + 64 hex chars
            raise ValueError('fileHash must be 76 characters (file:sha256: + 64 hex)')
        return v

    @field_validator('chunkIndex')
    @classmethod
    def validate_chunk_index(cls, v: int) -> int:
        """Validate chunk index is non-negative"""
        if v < 0:
            raise ValueError('chunkIndex must be non-negative')
        return v

    @field_validator('chunkSize')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is positive and within limits"""
        if v <= 0:
            raise ValueError('chunkSize must be positive')
        if v > 1024 * 1024:  # 1MB max chunk size
            raise ValueError('chunkSize cannot exceed 1MB')
        return v

    def mark_stored(self, storage_path: str) -> None:
        """Mark chunk as stored locally"""
        self.status = ChunkStatus.STORED
        self.storagePath = storage_path

    def mark_verified(self) -> None:
        """Mark chunk as verified"""
        self.status = ChunkStatus.VERIFIED
        self.verifiedAt = datetime.now(timezone.utc)

    def mark_requested(self) -> None:
        """Mark chunk as requested"""
        self.status = ChunkStatus.REQUESTED

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
