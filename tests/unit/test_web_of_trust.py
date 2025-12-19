"""
Unit tests for Web of Trust system

Tests:
- Trust score computation
- Vouch chain discovery
- Trust attenuation
- Revocation cascade
- Genesis nodes
"""
import pytest
import os
import tempfile
from datetime import datetime

from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.models.vouch import TRUST_ATTENUATION, TRUST_THRESHOLDS


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def vouch_repo(temp_db):
    """Create a VouchRepository for testing."""
    return VouchRepository(temp_db)


@pytest.fixture
def trust_service(vouch_repo):
    """Create a WebOfTrustService for testing."""
    return WebOfTrustService(vouch_repo)


def test_genesis_node_has_full_trust(vouch_repo, trust_service):
    """Genesis nodes should have 1.0 trust."""
    # Add a genesis node
    vouch_repo.add_genesis_node("genesis-alice", notes="Founding member")

    # Check trust
    trust_score = trust_service.compute_trust_score("genesis-alice")

    assert trust_score.computed_trust == 1.0
    assert trust_score.is_genesis is True
    assert trust_score.best_chain_distance == 0


def test_single_hop_vouch(vouch_repo, trust_service):
    """User vouched directly by genesis should have 0.8 trust."""
    # Setup: genesis node
    vouch_repo.add_genesis_node("genesis-alice")

    # Alice vouches for Bob
    vouch_repo.create_vouch("genesis-alice", "bob", "met_in_person")

    # Check Bob's trust
    trust_score = trust_service.compute_trust_score("bob")

    expected_trust = TRUST_ATTENUATION ** 1  # One hop from genesis
    assert abs(trust_score.computed_trust - expected_trust) < 0.01
    assert trust_score.best_chain_distance == 1
    assert len(trust_score.vouch_chains) > 0


def test_two_hop_vouch_chain(vouch_repo, trust_service):
    """Trust attenuates correctly over two hops."""
    # Setup: genesis -> Alice -> Bob -> Carol
    vouch_repo.add_genesis_node("genesis")
    vouch_repo.create_vouch("genesis", "alice", "founding_member")
    vouch_repo.create_vouch("alice", "bob", "worked_together")
    vouch_repo.create_vouch("bob", "carol", "family")

    # Check Carol's trust
    trust_score = trust_service.compute_trust_score("carol")

    # Carol is 3 hops from genesis
    expected_trust = TRUST_ATTENUATION ** 3
    assert abs(trust_score.computed_trust - expected_trust) < 0.01
    assert trust_score.best_chain_distance == 3


def test_multiple_vouch_chains_uses_best(vouch_repo, trust_service):
    """When multiple vouch chains exist, use the one with highest trust."""
    # Setup: Two genesis nodes with different chain lengths to target
    vouch_repo.add_genesis_node("genesis-1")
    vouch_repo.add_genesis_node("genesis-2")

    # Short chain: genesis-1 -> target (1 hop)
    vouch_repo.create_vouch("genesis-1", "target", "direct")

    # Long chain: genesis-2 -> alice -> bob -> target (3 hops)
    vouch_repo.create_vouch("genesis-2", "alice", "vouch")
    vouch_repo.create_vouch("alice", "bob", "vouch")
    vouch_repo.create_vouch("bob", "target", "vouch")

    # Check target's trust
    trust_score = trust_service.compute_trust_score("target")

    # Should use shorter chain (higher trust)
    expected_trust = TRUST_ATTENUATION ** 1
    assert abs(trust_score.computed_trust - expected_trust) < 0.01
    assert trust_score.best_chain_distance == 1


def test_no_path_to_genesis(vouch_repo, trust_service):
    """Users with no path to genesis have 0.0 trust."""
    # Create vouches between non-genesis users
    vouch_repo.create_vouch("alice", "bob", "friends")
    vouch_repo.create_vouch("bob", "carol", "friends")

    # Check Carol's trust (no genesis in chain)
    trust_score = trust_service.compute_trust_score("carol")

    assert trust_score.computed_trust == 0.0
    assert trust_score.best_chain_distance == 999
    assert len(trust_score.vouch_chains) == 0


