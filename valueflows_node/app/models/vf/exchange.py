"""
Exchange Model - VF-Full v1.0

Represents a negotiated arrangement for resource transfer.
Created from accepted matches. Coordinates handoff logistics.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ExchangeStatus(str, Enum):
    """Status of an exchange"""
    PLANNED = "planned"       # Arranged but not yet happened
    IN_PROGRESS = "in_progress"  # Happening now
    COMPLETED = "completed"   # Both parties recorded events
    CANCELLED = "cancelled"   # One or both parties cancelled


@dataclass
class Exchange:
    """
    A negotiated arrangement for resource transfer.

    Coordinates logistics: where, when, how much, constraints.
    Both parties commit to the exchange.
    Completion requires both parties to record events.
    """

    id: str
    # Parties
    provider_id: str  # Agent providing resource
    receiver_id: str  # Agent receiving resource

    # What
    resource_spec_id: str  # References ResourceSpec
    quantity: float
    unit: str

    match_id: Optional[str] = None  # References Match (if created from match)

    # Where and when
    location_id: Optional[str] = None  # Where handoff happens
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    # Status
    status: ExchangeStatus = ExchangeStatus.PLANNED

    # Constraints and notes
    constraints: Optional[str] = None  # e.g., "Bring container"
    notes: Optional[str] = None

    # Completion tracking
    provider_completed: bool = False
    receiver_completed: bool = False
    provider_event_id: Optional[str] = None  # References Event
    receiver_event_id: Optional[str] = None  # References Event

    # Commitment references
    provider_commitment_id: Optional[str] = None
    receiver_commitment_id: Optional[str] = None

    # Community scoping (GAP-03)
    community_id: Optional[str] = None  # Which community this exchange belongs to

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
            "match_id": self.match_id,
            "provider_id": self.provider_id,
            "receiver_id": self.receiver_id,
            "resource_spec_id": self.resource_spec_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "location_id": self.location_id,
            "scheduled_start": self.scheduled_start.isoformat() if self.scheduled_start else None,
            "scheduled_end": self.scheduled_end.isoformat() if self.scheduled_end else None,
            "status": self.status.value,
            "constraints": self.constraints,
            "notes": self.notes,
            "provider_completed": self.provider_completed,
            "receiver_completed": self.receiver_completed,
            "provider_event_id": self.provider_event_id,
            "receiver_event_id": self.receiver_event_id,
            "provider_commitment_id": self.provider_commitment_id,
            "receiver_commitment_id": self.receiver_commitment_id,
            "community_id": self.community_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Exchange":
        """Create Exchange from dictionary"""
        return cls(
            id=data["id"],
            match_id=data.get("match_id"),
            provider_id=data["provider_id"],
            receiver_id=data["receiver_id"],
            resource_spec_id=data["resource_spec_id"],
            quantity=data["quantity"],
            unit=data["unit"],
            location_id=data.get("location_id"),
            scheduled_start=datetime.fromisoformat(data["scheduled_start"]) if data.get("scheduled_start") else None,
            scheduled_end=datetime.fromisoformat(data["scheduled_end"]) if data.get("scheduled_end") else None,
            status=ExchangeStatus(data.get("status", "planned")),
            constraints=data.get("constraints"),
            notes=data.get("notes"),
            provider_completed=data.get("provider_completed", False),
            receiver_completed=data.get("receiver_completed", False),
            provider_event_id=data.get("provider_event_id"),
            receiver_event_id=data.get("receiver_event_id"),
            provider_commitment_id=data.get("provider_commitment_id"),
            receiver_commitment_id=data.get("receiver_commitment_id"),
            community_id=data.get("community_id"),
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

    def is_completed(self) -> bool:
        """Check if both parties have completed the exchange"""
        return self.provider_completed and self.receiver_completed
