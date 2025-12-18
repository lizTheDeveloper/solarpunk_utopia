"""
Mode Detector Service

Detects which mesh mode is available:
- Mode C (DTN-Only): Always available (foundation)
- Mode A (BATMAN-adv): Available if kernel module present
- Mode B (Wi-Fi Direct): Future research (not implemented)

Handles graceful degradation from Mode A to Mode C.
"""

import asyncio
import logging
import subprocess
from typing import Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MeshMode(Enum):
    """Available mesh modes"""
    MODE_C = "mode_c"  # DTN-only, store-and-forward (always available)
    MODE_A = "mode_a"  # BATMAN-adv multi-hop routing (requires kernel support)
    MODE_B = "mode_b"  # Wi-Fi Direct (future research)
    UNKNOWN = "unknown"


@dataclass
class ModeStatus:
    """Current mode status"""
    mode: MeshMode
    available: bool
    timestamp: datetime
    details: str
    batman_interface: Optional[str] = None
    batman_version: Optional[str] = None
    mesh_peers: int = 0

    def to_dict(self):
        return {
            "mode": self.mode.value,
            "available": self.available,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "batman_interface": self.batman_interface,
            "batman_version": self.batman_version,
            "mesh_peers": self.mesh_peers
        }


class ModeDetector:
    """
    Detects available mesh modes and monitors mode health.

    Mode C (DTN-only) is always available and is the foundation.
    Mode A (BATMAN-adv) is detected by checking for kernel module and interface.

    Responsibilities:
    - Detect Mode A availability
    - Monitor Mode A health (routing, peers)
    - Trigger fallback to Mode C when Mode A fails
    - Attempt recovery when Mode A becomes available again
    """

    def __init__(self, check_interval: float = 30.0):
        """
        Initialize mode detector.

        Args:
            check_interval: How often to check mode status (seconds)
        """
        self.check_interval = check_interval
        self.current_mode = MeshMode.MODE_C  # Always start in Mode C
        self.mode_a_available = False
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Callbacks
        self.on_mode_change: Optional[Callable[[MeshMode, MeshMode], None]] = None
        self.on_mode_a_available: Optional[Callable[[], None]] = None
        self.on_mode_a_unavailable: Optional[Callable[[], None]] = None

        # Status tracking
        self.last_status: Optional[ModeStatus] = None
        self.mode_a_failures = 0
        self.mode_c_always_available = True

    async def start(self):
        """Start monitoring mesh modes"""
        if self.is_running:
            logger.warning("Mode detector already running")
            return

        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Mode detector started (check interval: {self.check_interval}s)")

    async def stop(self):
        """Stop monitoring mesh modes"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Mode detector stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Check Mode A availability
                mode_a_status = await self.check_mode_a()

                # Update state and trigger callbacks if changed
                await self._handle_mode_change(mode_a_status)

                self.last_status = mode_a_status

            except Exception as e:
                logger.error(f"Error in mode detector loop: {e}")

            await asyncio.sleep(self.check_interval)

    async def check_mode_a(self) -> ModeStatus:
        """
        Check if Mode A (BATMAN-adv) is available.

        Checks:
        1. batman-adv kernel module loaded
        2. bat0 interface exists
        3. Interface is up
        4. Can see mesh peers

        Returns:
            ModeStatus indicating Mode A availability
        """
        try:
            # Check 1: Is batman-adv module loaded?
            module_loaded = await self._check_batman_module()
            if not module_loaded:
                return ModeStatus(
                    mode=MeshMode.MODE_A,
                    available=False,
                    timestamp=datetime.utcnow(),
                    details="batman-adv kernel module not loaded"
                )

            # Check 2: Does bat0 interface exist?
            interface = await self._find_batman_interface()
            if not interface:
                return ModeStatus(
                    mode=MeshMode.MODE_A,
                    available=False,
                    timestamp=datetime.utcnow(),
                    details="batman-adv interface (bat0) not found"
                )

            # Check 3: Is interface up?
            interface_up = await self._check_interface_up(interface)
            if not interface_up:
                return ModeStatus(
                    mode=MeshMode.MODE_A,
                    available=False,
                    timestamp=datetime.utcnow(),
                    details=f"batman-adv interface {interface} is down",
                    batman_interface=interface
                )

            # Check 4: Get version and peer count
            version = await self._get_batman_version()
            peers = await self._count_mesh_peers(interface)

            # Mode A is available
            return ModeStatus(
                mode=MeshMode.MODE_A,
                available=True,
                timestamp=datetime.utcnow(),
                details="Mode A (BATMAN-adv) operational",
                batman_interface=interface,
                batman_version=version,
                mesh_peers=peers
            )

        except Exception as e:
            logger.error(f"Error checking Mode A: {e}")
            return ModeStatus(
                mode=MeshMode.MODE_A,
                available=False,
                timestamp=datetime.utcnow(),
                details=f"Error checking Mode A: {str(e)}"
            )

    async def _check_batman_module(self) -> bool:
        """Check if batman-adv kernel module is loaded"""
        try:
            result = subprocess.run(
                ["lsmod"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                return "batman_adv" in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return False

    async def _find_batman_interface(self) -> Optional[str]:
        """Find batman-adv interface (usually bat0)"""
        try:
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "bat0:" in line or "batadv" in line:
                        # Extract interface name
                        parts = line.split(":")
                        if len(parts) >= 2:
                            return parts[1].strip()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    async def _check_interface_up(self, interface: str) -> bool:
        """Check if interface is up"""
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                return "UP" in result.stdout and "state UP" in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return False

    async def _get_batman_version(self) -> Optional[str]:
        """Get batman-adv version"""
        try:
            result = subprocess.run(
                ["batctl", "-v"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Extract version from output
                lines = result.stdout.strip().split("\n")
                if lines:
                    return lines[0]

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    async def _count_mesh_peers(self, interface: str) -> int:
        """Count mesh peers visible via batman-adv"""
        try:
            result = subprocess.run(
                ["batctl", "meshif", interface, "neighbors"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Count non-header lines
                lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith("[")]
                return len(lines)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return 0

    async def _handle_mode_change(self, new_status: ModeStatus):
        """Handle mode availability changes"""
        old_available = self.mode_a_available
        new_available = new_status.available

        # Mode A became available
        if not old_available and new_available:
            logger.info("Mode A (BATMAN-adv) now available")
            self.mode_a_available = True
            self.mode_a_failures = 0

            if self.on_mode_a_available:
                try:
                    await self._run_callback(self.on_mode_a_available)
                except Exception as e:
                    logger.error(f"Error in mode_a_available callback: {e}")

            # Potentially switch to Mode A
            await self._switch_to_mode_a()

        # Mode A became unavailable
        elif old_available and not new_available:
            logger.warning("Mode A (BATMAN-adv) no longer available")
            self.mode_a_available = False
            self.mode_a_failures += 1

            if self.on_mode_a_unavailable:
                try:
                    await self._run_callback(self.on_mode_a_unavailable)
                except Exception as e:
                    logger.error(f"Error in mode_a_unavailable callback: {e}")

            # Fallback to Mode C
            await self._fallback_to_mode_c()

    async def _switch_to_mode_a(self):
        """Switch from Mode C to Mode A"""
        if self.current_mode == MeshMode.MODE_A:
            return  # Already in Mode A

        old_mode = self.current_mode
        self.current_mode = MeshMode.MODE_A

        logger.info("Switched to Mode A (BATMAN-adv multi-hop routing)")

        if self.on_mode_change:
            try:
                await self._run_callback(self.on_mode_change, old_mode, MeshMode.MODE_A)
            except Exception as e:
                logger.error(f"Error in mode_change callback: {e}")

    async def _fallback_to_mode_c(self):
        """Fallback from Mode A to Mode C"""
        if self.current_mode == MeshMode.MODE_C:
            return  # Already in Mode C

        old_mode = self.current_mode
        self.current_mode = MeshMode.MODE_C

        logger.warning(
            f"Falling back to Mode C (DTN-only) due to Mode A failure "
            f"(failure count: {self.mode_a_failures})"
        )

        if self.on_mode_change:
            try:
                await self._run_callback(self.on_mode_change, old_mode, MeshMode.MODE_C)
            except Exception as e:
                logger.error(f"Error in mode_change callback: {e}")

    async def _run_callback(self, callback: Callable, *args):
        """Run callback, handling both sync and async functions"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)

    def get_current_mode(self) -> MeshMode:
        """Get current active mode"""
        return self.current_mode

    def is_mode_a_available(self) -> bool:
        """Check if Mode A is currently available"""
        return self.mode_a_available

    def get_mode_status(self) -> dict:
        """
        Get comprehensive mode status.

        Returns:
            Dictionary with mode information
        """
        return {
            "current_mode": self.current_mode.value,
            "mode_c_available": self.mode_c_always_available,
            "mode_a_available": self.mode_a_available,
            "mode_a_failures": self.mode_a_failures,
            "last_check": self.last_status.to_dict() if self.last_status else None
        }

    async def force_mode_c(self):
        """Force fallback to Mode C (for testing or manual override)"""
        logger.info("Forcing Mode C (manual override)")
        await self._fallback_to_mode_c()

    async def attempt_mode_a(self):
        """Attempt to enable Mode A (for testing or manual recovery)"""
        logger.info("Attempting to enable Mode A (manual trigger)")
        status = await self.check_mode_a()
        if status.available:
            await self._switch_to_mode_a()
        else:
            logger.warning(f"Cannot enable Mode A: {status.details}")
