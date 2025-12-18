"""
Commitment Model - VF-Full v1.0

Represents promises to do work, deliver resources, or teach.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class CommitmentStatus(str, Enum):
    """Status of a commitment"""
    PROPOSED = "proposed"      # Suggested by agent or user
    ACCEPTED = "accepted"      # Committed to do
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"    # Completed
    CANCELLED = "cancelled"


@dataclass
class Commitment:
    """
    A promise to perform an action or deliver a resource.

    Examples:
    - Alice commits to deliver 3 lbs tomatoes
    - Bob commits to help with beekeeping for 2 hours
    - Carol commits to teach composting workshop
    """

    id: str
    agent_id: str  # Who is committing

    # What action
    action: str  # e.g., "deliver", "work", "teach"

    # What resource (if applicable)
    resource_spec_id: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None

    # When
    due_date: Optional[datetime] = None

    # Status
    status: CommitmentStatus = CommitmentStatus.PROPOSED

    # Context
    exchange_id: Optional[str] = None  # References Exchange
    process_id: Optional[str] = None   # References Process
    plan_id: Optional[str] = None      # References Plan

    # Fulfillment
    fulfilled_by_event_id: Optional[str] = None  # References Event

    # Optional fields
    note: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None  # Should match agent_id
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "action": self.action,
            "resource_spec_id": self.resource_spec_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "exchange_id": self.exchange_id,
            "process_id": self.process_id,
            "plan_id": self.plan_id,
            "fulfilled_by_event_id": self.fulfilled_by_event_id,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Commitment":
        """Create Commitment from dictionary"""
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            action=data["action"],
            resource_spec_id=data.get("resource_spec_id"),
            quantity=data.get("quantity"),
            unit=data.get("unit"),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            status=CommitmentStatus(data.get("status", "proposed")),
            exchange_id=data.get("exchange_id"),
            process_id=data.get("process_id"),
            plan_id=data.get("plan_id"),
            fulfilled_by_event_id=data.get("fulfilled_by_event_id"),
            note=data.get("note"),
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
