"""
Plan Model - VF-Full v1.0

Represents a container of processes and commitments with dependencies.
Examples: weekly work schedule, seasonal planting plan
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class PlanStatus(str, Enum):
    """Status of a plan"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class PlanDependency:
    """A dependency between processes in a plan"""
    process_id: str
    depends_on_process_id: str
    dependency_type: str = "finish-to-start"  # or "start-to-start", etc.


@dataclass
class Plan:
    """
    A container for organizing processes and commitments.

    Examples:
    - Spring 2025 Planting Plan
    - Weekly Work Party Schedule
    - Harvest and Preservation Plan
    """

    id: str
    name: str
    status: PlanStatus = PlanStatus.DRAFT

    # Optional fields
    description: Optional[str] = None
    goal: Optional[str] = None  # What we're trying to achieve

    # Time frame
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Contained processes and commitments (stored as JSON in DB)
    process_ids: List[str] = None
    commitment_ids: List[str] = None

    # Dependencies between processes
    dependencies: List[PlanDependency] = None

    # Optional location context
    location_id: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.process_ids is None:
            self.process_ids = []
        if self.commitment_ids is None:
            self.commitment_ids = []
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "goal": self.goal,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "process_ids": self.process_ids,
            "commitment_ids": self.commitment_ids,
            "dependencies": [{"process_id": d.process_id, "depends_on_process_id": d.depends_on_process_id, "dependency_type": d.dependency_type} for d in self.dependencies],
            "location_id": self.location_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        """Create Plan from dictionary"""
        dependencies = [PlanDependency(**d) for d in data.get("dependencies", [])]

        return cls(
            id=data["id"],
            name=data["name"],
            status=PlanStatus(data.get("status", "draft")),
            description=data.get("description"),
            goal=data.get("goal"),
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            process_ids=data.get("process_ids", []),
            commitment_ids=data.get("commitment_ids", []),
            dependencies=dependencies,
            location_id=data.get("location_id"),
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
