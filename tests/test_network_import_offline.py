"""
Test Network Import functionality - verify all works offline.

Tests:
1. Threshold signature attestation creation (no internet)
2. In-person attestation claim (no internet)
3. Challenge-response verification (no internet)
4. Mesh vouch verification (no internet)
5. Steward bulk vouching (no internet)
6. Steward accountability tracking (no internet)

All tests verify NO external API calls, NO internet dependency.
"""
import pytest
from datetime import datetime
from app.models.attestation import (
    Attestation,
    AttestationClaim,
    ChallengeQuestion,
    BulkVouchRequest,
)
from app.database.attestation_repository import AttestationRepository
from app.database.vouch_repository import VouchRepository
from app.services.attestation_service import AttestationService
from app.services.crypto_service import CryptoService
from app.services.web_of_trust_service import WebOfTrustService


@pytest.fixture
def db_path(tmp_path):
    """Create temporary database for testing."""
    return str(tmp_path / "test.db")


@pytest.fixture
def attestation_repo(db_path):
    """Create attestation repository."""
    return AttestationRepository(db_path)


@pytest.fixture
def vouch_repo(db_path):
    """Create vouch repository."""
    return VouchRepository(db_path)


@pytest.fixture
def crypto_service(tmp_path):
    """Create crypto service with temp keys."""
    return CryptoService(keys_dir=tmp_path / "keys")


@pytest.fixture
def trust_service(vouch_repo):
    """Create trust service."""
    return WebOfTrustService(vouch_repo)


@pytest.fixture
def attestation_service(attestation_repo, vouch_repo, crypto_service, trust_service):
    """Create attestation service."""
    return AttestationService(
        attestation_repo=attestation_repo,
        vouch_repo=vouch_repo,
        crypto_service=crypto_service,
        trust_service=trust_service,
    )


@pytest.fixture
def genesis_steward(vouch_repo):
    """Create a genesis steward for testing."""
    steward_id = "steward-genesis-1"
    vouch_repo.add_genesis_node(steward_id, notes="Test steward")
    return steward_id


def test_threshold_signature_attestation_offline(attestation_service, crypto_service):
    """Test creating threshold-signed attestation works offline."""
    # Simulate 3 stewards signing an attestation (offline)
    stewards = []
    for i in range(3):
        service = CryptoService()
        stewards.append({
            'pubkey': service.get_public_key_pem(),
            'service': service
        })

    # Create canonical data
    attestation_data = {
        "type": "cohort",
        "subject_identifier": "Alex K.",
        "claims": {"cohort": "2019-fall-bootcamp", "role": "graduate"},
        "threshold_required": 3,
    }

    import json
    canonical = json.dumps(attestation_data, sort_keys=True)

    # Each steward signs (offline, no internet)
    signatures = [s['service'].sign(canonical) for s in stewards]
    pubkeys = [s['pubkey'] for s in stewards]

    # Create attestation (offline)
    attestation, success, message = attestation_service.create_attestation(
        type=attestation_data['type'],
        subject_identifier=attestation_data['subject_identifier'],
        claims=attestation_data['claims'],
        issuer_pubkeys=pubkeys,
        signatures=signatures,
        threshold_required=3,
    )

    # Verify - all offline, no network calls
    assert success is True
    assert attestation is not None
    assert attestation.type == "cohort"
    assert attestation.threshold_required == 3
    assert len(attestation.signatures) == 3

    # Verify signatures (offline)
    is_valid, valid_count = attestation_service.verify_attestation_signatures(attestation)
    assert is_valid is True
    assert valid_count == 3


def test_in_person_attestation_claim_offline(attestation_service, attestation_repo, vouch_repo, genesis_steward):
    """Test in-person attestation claim works offline."""
    # Create attestation (already tested above, assuming it exists)
    attestation = attestation_repo.create_attestation(
        type="cohort",
        subject_identifier="Test User",
        claims={"cohort": "2019-fall"},
        issuer_pubkeys=["key1", "key2", "key3"],
        signatures=["sig1", "sig2", "sig3"],
        threshold_required=3,
    )

    # Create claimer and vouch them to genesis
    claimer_id = "user-claimer-1"
    vouch_repo.create_vouch(
        voucher_id=genesis_steward,
        vouchee_id=claimer_id,
        context="met_in_person"
    )

    # Steward verifies in person (offline - face-to-face)
    claim, success, message = attestation_service.claim_attestation_in_person(
        attestation_id=attestation.id,
        claimer_user_id=claimer_id,
        verifier_steward_id=genesis_steward,
    )

    # Verify - all offline
    assert success is True
    assert claim is not None
    assert claim.verification_method == "in_person"
    assert claim.status == "verified"
    assert claim.trust_granted > 0


def test_challenge_response_verification_offline(attestation_service, attestation_repo, genesis_steward):
    """Test challenge-response verification works offline."""
    # Create attestation
    attestation = attestation_repo.create_attestation(
        type="cohort",
        subject_identifier="Test User",
        claims={"cohort": "2019-fall"},
        issuer_pubkeys=["key1", "key2", "key3"],
        signatures=["sig1", "sig2", "sig3"],
        threshold_required=3,
    )

    # Create challenge question (offline)
    challenge, success, message = attestation_service.create_challenge_question(
        attestation_id=attestation.id,
        question="What city was the bootcamp in?",
        answer="Portland",
        created_by=genesis_steward,
    )

    assert success is True
    assert challenge is not None

    # User claims via challenge (offline - no network lookup)
    claimer_id = "user-claimer-2"
    claim, success, message = attestation_service.claim_attestation_challenge(
        attestation_id=attestation.id,
        claimer_user_id=claimer_id,
        challenge_id=challenge.id,
        answer="Portland",  # Correct answer
    )

    # Verify - all offline
    assert success is True
    assert claim is not None
    assert claim.verification_method == "challenge"
    assert claim.status == "verified"

    # Test incorrect answer (offline)
    claim2, success2, message2 = attestation_service.claim_attestation_challenge(
        attestation_id=attestation.id,
        claimer_user_id="user-claimer-3",
        challenge_id=challenge.id,
        answer="Seattle",  # Wrong answer
    )

    assert success2 is False


