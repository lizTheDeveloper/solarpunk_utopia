"""
Tests for Mode Detector

Tests mesh mode detection and fallback behavior.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from ..services.mode_detector import (
    ModeDetector,
    MeshMode,
    ModeStatus
)


@pytest.fixture
def mode_detector():
    """Create a mode detector instance"""
    return ModeDetector(check_interval=0.1)  # Fast checking for tests


class TestModeDetector:
    """Test ModeDetector service"""

    @pytest.mark.asyncio
    async def test_starts_in_mode_c(self, mode_detector):
        """Test that mode detector always starts in Mode C"""
        assert mode_detector.get_current_mode() == MeshMode.MODE_C

    @pytest.mark.asyncio
    async def test_mode_a_detection_no_module(self, mode_detector):
        """Test Mode A detection when module not loaded"""
        with patch.object(mode_detector, '_check_batman_module', return_value=False):
            status = await mode_detector.check_mode_a()

        assert status.available is False
        assert "module not loaded" in status.details

    @pytest.mark.asyncio
    async def test_mode_a_detection_no_interface(self, mode_detector):
        """Test Mode A detection when interface doesn't exist"""
        with patch.object(mode_detector, '_check_batman_module', return_value=True):
            with patch.object(mode_detector, '_find_batman_interface', return_value=None):
                status = await mode_detector.check_mode_a()

        assert status.available is False
        assert "not found" in status.details

    @pytest.mark.asyncio
    async def test_mode_a_detection_interface_down(self, mode_detector):
        """Test Mode A detection when interface is down"""
        with patch.object(mode_detector, '_check_batman_module', return_value=True):
            with patch.object(mode_detector, '_find_batman_interface', return_value="bat0"):
                with patch.object(mode_detector, '_check_interface_up', return_value=False):
                    status = await mode_detector.check_mode_a()

        assert status.available is False
        assert "is down" in status.details

    @pytest.mark.asyncio
    async def test_mode_a_detection_success(self, mode_detector):
        """Test Mode A detection when everything is available"""
        with patch.object(mode_detector, '_check_batman_module', return_value=True):
            with patch.object(mode_detector, '_find_batman_interface', return_value="bat0"):
                with patch.object(mode_detector, '_check_interface_up', return_value=True):
                    with patch.object(mode_detector, '_get_batman_version', return_value="2023.1"):
                        with patch.object(mode_detector, '_count_mesh_peers', return_value=3):
                            status = await mode_detector.check_mode_a()

        assert status.available is True
        assert status.batman_interface == "bat0"
        assert status.batman_version == "2023.1"
        assert status.mesh_peers == 3

    @pytest.mark.asyncio
    async def test_callback_on_mode_a_available(self, mode_detector):
        """Test callback when Mode A becomes available"""
        callback_called = False

        def on_mode_a_available():
            nonlocal callback_called
            callback_called = True

        mode_detector.on_mode_a_available = on_mode_a_available

        # Simulate Mode A becoming available
        mode_status = ModeStatus(
            mode=MeshMode.MODE_A,
            available=True,
            timestamp=datetime.now(timezone.utc),
            details="Mode A operational",
            batman_interface="bat0"
        )

        await mode_detector._handle_mode_change(mode_status)

        assert callback_called is True
        assert mode_detector.is_mode_a_available() is True

    @pytest.mark.asyncio
    async def test_callback_on_mode_a_unavailable(self, mode_detector):
        """Test callback when Mode A becomes unavailable"""
        callback_called = False

        def on_mode_a_unavailable():
            nonlocal callback_called
            callback_called = True

        mode_detector.on_mode_a_unavailable = on_mode_a_unavailable

        # First make Mode A available
        mode_detector.mode_a_available = True

        # Then simulate it becoming unavailable
        mode_status = ModeStatus(
            mode=MeshMode.MODE_A,
            available=False,
            timestamp=datetime.now(timezone.utc),
            details="Module not loaded"
        )

        await mode_detector._handle_mode_change(mode_status)

        assert callback_called is True
        assert mode_detector.is_mode_a_available() is False

    @pytest.mark.asyncio
    async def test_fallback_to_mode_c(self, mode_detector):
        """Test fallback from Mode A to Mode C"""
        # Start in Mode A
        mode_detector.current_mode = MeshMode.MODE_A
        mode_detector.mode_a_available = True

        # Trigger fallback
        await mode_detector._fallback_to_mode_c()

        assert mode_detector.get_current_mode() == MeshMode.MODE_C
        assert mode_detector.mode_a_failures > 0

    @pytest.mark.asyncio
    async def test_switch_to_mode_a(self, mode_detector):
        """Test switching to Mode A"""
        callback_called = False
        old_mode = None
        new_mode = None

        def on_mode_change(old: MeshMode, new: MeshMode):
            nonlocal callback_called, old_mode, new_mode
            callback_called = True
            old_mode = old
            new_mode = new

        mode_detector.on_mode_change = on_mode_change

        # Switch to Mode A
        await mode_detector._switch_to_mode_a()

        assert mode_detector.get_current_mode() == MeshMode.MODE_A
        assert callback_called is True
        assert old_mode == MeshMode.MODE_C
        assert new_mode == MeshMode.MODE_A

    @pytest.mark.asyncio
    async def test_force_mode_c(self, mode_detector):
        """Test manual force to Mode C"""
        mode_detector.current_mode = MeshMode.MODE_A

        await mode_detector.force_mode_c()

        assert mode_detector.get_current_mode() == MeshMode.MODE_C

    @pytest.mark.asyncio
    async def test_get_mode_status(self, mode_detector):
        """Test getting mode status"""
        mode_detector.mode_a_available = True
        mode_detector.mode_a_failures = 2

        status = mode_detector.get_mode_status()

        assert status["current_mode"] == MeshMode.MODE_C.value  # Still starts in C
        assert status["mode_c_available"] is True
        assert status["mode_a_available"] is True
        assert status["mode_a_failures"] == 2
