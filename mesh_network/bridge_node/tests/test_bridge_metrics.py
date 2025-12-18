"""
Tests for Bridge Metrics

Tests bridge effectiveness tracking and metrics collection.
"""

import pytest
from datetime import datetime

from ..services.bridge_metrics import (
    BridgeMetrics,
    IslandVisit,
    BridgeSession
)


@pytest.fixture
def bridge_metrics():
    """Create a bridge metrics instance"""
    return BridgeMetrics(node_id="test_bridge")


class TestBridgeMetrics:
    """Test BridgeMetrics service"""

    def test_initialization(self, bridge_metrics):
        """Test metrics initialization"""
        assert bridge_metrics.node_id == "test_bridge"
        assert bridge_metrics.total_bundles_received == 0
        assert bridge_metrics.total_bundles_sent == 0
        assert bridge_metrics.total_syncs == 0

    def test_start_session(self, bridge_metrics):
        """Test starting a session"""
        session_id = bridge_metrics.start_session()

        assert bridge_metrics.current_session is not None
        assert bridge_metrics.current_session.session_id == session_id
        assert len(bridge_metrics.sessions) == 1

    def test_end_session(self, bridge_metrics):
        """Test ending a session"""
        bridge_metrics.start_session()
        session = bridge_metrics.current_session

        bridge_metrics.end_session()

        assert bridge_metrics.current_session is None
        assert session.ended_at is not None
        assert session.duration_hours() > 0

    def test_record_island_arrival(self, bridge_metrics):
        """Test recording island arrival"""
        bridge_metrics.record_island_arrival("garden")

        assert bridge_metrics.current_island == "garden"
        assert "garden" in bridge_metrics.total_islands_visited

    def test_record_island_departure(self, bridge_metrics):
        """Test recording island departure"""
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_island_departure()

        assert bridge_metrics.current_island is None
        assert len(bridge_metrics.island_visits) == 1
        assert bridge_metrics.island_visits[0].island_id == "garden"

    def test_record_sync(self, bridge_metrics):
        """Test recording a sync operation"""
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync(
            island_id="garden",
            bundles_received=5,
            bundles_sent=3,
            from_island=None
        )

        assert bridge_metrics.total_syncs == 1
        assert bridge_metrics.total_bundles_received == 5
        assert bridge_metrics.total_bundles_sent == 3

    def test_record_sync_with_session(self, bridge_metrics):
        """Test sync recording updates session stats"""
        bridge_metrics.start_session()
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync(
            island_id="garden",
            bundles_received=5,
            bundles_sent=3
        )

        assert bridge_metrics.current_session.total_syncs == 1
        assert bridge_metrics.current_session.total_bundles_carried == 8

    def test_island_pair_tracking(self, bridge_metrics):
        """Test tracking bundles between island pairs"""
        # Arrive at garden
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync("garden", 5, 0)

        # Move to kitchen and forward bundles from garden
        bridge_metrics.record_island_arrival("kitchen")
        bridge_metrics.record_sync(
            island_id="kitchen",
            bundles_received=3,
            bundles_sent=5,
            from_island="garden"
        )

        # Check transport matrix
        matrix = bridge_metrics.get_transport_matrix()
        assert matrix["garden"]["kitchen"] == 5

    def test_effectiveness_score_island_coverage(self, bridge_metrics):
        """Test effectiveness score increases with island coverage"""
        # Visit one island
        bridge_metrics.record_island_arrival("garden")
        score_one = bridge_metrics.get_effectiveness_score()

        # Visit more islands
        bridge_metrics.record_island_arrival("kitchen")
        bridge_metrics.record_island_arrival("workshop")
        bridge_metrics.record_island_arrival("library")
        score_four = bridge_metrics.get_effectiveness_score()

        # More islands should increase score
        assert score_four > score_one

    def test_effectiveness_score_bundle_volume(self, bridge_metrics):
        """Test effectiveness score increases with bundle volume"""
        bridge_metrics.record_island_arrival("garden")

        score_before = bridge_metrics.get_effectiveness_score()

        # Transport many bundles
        for _ in range(10):
            bridge_metrics.record_sync("garden", 10, 10)

        score_after = bridge_metrics.get_effectiveness_score()

        assert score_after > score_before

    def test_get_island_stats(self, bridge_metrics):
        """Test getting per-island statistics"""
        # Visit garden twice
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync("garden", 5, 3)
        bridge_metrics.record_island_departure()

        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync("garden", 2, 1)
        bridge_metrics.record_island_departure()

        stats = bridge_metrics.get_island_stats()

        assert "garden" in stats
        assert stats["garden"]["visits"] == 2
        assert stats["garden"]["bundles_received"] == 7
        assert stats["garden"]["bundles_sent"] == 4

    def test_get_summary(self, bridge_metrics):
        """Test getting comprehensive summary"""
        bridge_metrics.start_session()
        bridge_metrics.record_island_arrival("garden")
        bridge_metrics.record_sync("garden", 5, 3)
        bridge_metrics.record_island_arrival("kitchen")
        bridge_metrics.record_sync("kitchen", 2, 5, from_island="garden")

        summary = bridge_metrics.get_summary()

        assert summary["node_id"] == "test_bridge"
        assert summary["totals"]["syncs"] == 2
        assert summary["totals"]["bundles_received"] == 7
        assert summary["totals"]["bundles_sent"] == 8
        assert summary["totals"]["islands_visited"] == 2
        assert summary["current_island"] == "kitchen"
        assert "effectiveness_score" in summary
