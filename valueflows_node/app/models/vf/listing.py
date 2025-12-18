"""
Listing Model - VF-Full v1.0

Represents offers and needs - the primary UX primitive for gift economy.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ListingType(str, Enum):
    """Type of listing"""
    OFFER = "offer"
    NEED = "need"


@dataclass
class Listing:
    """
    A listing represents an offer or need in the gift economy.

    UX primitive: simple to create, easy to browse.
    Backend stores rich data for agent matching.

    Examples:
    - Offer: "5 lbs heirloom tomatoes, available next 2 days"
    - Need: "Beekeeping help, 2 hours, next week"
    """

    id: str
    listing_type: ListingType
    resource_spec_id: str  # References ResourceSpec

    # Who and where
    agent_id: str  # Who is offering/needing (references Agent)
    location_id: Optional[str] = None  # Where (references Location)

    # What and how much
    quantity: float = 1.0
    unit: str = "items"

    # When
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Optional fields
    title: Optional[str] = None  # e.g., "Fresh tomatoes from garden"
    description: Optional[str] = None  # Notes, details
    image_url: Optional[str] = None

    # State
    status: str = "active"  # active, fulfilled, expired, cancelled

    # Links to related objects
    resource_instance_id: Optional[str] = None  # If offering specific instance

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
            "listing_type": self.listing_type.value,
            "resource_spec_id": self.resource_spec_id,
            "agent_id": self.agent_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "available_until": self.available_until.isoformat() if self.available_until else None,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "status": self.status,
            "resource_instance_id": self.resource_instance_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Listing":
        """Create Listing from dictionary"""
        return cls(
            id=data["id"],
            listing_type=ListingType(data["listing_type"]),
            resource_spec_id=data["resource_spec_id"],
            agent_id=data["agent_id"],
            location_id=data.get("location_id"),
            quantity=data.get("quantity", 1.0),
            unit=data.get("unit", "items"),
            available_from=datetime.fromisoformat(data["available_from"]) if data.get("available_from") else None,
            available_until=datetime.fromisoformat(data["available_until"]) if data.get("available_until") else None,
            title=data.get("title"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            status=data.get("status", "active"),
            resource_instance_id=data.get("resource_instance_id"),
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

    def is_active(self) -> bool:
        """Check if listing is currently active"""
        if self.status != "active":
            return False

        now = datetime.now()

        if self.available_from and now < self.available_from:
            return False

        if self.available_until and now > self.available_until:
            return False

        return True