def test_revocation_reduces_trust(vouch_repo, trust_service):
    """Revoking a vouch reduces vouchee's trust."""
    # Setup chain
    vouch_repo.add_genesis_node("genesis")
    vouch = vouch_repo.create_vouch("genesis", "alice", "initial_trust")

    # Alice has trust
    trust_before = trust_service.compute_trust_score("alice")
    assert trust_before.computed_trust > 0.0

    # Revoke the vouch
    vouch_repo.revoke_vouch(vouch.id, "compromised")

    # Alice's trust drops to 0
    trust_after = trust_service.compute_trust_score("alice", force_recompute=True)
    assert trust_after.computed_trust == 0.0


def test_revocation_cascade(vouch_repo, trust_service):
    """Revoking a vouch cascades to downstream users."""
    # Setup chain: genesis -> alice -> bob -> carol
    vouch_repo.add_genesis_node("genesis")
    vouch_genesis_alice = vouch_repo.create_vouch("genesis", "alice", "trust")
    vouch_alice_bob = vouch_repo.create_vouch("alice", "bob", "trust")
    vouch_bob_carol = vouch_repo.create_vouch("bob", "carol", "trust")

    # All have trust
    assert trust_service.compute_trust_score("alice").computed_trust > 0.0
    assert trust_service.compute_trust_score("bob").computed_trust > 0.0
    assert trust_service.compute_trust_score("carol").computed_trust > 0.0

    # Revoke genesis -> alice
    result = trust_service.revoke_vouch_with_cascade(vouch_genesis_alice.id, "compromised")

    # All downstream users affected
    assert "alice" in result["affected_users"]
    assert "bob" in result["affected_users"]
    assert "carol" in result["affected_users"]

    # All have 0 trust now
    assert trust_service.compute_trust_score("alice", force_recompute=True).computed_trust == 0.0
    assert trust_service.compute_trust_score("bob", force_recompute=True).computed_trust == 0.0
    assert trust_service.compute_trust_score("carol", force_recompute=True).computed_trust == 0.0


def test_partial_revocation_cascade(vouch_repo, trust_service):
    """Revoking one path doesn't affect users with alternate paths."""
    # Setup: Two paths to carol
    vouch_repo.add_genesis_node("genesis-1")
    vouch_repo.add_genesis_node("genesis-2")

    # Path 1: genesis-1 -> alice -> carol
    vouch_g1_alice = vouch_repo.create_vouch("genesis-1", "alice", "trust")
    vouch_alice_carol = vouch_repo.create_vouch("alice", "carol", "trust")

    # Path 2: genesis-2 -> bob -> carol
    vouch_g2_bob = vouch_repo.create_vouch("genesis-2", "bob", "trust")
    vouch_bob_carol = vouch_repo.create_vouch("bob", "carol", "trust")

    # Carol has trust from both paths
    carol_trust_before = trust_service.compute_trust_score("carol")
    assert carol_trust_before.computed_trust > 0.0

    # Revoke path 1 (genesis-1 -> alice)
    trust_service.revoke_vouch_with_cascade(vouch_g1_alice.id, "compromised")

    # Carol still has trust from path 2
    carol_trust_after = trust_service.compute_trust_score("carol", force_recompute=True)
    assert carol_trust_after.computed_trust > 0.0


