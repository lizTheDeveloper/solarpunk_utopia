"""Tests for Multi-Steward Sanctuary Verification (GAP-109)

Ensures sanctuary resources require 2+ independent steward verifications
before becoming available for matching.
"""
import pytest
from datetime import datetime, timedelta, UTC
import uuid

from app.models.sanctuary import (
    SanctuaryResource,
    SanctuaryResourceType,
    SensitivityLevel,
    VerificationStatus,
    VerificationMethod,
    VerificationRecord,
    SanctuaryVerification,
    SanctuaryUse,
    MIN_SANCTUARY_VERIFICATIONS,
    VERIFICATION_VALIDITY_DAYS,
)
from app.services.sanctuary_service import SanctuaryService
from app.database.sanctuary_repository import SanctuaryRepository


@pytest.fixture
def sanctuary_service(tmp_path):
    """Create a sanctuary service with temporary database."""
    db_path = str(tmp_path / "test_sanctuary.db")
    return SanctuaryService(db_path=db_path)


@pytest.fixture
def sample_resource(sanctuary_service):
    """Create a sample sanctuary resource."""
    return sanctuary_service.offer_resource(
        user_id="user-maria",
        cell_id="cell-001",
        resource_type=SanctuaryResourceType.SAFE_SPACE,
        description="Phoenix safe space, 2 people, 1 week max",
        capacity=2,
        duration_days=7
    )


class TestSingleStewardVerificationNotEnough:
    """Resource needs 2 stewards to verify"""

    def test_single_verification_keeps_status_pending(self, sanctuary_service, sample_resource):
        """Resource with only 1 verification stays PENDING."""
        # First steward verifies
        result = sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON,
            escape_routes_verified=True,
            capacity_verified=True,
            buddy_protocol_available=True
        )

        assert result['verification_count'] == 1
        assert result['status'] == 'pending'
        assert result['needs_second_verification'] is True
        assert "Needs 1 more steward" in result['message']

    def test_single_verification_not_available_for_matching(self, sanctuary_service, sample_resource):
        """Resource with only 1 verification should not appear in matches."""
        # First steward verifies
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON,
            escape_routes_verified=True,
            capacity_verified=True
        )

        # Get available resources (verified_only=True by default)
        resources = sanctuary_service.get_available_resources(
            cell_id="cell-001",
            user_trust_score=0.9  # High trust user
        )

        # Resource should NOT appear in results
        resource_ids = [r.id for r in resources]
        assert sample_resource.id not in resource_ids


class TestTwoStewardVerificationSucceeds:
    """Resource verified after 2 stewards approve"""

    def test_two_stewards_changes_status_to_verified(self, sanctuary_service, sample_resource):
        """Resource becomes VERIFIED after 2 steward verifications."""
        # First steward verifies
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON,
            escape_routes_verified=True,
            capacity_verified=True
        )

        # Second steward verifies
        result = sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.VIDEO_CALL,
            escape_routes_verified=True,
            capacity_verified=True
        )

        assert result['verification_count'] == 2
        assert result['status'] == 'verified'
        assert result['needs_second_verification'] is False
        assert "verified and available" in result['message'].lower()

    def test_two_stewards_makes_resource_available(self, sanctuary_service, sample_resource):
        """Resource appears in matches after 2 verifications."""
        # Two stewards verify
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Get available resources
        resources = sanctuary_service.get_available_resources(
            cell_id="cell-001",
            user_trust_score=0.9
        )

        # Resource should NOW appear in results
        resource_ids = [r.id for r in resources]
        assert sample_resource.id in resource_ids

    def test_verification_metadata_updated(self, sanctuary_service, sample_resource):
        """Verification sets first_verified_at, last_check, expires_at."""
        before = datetime.now(UTC)

        # Two stewards verify
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        after = datetime.now(UTC)

        # Check verification status
        verification = sanctuary_service.get_verification_status(sample_resource.id)

        assert verification is not None
        assert verification.first_verified_at >= before
        assert verification.last_check >= before
        assert verification.expires_at is not None
        # Expires 90 days from now
        expected_expiry = verification.last_check + timedelta(days=VERIFICATION_VALIDITY_DAYS)
        assert abs((verification.expires_at - expected_expiry).total_seconds()) < 2  # Within 2 seconds


