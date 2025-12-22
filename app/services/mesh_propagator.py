"""Mesh Propagation Service

Unified DTN bundle creation and propagation for all mesh message types:
- Emergency alerts (rapid response)
- Burn notices (panic/trust revocations)
- Encrypted messages (E2E messaging)

All mesh communications go through this service to ensure consistent
bundle creation, signing, and propagation.
"""
import json
from typing import Optional
from datetime import datetime, timedelta, UTC

from app.services.bundle_service import BundleService
from app.models import BundleCreate, BundlePriority, AudienceType


class MeshPropagator:
    """Unified mesh propagation for all message types."""

    def __init__(self, bundle_service: BundleService):
        self.bundle_service = bundle_service

    async def propagate_alert(
        self,
        alert_id: str,
        alert_type: str,
        severity: str,
        cell_id: str,
        payload_data: dict
    ) -> str:
        """Create and propagate emergency alert bundle.

        Args:
            alert_id: Unique alert ID
            alert_type: Type of alert (ice_raid, checkpoint, etc.)
            severity: critical, urgent, watch
            cell_id: Cell that triggered the alert
            payload_data: Full alert data as dict

        Returns:
            Bundle ID
        """
        # Determine priority based on severity
        priority_map = {
            "critical": BundlePriority.EXPEDITED,
            "urgent": BundlePriority.NORMAL,
            "watch": BundlePriority.BULK
        }
        priority = priority_map.get(severity.lower(), BundlePriority.NORMAL)

        # Create bundle with multicast destination
        bundle_create = BundleCreate(
            audience=AudienceType.MULTICAST,
            topic=f"alerts.{alert_type}",
            tags=["rapid-response", f"severity:{severity}", f"cell:{cell_id}"],
            priority=priority,
            payloadType="application/json",
            payload=json.dumps(payload_data),
            hopLimit=10,  # Allow wide propagation for emergencies
            expiresAt=datetime.now(UTC) + timedelta(hours=24),  # 24 hour TTL
            receiptPolicy="delivery_report"
        )

        bundle = await self.bundle_service.create_bundle(bundle_create)
        return bundle.bundleId

    async def propagate_burn_notice(
        self,
        user_id: str,
        reason: str,
        issued_at: datetime,
        signed_by: str
    ) -> str:
        """Create and propagate burn notice bundle.

        Burn notices are trust revocations that need to reach the entire network.

        Args:
            user_id: User being burned
            reason: Reason code (duress_pin_entered, manual_trigger, etc.)
            issued_at: When notice was created
            signed_by: Public key of issuer

        Returns:
            Bundle ID
        """
        payload_data = {
            "user_id": user_id,
            "reason": reason,
            "issued_at": issued_at.isoformat(),
            "signed_by": signed_by,
            "type": "burn_notice"
        }

        # Burn notices are EXPEDITED to reach network quickly
        bundle_create = BundleCreate(
            audience=AudienceType.BROADCAST,  # Reach entire mesh
            topic="trust.revocations",
            tags=["burn-notice", f"user:{user_id}"],
            priority=BundlePriority.EXPEDITED,
            payloadType="application/json",
            payload=json.dumps(payload_data),
            hopLimit=20,  # Maximum propagation for trust updates
            expiresAt=datetime.now(UTC) + timedelta(days=7),  # 7 day TTL
            receiptPolicy="none"  # Don't need receipts for broadcasts
        )

        bundle = await self.bundle_service.create_bundle(bundle_create)
        return bundle.bundleId

    async def propagate_message(
        self,
        message_id: str,
        sender_id: str,
        recipient_id: str,
        encrypted_content: bytes,
        message_type: str = "direct",
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create and propagate encrypted message bundle.

        Args:
            message_id: Unique message ID
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            encrypted_content: Already-encrypted message bytes
            message_type: Type of message (direct, exchange, broadcast)
            expires_at: When message expires (default: 3 days)

        Returns:
            Bundle ID
        """
        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(days=3)

        payload_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "encrypted_content": encrypted_content.decode('utf-8') if isinstance(encrypted_content, bytes) else encrypted_content,
            "message_type": message_type,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Messages are DIRECT audience (unicast to specific recipient)
        bundle_create = BundleCreate(
            audience=AudienceType.DIRECT,
            topic=f"messages.{recipient_id}",  # Topic is recipient's inbox
            tags=["encrypted-message", f"sender:{sender_id}", f"recipient:{recipient_id}"],
            priority=BundlePriority.NORMAL,
            payloadType="application/json",
            payload=json.dumps(payload_data),
            hopLimit=15,  # Allow routing through mesh
            expiresAt=expires_at,
            receiptPolicy="delivery_report"  # Request delivery confirmation
        )

        bundle = await self.bundle_service.create_bundle(bundle_create)
        return bundle.bundleId

    async def propagate_broadcast_message(
        self,
        message_id: str,
        sender_id: str,
        cell_id: str,
        encrypted_content: bytes,
        recipient_count: int
    ) -> str:
        """Create and propagate cell broadcast message bundle.

        Args:
            message_id: Unique message ID
            sender_id: Sender (must be steward)
            cell_id: Cell to broadcast to
            encrypted_content: Encrypted message
            recipient_count: Number of recipients

        Returns:
            Bundle ID
        """
        payload_data = {
            "message_id": message_id,
            "sender_id": sender_id,
            "cell_id": cell_id,
            "encrypted_content": encrypted_content.decode('utf-8') if isinstance(encrypted_content, bytes) else encrypted_content,
            "message_type": "broadcast",
            "recipient_count": recipient_count,
            "timestamp": datetime.now(UTC).isoformat()
        }

        # Cell broadcasts are MULTICAST to cell members
        bundle_create = BundleCreate(
            audience=AudienceType.MULTICAST,
            topic=f"cells.{cell_id}.broadcasts",
            tags=["cell-broadcast", f"cell:{cell_id}", f"sender:{sender_id}"],
            priority=BundlePriority.NORMAL,
            payloadType="application/json",
            payload=json.dumps(payload_data),
            hopLimit=10,
            expiresAt=datetime.now(UTC) + timedelta(days=1),
            receiptPolicy="none"
        )

        bundle = await self.bundle_service.create_bundle(bundle_create)
        return bundle.bundleId
