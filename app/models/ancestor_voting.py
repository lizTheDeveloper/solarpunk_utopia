"""Models for Ancestor Voting

'The only good authority is a dead one.' - Mikhail Bakunin

When members leave, their reputation becomes a Memorial Fund that amplifies
marginalized voices instead of concentrating power.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class DepartureType(Enum):
    """Type of user departure."""
    VOLUNTARY = "voluntary"
    DEATH = "death"
    REMOVAL = "removal"
    INACTIVE = "inactive"


class AllocationStatus(Enum):
    """Status of a ghost reputation allocation."""
    ACTIVE = "active"
    REFUNDED = "refunded"
    COMPLETED = "completed"
    VETOED = "vetoed"


class ProposalStatus(Enum):
    """Status of a proposal."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class AuditAction(Enum):
    """Audit log actions."""
    ALLOCATED = "allocated"
    VETOED = "vetoed"
    REFUNDED = "refunded"
    COMPLETED = "completed"


@dataclass
class MemorialFund:
    """Memorial Fund created from a departed member's reputation."""
    id: str
    created_from_user_id: str
    departed_user_name: str

    # Reputation balance
    initial_reputation: float
    current_balance: float

    # Metadata
    created_at: datetime
    updated_at: datetime

    # Optional fields with explicit defaults
    departed_user_display_name: Optional[str] = None
    family_requested_removal: bool = False
    removal_requested_at: Optional[datetime] = None


@dataclass
class GhostReputationAllocation:
    """Allocation of Ghost Reputation to boost a proposal."""
    id: str
    fund_id: str
    proposal_id: str

    # Allocation details
    amount: float
    allocated_by: str  # Steward user ID
    reason: str

    # Status
    status: AllocationStatus

    # Timestamps (required fields)
    allocated_at: datetime
    veto_deadline: datetime

    # Optional fields with defaults
    refunded: bool = False
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Anti-abuse: veto window
    vetoed: bool = False
    vetoed_by: Optional[str] = None
    veto_reason: Optional[str] = None
    vetoed_at: Optional[datetime] = None


@dataclass
class ProposalAncestorAttribution:
    """Attribution of ancestor reputation to a proposal."""
    id: str
    proposal_id: str
    allocation_id: str
    fund_id: str

    # Attribution details
    ancestor_name: str
    reputation_amount: float

    # Impact tracking
    proposal_status: ProposalStatus
    attributed_at: datetime


@dataclass
class UserDepartureRecord:
    """Record of a user's departure from the network."""
    id: str
    user_id: str

    # Departure details
    departure_type: DepartureType

    # Reputation transfer
    final_reputation: float

    # Metadata (required fields)
    departed_at: datetime

    # Optional fields with explicit defaults
    departure_reason: Optional[str] = None
    memorial_fund_id: Optional[str] = None
    private_data_purged: bool = False
    purged_at: Optional[datetime] = None
    public_contributions_retained: bool = True
    recorded_by: Optional[str] = None  # Who recorded the departure


@dataclass
class AllocationPriority:
    """Priority factors for an allocation."""
    id: str
    allocation_id: str

    # Required fields
    priority_score: int
    calculated_at: datetime

    # Priority factors (optional with defaults)
    is_new_member: bool = False  # <3 months
    has_low_reputation: bool = False
    is_controversial: bool = False
    is_marginalized_identity: bool = False  # Self-disclosed


@dataclass
class MemorialImpactTracking:
    """Impact metrics for a Memorial Fund."""
    id: str
    fund_id: str

    # Metadata (required)
    last_updated: datetime

    # Impact metrics (optional with defaults)
    total_allocated: float = 0.0
    total_refunded: float = 0.0
    proposals_boosted: int = 0
    proposals_approved: int = 0
    proposals_implemented: int = 0

    # Marginalized voice metrics
    new_members_helped: int = 0
    controversial_proposals_boosted: int = 0


@dataclass
class AllocationAuditLog:
    """Audit log entry for allocation transparency."""
    id: str
    allocation_id: str

    # Audit details
    action: AuditAction
    actor_id: str
    actor_role: str  # 'steward', 'system'

    # Timestamp (required)
    logged_at: datetime

    # Context (optional)
    details: Optional[str] = None  # JSON with additional context
