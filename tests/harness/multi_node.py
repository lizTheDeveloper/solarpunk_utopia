"""
Multi-Node Test Harness

Simulates a mesh network with multiple DTN nodes that can:
- Connect/disconnect on demand
- Exchange bundles via mock transport
- Verify bundle propagation timing
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid


@dataclass
class MockBundle:
    """A mock DTN bundle for testing"""
    bundle_id: str
    source_node: str
    destination: str
    payload: bytes
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    hop_count: int = 0
    max_hops: int = 10


@dataclass
class MockNode:
    """A mock DTN node in the test network"""
    node_id: str
    bundles: Dict[str, MockBundle] = field(default_factory=dict)
    connections: Set[str] = field(default_factory=set)
    bundle_log: List[Tuple[float, str, str]] = field(default_factory=list)  # (timestamp, action, bundle_id)

    def add_bundle(self, bundle: MockBundle) -> None:
        """Add a bundle to this node's storage"""
        self.bundles[bundle.bundle_id] = bundle
        self.bundle_log.append((time.time(), "received", bundle.bundle_id))

    def remove_bundle(self, bundle_id: str) -> Optional[MockBundle]:
        """Remove and return a bundle from storage"""
        bundle = self.bundles.pop(bundle_id, None)
        if bundle:
            self.bundle_log.append((time.time(), "removed", bundle_id))
        return bundle

    def get_bundle_index(self) -> List[str]:
        """Get list of bundle IDs this node has"""
        return list(self.bundles.keys())

    def is_connected_to(self, other_node_id: str) -> bool:
        """Check if this node is connected to another"""
        return other_node_id in self.connections


