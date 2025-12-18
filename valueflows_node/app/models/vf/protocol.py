"""
Protocol Model - VF-Full v1.0

Represents a repeatable method or recipe.
Examples: composting method, tomato sauce recipe, hive inspection protocol
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Protocol:
    """
    A reusable recipe or method for a process.

    Can be referenced by Process objects.
    Can reference Lessons for learning.
    Can reference files via content hash.

    Examples:
    - Hot Composting Method
    - Community Tomato Sauce Recipe
    - Hive Inspection Protocol
    """

    id: str
    name: str
    category: str  # e.g., "Waste Management", "Food Preservation", "Beekeeping"

    # Optional fields
    description: Optional[str] = None
    instructions: Optional[str] = None  # Step-by-step

    # Expected inputs and outputs (templates)
    expected_inputs: Optional[str] = None  # JSON or text
    expected_outputs: Optional[str] = None  # JSON or text

    # Time and difficulty
    estimated_duration: Optional[str] = None  # e.g., "2-3 hours"
    difficulty_level: Optional[str] = None    # e.g., "beginner", "intermediate", "advanced"

    # References to learning materials
    lesson_ids: List[str] = None  # References to Lesson objects
    file_hashes: List[str] = None  # Content hashes of PDF/video files

    # Tags for discovery
    tags: List[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.lesson_ids is None:
            self.lesson_ids = []
        if self.file_hashes is None:
            self.file_hashes = []
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "instructions": self.instructions,
            "expected_inputs": self.expected_inputs,
            "expected_outputs": self.expected_outputs,
            "estimated_duration": self.estimated_duration,
            "difficulty_level": self.difficulty_level,
            "lesson_ids": self.lesson_ids,
            "file_hashes": self.file_hashes,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Protocol":
        """Create Protocol from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data.get("description"),
            instructions=data.get("instructions"),
            expected_inputs=data.get("expected_inputs"),
            expected_outputs=data.get("expected_outputs"),
            estimated_duration=data.get("estimated_duration"),
            difficulty_level=data.get("difficulty_level"),
            lesson_ids=data.get("lesson_ids", []),
            file_hashes=data.get("file_hashes", []),
            tags=data.get("tags", []),
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
