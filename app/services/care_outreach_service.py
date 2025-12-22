"""Care Outreach Service - Saboteur Conversion Through Care

"The oppressor is also dehumanized." - Paulo Freire
"Love is an action, never simply a feeling." - bell hooks
"Mutual aid is a factor of evolution." - Kropotkin
"The master's tools will never dismantle the master's house." - Audre Lorde

This isn't a security system. It's a care system.
"""

import uuid
from typing import List, Optional, Tuple
from datetime import datetime, UTC

from app.models.care_outreach import (
    CareVolunteer,
    OutreachAssignment,
    OutreachNote,
    NeedsAssessment,
    ConversionMetrics,
    OutreachStatus,
    DetectionReason,
    AccessLevel,
    CONVERSION_EXPERIENCES,
)
from app.database.care_outreach_repository import CareOutreachRepository
from app.services.web_of_trust_service import WebOfTrustService


class CareOutreachService:
    """Service for managing care-based outreach to struggling members"""

    def __init__(
        self,
        outreach_repo: CareOutreachRepository,
        trust_service: WebOfTrustService
    ):
        self.outreach_repo = outreach_repo
        self.trust_service = trust_service

    # --- Volunteer Management ---

    def register_volunteer(
        self,
        user_id: str,
        name: str,
        training: List[str],
        supervision_partner_id: str,
        max_capacity: int = 3
    ) -> CareVolunteer:
        """Register a new care volunteer

        Args:
            user_id: User who wants to volunteer
            name: Their name
            training: List of training they've received
            supervision_partner_id: Another volunteer who will support them
            max_capacity: Max number of people they can support (default 3)

        Returns:
            CareVolunteer
        """
        volunteer = CareVolunteer(
            user_id=user_id,
            name=name,
            training=training,
            currently_supporting=0,
            max_capacity=max_capacity,
            supervision_partner_id=supervision_partner_id,
            joined_at=datetime.now(UTC),
        )

        return self.outreach_repo.add_volunteer(volunteer)

    def find_available_volunteer(self) -> Optional[CareVolunteer]:
        """Find a volunteer with capacity

        Returns:
            CareVolunteer with lowest current load, or None if all at capacity
        """
        available = self.outreach_repo.get_available_volunteers()
        if not available:
            return None

        # Return volunteer with lowest current load
        return available[0]

    # --- Outreach Assignment ---

    def flag_for_outreach(
        self,
        user_id: str,
        reason: DetectionReason,
        details: Optional[str] = None
    ) -> OutreachAssignment:
        """Flag a user for care outreach

        Detection is not condemnation. It's an invitation to care.

        Args:
            user_id: User who triggered detection
            reason: Why they were flagged
            details: Additional context

        Returns:
            OutreachAssignment
        """
        # Check if already has active outreach
        existing = self.outreach_repo.get_assignment_for_user(user_id)
        if existing and existing.is_active:
            return existing

        # Find available volunteer
        volunteer = self.find_available_volunteer()
        if not volunteer:
            raise ValueError("No volunteers available. Need more care volunteers!")

        # Create assignment
        assignment = OutreachAssignment(
            id=str(uuid.uuid4()),
            flagged_user_id=user_id,
            outreach_volunteer_id=volunteer.user_id,
            detection_reason=reason,
            detection_details=details,
            status=OutreachStatus.ACTIVE,
            started_at=datetime.now(UTC),
        )

        return self.outreach_repo.create_assignment(assignment)

    def add_outreach_note(
        self,
        assignment_id: str,
        volunteer_id: str,
        note_text: str,
        needs_identified: Optional[List[str]] = None,
        resources_connected: Optional[List[str]] = None,
        sentiment: Optional[str] = None
    ) -> OutreachNote:
        """Add a note to an outreach assignment

        Args:
            assignment_id: Assignment to add note to
            volunteer_id: Volunteer writing the note
            note_text: The note content
            needs_identified: List of needs discovered
            resources_connected: Resources provided
            sentiment: How the person seems ("hopeful", "struggling", etc.)

        Returns:
            OutreachNote
        """
        note = OutreachNote(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            volunteer_id=volunteer_id,
            timestamp=datetime.now(UTC),
            note=note_text,
            needs_identified=needs_identified,
            resources_connected=resources_connected,
            sentiment=sentiment,
        )

        return self.outreach_repo.add_note(note)

    def mark_converted(
        self,
        assignment_id: str,
        conversion_story: Optional[str] = None
    ):
        """Mark someone as having converted / come around

        Args:
            assignment_id: Assignment to mark as converted
            conversion_story: Optional story to share (with permission)
        """
        self.outreach_repo.update_assignment_status(
            assignment_id,
            OutreachStatus.CONVERTED,
            conversion_story
        )

    def mark_chose_to_leave(self, assignment_id: str):
        """Mark someone as having chosen to leave

        They left on their own terms. Door is always open.
        """
        self.outreach_repo.update_assignment_status(
            assignment_id,
            OutreachStatus.CHOSE_TO_LEAVE
        )

    # --- Needs Assessment ---

    def assess_and_provide(
        self,
        user_id: str,
        volunteer_id: str,
        **needs
    ) -> NeedsAssessment:
        """Assess needs and connect to resources

        Through conversation (not interrogation), learn what they need
        and connect them WITHOUT requiring "good behavior"

        Args:
            user_id: Person being assessed
            volunteer_id: Volunteer doing assessment
            **needs: Keyword args for need flags

        Returns:
            NeedsAssessment
        """
        assessment = NeedsAssessment(
            user_id=user_id,
            assessed_by=volunteer_id,
            assessed_at=datetime.now(UTC),
            **needs
        )

        # Save assessment
        self.outreach_repo.save_needs_assessment(assessment)

        # Connect to resources based on needs
        self._connect_to_resources(assessment)

        return assessment

    def _connect_to_resources(self, assessment: NeedsAssessment):
        """Connect user to resources based on needs assessment

        Creates need listings in the ValueFlows system so the community
        can respond with offers.

        Args:
            assessment: The completed needs assessment
        """
        import uuid
        from pathlib import Path
        import sqlite3
        import sys

        # Import VF components
        from valueflows_node.app.models.vf.listing import Listing, ListingType
        from valueflows_node.app.models.vf.resource_spec import ResourceCategory
        from valueflows_node.app.repositories.vf.listing_repo import ListingRepository
        from valueflows_node.app.repositories.vf.resource_spec_repo import ResourceSpecRepository

        # Connect to ValueFlows database
        vf_db_path = str(Path(__file__).parent.parent.parent / "valueflows_node" / "app" / "database" / "valueflows.db")
        conn = sqlite3.connect(vf_db_path)
        conn.row_factory = sqlite3.Row

        try:
            listing_repo = ListingRepository(conn)
            resource_spec_repo = ResourceSpecRepository(conn)
            resources_connected = []

            # Create needs based on assessment
            if assessment.housing_insecure:
                # Find or create housing resource spec
                specs = resource_spec_repo.find_by_category(ResourceCategory.HOUSING)
                if specs:
                    spec_id = specs[0].id
                else:
                    # Use a generic ID - in production, ensure resource specs exist
                    spec_id = "housing-general"

                listing = Listing(
                    id=str(uuid.uuid4()),
                    listing_type=ListingType.NEED,
                    resource_spec_id=spec_id,
                    agent_id=assessment.user_id,
                    anonymous=True,  # Privacy for vulnerable users
                    location_id=None,
                    quantity=1.0,
                    unit="unit",
                    title="Need: Safe Housing",
                    description="Looking for safe, stable housing. Connected through care outreach.",
                    status="active"
                )
                listing_repo.create(listing)
                resources_connected.append("housing")

            if assessment.food_insecure:
                specs = resource_spec_repo.find_by_category(ResourceCategory.FOOD)
                spec_id = specs[0].id if specs else "food-general"

                listing = Listing(
                    id=str(uuid.uuid4()),
                    listing_type=ListingType.NEED,
                    resource_spec_id=spec_id,
                    agent_id=assessment.user_id,
                    anonymous=True,
                    location_id=None,
                    quantity=1.0,
                    unit="unit",
                    title="Need: Food Access",
                    description="Need access to food. Connected through care outreach.",
                    status="active"
                )
                listing_repo.create(listing)
                resources_connected.append("food")

            if assessment.employment_unstable:
                specs = resource_spec_repo.find_by_category(ResourceCategory.LABOR)
                spec_id = specs[0].id if specs else "work-general"

                listing = Listing(
                    id=str(uuid.uuid4()),
                    listing_type=ListingType.NEED,
                    resource_spec_id=spec_id,
                    agent_id=assessment.user_id,
                    anonymous=True,
                    location_id=None,
                    quantity=1.0,
                    unit="unit",
                    title="Need: Work Opportunity",
                    description="Looking for work or income opportunities. Connected through care outreach.",
                    status="active"
                )
                listing_repo.create(listing)
                resources_connected.append("work")

            if assessment.healthcare_access:
                listing = Listing(
                    id=str(uuid.uuid4()),
                    listing_type=ListingType.NEED,
                    resource_spec_id="healthcare-general",
                    agent_id=assessment.user_id,
                    anonymous=True,
                    location_id=None,
                    quantity=1.0,
                    unit="unit",
                    title="Need: Healthcare Access",
                    description="Need healthcare access or support. Connected through care outreach.",
                    status="active"
                )
                listing_repo.create(listing)
                resources_connected.append("healthcare")

            if assessment.isolated:
                # Create need for community connection
                listing = Listing(
                    id=str(uuid.uuid4()),
                    listing_type=ListingType.NEED,
                    resource_spec_id="community-connection",
                    agent_id=assessment.user_id,
                    anonymous=True,
                    location_id=None,
                    quantity=1.0,
                    unit="unit",
                    title="Need: Community Connection",
                    description="Looking to connect with local community. Connected through care outreach.",
                    status="active"
                )
                listing_repo.create(listing)
                resources_connected.append("community")

            # Update assessment with resources connected
            assessment.resources_connected = resources_connected
            self.outreach_repo.save_needs_assessment(assessment)

            conn.commit()
        finally:
            conn.close()

    # --- Access Level Determination ---

    def determine_access_level(self, user_id: str) -> AccessLevel:
        """Determine access level based on trust and outreach status

        Access based on trust, but never zero.

        Returns:
            AccessLevel
        """
        # Get trust score
        trust_score = self.trust_service.compute_trust_score(user_id)
        trust = trust_score.computed_trust

        # Get outreach status
        assignment = self.outreach_repo.get_assignment_for_user(user_id)
        outreach_status = assignment.status if assignment else None

        if trust >= 0.7:
            return AccessLevel.FULL

        elif trust >= 0.3:
            return AccessLevel.STANDARD

        elif outreach_status == OutreachStatus.ACTIVE:
            # They're being cared for. Give them basics.
            return AccessLevel.RECEIVING_CARE

        else:
            # Very low trust, not in outreach
            # They can still:
            # - Receive help if they ask
            # - Attend public events
            # - Be treated with dignity
            return AccessLevel.MINIMAL_BUT_HUMAN

    def get_access_permissions(self, access_level: AccessLevel) -> dict:
        """Get what permissions each access level has

        Returns:
            Dict of permission flags
        """
        if access_level == AccessLevel.FULL:
            return {
                "create_offers": True,
                "create_needs": True,
                "vouch_for_others": True,
                "join_cells": True,
                "become_steward": True,
                "access_sanctuary": True,
                "rapid_response": True,
            }

        elif access_level == AccessLevel.STANDARD:
            return {
                "create_offers": True,
                "create_needs": True,
                "vouch_for_others": False,  # Need higher trust
                "join_cells": True,
                "become_steward": False,
                "access_sanctuary": False,
                "rapid_response": False,
            }

        elif access_level == AccessLevel.RECEIVING_CARE:
            return {
                "create_offers": True,  # Can still contribute
                "create_needs": True,  # Can still ask for help
                "vouch_for_others": False,
                "join_cells": True,  # Can join community
                "become_steward": False,
                "access_sanctuary": False,
                "rapid_response": False,
            }

        else:  # MINIMAL_BUT_HUMAN
            return {
                "create_offers": False,
                "create_needs": True,  # Can still ask for help
                "vouch_for_others": False,
                "join_cells": False,
                "become_steward": False,
                "access_sanctuary": False,
                "rapid_response": False,
            }

    # --- Special Case: Suspected Infiltrator ---

    def handle_suspected_infiltrator(self, user_id: str) -> OutreachAssignment:
        """Handle suspected law enforcement / paid informant

        They might be a cop. But they're also a person.

        Process:
        1. Protect the network (limit access)
        2. Reach out anyway
        3. The message (through relationship, not explicit):
           "We know. We're not angry. You're doing a job.
            But you're also a person with a life outside that job.
            If you ever want out, we'll help you."

        Args:
            user_id: Suspected infiltrator

        Returns:
            OutreachAssignment
        """
        # Create outreach assignment
        assignment = self.flag_for_outreach(
            user_id,
            DetectionReason.SUSPECTED_INFILTRATOR,
            details="Flagged by fraud detection. Limiting sensitive access while reaching out."
        )

        # Access level will be MINIMAL_BUT_HUMAN or RECEIVING_CARE
        # which automatically limits sensitive operations

        return assignment

    # --- Metrics ---

    def get_metrics(self) -> ConversionMetrics:
        """Get conversion metrics

        How are we doing at caring for everyone?
        """
        return self.outreach_repo.get_conversion_metrics()

    # --- Suggested Experiences ---

    def suggest_experience(self, user_id: str) -> str:
        """Suggest a conversion experience for someone

        Not lectures. Not pamphlets. Experience.
        Let them feel it, not hear about it.

        Args:
            user_id: User to suggest experience for

        Returns:
            Experience name
        """
        # Get their current state
        assignment = self.outreach_repo.get_assignment_for_user(user_id)

        if not assignment:
            # Not in outreach - start with low stakes
            return "community_meal"

        # Count notes to see how long they've been in outreach
        duration = assignment.duration_days

        if duration < 7:
            # First week - low stakes, high meaning
            return "garden_workday"  # or community_meal, celebration

        elif duration < 30:
            # First month - slightly more engagement
            return "help_someone_move"  # or distribute_food, teach_a_skill

        else:
            # After a month - deeper understanding (if they're curious)
            return "study_circle"  # or planning_session

    def get_all_experiences(self) -> List[str]:
        """Get list of all conversion experiences"""
        return CONVERSION_EXPERIENCES
