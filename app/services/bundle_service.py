from datetime import datetime, timezone
from typing import Optional

from ..models import Bundle, BundleCreate, QueueName
from ..database import QueueManager
from .crypto_service import CryptoService


class BundleService:
    """
    Service for creating and validating DTN bundles.

    Handles:
    - Bundle creation with signing
    - Bundle validation (schema, signature, TTL)
    - Content-addressed bundleId generation
    """

    def __init__(self, crypto_service: CryptoService):
        self.crypto_service = crypto_service

    async def create_bundle(self, bundle_create: BundleCreate) -> Bundle:
        """
        Create a new signed bundle from input data.

        Steps:
        1. Calculate TTL if not provided
        2. Create bundle with temporary bundleId
        3. Generate canonical JSON
        4. Sign canonical JSON
        5. Calculate content-addressed bundleId
        6. Store in outbox queue

        Returns:
            Signed bundle ready for forwarding
        """
        now = datetime.now(timezone.utc)

        # Calculate TTL if not provided
        expires_at = bundle_create.expiresAt
        if expires_at is None:
            expires_at = Bundle.calculate_default_ttl(
                priority=bundle_create.priority,
                topic=bundle_create.topic,
                tags=bundle_create.tags,
                created_at=now
            )

        # Create bundle with placeholder bundleId
        bundle = Bundle(
            bundleId="b:sha256:placeholder",  # Will be replaced
            createdAt=now,
            expiresAt=expires_at,
            priority=bundle_create.priority,
            audience=bundle_create.audience,
            topic=bundle_create.topic,
            tags=bundle_create.tags,
            payloadType=bundle_create.payloadType,
            payload=bundle_create.payload,
            hopLimit=bundle_create.hopLimit,
            hopCount=0,
            receiptPolicy=bundle_create.receiptPolicy,
            signature="sig:placeholder",  # Will be replaced
            authorPublicKey=self.crypto_service.get_public_key_pem()
        )

        # Generate canonical JSON for signing
        canonical_json = bundle.to_canonical_json()

        # Sign bundle
        signature = self.crypto_service.sign(canonical_json)
        bundle.signature = signature

        # Calculate content-addressed bundleId
        bundle_id = bundle.calculate_bundle_id()
        bundle.bundleId = bundle_id

        # Store in outbox queue
        await QueueManager.enqueue(QueueName.OUTBOX, bundle)

        return bundle

    async def validate_bundle(self, bundle: Bundle) -> tuple[bool, Optional[str]]:
        """
        Validate a received bundle.

        Checks:
        1. Schema validation (handled by Pydantic)
        2. Signature verification
        3. TTL not expired
        4. Hop limit not exceeded
        5. BundleId matches content

        Returns:
            (is_valid, error_message)
        """
        # Check signature
        canonical_json = bundle.to_canonical_json()
        if not self.crypto_service.verify(
            canonical_json,
            bundle.signature,
            bundle.authorPublicKey
        ):
            return False, "Invalid signature"

        # Check bundleId matches content
        expected_id = bundle.calculate_bundle_id()
        if bundle.bundleId != expected_id:
            return False, f"BundleId mismatch: expected {expected_id}, got {bundle.bundleId}"

        # Check TTL
        if bundle.is_expired():
            return False, "Bundle expired"

        # Check hop limit
        if bundle.is_hop_limit_exceeded():
            return False, "Hop limit exceeded"

        return True, None

    async def receive_bundle(self, bundle: Bundle) -> tuple[bool, str]:
        """
        Receive a bundle from a peer.

        Steps:
        1. Validate bundle
        2. Check for duplicates in inbox/quarantine
        3. Move to inbox or quarantine
        4. Return result

        Returns:
            (success, message)
        """
        # Check if we already have this bundle in inbox or quarantine
        # (bundles in outbox/pending are locally created, receiving them is OK but will fail on enqueue)
        if await QueueManager.exists_in_queues(
            bundle.bundleId,
            [QueueName.INBOX, QueueName.QUARANTINE]
        ):
            return False, "Bundle already exists"

        # Validate bundle
        is_valid, error_msg = await self.validate_bundle(bundle)

        if not is_valid:
            # Move to quarantine
            await QueueManager.enqueue(QueueName.QUARANTINE, bundle)
            return False, f"Invalid bundle: {error_msg}"

        # Try to add to inbox
        # If bundle doesn't exist anywhere, enqueue will add it
        # If bundle exists in another queue, try to move it
        was_added = await QueueManager.enqueue(QueueName.INBOX, bundle)
        if was_added:
            return True, "Bundle received successfully"

        # Bundle already exists - check if we can move it from another queue
        existing_bundle = await QueueManager.get_bundle(bundle.bundleId)
        if not existing_bundle:
            return False, "Bundle processing failed"

        # If already in INBOX or QUARANTINE, it's a duplicate
        # (we already checked INBOX/QUARANTINE earlier, but double-check)
        if await QueueManager.exists_in_queues(
            bundle.bundleId,
            [QueueName.INBOX, QueueName.QUARANTINE]
        ):
            return False, "Bundle already exists"

        # Bundle exists in OUTBOX or PENDING - this means we created it locally
        # Move it to INBOX since we've now received confirmation it exists in the network
        # We need to find which queue it's in to move it
        for queue in [QueueName.OUTBOX, QueueName.PENDING, QueueName.DELIVERED, QueueName.EXPIRED]:
            moved = await QueueManager.move(bundle.bundleId, queue, QueueName.INBOX)
            if moved:
                return True, "Bundle received successfully (moved from outbox)"

        # Couldn't move it (shouldn't happen)
        return False, "Bundle exists but couldn't be moved"

    async def get_bundle(self, bundle_id: str) -> Optional[Bundle]:
        """Get a bundle by ID"""
        return await QueueManager.get_bundle(bundle_id)

    async def list_bundles(
        self,
        queue: QueueName,
        limit: int = 100,
        offset: int = 0
    ) -> list[Bundle]:
        """List bundles in a queue"""
        return await QueueManager.list_queue(queue, limit, offset)

    async def count_bundles(self, queue: QueueName) -> int:
        """Count bundles in a queue"""
        return await QueueManager.count_queue(queue)
