"""Economic Withdrawal - Coordinated Wealth Deconcentration Models

Every transaction in the gift economy is a transaction that DIDN'T go to Bezos.

This is economic strike as praxis. Coordinated campaigns to redirect spending
from extractive corporations to regenerative community systems.

CAMPAIGN TYPES:
- Amazon Exit: Collective boycott + local alternatives
- Local Food Shift: Redirect grocery spending to community sources
- Tool Library: Eliminate individual purchases through sharing
- Skill Share: Replace credentialing with free exchange
- Housing Mutual Aid: Co-ops instead of rent extraction
- Transport Commons: Ride shares instead of Uber/cars
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class CampaignType(str, Enum):
    """Types of economic withdrawal campaigns."""
    AMAZON_EXIT = "amazon_exit"
    LOCAL_FOOD_SHIFT = "local_food_shift"
    TOOL_LIBRARY = "tool_library"
    SKILL_SHARE = "skill_share"
    HOUSING_MUTUAL_AID = "housing_mutual_aid"
    TRANSPORT_COMMONS = "transport_commons"
    BULK_BUY = "bulk_buy"
    CUSTOM = "custom"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""
    GATHERING = "gathering"  # Collecting pledges
    ACTIVE = "active"        # Campaign running
    COMPLETED = "completed"  # Campaign finished
    CANCELLED = "cancelled"  # Campaign cancelled


class PledgeStatus(str, Enum):
    """Member pledge status."""
    COMMITTED = "committed"  # Pledged to participate
    ACTIVE = "active"        # Campaign started, participating
    COMPLETED = "completed"  # Fulfilled commitment
    BROKEN = "broken"        # Did not follow through


class Campaign(BaseModel):
    """An economic withdrawal campaign.

    Collective action to redirect spending from extractive to regenerative.
    """
    id: str = Field(description="Unique campaign ID")
    campaign_type: CampaignType = Field(description="Type of campaign")
    name: str = Field(description="Campaign name (e.g., 'No Amazon November')")
    description: str = Field(description="What this campaign is about")

    # Targeting
    target_corporation: str = Field(
        description="What we're withdrawing from (e.g., 'Amazon', 'Walmart')"
    )
    target_category: Optional[str] = Field(
        default=None,
        description="Category (e.g., 'online retail', 'grocery', 'transport')"
    )

    # Scope
    cell_id: Optional[str] = Field(
        default=None,
        description="Cell running this campaign (if cell-scoped)"
    )
    network_wide: bool = Field(
        default=False,
        description="Is this network-wide or cell-specific?"
    )

    # Activation
    created_by: str = Field(description="Steward who created campaign")
    threshold_participants: int = Field(
        description="Minimum participants to activate campaign"
    )
    current_participants: int = Field(
        default=0,
        description="Current number of pledges"
    )
    status: CampaignStatus = Field(
        default=CampaignStatus.GATHERING,
        description="Current campaign status"
    )

    # Timeline
    pledge_deadline: datetime = Field(
        description="Deadline to pledge participation"
    )
    campaign_start: datetime = Field(
        description="When campaign starts (if activated)"
    )
    campaign_end: datetime = Field(
        description="When campaign ends"
    )

    # Impact tracking
    estimated_economic_impact: Optional[float] = Field(
        default=None,
        description="Estimated dollars redirected (calculated)"
    )
    network_value_circulated: Optional[float] = Field(
        default=None,
        description="Value circulated within network"
    )
    local_transactions_facilitated: int = Field(
        default=0,
        description="Number of local alternative transactions"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = Field(
        default=None,
        description="When campaign activated"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When campaign completed"
    )

    def can_activate(self) -> bool:
        """Check if campaign can activate (threshold met, before deadline)."""
        return (
            self.current_participants >= self.threshold_participants and
            datetime.now(UTC) < self.pledge_deadline and
            self.status == CampaignStatus.GATHERING
        )

    def activate(self):
        """Activate campaign (move from GATHERING to ACTIVE)."""
        if not self.can_activate():
            raise ValueError("Campaign cannot be activated yet")

        self.status = CampaignStatus.ACTIVE
        self.activated_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def complete(self):
        """Complete campaign (calculate final impact)."""
        self.status = CampaignStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "campaign-001",
                "campaign_type": "amazon_exit",
                "name": "No Amazon November",
                "description": "Collective commitment to buy nothing from Amazon for 30 days",
                "target_corporation": "Amazon",
                "target_category": "online_retail",
                "cell_id": "cell-001",
                "network_wide": False,
                "created_by": "steward-pk-123",
                "threshold_participants": 100,
                "current_participants": 0,
                "status": "gathering",
                "pledge_deadline": "2025-10-31T23:59:59Z",
                "campaign_start": "2025-11-01T00:00:00Z",
                "campaign_end": "2025-11-30T23:59:59Z",
                "created_at": "2025-10-01T00:00:00Z"
            }
        }


class CampaignPledge(BaseModel):
    """A member's pledge to participate in a campaign."""
    id: str = Field(description="Unique pledge ID")
    campaign_id: str = Field(description="Campaign being pledged to")
    user_id: str = Field(description="Member making pledge")

    # Commitment
    commitment_level: str = Field(
        default="full",
        description="Level: 'full' (100%), 'partial' (reduce by X%), 'explore' (try alternatives)"
    )
    commitment_notes: Optional[str] = Field(
        default=None,
        description="Personal notes about commitment"
    )

    # Status
    status: PledgeStatus = Field(
        default=PledgeStatus.COMMITTED,
        description="Current pledge status"
    )

    # Impact tracking (self-reported + estimated)
    times_avoided_target: int = Field(
        default=0,
        description="Number of times avoided target corporation"
    )
    estimated_spending_redirected: Optional[float] = Field(
        default=None,
        description="Estimated dollars redirected (self-reported or calculated)"
    )
    alternatives_used: int = Field(
        default=0,
        description="Number of alternative transactions"
    )

    # Buddy system
    buddy_id: Optional[str] = Field(
        default=None,
        description="Accountability buddy (optional)"
    )

    # Metadata
    pledged_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When pledge made"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update"
    )

    def mark_avoided(self, estimated_value: Optional[float] = None):
        """Mark that user avoided target corporation once."""
        self.times_avoided_target += 1
        if estimated_value:
            if self.estimated_spending_redirected:
                self.estimated_spending_redirected += estimated_value
            else:
                self.estimated_spending_redirected = estimated_value
        self.updated_at = datetime.now(UTC)

    def mark_alternative_used(self):
        """Mark that user used an alternative transaction."""
        self.alternatives_used += 1
        self.updated_at = datetime.now(UTC)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pledge-001",
                "campaign_id": "campaign-001",
                "user_id": "user-pk-456",
                "commitment_level": "full",
                "commitment_notes": "Time to break my Amazon addiction!",
                "status": "committed",
                "times_avoided_target": 0,
                "alternatives_used": 0,
                "pledged_at": "2025-10-15T12:00:00Z"
            }
        }