class TestSameStewardCannotVerifyTwice:
    """Prevent single steward from verifying alone"""

    def test_same_steward_rejected(self, sanctuary_service, sample_resource):
        """Same steward cannot verify twice."""
        # First verification
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Second verification by same steward should fail
        with pytest.raises(ValueError, match="Different steward required"):
            sanctuary_service.add_verification(
                resource_id=sample_resource.id,
                steward_id="steward-alice",  # Same steward!
                verification_method=VerificationMethod.VIDEO_CALL
            )


class TestResourcesNeedingVerification:
    """Get list of resources needing verification"""

    def test_pending_verification_list(self, sanctuary_service):
        """Resources with 1 verification appear in pending list."""
        # Create resource
        resource = sanctuary_service.offer_resource(
            user_id="user-maria",
            cell_id="cell-001",
            resource_type=SanctuaryResourceType.SAFE_SPACE,
            description="Test space",
            capacity=2
        )

        # First steward verifies
        sanctuary_service.add_verification(
            resource_id=resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Get resources needing verification (exclude Alice)
        result = sanctuary_service.get_resources_needing_verification(
            cell_id="cell-001",
            steward_id="steward-bob"  # Bob hasn't verified yet
        )

        # Resource should appear in pending list
        pending_ids = [r.id for r in result['pending_verification']]
        assert resource.id in pending_ids

    def test_pending_excludes_steward_who_verified(self, sanctuary_service):
        """Steward who verified doesn't see resource in their pending list."""
        # Create resource
        resource = sanctuary_service.offer_resource(
            user_id="user-maria",
            cell_id="cell-001",
            resource_type=SanctuaryResourceType.SAFE_SPACE,
            description="Test space",
            capacity=2
        )

        # Alice verifies
        sanctuary_service.add_verification(
            resource_id=resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Get pending for Alice
        result = sanctuary_service.get_resources_needing_verification(
            cell_id="cell-001",
            steward_id="steward-alice"  # Alice asking
        )

        # Resource should NOT appear (Alice already verified)
        pending_ids = [r.id for r in result['pending_verification']]
        assert resource.id not in pending_ids


class TestSuccessfulUsesTracking:
    """Track successful sanctuary uses for quality filtering"""

    def test_record_successful_use(self, sanctuary_service, sample_resource):
        """Recording successful use increments counter."""
        # Verify resource first
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Record successful use
        sanctuary_service.record_sanctuary_use(
            resource_id=sample_resource.id,
            request_id="request-001",
            outcome="success"
        )

        # Check successful_uses counter
        verification = sanctuary_service.get_verification_status(sample_resource.id)
        assert verification.successful_uses == 1

    def test_failed_use_does_not_increment(self, sanctuary_service, sample_resource):
        """Failed outcomes don't count as successful uses."""
        # Verify resource
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Record failed use
        sanctuary_service.record_sanctuary_use(
            resource_id=sample_resource.id,
            request_id="request-001",
            outcome="failed"
        )

        # Check successful_uses counter (should still be 0)
        verification = sanctuary_service.get_verification_status(sample_resource.id)
        assert verification.successful_uses == 0

    def test_multiple_successful_uses(self, sanctuary_service, sample_resource):
        """Multiple successful uses increment counter."""
        # Verify resource
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Record 3 successful uses
        for i in range(3):
            sanctuary_service.record_sanctuary_use(
                resource_id=sample_resource.id,
                request_id=f"request-{i}",
                outcome="success"
            )

        # Check counter
        verification = sanctuary_service.get_verification_status(sample_resource.id)
        assert verification.successful_uses == 3


class TestCriticalNeedsFilteringExcluded:
    """Critical needs only match to proven sanctuaries"""

    def test_new_sanctuary_not_high_trust(self, sanctuary_service, sample_resource):
        """New sanctuary with 0 uses is not high-trust."""
        # Verify resource (but no uses yet)
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Get high-trust resources
        high_trust = sanctuary_service.get_high_trust_resources(
            cell_id="cell-001",
            resource_type=SanctuaryResourceType.SAFE_SPACE
        )

        # New resource should NOT appear (needs 3+ successful uses)
        resource_ids = [r.id for r in high_trust]
        assert sample_resource.id not in resource_ids

    def test_proven_sanctuary_is_high_trust(self, sanctuary_service, sample_resource):
        """Sanctuary with 3+ successful uses is high-trust."""
        # Verify resource
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-alice",
            verification_method=VerificationMethod.IN_PERSON
        )
        sanctuary_service.add_verification(
            resource_id=sample_resource.id,
            steward_id="steward-bob",
            verification_method=VerificationMethod.IN_PERSON
        )

        # Record 3 successful uses
        for i in range(3):
            sanctuary_service.record_sanctuary_use(
                resource_id=sample_resource.id,
                request_id=f"request-{i}",
                outcome="success"
            )

        # Get high-trust resources
        high_trust = sanctuary_service.get_high_trust_resources(
            cell_id="cell-001",
            resource_type=SanctuaryResourceType.SAFE_SPACE
        )

        # Resource should NOW appear
        resource_ids = [r.id for r in high_trust]
        assert sample_resource.id in resource_ids


class TestVerificationModels:
    """Test verification model properties"""

    def test_verification_is_valid_property(self):
        """is_valid checks verification count and expiry."""
        verification = SanctuaryVerification(
            resource_id="resource-001",
            verifications=[
                VerificationRecord(
                    id="ver-001",
                    resource_id="resource-001",
                    steward_id="alice",
                    verification_method=VerificationMethod.IN_PERSON
                ),
                VerificationRecord(
                    id="ver-002",
                    resource_id="resource-001",
                    steward_id="bob",
                    verification_method=VerificationMethod.IN_PERSON
                )
            ],
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )

        assert verification.is_valid is True
        assert verification.verification_count == 2

    def test_verification_invalid_if_too_few(self):
        """is_valid is False if less than 2 verifications."""
        verification = SanctuaryVerification(
            resource_id="resource-001",
            verifications=[
                VerificationRecord(
                    id="ver-001",
                    resource_id="resource-001",
                    steward_id="alice",
                    verification_method=VerificationMethod.IN_PERSON
                )
            ],
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )

        assert verification.is_valid is False

    def test_verification_invalid_if_expired(self):
        """is_valid is False if expired."""
        verification = SanctuaryVerification(
            resource_id="resource-001",
            verifications=[
                VerificationRecord(
                    id="ver-001",
                    resource_id="resource-001",
                    steward_id="alice",
                    verification_method=VerificationMethod.IN_PERSON
                ),
                VerificationRecord(
                    id="ver-002",
                    resource_id="resource-001",
                    steward_id="bob",
                    verification_method=VerificationMethod.IN_PERSON
                )
            ],
            expires_at=datetime.now(UTC) - timedelta(days=1)  # Expired yesterday
        )

        assert verification.is_valid is False

    def test_is_high_trust_requires_three_uses(self):
        """is_high_trust requires 3+ successful uses and valid verification."""
        verification = SanctuaryVerification(
            resource_id="resource-001",
            verifications=[
                VerificationRecord(
                    id="ver-001",
                    resource_id="resource-001",
                    steward_id="alice",
                    verification_method=VerificationMethod.IN_PERSON
                ),
                VerificationRecord(
                    id="ver-002",
                    resource_id="resource-001",
                    steward_id="bob",
                    verification_method=VerificationMethod.IN_PERSON
                )
            ],
            expires_at=datetime.now(UTC) + timedelta(days=30),
            successful_uses=3
        )

        assert verification.is_high_trust is True

    def test_is_high_trust_false_with_low_uses(self):
        """is_high_trust is False with less than 3 uses."""
        verification = SanctuaryVerification(
            resource_id="resource-001",
            verifications=[
                VerificationRecord(
                    id="ver-001",
                    resource_id="resource-001",
                    steward_id="alice",
                    verification_method=VerificationMethod.IN_PERSON
                ),
                VerificationRecord(
                    id="ver-002",
                    resource_id="resource-001",
                    steward_id="bob",
                    verification_method=VerificationMethod.IN_PERSON
                )
            ],
            expires_at=datetime.now(UTC) + timedelta(days=30),
            successful_uses=2  # Only 2 uses
        )

        assert verification.is_high_trust is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
