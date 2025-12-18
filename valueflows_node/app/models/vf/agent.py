"""
Agent Model - VF-Full v1.0

Represents people, groups, or places that participate in economic activities.
Agent ID is typically the public key for cryptographic identity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class AgentType(str, Enum):
    PERSON = "person"
    GROUP = "group"
    PLACE = "place"


@dataclass
class Agent:
    """
    An agent is any entity that participates in economic activities.

    Examples:
    - Person: individual community member
    - Group: tool library, community kitchen, garden collective
    - Place: community space that can hold resources
    """

    id: str  # Usually public key (Ed25519)
    name: str
    agent_type: AgentType

    # Optional fields
    description: Optional[str] = None
    image_url: Optional[str] = None
    primary_location_id: Optional[str] = None

    # Contact/coordination
    contact_info: Optional[str] = None  # Can be encrypted

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
            "agent_type": self.agent_type.value,
            "description": self.description,
            "image_url": self.image_url,
            "primary_location_id": self.primary_location_id,
            "contact_info": self.contact_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        """Create Agent from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            agent_type=AgentType(data["agent_type"]),
            description=data.get("description"),
            image_url=data.get("image_url"),
            primary_location_id=data.get("primary_location_id"),
            contact_info=data.get("contact_info"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            author=data.get("author"),
            signature=data.get("signature"),
        )

    def canonical_json(self) -> str:
        """
        Generate canonical JSON for signature verification.
        Excludes signature field itself.
        """
        import json
        data = self.to_dict()
        data.pop("signature", None)
        return json.dumps(data, sort_keys=True, separators=(',', ':'))
