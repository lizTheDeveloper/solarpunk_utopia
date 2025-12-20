"""Tests for Care Outreach System - Saboteur Conversion Through Care

This isn't a security system. It's a care system.
Exclusion is failure.
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta

from app.models.care_outreach import (
    CareVolunteer,
    OutreachAssignment,
    OutreachNote,
    NeedsAssessment,
    DetectionReason,
    OutreachStatus,
    AccessLevel,
)
from app.database.care_outreach_repository import CareOutreachRepository
from app.services.care_outreach_service import CareOutreachService
from app.services.web_of_trust_service import WebOfTrustService
from app.database.vouch_repository import VouchRepository


@pytest.fixture
def db_conn():
    """Create temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    conn = sqlite3.connect(db_path)

    yield conn

    conn.close()
    os.unlink(db_path)


@pytest.fixture
def outreach_repo(db_conn):
    """Create outreach repository"""
    return CareOutreachRepository(db_conn)


@pytest.fixture
def vouch_repo(db_conn):
    """Create vouch repository"""
    return VouchRepository(db_conn)


@pytest.fixture
def care_service(outreach_repo, vouch_repo):
    """Create care outreach service"""
    trust_service = WebOfTrustService(vouch_repo)
    return CareOutreachService(outreach_repo, trust_service)


class TestVolunteerManagement:
    """Test volunteer registration and management"""

    def test_register_volunteer(self, care_service):
        """Test registering a care volunteer"""
        volunteer = care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening", "trauma_informed"],
            supervision_partner_id="volunteer_2",
            max_capacity=3,
        )

        assert volunteer.user_id == "volunteer_1"
        assert volunteer.name == "Alex"
        assert volunteer.training == ["active_listening", "trauma_informed"]
        assert volunteer.currently_supporting == 0
        assert volunteer.max_capacity == 3
        assert volunteer.has_capacity == True

    def test_find_available_volunteer(self, care_service):
        """Test finding volunteers with capacity"""
        # Register two volunteers
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )
        care_service.register_volunteer(
            user_id="volunteer_2",
            name="Sam",
            training=["trauma_informed"],
            supervision_partner_id="volunteer_1",
        )

        # Should find an available volunteer
        volunteer = care_service.find_available_volunteer()
        assert volunteer is not None
        assert volunteer.has_capacity == True


class TestOutreachAssignment:
    """Test outreach assignment creation and management"""

    def test_flag_for_outreach(self, care_service):
        """Test flagging a user for care outreach"""
        # Register a volunteer first
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )

        # Flag a user
        assignment = care_service.flag_for_outreach(
            user_id="flagged_user_1",
            reason=DetectionReason.PATTERN_FAKE_OFFERS,
            details="Repeated no-shows on offers",
        )

        assert assignment.flagged_user_id == "flagged_user_1"
        assert assignment.outreach_volunteer_id == "volunteer_1"
        assert assignment.detection_reason == DetectionReason.PATTERN_FAKE_OFFERS
        assert assignment.status == OutreachStatus.ACTIVE
        assert assignment.is_active == True

    def test_add_outreach_note(self, care_service, outreach_repo):
        """Test adding notes to outreach assignment"""
        # Register volunteer and create assignment
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )
        assignment = care_service.flag_for_outreach(
            user_id="flagged_user_1",
            reason=DetectionReason.STRUGGLING,
        )

        # Add note
        note = care_service.add_outreach_note(
            assignment_id=assignment.id,
            volunteer_id="volunteer_1",
            note_text="Met for coffee. They're struggling with rent.",
            needs_identified=["housing"],
            sentiment="opening_up",
        )

        assert note.note == "Met for coffee. They're struggling with rent."
        assert note.needs_identified == ["housing"]
        assert note.sentiment == "opening_up"

        # Verify note is attached to assignment
        retrieved = outreach_repo.get_assignment(assignment.id)
        assert len(retrieved.notes) == 1
        assert retrieved.notes[0].note == note.note

    def test_mark_converted(self, care_service, outreach_repo):
        """Test marking someone as converted"""
        # Setup
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )
        assignment = care_service.flag_for_outreach(
            user_id="flagged_user_1",
            reason=DetectionReason.VOUCH_VELOCITY,
        )

        # Mark as converted
        care_service.mark_converted(
            assignment_id=assignment.id,
            conversion_story="Was selling vouches for money. Connected them to work opportunities. Now one of our most dedicated members.",
        )

        # Verify status changed
        retrieved = outreach_repo.get_assignment(assignment.id)
        assert retrieved.status == OutreachStatus.CONVERTED
        assert retrieved.conversion_story is not None
        assert "most dedicated members" in retrieved.conversion_story


