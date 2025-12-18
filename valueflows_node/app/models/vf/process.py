"""
Process Model - VF-Full v1.0

Represents a transformation: inputs → outputs.
Examples: cooking, planting, composting, repair
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ProcessStatus(str, Enum):
    """Status of a process"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ProcessInput:
    """An input to a process"""
    resource_spec_id: str
    quantity: float
    unit: str
    note: Optional[str] = None


@dataclass
class ProcessOutput:
    """An output from a process"""
    resource_spec_id: str
    quantity: float
    unit: str
    note: Optional[str] = None


@dataclass
class Process:
    """
    A transformation process with inputs and outputs.

    Examples:
    - Cooking: tomatoes + onions + oil → tomato sauce
    - Planting: seeds + compost + labor → seedlings
    - Composting: scraps + yard waste → compost
    """

    id: str
    name: str
    status: ProcessStatus = ProcessStatus.PLANNED

    # What kind of process (references Protocol if following standard recipe)
    protocol_id: Optional[str] = None

    # Optional fields
    description: Optional[str] = None

    # Where and when
    location_id: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # Inputs and outputs (stored as JSON in DB)
    inputs: List[ProcessInput] = None
    outputs: List[ProcessOutput] = None

    # Participants (stored as JSON in DB)
    participant_ids: List[str] = None  # List of Agent IDs

    # Context
    plan_id: Optional[str] = None  # References Plan (if part of larger plan)

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cryptographic provenance
    author: Optional[str] = None
    signature: Optional[str] = None

    def __post_init__(self):
        """Initialize empty lists if None"""
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.participant_ids is None:
            self.participant_ids = []

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "protocol_id": self.protocol_id,
            "description": self.description,
            "location_id": self.location_id,
            "planned_start": self.planned_start.isoformat() if self.planned_start else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "inputs": [{"resource_spec_id": i.resource_spec_id, "quantity": i.quantity, "unit": i.unit, "note": i.note} for i in self.inputs],
            "outputs": [{"resource_spec_id": o.resource_spec_id, "quantity": o.quantity, "unit": o.unit, "note": o.note} for o in self.outputs],
            "participant_ids": self.participant_ids,
            "plan_id": self.plan_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Process":
        """Create Process from dictionary"""
        inputs = [ProcessInput(**i) for i in data.get("inputs", [])]
        outputs = [ProcessOutput(**o) for o in data.get("outputs", [])]

        return cls(
            id=data["id"],
            name=data["name"],
            status=ProcessStatus(data.get("status", "planned")),
            protocol_id=data.get("protocol_id"),
            description=data.get("description"),
            location_id=data.get("location_id"),
            planned_start=datetime.fromisoformat(data["planned_start"]) if data.get("planned_start") else None,
            planned_end=datetime.fromisoformat(data["planned_end"]) if data.get("planned_end") else None,
            actual_start=datetime.fromisoformat(data["actual_start"]) if data.get("actual_start") else None,
            actual_end=datetime.fromisoformat(data["actual_end"]) if data.get("actual_end") else None,
            inputs=inputs,
            outputs=outputs,
            participant_ids=data.get("participant_ids", []),
            plan_id=data.get("plan_id"),
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
