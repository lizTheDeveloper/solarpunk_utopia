"""
Location Model - VF-Full v1.0

Represents physical places where resources exist or activities happen.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Location:
    """
    A physical place with optional coordinates.

    Examples:
    - Community Garden
    - Tool Library, Shelf 3
    - Community Kitchen
    - Alice's Backyard
    """

    id: str
    name: str

    # Optional fields
    description: Optional[str] = None
    address: Optional[str] = None

    # Coordinates (optional)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Hierarchy (location can be inside another location)
    parent_location_id: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None  # Public key of creator
    signature: Optional[str] = None  # Ed25519 signature

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "parent_location_id": self.parent_location_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Location":
        """Create Location from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            parent_location_id=data.get("parent_location_id"),
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