class CorporateAlternative(BaseModel):
    """A community alternative to a corporate service.

    Maps extractive services to regenerative community alternatives.
    """
    id: str = Field(description="Unique alternative ID")
    campaign_type: CampaignType = Field(description="Campaign type this supports")

    # Corporate target
    replaces_corporation: str = Field(
        description="Corporation this replaces (e.g., 'Amazon')"
    )
    replaces_service: str = Field(
        description="Specific service (e.g., 'online retail', 'groceries')"
    )

    # Alternative details
    alternative_type: str = Field(
        description="Type: 'network_sharing', 'local_business', 'co_op', 'mutual_aid'"
    )
    name: str = Field(description="Name of alternative")
    description: str = Field(description="What this alternative provides")

    # Availability
    cell_id: Optional[str] = Field(
        default=None,
        description="Cell where this alternative exists (if local)"
    )
    network_wide: bool = Field(
        default=False,
        description="Available network-wide?"
    )

    # Contact/access
    contact_user_id: Optional[str] = Field(
        default=None,
        description="User managing this alternative"
    )
    access_instructions: Optional[str] = Field(
        default=None,
        description="How to access (e.g., 'DM Maria for tool library key')"
    )

    # Usage tracking
    times_used: int = Field(
        default=0,
        description="Number of times this alternative was used"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(description="Who added this alternative")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alt-001",
                "campaign_type": "tool_library",
                "replaces_corporation": "Home Depot",
                "replaces_service": "tool rental/purchase",
                "alternative_type": "network_sharing",
                "name": "Downtown Tool Library",
                "description": "Shared power tools, hand tools, garden equipment",
                "cell_id": "cell-001",
                "network_wide": False,
                "contact_user_id": "user-pk-789",
                "access_instructions": "DM Maria (@maria) for access code",
                "times_used": 47,
                "created_at": "2025-10-01T00:00:00Z",
                "created_by": "steward-pk-123"
            }
        }


