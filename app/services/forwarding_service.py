import logging
from typing import List, Optional

from ..models import Bundle, Priority, Audience, QueueName
from ..database import QueueManager

logger = logging.getLogger(__name__)


class ForwardingService:
    """
    Forwarding policy engine for DTN bundles.

    Implements:
    1. Priority-based forwarding (emergency first)
    2. Audience enforcement (public, local, trusted, private)
    3. Hop limit tracking
    4. Forwarding queue management
    """

    def __init__(self):
        """Initialize forwarding service"""
        pass

    async def get_bundles_for_forwarding(
        self,
        max_bundles: int = 100
    ) -> List[Bundle]:
        """
        Get bundles ready for forwarding, ordered by priority.

        Priority order:
        1. emergency (never defer)
        2. perishable AND time-sensitive
        3. normal, audience=trusted/private
        4. normal, audience=public/local
        5. low

        Returns:
            List of bundles ready to forward
        """
        bundles = []

        # Emergency bundles (highest priority)
        emergency = await QueueManager.dequeue(
            QueueName.PENDING,
            limit=max_bundles,
            priority_filter=Priority.EMERGENCY
        )
        bundles.extend(emergency)

        # Perishable bundles
        remaining = max_bundles - len(bundles)
        if remaining > 0:
            perishable = await QueueManager.dequeue(
                QueueName.PENDING,
                limit=remaining,
                priority_filter=Priority.PERISHABLE
            )
            bundles.extend(perishable)

        # Normal priority bundles
        remaining = max_bundles - len(bundles)
        if remaining > 0:
            normal = await QueueManager.dequeue(
                QueueName.PENDING,
                limit=remaining,
                priority_filter=Priority.NORMAL
            )
            bundles.extend(normal)

        # Low priority bundles
        remaining = max_bundles - len(bundles)
        if remaining > 0:
            low = await QueueManager.dequeue(
                QueueName.PENDING,
                limit=remaining,
                priority_filter=Priority.LOW
            )
            bundles.extend(low)

        return bundles[:max_bundles]

    def can_forward_to_peer(
        self,
        bundle: Bundle,
        peer_trust_score: float = 0.5,
        peer_is_local: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Check if bundle can be forwarded to a specific peer.

        Audience enforcement:
        - PUBLIC: anyone may carry
        - LOCAL: only within community boundary (peer_is_local=True)
        - TRUSTED: only nodes meeting trust threshold (trust_score >= 0.7)
        - PRIVATE: encrypted direct delivery only (not implemented yet)

        Args:
            bundle: Bundle to forward
            peer_trust_score: Trust score of peer (0.0-1.0)
            peer_is_local: Whether peer is in local community

        Returns:
            (can_forward, reason)
        """
        # Check if bundle is expired
        if bundle.is_expired():
            return False, "Bundle expired"

        # Check if hop limit exceeded
        if bundle.is_hop_limit_exceeded():
            return False, "Hop limit exceeded"

        # Audience enforcement
        if bundle.audience == Audience.PUBLIC:
            # Anyone can carry
            return True, None

        if bundle.audience == Audience.LOCAL:
            # Only local peers
            if not peer_is_local:
                return False, "Bundle audience is LOCAL, peer not local"
            return True, None

        if bundle.audience == Audience.TRUSTED:
            # Only trusted peers (trust score >= 0.7)
            if peer_trust_score < 0.7:
                return False, f"Bundle audience is TRUSTED, peer trust score too low ({peer_trust_score})"
            return True, None

        if bundle.audience == Audience.PRIVATE:
            # Encrypted direct delivery only (not implemented yet)
            return False, "PRIVATE audience not yet implemented"

        return True, None

    async def forward_bundle(
        self,
        bundle: Bundle,
        peer_trust_score: float = 0.5,
        peer_is_local: bool = True
    ) -> tuple[bool, str]:
        """
        Forward a bundle to a peer.

        Steps:
        1. Check if forwarding is allowed
        2. Increment hop count
        3. Return bundle for transmission

        Args:
            bundle: Bundle to forward
            peer_trust_score: Trust score of peer
            peer_is_local: Whether peer is local

        Returns:
            (success, message)
        """
        # Check if forwarding is allowed
        can_forward, reason = self.can_forward_to_peer(
            bundle,
            peer_trust_score,
            peer_is_local
        )

        if not can_forward:
            return False, f"Cannot forward: {reason}"

        # Increment hop count
        bundle.increment_hop_count()

        # Update in database
        # Note: In a real implementation, we'd update the bundle in the database
        # For now, we just return success
        return True, "Bundle ready for forwarding"

    async def move_to_pending(self, bundle_id: str) -> bool:
        """
        Move a bundle from outbox to pending queue.

        This is called after a bundle has been created and is ready
        for opportunistic forwarding.

        Args:
            bundle_id: Bundle to move

        Returns:
            True if successful
        """
        return await QueueManager.move(
            bundle_id,
            QueueName.OUTBOX,
            QueueName.PENDING
        )

    async def mark_delivered(self, bundle_id: str) -> bool:
        """
        Mark a bundle as delivered (move to delivered queue).

        This is called when we receive a receipt acknowledgment.

        Args:
            bundle_id: Bundle that was delivered

        Returns:
            True if successful
        """
        # Try moving from pending first
        success = await QueueManager.move(
            bundle_id,
            QueueName.PENDING,
            QueueName.DELIVERED
        )

        # If not in pending, try outbox
        if not success:
            success = await QueueManager.move(
                bundle_id,
                QueueName.OUTBOX,
                QueueName.DELIVERED
            )

        return success

    async def get_forwarding_stats(self) -> dict:
        """Get statistics about forwarding queues"""
        outbox_count = await QueueManager.count_queue(QueueName.OUTBOX)
        pending_count = await QueueManager.count_queue(QueueName.PENDING)
        delivered_count = await QueueManager.count_queue(QueueName.DELIVERED)

        # Count by priority in pending queue
        pending_bundles = await QueueManager.list_queue(QueueName.PENDING, limit=1000)

        priority_counts = {
            Priority.EMERGENCY.value: 0,
            Priority.PERISHABLE.value: 0,
            Priority.NORMAL.value: 0,
            Priority.LOW.value: 0,
        }

        for bundle in pending_bundles:
            priority_counts[bundle.priority.value] += 1

        return {
            'outbox_count': outbox_count,
            'pending_count': pending_count,
            'delivered_count': delivered_count,
            'pending_by_priority': priority_counts
        }