def test_trust_threshold_check(vouch_repo, trust_service):
    """check_trust_threshold correctly validates trust levels."""
    # Setup: genesis -> alice (0.8 trust)
    vouch_repo.add_genesis_node("genesis")
    vouch_repo.create_vouch("genesis", "alice", "trust")

    # Alice has 0.8 trust
    trust_score = trust_service.compute_trust_score("alice")
    assert abs(trust_score.computed_trust - 0.8) < 0.01

    # Check various thresholds
    can_view, _ = trust_service.check_trust_threshold("alice", "view_public_offers")
    assert can_view is True  # 0.8 > 0.3

    can_post, _ = trust_service.check_trust_threshold("alice", "post_offers_needs")
    assert can_post is True  # 0.8 > 0.5

    can_message, _ = trust_service.check_trust_threshold("alice", "send_messages")
    assert can_message is True  # 0.8 > 0.6

    can_vouch, _ = trust_service.check_trust_threshold("alice", "vouch_others")
    assert can_vouch is True  # 0.8 > 0.7

    can_steward, _ = trust_service.check_trust_threshold("alice", "steward_actions")
    assert can_steward is False  # 0.8 < 0.9


def test_vouch_eligibility(vouch_repo, trust_service):
    """get_vouch_eligibility checks if user can vouch."""
    # Setup: genesis -> alice -> bob
    vouch_repo.add_genesis_node("genesis")
    vouch_repo.create_vouch("genesis", "alice", "trust")

    # Alice (0.8 trust) CAN vouch
    eligibility = trust_service.get_vouch_eligibility("alice", "new-user")
    assert eligibility["can_vouch"] is True

    # Bob (no vouches yet) CANNOT vouch
    eligibility = trust_service.get_vouch_eligibility("bob", "new-user")
    assert eligibility["can_vouch"] is False
    assert "Insufficient trust" in eligibility["reason"]

    # Alice cannot vouch for same person twice
    vouch_repo.create_vouch("alice", "carol", "friend")
    eligibility = trust_service.get_vouch_eligibility("alice", "carol")
    assert eligibility["can_vouch"] is False
    assert "already vouched" in eligibility["reason"]


def test_cached_trust_score(vouch_repo, trust_service):
    """Trust scores are cached and reused within time window."""
    vouch_repo.add_genesis_node("genesis")
    vouch_repo.create_vouch("genesis", "alice", "trust")

    # First computation
    trust1 = trust_service.compute_trust_score("alice")
    time1 = trust1.last_computed

    # Second computation (should use cache)
    trust2 = trust_service.compute_trust_score("alice")
    time2 = trust2.last_computed

    # Same timestamp = cache hit
    assert time1 == time2

    # Force recompute
    trust3 = trust_service.compute_trust_score("alice", force_recompute=True)
    time3 = trust3.last_computed

    # Different timestamp = fresh computation
    assert time3 > time1


def test_vouch_count_and_revocation_count(vouch_repo, trust_service):
    """Trust score includes vouch and revocation counts."""
    vouch_repo.add_genesis_node("genesis-1")
    vouch_repo.add_genesis_node("genesis-2")

    # Alice gets two vouches
    vouch1 = vouch_repo.create_vouch("genesis-1", "alice", "trust")
    vouch2 = vouch_repo.create_vouch("genesis-2", "alice", "trust")

    trust = trust_service.compute_trust_score("alice")
    assert trust.vouch_count == 2
    assert trust.revocation_count == 0

    # Revoke one
    vouch_repo.revoke_vouch(vouch1.id, "test")

    trust = trust_service.compute_trust_score("alice", force_recompute=True)
    assert trust.vouch_count == 1  # One active vouch
    assert trust.revocation_count == 1  # One revoked


def test_genesis_node_list(vouch_repo):
    """Can list all genesis nodes."""
    vouch_repo.add_genesis_node("genesis-1", notes="Founder")
    vouch_repo.add_genesis_node("genesis-2", notes="Co-founder")

    genesis_list = vouch_repo.get_genesis_nodes()

    assert len(genesis_list) == 2
    assert "genesis-1" in genesis_list
    assert "genesis-2" in genesis_list


def test_is_genesis_node(vouch_repo):
    """Can check if user is genesis node."""
    vouch_repo.add_genesis_node("genesis")

    assert vouch_repo.is_genesis_node("genesis") is True
    assert vouch_repo.is_genesis_node("not-genesis") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
