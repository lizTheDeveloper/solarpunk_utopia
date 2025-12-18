"""
Chunk Publisher Service

Publishes chunks and manifests as DTN bundles.
"""

import base64
import logging
import sys
from pathlib import Path
from typing import Optional, List

# Add app directory to path to import DTN services
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import BundleCreate, Priority, Audience, Topic
from app.services import BundleService

from ..models import FileManifest, ChunkMetadata, ChunkResponse
from .chunk_storage_service import ChunkStorageService

logger = logging.getLogger(__name__)


class ChunkPublisherService:
    """
    Service for publishing chunks and manifests as DTN bundles.

    Features:
    - Publish file manifests as bundles
    - Publish individual chunks as bundles
    - Serve chunk requests from library nodes
    - Long TTL for knowledge content
    """

    def __init__(
        self,
        bundle_service: BundleService,
        chunk_storage: ChunkStorageService
    ):
        """
        Initialize chunk publisher service.

        Args:
            bundle_service: DTN BundleService instance
            chunk_storage: ChunkStorageService instance
        """
        self.bundle_service = bundle_service
        self.chunk_storage = chunk_storage

    async def publish_manifest(
        self,
        manifest: FileManifest,
        priority: Priority = Priority.LOW,
        ttl_days: int = 270
    ) -> Optional[str]:
        """
        Publish file manifest as DTN bundle.

        Args:
            manifest: FileManifest to publish
            priority: Bundle priority (default: LOW for knowledge content)
            ttl_days: TTL in days (default: 270 days for knowledge)

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            # Create bundle payload
            payload = manifest.get_manifest_bundle_payload()

            # Determine topic based on tags
            topic = Topic.KNOWLEDGE
            if manifest.tags:
                tag_set = set(t.lower() for t in manifest.tags)
                if "education" in tag_set:
                    topic = Topic.EDUCATION
                elif "protocol" in tag_set or "lesson" in tag_set:
                    topic = Topic.KNOWLEDGE

            # Create bundle
            bundle_create = BundleCreate(
                payload=payload,
                payloadType="file:manifest",
                priority=priority,
                audience=Audience.PUBLIC,
                topic=topic,
                tags=["file-manifest", "chunking"] + manifest.tags,
                hopLimit=20
            )

            # Publish bundle
            bundle = await self.bundle_service.create_bundle(bundle_create)

            logger.info(f"Published manifest for {manifest.fileName} as bundle {bundle.bundleId}")
            return bundle.bundleId

        except Exception as e:
            logger.error(f"Failed to publish manifest: {str(e)}")
            return None

    async def publish_chunk(
        self,
        chunk_metadata: ChunkMetadata,
        chunk_data: bytes,
        request_id: Optional[str] = None,
        priority: Priority = Priority.LOW,
        ttl_days: int = 270
    ) -> Optional[str]:
        """
        Publish chunk as DTN bundle.

        Args:
            chunk_metadata: Metadata for the chunk
            chunk_data: Raw chunk data
            request_id: Optional request ID if responding to request
            priority: Bundle priority (default: LOW)
            ttl_days: TTL in days (default: 270 days)

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            # Encode chunk data as base64
            chunk_data_b64 = base64.b64encode(chunk_data).decode('utf-8')

            # Create chunk response payload
            chunk_response = ChunkResponse(
                chunkHash=chunk_metadata.chunkHash,
                fileHash=chunk_metadata.fileHash,
                chunkIndex=chunk_metadata.chunkIndex,
                chunkSize=chunk_metadata.chunkSize,
                chunkData=chunk_data_b64,
                requestId=request_id,
                providedBy=self.bundle_service.crypto_service.get_public_key_pem()
            )

            # Create bundle
            bundle_create = BundleCreate(
                payload=chunk_response.model_dump(),
                payloadType="file:chunk",
                priority=priority,
                audience=Audience.PUBLIC,
                topic=Topic.KNOWLEDGE,
                tags=["file-chunk", "chunking"],
                hopLimit=20
            )

            # Publish bundle
            bundle = await self.bundle_service.create_bundle(bundle_create)

            logger.info(f"Published chunk {chunk_metadata.chunkHash} as bundle {bundle.bundleId}")
            return bundle.bundleId

        except Exception as e:
            logger.error(f"Failed to publish chunk: {str(e)}")
            return None

    async def serve_chunk_request(
        self,
        chunk_hash: str,
        request_id: str,
        priority: Priority = Priority.NORMAL
    ) -> Optional[str]:
        """
        Serve a chunk request by publishing the chunk.

        Args:
            chunk_hash: Hash of requested chunk
            request_id: ID of the request
            priority: Bundle priority for response

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            # Retrieve chunk data
            chunk_data = await self.chunk_storage.retrieve_chunk(chunk_hash)
            if chunk_data is None:
                logger.warning(f"Cannot serve chunk request: chunk {chunk_hash} not found")
                return None

            # Get chunk metadata
            from ..database import ChunkRepository
            chunk_metadata = await ChunkRepository.get(chunk_hash)
            if chunk_metadata is None:
                logger.warning(f"Cannot serve chunk request: metadata for {chunk_hash} not found")
                return None

            # Publish chunk with request ID
            return await self.publish_chunk(
                chunk_metadata,
                chunk_data,
                request_id=request_id,
                priority=priority,
                ttl_days=30  # Shorter TTL for request responses
            )

        except Exception as e:
            logger.error(f"Failed to serve chunk request: {str(e)}")
            return None

    async def publish_all_chunks(
        self,
        file_hash: str,
        priority: Priority = Priority.LOW,
        ttl_days: int = 270
    ) -> List[str]:
        """
        Publish all chunks for a file.

        Useful for library nodes to pre-publish popular content.

        Args:
            file_hash: Hash of file whose chunks to publish
            priority: Bundle priority
            ttl_days: TTL in days

        Returns:
            List of published bundle IDs
        """
        try:
            from ..database import ChunkRepository

            # Get all chunks for file
            chunks = await ChunkRepository.get_by_file(file_hash)

            published_bundles = []

            for chunk in chunks:
                # Retrieve chunk data
                chunk_data = await self.chunk_storage.retrieve_chunk(chunk.chunkHash)
                if chunk_data is None:
                    logger.warning(f"Skipping chunk {chunk.chunkHash} - not found in storage")
                    continue

                # Publish chunk
                bundle_id = await self.publish_chunk(
                    chunk,
                    chunk_data,
                    priority=priority,
                    ttl_days=ttl_days
                )

                if bundle_id:
                    published_bundles.append(bundle_id)

            logger.info(f"Published {len(published_bundles)} chunks for file {file_hash}")
            return published_bundles

        except Exception as e:
            logger.error(f"Failed to publish all chunks: {str(e)}")
            return []

    async def republish_manifest(
        self,
        file_hash: str,
        priority: Priority = Priority.LOW
    ) -> Optional[str]:
        """
        Republish a file manifest (e.g., for refreshing TTL).

        Args:
            file_hash: Hash of file whose manifest to republish
            priority: Bundle priority

        Returns:
            Bundle ID if successful, None otherwise
        """
        try:
            from ..database import ManifestRepository

            # Get manifest
            manifest = await ManifestRepository.get(file_hash)
            if manifest is None:
                logger.warning(f"Cannot republish manifest: not found for {file_hash}")
                return None

            # Publish manifest
            return await self.publish_manifest(manifest, priority=priority)

        except Exception as e:
            logger.error(f"Failed to republish manifest: {str(e)}")
            return None
