"""
Tests for Network Monitor

Tests network detection and AP transition detection.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ..services.network_monitor import (
    NetworkMonitor,
    NetworkInfo,
    NetworkStatus
)


@pytest.fixture
def network_monitor():
    """Create a network monitor instance"""
    monitor = NetworkMonitor(poll_interval=0.1)  # Fast polling for tests
    return monitor


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
        timestamp=datetime.utcnow()
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
        timestamp=datetime.utcnow()
    )


class TestNetworkInfo:
    """Test NetworkInfo data class"""

    def test_is_solarpunk_network(self, garden_network):
        """Test Solarpunk network detection"""
        assert garden_network.is_solarpunk_network() is True

        # Non-Solarpunk network
        other_network = NetworkInfo(
            ssid="SomeOtherNetwork",
            bssid=None,
            ip_address=None,
            gateway=None,
            subnet=None,
            island_id=None,
            status=NetworkStatus.CONNECTED,
            timestamp=datetime.utcnow()
        )
        assert other_network.is_solarpunk_network() is False

    def test_extract_island_id(self, garden_network, kitchen_network):
        """Test island ID extraction from SSID"""
        assert garden_network.extract_island_id() == "garden"
        assert kitchen_network.extract_island_id() == "kitchen"

        # Non-Solarpunk network
        other_network = NetworkInfo(
            ssid="SomeOtherNetwork",
            bssid=None,
            ip_address=None,
            gateway=None,
            subnet=None,
            island_id=None,
            status=NetworkStatus.CONNECTED,
            timestamp=datetime.utcnow()
        )
        assert other_network.extract_island_id() is None


class TestNetworkMonitor:
    """Test NetworkMonitor service"""

    @pytest.mark.asyncio
    async def test_start_stop(self, network_monitor):
        """Test starting and stopping the monitor"""
        assert network_monitor.is_running is False

        await network_monitor.start()
        assert network_monitor.is_running is True

        await network_monitor.stop()
        assert network_monitor.is_running is False

    @pytest.mark.asyncio
    async def test_callback_on_connect(self, network_monitor, garden_network):
        """Test callback triggered on network connection"""
        callback_called = False
        received_network = None

        def on_connect(network: NetworkInfo):
            nonlocal callback_called, received_network
            callback_called = True
            received_network = network

        network_monitor.on_connect = on_connect

        # Simulate network change
        network_monitor.current_network = NetworkInfo(
            ssid=None,
            bssid=None,
            ip_address=None,
            gateway=None,
            subnet=None,
            island_id=None,
            status=NetworkStatus.DISCONNECTED,
            timestamp=datetime.utcnow()
        )

        await network_monitor._handle_network_change(garden_network)

        assert callback_called is True
        assert received_network.ssid == "SolarpunkGarden"

    @pytest.mark.asyncio
    async def test_callback_on_disconnect(self, network_monitor, garden_network):
        """Test callback triggered on network disconnection"""
        callback_called = False

        def on_disconnect(network: NetworkInfo):
            nonlocal callback_called
            callback_called = True

        network_monitor.on_disconnect = on_disconnect

        # Start connected
        network_monitor.current_network = garden_network

        # Simulate disconnection
        disconnected_network = NetworkInfo(
            ssid=None,
            bssid=None,
            ip_address=None,
            gateway=None,
            subnet=None,
            island_id=None,
            status=NetworkStatus.DISCONNECTED,
            timestamp=datetime.utcnow()
        )

        await network_monitor._handle_network_change(disconnected_network)

        assert callback_called is True

    @pytest.mark.asyncio
    async def test_callback_on_ap_transition(
        self,
        network_monitor,
        garden_network,
        kitchen_network
    ):
        """Test callback triggered on AP transition"""
        callback_called = False
        old_network_received = None
        new_network_received = None

        def on_transition(old: NetworkInfo, new: NetworkInfo):
            nonlocal callback_called, old_network_received, new_network_received
            callback_called = True
            old_network_received = old
            new_network_received = new

        network_monitor.on_ap_transition = on_transition

        # Start on garden network
        network_monitor.current_network = garden_network

        # Transition to kitchen
        await network_monitor._handle_network_change(kitchen_network)

        assert callback_called is True
        assert old_network_received.island_id == "garden"
        assert new_network_received.island_id == "kitchen"

    def test_get_current_island(self, network_monitor, garden_network):
        """Test getting current island ID"""
        network_monitor.current_network = garden_network
        assert network_monitor.get_current_island() == "garden"

    def test_is_connected(self, network_monitor, garden_network):
        """Test connection status check"""
        network_monitor.current_network = None
        assert network_monitor.is_connected() is False

        network_monitor.current_network = garden_network
        assert network_monitor.is_connected() is True

    def test_is_on_solarpunk_network(self, network_monitor, garden_network):
        """Test Solarpunk network detection"""
        network_monitor.current_network = garden_network
        assert network_monitor.is_on_solarpunk_network() is True

        # Non-Solarpunk network
        other_network = NetworkInfo(
            ssid="SomeOtherNetwork",
            bssid=None,
            ip_address="192.168.1.100",
            gateway="192.168.1.1",
            subnet="/24",
            island_id=None,
            status=NetworkStatus.CONNECTED,
            timestamp=datetime.utcnow()
        )
        network_monitor.current_network = other_network
        assert network_monitor.is_on_solarpunk_network() is False
