"""Sanctuary Network - Underground Railroad Infrastructure

Coordinates safe houses, transport, legal resources for people at risk.

CRITICAL OPSEC:
- Auto-purge after 24 hours
- High trust requirements (>0.8)
- No permanent records of who helped whom
- Steward verification required
"""
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SensitivityLevel(str, Enum):
    """Sensitivity level for sanctuary resources."""
    HIGH = "high"        # >0.8 trust, extra verification, never broadcast
    MEDIUM = "medium"    # >0.6 trust, cell-scoped
    LOW = "low"          # Standard visibility


class SanctuaryResourceType(str, Enum):
    """Types of sanctuary resources."""
    SAFE_SPACE = "safe_space"          # Spare room, basement, rural property
    TRANSPORT = "transport"            # Car, bike, knowledge of routes
    LEGAL = "legal"                    # Immigration lawyer, bail fund
    SUPPLIES = "supplies"              # Food, clothes, cash, burner phones
    SKILLS = "skills"                  # Translation, medical, de-escalation
    INTEL = "intel"                    # ICE activity, checkpoint locations


class VerificationStatus(str, Enum):
    """Verification status for sanctuary offers."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class SanctuaryResource(BaseModel):
    """A sanctuary resource offer (safe space, transport, legal, etc)."""
    id: str = Field(description="Unique resource ID")
    resource_type: SanctuaryResourceType = Field(description="Type of resource")
    sensitivity: SensitivityLevel = Field(description="Sensitivity level")
    offered_by: str = Field(description="User ID of person offering")
    cell_id: str = Field(description="Cell this resource belongs to")

    # Details (minimal, encrypted at rest)
    description: str = Field(description="Brief description (use code words)")
    capacity: Optional[int] = Field(
        default=None,
        description="Capacity: people for safe space, seats for transport, etc."
    )
    duration_days: Optional[int] = Field(
        default=None,
        description="How long resource is available (days)"
    )

    # Verification
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="Verification status"
    )
    verified_by: Optional[str] = Field(
        default=None,
        description="Steward who verified (if verified)"
    )
    verified_at: Optional[datetime] = Field(
        default=None,
        description="When verified"
    )
    verification_notes: Optional[str] = Field(
        default=None,
        description="Verification notes (encrypted, steward-only)"
    )

    # Availability
    available: bool = Field(default=True, description="Currently available?")
    available_from: datetime = Field(
        default_factory=datetime.utcnow,
        description="Available from"
    )
    available_until: Optional[datetime] = Field(
        default=None,
        description="Available until"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    purge_at: Optional[datetime] = Field(
        default=None,
        description="Auto-purge timestamp (set when matched)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sanctuary-res-001",
                "resource_type": "safe_space",
                "sensitivity": "high",
                "offered_by": "user-pk-123",
                "cell_id": "cell-001",
                "description": "Phoenix location, 2 people, 1 week max",
                "capacity": 2,
                "duration_days": 7,
                "verification_status": "verified",
                "verified_by": "steward-pk-456",
                "verified_at": "2025-12-19T00:00:00Z",
                "available": True,
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class SanctuaryRequest(BaseModel):
    """A request for sanctuary resources."""
    id: str = Field(description="Unique request ID")
    request_type: SanctuaryResourceType = Field(description="Type of resource needed")
    urgency: str = Field(
        description="Urgency: critical (minutes), urgent (hours), soon (days)"
    )

    # Requester info (minimal)
    requested_by: str = Field(description="User ID of requester")
    cell_id: str = Field(description="Cell making the request")
    verified_by: str = Field(description="Steward who verified request")

    # Need details (minimal)
    description: str = Field(description="Brief need description (use code words)")
    people_count: Optional[int] = Field(default=1, description="Number of people")
    duration_needed_days: Optional[int] = Field(
        default=None,
        description="Duration needed (days)"
    )
    location_hint: Optional[str] = Field(
        default=None,
        description="General location (city level, no addresses)"
    )

    # Status
    status: str = Field(
        default="pending",
        description="Status: pending, matched, completed, expired"
    )
    matched_resource_id: Optional[str] = Field(
        default=None,
        description="Resource matched to (if matched)"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When request completed"
    )

    # Auto-purge (CRITICAL)
    purge_at: datetime = Field(
        description="When to auto-purge (24 hours after completion)"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        description="When request expires if not matched"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Set purge_at if not provided (24 hours after completion)
        if not self.purge_at:
            self.purge_at = self.created_at + timedelta(days=1)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sanctuary-req-001",
                "request_type": "safe_space",
                "urgency": "urgent",
                "requested_by": "user-pk-789",
                "cell_id": "cell-001",
                "verified_by": "steward-pk-456",
                "description": "Person needs shelter, Phoenix area",
                "people_count": 1,
                "duration_needed_days": 3,
                "location_hint": "Phoenix metro",
                "status": "pending",
                "purge_at": "2025-12-20T00:00:00Z",
                "created_at": "2025-12-19T00:00:00Z",
                "expires_at": "2025-12-19T12:00:00Z"
            }
        }


class SanctuaryMatch(BaseModel):
    """A match between a sanctuary request and resource.

    CRITICAL: These are auto-purged 24 hours after completion.
    """
    id: str = Field(description="Unique match ID")
    request_id: str = Field(description="Request being matched")
    resource_id: str = Field(description="Resource being provided")
    cell_id: str = Field(description="Cell coordinating")

    # Coordination (minimal)
    coordinated_by: str = Field(description="Steward coordinating")
    status: str = Field(
        default="active",
        description="Status: active, completed, aborted"
    )

    # Completion
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When sanctuary completed"
    )

    # Auto-purge (CRITICAL)
    purge_at: datetime = Field(
        description="When to purge (24 hours after completion)"
    )

    # Metadata (minimal)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def mark_completed(self):
        """Mark match as completed and set purge timer."""
        self.completed_at = datetime.utcnow()
        self.status = "completed"
        # Purge 24 hours after completion
        self.purge_at = self.completed_at + timedelta(hours=24)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "sanctuary-match-001",
                "request_id": "sanctuary-req-001",
                "resource_id": "sanctuary-res-001",
                "cell_id": "cell-001",
                "coordinated_by": "steward-pk-456",
                "status": "active",
                "purge_at": "2025-12-20T00:00:00Z",
                "created_at": "2025-12-19T00:00:00Z"
            }
        }


class RapidAlert(BaseModel):
    """Rapid alert for immediate danger (ICE raids, etc).

    These broadcast to nearby high-trust members immediately.
    """
    id: str = Field(description="Unique alert ID")
    alert_type: str = Field(
        description="Type: ice_raid, checkpoint, detention, threat"
    )
    severity: str = Field(
        description="Severity: critical, high, medium"
    )

    # Source
    reported_by: str = Field(description="User reporting")
    cell_id: str = Field(description="Cell where alert originated")

    # Location (general only)
    location_hint: str = Field(
        description="General location (intersection, neighborhood)"
    )
    coordinates: Optional[dict] = Field(
        default=None,
        description="Optional coordinates (if safe to share)"
    )

    # Details
    description: str = Field(description="Brief description")
    people_affected: Optional[int] = Field(
        default=None,
        description="Number of people affected"
    )

    # Response tracking
    responders: List[str] = Field(
        default_factory=list,
        description="User IDs of people who responded"
    )
    resolved: bool = Field(default=False, description="Is situation resolved?")
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When resolved"
    )

    # Auto-purge (purge after 7 days)
    purge_at: datetime = Field(
        description="When to purge alert"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        description="When alert expires"
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Set default purge (7 days after creation)
        if not self.purge_at:
            self.purge_at = self.created_at + timedelta(days=7)
        # Set default expiration (24 hours)
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(hours=24)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert-001",
                "alert_type": "ice_raid",
                "severity": "critical",
                "reported_by": "user-pk-123",
                "cell_id": "cell-001",
                "location_hint": "7th & Main, downtown",
                "description": "ICE vans spotted, 4-5 agents",
                "people_affected": 2,
                "resolved": False,
                "purge_at": "2025-12-26T00:00:00Z",
                "created_at": "2025-12-19T00:00:00Z",
                "expires_at": "2025-12-20T00:00:00Z"
            }
        }


# Minimum trust level for sanctuary features
SANCTUARY_MIN_TRUST = 0.8  # High trust required for HIGH sensitivity resources
SANCTUARY_MEDIUM_TRUST = 0.6  # Medium trust for MEDIUM sensitivity


# Auto-purge timers
SANCTUARY_MATCH_PURGE_HOURS = 24  # Purge matches 24 hours after completion
SANCTUARY_REQUEST_PURGE_HOURS = 24  # Purge completed requests after 24 hours
RAPID_ALERT_PURGE_DAYS = 7  # Purge alerts after 7 days


# GAP-109: Sanctuary Verification Requirements
MIN_SANCTUARY_VERIFICATIONS = 2  # Minimum steward verifications required
VERIFICATION_VALIDITY_DAYS = 90  # Verification expires after 90 days


class SanctuaryVerification(BaseModel):
    """
    Multi-steward verification for sanctuary spaces (GAP-109).

    Ensures safety by requiring:
    - 2+ steward verifications
    - Verified escape routes
    - Buddy protocol in place
    - Track record of successful uses
    """

    space_id: str = Field(description="ID of sanctuary space being verified")
    verified_by: List[str] = Field(
        description="List of steward IDs who verified",
        default_factory=list
    )
    verified_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When verification was completed"
    )
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last physical check of space"
    )
    escape_routes: List[str] = Field(
        description="List of escape route descriptions",
        default_factory=list
    )
    has_buddy_protocol: bool = Field(
        default=False,
        description="Whether buddy system is in place"
    )
    successful_uses: int = Field(
        default=0,
        description="Number of successful sanctuary uses"
    )

    @property
    def is_valid(self) -> bool:
        """Check if verification is still valid."""
        # Must have minimum verifications
        if len(self.verified_by) < MIN_SANCTUARY_VERIFICATIONS:
            return False

        # Must not be expired
        age_days = (datetime.utcnow() - self.verified_at).days
        if age_days > VERIFICATION_VALIDITY_DAYS:
            return False

        return True

    @property
    def is_high_trust(self) -> bool:
        """Check if this space has proven track record for critical needs."""
        # For critical needs, require 3+ successful prior uses
        return self.successful_uses >= 3 and self.is_valid

    def add_verification(self, steward_id: str):
        """Add a steward verification."""
        if steward_id not in self.verified_by:
            self.verified_by.append(steward_id)
            self.verified_at = datetime.utcnow()

    def record_successful_use(self):
        """Record a successful sanctuary use."""
        self.successful_uses += 1
