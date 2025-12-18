"""
ResourceInstance Model - VF-Full v1.0

Represents specific, trackable instances of resources.
Examples: "Batch-20251217-tomatoes", "Shovel-001"
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ResourceState(str, Enum):
    """State of a resource instance"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    IN_TRANSIT = "in_transit"
    CONSUMED = "consumed"
    DAMAGED = "damaged"
    IN_REPAIR = "in_repair"
    EXPIRED = "expired"


@dataclass
class ResourceInstance:
    """
    A specific, trackable instance or batch of a resource.

    Examples:
    - Batch of tomatoes with expiry date
    - A specific shovel with serial number
    - A jar of tomato sauce produced in a process
    """

    id: str
    resource_spec_id: str  # References ResourceSpec

    # Quantity and unit
    quantity: float
    unit: str

    # State tracking
    state: ResourceState
    current_location_id: Optional[str] = None  # References Location

    # Optional fields
    label: Optional[str] = None  # e.g., "Shovel-001", "Batch-20251217"
    description: Optional[str] = None
    image_url: Optional[str] = None

    # Perishable tracking
    expires_at: Optional[datetime] = None

    # Ownership/custody
    current_custodian_id: Optional[str] = None  # References Agent

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "resource_spec_id": self.resource_spec_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "state": self.state.value,
            "current_location_id": self.current_location_id,
            "label": self.label,
            "description": self.description,
            "image_url": self.image_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "current_custodian_id": self.current_custodian_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceInstance":
        """Create ResourceInstance from dictionary"""
        return cls(
            id=data["id"],
            resource_spec_id=data["resource_spec_id"],
            quantity=data["quantity"],
            unit=data["unit"],
            state=ResourceState(data["state"]),
            current_location_id=data.get("current_location_id"),
            label=data.get("label"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            current_custodian_id=data.get("current_custodian_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            author=data.get("author"),
            signature=data.get("signature"),
        )

    def canonical_json(self) -> str:
        """Generate canonical JSON for signature verification"""
        import json
        data = self.to_dict()
        data.pop("signature", None)
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    def is_expired(self) -> bool:
        """Check if resource has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def hours_until_expiry(self) -> Optional[float]:
        """Get hours until expiry, or None if not perishable"""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now()
        return delta.total_seconds() / 3600
