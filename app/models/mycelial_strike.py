"""Models for Mycelial Strike

'Mutual Aid includes Mutual Defense.' - Peter Kropotkin

The mycelium doesn't just share nutrients - it also fights infections.
Automated solidarity defense against extractive behavior.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class AbuseType(Enum):
    """Type of abusive behavior."""
    BATTERY_WARLORD = "battery_warlord"  # Extraction without contribution
    EXTRACTION_PATTERN = "extraction_pattern"
    HARASSMENT = "harassment"
    SPAM = "spam"
    EXPLOITATION = "exploitation"


class ThrottleLevel(Enum):
    """Level of throttling applied."""
    LOW = "low"  # Deprioritize in matching
    MEDIUM = "medium"  # Add message latency + matching penalty
    HIGH = "high"  # Full throttle - minimal interaction
    CRITICAL = "critical"  # Automatic isolation pending steward review


class StrikeStatus(Enum):
    """Status of a strike."""
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    OVERRIDDEN = "overridden"


class OverrideAction(Enum):
    """Type of steward override."""
    CANCEL_STRIKE = "cancel_strike"
    CANCEL_ALERT = "cancel_alert"
    ADJUST_SEVERITY = "adjust_severity"
    WHITELIST_USER = "whitelist_user"


class DeescalationReason(Enum):
    """Reason for de-escalation."""
    BEHAVIOR_IMPROVED = "behavior_improved"
    TIME_ELAPSED = "time_elapsed"
    STEWARD_OVERRIDE = "steward_override"


@dataclass
class EvidenceItem:
    """A piece of evidence for an abuse alert."""
    type: str  # 'exchange', 'pattern', 'report', 'behavior'
    details: str
    reliability_score: float = 1.0


@dataclass
class WarlordAlert:
    """Alert about extractive behavior, propagated through the mesh."""
    id: str
    target_user_id: str

    # Severity and type
    severity: int  # 1-10
    abuse_type: AbuseType

    # Evidence
    evidence: List[EvidenceItem]

    # Source
    reporting_node_fingerprint: str

    # Lifecycle (required fields)
    created_at: datetime
    expires_at: datetime  # 7 days default

    # Optional fields with defaults
    reporting_user_id: Optional[str] = None
    trusted_source: bool = True
    propagation_count: int = 0
    cancelled: bool = False
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None


@dataclass
class ThrottleActions:
    """Actions to take when throttling a user."""
    deprioritize_matching: bool = False
    add_message_latency: int = 0  # Milliseconds
    reduce_proposal_visibility: bool = False
    show_warning_indicator: bool = False
    block_high_value_exchanges: bool = False


@dataclass
class LocalStrike:
    """A local strike against an abusive user."""
    id: str
    alert_id: str
    target_user_id: str

    # Throttle configuration
    throttle_level: ThrottleLevel
    throttle_actions: ThrottleActions

    # Status
    status: StrikeStatus

    # Behavior tracking (required)
    behavior_score_at_start: float
    current_behavior_score: float

    # Timestamps (required)
    activated_at: datetime

    # Optional fields with defaults
    automatic: bool = True
    deactivated_at: Optional[datetime] = None
    overridden_by: Optional[str] = None
    override_reason: Optional[str] = None
    overridden_at: Optional[datetime] = None


@dataclass
class StrikeEvidence:
    """Evidence collected for a strike."""
    id: str
    alert_id: str

    # Evidence details
    evidence_type: str
    evidence_data: Dict[str, Any]

    # Source
    collected_by: str  # Node fingerprint

    # Timestamp
    collected_at: datetime

    # Weight
    reliability_score: float = 1.0


@dataclass
class StrikePropagation:
    """Record of strike alert propagation between nodes."""
    id: str
    alert_id: str

    # Propagation details
    from_node_fingerprint: str
    to_node_fingerprint: str

    # Trust
    trust_score: float

    # Timestamp
    propagated_at: datetime

    # Status
    accepted: bool = True
    rejection_reason: Optional[str] = None


@dataclass
class BehaviorTracking:
    """Tracking of user behavior for strike de-escalation."""
    id: str
    user_id: str

    # Calculated score
    behavior_score: float  # 0-10, higher is better

    # Tracking period
    period_start: datetime
    period_end: datetime
    last_updated: datetime

    # Optional fields
    strike_id: Optional[str] = None

    # Behavior metrics
    exchanges_given: int = 0
    exchanges_received: int = 0
    offers_posted: int = 0
    needs_posted: int = 0


@dataclass
class StrikeDeescalationLog:
    """Log of strike de-escalation."""
    id: str
    strike_id: str

    # De-escalation details
    previous_level: ThrottleLevel
    new_level: ThrottleLevel
    trigger_reason: DeescalationReason

    # Behavior at time of de-escalation
    behavior_score: float

    # Timestamp
    deescalated_at: datetime


@dataclass
class StrikeOverrideLog:
    """Log of steward overrides."""
    id: str
    alert_id: Optional[str]

    # Override details
    action: OverrideAction
    override_by: str  # Steward user ID
    reason: str

    # Timestamp
    overridden_at: datetime

    # What was overridden
    strike_id: Optional[str] = None

    # Before/after snapshots
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None


@dataclass
class UserStrikeWhitelist:
    """User whitelisted from automatic strikes."""
    id: str
    user_id: str

    # Whitelist details
    whitelisted_by: str  # Steward user ID
    reason: str

    # Scope
    scope: str  # 'all', 'specific_abuse_type'

    # Timestamp
    whitelisted_at: datetime

    # Optional fields
    abuse_type: Optional[AbuseType] = None

    # Duration
    is_permanent: bool = False
    expires_at: Optional[datetime] = None


@dataclass
class StrikeNetworkStats:
    """Aggregate statistics for the strike network."""
    id: str

    # Timeframe
    period_start: datetime
    period_end: datetime

    # Timestamp
    calculated_at: datetime

    # Alert metrics
    total_alerts_created: int = 0
    total_alerts_propagated: int = 0
    total_alerts_cancelled: int = 0

    # Strike metrics
    total_strikes_activated: int = 0
    total_strikes_deescalated: int = 0
    total_strikes_overridden: int = 0

    # False positive tracking
    false_positive_count: int = 0
    false_positive_rate: float = 0.0

    # Effectiveness
    behavior_improvement_count: int = 0
