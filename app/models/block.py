"""
Block List Model - GAP-107

Allows users to block others from matching or messaging them.
Harassment prevention without revealing the block to the blocked user.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BlockEntry:
    """
    Record of one user blocking another.

    The block is one-directional and private:
    - blocker_id can't be matched with blocked_id
    - blocked_id doesn't know they've been blocked (silent)
    - Reason is private to blocker (not shared)
    """

    id: str
    blocker_id: str  # User who initiated the block
    blocked_id: str  # User being blocked
    created_at: datetime
    reason: Optional[str] = None  # Private reason (never shared with blocked user)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "blocker_id": self.blocker_id,
            "blocked_id": self.blocked_id,
            "created_at": self.created_at.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BlockEntry":
        """Create BlockEntry from dictionary"""
        return cls(
            id=data["id"],
            blocker_id=data["blocker_id"],
            blocked_id=data["blocked_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            reason=data.get("reason"),
        )