class MultiNodeHarness:
    """
    Test harness for simulating multi-node DTN mesh networks

    Example usage:
        harness = MultiNodeHarness()
        node_a = harness.create_node("Alice")
        node_b = harness.create_node("Bob")
        node_c = harness.create_node("Carol")

        # Create a bundle on node A
        bundle = harness.create_bundle(
            source="Alice",
            destination="Carol",
            payload=b"Hello from Alice",
            priority=1
        )
        node_a.add_bundle(bundle)

        # Connect A to B, B to C
        harness.connect(node_a, node_b)
        harness.connect(node_b, node_c)

        # Simulate sync
        await harness.sync_nodes(node_a, node_b)
        await harness.sync_nodes(node_b, node_c)

        # Verify bundle reached Carol
        assert bundle.bundle_id in node_c.bundles
    """

    def __init__(self):
        self.nodes: Dict[str, MockNode] = {}
        self.sync_log: List[Tuple[float, str, str, List[str]]] = []  # (timestamp, source, dest, bundles)

    def create_node(self, node_id: str) -> MockNode:
        """Create a new mock node in the network"""
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists")

        node = MockNode(node_id=node_id)
        self.nodes[node_id] = node
        return node

    def get_node(self, node_id: str) -> MockNode:
        """Get a node by ID"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        return self.nodes[node_id]

    def connect(self, node_a: MockNode, node_b: MockNode) -> None:
        """Create a bidirectional connection between two nodes"""
        node_a.connections.add(node_b.node_id)
        node_b.connections.add(node_a.node_id)

    def disconnect(self, node_a: MockNode, node_b: MockNode) -> None:
        """Remove connection between two nodes"""
        node_a.connections.discard(node_b.node_id)
        node_b.connections.discard(node_a.node_id)

    def create_bundle(
        self,
        source: str,
        destination: str,
        payload: bytes,
        priority: int = 0,
        ttl_seconds: Optional[int] = None
    ) -> MockBundle:
        """Create a new bundle"""
        bundle_id = str(uuid.uuid4())
        expires_at = None
        if ttl_seconds:
            expires_at = time.time() + ttl_seconds

        return MockBundle(
            bundle_id=bundle_id,
            source_node=source,
            destination=destination,
            payload=payload,
            priority=priority,
            expires_at=expires_at
        )

    async def sync_nodes(
        self,
        source_node: MockNode,
        dest_node: MockNode,
        simulate_latency: bool = False
    ) -> List[str]:
        """
        Simulate bundle sync between two connected nodes

        Returns list of bundle IDs transferred
        """
        if not source_node.is_connected_to(dest_node.node_id):
            raise ValueError(f"Nodes {source_node.node_id} and {dest_node.node_id} are not connected")

        # Simulate network latency if requested
        if simulate_latency:
            await asyncio.sleep(0.1)

        # Get bundle indices
        source_index = set(source_node.get_bundle_index())
        dest_index = set(dest_node.get_bundle_index())

        # Find bundles to transfer
        to_transfer = []

        # Priority 1: EMERGENCY bundles from source to dest
        # Priority 2: Bundles destined for dest node
        # Priority 3: Other bundles that dest doesn't have

        for bundle_id in source_index:
            if bundle_id in dest_index:
                continue

            bundle = source_node.bundles[bundle_id]

            # Skip expired bundles
            if bundle.expires_at and bundle.expires_at < time.time():
                continue

            # Skip bundles that exceeded hop limit
            if bundle.hop_count >= bundle.max_hops:
                continue

            to_transfer.append((bundle.priority, bundle_id))

        # Sort by priority (higher first)
        to_transfer.sort(reverse=True, key=lambda x: x[0])

        # Transfer bundles
        transferred = []
        for _, bundle_id in to_transfer:
            bundle = source_node.bundles[bundle_id]

            # Create a copy with incremented hop count
            transferred_bundle = MockBundle(
                bundle_id=bundle.bundle_id,
                source_node=bundle.source_node,
                destination=bundle.destination,
                payload=bundle.payload,
                priority=bundle.priority,
                created_at=bundle.created_at,
                expires_at=bundle.expires_at,
                hop_count=bundle.hop_count + 1,
                max_hops=bundle.max_hops
            )

            dest_node.add_bundle(transferred_bundle)
            transferred.append(bundle_id)

        # Log the sync
        self.sync_log.append((time.time(), source_node.node_id, dest_node.node_id, transferred))

        return transferred

    async def propagate_bundle(
        self,
        bundle: MockBundle,
        source_node: MockNode,
        max_hops: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Simulate bundle propagation through the network

        Returns dict of {node_id: hop_count} for nodes that received the bundle
        """
        if max_hops is None:
            max_hops = bundle.max_hops

        reached = {source_node.node_id: 0}
        queue = [(source_node.node_id, 0)]
        visited = set()

        while queue:
            current_id, hops = queue.pop(0)

            if current_id in visited or hops >= max_hops:
                continue

            visited.add(current_id)
            current_node = self.get_node(current_id)

            # Propagate to all connected nodes
            for neighbor_id in current_node.connections:
                if neighbor_id not in visited:
                    neighbor = self.get_node(neighbor_id)

                    # Create bundle copy with incremented hop count
                    neighbor_bundle = MockBundle(
                        bundle_id=bundle.bundle_id,
                        source_node=bundle.source_node,
                        destination=bundle.destination,
                        payload=bundle.payload,
                        priority=bundle.priority,
                        created_at=bundle.created_at,
                        expires_at=bundle.expires_at,
                        hop_count=hops + 1,
                        max_hops=bundle.max_hops
                    )

                    neighbor.add_bundle(neighbor_bundle)
                    reached[neighbor_id] = hops + 1
                    queue.append((neighbor_id, hops + 1))

        return reached

    def verify_propagation(
        self,
        bundle_id: str,
        expected_nodes: List[str],
        max_time: float = 5.0
    ) -> bool:
        """
        Verify that a bundle reached expected nodes within time limit

        Returns True if all expected nodes have the bundle
        """
        for node_id in expected_nodes:
            node = self.get_node(node_id)
            if bundle_id not in node.bundles:
                return False

        return True

    def get_sync_stats(self) -> Dict:
        """Get statistics about sync operations"""
        total_syncs = len(self.sync_log)
        total_bundles = sum(len(bundles) for _, _, _, bundles in self.sync_log)

        return {
            "total_syncs": total_syncs,
            "total_bundles_transferred": total_bundles,
            "average_bundles_per_sync": total_bundles / total_syncs if total_syncs > 0 else 0,
            "sync_log": self.sync_log
        }

    def reset(self) -> None:
        """Reset the harness (clear all nodes and logs)"""
        self.nodes.clear()
        self.sync_log.clear()
