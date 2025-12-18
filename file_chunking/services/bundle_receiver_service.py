"""
Bundle Receiver Service

Integrates with DTN bundle system to receive and process file chunk bundles.
This service should be registered with the DTN system to handle incoming bundles.
"""

import logging
from typing import Optional
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import Bundle

from ..services import ChunkRequestService
from ..database import ManifestRepository

logger = logging.getLogger(__name__)


class BundleReceiverService:
    """
    Service for receiving and processing file chunk bundles from DTN system.

    This service should be called by the DTN bundle system when bundles
    with file-related payload types are received.
    """

    def __init__(self, chunk_request_service: ChunkRequestService):
        """
        Initialize bundle receiver service.

        Args:
            chunk_request_service: ChunkRequestService instance
        """
        self.chunk_request_service = chunk_request_service

    async def handle_received_bundle(self, bundle: Bundle) -> bool:
        """
        Handle a received bundle.

        Routes bundle to appropriate handler based on payload type.

        Args:
            bundle: Received bundle

        Returns:
            True if handled successfully, False otherwise
        """
        payload_type = bundle.payloadType

        if payload_type == "file:manifest":
            return await self._handle_manifest_bundle(bundle)
        elif payload_type == "file:chunk":
            return await self._handle_chunk_bundle(bundle)
        elif payload_type == "file:manifest_request":
            return await self._handle_manifest_request(bundle)
        elif payload_type == "file:chunk_request":
            return await self._handle_chunk_request(bundle)
        else:
            # Not a file-related bundle
            return False

    async def _handle_manifest_bundle(self, bundle: Bundle) -> bool:
        """
        Handle received manifest bundle.

        Args:
            bundle: Bundle containing file manifest

        Returns:
            True if handled successfully
        """
        try:
            logger.info(f"Received manifest bundle: {bundle.bundleId}")
            return await self.chunk_request_service.handle_manifest_response(bundle)
        except Exception as e:
            logger.error(f"Failed to handle manifest bundle: {str(e)}")
            return False

    async def _handle_chunk_bundle(self, bundle: Bundle) -> bool:
        """
        Handle received chunk bundle.

        Args:
            bundle: Bundle containing chunk data

        Returns:
            True if handled successfully
        """
        try:
            logger.info(f"Received chunk bundle: {bundle.bundleId}")
            return await self.chunk_request_service.handle_chunk_response(bundle)
        except Exception as e:
            logger.error(f"Failed to handle chunk bundle: {str(e)}")
            return False

    async def _handle_manifest_request(self, bundle: Bundle) -> bool:
        """
        Handle manifest request from another node.

        If we have the manifest, respond with it.

        Args:
            bundle: Bundle containing manifest request

        Returns:
            True if handled successfully
        """
        try:
            from ..models import ManifestRequest
            from ..services import ChunkPublisherService

            logger.info(f"Received manifest request: {bundle.bundleId}")

            # Parse request
            manifest_request = ManifestRequest(**bundle.payload)

            # Check if we have the manifest
            manifest = await ManifestRepository.get(manifest_request.fileHash)

            if manifest is None:
                logger.debug(f"Don't have manifest for {manifest_request.fileHash}")
                return False

            # We have the manifest - publish it
            from app.services import CryptoService, BundleService
            from .chunk_storage_service import ChunkStorageService

            crypto_service = CryptoService()
            bundle_service = BundleService(crypto_service)
            chunk_storage = ChunkStorageService()
            chunk_publisher = ChunkPublisherService(bundle_service, chunk_storage)

            bundle_id = await chunk_publisher.publish_manifest(manifest)

            if bundle_id:
                logger.info(f"Responded to manifest request with bundle {bundle_id}")
                return True
            else:
                logger.error("Failed to publish manifest in response to request")
                return False

        except Exception as e:
            logger.error(f"Failed to handle manifest request: {str(e)}")
            return False

    async def _handle_chunk_request(self, bundle: Bundle) -> bool:
        """
        Handle chunk request from another node.

        If we have the chunk, serve it.

        Args:
            bundle: Bundle containing chunk request

        Returns:
            True if handled successfully
        """
        try:
            from ..models import ChunkRequest
            from ..services import ChunkPublisherService

            logger.info(f"Received chunk request: {bundle.bundleId}")

            # Parse request
            chunk_request = ChunkRequest(**bundle.payload)

            # Try to serve the chunk
            from app.services import CryptoService, BundleService
            from .chunk_storage_service import ChunkStorageService

            crypto_service = CryptoService()
            bundle_service = BundleService(crypto_service)
            chunk_storage = ChunkStorageService()
            chunk_publisher = ChunkPublisherService(bundle_service, chunk_storage)

            bundle_id = await chunk_publisher.serve_chunk_request(
                chunk_request.chunkHash,
                chunk_request.requestId
            )

            if bundle_id:
                logger.info(f"Served chunk request with bundle {bundle_id}")
                return True
            else:
                logger.debug(f"Don't have chunk {chunk_request.chunkHash}")
                return False

        except Exception as e:
            logger.error(f"Failed to handle chunk request: {str(e)}")
            return False


# Integration point for DTN system
async def register_with_dtn_system():
    """
    Register this service with the DTN bundle system.

    This should be called on startup to ensure incoming file-related
    bundles are routed to this service.
    """
    from app.services import CryptoService, BundleService
    from .chunk_storage_service import ChunkStorageService

    crypto_service = CryptoService()
    bundle_service = BundleService(crypto_service)
    chunk_storage = ChunkStorageService()
    chunk_request_service = ChunkRequestService(bundle_service, chunk_storage)

    receiver_service = BundleReceiverService(chunk_request_service)

    logger.info("File chunking bundle receiver registered with DTN system")
    logger.info("Handling payload types: file:manifest, file:chunk, file:manifest_request, file:chunk_request")

    return receiver_service
