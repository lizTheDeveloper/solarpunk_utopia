from enum import Enum


class QueueName(str, Enum):
    """Bundle queue names for lifecycle management"""
    INBOX = "inbox"  # Received bundles awaiting processing
    OUTBOX = "outbox"  # Locally-created bundles awaiting forwarding
    PENDING = "pending"  # Bundles awaiting opportunistic forwarding
    DELIVERED = "delivered"  # Acknowledged deliveries
    EXPIRED = "expired"  # Bundles dropped due to TTL expiration
    QUARANTINE = "quarantine"  # Invalid signatures or policy violations
