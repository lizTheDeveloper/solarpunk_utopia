"""Rapid Response Coordination Models

When ICE shows up. When someone is detained. When the community needs to mobilize NOW.

CRITICAL DESIGN PRINCIPLES:
- 2-tap alert trigger (big red button + confirm)
- <30 second propagation via mesh
- High-priority DTN bundles preempt normal traffic
- Auto-purge sensitive data after 24 hours
- High trust required to trigger CRITICAL alerts
- Coordinator manages response (first steward online)
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AlertLevel(str, Enum):
    """Alert urgency levels."""
    CRITICAL = "critical"  # Active raid, detention, immediate danger
    URGENT = "urgent"      # Developing situation, heightened risk
    WATCH = "watch"        # Reported activity, monitor


class AlertType(str, Enum):
    """Types of rapid response alerts."""
    ICE_RAID = "ice_raid"
    CHECKPOINT = "checkpoint"
    DETENTION = "detention"
    WORKPLACE_RAID = "workplace_raid"
    THREAT = "threat"
    OTHER = "other"


class ResponderStatus(str, Enum):
    """Responder availability status."""
    RESPONDING = "responding"      # On my way
    AVAILABLE_FAR = "available_far"  # Can help but distant
    UNAVAILABLE = "unavailable"    # Cannot respond


class ResponderRole(str, Enum):
    """Roles responders can take."""
    WITNESS = "witness"         # Person who triggered alert
    COORDINATOR = "coordinator"  # Manages response (steward)
    PHYSICAL = "physical"       # Can physically respond
    LEGAL = "legal"             # Know-your-rights, lawyer contacts
    MEDIA = "media"             # Documenter, journalist
    SUPPORT = "support"         # Supplies, transport, childcare


class AlertStatus(str, Enum):
    """Current status of an alert."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    FALSE_ALARM = "false_alarm"


