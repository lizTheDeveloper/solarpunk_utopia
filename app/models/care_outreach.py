"""Care Outreach Models - Saboteur Conversion Through Care

This isn't a security system. It's a care system.
Exclusion is failure. If we exclude someone, we've failed to build utopia for them.

Models for:
- Care volunteers (real humans who do care work)
- Outreach assignments (flagged users matched with volunteers)
- Outreach notes (private notes from volunteers)
- Access levels (based on trust but never zero)
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Literal, Optional
from enum import Enum


class AccessLevel(str, Enum):
    """Access levels - never zero, always human"""
    FULL = "full"  # Trust >= 0.7
    STANDARD = "standard"  # Trust >= 0.3
    RECEIVING_CARE = "receiving_care"  # In outreach, get basics
    MINIMAL_BUT_HUMAN = "minimal_but_human"  # Low trust but still human
    # Can still:
    # - Receive help if they ask
    # - Attend public events
    # - Be treated with dignity


class OutreachStatus(str, Enum):
    """Status of outreach efforts"""
    ACTIVE = "active"  # Currently being cared for
    CONVERTED = "converted"  # Came around
    CHOSE_TO_LEAVE = "chose_to_leave"  # Left on their own terms
    STILL_TRYING = "still_trying"  # Haven't given up


class DetectionReason(str, Enum):
    """Why someone was flagged - gentle, not accusatory"""
    PATTERN_FAKE_OFFERS = "pattern_fake_offers"  # Offers that never deliver
    VOUCH_VELOCITY = "vouch_velocity"  # Selling vouches
    INFO_HARVESTING = "info_harvesting"  # Collecting data on others
    COORDINATED_DISRUPTION = "coordinated_disruption"  # Organized sabotage
    REPEATED_NO_SHOWS = "repeated_no_shows"  # Flaking on commitments
    EXTRACTION_ONLY = "extraction_only"  # Taking without giving
    HARASSMENT = "harassment"  # Harmful to others
    OOPS = "oops"  # Honest mistake - Level 0
    STRUGGLING = "struggling"  # Life got hard - Level 1
    PATTERN_CONCERNING = "pattern"  # Repeated issues - Level 2
    HARMFUL = "harmful"  # Actively causing harm - Level 3
    SUSPECTED_INFILTRATOR = "infiltrator"  # Law enforcement / paid informant - Level 4


@dataclass
class CareVolunteer:
    """Real humans who've chosen to do care work

    This CANNOT be automated. You cannot care for someone through a bot.
    """
    user_id: str
    name: str

    # Training they've received (from other humans)
    training: List[str]  # ["active_listening", "trauma_informed", "conflict_de_escalation"]

    # Capacity - they're human, they have limits
    currently_supporting: int  # Max 2-3 at a time

    # Support for the supporter
    supervision_partner_id: str  # Someone who checks in on THEM

    # When they joined and last check-in
    joined_at: datetime

    max_capacity: int = 3
    last_supervision: Optional[datetime] = None

    @property
    def has_capacity(self) -> bool:
        """Can this volunteer take on another person?"""
        return self.currently_supporting < self.max_capacity

    @property
    def needs_supervision(self) -> bool:
        """Has it been more than a week since supervision check-in?"""
        if not self.last_supervision:
            return True
        days_since = (datetime.now(UTC) - self.last_supervision).days
        return days_since > 7


@dataclass
class OutreachNote:
    """Private notes from outreach volunteer

    Examples:
    - "Met for coffee. They're struggling with rent. Connected them with housing cell."
    - "They seemed suspicious at first but opened up about past co-op that failed them."
    - "Invited them to the garden workday. They seemed genuinely happy."
    - "They admitted they were paid to report on us. They're scared. I told them we'd help them find other work."
    """
    id: str
    assignment_id: str  # Which outreach assignment this belongs to
    volunteer_id: str  # Who wrote this
    timestamp: datetime
    note: str  # Free-form text

    # Optional structured data
    needs_identified: Optional[List[str]] = None  # ["housing", "employment", "community"]
    resources_connected: Optional[List[str]] = None  # ["housing_cell", "work_opportunities"]
    sentiment: Optional[str] = None  # "hopeful", "struggling", "resistant", "opening_up"


@dataclass
class OutreachAssignment:
    """Someone has been assigned to befriend a struggling member

    Detection is not condemnation. It's an invitation to care.
    """
    id: str
    flagged_user_id: str
    outreach_volunteer_id: str

    # What triggered this? NOT shared with the flagged person
    detection_reason: DetectionReason
    detection_details: Optional[str] = None  # Extra context

    # Status tracking
    status: OutreachStatus = OutreachStatus.ACTIVE
    started_at: datetime = None
    ended_at: Optional[datetime] = None

    # Notes (private, for continuity)
    notes: List[OutreachNote] = None

    # Needs assessment (learned through conversation)
    needs_assessment: Optional[dict] = None  # Structured needs data

    # Outcomes
    converted_at: Optional[datetime] = None
    conversion_story: Optional[str] = None  # Story to share (with permission)

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now(UTC)
        if self.notes is None:
            self.notes = []

    @property
    def duration_days(self) -> int:
        """How long has this outreach been active?"""
        end = self.ended_at or datetime.now(UTC)
        return (end - self.started_at).days

    @property
    def is_active(self) -> bool:
        return self.status == OutreachStatus.ACTIVE


@dataclass
class NeedsAssessment:
    """What someone needs - learned through conversation, not interrogation"""
    user_id: str
    assessed_by: str  # Volunteer who did the assessment
    assessed_at: datetime

    # Material needs
    housing_insecure: bool = False
    food_insecure: bool = False
    employment_unstable: bool = False
    healthcare_access: bool = False
    transportation_needed: bool = False

    # Care needs
    mental_health_crisis: bool = False
    substance_issues: bool = False
    disability_accommodation: bool = False
    childcare_needed: bool = False
    eldercare_needed: bool = False

    # Social/emotional needs
    isolated: bool = False
    past_trauma_with_orgs: bool = False
    trust_issues: bool = False

    # Special cases
    being_paid_to_sabotage: Optional[str] = None  # "suspected", "confirmed", None
    law_enforcement: Optional[str] = None  # "suspected", "confirmed", None

    # Resources provided (no conditions)
    resources_connected: List[str] = None

    def __post_init__(self):
        if self.resources_connected is None:
            self.resources_connected = []


@dataclass
class ConversionMetrics:
    """How are we doing at caring for everyone?

    We track, but don't obsess.
    """
    # Current state
    outreach_active: int  # People being cared for
    converted_this_month: int  # People who came around
    chose_to_leave: int  # Left on their own terms
    still_trying: int  # Haven't given up

    # The metric we care about most:
    average_time_to_first_real_conversation: Optional[float] = None  # Days
    # How quickly do people feel safe enough to be real with us?

    # Success stories (with permission)
    conversion_stories: List[str] = None

    def __post_init__(self):
        if self.conversion_stories is None:
            self.conversion_stories = []


# Conversion experiences - not lectures, not pamphlets, EXPERIENCE
CONVERSION_EXPERIENCES = [
    # Low stakes, high meaning
    "community_meal",  # Eat together
    "garden_workday",  # Work the soil together
    "skill_share",  # Learn something from someone
    "story_circle",  # Hear why people are here
    "celebration",  # Joy is contagious

    # Slightly more engagement
    "help_someone_move",  # See mutual aid in action
    "distribute_food",  # Be the one giving
    "teach_a_skill",  # Contribute their knowledge

    # Deeper understanding (only if they're curious)
    "study_circle",  # Read and discuss together
    "planning_session",  # See how decisions get made (no hierarchy)
    "conflict_mediation",  # See how we handle disagreements
]
