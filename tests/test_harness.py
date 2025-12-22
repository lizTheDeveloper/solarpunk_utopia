"""
Tests for the test harness infrastructure

Verifies that multi-node simulation, time control, and trust fixtures work correctly
"""

import pytest
import time
from tests.harness import (
    MultiNodeHarness,
    TimeController,
    freeze_time,
    advance_time,
    create_trust_chain,
    create_disjoint_communities,
    create_ring_topology,
    create_star_topology,
    TrustGraphFixture
)


class TestMultiNodeHarness:
    """Tests for multi-node mesh simulation"""

    @pytest.mark.asyncio
    async def test_create_nodes(self):
        """Can create nodes in the harness"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")

        assert alice.node_id == "Alice"
        assert bob.node_id == "Bob"
        assert len(harness.nodes) == 2

    @pytest.mark.asyncio
    async def test_connect_nodes(self):
        """Can create bidirectional connections"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")

        harness.connect(alice, bob)

        assert bob.node_id in alice.connections
        assert alice.node_id in bob.connections

    @pytest.mark.asyncio
    async def test_disconnect_nodes(self):
        """Can disconnect nodes"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")

        harness.connect(alice, bob)
        harness.disconnect(alice, bob)

        assert bob.node_id not in alice.connections
        assert alice.node_id not in bob.connections

    @pytest.mark.asyncio
    async def test_create_bundle(self):
        """Can create bundles with metadata"""
        harness = MultiNodeHarness()

        bundle = harness.create_bundle(
            source="Alice",
            destination="Bob",
            payload=b"Hello",
            priority=5,
            ttl_seconds=60
        )

        assert bundle.source_node == "Alice"
        assert bundle.destination == "Bob"
        assert bundle.payload == b"Hello"
        assert bundle.priority == 5
        assert bundle.expires_at is not None

    @pytest.mark.asyncio
    async def test_sync_transfers_bundles(self):
        """Sync transfers bundles between connected nodes"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")
        harness.connect(alice, bob)

        # Create bundle on Alice
        bundle = harness.create_bundle("Alice", "Bob", b"Test")
        alice.add_bundle(bundle)

        # Sync to Bob
        transferred = await harness.sync_nodes(alice, bob)

        assert bundle.bundle_id in transferred
        assert bundle.bundle_id in bob.bundles

    @pytest.mark.asyncio
    async def test_sync_respects_priority(self):
        """High priority bundles transfer first"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")
        harness.connect(alice, bob)

        # Create bundles with different priorities
        low = harness.create_bundle("Alice", "Bob", b"Low", priority=1)
        high = harness.create_bundle("Alice", "Bob", b"High", priority=10)

        alice.add_bundle(low)
        alice.add_bundle(high)

        transferred = await harness.sync_nodes(alice, bob)

        # Both transferred, but check order in log
        assert len(transferred) == 2

    @pytest.mark.asyncio
    async def test_bundle_expiration(self):
        """Expired bundles are not transferred"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")
        harness.connect(alice, bob)

        # Create bundle that expired 1 second ago
        bundle = harness.create_bundle("Alice", "Bob", b"Test", ttl_seconds=-1)
        alice.add_bundle(bundle)

        # Sync should skip expired bundle
        transferred = await harness.sync_nodes(alice, bob)

        assert bundle.bundle_id not in transferred
        assert bundle.bundle_id not in bob.bundles

    @pytest.mark.asyncio
    async def test_hop_limit(self):
        """Bundles stop propagating after max hops"""
        harness = MultiNodeHarness()

        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")
        harness.connect(alice, bob)

        # Create bundle with max_hops=0
        bundle = harness.create_bundle("Alice", "Bob", b"Test")
        bundle.max_hops = 0
        alice.add_bundle(bundle)

        # Should not transfer (already at hop limit)
        transferred = await harness.sync_nodes(alice, bob)
        assert bundle.bundle_id not in transferred

    @pytest.mark.asyncio
    async def test_propagate_bundle(self):
        """Bundles propagate through the network"""
        harness = MultiNodeHarness()

        # Create chain: Alice -- Bob -- Carol
        alice = harness.create_node("Alice")
        bob = harness.create_node("Bob")
        carol = harness.create_node("Carol")

        harness.connect(alice, bob)
        harness.connect(bob, carol)

        # Create bundle
        bundle = harness.create_bundle("Alice", "*", b"Broadcast")
        alice.add_bundle(bundle)

        # Propagate
        reached = await harness.propagate_bundle(bundle, alice)

        assert "Alice" in reached
        assert "Bob" in reached
        assert "Carol" in reached
        assert reached["Alice"] == 0
        assert reached["Bob"] == 1
        assert reached["Carol"] == 2