class TestNeedsAssessment:
    """Test needs assessment and resource connection"""

    def test_assess_and_provide(self, care_service):
        """Test assessing needs"""
        # Register volunteer
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )

        # Assess needs
        assessment = care_service.assess_and_provide(
            user_id="user_1",
            volunteer_id="volunteer_1",
            housing_insecure=True,
            employment_unstable=True,
            isolated=True,
        )

        assert assessment.user_id == "user_1"
        assert assessment.housing_insecure == True
        assert assessment.employment_unstable == True
        assert assessment.isolated == True


class TestAccessLevels:
    """Test access level determination"""

    def test_access_level_receiving_care(self, care_service):
        """Test that users in outreach get RECEIVING_CARE access"""
        # Register volunteer
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )

        # Flag user (creates outreach assignment)
        assignment = care_service.flag_for_outreach(
            user_id="low_trust_user",
            reason=DetectionReason.PATTERN_FAKE_OFFERS,
        )

        # Get access level
        access_level = care_service.determine_access_level("low_trust_user")

        # They're in outreach, so should get RECEIVING_CARE
        # (unless they have high trust score, which they don't in this test)
        assert access_level in [AccessLevel.RECEIVING_CARE, AccessLevel.MINIMAL_BUT_HUMAN]

    def test_access_permissions_minimal_but_human(self, care_service):
        """Test that even MINIMAL_BUT_HUMAN has basic dignity"""
        permissions = care_service.get_access_permissions(AccessLevel.MINIMAL_BUT_HUMAN)

        # Can still ask for help
        assert permissions["create_needs"] == True

        # But limited in other ways
        assert permissions["vouch_for_others"] == False
        assert permissions["become_steward"] == False

        # The point: they can still receive help and be treated with dignity


class TestSuspectedInfiltrator:
    """Test handling of suspected infiltrators"""

    def test_handle_suspected_infiltrator(self, care_service):
        """Test that infiltrators get care too"""
        # Register volunteer
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )

        # Handle suspected infiltrator
        assignment = care_service.handle_suspected_infiltrator("suspected_cop")

        assert assignment.flagged_user_id == "suspected_cop"
        assert assignment.detection_reason == DetectionReason.SUSPECTED_INFILTRATOR
        assert assignment.status == OutreachStatus.ACTIVE

        # They're still assigned a volunteer
        assert assignment.outreach_volunteer_id is not None

        # The message: "We know. We're not angry. If you ever want out, we'll help you."


class TestConversionMetrics:
    """Test metrics tracking"""

    def test_get_metrics(self, care_service):
        """Test getting conversion metrics"""
        # Setup some data
        care_service.register_volunteer(
            user_id="volunteer_1",
            name="Alex",
            training=["active_listening"],
            supervision_partner_id="volunteer_2",
        )

        # Create some assignments
        assignment1 = care_service.flag_for_outreach(
            user_id="user_1",
            reason=DetectionReason.STRUGGLING,
        )
        assignment2 = care_service.flag_for_outreach(
            user_id="user_2",
            reason=DetectionReason.PATTERN_FAKE_OFFERS,
        )

        # Mark one as converted
        care_service.mark_converted(
            assignment_id=assignment1.id,
            conversion_story="They came around!",
        )

        # Get metrics
        metrics = care_service.get_metrics()

        assert metrics.outreach_active >= 1  # user_2 still active
        assert metrics.converted_this_month >= 1  # user_1 converted
        assert metrics.conversion_stories[0] == "They came around!"


class TestConversionExperiences:
    """Test conversion experience suggestions"""

    def test_suggest_experience_for_new_outreach(self, care_service):
        """Test suggesting experiences for new people in outreach"""
        # Not in outreach - suggest low stakes
        experience = care_service.suggest_experience("new_user")
        assert experience == "community_meal"

    def test_get_all_experiences(self, care_service):
        """Test getting all conversion experiences"""
        experiences = care_service.get_all_experiences()

        # Should include low stakes experiences
        assert "community_meal" in experiences
        assert "garden_workday" in experiences

        # Should include deeper experiences
        assert "study_circle" in experiences
        assert "planning_session" in experiences


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
