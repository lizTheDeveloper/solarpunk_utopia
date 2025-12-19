from datetime import datetime, timedelta, timezone
from typing import Any, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json
import hashlib

from .priority import Priority, Audience, ReceiptPolicy, Topic


class BundleCreate(BaseModel):
    """Input model for creating a new bundle"""
    payload: dict[str, Any]
    payloadType: Optional[str] = None  # Also accepts payload_type
    payload_type: Optional[str] = None  # Snake_case alternative
    priority: Priority = Priority.NORMAL
    audience: Audience = Audience.PUBLIC
    topic: Topic
    tags: List[str] = Field(default_factory=list)
    hopLimit: int = 20
    receiptPolicy: ReceiptPolicy = ReceiptPolicy.NONE
    expiresAt: Optional[datetime] = None  # Will be auto-calculated if not provided
    ttl_hours: Optional[int] = None  # Alternative to expiresAt (converts to expiresAt)

    def model_post_init(self, __context):
        """Normalize field names and handle TTL conversion"""
        # Handle payload_type -> payloadType
        if self.payload_type and not self.payloadType:
            self.payloadType = self.payload_type
        if not self.payloadType:
            raise ValueError("payloadType or payload_type is required")

        # Handle ttl_hours -> expiresAt
        if self.ttl_hours and not self.expiresAt:
            from datetime import datetime, timedelta, timezone
            self.expiresAt = datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours)


class Bundle(BaseModel):
    """
    DTN Bundle format - core transport unit for all data

    All payloads (offers, needs, files, indexes, queries) move as signed bundles
    with TTL, priority, audience controls, and hop limits.
    """
    bundleId: str  # Content-addressed: b:sha256:...
    createdAt: datetime
    expiresAt: datetime
    priority: Priority
    audience: Audience
    topic: Topic
    tags: List[str]
    payloadType: str  # Schema identifier (vf:Listing, vf:Event, query:Search, etc.)
    payload: dict[str, Any]
    hopLimit: int
    hopCount: int = 0  # Tracks how many times forwarded
    receiptPolicy: ReceiptPolicy
    signature: str  # Ed25519 signature
    authorPublicKey: str  # Ed25519 public key of creator

    model_config = ConfigDict(
        # Allow both camelCase and snake_case in JSON
        populate_by_name=True
    )

    # Add snake_case aliases for compatibility
    @property
    def bundle_id(self) -> str:
        """Alias for bundleId (snake_case compatibility)"""
        return self.bundleId

    @property
    def created_at(self) -> datetime:
        """Alias for createdAt (snake_case compatibility)"""
        return self.createdAt

    @property
    def expires_at(self) -> datetime:
        """Alias for expiresAt (snake_case compatibility)"""
        return self.expiresAt

    @property
    def payload_type(self) -> str:
        """Alias for payloadType (snake_case compatibility)"""
        return self.payloadType

    @property
    def hop_limit(self) -> int:
        """Alias for hopLimit (snake_case compatibility)"""
        return self.hopLimit

    @property
    def hop_count(self) -> int:
        """Alias for hopCount (snake_case compatibility)"""
        return self.hopCount

    @property
    def receipt_policy(self) -> ReceiptPolicy:
        """Alias for receiptPolicy (snake_case compatibility)"""
        return self.receiptPolicy

    @property
    def author_public_key(self) -> str:
        """Alias for authorPublicKey (snake_case compatibility)"""
        return self.authorPublicKey

    @field_validator('bundleId')
    @classmethod
    def validate_bundle_id(cls, v: str) -> str:
        if not v.startswith('b:sha256:'):
            raise ValueError('bundleId must start with b:sha256:')
        return v

    def to_canonical_json(self) -> str:
        """
        Convert bundle to canonical JSON for signing/hashing.
        Excludes bundleId and signature for content-addressing.
        """
        data = self.model_dump(exclude={'bundleId', 'signature'})
        # Convert datetime objects to ISO format
        data['createdAt'] = self.createdAt.isoformat()
        data['expiresAt'] = self.expiresAt.isoformat()
        # Sort keys for deterministic JSON
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    def calculate_bundle_id(self) -> str:
        """Calculate content-addressed bundleId from canonical JSON"""
        canonical = self.to_canonical_json()
        hash_digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return f"b:sha256:{hash_digest}"

    def is_expired(self) -> bool:
        """Check if bundle has expired based on TTL"""
        return datetime.now(timezone.utc) > self.expiresAt

    def is_hop_limit_exceeded(self) -> bool:
        """Check if bundle has exceeded hop limit"""
        return self.hopCount >= self.hopLimit

    def increment_hop_count(self) -> 'Bundle':
        """Increment hop count when forwarding"""
        self.hopCount += 1
        return self

    @staticmethod
    def calculate_default_ttl(
        priority: Priority,
        topic: Topic,
        tags: List[str],
        created_at: datetime
    ) -> datetime:
        """
        Calculate default TTL based on bundle content and priority.

        TTL defaults from spec:
        - emergency: 6-24 hours
        - perishable food offers: 24-72 hours
        - time-sensitive needs: 24-72 hours
        - tool lending: 7-30 days
        - skill offers: 30-90 days
        - plans/processes: until end + 30 days
        - protocols/lessons: 180-365 days
        - indexes: 1-7 days
        """
        if priority == Priority.EMERGENCY:
            # Emergency: 12 hours (middle of 6-24 hour range)
            return created_at + timedelta(hours=12)

        if priority == Priority.PERISHABLE:
            # Perishable: 48 hours (middle of 24-72 hour range)
            return created_at + timedelta(hours=48)

        # Check tags for specific content types
        tag_set = set(t.lower() for t in tags)

        if "food" in tag_set or "perishable" in tag_set:
            return created_at + timedelta(hours=48)

        if "index" in tag_set:
            return created_at + timedelta(days=3)

        # Topic-based TTL
        if topic == Topic.KNOWLEDGE:
            # Knowledge: 270 days (middle of 180-365 day range)
            return created_at + timedelta(days=270)

        if topic == Topic.EDUCATION:
            # Education: similar to knowledge
            return created_at + timedelta(days=270)

        if topic == Topic.MUTUAL_AID:
            # Mutual aid: 48 hours default (time-sensitive)
            return created_at + timedelta(hours=48)

        if topic == Topic.COORDINATION:
            # Coordination: 7 days
            return created_at + timedelta(days=7)

        if topic == Topic.INVENTORY:
            # Inventory: 30 days
            return created_at + timedelta(days=30)

        # Default for NORMAL priority
        if priority == Priority.NORMAL:
            return created_at + timedelta(days=7)

        # LOW priority
        if priority == Priority.LOW:
            return created_at + timedelta(days=3)

        # Fallback
        return created_at + timedelta(days=7)
