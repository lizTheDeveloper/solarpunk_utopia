"""Fork Rights (Eject Button) - GAP-65

Data portability and community forking for freedom to exit.
Based on Bakunin: "Freedom without socialism is privilege, injustice;
socialism without freedom is slavery and brutality."
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class DataExportRequest(BaseModel):
    """Request to export personal data."""
    user_id: str = Field(description="User requesting export")
    export_type: Literal["data_only", "with_connections", "fork"] = Field(
        description="Type of export: just data, data + connections, or full fork"
    )
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["pending", "processing", "complete", "failed"] = Field(default="pending")
    export_url: Optional[str] = Field(
        default=None,
        description="Local file path or DTN bundle ID for export (no cloud storage)"
    )
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "maria-pk",
                "export_type": "with_connections",
                "requested_at": "2025-12-20T00:00:00Z",
                "status": "pending"
            }
        }


class DataExport(BaseModel):
    """Complete export of user's data.

    This is LOCAL-FIRST - exports to SQLite file on device.
    No cloud storage, no external dependencies.
    """
    user_id: str
    exported_at: datetime = Field(default_factory=datetime.utcnow)

    # User's own data (always included)
    my_profile: dict  # UserProfile
    my_offers: List[dict]  # List[Offer]
    my_needs: List[dict]  # List[Need]
    my_exchanges: List[dict]  # List[Exchange]
    my_vouches_given: List[dict]  # List[Vouch] - who you vouched for
    my_vouches_received: List[dict]  # List[Vouch] - who vouched for you

    # Connections (with consent if export_type == "with_connections")
    my_connections: List[dict] = Field(default_factory=list)

    # NOT included (community data):
    # - Other people's offers/needs
    # - Community governance decisions
    # - Cell membership lists (except your own cells)

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "maria-pk",
                "exported_at": "2025-12-20T00:00:00Z",
                "my_profile": {"name": "Maria", "bio": "..."},
                "my_offers": [],
                "my_needs": [],
                "my_exchanges": [],
                "my_vouches_given": [],
                "my_vouches_received": [],
                "my_connections": []
            }
        }


class ConnectionExportConsent(BaseModel):
    """Request consent to export a connection.

    You can't export someone else's contact info without asking.
    """
    id: str = Field(description="Consent request ID")
    requester_id: str = Field(description="Person leaving and requesting export")
    connection_id: str = Field(description="Person being asked for consent")
    asked_at: datetime = Field(default_factory=datetime.utcnow)
    response: Optional[Literal["allow", "deny"]] = None
    responded_at: Optional[datetime] = None
    expires_at: datetime = Field(
        description="If no response after 7 days, assume deny"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "consent-001",
                "requester_id": "maria-pk",
                "connection_id": "bob-pk",
                "asked_at": "2025-12-20T00:00:00Z",
                "response": "allow",
                "responded_at": "2025-12-20T01:00:00Z"
            }
        }


class CommunityFork(BaseModel):
    """Fork a community - create new cell with subset of members.

    If you disagree with how a community is governed, you can fork.
    Original cell continues unchanged.
    """
    id: str = Field(description="Fork ID")
    original_cell_id: str = Field(description="Cell being forked from")
    new_cell_name: str = Field(description="Name for new cell")
    new_cell_id: str = Field(description="ID of newly created cell")
    forked_by: str = Field(description="User who initiated fork")
    fork_reason: Optional[str] = Field(
        default=None,
        description="Optional public statement about why forking"
    )
    members_invited: List[str] = Field(
        default_factory=list,
        description="User IDs invited to join fork"
    )
    forked_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "fork-001",
                "original_cell_id": "cell-main",
                "new_cell_name": "Autonomous Collective",
                "new_cell_id": "cell-fork-001",
                "forked_by": "carlos-pk",
                "fork_reason": "Disagreement on governance model",
                "members_invited": ["alice-pk", "bob-pk"],
                "forked_at": "2025-12-20T00:00:00Z"
            }
        }


class ForkInvitation(BaseModel):
    """Invitation to join a forked community."""
    id: str = Field(description="Invitation ID")
    fork_id: str = Field(description="Which fork this is for")
    inviter_id: str = Field(description="Person who created fork")
    invitee_id: str = Field(description="Person being invited")
    status: Literal["pending", "accepted", "declined"] = Field(default="pending")
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None

    # Auto-delete declined invitations after 30 days (data minimization)
    expires_at: datetime = Field(
        description="Declined invitations deleted after this time"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "invite-001",
                "fork_id": "fork-001",
                "inviter_id": "carlos-pk",
                "invitee_id": "alice-pk",
                "status": "pending",
                "invited_at": "2025-12-20T00:00:00Z"
            }
        }


class ExitRecord(BaseModel):
    """Record that someone left a community.

    NO exit interview. NO surveillance. Just: they left.
    This is for cell stewards to know membership changed.
    """
    user_id: str
    cell_id: str
    left_at: datetime = Field(default_factory=datetime.utcnow)

    # Deliberately minimal - no "why" tracking, no exit count
    # If they want to make a statement, they use fork_reason

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "maria-pk",
                "cell_id": "cell-main",
                "left_at": "2025-12-20T00:00:00Z"
            }
        }


# Privacy Guarantees
"""
What we track:
- That you exported data (the export request)
- Who you asked for connection consent
- That you forked (the fork record)

What we DON'T track:
- Why you left (unless you chose to share fork_reason)
- How many times you've left communities
- "Exit interview" data
- Individual "departure risk" scores
- Who declined your connection requests (consent deleted after export)

Exiting is a right, not suspicious behavior.
"""
