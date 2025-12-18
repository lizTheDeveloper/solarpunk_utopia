"""
ResourceSpec Model - VF-Full v1.0

Represents categories or types of resources.
Examples: "Tomatoes", "Shovel", "Beekeeping Tutorial"
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ResourceCategory(str, Enum):
    """Common resource categories for gift economy"""
    FOOD = "food"
    TOOLS = "tools"
    SEEDS = "seeds"
    SKILLS = "skills"
    LABOR = "labor"
    KNOWLEDGE = "knowledge"
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    MATERIALS = "materials"
    OTHER = "other"


@dataclass
class ResourceSpec:
    """
    A specification/category/type of resource.

    Examples:
    - Food > Vegetables > Tomatoes
    - Tools > Garden > Shovel
    - Skills > Agriculture > Beekeeping
    """

    id: str
    name: str
    category: ResourceCategory

    # Optional fields
    description: Optional[str] = None
    subcategory: Optional[str] = None  # e.g., "Vegetables" for Food
    image_url: Optional[str] = None

    # Unit of measure
    default_unit: Optional[str] = None  # e.g., "lbs", "hours", "items"

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
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "subcategory": self.subcategory,
            "image_url": self.image_url,
            "default_unit": self.default_unit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceSpec":
        """Create ResourceSpec from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            category=ResourceCategory(data["category"]),
            description=data.get("description"),
            subcategory=data.get("subcategory"),
            image_url=data.get("image_url"),
            default_unit=data.get("default_unit"),
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
