"""
Abundance Osmosis Models (GAP-63)

Kropotkin observed: In nature, abundance spreads. Seeds flow to neighbors.
Knowledge transfers. Without explicit transactions.

These models support:
- Community shelves (take what you need)
- Overflow detection (old offers → community sharing)
- Circulating resources (tracked by location, not ownership)
- Knowledge ripples (teach what you learned)
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CommunityShelf(BaseModel):
    """
    Physical or virtual 'take what you need' space.

    Items placed here can be taken anonymously (see GAP-61).
    No transaction tracking. The abundance just flows.
    """
    id: str
    name: str
    location: str  # "Downtown library foyer" or "virtual"
    created_by: str  # Steward who set it up
    cell_id: str
    is_virtual: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ShelfItem(BaseModel):
    """
    Item on a community shelf.

    NOTE: No tracking of who took what. When taken, item is deleted.
    """
    id: str
    shelf_id: str
    description: str
    category: str  # "food", "tools", "books", etc.
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[str] = None  # None if anonymous (GAP-61)
    still_available: bool = True

    # NOT included: taken_by, quantity_taken
    # The gift flows anonymously


class CirculatingResource(BaseModel):
    """
    Shared resources that belong to the community.

    We track WHERE they are, not WHO OWNS them.
    Like a library book - it circulates, no one owns it.
    """
    id: str
    description: str  # "Dewalt drill"
    category: str  # "tools"
    current_location: str  # "Alice's garage" (just location, not ownership)
    current_holder_notes: Optional[str] = None  # "Needs new battery"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    cell_id: str

    # NOT included: owner, checkout history
    # It belongs to everyone


class OverflowPrompt(BaseModel):
    """
    Gentle suggestion when offers have been available for a while.

    "You've had tomatoes available for 3 days. Let them flow to the community shelf?"
    """
    id: str
    user_id: str
    listing_id: str  # The offer that's been sitting
    days_available: int
    prompted_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "accepted", "declined", "snoozed"] = "pending"
    snoozed_until: Optional[datetime] = None


class KnowledgeRipple(BaseModel):
    """
    Suggestion to teach what you learned.

    "You learned bicycle repair 2 weeks ago. Feeling confident? Maybe teach someone else?"
    """
    id: str
    user_id: str
    exchange_id: str  # The learning exchange
    skill_learned: str
    learned_at: datetime
    prompted_at: Optional[datetime] = None
    status: Literal["pending", "prompted", "accepted", "declined", "dismissed"] = "pending"

    # User can dismiss permanently: "stop suggesting"
    permanently_dismissed: bool = False


def to_dict(self) -> dict:
    """Convert model to dictionary"""
    data = self.model_dump()
    # Convert datetime objects to ISO format strings
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


# Add to_dict method to all models
CommunityShelf.to_dict = to_dict
ShelfItem.to_dict = to_dict
CirculatingResource.to_dict = to_dict
OverflowPrompt.to_dict = to_dict
KnowledgeRipple.to_dict = to_dict
