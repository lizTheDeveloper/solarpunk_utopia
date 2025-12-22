"""Mourning Protocol Models - GAP-67

Creating space for grief in the community.
"The moment we choose to love we begin to move against domination, against oppression." - bell hooks
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class MourningPeriod(BaseModel):
    """A mourning period for a community.

    When activated, community enters different mode:
    - Metrics pause
    - Non-urgent notifications stop
    - Memorial space created
    - Support flows enabled
    """
    id: str = Field(description="Mourning period ID")
    cell_id: str = Field(description="Which community is mourning")
    trigger: Literal["death", "departure", "collective_trauma", "other"] = Field(
        description="What caused the mourning"
    )
    honoring: Optional[str] = Field(
        default=None,
        description="Name of person being mourned (if applicable)"
    )
    description: Optional[str] = Field(
        default=None,
        description="What happened (optional)"
    )
    started_at: datetime = Field(default_factory=datetime.utcnow)
    duration_days: int = Field(default=7, description="Default 1 week, adjustable")
    ends_at: datetime = Field(
        description="When mourning period ends (can be extended)"
    )
    extended_count: int = Field(default=0, description="How many times extended")
    ended_early: bool = Field(default=False)
    created_by: str = Field(description="Steward who activated mourning")

    # What changes during mourning
    pause_metrics: bool = Field(
        default=True,
        description="Stop counting contributions"
    )
    silence_non_urgent: bool = Field(
        default=True,
        description="Quiet the noise, only urgent notifications"
    )
    create_memorial: bool = Field(
        default=True,
        description="Space for remembrance"
    )
    enable_support_offers: bool = Field(
        default=True,
        description="Easy way to offer help"
    )

    def __init__(self, **data):
        if 'ends_at' not in data:
            data['ends_at'] = data.get('started_at', datetime.now(UTC)) + timedelta(days=data.get('duration_days', 7))
        super().__init__(**data)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "mourning-001",
                "cell_id": "cell-main",
                "trigger": "death",
                "honoring": "Alex Chen",
                "description": "Beloved member passed away",
                "started_at": "2025-12-20T00:00:00Z",
                "duration_days": 7,
                "ends_at": "2025-12-27T00:00:00Z",
                "extended_count": 0,
                "ended_early": False,
                "created_by": "steward-pk",
                "pause_metrics": True,
                "silence_non_urgent": True,
                "create_memorial": True,
                "enable_support_offers": True
            }
        }


class Memorial(BaseModel):
    """Memorial space for remembering someone or something.

    Persists after mourning ends.
    """
    id: str = Field(description="Memorial ID")
    mourning_id: str = Field(description="Associated mourning period")
    person_name: Optional[str] = None
    event_name: Optional[str] = None  # For collective trauma
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "memorial-001",
                "mourning_id": "mourning-001",
                "person_name": "Alex Chen",
                "event_name": None,
                "created_at": "2025-12-20T00:00:00Z"
            }
        }


class MemorialEntry(BaseModel):
    """An entry in a memorial - memory, reflection, photo."""
    id: str
    memorial_id: str
    author_id: str
    content: str = Field(description="Memory, reflection, what they meant to you")
    media_url: Optional[str] = Field(
        default=None,
        description="Photo (local file, no cloud upload)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "entry-001",
                "memorial_id": "memorial-001",
                "author_id": "maria-pk",
                "content": "Alex taught me to grow tomatoes. I'll miss their laugh.",
                "media_url": "data/photos/alex-garden.jpg",
                "created_at": "2025-12-20T01:00:00Z"
            }
        }


class GriefSupport(BaseModel):
    """Support offer during mourning."""
    id: str
    mourning_id: str
    offered_by: str
    support_type: Literal["meals", "childcare", "errands", "presence", "other"]
    details: str = Field(description="What specifically is offered")
    claimed_by: Optional[str] = Field(
        default=None,
        description="If coordinated, who claimed this support"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "support-001",
                "mourning_id": "mourning-001",
                "offered_by": "bob-pk",
                "support_type": "meals",
                "details": "Can bring dinner for the family Tuesday/Thursday",
                "claimed_by": None,
                "created_at": "2025-12-20T02:00:00Z"
            }
        }


class MourningBanner(BaseModel):
    """Banner shown to all cell members during mourning."""
    cell_id: str
    mourning_id: str
    message: str
    quote: str = Field(
        default="Grief is not something to get over, but something to move through. - bell hooks"
    )
    show_until: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "cell_id": "cell-main",
                "mourning_id": "mourning-001",
                "message": "We are honoring the memory of Alex Chen.",
                "quote": "Grief is not something to get over, but something to move through. - bell hooks",
                "show_until": "2025-12-27T00:00:00Z"
            }
        }


# Privacy Guarantees
"""
What we track:
- That mourning is active (so we can pause metrics)
- Memorial entries (public within cell)
- Support offers (for coordination)

What we DON'T track:
- Who visited the memorial
- How long anyone grieved
- "Participation" in mourning
- Who didn't offer support

Grief is private. We hold space without surveillance.
"""
