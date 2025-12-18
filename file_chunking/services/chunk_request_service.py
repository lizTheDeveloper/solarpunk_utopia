"""
Chunk Request Service

Handles chunk requests and file download orchestration.
"""

import base64
import logging
import uuid
from datetime import datetime
from typing import Optional, List
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import BundleCreate, Priority, Audience, Topic, Bundle
from app.services import BundleService

from ..models import (
    FileRequest, ChunkRequest, ManifestRequest,
    ChunkResponse, FileManifest, ChunkMetadata,
    FileDownloadStatus, DownloadStatus, ChunkStatus
)
from ..database import (
    ManifestRepository, ChunkRepository, DownloadRepository
)
from .chunk_storage_service import ChunkStorageService
from .hashing_service import HashingService

logger = logging.getLogger(__name__)


class ChunkRequestService:
    """
    Service for requesting chunks and orchestrating file downloads.

    Features:
    - Request file manifests
    - Request individual chunks
    - Track download progress
    - Resume interrupted downloads
    """

    def __init__(
        self,
        bundle_service: BundleService,
        chunk_storage: ChunkStorageService
    ):
        """
        Initialize chunk request service.

        Args:
            bundle_service: DTN BundleService instance
            chunk_storage: ChunkStorageService instance
        """
        self.bundle_service = bundle_service
        self.chunk_storage = chunk_storage

    async def request_file(
        self,
        file_hash: str,
        output_path: str,
        priority: int = 5
    ) -> str:
        """
        Request a complete file download.

        This initiates the download process:
        1. Request manifest
        2. Wait for manifest
        3. Request missing chunks
        4. Reassemble when complete

        Args:
            file_hash: Hash of file to download
            output_path: Where to save completed file
            priority: Download priority (1-10)

        Returns:
            Request ID for tracking
        """
        try:
            request_id = f"req:{uuid.uuid4().hex}"

            # Create download status record
            download_status = FileDownloadStatus(
                fileHash=file_hash,
                requestId=request_id,
                status=DownloadStatus.REQUESTING_MANIFEST,
                outputPath=output_path
            )

            await DownloadRepository.create(download_status)

            # Check if we already have the manifest
            manifest = await ManifestRepository.get(file_hash)

            if manifest:
                # We have manifest, initialize download tracking
                download_status.initialize_from_manifest(
                    manifest.fileName,
                    manifest.fileSize,
                    manifest.chunkHashes
                )
                download_status.status = DownloadStatus.REQUESTING_CHUNKS

                await DownloadRepository.update(download_status)

                # Request missing chunks
                await self._request_missing_chunks(file_hash, request_id, priority)
            else:
                # Request manifest
                await self.request_manifest(file_hash, request_id)

            logger.info(f"Initiated file request {request_id} for {file_hash}")
            return request_id

        except Exception as e:
            logger.error(f"Failed to request file: {str(e)}")
            raise

    async def request_manifest(
        self,
        file_hash: str,
        request_id: str
    ) -> Optional[str]:
        """
        Request a file manifest via DTN bundle.

        Args:
            file_hash: Hash of file whose manifest to request
            request_id: Request ID for tracking

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            # Create manifest request
            manifest_request = ManifestRequest(
                fileHash=file_hash,
                requestId=request_id,
                requestedBy=self.bundle_service.crypto_service.get_public_key_pem()
            )

            # Create bundle
            bundle_create = BundleCreate(
                payload=manifest_request.model_dump(),
                payloadType="file:manifest_request",
                priority=Priority.NORMAL,
                audience=Audience.PUBLIC,
                topic=Topic.COORDINATION,
                tags=["file-request", "manifest-request"],
                hopLimit=20
            )

            # Publish bundle
            bundle = await self.bundle_service.create_bundle(bundle_create)

            logger.info(f"Requested manifest for {file_hash} with request {request_id}")
            return bundle.bundleId

        except Exception as e:
            logger.error(f"Failed to request manifest: {str(e)}")
            return None

    async def request_chunk(
        self,
        chunk_hash: str,
        file_hash: str,
        request_id: str
    ) -> Optional[str]:
        """
        Request a specific chunk via DTN bundle.

        Args:
            chunk_hash: Hash of chunk to request
            file_hash: Hash of file this chunk belongs to
            request_id: Request ID for tracking

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            # Create chunk request
            chunk_request = ChunkRequest(
                chunkHash=chunk_hash,
                fileHash=file_hash,
                requestId=request_id,
                requestedBy=self.bundle_service.crypto_service.get_public_key_pem()
            )

            # Create bundle
            bundle_create = BundleCreate(
                payload=chunk_request.model_dump(),
                payloadType="file:chunk_request",
                priority=Priority.NORMAL,
                audience=Audience.PUBLIC,
                topic=Topic.COORDINATION,
                tags=["file-request", "chunk-request"],
                hopLimit=20
            )

            # Publish bundle
            bundle = await self.bundle_service.create_bundle(bundle_create)

            # Update chunk status to REQUESTED
            if await ChunkRepository.exists(chunk_hash):
                await ChunkRepository.update_status(chunk_hash, ChunkStatus.REQUESTED)

            logger.debug(f"Requested chunk {chunk_hash}")
            return bundle.bundleId

        except Exception as e:
            logger.error(f"Failed to request chunk: {str(e)}")
            return None

    async def handle_manifest_response(self, bundle: Bundle) -> bool:
        """
        Handle received manifest bundle.

        Args:
            bundle: Bundle containing manifest data

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            if bundle.payloadType != "file:manifest":
                return False

            # Parse manifest
            manifest = FileManifest(**bundle.payload)

            # Save manifest to database
            if not await ManifestRepository.exists(manifest.fileHash):
                await ManifestRepository.create(manifest)
                logger.info(f"Received manifest for {manifest.fileName} ({manifest.fileHash})")

            # Check if this manifest is being waited for by any downloads
            downloads = await DownloadRepository.get_by_file(manifest.fileHash)

            for download in downloads:
                if download.status == DownloadStatus.REQUESTING_MANIFEST:
                    # Initialize download with manifest data
                    download.initialize_from_manifest(
                        manifest.fileName,
                        manifest.fileSize,
                        manifest.chunkHashes
                    )
                    download.status = DownloadStatus.REQUESTING_CHUNKS

                    await DownloadRepository.update(download)

                    # Request missing chunks
                    await self._request_missing_chunks(
                        manifest.fileHash,
                        download.requestId,
                        priority=5
                    )

            return True

        except Exception as e:
            logger.error(f"Failed to handle manifest response: {str(e)}")
            return False

    async def handle_chunk_response(self, bundle: Bundle) -> bool:
        """
        Handle received chunk bundle.

        Args:
            bundle: Bundle containing chunk data

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            if bundle.payloadType != "file:chunk":
                return False

            # Parse chunk response
            chunk_response = ChunkResponse(**bundle.payload)

            # Decode chunk data
            chunk_data = base64.b64decode(chunk_response.chunkData)

            # Verify chunk hash
            if not HashingService.verify_chunk_hash(chunk_data, chunk_response.chunkHash):
                logger.error(f"Chunk hash verification failed for {chunk_response.chunkHash}")
                return False

            # Create chunk metadata
            chunk_metadata = ChunkMetadata(
                chunkHash=chunk_response.chunkHash,
                chunkIndex=chunk_response.chunkIndex,
                chunkSize=chunk_response.chunkSize,
                fileHash=chunk_response.fileHash,
                status=ChunkStatus.PENDING
            )

            # Store chunk
            success, error = await self.chunk_storage.store_chunk(chunk_metadata, chunk_data)

            if not success:
                logger.error(f"Failed to store chunk: {error}")
                return False

            logger.info(f"Received and stored chunk {chunk_response.chunkHash}")

            # Update download progress
            await self._update_download_progress(
                chunk_response.fileHash,
                chunk_response.chunkIndex,
                chunk_response.chunkSize
            )

            return True

        except Exception as e:
            logger.error(f"Failed to handle chunk response: {str(e)}")
            return False

    async def _request_missing_chunks(
        self,
        file_hash: str,
        request_id: str,
        priority: int = 5
    ) -> None:
        """
        Request all missing chunks for a file.

        Args:
            file_hash: Hash of file
            request_id: Request ID
            priority: Request priority
        """
        try:
            # Get manifest
            manifest = await ManifestRepository.get(file_hash)
            if not manifest:
                logger.error(f"Cannot request chunks: manifest not found for {file_hash}")
                return

            # Get stored chunks
            stored_chunks = await ChunkRepository.get_by_file(file_hash)
            stored_hashes = set(chunk.chunkHash for chunk in stored_chunks)

            # Request missing chunks
            for chunk_hash in manifest.chunkHashes:
                if chunk_hash not in stored_hashes:
                    await self.request_chunk(chunk_hash, file_hash, request_id)

            logger.info(f"Requested {len(manifest.chunkHashes) - len(stored_hashes)} missing chunks for {file_hash}")

        except Exception as e:
            logger.error(f"Failed to request missing chunks: {str(e)}")

    async def _update_download_progress(
        self,
        file_hash: str,
        chunk_index: int,
        chunk_size: int
    ) -> None:
        """
        Update download progress when a chunk is received.

        Args:
            file_hash: Hash of file
            chunk_index: Index of received chunk
            chunk_size: Size of received chunk
        """
        try:
            # Get active downloads for this file
            downloads = await DownloadRepository.get_by_file(file_hash)

            for download in downloads:
                if download.status not in [DownloadStatus.COMPLETED, DownloadStatus.FAILED]:
                    # Get manifest
                    manifest = await ManifestRepository.get(file_hash)
                    if not manifest:
                        continue

                    # Mark chunk received
                    download.mark_chunk_received(chunk_index, manifest.chunkHashes[chunk_index], chunk_size)

                    # Check if download is complete
                    if download.progress and download.progress.is_complete():
                        download.status = DownloadStatus.REASSEMBLING

                    await DownloadRepository.update(download)

        except Exception as e:
            logger.error(f"Failed to update download progress: {str(e)}")

    async def get_download_status(self, request_id: str) -> Optional[FileDownloadStatus]:
        """
        Get status of a download.

        Args:
            request_id: Request ID

        Returns:
            FileDownloadStatus or None
        """
        return await DownloadRepository.get(request_id)

    async def cancel_download(self, request_id: str) -> bool:
        """
        Cancel a download.

        Args:
            request_id: Request ID

        Returns:
            True if cancelled, False otherwise
        """
        try:
            download = await DownloadRepository.get(request_id)
            if not download:
                return False

            download.mark_failed("Download cancelled by user")
            await DownloadRepository.update(download)

            logger.info(f"Cancelled download {request_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel download: {str(e)}")
            return False
