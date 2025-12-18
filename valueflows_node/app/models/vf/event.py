"""
Event Model - VF-Full v1.0

Represents economic events - things that actually happened.
Examples: handoff, work, delivery, harvest, class, repair
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class EventAction(str, Enum):
    """Type of economic event"""
    # Transfer events
    TRANSFER = "transfer"           # Generic transfer
    TRANSFER_OUT = "transfer-out"   # Giving to someone
    RECEIVE = "receive"             # Receiving from someone

    # Production events
    PRODUCE = "produce"   # Creating resource
    CONSUME = "consume"   # Using up resource

    # Work events
    WORK = "work"         # Labor contribution
    USE = "use"           # Using a resource (not consuming)

    # State change events
    PICKUP = "pickup"     # Picking up from location
    DROPOFF = "dropoff"   # Dropping off at location
    ACCEPT = "accept"     # Accepting delivery/gift
    MODIFY = "modify"     # Changing resource

    # Other
    CITE = "cite"         # Reference to knowledge/protocol
    DELIVER_SERVICE = "deliver-service"  # Service provided


@dataclass
class Event:
    """
    An economic event that actually happened.

    Events are the ground truth of the gift economy.
    Both provider and receiver should record events for exchanges.
    Processes emit events for inputs (consume) and outputs (produce).
    """

    id: str
    action: EventAction
    agent_id: str  # Who performed the action
    occurred_at: datetime

    # What happened
    resource_spec_id: Optional[str] = None  # References ResourceSpec
    resource_instance_id: Optional[str] = None  # References ResourceInstance
    quantity: Optional[float] = None
    unit: Optional[str] = None

    # Who (other parties)
    to_agent_id: Optional[str] = None  # Recipient (for transfers)
    from_agent_id: Optional[str] = None  # Source (for receives)

    # Where
    location_id: Optional[str] = None

    # Context
    process_id: Optional[str] = None  # References Process (if part of production)
    exchange_id: Optional[str] = None  # References Exchange (if part of exchange)
    commitment_id: Optional[str] = None  # References Commitment (if fulfilling)

    # Optional fields
    note: Optional[str] = None
    image_url: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None  # Must match agent_id
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "action": self.action.value,
            "resource_spec_id": self.resource_spec_id,
            "resource_instance_id": self.resource_instance_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "agent_id": self.agent_id,
            "to_agent_id": self.to_agent_id,
            "from_agent_id": self.from_agent_id,
            "location_id": self.location_id,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "process_id": self.process_id,
            "exchange_id": self.exchange_id,
            "commitment_id": self.commitment_id,
            "note": self.note,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create Event from dictionary"""
        return cls(
            id=data["id"],
            action=EventAction(data["action"]),
            resource_spec_id=data.get("resource_spec_id"),
            resource_instance_id=data.get("resource_instance_id"),
            quantity=data.get("quantity"),
            unit=data.get("unit"),
            agent_id=data["agent_id"],
            to_agent_id=data.get("to_agent_id"),
            from_agent_id=data.get("from_agent_id"),
            location_id=data.get("location_id"),
            occurred_at=datetime.fromisoformat(data["occurred_at"]) if data.get("occurred_at") else datetime.now(),
            process_id=data.get("process_id"),
            exchange_id=data.get("exchange_id"),
            commitment_id=data.get("commitment_id"),
            note=data.get("note"),
            image_url=data.get("image_url"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            author=data.get("author"),
            signature=data.get("signature"),
        )

    def canonical_json(self) -> str:
        """Generate canonical JSON for signature verification"""
        import json
        data = self.to_dict()
        data.pop("signature", None)
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