class ExitProgress(BaseModel):
    """A member's progress in exiting extractive economy.

    Tracks personal journey toward economic withdrawal.
    """
    id: str = Field(description="Unique progress record ID")
    user_id: str = Field(description="Member being tracked")

    # Categories
    categories: Dict[str, dict] = Field(
        description="Progress by category (amazon, grocery, transport, etc.)"
    )
    # Example:
    # {
    #   "amazon": {
    #     "baseline_monthly_spending": 200.0,
    #     "current_monthly_spending": 50.0,
    #     "reduction_percent": 75.0,
    #     "last_purchase": "2025-09-15"
    #   },
    #   "grocery": {...}
    # }

    # Overall
    total_estimated_redirected: float = Field(
        default=0.0,
        description="Total estimated spending redirected (all time)"
    )
    campaigns_participated: int = Field(
        default=0,
        description="Number of campaigns participated in"
    )
    campaigns_completed: int = Field(
        default=0,
        description="Number of campaigns completed successfully"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "progress-001",
                "user_id": "user-pk-456",
                "categories": {
                    "amazon": {
                        "baseline_monthly_spending": 200.0,
                        "current_monthly_spending": 50.0,
                        "reduction_percent": 75.0,
                        "last_purchase": "2025-09-15"
                    },
                    "grocery": {
                        "baseline_monthly_spending": 500.0,
                        "current_monthly_spending": 350.0,
                        "reduction_percent": 30.0,
                        "community_sources_percent": 35.0
                    }
                },
                "total_estimated_redirected": 3500.0,
                "campaigns_participated": 5,
                "campaigns_completed": 3,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-12-19T00:00:00Z"
            }
        }


class BulkBuyOrder(BaseModel):
    """A coordinated bulk purchase to get wholesale pricing.

    Collective bargaining for better prices.
    """
    id: str = Field(description="Unique bulk buy ID")
    campaign_id: Optional[str] = Field(
        default=None,
        description="Parent campaign (if part of larger campaign)"
    )

    # Item details
    item_name: str = Field(description="What's being bought (e.g., 'organic rice')")
    item_description: str = Field(description="Details about item")
    unit: str = Field(description="Unit (lb, kg, count)")

    # Pricing
    retail_price_per_unit: float = Field(description="Retail price per unit")
    wholesale_price_per_unit: float = Field(description="Wholesale price (if threshold met)")
    savings_percent: float = Field(description="Percent savings vs retail")

    # Threshold
    minimum_units: int = Field(description="Minimum units to get wholesale pricing")
    current_committed_units: int = Field(
        default=0,
        description="Units currently committed"
    )

    # Coordination
    cell_id: str = Field(description="Cell coordinating this bulk buy")
    coordinator_id: str = Field(description="Steward coordinating")
    supplier: Optional[str] = Field(
        default=None,
        description="Wholesale supplier (or local farm/co-op)"
    )

    # Timeline
    commitment_deadline: datetime = Field(description="Deadline to commit")
    delivery_date: datetime = Field(description="When delivery happens")
    distribution_location: Optional[str] = Field(
        default=None,
        description="Where to pick up (general location only)"
    )

    # Status
    status: str = Field(
        default="gathering",
        description="Status: gathering, confirmed, ordered, delivered, distributed"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def can_order(self) -> bool:
        """Check if bulk buy can be ordered (threshold met)."""
        return self.current_committed_units >= self.minimum_units

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bulk-001",
                "item_name": "Organic Brown Rice",
                "item_description": "25lb bags, local organic farm",
                "unit": "lb",
                "retail_price_per_unit": 3.50,
                "wholesale_price_per_unit": 2.00,
                "savings_percent": 42.9,
                "minimum_units": 500,
                "current_committed_units": 0,
                "cell_id": "cell-001",
                "coordinator_id": "steward-pk-123",
                "supplier": "Valley View Organic Farm",
                "commitment_deadline": "2025-12-25T23:59:59Z",
                "delivery_date": "2026-01-05T10:00:00Z",
                "status": "gathering",
                "created_at": "2025-12-01T00:00:00Z"
            }
        }


class BulkBuyCommitment(BaseModel):
    """A member's commitment to a bulk buy."""
    id: str = Field(description="Unique commitment ID")
    bulk_buy_id: str = Field(description="Bulk buy being committed to")
    user_id: str = Field(description="Member committing")

    units: int = Field(description="Number of units committed")
    total_cost: float = Field(description="Total cost for this member")

    # Payment/fulfillment
    paid: bool = Field(default=False, description="Has member paid?")
    picked_up: bool = Field(default=False, description="Has member picked up?")

    # Metadata
    committed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "commitment-001",
                "bulk_buy_id": "bulk-001",
                "user_id": "user-pk-456",
                "units": 25,
                "total_cost": 50.00,
                "paid": False,
                "picked_up": False,
                "committed_at": "2025-12-10T12:00:00Z"
            }
        }
