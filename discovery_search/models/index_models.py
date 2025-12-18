"""
Index Models for Discovery System

Three types of indexes advertise local data:
1. InventoryIndex: Offers, needs, resource specs
2. ServiceIndex: Skills, labor offers, availability
3. KnowledgeIndex: Protocols, lessons, files

Each index is published as a DTN bundle periodically.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class IndexType(str, Enum):
    """Types of index bundles"""
    INVENTORY = "inventory"
    SERVICE = "service"
    KNOWLEDGE = "knowledge"


class InventoryIndexEntry(BaseModel):
    """
    Single entry in an inventory index.

    Represents a listing (offer or need) available at this node.
    """
    listing_id: str
    listing_type: str  # "offer" or "need"
    resource_spec_id: str
    resource_name: str  # e.g., "Tomatoes"
    category: str  # e.g., "food"
    subcategory: Optional[str] = None  # e.g., "vegetables"

    # Quantity and units
    quantity: float
    unit: str

    # Location
    location_id: Optional[str] = None
    location_name: Optional[str] = None

    # Time constraints
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None

    # Preview data for UI
    title: Optional[str] = None
    description: Optional[str] = None
    agent_id: str
    agent_name: Optional[str] = None

    # Bundle reference for full data
    bundle_id: Optional[str] = None  # Reference to full listing bundle


class InventoryIndex(BaseModel):
    """
    Inventory index advertises local offers and needs.

    Published periodically (every 5-60 min) to advertise what's available.
    Enables queries like "who has tomatoes?" to find matches quickly.
    """
    index_type: IndexType = IndexType.INVENTORY
    node_id: str  # Node's public key fingerprint
    node_public_key: str  # Full public key for verification

    # Index entries
    entries: List[InventoryIndexEntry] = Field(default_factory=list)

    # Metadata
    generated_at: datetime
    expires_at: datetime  # When this index becomes stale
    version: int = 1  # For future schema changes

    # Statistics for display
    total_offers: int = 0
    total_needs: int = 0
    categories: List[str] = Field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to bundle payload format"""
        return {
            "index_type": self.index_type.value,
            "node_id": self.node_id,
            "node_public_key": self.node_public_key,
            "entries": [entry.model_dump(mode='json') for entry in self.entries],
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "version": self.version,
            "total_offers": self.total_offers,
            "total_needs": self.total_needs,
            "categories": self.categories,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "InventoryIndex":
        """Create from bundle payload"""
        return cls(
            index_type=IndexType(payload["index_type"]),
            node_id=payload["node_id"],
            node_public_key=payload["node_public_key"],
            entries=[InventoryIndexEntry(**entry) for entry in payload["entries"]],
            generated_at=datetime.fromisoformat(payload["generated_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            version=payload.get("version", 1),
            total_offers=payload.get("total_offers", 0),
            total_needs=payload.get("total_needs", 0),
            categories=payload.get("categories", []),
        )


class ServiceIndexEntry(BaseModel):
    """
    Single entry in a service index.

    Represents a skill or labor offer available at this node.
    """
    listing_id: str
    service_type: str  # e.g., "beekeeping", "carpentry", "teaching"
    skill_name: str
    category: str  # e.g., "skills"

    # Agent offering service
    agent_id: str
    agent_name: Optional[str] = None

    # Availability
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    hours_available: Optional[float] = None

    # Location
    location_id: Optional[str] = None
    location_name: Optional[str] = None

    # Preview data
    title: Optional[str] = None
    description: Optional[str] = None

    # Bundle reference
    bundle_id: Optional[str] = None


class ServiceIndex(BaseModel):
    """
    Service index advertises skills and labor offers.

    Enables queries like "who can teach beekeeping?"
    """
    index_type: IndexType = IndexType.SERVICE
    node_id: str
    node_public_key: str

    # Index entries
    entries: List[ServiceIndexEntry] = Field(default_factory=list)

    # Metadata
    generated_at: datetime
    expires_at: datetime
    version: int = 1

    # Statistics
    total_services: int = 0
    service_types: List[str] = Field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to bundle payload format"""
        return {
            "index_type": self.index_type.value,
            "node_id": self.node_id,
            "node_public_key": self.node_public_key,
            "entries": [entry.model_dump(mode='json') for entry in self.entries],
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "version": self.version,
            "total_services": self.total_services,
            "service_types": self.service_types,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ServiceIndex":
        """Create from bundle payload"""
        return cls(
            index_type=IndexType(payload["index_type"]),
            node_id=payload["node_id"],
            node_public_key=payload["node_public_key"],
            entries=[ServiceIndexEntry(**entry) for entry in payload["entries"]],
            generated_at=datetime.fromisoformat(payload["generated_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            version=payload.get("version", 1),
            total_services=payload.get("total_services", 0),
            service_types=payload.get("service_types", []),
        )


class KnowledgeIndexEntry(BaseModel):
    """
    Single entry in a knowledge index.

    Represents a protocol, lesson, or file available at this node.
    """
    content_id: str
    content_type: str  # "protocol", "lesson", "file"
    title: str
    category: str  # e.g., "agriculture", "construction"

    # Content metadata
    content_hash: Optional[str] = None  # SHA256 hash if file
    file_size: Optional[int] = None  # Bytes
    mime_type: Optional[str] = None

    # Authorship
    author_id: Optional[str] = None
    author_name: Optional[str] = None

    # Preview
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Bundle reference
    bundle_id: Optional[str] = None

    # Created date
    created_at: Optional[datetime] = None


class KnowledgeIndex(BaseModel):
    """
    Knowledge index advertises protocols, lessons, and cached files.

    Enables queries like "what protocols exist for composting?"
    """
    index_type: IndexType = IndexType.KNOWLEDGE
    node_id: str
    node_public_key: str

    # Index entries
    entries: List[KnowledgeIndexEntry] = Field(default_factory=list)

    # Metadata
    generated_at: datetime
    expires_at: datetime
    version: int = 1

    # Statistics
    total_protocols: int = 0
    total_lessons: int = 0
    total_files: int = 0
    categories: List[str] = Field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to bundle payload format"""
        return {
            "index_type": self.index_type.value,
            "node_id": self.node_id,
            "node_public_key": self.node_public_key,
            "entries": [entry.model_dump(mode='json') for entry in self.entries],
            "generated_at": self.generated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "version": self.version,
            "total_protocols": self.total_protocols,
            "total_lessons": self.total_lessons,
            "total_files": self.total_files,
            "categories": self.categories,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "KnowledgeIndex":
        """Create from bundle payload"""
        return cls(
            index_type=IndexType(payload["index_type"]),
            node_id=payload["node_id"],
            node_public_key=payload["node_public_key"],
            entries=[KnowledgeIndexEntry(**entry) for entry in payload["entries"]],
            generated_at=datetime.fromisoformat(payload["generated_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]),
            version=payload.get("version", 1),
            total_protocols=payload.get("total_protocols", 0),
            total_lessons=payload.get("total_lessons", 0),
            total_files=payload.get("total_files", 0),
            categories=payload.get("categories", []),
        )
