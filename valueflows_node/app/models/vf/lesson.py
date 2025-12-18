"""
Lesson Model - VF-Full v1.0

Represents microlearning tied to tasks and protocols.
Just-in-time education for gift economy participants.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Lesson:
    """
    A learning module tied to a task, skill, or protocol.

    Examples:
    - "Beekeeping Safety Basics" (5 min video)
    - "Hive Inspection Checklist" (1-page PDF)
    - "Composting Temperature Monitoring" (article)
    """

    id: str
    title: str
    lesson_type: str  # e.g., "video", "article", "checklist", "interactive"

    # Optional fields
    description: Optional[str] = None
    content: Optional[str] = None  # Inline content (text/markdown)

    # File references (distributed via file chunking system)
    file_hash: Optional[str] = None  # Content hash for PDF/video/etc
    file_url: Optional[str] = None   # URL if externally hosted

    # Learning metadata
    estimated_duration: Optional[str] = None  # e.g., "5 minutes"
    difficulty_level: Optional[str] = None    # e.g., "beginner"

    # Context and discovery
    skill_tags: List[str] = None      # e.g., ["beekeeping", "agriculture"]
    protocol_ids: List[str] = None    # References Protocol objects
    resource_spec_ids: List[str] = None  # Related to these resources

    # Prerequisites
    prerequisite_lesson_ids: List[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.skill_tags is None:
            self.skill_tags = []
        if self.protocol_ids is None:
            self.protocol_ids = []
        if self.resource_spec_ids is None:
            self.resource_spec_ids = []
        if self.prerequisite_lesson_ids is None:
            self.prerequisite_lesson_ids = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "lesson_type": self.lesson_type,
            "description": self.description,
            "content": self.content,
            "file_hash": self.file_hash,
            "file_url": self.file_url,
            "estimated_duration": self.estimated_duration,
            "difficulty_level": self.difficulty_level,
            "skill_tags": self.skill_tags,
            "protocol_ids": self.protocol_ids,
            "resource_spec_ids": self.resource_spec_ids,
            "prerequisite_lesson_ids": self.prerequisite_lesson_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        """Create Lesson from dictionary"""
        return cls(
            id=data["id"],
            title=data["title"],
            lesson_type=data["lesson_type"],
            description=data.get("description"),
            content=data.get("content"),
            file_hash=data.get("file_hash"),
            file_url=data.get("file_url"),
            estimated_duration=data.get("estimated_duration"),
            difficulty_level=data.get("difficulty_level"),
            skill_tags=data.get("skill_tags", []),
            protocol_ids=data.get("protocol_ids", []),
            resource_spec_ids=data.get("resource_spec_ids", []),
            prerequisite_lesson_ids=data.get("prerequisite_lesson_ids", []),
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
