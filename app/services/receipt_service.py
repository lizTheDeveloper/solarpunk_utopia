"""
Receipt/Acknowledgment Service for DTN Bundles

Implements delivery confirmations and receipt handling according to ReceiptPolicy.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum

from ..models import Bundle, ReceiptPolicy
from ..database import QueueManager
from .bundle_service import BundleService


logger = logging.getLogger(__name__)


class ReceiptType(str, Enum):
    """Types of receipts"""
    RECEIVED = "received"  # Bundle received by destination
    FORWARDED = "forwarded"  # Bundle forwarded to next hop
    DELIVERED = "delivered"  # Bundle successfully delivered to final destination
    EXPIRED = "expired"  # Bundle expired before delivery
    DELETED = "deleted"  # Bundle was deleted (e.g., cache eviction)


class Receipt:
    """
    A receipt acknowledging bundle status.

    Receipts are themselves bundles that report on the status of another bundle.
    """

    def __init__(
        self,
        original_bundle_id: str,
        receipt_type: ReceiptType,
        reporter_node_id: str,
        timestamp: datetime,
        reason: Optional[str] = None
    ):
        self.original_bundle_id = original_bundle_id
        self.receipt_type = receipt_type
        self.reporter_node_id = reporter_node_id
        self.timestamp = timestamp
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary"""
        return {
            "original_bundle_id": self.original_bundle_id,
            "receipt_type": self.receipt_type.value,
            "reporter_node_id": self.reporter_node_id,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Receipt":
        """Create receipt from dictionary"""
        return cls(
            original_bundle_id=data["original_bundle_id"],
            receipt_type=ReceiptType(data["receipt_type"]),
            reporter_node_id=data["reporter_node_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            reason=data.get("reason")
        )


class ReceiptService:
    """
    Service for managing bundle receipts and acknowledgments.

    Handles:
    - Generating receipts based on ReceiptPolicy
    - Sending receipt bundles back to originators
    - Tracking delivery status
    """

    def __init__(self, bundle_service: BundleService, node_id: str):
        """
        Initialize receipt service.

        Args:
            bundle_service: Bundle service for creating receipt bundles
            node_id: Identifier for this node (for receipt attribution)
        """
        self.bundle_service = bundle_service
        self.node_id = node_id

    async def generate_receipt(
        self,
        bundle: Bundle,
        receipt_type: ReceiptType,
        reason: Optional[str] = None
    ) -> Optional[Bundle]:
        """
        Generate a receipt bundle for another bundle.

        Args:
            bundle: Original bundle to receipt
            receipt_type: Type of receipt
            reason: Optional reason (e.g., for expired/deleted)

        Returns:
            Receipt bundle if policy requires it, None otherwise
        """
        # Check if receipt is required
        if not self._should_send_receipt(bundle, receipt_type):
            logger.debug(f"Receipt not required for bundle {bundle.bundleId} (policy: {bundle.receiptPolicy})")
            return None

        # Create receipt payload
        receipt = Receipt(
            original_bundle_id=bundle.bundleId,
            receipt_type=receipt_type,
            reporter_node_id=self.node_id,
            timestamp=datetime.now(timezone.utc),
            reason=reason
        )

        # Determine who to send receipt to (bundle originator)
        # In a real system, we'd extract the return address from the bundle
        # For now, we'll send back to the author's public key fingerprint
        recipient = bundle.authorPublicKey[:16]  # Short fingerprint

        logger.info(
            f"Generating {receipt_type.value} receipt for bundle {bundle.bundleId} "
            f"from node {self.node_id} to {recipient}"
        )

        # Create receipt bundle
        from ..models.bundle import BundleCreate
        from ..models.priority import Priority, Audience, Topic

        receipt_bundle_create = BundleCreate(
            payload=receipt.to_dict(),
            payloadType="dtn:receipt",
            topic=Topic.COORDINATION,
            priority=Priority.NORMAL,  # Receipts are normal priority
            audience=Audience.PRIVATE,  # Receipts are private
            tags=["receipt", receipt_type.value],
            ttl_hours=24  # Receipts have 24 hour TTL
        )

        receipt_bundle = await self.bundle_service.create_bundle(receipt_bundle_create)
        logger.info(f"Created receipt bundle: {receipt_bundle.bundleId}")

        return receipt_bundle

    def _should_send_receipt(self, bundle: Bundle, receipt_type: ReceiptType) -> bool:
        """
        Check if a receipt should be sent based on bundle's receipt policy.

        Args:
            bundle: Bundle to check
            receipt_type: Type of receipt being considered

        Returns:
            True if receipt should be sent
        """
        policy = bundle.receiptPolicy

        if policy == ReceiptPolicy.NONE:
            return False

        if policy == ReceiptPolicy.RECEIVED:
            # Only send receipt when first received
            return receipt_type == ReceiptType.RECEIVED

        if policy == ReceiptPolicy.FORWARDED:
            # Send receipt for received and forwarded
            return receipt_type in [ReceiptType.RECEIVED, ReceiptType.FORWARDED]

        if policy == ReceiptPolicy.DELIVERED:
            # Send receipt for all delivery-related events
            return receipt_type in [
                ReceiptType.RECEIVED,
                ReceiptType.FORWARDED,
                ReceiptType.DELIVERED
            ]

        if policy == ReceiptPolicy.ALL:
            # Send receipt for all events including errors
            return True

        return False

    async def handle_bundle_received(self, bundle: Bundle) -> None:
        """
        Handle receipt generation when a bundle is received.

        Args:
            bundle: Bundle that was received
        """
        receipt_bundle = await self.generate_receipt(
            bundle,
            ReceiptType.RECEIVED
        )

        if receipt_bundle:
            # Receipt bundle is already in outbox (created by bundle_service)
            logger.info(f"Receipt sent for received bundle {bundle.bundleId}")

    async def handle_bundle_forwarded(self, bundle: Bundle, next_hop: str) -> None:
        """
        Handle receipt generation when a bundle is forwarded.

        Args:
            bundle: Bundle that was forwarded
            next_hop: Node ID that bundle was forwarded to
        """
        receipt_bundle = await self.generate_receipt(
            bundle,
            ReceiptType.FORWARDED,
            reason=f"Forwarded to {next_hop}"
        )

        if receipt_bundle:
            logger.info(f"Receipt sent for forwarded bundle {bundle.bundleId}")

    async def handle_bundle_delivered(self, bundle: Bundle) -> None:
        """
        Handle receipt generation when a bundle is delivered to final destination.

        Args:
            bundle: Bundle that was delivered
        """
        receipt_bundle = await self.generate_receipt(
            bundle,
            ReceiptType.DELIVERED
        )

        if receipt_bundle:
            logger.info(f"Receipt sent for delivered bundle {bundle.bundleId}")

    async def handle_bundle_expired(self, bundle: Bundle) -> None:
        """
        Handle receipt generation when a bundle expires.

        Args:
            bundle: Bundle that expired
        """
        receipt_bundle = await self.generate_receipt(
            bundle,
            ReceiptType.EXPIRED,
            reason="Bundle TTL expired"
        )

        if receipt_bundle:
            logger.info(f"Receipt sent for expired bundle {bundle.bundleId}")

    async def handle_bundle_deleted(self, bundle: Bundle, reason: str) -> None:
        """
        Handle receipt generation when a bundle is deleted.

        Args:
            bundle: Bundle that was deleted
            reason: Reason for deletion
        """
        receipt_bundle = await self.generate_receipt(
            bundle,
            ReceiptType.DELETED,
            reason=reason
        )

        if receipt_bundle:
            logger.info(f"Receipt sent for deleted bundle {bundle.bundleId}")

    async def process_receipt_bundle(self, receipt_bundle: Bundle) -> Optional[Receipt]:
        """
        Process a received receipt bundle.

        Args:
            receipt_bundle: Bundle containing a receipt

        Returns:
            Parsed receipt if valid, None otherwise
        """
        if receipt_bundle.payloadType != "dtn:receipt":
            logger.warning(f"Bundle {receipt_bundle.bundleId} is not a receipt")
            return None

        try:
            receipt = Receipt.from_dict(receipt_bundle.payload)
            logger.info(
                f"Received {receipt.receipt_type.value} receipt for bundle "
                f"{receipt.original_bundle_id} from node {receipt.reporter_node_id}"
            )
            return receipt

        except Exception as e:
            logger.error(f"Failed to parse receipt bundle: {e}")
            return None

    async def get_bundle_receipts(self, bundle_id: str) -> List[Receipt]:
        """
        Get all receipts for a specific bundle.

        This searches the inbox for receipt bundles related to the given bundle ID.

        Args:
            bundle_id: Bundle ID to find receipts for

        Returns:
            List of receipts
        """
        from ..models import QueueName

        # Search inbox for receipts
        all_bundles = await QueueManager.list_queue(QueueName.INBOX, limit=1000)

        receipts = []
        for bundle in all_bundles:
            if bundle.payloadType == "dtn:receipt":
                try:
                    receipt = Receipt.from_dict(bundle.payload)
                    if receipt.original_bundle_id == bundle_id:
                        receipts.append(receipt)
                except Exception as e:
                    logger.debug(f"Skipping invalid receipt bundle: {e}")

        return receipts

    async def get_bundle_delivery_status(self, bundle_id: str) -> Dict[str, Any]:
        """
        Get comprehensive delivery status for a bundle.

        Args:
            bundle_id: Bundle ID to check status for

        Returns:
            Status dictionary with receipt timeline
        """
        receipts = await self.get_bundle_receipts(bundle_id)

        status = {
            "bundle_id": bundle_id,
            "receipt_count": len(receipts),
            "received": False,
            "forwarded": False,
            "delivered": False,
            "expired": False,
            "deleted": False,
            "timeline": []
        }

        for receipt in receipts:
            status["timeline"].append({
                "type": receipt.receipt_type.value,
                "node": receipt.reporter_node_id,
                "timestamp": receipt.timestamp.isoformat(),
                "reason": receipt.reason
            })

            # Update status flags
            if receipt.receipt_type == ReceiptType.RECEIVED:
                status["received"] = True
            elif receipt.receipt_type == ReceiptType.FORWARDED:
                status["forwarded"] = True
            elif receipt.receipt_type == ReceiptType.DELIVERED:
                status["delivered"] = True
            elif receipt.receipt_type == ReceiptType.EXPIRED:
                status["expired"] = True
            elif receipt.receipt_type == ReceiptType.DELETED:
                status["deleted"] = True

        # Sort timeline by timestamp
        status["timeline"].sort(key=lambda x: x["timestamp"])

        return status
