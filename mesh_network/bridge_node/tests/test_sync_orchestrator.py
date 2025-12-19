"""
Tests for Sync Orchestrator

Tests sync triggering and coordination with DTN system.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
import httpx

from ..services.sync_orchestrator import (
    SyncOrchestrator,
    SyncOperation,
    SyncStatus
)
from ..services.network_monitor import NetworkInfo, NetworkStatus


@pytest.fixture
def sync_orchestrator():
    """Create a sync orchestrator instance"""
    return SyncOrchestrator(
        dtn_base_url="http://localhost:8000",
        sync_timeout=10,
        max_bundles_per_sync=100
    )


@pytest.fixture
def garden_network():
    """Sample network info for Garden AP"""
    return NetworkInfo(
        ssid="SolarpunkGarden",
        bssid="00:11:22:33:44:55",
        ip_address="10.44.1.42",
        gateway="10.44.1.1",
        subnet="/24",
        island_id="garden",
        status=NetworkStatus.CONNECTED,
        timestamp=datetime.now(timezone.utc)
    )


@pytest.fixture
def kitchen_network():
    """Sample network info for Kitchen AP"""
    return NetworkInfo(
        ssid="SolarpunkKitchen",
        bssid="00:11:22:33:44:66",
        ip_address="10.44.2.42",
        gateway="10.44.2.1",
        subnet="/24",
        island_id="kitchen",
        status=NetworkStatus.CONNECTED,
        timestamp=datetime.now(timezone.utc)
    )


class TestSyncOrchestrator:
    """Test SyncOrchestrator service"""

    @pytest.mark.asyncio
    async def test_sync_counter_increments(self, sync_orchestrator, garden_network, kitchen_network):
        """Test that sync counter increments"""
        initial_counter = sync_orchestrator.sync_counter

        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            with patch.object(sync_orchestrator, '_push_bundles', new_callable=AsyncMock) as mock_push:
                mock_pull.return_value = 5
                mock_push.return_value = 3

                await sync_orchestrator.sync_on_ap_transition(garden_network, kitchen_network)

        assert sync_orchestrator.sync_counter == initial_counter + 1

    @pytest.mark.asyncio
    async def test_sync_records_created(self, sync_orchestrator, garden_network, kitchen_network):
        """Test that sync operations are recorded"""
        initial_count = len(sync_orchestrator.sync_history)

        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            with patch.object(sync_orchestrator, '_push_bundles', new_callable=AsyncMock) as mock_push:
                mock_pull.return_value = 5
                mock_push.return_value = 3

                sync_op = await sync_orchestrator.sync_on_ap_transition(garden_network, kitchen_network)

        assert len(sync_orchestrator.sync_history) == initial_count + 1
        assert sync_op.island_id == "kitchen"
        assert sync_op.status == SyncStatus.COMPLETED
        assert sync_op.bundles_received == 5
        assert sync_op.bundles_sent == 3

    @pytest.mark.asyncio
    async def test_sync_handles_errors(self, sync_orchestrator, garden_network, kitchen_network):
        """Test that sync handles errors gracefully"""
        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            mock_pull.side_effect = Exception("Network error")

            sync_op = await sync_orchestrator.sync_on_ap_transition(garden_network, kitchen_network)

        assert sync_op.status == SyncStatus.FAILED
        assert "Network error" in sync_op.error_message

    @pytest.mark.asyncio
    async def test_get_sync_stats(self, sync_orchestrator, garden_network, kitchen_network):
        """Test getting sync statistics"""
        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            with patch.object(sync_orchestrator, '_push_bundles', new_callable=AsyncMock) as mock_push:
                mock_pull.return_value = 5
                mock_push.return_value = 3

                await sync_orchestrator.sync_on_ap_transition(garden_network, kitchen_network)

        stats = await sync_orchestrator.get_sync_stats()

        assert stats["total_syncs"] == 1
        assert stats["completed_syncs"] == 1
        assert stats["total_bundles_received"] == 5
        assert stats["total_bundles_sent"] == 3
        assert stats["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_recent_syncs(self, sync_orchestrator, garden_network, kitchen_network):
        """Test getting recent sync history"""
        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            with patch.object(sync_orchestrator, '_push_bundles', new_callable=AsyncMock) as mock_push:
                mock_pull.return_value = 5
                mock_push.return_value = 3

                # Perform multiple syncs
                await sync_orchestrator.sync_on_ap_transition(garden_network, kitchen_network)
                await sync_orchestrator.sync_on_ap_transition(kitchen_network, garden_network)

        recent = sync_orchestrator.get_recent_syncs(limit=5)

        assert len(recent) == 2
        assert recent[0]["island_id"] == "garden"  # Most recent first
        assert recent[1]["island_id"] == "kitchen"

    @pytest.mark.asyncio
    async def test_manual_sync(self, sync_orchestrator, garden_network):
        """Test manual sync trigger"""
        with patch.object(sync_orchestrator, '_pull_bundles', new_callable=AsyncMock) as mock_pull:
            with patch.object(sync_orchestrator, '_push_bundles', new_callable=AsyncMock) as mock_push:
                mock_pull.return_value = 3
                mock_push.return_value = 2

                sync_op = await sync_orchestrator.manual_sync(garden_network)

        assert sync_op.island_id == "garden"
        assert sync_op.status == SyncStatus.COMPLETED
        assert sync_op.bundles_received == 3
        assert sync_op.bundles_sent == 2
