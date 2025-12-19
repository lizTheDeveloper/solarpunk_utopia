"""
Match Model - VF-Full v1.0

Represents a suggested or accepted pairing of an offer and a need.
Created by Mutual Aid Matchmaker agent or manually.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class MatchStatus(str, Enum):
    """Status of a match"""
    SUGGESTED = "suggested"  # Agent suggested, awaiting review
    ACCEPTED = "accepted"    # Both parties accepted
    REJECTED = "rejected"    # One or both parties rejected
    EXPIRED = "expired"      # No response within timeframe


@dataclass
class Match:
    """
    A pairing of an offer and a need.

    Flow:
    1. Agent suggests match (or users create manually)
    2. Both parties review and accept/reject
    3. If accepted, can create Exchange
    """

    id: str
    offer_id: str  # References Listing (type=offer)
    need_id: str   # References Listing (type=need)

    # Parties
    provider_id: str  # Agent offering (from offer listing)
    receiver_id: str  # Agent needing (from need listing)

    # Status
    status: MatchStatus = MatchStatus.SUGGESTED

    # Approval tracking
    provider_approved: bool = False
    receiver_approved: bool = False
    provider_approved_at: Optional[datetime] = None
    receiver_approved_at: Optional[datetime] = None

    # Optional fields
    match_score: Optional[float] = None  # Agent confidence (0.0-1.0)
    match_reason: Optional[str] = None   # Why this is a good match
    proposed_quantity: Optional[float] = None
    proposed_unit: Optional[str] = None

    # Community scoping (GAP-03)
    community_id: Optional[str] = None  # Which community this match belongs to

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None  # Agent or user who created match
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "need_id": self.need_id,
            "provider_id": self.provider_id,
            "receiver_id": self.receiver_id,
            "status": self.status.value,
            "provider_approved": self.provider_approved,
            "receiver_approved": self.receiver_approved,
            "provider_approved_at": self.provider_approved_at.isoformat() if self.provider_approved_at else None,
            "receiver_approved_at": self.receiver_approved_at.isoformat() if self.receiver_approved_at else None,
            "match_score": self.match_score,
            "match_reason": self.match_reason,
            "proposed_quantity": self.proposed_quantity,
            "proposed_unit": self.proposed_unit,
            "community_id": self.community_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Match":
        """Create Match from dictionary"""
        return cls(
            id=data["id"],
            offer_id=data["offer_id"],
            need_id=data["need_id"],
            provider_id=data["provider_id"],
            receiver_id=data["receiver_id"],
            status=MatchStatus(data.get("status", "suggested")),
            provider_approved=data.get("provider_approved", False),
            receiver_approved=data.get("receiver_approved", False),
            provider_approved_at=datetime.fromisoformat(data["provider_approved_at"]) if data.get("provider_approved_at") else None,
            receiver_approved_at=datetime.fromisoformat(data["receiver_approved_at"]) if data.get("receiver_approved_at") else None,
            match_score=data.get("match_score"),
            match_reason=data.get("match_reason"),
            proposed_quantity=data.get("proposed_quantity"),
            proposed_unit=data.get("proposed_unit"),
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

    def is_fully_approved(self) -> bool:
        """Check if both parties have approved the match"""
        return self.provider_approved and self.receiver_approved