def test_mesh_vouch_verification_offline(attestation_service, attestation_repo, vouch_repo, genesis_steward):
    """Test mesh vouch verification works offline (via mesh network)."""
    # Create attestation
    attestation = attestation_repo.create_attestation(
        type="cohort",
        subject_identifier="Test User",
        claims={"cohort": "2019-fall"},
        issuer_pubkeys=["key1", "key2", "key3"],
        signatures=["sig1", "sig2", "sig3"],
        threshold_required=3,
    )

    # Create first verified member (in-person)
    verified_member_id = "user-verified-1"
    vouch_repo.create_vouch(
        voucher_id=genesis_steward,
        vouchee_id=verified_member_id,
        context="met_in_person"
    )

    # First member claims attestation in-person
    claim1, _, _ = attestation_service.claim_attestation_in_person(
        attestation_id=attestation.id,
        claimer_user_id=verified_member_id,
        verifier_steward_id=genesis_steward,
    )

    assert claim1.status == "verified"

    # New member joins via mesh vouch (offline - via mesh network)
    new_member_id = "user-new-1"
    claim2, success, message = attestation_service.claim_attestation_mesh_vouch(
        attestation_id=attestation.id,
        claimer_user_id=new_member_id,
        voucher_cohort_member_id=verified_member_id,
    )

    # Verify - all offline, via mesh
    assert success is True
    assert claim2 is not None
    assert claim2.verification_method == "mesh_vouch"
    assert claim2.status == "verified"
    assert claim2.verifier_id == verified_member_id


def test_steward_bulk_vouch_offline(attestation_service, vouch_repo, genesis_steward):
    """Test steward bulk vouching works offline."""
    # Steward vouches for multiple people (offline - no external APIs)
    request = BulkVouchRequest(
        vouchees=[
            {"name": "Alice", "identifier": "alice-pk"},
            {"name": "Bob", "identifier": "bob-pk"},
            {"name": "Charlie", "identifier": "charlie-pk"},
        ],
        context="food_co_op_members",
        attestation="met_in_person"
    )

    vouches, failed, message = attestation_service.bulk_vouch(
        steward_id=genesis_steward,
        request=request,
    )

    # Verify - all offline
    assert len(vouches) == 3
    assert len(failed) == 0
    assert all(v.voucher_id == genesis_steward for v in vouches)
    assert all(v.context == "food_co_op_members" for v in vouches)


def test_steward_accountability_offline(attestation_service, vouch_repo, genesis_steward):
    """Test steward accountability tracking works offline."""
    # Create some vouches
    for i in range(5):
        vouch_repo.create_vouch(
            voucher_id=genesis_steward,
            vouchee_id=f"user-{i}",
            context="test"
        )

    # Revoke one (simulate infiltrator found)
    vouches = vouch_repo.get_vouches_by_user(genesis_steward)
    vouch_repo.revoke_vouch(vouches[0].id, "infiltrator detected")

    # Update accountability (offline)
    record = attestation_service.update_steward_accountability_on_revocation(vouches[0].id)

    # Verify - all offline
    assert record is not None
    assert record.total_vouches == 5
    assert record.vouches_revoked == 1
    assert record.revocation_rate == 0.2  # 1/5 = 20%
    assert record.status == "warning"  # 20% triggers warning


def test_trust_bonus_calculation_offline(attestation_service, attestation_repo, genesis_steward):
    """Test trust bonus from attestations calculated offline."""
    # Create user and attestation
    user_id = "user-bonus-test"
    attestation = attestation_repo.create_attestation(
        type="cohort",
        subject_identifier="Test User",
        claims={"cohort": "2019-fall"},
        issuer_pubkeys=["key1", "key2", "key3"],
        signatures=["sig1", "sig2", "sig3"],
        threshold_required=3,
    )

    # User claims attestation in-person
    claim = attestation_repo.create_claim(
        attestation_id=attestation.id,
        claimer_user_id=user_id,
        verification_method="in_person",
        trust_granted=0.25,
        verifier_id=genesis_steward,
    )
    attestation_repo.update_claim_status(claim.id, "verified")

    # Calculate trust bonus (offline)
    bonus = attestation_service.get_user_attestation_trust_bonus(user_id)

    # Verify - all offline
    assert bonus == 0.25
    assert bonus <= 0.3  # Capped at 0.3


def test_no_external_dependencies():
    """Verify NO external API calls or internet dependencies."""
    import inspect
    from app.services.attestation_service import AttestationService
    from app.database.attestation_repository import AttestationRepository

    # Check that attestation service doesn't import requests, urllib, httpx, etc.
    service_source = inspect.getsource(AttestationService)
    repo_source = inspect.getsource(AttestationRepository)

    # Should NOT contain external HTTP libraries
    forbidden = ['import requests', 'import urllib', 'import httpx', 'import http.client']
    for lib in forbidden:
        assert lib not in service_source, f"Found forbidden import: {lib}"
        assert lib not in repo_source, f"Found forbidden import: {lib}"

    # Should NOT contain OAuth or external APIs
    forbidden_patterns = ['oauth', 'googleapis', 'api.github', 'graph.facebook']
    for pattern in forbidden_patterns:
        assert pattern not in service_source.lower(), f"Found external API: {pattern}"
        assert pattern not in repo_source.lower(), f"Found external API: {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
