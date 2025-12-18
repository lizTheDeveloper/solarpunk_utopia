"""
Download Status Models

Tracks file download progress and reassembly status.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DownloadStatus(str, Enum):
    """Status of a file download"""
    PENDING = "pending"  # Download not yet started
    REQUESTING_MANIFEST = "requesting_manifest"  # Requesting file manifest
    MANIFEST_RECEIVED = "manifest_received"  # Manifest received
    REQUESTING_CHUNKS = "requesting_chunks"  # Requesting individual chunks
    DOWNLOADING = "downloading"  # Chunks being received
    REASSEMBLING = "reassembling"  # Reassembling file from chunks
    VERIFYING = "verifying"  # Verifying final file hash
    COMPLETED = "completed"  # Download complete and verified
    FAILED = "failed"  # Download failed


class DownloadProgress(BaseModel):
    """
    Progress information for a file download.

    Tracks which chunks have been received and overall progress.
    """
    totalChunks: int
    receivedChunks: int
    missingChunks: List[int]  # Indices of missing chunks
    failedChunks: List[int] = Field(default_factory=list)  # Indices of chunks that failed verification
    bytesReceived: int = 0
    totalBytes: int
    percentComplete: float = 0.0

    @field_validator('percentComplete')
    @classmethod
    def validate_percent(cls, v: float) -> float:
        """Validate percentage is between 0 and 100"""
        if v < 0 or v > 100:
            raise ValueError('percentComplete must be between 0 and 100')
        return v

    def update_progress(self) -> None:
        """Recalculate progress percentage"""
        if self.totalChunks > 0:
            self.percentComplete = (self.receivedChunks / self.totalChunks) * 100.0
        else:
            self.percentComplete = 0.0

    def mark_chunk_received(self, chunk_index: int) -> None:
        """Mark a chunk as received"""
        if chunk_index in self.missingChunks:
            self.missingChunks.remove(chunk_index)
            self.receivedChunks += 1
            self.update_progress()

    def mark_chunk_failed(self, chunk_index: int) -> None:
        """Mark a chunk as failed verification"""
        if chunk_index not in self.failedChunks:
            self.failedChunks.append(chunk_index)

    def is_complete(self) -> bool:
        """Check if all chunks have been received"""
        return self.receivedChunks == self.totalChunks and len(self.missingChunks) == 0


class FileDownloadStatus(BaseModel):
    """
    Complete status of a file download operation.

    Tracks manifest, chunks, and overall download progress.
    """
    fileHash: str  # Hash of file being downloaded
    fileName: Optional[str] = None  # Filename (from manifest)
    fileSize: Optional[int] = None  # File size (from manifest)
    status: DownloadStatus = DownloadStatus.PENDING
    progress: Optional[DownloadProgress] = None
    manifestReceived: bool = False
    manifestHash: Optional[str] = None  # Hash of manifest bundle
    chunkHashes: List[str] = Field(default_factory=list)  # Ordered chunk hashes
    receivedChunkHashes: Dict[int, str] = Field(default_factory=dict)  # index -> hash
    startedAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: Optional[datetime] = None
    errorMessage: Optional[str] = None
    requestId: str  # Unique download request ID
    outputPath: Optional[str] = None  # Where to save completed file

    @field_validator('fileHash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """Validate file hash format"""
        if not v.startswith('file:sha256:'):
            raise ValueError('fileHash must start with file:sha256:')
        return v

    def initialize_from_manifest(
        self,
        file_name: str,
        file_size: int,
        chunk_hashes: List[str]
    ) -> None:
        """Initialize download tracking from received manifest"""
        self.fileName = file_name
        self.fileSize = file_size
        self.chunkHashes = chunk_hashes
        self.manifestReceived = True
        self.status = DownloadStatus.MANIFEST_RECEIVED

        # Initialize progress tracking
        total_chunks = len(chunk_hashes)
        self.progress = DownloadProgress(
            totalChunks=total_chunks,
            receivedChunks=0,
            missingChunks=list(range(total_chunks)),
            totalBytes=file_size,
            bytesReceived=0
        )

    def mark_chunk_received(self, chunk_index: int, chunk_hash: str, chunk_size: int) -> None:
        """Mark a chunk as received and verified"""
        if self.progress:
            self.receivedChunkHashes[chunk_index] = chunk_hash
            self.progress.mark_chunk_received(chunk_index)
            self.progress.bytesReceived += chunk_size

            # Update status
            if self.status == DownloadStatus.MANIFEST_RECEIVED:
                self.status = DownloadStatus.DOWNLOADING
            elif self.progress.is_complete():
                self.status = DownloadStatus.REASSEMBLING

    def mark_completed(self, output_path: str) -> None:
        """Mark download as completed"""
        self.status = DownloadStatus.COMPLETED
        self.completedAt = datetime.utcnow()
        self.outputPath = output_path

    def mark_failed(self, error_message: str) -> None:
        """Mark download as failed"""
        self.status = DownloadStatus.FAILED
        self.errorMessage = error_message
        self.completedAt = datetime.utcnow()

    def get_missing_chunk_indices(self) -> List[int]:
        """Get list of missing chunk indices"""
        if self.progress:
            return self.progress.missingChunks
        return []

    def get_progress_percentage(self) -> float:
        """Get download progress as percentage"""
        if self.progress:
            return self.progress.percentComplete
        return 0.0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
