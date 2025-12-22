"""
Trust Graph Fixtures

Provides predefined trust network topologies for testing Web of Trust:
- Genesis → fully trusted chain (5 hops)
- Disjoint communities (no trust path)
- Ring topology (circular vouches)
- Star topology (one central node vouches for all)
- Mesh topology (everyone vouches for multiple neighbors)
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
import uuid


@dataclass
class TrustNode:
    """A node in the trust graph"""
    node_id: str
    name: str
    trust_score: float = 0.0
    vouched_by: Set[str] = field(default_factory=set)
    has_vouched: Set[str] = field(default_factory=set)


@dataclass
class TrustVouch:
    """A vouch relationship in the trust graph"""
    voucher_id: str
    vouchee_id: str
    weight: float = 1.0
    created_at: float = 0.0


class TrustGraphFixture:
    """
    Fixture for creating and managing test trust graphs

    Example usage:
        fixture = TrustGraphFixture()

        # Create a chain: Genesis → Alice → Bob → Carol
        chain = fixture.create_chain(["Genesis", "Alice", "Bob", "Carol"])

        # Verify trust propagation
        assert fixture.get_trust("Genesis") == 1.0
        assert fixture.get_trust("Alice") == 0.85
        assert fixture.get_trust("Bob") == 0.85 * 0.85
    """

    def __init__(self, trust_decay: float = 0.85):
        """
        Initialize trust graph fixture

        Args:
            trust_decay: How much trust decays per hop (default 0.85 = 15% decay)
        """
        self.nodes: Dict[str, TrustNode] = {}
        self.vouches: List[TrustVouch] = []
        self.trust_decay = trust_decay

    def create_node(self, node_id: str, name: Optional[str] = None) -> TrustNode:
        """Create a new node in the trust graph"""
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists")

        if name is None:
            name = node_id

        node = TrustNode(node_id=node_id, name=name)
        self.nodes[node_id] = node
        return node

    def create_vouch(
        self,
        voucher_id: str,
        vouchee_id: str,
        weight: float = 1.0
    ) -> TrustVouch:
        """
        Create a vouch from voucher to vouchee

        Args:
            voucher_id: ID of node giving the vouch
            vouchee_id: ID of node receiving the vouch
            weight: Strength of the vouch (0.0 to 1.0)
        """
        if voucher_id not in self.nodes:
            raise ValueError(f"Voucher node {voucher_id} not found")
        if vouchee_id not in self.nodes:
            raise ValueError(f"Vouchee node {vouchee_id} not found")

        vouch = TrustVouch(voucher_id=voucher_id, vouchee_id=vouchee_id, weight=weight)
        self.vouches.append(vouch)

        self.nodes[voucher_id].has_vouched.add(vouchee_id)
        self.nodes[vouchee_id].vouched_by.add(voucher_id)

        # Recalculate trust scores
        self._recalculate_trust()

        return vouch

    def revoke_vouch(self, voucher_id: str, vouchee_id: str) -> None:
        """Revoke a vouch (remove the relationship)"""
        # Remove from vouches list
        self.vouches = [
            v for v in self.vouches
            if not (v.voucher_id == voucher_id and v.vouchee_id == vouchee_id)
        ]

        # Update nodes
        if voucher_id in self.nodes:
            self.nodes[voucher_id].has_vouched.discard(vouchee_id)
        if vouchee_id in self.nodes:
            self.nodes[vouchee_id].vouched_by.discard(voucher_id)

        # Recalculate trust scores
        self._recalculate_trust()

    def get_trust(self, node_id: str) -> float:
        """Get the trust score for a node"""
        if node_id not in self.nodes:
            return 0.0
        return self.nodes[node_id].trust_score

    def _recalculate_trust(self) -> None:
        """
        Recalculate trust scores for all nodes

        Uses a simple decay model:
        - Genesis nodes have trust 1.0
        - Each vouch multiplies trust by decay factor
        - If multiple paths exist, take the maximum
        """
        # Reset all trust scores
        for node in self.nodes.values():
            node.trust_score = 0.0

        # Find genesis nodes (nodes with trust explicitly set to 1.0 or no vouchers)
        genesis_nodes = [nid for nid, node in self.nodes.items() if len(node.vouched_by) == 0]

        # Set genesis nodes to 1.0
        for nid in genesis_nodes:
            self.nodes[nid].trust_score = 1.0

        # Propagate trust using BFS
        visited = set(genesis_nodes)
        queue = [(nid, 1.0, 0) for nid in genesis_nodes]

        while queue:
            current_id, current_trust, depth = queue.pop(0)

            # Find all nodes vouched by current node
            for vouch in self.vouches:
                if vouch.voucher_id == current_id:
                    vouchee_id = vouch.vouchee_id
                    new_trust = current_trust * self.trust_decay * vouch.weight

                    # Update if this path gives higher trust
                    if new_trust > self.nodes[vouchee_id].trust_score:
                        self.nodes[vouchee_id].trust_score = new_trust

                        if vouchee_id not in visited:
                            visited.add(vouchee_id)
                            queue.append((vouchee_id, new_trust, depth + 1))

    def get_trust_path(self, from_id: str, to_id: str) -> Optional[List[str]]:
        """
        Find the highest-trust path from one node to another

        Returns list of node IDs in the path, or None if no path exists
        """
        if from_id not in self.nodes or to_id not in self.nodes:
            return None

        # BFS to find path
        queue = [(from_id, [from_id])]
        visited = {from_id}

        while queue:
            current_id, path = queue.pop(0)

            if current_id == to_id:
                return path

            # Find nodes vouched by current
            for vouch in self.vouches:
                if vouch.voucher_id == current_id and vouch.vouchee_id not in visited:
                    visited.add(vouch.vouchee_id)
                    queue.append((vouch.vouchee_id, path + [vouch.vouchee_id]))

        return None

    def export_graph(self) -> Dict:
        """Export graph as dictionary for inspection/debugging"""
        return {
            "nodes": {
                nid: {
                    "name": node.name,
                    "trust": node.trust_score,
                    "vouched_by": list(node.vouched_by),
                    "has_vouched": list(node.has_vouched)
                }
                for nid, node in self.nodes.items()
            },
            "vouches": [
                {"from": v.voucher_id, "to": v.vouchee_id, "weight": v.weight}
                for v in self.vouches
            ]
        }


def create_trust_chain(names: List[str], decay: float = 0.85) -> TrustGraphFixture:
    """
    Create a linear trust chain: A → B → C → D

    Args:
        names: List of node names (first is genesis)
        decay: Trust decay factor

    Returns:
        TrustGraphFixture with chain configured
    """
    fixture = TrustGraphFixture(trust_decay=decay)

    # Create nodes
    for name in names:
        fixture.create_node(name, name)

    # Create vouches
    for i in range(len(names) - 1):
        fixture.create_vouch(names[i], names[i + 1])

    return fixture


def create_disjoint_communities(
    community_sizes: List[int],
    decay: float = 0.85
) -> TrustGraphFixture:
    """
    Create multiple disjoint communities with no trust paths between them

    Args:
        community_sizes: List of sizes for each community
        decay: Trust decay factor

    Returns:
        TrustGraphFixture with disjoint communities
    """
    fixture = TrustGraphFixture(trust_decay=decay)

    node_counter = 0

    for comm_idx, size in enumerate(community_sizes):
        # Create genesis for this community
        genesis_id = f"Community{comm_idx}_Genesis"
        fixture.create_node(genesis_id, genesis_id)

        # Create members
        for i in range(size - 1):
            member_id = f"Community{comm_idx}_Member{i}"
            fixture.create_node(member_id, member_id)
            fixture.create_vouch(genesis_id, member_id)

    return fixture


def create_ring_topology(names: List[str], decay: float = 0.85) -> TrustGraphFixture:
    """
    Create a ring topology: A → B → C → D → A

    Args:
        names: List of node names
        decay: Trust decay factor

    Returns:
        TrustGraphFixture with ring configured
    """
    fixture = TrustGraphFixture(trust_decay=decay)

    # Create nodes
    for name in names:
        fixture.create_node(name, name)

    # Create ring
    for i in range(len(names)):
        voucher = names[i]
        vouchee = names[(i + 1) % len(names)]
        fixture.create_vouch(voucher, vouchee)

    return fixture


def create_star_topology(
    center_name: str,
    spoke_names: List[str],
    decay: float = 0.85
) -> TrustGraphFixture:
    """
    Create a star topology: Center vouches for all spokes

    Args:
        center_name: Name of center node (genesis)
        spoke_names: Names of spoke nodes
        decay: Trust decay factor

    Returns:
        TrustGraphFixture with star configured
    """
    fixture = TrustGraphFixture(trust_decay=decay)

    # Create center
    fixture.create_node(center_name, center_name)

    # Create spokes and vouch for them
    for spoke in spoke_names:
        fixture.create_node(spoke, spoke)
        fixture.create_vouch(center_name, spoke)

    return fixture
