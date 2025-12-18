"""
Network Monitor Service

Detects network changes (AP transitions) for bridge nodes.
Monitors SSID changes and triggers sync events when moving between islands.
"""

import asyncio
import logging
import subprocess
import re
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NetworkStatus(Enum):
    """Network connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    UNKNOWN = "unknown"


@dataclass
class NetworkInfo:
    """Information about current network connection"""
    ssid: Optional[str]
    bssid: Optional[str]
    ip_address: Optional[str]
    gateway: Optional[str]
    subnet: Optional[str]
    island_id: Optional[str]
    status: NetworkStatus
    timestamp: datetime
    signal_strength: Optional[int] = None

    def is_solarpunk_network(self) -> bool:
        """Check if connected to a Solarpunk mesh network"""
        if not self.ssid:
            return False
        return self.ssid.startswith("Solarpunk")

    def extract_island_id(self) -> Optional[str]:
        """Extract island ID from SSID (e.g., 'SolarpunkGarden' -> 'garden')"""
        if not self.ssid or not self.is_solarpunk_network():
            return None

        # Remove 'Solarpunk' prefix and convert to lowercase
        island = self.ssid.replace("Solarpunk", "").lower()
        return island if island else None


class NetworkMonitor:
    """
    Monitors network connectivity and detects AP transitions.

    Designed for bridge nodes that move between islands. Detects:
    - Connection to new AP
    - Disconnection from current AP
    - Network parameter changes (IP, gateway, etc.)

    Triggers callbacks when transitions occur.
    """

    def __init__(self, poll_interval: float = 5.0):
        """
        Initialize network monitor.

        Args:
            poll_interval: How often to check network status (seconds)
        """
        self.poll_interval = poll_interval
        self.current_network: Optional[NetworkInfo] = None
        self.previous_network: Optional[NetworkInfo] = None
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Callbacks for network events
        self.on_connect: Optional[Callable[[NetworkInfo], None]] = None
        self.on_disconnect: Optional[Callable[[NetworkInfo], None]] = None
        self.on_ap_transition: Optional[Callable[[NetworkInfo, NetworkInfo], None]] = None

    async def start(self):
        """Start monitoring network changes"""
        if self.is_running:
            logger.warning("Network monitor already running")
            return

        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Network monitor started (poll interval: {self.poll_interval}s)")

    async def stop(self):
        """Stop monitoring network changes"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Network monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Get current network info
                network_info = await self._get_network_info()

                # Check for changes
                await self._handle_network_change(network_info)

                # Update state
                self.previous_network = self.current_network
                self.current_network = network_info

            except Exception as e:
                logger.error(f"Error in network monitor loop: {e}")

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

    async def _get_network_info(self) -> NetworkInfo:
        """
        Get current network information.

        Uses platform-specific commands to detect network state.
        Supports Linux (Android/Termux) and macOS.
        """
        try:
            # Try to get SSID and connection info
            ssid = await self._get_ssid()
            ip_info = await self._get_ip_info()

            if ssid and ip_info.get("ip_address"):
                status = NetworkStatus.CONNECTED
            else:
                status = NetworkStatus.DISCONNECTED

            network_info = NetworkInfo(
                ssid=ssid,
                bssid=ip_info.get("bssid"),
                ip_address=ip_info.get("ip_address"),
                gateway=ip_info.get("gateway"),
                subnet=ip_info.get("subnet"),
                island_id=None,  # Will be set below
                status=status,
                timestamp=datetime.utcnow(),
                signal_strength=ip_info.get("signal_strength")
            )

            # Extract island ID from SSID
            network_info.island_id = network_info.extract_island_id()

            return network_info

        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return NetworkInfo(
                ssid=None,
                bssid=None,
                ip_address=None,
                gateway=None,
                subnet=None,
                island_id=None,
                status=NetworkStatus.UNKNOWN,
                timestamp=datetime.utcnow()
            )

    async def _get_ssid(self) -> Optional[str]:
        """Get current WiFi SSID"""
        try:
            # Try Linux/Android (Termux) first
            result = subprocess.run(
                ["termux-wifi-connectioninfo"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Parse JSON output from termux-wifi-connectioninfo
                import json
                info = json.loads(result.stdout)
                return info.get("ssid", "").strip('"')

        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass

        try:
            # Try macOS
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if " SSID:" in line:
                        return line.split("SSID:")[1].strip()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            # Try Linux iwgetid
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    async def _get_ip_info(self) -> Dict[str, Any]:
        """Get IP address, gateway, and other network info"""
        info = {}

        try:
            # Get IP address and subnet
            result = subprocess.run(
                ["ip", "addr", "show"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Look for wlan0 or similar wireless interface
                for line in result.stdout.split("\n"):
                    if "inet " in line and ("wlan" in line or "wlp" in line):
                        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", line)
                        if match:
                            info["ip_address"] = match.group(1)
                            info["subnet"] = f"/{match.group(2)}"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            # Get gateway
            result = subprocess.run(
                ["ip", "route", "show"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "default via" in line:
                        match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", line)
                        if match:
                            info["gateway"] = match.group(1)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return info

    async def _handle_network_change(self, new_network: NetworkInfo):
        """
        Handle network state changes and trigger appropriate callbacks.

        Detects:
        - New connection (was disconnected, now connected)
        - Disconnection (was connected, now disconnected)
        - AP transition (connected to different SSID)
        """
        if not self.current_network:
            # First run, just store state
            return

        old = self.current_network
        new = new_network

        # Detect disconnection
        if old.status == NetworkStatus.CONNECTED and new.status != NetworkStatus.CONNECTED:
            logger.info(f"Disconnected from {old.ssid}")
            if self.on_disconnect:
                try:
                    await self._run_callback(self.on_disconnect, old)
                except Exception as e:
                    logger.error(f"Error in disconnect callback: {e}")

        # Detect new connection
        elif old.status != NetworkStatus.CONNECTED and new.status == NetworkStatus.CONNECTED:
            logger.info(f"Connected to {new.ssid} ({new.ip_address})")
            if self.on_connect:
                try:
                    await self._run_callback(self.on_connect, new)
                except Exception as e:
                    logger.error(f"Error in connect callback: {e}")

        # Detect AP transition (SSID change while connected)
        elif (old.status == NetworkStatus.CONNECTED and
              new.status == NetworkStatus.CONNECTED and
              old.ssid != new.ssid):

            logger.info(f"AP transition: {old.ssid} -> {new.ssid}")

            # Only trigger for Solarpunk networks
            if new.is_solarpunk_network():
                logger.info(f"Island transition: {old.island_id} -> {new.island_id}")
                if self.on_ap_transition:
                    try:
                        await self._run_callback(self.on_ap_transition, old, new)
                    except Exception as e:
                        logger.error(f"Error in AP transition callback: {e}")

    async def _run_callback(self, callback: Callable, *args):
        """Run callback, handling both sync and async functions"""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)

    def get_current_network(self) -> Optional[NetworkInfo]:
        """Get current network information"""
        return self.current_network

    def is_connected(self) -> bool:
        """Check if currently connected to a network"""
        return (self.current_network is not None and
                self.current_network.status == NetworkStatus.CONNECTED)

    def is_on_solarpunk_network(self) -> bool:
        """Check if connected to a Solarpunk mesh network"""
        return (self.is_connected() and
                self.current_network.is_solarpunk_network())

    def get_current_island(self) -> Optional[str]:
        """Get current island ID (e.g., 'garden', 'kitchen')"""
        if self.current_network:
            return self.current_network.island_id
        return None
