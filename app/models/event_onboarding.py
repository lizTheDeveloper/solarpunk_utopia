"""Event-Based Mass Onboarding Models"""
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """Type of onboarding event"""
    WORKSHOP = "workshop"
    GATHERING = "gathering"
    COMMUNITY_MEETING = "community_meeting"
    FESTIVAL = "festival"
    PRIVATE_EVENT = "private_event"


class TrustLevel(str, Enum):
    """Graduated trust levels for users"""
    EVENT = "event"  # Can participate in event only (0.3)
    MEMBER = "member"  # Cell access, can post (0.5)
    ESTABLISHED = "established"  # Can vouch others (0.7)
    STEWARD = "steward"  # Steward actions (0.9)
    GENESIS = "genesis"  # Genesis node (1.0)


class EventInvite(BaseModel):
    """An event invitation for mass onboarding"""
    id: str = Field(description="Unique event invite ID")
    created_by: str = Field(description="User ID of event organizer (steward)")
    event_name: str = Field(description="Name of the event")
    event_type: EventType = Field(description="Type of event")
    event_start: datetime = Field(description="When the event starts")
    event_end: datetime = Field(description="When the event ends")
    event_location: Optional[str] = Field(None, description="Location of event")
    max_attendees: Optional[int] = Field(None, description="Maximum number of attendees (None = unlimited)")
    invite_code: str = Field(description="Unique code/QR for scanning")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="When this invite expires")
    active: bool = Field(default=True, description="Whether invite is still active")
    attendee_count: int = Field(default=0, description="Number of people who used this invite")
    temporary_trust_level: float = Field(default=0.3, description="Trust level granted during event")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "event-001",
                "created_by": "steward-alice",
                "event_name": "Solarpunk Workshop",
                "event_type": "workshop",
                "event_start": "2025-12-20T10:00:00Z",
                "event_end": "2025-12-20T18:00:00Z",
                "event_location": "Portland Community Center",
                "max_attendees": 200,
                "invite_code": "WORKSHOP2025",
                "created_at": "2025-12-19T00:00:00Z",
                "expires_at": "2025-12-21T00:00:00Z",
                "active": True,
                "attendee_count": 0,
                "temporary_trust_level": 0.3,
            }
        }


class CreateEventInviteRequest(BaseModel):
    """Request to create an event invite"""
    event_name: str = Field(description="Name of the event")
    event_type: EventType = Field(description="Type of event")
    event_start: datetime = Field(description="When the event starts")
    event_end: datetime = Field(description="When the event ends")
    event_location: Optional[str] = Field(None, description="Location of event")
    max_attendees: Optional[int] = Field(None, description="Maximum number of attendees")
    temporary_trust_level: float = Field(default=0.3, ge=0.0, le=1.0, description="Trust level during event")


class BatchInvite(BaseModel):
    """A batch invite link for a steward to share"""
    id: str = Field(description="Unique batch invite ID")
    created_by: str = Field(description="User ID of steward creating invite")
    invite_link: str = Field(description="Unique invite link/code")
    max_uses: int = Field(description="Maximum number of people who can use this link")
    used_count: int = Field(default=0, description="Number of people who used this link")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="When this invite expires")
    active: bool = Field(default=True, description="Whether invite is still active")
    context: str = Field(description="How/why this batch invite was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "batch-001",
                "created_by": "steward-carlos",
                "invite_link": "BATCH-CARLOS-001",
                "max_uses": 20,
                "used_count": 0,
                "created_at": "2025-12-19T00:00:00Z",
                "expires_at": "2025-12-26T00:00:00Z",
                "active": True,
                "context": "Community leader bringing trusted members",
            }
        }


class CreateBatchInviteRequest(BaseModel):
    """Request to create a batch invite"""
    max_uses: int = Field(ge=1, le=100, description="Maximum number of uses (1-100)")
    days_valid: int = Field(default=7, ge=1, le=30, description="Number of days invite is valid")
    context: str = Field(description="Why are you creating this invite?")


class EventAttendee(BaseModel):
    """Record of someone who joined via event"""
    id: str = Field(description="Unique attendee record ID")
    event_id: str = Field(description="Event invite ID they used")
    user_id: str = Field(description="User ID of attendee")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    upgraded_to_member: bool = Field(default=False, description="Whether they upgraded to full member after event")
    upgraded_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "attendee-001",
                "event_id": "event-001",
                "user_id": "user-bob",
                "joined_at": "2025-12-20T10:15:00Z",
                "upgraded_to_member": False,
            }
        }


class OnboardingAnalytics(BaseModel):
    """Analytics for stewards about onboarding"""
    total_event_invites: int = Field(default=0, description="Total event invites created")
    total_batch_invites: int = Field(default=0, description="Total batch invites created")
    total_event_attendees: int = Field(default=0, description="Total people joined via events")
    total_batch_members: int = Field(default=0, description="Total people joined via batch invites")
    upgrade_rate: float = Field(default=0.0, description="% of event attendees who upgraded to full members")
    active_events: int = Field(default=0, description="Number of currently active events")
    recent_joins_24h: int = Field(default=0, description="New members in last 24 hours")
    trust_level_distribution: dict = Field(default_factory=dict, description="Count of users at each trust level")

    class Config:
        json_schema_extra = {
            "example": {
                "total_event_invites": 5,
                "total_batch_invites": 10,
                "total_event_attendees": 200,
                "total_batch_members": 50,
                "upgrade_rate": 0.65,
                "active_events": 2,
                "recent_joins_24h": 15,
                "trust_level_distribution": {
                    "event": 40,
                    "member": 150,
                    "established": 50,
                    "steward": 10,
                },
            }
        }


class UseEventInviteRequest(BaseModel):
    """Request to join via event invite"""
    invite_code: str = Field(description="Event invite code from QR or link")
    user_name: str = Field(description="Display name for new user")
    location: Optional[str] = Field(None, description="User's location (city, region)")


class UseBatchInviteRequest(BaseModel):
    """Request to join via batch invite"""
    invite_link: str = Field(description="Batch invite link/code")
    user_name: str = Field(description="Display name for new user")
    location: Optional[str] = Field(None, description="User's location (city, region)")