class RapidAlert(BaseModel):
    """A rapid response alert for immediate danger.

    Broadcasts to nearby high-trust members via high-priority DTN bundles.
    """
    id: str = Field(description="Unique alert ID")
    alert_type: AlertType = Field(description="Type of alert")
    alert_level: AlertLevel = Field(description="Urgency level")
    status: AlertStatus = Field(default=AlertStatus.ACTIVE, description="Current status")

    # Source
    reported_by: str = Field(description="User ID of person reporting")
    cell_id: str = Field(description="Cell where alert originated")

    # Location (general only - no precise addresses for OPSEC)
    location_hint: str = Field(
        description="General location (intersection, neighborhood, city)"
    )
    coordinates: Optional[dict] = Field(
        default=None,
        description="Optional coordinates (if reporter enables location)"
    )

    # Details
    description: str = Field(description="Brief description of situation")
    people_affected: Optional[int] = Field(
        default=None,
        description="Estimated number of people affected"
    )

    # Coordinator (first steward to claim)
    coordinator_id: Optional[str] = Field(
        default=None,
        description="Steward coordinating response"
    )
    coordinator_claimed_at: Optional[datetime] = Field(
        default=None,
        description="When coordinator claimed"
    )

    # Resolution
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When situation resolved"
    )
    resolution_notes: Optional[str] = Field(
        default=None,
        description="Brief resolution summary"
    )

    # Confirmation (anti-false-alarm)
    confirmed: bool = Field(
        default=False,
        description="Has another member confirmed this alert?"
    )
    confirmed_by: Optional[str] = Field(
        default=None,
        description="User ID who confirmed"
    )
    confirmed_at: Optional[datetime] = Field(
        default=None,
        description="When confirmed"
    )
    auto_downgrade_at: Optional[datetime] = Field(
        default=None,
        description="When to auto-downgrade to WATCH if unconfirmed"
    )

    # DTN propagation
    bundle_id: Optional[str] = Field(
        default=None,
        description="DTN bundle ID for this alert"
    )
    propagation_radius_km: float = Field(
        default=50.0,
        description="Geographic radius for alert propagation (km)"
    )

    # Auto-purge (24 hours after resolution)
    purge_at: Optional[datetime] = Field(
        default=None,
        description="When to auto-purge (24 hours after resolution)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        description="When alert auto-expires if not resolved"
    )

    def __init__(self, **data):
        super().__init__(**data)

        # Set auto-downgrade for CRITICAL alerts (5 min to confirm or downgrade to WATCH)
        if self.alert_level == AlertLevel.CRITICAL and not self.auto_downgrade_at:
            self.auto_downgrade_at = self.created_at + timedelta(minutes=5)

        # Set default expiration based on level
        if not hasattr(self, 'expires_at') or not self.expires_at:
            if self.alert_level == AlertLevel.CRITICAL:
                self.expires_at = self.created_at + timedelta(hours=6)
            elif self.alert_level == AlertLevel.URGENT:
                self.expires_at = self.created_at + timedelta(hours=24)
            else:  # WATCH
                self.expires_at = self.created_at + timedelta(hours=48)

    def mark_resolved(self, resolution_notes: str):
        """Mark alert as resolved and set purge timer."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now(UTC)
        self.resolution_notes = resolution_notes
        # Purge 24 hours after resolution
        self.purge_at = self.resolved_at + timedelta(hours=24)
        self.updated_at = datetime.now(UTC)

    def confirm_alert(self, user_id: str):
        """Confirm alert (prevents auto-downgrade)."""
        self.confirmed = True
        self.confirmed_by = user_id
        self.confirmed_at = datetime.now(UTC)
        self.auto_downgrade_at = None  # Cancel auto-downgrade
        self.updated_at = datetime.now(UTC)

    def claim_coordinator(self, steward_id: str):
        """Claim coordinator role (first steward to respond)."""
        if not self.coordinator_id:
            self.coordinator_id = steward_id
            self.coordinator_claimed_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert-001",
                "alert_type": "ice_raid",
                "alert_level": "critical",
                "status": "active",
                "reported_by": "user-pk-123",
                "cell_id": "cell-001",
                "location_hint": "7th & Main, downtown Phoenix",
                "description": "ICE vans spotted, 4-5 agents, entering workplace",
                "people_affected": 2,
                "confirmed": False,
                "propagation_radius_km": 50.0,
                "created_at": "2025-12-19T10:00:00Z",
                "expires_at": "2025-12-19T16:00:00Z",
                "auto_downgrade_at": "2025-12-19T10:05:00Z"
            }
        }


class AlertResponder(BaseModel):
    """A person responding to a rapid alert."""
    id: str = Field(description="Unique responder record ID")
    alert_id: str = Field(description="Alert being responded to")
    user_id: str = Field(description="User ID of responder")

    # Status
    status: ResponderStatus = Field(description="Availability status")
    role: ResponderRole = Field(description="Role in response")

    # Details
    eta_minutes: Optional[int] = Field(
        default=None,
        description="Estimated time of arrival (minutes)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Brief notes (e.g., 'bringing camera', '10 min away')"
    )

    # Timestamps
    responded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When they indicated response"
    )
    arrived_at: Optional[datetime] = Field(
        default=None,
        description="When they arrived on scene"
    )
    departed_at: Optional[datetime] = Field(
        default=None,
        description="When they left scene"
    )

    def mark_arrived(self):
        """Mark responder as arrived on scene."""
        self.arrived_at = datetime.now(UTC)

    def mark_departed(self):
        """Mark responder as departed from scene."""
        self.departed_at = datetime.now(UTC)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "responder-001",
                "alert_id": "alert-001",
                "user_id": "user-pk-456",
                "status": "responding",
                "role": "legal",
                "eta_minutes": 15,
                "notes": "Know-your-rights cards + lawyer contact",
                "responded_at": "2025-12-19T10:02:00Z"
            }
        }


class AlertUpdate(BaseModel):
    """A status update posted during an active alert.

    Coordinator posts updates, all responders receive.
    """
    id: str = Field(description="Unique update ID")
    alert_id: str = Field(description="Alert this update belongs to")
    posted_by: str = Field(description="User ID who posted (usually coordinator)")

    # Update content
    update_type: str = Field(
        description="Type: status_change, escalation, de-escalation, info"
    )
    message: str = Field(description="Update message")

    # Level change (if escalation/de-escalation)
    new_alert_level: Optional[AlertLevel] = Field(
        default=None,
        description="New alert level (if changed)"
    )

    # DTN propagation
    bundle_id: Optional[str] = Field(
        default=None,
        description="DTN bundle ID for this update"
    )

    # Metadata
    posted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When posted"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "update-001",
                "alert_id": "alert-001",
                "posted_by": "coordinator-pk-789",
                "update_type": "info",
                "message": "Agents left building, situation cooling down",
                "posted_at": "2025-12-19T10:30:00Z"
            }
        }


class AlertMedia(BaseModel):
    """Media documentation captured during an alert.

    CRITICAL: All media is encrypted immediately on capture.
    Stored distributed, NOT on central server.
    """
    id: str = Field(description="Unique media ID")
    alert_id: str = Field(description="Alert this media belongs to")
    captured_by: str = Field(description="User ID who captured")

    # Media details
    media_type: str = Field(
        description="Type: photo, video, audio, document"
    )
    encrypted_data: Optional[str] = Field(
        default=None,
        description="Encrypted media data (or reference to distributed storage)"
    )
    storage_bundle_id: Optional[str] = Field(
        default=None,
        description="DTN bundle ID if stored in DTN"
    )
    file_size_bytes: int = Field(description="File size in bytes")

    # Metadata (encrypted)
    encrypted_metadata: Optional[str] = Field(
        default=None,
        description="Encrypted metadata (GPS, timestamp, device info)"
    )

    # Access control
    shared_with_legal: bool = Field(
        default=False,
        description="Shared with legal contacts?"
    )
    shared_with_media: bool = Field(
        default=False,
        description="Shared with media contacts?"
    )

    # Auto-purge
    purge_at: datetime = Field(
        description="When to auto-purge (24 hours after alert resolution)"
    )

    # Timestamps
    captured_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When captured"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "media-001",
                "alert_id": "alert-001",
                "captured_by": "user-pk-456",
                "media_type": "photo",
                "storage_bundle_id": "bundle-media-001",
                "file_size_bytes": 2048000,
                "shared_with_legal": True,
                "shared_with_media": False,
                "purge_at": "2025-12-20T10:00:00Z",
                "captured_at": "2025-12-19T10:15:00Z"
            }
        }


class AfterActionReview(BaseModel):
    """After-action review template for resolved alerts.

    What worked? What didn't? How can we improve?
    """
    id: str = Field(description="Unique review ID")
    alert_id: str = Field(description="Alert being reviewed")
    completed_by: str = Field(description="User ID who completed review (usually coordinator)")

    # Response analysis
    response_time_minutes: Optional[int] = Field(
        default=None,
        description="Time from alert to first responder on scene"
    )
    total_responders: int = Field(description="Number of responders")

    # What went well
    successes: str = Field(description="What worked well")

    # What needs improvement
    challenges: str = Field(description="What was difficult or didn't work")

    # Lessons learned
    lessons: str = Field(description="Key lessons for future responses")

    # Recommendations
    recommendations: str = Field(description="Changes to make for next time")

    # Metadata
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When review completed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "review-001",
                "alert_id": "alert-001",
                "completed_by": "coordinator-pk-789",
                "response_time_minutes": 12,
                "total_responders": 7,
                "successes": "Fast response, good coordination, legal observer arrived quickly",
                "challenges": "Mesh connection dropped briefly, some confusion about roles",
                "lessons": "Need clearer role assignments upfront, backup comms plan",
                "recommendations": "Designate backup coordinator, test mesh more often",
                "completed_at": "2025-12-19T14:00:00Z"
            }
        }


# Constants
CRITICAL_ALERT_MIN_TRUST = 0.7  # Minimum trust to trigger CRITICAL alerts
URGENT_ALERT_MIN_TRUST = 0.5    # Minimum trust to trigger URGENT alerts
WATCH_ALERT_MIN_TRUST = 0.3     # Minimum trust to trigger WATCH alerts

CRITICAL_CONFIRMATION_WINDOW_MINUTES = 5  # Auto-downgrade to WATCH if not confirmed
ALERT_PURGE_HOURS_AFTER_RESOLUTION = 24   # Purge 24 hours after resolution
