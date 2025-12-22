"""
End-to-End tests for Care Outreach Conversion Flow.

Tests the complete flow from detection through conversion.

"Saboteurs" are often people in crisis. Exclusion is failure. This is a care system.

Based on adrienne maree brown's "Emergent Strategy" - "There is such urgency in the
multitude of crises we face, it can make it hard to remember that in fact it is
urgency thinking (urgent constant unsustainable growth) that got us to this point."
"""

import pytest
import pytest_asyncio
import os
import tempfile
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.models.care_outreach import (
    DetectionReason,
    OutreachStatus,
    AccessLevel,
)
from app.database.care_outreach_repository import CareOutreachRepository
from app.services.care_outreach_service import CareOutreachService
from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService


class TestCareOutreachE2E:
    """End-to-end care outreach conversion flow tests"""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Set up test database and services"""
        # Setup
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")

        # Run migrations
        import aiosqlite
        import os
        # Find project root (where both valueflows_node and app directories exist)
        test_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(test_file_dir)))

        async with aiosqlite.connect(self.db_path) as db:
            # Load base schema first (has users table and other dependencies)
            vf_schema_path = os.path.join(project_root, "valueflows_node", "app", "database", "vf_schema.sql")
            with open(vf_schema_path) as f:
                base_schema = f.read()
            await db.executescript(base_schema)
            await db.commit()

            # Care outreach migration
            care_migration_path = os.path.join(project_root, "app", "database", "migrations", "017_add_care_outreach.sql")
            with open(care_migration_path) as f:
                migration_sql = f.read()
            await db.executescript(migration_sql)
            await db.commit()

        # Create repositories and services
        import sqlite3
        self.sync_conn = sqlite3.connect(self.db_path)
        self.outreach_repo = CareOutreachRepository(self.sync_conn)
        self.vouch_repo = VouchRepository(self.db_path)  # VouchRepository expects path, not connection
        self.trust_service = WebOfTrustService(self.vouch_repo)
        self.service = CareOutreachService(self.outreach_repo, self.trust_service)

        yield  # Run the test

        # Teardown
        self.sync_conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    @pytest.mark.asyncio
    async def test_full_conversion_flow_isolated_member(self):
        """
        E2E test: Detection → assignment → outreach → conversion

        Scenario from proposal:
        - Bob flagged as isolated (no exchanges in 30 days)
        - Volunteer Carol assigned
        - Carol sees Bob's needs assessment
        - Carol connects Bob with resources
        - Bob re-engages (creates offer or need)
        - Bob marked "converted"
        - Conversion metrics updated
        """

        # Step 1: Register care volunteer
        carol = self.service.register_volunteer(
            user_id="carol",
            name="Carol",
            training=["active_listening", "trauma_informed", "mutual_aid"],
            supervision_partner_id="supervisor_1",
            max_capacity=5,
        )

        assert carol.user_id == "carol"
        assert carol.has_capacity == True
        assert carol.max_capacity == 5

        # Step 2: System flags Bob as isolated (30 days no activity)
        assignment = self.service.flag_for_outreach(
            user_id="bob",
            reason=DetectionReason.STRUGGLING,
            details="No exchanges in 30 days, last logged in 25 days ago",
        )

        assert assignment.flagged_user_id == "bob"
        assert assignment.outreach_volunteer_id == "carol"
        assert assignment.detection_reason == DetectionReason.STRUGGLING
        assert assignment.status == OutreachStatus.ACTIVE

        # Step 3: Carol views Bob's assignment and does needs assessment
        assessment = self.service.assess_and_provide(
            user_id="bob",
            volunteer_id="carol",
            housing_insecure=True,
            employment_unstable=False,
            isolated=True,
            food_insecure=False,
            mental_health_crisis=False,
            substance_issues=False,
            disability_accommodation=False,
            childcare_needed=False,
            eldercare_needed=False,
            transportation_needed=True,
        )

        assert assessment.user_id == "bob"
        assert assessment.housing_insecure == True
        assert assessment.isolated == True
        assert assessment.transportation_needed == True

        # Step 4: Carol adds outreach notes
        note1 = self.service.add_outreach_note(
            assignment_id=assignment.id,
            volunteer_id="carol",
            note_text="Met Bob for coffee. He's been overwhelmed - recently evicted, couch surfing.",
            needs_identified=["housing", "transportation"],
            sentiment="resistant",
        )

        assert note1.needs_identified == ["housing", "transportation"]
        assert note1.sentiment == "resistant"

        # Step 5: Carol connects Bob with resources (7 days later)
        with freeze_time(assignment.created_at + timedelta(days=7)):
            note2 = self.service.add_outreach_note(
                assignment_id=assignment.id,
                volunteer_id="carol",
                note_text="Connected Bob with Sarah who has a spare room. He's moving in next week!",
                needs_identified=["housing"],
                sentiment="opening_up",
            )

            assert note2.sentiment == "opening_up"

        # Step 6: Bob re-engages (14 days later) - creates an offer
        with freeze_time(assignment.created_at + timedelta(days=14)):
            note3 = self.service.add_outreach_note(
                assignment_id=assignment.id,
                volunteer_id="carol",
                note_text="Bob just posted his first offer - offering computer repair skills! He's housed and feeling more stable.",
                needs_identified=[],
                sentiment="engaged",
            )

            assert note3.sentiment == "engaged"

        # Step 7: Carol marks Bob as converted (celebration, not surveillance)
        with freeze_time(assignment.created_at + timedelta(days=16)):
            self.service.mark_converted(
                assignment_id=assignment.id,
                conversion_story=(
                    "Bob was isolated after eviction. Connected him with housing through "
                    "Sarah. Once stable, he started contributing computer repair skills. "
                    "Now one of our most active members in the tech mutual aid group."
                ),
            )

            # Verify conversion
            updated = self.outreach_repo.get_assignment(assignment.id)
            assert updated.status == OutreachStatus.CONVERTED
            assert updated.converted_at is not None
            assert "most active members" in updated.conversion_story

        # Step 8: Verify conversion metrics updated
        metrics = self.service.get_metrics()
        assert metrics.converted_this_month >= 1
        assert len(metrics.conversion_stories) >= 1
        assert any("Bob" in story or "computer repair" in story for story in metrics.conversion_stories)

    @pytest.mark.asyncio
    async def test_suspected_infiltrator_receives_care(self):
        """
        Even suspected infiltrators receive care, not exclusion.

        Scenario:
        - System flags Mallory as suspected infiltrator
        - Volunteer assigned (not security response)
        - Outreach proceeds with awareness
        - Message: "We know. We're not angry. If you ever want out, we'll help you."
        """

        # Register volunteer
        self.service.register_volunteer(
            user_id="dave",
            name="Dave",
            training=["active_listening", "de_escalation"],
            supervision_partner_id="supervisor_1",
        )

        # Flag suspected infiltrator
        assignment = self.service.handle_suspected_infiltrator("mallory")

        assert assignment.flagged_user_id == "mallory"
        assert assignment.detection_reason == DetectionReason.SUSPECTED_INFILTRATOR
        assert assignment.outreach_volunteer_id == "dave"
        assert assignment.status == OutreachStatus.ACTIVE

        # Volunteer adds note with awareness
        note = self.service.add_outreach_note(
            assignment_id=assignment.id,
            volunteer_id="dave",
            note_text=(
                "Met Mallory. Kept it light - talked about community gardens. "
                "They seemed uncomfortable but stayed. Door is open if they ever want to talk."
            ),
            needs_identified=[],
            sentiment="guarded",
        )

        assert note.sentiment == "guarded"

        # The point: We don't exclude. We offer a door out.

    @pytest.mark.asyncio
    async def test_access_level_receiving_care(self):
        """
        Users in outreach get RECEIVING_CARE access - limited but dignified.

        Scenario:
        - User flagged for fake offer pattern
        - Gets RECEIVING_CARE access level
        - Can still create needs (ask for help)
        - Cannot vouch for others or become steward
        - After conversion, access restored
        """

        # Register volunteer
        self.service.register_volunteer(
            user_id="eve",
            name="Eve",
            training=["active_listening"],
            supervision_partner_id="supervisor_1",
        )

        # Flag user for fake offers
        assignment = self.service.flag_for_outreach(
            user_id="frank",
            reason=DetectionReason.PATTERN_FAKE_OFFERS,
            details="3 no-shows on offered items",
        )

        # Check access level
        access_level = self.service.determine_access_level("frank")
        assert access_level in [AccessLevel.RECEIVING_CARE, AccessLevel.MINIMAL_BUT_HUMAN]

        # Check permissions
        permissions = self.service.get_access_permissions(access_level)

        # Can still ask for help (dignity)
        assert permissions["create_needs"] == True

        # Limited in other ways
        assert permissions["vouch_for_others"] == False
        assert permissions["become_steward"] == False

        # After conversion
        self.service.mark_converted(
            assignment_id=assignment.id,
            conversion_story="Frank was overwhelmed - connected him with support. Now reliable.",
        )

        # Access level should improve (in real system, would check trust score)
        updated_assignment = self.outreach_repo.get_assignment(assignment.id)
        assert updated_assignment.status == OutreachStatus.CONVERTED

    @pytest.mark.asyncio
    async def test_volunteer_capacity_management(self):
        """
        Volunteers have capacity limits to prevent burnout.

        Scenario:
        - Volunteer has max_capacity of 2
        - Gets 2 assignments
        - 3rd assignment goes to different volunteer
        - After conversion, capacity freed up
        """

        # Register volunteer with limited capacity
        grace = self.service.register_volunteer(
            user_id="grace",
            name="Grace",
            training=["active_listening"],
            supervision_partner_id="supervisor_1",
            max_capacity=2,
        )

        assert grace.max_capacity == 2
        assert grace.currently_supporting == 0
        assert grace.has_capacity == True

        # First assignment
        assignment1 = self.service.flag_for_outreach(
            user_id="user1",
            reason=DetectionReason.STRUGGLING,
        )
        assert assignment1.outreach_volunteer_id == "grace"

        # Second assignment
        assignment2 = self.service.flag_for_outreach(
            user_id="user2",
            reason=DetectionReason.STRUGGLING,
        )
        assert assignment2.outreach_volunteer_id == "grace"

        # Grace now at capacity
        grace_updated = self.outreach_repo.get_volunteer("grace")
        assert grace_updated.currently_supporting == 2
        assert grace_updated.has_capacity == False

        # Register second volunteer for overflow
        self.service.register_volunteer(
            user_id="hank",
            name="Hank",
            training=["active_listening"],
            supervision_partner_id="supervisor_1",
        )

        # Third assignment goes to Hank
        assignment3 = self.service.flag_for_outreach(
            user_id="user3",
            reason=DetectionReason.STRUGGLING,
        )
        assert assignment3.outreach_volunteer_id == "hank"

        # Mark first assignment as converted - frees Grace's capacity
        self.service.mark_converted(
            assignment_id=assignment1.id,
            conversion_story="Converted!",
        )

        grace_final = self.outreach_repo.get_volunteer("grace")
        assert grace_final.currently_supporting == 1
        assert grace_final.has_capacity == True

    @pytest.mark.asyncio
    async def test_conversion_experiences_progression(self):
        """
        Suggest low-stakes experiences first, then deeper engagement.

        Scenario:
        - New person: suggest community meal
        - After engagement: suggest garden workday
        - After trust builds: suggest study circle
        """

        # New user not in outreach - suggest low stakes
        experience = self.service.suggest_experience("new_user")
        assert experience == "community_meal"

        # Get all available experiences
        experiences = self.service.get_all_experiences()
        assert "community_meal" in experiences
        assert "garden_workday" in experiences
        assert "study_circle" in experiences
        assert "planning_session" in experiences

    @pytest.mark.asyncio
    async def test_needs_assessment_comprehensive(self):
        """
        Comprehensive needs assessment covers many dimensions.

        Scenario:
        - Assess user with multiple needs
        - All dimensions captured
        - Volunteer can see full picture
        """

        # Register volunteer
        self.service.register_volunteer(
            user_id="iris",
            name="Iris",
            training=["social_work_background"],
            supervision_partner_id="supervisor_1",
        )

        # Comprehensive assessment
        assessment = self.service.assess_and_provide(
            user_id="jack",
            volunteer_id="iris",
            housing_insecure=True,
            employment_unstable=True,
            isolated=True,
            food_insecure=True,
            mental_health_crisis=False,
            substance_issues=False,
            disability_accommodation=True,
            childcare_needed=True,
            eldercare_needed=False,
            transportation_needed=True,
        )

        # Verify all dimensions captured
        assert assessment.housing_insecure == True
        assert assessment.employment_unstable == True
        assert assessment.isolated == True
        assert assessment.food_insecure == True
        assert assessment.disability_accommodation == True
        assert assessment.childcare_needed == True
        assert assessment.transportation_needed == True
        assert assessment.mental_health_crisis == False

    @pytest.mark.asyncio
    async def test_supervision_partnership(self):
        """
        Volunteers have supervision partners for support.

        Scenario:
        - Volunteer registered with supervision partner
        - Can process difficult cases together
        - Prevents burnout and secondary trauma
        """

        # Register two volunteers as supervision partners
        alice_volunteer = self.service.register_volunteer(
            user_id="alice_v",
            name="Alice",
            training=["active_listening", "trauma_informed"],
            supervision_partner_id="bob_v",
        )

        bob_volunteer = self.service.register_volunteer(
            user_id="bob_v",
            name="Bob",
            training=["active_listening", "de_escalation"],
            supervision_partner_id="alice_v",
        )

        # Verify partnership
        assert alice_volunteer.supervision_partner_id == "bob_v"
        assert bob_volunteer.supervision_partner_id == "alice_v"

    @pytest.mark.asyncio
    async def test_metrics_track_success_not_surveillance(self):
        """
        Metrics celebrate success, not track failures.

        Scenario:
        - Track conversions (celebration)
        - Track conversion stories (learning)
        - Do NOT track: who's "most difficult", "failure rate"
        """

        # Setup
        self.service.register_volunteer(
            user_id="volunteer",
            name="Volunteer",
            training=["active_listening"],
            supervision_partner_id="supervisor",
        )

        # Create assignments
        assignment1 = self.service.flag_for_outreach(
            user_id="user1",
            reason=DetectionReason.STRUGGLING,
        )

        assignment2 = self.service.flag_for_outreach(
            user_id="user2",
            reason=DetectionReason.PATTERN_FAKE_OFFERS,
        )

        # Convert one
        self.service.mark_converted(
            assignment_id=assignment1.id,
            conversion_story="Amazing transformation - from isolated to community organizer!",
        )

        # Get metrics
        metrics = self.service.get_metrics()

        # Positive metrics
        assert metrics.outreach_active >= 1  # user2 still active
        assert metrics.converted_this_month >= 1  # user1 converted
        assert len(metrics.conversion_stories) >= 1

        # NO negative surveillance metrics
        assert not hasattr(metrics, "failure_rate")
        assert not hasattr(metrics, "most_difficult_users")
        assert not hasattr(metrics, "time_to_conversion_by_user")

    @pytest.mark.asyncio
    async def test_not_converted_not_failure(self):
        """
        CRITICAL: Not converting is NOT failure. Some people need time.

        Scenario:
        - User in outreach for months
        - Never fully engages
        - Assignment remains ACTIVE (not "failed")
        - Door remains open
        """

        # Register volunteer
        self.service.register_volunteer(
            user_id="volunteer",
            name="Volunteer",
            training=["active_listening"],
            supervision_partner_id="supervisor",
        )

        # Flag user
        assignment = self.service.flag_for_outreach(
            user_id="slow_user",
            reason=DetectionReason.STRUGGLING,
        )

        # Many months pass
        with freeze_time(assignment.created_at + timedelta(days=180)):
            # Add note - still engaged but slow
            self.service.add_outreach_note(
                assignment_id=assignment.id,
                volunteer_id="volunteer",
                note_text="Still checking in monthly. They appreciate it but aren't ready to engage more.",
                needs_identified=["time", "trust"],
                sentiment="cautious",
            )

            # Status is still ACTIVE (not "failed")
            updated = self.outreach_repo.get_assignment(assignment.id)
            assert updated.status == OutreachStatus.ACTIVE

            # No "failure" status exists
            # The door remains open


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
