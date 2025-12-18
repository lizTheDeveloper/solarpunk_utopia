"""
Request/Response Models

Defines structures for requesting and responding to chunk/file requests.
These are transmitted as DTN bundle payloads.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ChunkRequest(BaseModel):
    """
    Request for a specific chunk.

    Sent as DTN bundle with payloadType "file:chunk_request".
    """
    chunkHash: str  # Hash of requested chunk
    fileHash: str  # Hash of file this chunk belongs to
    requestId: str  # Unique request ID
    requestedBy: str  # Public key of requester
    requestedAt: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('chunkHash')
    @classmethod
    def validate_chunk_hash(cls, v: str) -> str:
        """Validate chunk hash format"""
        if not v.startswith('chunk:sha256:'):
            raise ValueError('chunkHash must start with chunk:sha256:')
        return v

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChunkResponse(BaseModel):
    """
    Response containing chunk data.

    Sent as DTN bundle with payloadType "file:chunk".
    The chunk data is base64-encoded in the payload.
    """
    chunkHash: str  # Hash of this chunk
    fileHash: str  # Hash of file this chunk belongs to
    chunkIndex: int  # Position in file
    chunkSize: int  # Size of chunk data
    chunkData: str  # Base64-encoded chunk data
    requestId: Optional[str] = None  # ID of original request (if responding to request)
    providedBy: str  # Public key of provider
    providedAt: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('chunkHash')
    @classmethod
    def validate_chunk_hash(cls, v: str) -> str:
        """Validate chunk hash format"""
        if not v.startswith('chunk:sha256:'):
            raise ValueError('chunkHash must start with chunk:sha256:')
        return v

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
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
        """Validate chunk size is positive"""
        if v <= 0:
            raise ValueError('chunkSize must be positive')
        if v > 1024 * 1024:  # 1MB max
            raise ValueError('chunkSize cannot exceed 1MB')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileRequest(BaseModel):
    """
    Request for a complete file.

    This triggers manifest retrieval followed by chunk requests.
    Sent as DTN bundle with payloadType "file:file_request".
    """
    fileHash: str  # Hash of requested file
    requestId: str  # Unique request ID
    requestedBy: str  # Public key of requester
    requestedAt: datetime = Field(default_factory=datetime.utcnow)
    priority: int = Field(default=5, ge=1, le=10)  # Request priority (1=low, 10=urgent)
    requestedChunks: Optional[List[str]] = None  # Specific chunks if resuming download

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        return v

    @field_validator('requestedChunks')
    @classmethod
    def validate_requested_chunks(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate chunk hashes if provided"""
        if v is not None:
            for chunk_hash in v:
                if not chunk_hash.startswith('chunk:sha256:'):
                    raise ValueError(f'Invalid chunk hash: {chunk_hash}')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ManifestRequest(BaseModel):
    """
    Request for a file manifest.

    Sent as DTN bundle with payloadType "file:manifest_request".
    """
    fileHash: str  # Hash of file whose manifest is requested
    requestId: str  # Unique request ID
    requestedBy: str  # Public key of requester
    requestedAt: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