class TestTimeControl:
    """Tests for time manipulation"""

    def test_freeze_time(self):
        """Can freeze time"""
        tc = TimeController()
        tc.freeze()

        t1 = tc.now()
        time.sleep(0.01)  # Try to advance time
        t2 = tc.now()

        assert t1 == t2  # Time didn't advance

        tc.unfreeze()

    def test_advance_time(self):
        """Can advance frozen time"""
        tc = TimeController()
        tc.freeze()

        t1 = tc.now()
        tc.advance(seconds=60)
        t2 = tc.now()

        assert t2 == t1 + 60

        tc.unfreeze()

    def test_advance_with_units(self):
        """Can advance by different time units"""
        tc = TimeController()
        tc.freeze()

        t1 = tc.now()
        tc.advance(minutes=5, hours=2, days=1)
        t2 = tc.now()

        expected = t1 + (5 * 60) + (2 * 3600) + (1 * 86400)
        assert t2 == expected

        tc.unfreeze()

    def test_freeze_time_context_manager(self):
        """freeze_time context manager works"""
        with freeze_time() as tc:
            t1 = time.time()
            time.sleep(0.01)
            t2 = time.time()
            assert t1 == t2

        # Time resumes after context

    def test_advance_time_context_manager(self):
        """advance_time context manager works"""
        with advance_time(hours=24) as tc:
            # We're 24 hours in the future
            assert tc.is_frozen()


class TestTrustGraphFixtures:
    """Tests for trust graph fixtures"""

    def test_create_node(self):
        """Can create nodes in trust graph"""
        fixture = TrustGraphFixture()

        alice = fixture.create_node("alice", "Alice")

        assert alice.node_id == "alice"
        assert alice.name == "Alice"
        assert fixture.get_trust("alice") == 0.0

    def test_create_vouch(self):
        """Can create vouch relationship"""
        fixture = TrustGraphFixture()

        fixture.create_node("genesis", "Genesis")
        fixture.create_node("alice", "Alice")

        # Genesis vouches for Alice
        fixture.create_vouch("genesis", "alice")

        assert "alice" in fixture.nodes["genesis"].has_vouched
        assert "genesis" in fixture.nodes["alice"].vouched_by

    def test_trust_propagation(self):
        """Trust propagates through vouches"""
        fixture = TrustGraphFixture(trust_decay=0.85)

        fixture.create_node("genesis", "Genesis")
        fixture.create_node("alice", "Alice")
        fixture.create_node("bob", "Bob")

        # Create chain: Genesis → Alice → Bob
        fixture.create_vouch("genesis", "alice")
        fixture.create_vouch("alice", "bob")

        # Genesis has no vouchers, so trust = 1.0 (genesis node)
        assert fixture.get_trust("genesis") == 1.0

        # Alice vouched by genesis: 1.0 * 0.85 = 0.85
        assert fixture.get_trust("alice") == pytest.approx(0.85)

        # Bob vouched by Alice: 0.85 * 0.85 = 0.7225
        assert fixture.get_trust("bob") == pytest.approx(0.7225)

    def test_revoke_vouch(self):
        """Revoking vouch recalculates trust"""
        fixture = TrustGraphFixture(trust_decay=0.85)

        fixture.create_node("genesis", "Genesis")
        fixture.create_node("alice", "Alice")
        fixture.create_node("bob", "Bob")

        fixture.create_vouch("genesis", "alice")
        fixture.create_vouch("alice", "bob")

        # Bob has trust
        assert fixture.get_trust("bob") > 0.7

        # Revoke Alice's vouch for Bob
        fixture.revoke_vouch("alice", "bob")

        # Bob's trust drops to 0 (no path to genesis)
        assert fixture.get_trust("bob") == 0.0

    def test_create_trust_chain(self):
        """create_trust_chain helper works"""
        chain = create_trust_chain(["Genesis", "Alice", "Bob", "Carol"])

        assert chain.get_trust("Genesis") == 1.0
        assert chain.get_trust("Alice") == pytest.approx(0.85)
        assert chain.get_trust("Bob") == pytest.approx(0.7225)
        assert chain.get_trust("Carol") == pytest.approx(0.614125)

    def test_create_disjoint_communities(self):
        """create_disjoint_communities creates separate trust networks"""
        fixture = create_disjoint_communities([3, 2])

        # No trust path between communities
        path = fixture.get_trust_path("Community0_Member0", "Community1_Member0")
        assert path is None

        # Within community, path exists
        path = fixture.get_trust_path("Community0_Genesis", "Community0_Member0")
        assert path is not None

    def test_create_ring_topology(self):
        """create_ring_topology creates circular vouches"""
        ring = create_ring_topology(["A", "B", "C", "D"])

        # Check vouches form a ring
        assert "B" in ring.nodes["A"].has_vouched
        assert "C" in ring.nodes["B"].has_vouched
        assert "D" in ring.nodes["C"].has_vouched
        assert "A" in ring.nodes["D"].has_vouched

    def test_create_star_topology(self):
        """create_star_topology creates hub-and-spoke"""
        star = create_star_topology("Hub", ["Spoke1", "Spoke2", "Spoke3"])

        # Hub vouches for all spokes
        assert "Spoke1" in star.nodes["Hub"].has_vouched
        assert "Spoke2" in star.nodes["Hub"].has_vouched
        assert "Spoke3" in star.nodes["Hub"].has_vouched

        # All spokes have same trust level
        trust1 = star.get_trust("Spoke1")
        trust2 = star.get_trust("Spoke2")
        trust3 = star.get_trust("Spoke3")

        assert trust1 == trust2 == trust3

    def test_export_graph(self):
        """Can export graph for debugging"""
        chain = create_trust_chain(["Genesis", "Alice", "Bob"])

        exported = chain.export_graph()

        assert "nodes" in exported
        assert "vouches" in exported
        assert len(exported["nodes"]) == 3
        assert len(exported["vouches"]) == 2
