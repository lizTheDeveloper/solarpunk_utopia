"""
End-to-End tests for Web of Trust system.

Tests the complete vouch chain flow from genesis through propagation to revocation.

Test scenarios (from GAP-E2E proposal):
GIVEN Genesis node G with trust 1.0
WHEN G vouches for Alice
THEN Alice.trust = 0.8 (or configured decay)
WHEN Alice vouches for Bob (Alice.trust >= 0.7)
THEN Bob.trust = Alice.trust * decay
WHEN Alice revokes vouch for Bob
THEN Bob.trust recalculated (may drop to 0 if no other chains)
AND Bob's access to high-trust resources restricted
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.models.vouch import (
    TRUST_ATTENUATION,
    TRUST_THRESHOLDS,
    MAX_VOUCHES_PER_MONTH,
)


class TestWebOfTrustE2E:
    """End-to-end Web of Trust flow tests"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test database and service"""
        # Create temp database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)

        # Create repositories and services
        self.vouch_repo = VouchRepository(self.db_path)
        self.trust_service = WebOfTrustService(self.vouch_repo)

        yield

        # Cleanup
        os.unlink(self.db_path)

    def test_genesis_to_alice_vouch_chain(self):
        """
        E2E Test 1: Genesis vouches for Alice

        GIVEN Genesis node G with trust 1.0
        WHEN G vouches for Alice
        THEN Alice.trust = 0.8 (TRUST_ATTENUATION ^ 1)
        AND Alice can perform trust-gated actions
        """
        # Setup: Create genesis node
        self.vouch_repo.add_genesis_node("genesis-g", notes="Founding member")

        # Verify genesis has full trust
        g_trust = self.trust_service.compute_trust_score("genesis-g")
        assert g_trust.computed_trust == 1.0
        assert g_trust.is_genesis is True

        # Action: Genesis vouches for Alice
        vouch = self.vouch_repo.create_vouch("genesis-g", "alice", "met_in_person")
        assert vouch is not None
        assert vouch.voucher_id == "genesis-g"
        assert vouch.vouchee_id == "alice"

        # Verify: Alice gets correct trust
        alice_trust = self.trust_service.compute_trust_score("alice")
        expected_trust = TRUST_ATTENUATION ** 1  # 0.8
        assert abs(alice_trust.computed_trust - expected_trust) < 0.01
        assert alice_trust.best_chain_distance == 1
        assert alice_trust.is_genesis is False
        assert len(alice_trust.vouch_chains) == 1

        # Verify: Alice can perform trust-gated actions
        can_view, _ = self.trust_service.check_trust_threshold("alice", "view_public_offers")
        assert can_view is True  # 0.8 > 0.3

        can_post, _ = self.trust_service.check_trust_threshold("alice", "post_offers_needs")
        assert can_post is True  # 0.8 > 0.5

        can_message, _ = self.trust_service.check_trust_threshold("alice", "send_messages")
        assert can_message is True  # 0.8 > 0.6

        can_vouch, _ = self.trust_service.check_trust_threshold("alice", "vouch_others")
        assert can_vouch is True  # 0.8 > 0.7

        can_steward, _ = self.trust_service.check_trust_threshold("alice", "steward_actions")
        assert can_steward is False  # 0.8 < 0.9

    def test_multi_hop_vouch_chain_with_attenuation(self):
        """
        E2E Test 2: Multi-hop vouch chain with trust attenuation

        GIVEN Genesis -> Alice (0.8 trust)
        WHEN Alice vouches for Bob (Alice.trust >= 0.7)
        THEN Bob.trust = 0.8 * 0.8 = 0.64
        WHEN Bob vouches for Carol
        THEN Carol.trust = 0.64 * 0.8 = 0.512
        AND each user has appropriate access levels
        """
        # Setup: Genesis -> Alice
        self.vouch_repo.add_genesis_node("genesis")
        self.vouch_repo.create_vouch("genesis", "alice", "founding_member")

        alice_trust = self.trust_service.compute_trust_score("alice")
        assert abs(alice_trust.computed_trust - 0.8) < 0.01

        # Action: Alice vouches for Bob
        eligibility = self.trust_service.get_vouch_eligibility("alice", "bob")
        assert eligibility["can_vouch"] is True

        self.vouch_repo.create_vouch("alice", "bob", "worked_together")

        # Verify: Bob has correct trust
        bob_trust = self.trust_service.compute_trust_score("bob")
        expected_bob_trust = TRUST_ATTENUATION ** 2  # 0.64
        assert abs(bob_trust.computed_trust - expected_bob_trust) < 0.01
        assert bob_trust.best_chain_distance == 2

        # Verify: Bob can do some actions but not vouch (0.64 < 0.7)
        can_view, _ = self.trust_service.check_trust_threshold("bob", "view_public_offers")
        assert can_view is True

        can_message, _ = self.trust_service.check_trust_threshold("bob", "send_messages")
        assert can_message is True

        can_vouch, _ = self.trust_service.check_trust_threshold("bob", "vouch_others")
        assert can_vouch is False  # 0.64 < 0.7

        # Setup: Boost Bob's trust with second path
        self.vouch_repo.add_genesis_node("genesis-2")
        self.vouch_repo.create_vouch("genesis-2", "bob", "second_path")

        # Bob now has higher trust from shorter path
        bob_trust_boosted = self.trust_service.compute_trust_score("bob", force_recompute=True)
        assert abs(bob_trust_boosted.computed_trust - 0.8) < 0.01  # Best path is now 1 hop

        # Action: Bob (now 0.8 trust) vouches for Carol
        self.vouch_repo.create_vouch("bob", "carol", "family")

        # Verify: Carol has trust based on Bob's best path
        carol_trust = self.trust_service.compute_trust_score("carol")
        # Carol is 2 hops from genesis-2 (via Bob)
        expected_carol_trust = TRUST_ATTENUATION ** 2  # 0.64
        assert abs(carol_trust.computed_trust - expected_carol_trust) < 0.01

    def test_vouch_revocation_reduces_trust(self):
        """
        E2E Test 3: Revoking vouch reduces vouchee's trust

        GIVEN Genesis -> Alice (0.8 trust)
        WHEN Genesis revokes vouch for Alice
        THEN Alice.trust drops to 0.0
        AND Alice loses access to trust-gated actions
        """
        # Setup: Genesis -> Alice
        self.vouch_repo.add_genesis_node("genesis")
        vouch = self.vouch_repo.create_vouch("genesis", "alice", "initial_trust")

        # Verify: Alice has trust
        alice_trust_before = self.trust_service.compute_trust_score("alice")
        assert abs(alice_trust_before.computed_trust - 0.8) < 0.01

        can_vouch_before, _ = self.trust_service.check_trust_threshold("alice", "vouch_others")
        assert can_vouch_before is True

        # Action: Revoke the vouch
        self.vouch_repo.revoke_vouch(vouch.id, "compromised_device")

        # Verify: Alice's trust drops to 0
        alice_trust_after = self.trust_service.compute_trust_score("alice", force_recompute=True)
        assert alice_trust_after.computed_trust == 0.0

        # Verify: Alice loses access to trust-gated actions
        can_vouch_after, _ = self.trust_service.check_trust_threshold("alice", "vouch_others")
        assert can_vouch_after is False

        can_message_after, _ = self.trust_service.check_trust_threshold("alice", "send_messages")
        assert can_message_after is False

    def test_revocation_cascade_affects_downstream_users(self):
        """
        E2E Test 4: Revocation cascades to downstream users

        GIVEN Genesis -> Alice -> Bob -> Carol (vouch chain)
        WHEN Genesis revokes vouch for Alice
        THEN Alice, Bob, and Carol all lose trust
        AND all are affected in cascade result
        """
        # Setup: Build vouch chain
        self.vouch_repo.add_genesis_node("genesis")
        vouch_genesis_alice = self.vouch_repo.create_vouch("genesis", "alice", "trust")
        vouch_alice_bob = self.vouch_repo.create_vouch("alice", "bob", "trust")
        vouch_bob_carol = self.vouch_repo.create_vouch("bob", "carol", "trust")

        # Verify: All have trust
        alice_trust_before = self.trust_service.compute_trust_score("alice")
        bob_trust_before = self.trust_service.compute_trust_score("bob")
        carol_trust_before = self.trust_service.compute_trust_score("carol")

        assert alice_trust_before.computed_trust > 0.0
        assert bob_trust_before.computed_trust > 0.0
        assert carol_trust_before.computed_trust > 0.0

        # Action: Revoke genesis -> alice with cascade
        result = self.trust_service.revoke_vouch_with_cascade(
            vouch_genesis_alice.id,
            "compromised"
        )

        # Verify: Cascade result includes all affected users
        assert "alice" in result["affected_users"]
        assert "bob" in result["affected_users"]
        assert "carol" in result["affected_users"]
        assert len(result["affected_users"]) == 3

        # Verify: All have 0 trust now
        alice_trust_after = self.trust_service.compute_trust_score("alice", force_recompute=True)
        bob_trust_after = self.trust_service.compute_trust_score("bob", force_recompute=True)
        carol_trust_after = self.trust_service.compute_trust_score("carol", force_recompute=True)

        assert alice_trust_after.computed_trust == 0.0
        assert bob_trust_after.computed_trust == 0.0
        assert carol_trust_after.computed_trust == 0.0

    def test_partial_revocation_preserves_alternate_paths(self):
        """
        E2E Test 5: Revoking one path doesn't affect users with alternate paths

        GIVEN Two paths to Carol:
          - Genesis-1 -> Alice -> Carol
          - Genesis-2 -> Bob -> Carol
        WHEN Genesis-1 -> Alice is revoked
        THEN Alice loses trust
        BUT Carol maintains trust via Genesis-2 -> Bob -> Carol path
        """
        # Setup: Two genesis nodes
        self.vouch_repo.add_genesis_node("genesis-1")
        self.vouch_repo.add_genesis_node("genesis-2")

        # Path 1: genesis-1 -> alice -> carol
        vouch_g1_alice = self.vouch_repo.create_vouch("genesis-1", "alice", "trust")
        vouch_alice_carol = self.vouch_repo.create_vouch("alice", "carol", "trust")

        # Path 2: genesis-2 -> bob -> carol
        vouch_g2_bob = self.vouch_repo.create_vouch("genesis-2", "bob", "trust")
        vouch_bob_carol = self.vouch_repo.create_vouch("bob", "carol", "trust")

        # Verify: Carol has trust from both paths
        carol_trust_before = self.trust_service.compute_trust_score("carol")
        assert carol_trust_before.computed_trust > 0.0
        assert len(carol_trust_before.vouch_chains) == 2  # Two paths

        # Action: Revoke path 1 (genesis-1 -> alice)
        result = self.trust_service.revoke_vouch_with_cascade(vouch_g1_alice.id, "compromised")

        # Verify: Alice is affected
        assert "alice" in result["affected_users"]

        alice_trust_after = self.trust_service.compute_trust_score("alice", force_recompute=True)
        assert alice_trust_after.computed_trust == 0.0

        # Verify: Carol still has trust from path 2
        carol_trust_after = self.trust_service.compute_trust_score("carol", force_recompute=True)
        assert carol_trust_after.computed_trust > 0.0
        expected_trust = TRUST_ATTENUATION ** 2  # 2 hops via bob
        assert abs(carol_trust_after.computed_trust - expected_trust) < 0.01
        assert len(carol_trust_after.vouch_chains) == 1  # Only one path remains

    def test_monthly_vouch_limit_prevents_spam(self):
        """
        E2E Test 6: Monthly vouch limit prevents sybil attacks (GAP-103)

        GIVEN Alice has high trust (0.8)
        WHEN Alice vouches for 5 users in 30 days (MAX_VOUCHES_PER_MONTH)
        THEN Alice cannot vouch for a 6th user
        AND receives clear error message with reset date
        """
        # Setup: Genesis -> Alice
        self.vouch_repo.add_genesis_node("genesis")
        self.vouch_repo.create_vouch("genesis", "alice", "trust")

        alice_trust = self.trust_service.compute_trust_score("alice")
        assert abs(alice_trust.computed_trust - 0.8) < 0.01

        # Action: Alice vouches for MAX_VOUCHES_PER_MONTH users
        for i in range(MAX_VOUCHES_PER_MONTH):
            user_id = f"user-{i}"
            eligibility = self.trust_service.get_vouch_eligibility("alice", user_id)
            assert eligibility["can_vouch"] is True
            self.vouch_repo.create_vouch("alice", user_id, f"vouch_{i}")

        # Verify: Alice cannot vouch for 6th user
        eligibility_6th = self.trust_service.get_vouch_eligibility("alice", "user-6")
        assert eligibility_6th["can_vouch"] is False
        assert "Monthly vouch limit" in eligibility_6th["reason"]
        assert "Resets in" in eligibility_6th["reason"]

    def test_cannot_vouch_for_same_user_twice(self):
        """
        E2E Test 7: Users cannot vouch for the same person twice

        GIVEN Alice has vouched for Bob
        WHEN Alice tries to vouch for Bob again
        THEN vouch is rejected with clear error
        """
        # Setup: Genesis -> Alice -> Bob
        self.vouch_repo.add_genesis_node("genesis")
        self.vouch_repo.create_vouch("genesis", "alice", "trust")
        self.vouch_repo.create_vouch("alice", "bob", "initial_vouch")

        # Verify: Alice cannot vouch for Bob again
        eligibility = self.trust_service.get_vouch_eligibility("alice", "bob")
        assert eligibility["can_vouch"] is False
        assert "already vouched" in eligibility["reason"]

    def test_low_trust_user_cannot_vouch(self):
        """
        E2E Test 8: Low-trust users cannot vouch for others

        GIVEN Bob has 0.64 trust (below 0.7 threshold)
        WHEN Bob tries to vouch for Carol
        THEN vouch is rejected due to insufficient trust
        """
        # Setup: Genesis -> Alice -> Bob (0.64 trust)
        self.vouch_repo.add_genesis_node("genesis")
        self.vouch_repo.create_vouch("genesis", "alice", "trust")
        self.vouch_repo.create_vouch("alice", "bob", "trust")

        bob_trust = self.trust_service.compute_trust_score("bob")
        assert abs(bob_trust.computed_trust - 0.64) < 0.01

        # Verify: Bob cannot vouch
        eligibility = self.trust_service.get_vouch_eligibility("bob", "carol")
        assert eligibility["can_vouch"] is False
        assert "Insufficient trust" in eligibility["reason"]
        assert "0.7" in eligibility["reason"]  # Threshold
        assert "0.64" in eligibility["reason"]  # Bob's actual trust

    def test_multiple_genesis_nodes_provide_redundancy(self):
        """
        E2E Test 9: Multiple genesis nodes for network resilience

        GIVEN Multiple genesis nodes (founding community members)
        WHEN each genesis vouches for different users
        THEN network has multiple trust roots
        AND users can be reached via different paths
        """
        # Setup: Three genesis nodes (founding collective)
        self.vouch_repo.add_genesis_node("genesis-alice", notes="Co-founder 1")
        self.vouch_repo.add_genesis_node("genesis-bob", notes="Co-founder 2")
        self.vouch_repo.add_genesis_node("genesis-carol", notes="Co-founder 3")

        # Each genesis vouches for different users
        self.vouch_repo.create_vouch("genesis-alice", "user-a", "trust")
        self.vouch_repo.create_vouch("genesis-bob", "user-b", "trust")
        self.vouch_repo.create_vouch("genesis-carol", "user-c", "trust")

        # Cross-network connections
        self.vouch_repo.create_vouch("user-a", "user-b", "collaboration")
        self.vouch_repo.create_vouch("user-b", "user-c", "collaboration")

        # Verify: All genesis nodes have full trust
        genesis_list = self.vouch_repo.get_genesis_nodes()
        assert len(genesis_list) == 3

        for genesis_id in genesis_list:
            trust = self.trust_service.compute_trust_score(genesis_id)
            assert trust.computed_trust == 1.0
            assert trust.is_genesis is True

        # Verify: user-b has TWO paths to genesis (direct + via user-a)
        user_b_trust = self.trust_service.compute_trust_score("user-b")
        assert len(user_b_trust.vouch_chains) == 2
        # Best path is direct: genesis-bob -> user-b
        assert abs(user_b_trust.computed_trust - 0.8) < 0.01

        # Verify: user-c has THREE paths to genesis
        user_c_trust = self.trust_service.compute_trust_score("user-c")
        assert len(user_c_trust.vouch_chains) == 3
        # Best path is direct: genesis-carol -> user-c
        assert abs(user_c_trust.computed_trust - 0.8) < 0.01

    def test_trust_score_caching_improves_performance(self):
        """
        E2E Test 10: Trust score caching reduces computation

        GIVEN Complex vouch network
        WHEN trust score is computed multiple times
        THEN cached score is reused (same timestamp)
        UNTIL force_recompute or cache expires
        """
        # Setup: Complex network
        self.vouch_repo.add_genesis_node("genesis")
        self.vouch_repo.create_vouch("genesis", "alice", "trust")
        self.vouch_repo.create_vouch("alice", "bob", "trust")

        # First computation
        trust_1 = self.trust_service.compute_trust_score("bob")
        time_1 = trust_1.last_computed

        # Second computation (should use cache)
        trust_2 = self.trust_service.compute_trust_score("bob")
        time_2 = trust_2.last_computed

        # Verify: Same timestamp = cache hit
        assert time_1 == time_2
        assert trust_1.computed_trust == trust_2.computed_trust

        # Force recompute
        trust_3 = self.trust_service.compute_trust_score("bob", force_recompute=True)
        time_3 = trust_3.last_computed

        # Verify: Different timestamp = fresh computation
        assert time_3 > time_1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
