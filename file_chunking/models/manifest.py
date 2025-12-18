"""
File Manifest Models

Defines file-level metadata and Merkle tree structures.
The manifest contains all chunk hashes and verification data.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MerkleNode(BaseModel):
    """
    Node in a Merkle tree for chunk verification.

    The Merkle tree allows efficient verification of individual chunks
    and ensures file integrity.
    """
    hash: str  # SHA-256 hash of this node
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    isLeaf: bool = False

    @field_validator('hash')
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Validate hash is 64-character hex string"""
        if len(v) != 64:
            raise ValueError('hash must be 64 characters (SHA-256 hex)')
        # Verify it's valid hex
        try:
            int(v, 16)
        except ValueError:
            raise ValueError('hash must be valid hexadecimal')
        return v


class FileManifest(BaseModel):
    """
    Manifest for a chunked file.

    Contains metadata about the file and references to all chunks.
    The manifest itself is distributed as a DTN bundle.
    """
    fileHash: str  # SHA-256 hash of complete file (format: file:sha256:...)
    fileName: str  # Original filename
    fileSize: int  # Total file size in bytes
    mimeType: str  # MIME type (e.g., application/pdf, image/jpeg)
    chunkSize: int  # Size of each chunk (last chunk may be smaller)
    chunkCount: int  # Total number of chunks
    chunkHashes: List[str]  # Ordered list of chunk hashes
    merkleRoot: str  # Root hash of Merkle tree for verification
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    createdBy: Optional[str] = None  # Public key of creator
    tags: List[str] = Field(default_factory=list)  # Tags for categorization
    description: Optional[str] = None  # Optional description

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        if len(v) != 76:  # "file:sha256:" (12) + 64 hex chars
            raise ValueError('fileHash must be 76 characters')
        return v

    @field_validator('fileName')
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        """Validate filename is not empty"""
        if not v or not v.strip():
            raise ValueError('fileName cannot be empty')
        return v

    @field_validator('fileSize')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is positive"""
        if v <= 0:
            raise ValueError('fileSize must be positive')
        return v

    @field_validator('chunkSize')
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is within limits"""
        min_size = 256 * 1024  # 256KB
        max_size = 1024 * 1024  # 1MB
        if v < min_size or v > max_size:
            raise ValueError(f'chunkSize must be between {min_size} and {max_size} bytes')
        return v

    @field_validator('chunkCount')
    @classmethod
    def validate_chunk_count(cls, v: int) -> int:
        """Validate chunk count is positive"""
        if v <= 0:
            raise ValueError('chunkCount must be positive')
        return v

    @field_validator('chunkHashes')
    @classmethod
    def validate_chunk_hashes(cls, v: List[str]) -> List[str]:
        """Validate all chunk hashes are properly formatted"""
        if not v:
            raise ValueError('chunkHashes cannot be empty')
        for chunk_hash in v:
            if not chunk_hash.startswith('chunk:sha256:'):
                raise ValueError(f'Invalid chunk hash format: {chunk_hash}')
        return v

    @field_validator('merkleRoot')
    @classmethod
    def validate_merkle_root(cls, v: str) -> str:
        """Validate Merkle root is 64-character hex string"""
        if len(v) != 64:
            raise ValueError('merkleRoot must be 64 characters (SHA-256 hex)')
        try:
            int(v, 16)
        except ValueError:
            raise ValueError('merkleRoot must be valid hexadecimal')
        return v

    def verify_chunk_count(self) -> bool:
        """Verify chunk count matches number of chunk hashes"""
        return len(self.chunkHashes) == self.chunkCount

    def get_chunk_hash(self, index: int) -> Optional[str]:
        """Get chunk hash by index"""
        if 0 <= index < len(self.chunkHashes):
            return self.chunkHashes[index]
        return None

    def get_manifest_bundle_payload(self) -> dict:
        """
        Convert manifest to bundle payload format.

        The manifest is distributed as a DTN bundle with payloadType "file:manifest".
        """
        return {
            "fileHash": self.fileHash,
            "fileName": self.fileName,
            "fileSize": self.fileSize,
            "mimeType": self.mimeType,
            "chunkSize": self.chunkSize,
            "chunkCount": self.chunkCount,
            "chunkHashes": self.chunkHashes,
            "merkleRoot": self.merkleRoot,
            "createdAt": self.createdAt.isoformat(),
            "createdBy": self.createdBy,
            "tags": self.tags,
            "description": self.description
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
