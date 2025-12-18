"""
Bridge Node

Software components for bridge node functionality in the multi-AP mesh network.

Bridge nodes move between AP islands, carrying bundles to enable
store-and-forward communication across the mesh.
"""

from .services import (
    NetworkMonitor,
    NetworkInfo,
    NetworkStatus,
    SyncOrchestrator,
    SyncOperation,
    SyncStatus,
    BridgeMetrics,
    IslandVisit,
    BridgeSession,
    ModeDetector,
    MeshMode,
    ModeStatus,
)

from .api import router, initialize_services, shutdown_services

__all__ = [
    # Services
    "NetworkMonitor",
    "NetworkInfo",
    "NetworkStatus",
    "SyncOrchestrator",
    "SyncOperation",
    "SyncStatus",
    "BridgeMetrics",
    "IslandVisit",
    "BridgeSession",
    "ModeDetector",
    "MeshMode",
    "ModeStatus",
    # API
    "router",
    "initialize_services",
    "shutdown_services",
]
