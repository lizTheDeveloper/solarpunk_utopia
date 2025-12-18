"""
Bridge Node Management API

FastAPI endpoints for managing bridge node functionality:
- Network status
- Sync operations
- Bridge metrics
- Mode detection and control
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..services import (
    NetworkMonitor,
    SyncOrchestrator,
    BridgeMetrics,
    ModeDetector,
    NetworkInfo,
    MeshMode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bridge", tags=["bridge"])


# Global service instances (initialized by main app)
network_monitor: Optional[NetworkMonitor] = None
sync_orchestrator: Optional[SyncOrchestrator] = None
bridge_metrics: Optional[BridgeMetrics] = None
mode_detector: Optional[ModeDetector] = None


# Request/Response Models
class BridgeStatusResponse(BaseModel):
    """Overall bridge node status"""
    is_active: bool
    current_island: Optional[str]
    current_mode: str
    network_connected: bool
    sync_in_progress: bool
    effectiveness_score: float


class NetworkStatusResponse(BaseModel):
    """Current network connection status"""
    ssid: Optional[str]
    island_id: Optional[str]
    ip_address: Optional[str]
    gateway: Optional[str]
    is_solarpunk_network: bool
    status: str


class ManualSyncRequest(BaseModel):
    """Request to manually trigger sync"""
    island_id: Optional[str] = None


class ModeControlRequest(BaseModel):
    """Request to control mesh mode"""
    action: str  # "force_mode_c", "attempt_mode_a"


# Service initialization
async def initialize_services(
    node_id: str = "bridge_node",
    dtn_base_url: str = "http://localhost:8000"
):
    """
    Initialize bridge node services.

    Call this from the main FastAPI app startup.
    """
    global network_monitor, sync_orchestrator, bridge_metrics, mode_detector

    logger.info("Initializing bridge node services...")

    # Initialize services
    network_monitor = NetworkMonitor(poll_interval=5.0)
    sync_orchestrator = SyncOrchestrator(dtn_base_url=dtn_base_url)
    bridge_metrics = BridgeMetrics(node_id=node_id)
    mode_detector = ModeDetector(check_interval=30.0)

    # Wire up callbacks
    async def on_ap_transition(old_network: NetworkInfo, new_network: NetworkInfo):
        """Handle AP transition"""
        logger.info(f"AP transition detected: {old_network.island_id} -> {new_network.island_id}")

        # Record arrival at new island
        if new_network.island_id:
            bridge_metrics.record_island_arrival(new_network.island_id)

        # Trigger sync
        sync_op = await sync_orchestrator.sync_on_ap_transition(old_network, new_network)

        # Record sync metrics
        if new_network.island_id:
            bridge_metrics.record_sync(
                island_id=new_network.island_id,
                bundles_received=sync_op.bundles_received,
                bundles_sent=sync_op.bundles_sent,
                from_island=old_network.island_id
            )

    network_monitor.on_ap_transition = on_ap_transition

    # Start services
    await network_monitor.start()
    await mode_detector.start()

    # Start a bridge session
    bridge_metrics.start_session()

    logger.info("Bridge node services initialized")


async def shutdown_services():
    """
    Shutdown bridge node services.

    Call this from the main FastAPI app shutdown.
    """
    global network_monitor, sync_orchestrator, bridge_metrics, mode_detector

    logger.info("Shutting down bridge node services...")

    if network_monitor:
        await network_monitor.stop()

    if mode_detector:
        await mode_detector.stop()

    if bridge_metrics:
        bridge_metrics.end_session()

    logger.info("Bridge node services shut down")


# API Endpoints

@router.get("/status", response_model=BridgeStatusResponse)
async def get_bridge_status():
    """
    Get overall bridge node status.

    Returns high-level status including:
    - Whether bridge is active
    - Current island
    - Current mesh mode
    - Network connection status
    - Effectiveness score
    """
    if not all([network_monitor, sync_orchestrator, bridge_metrics, mode_detector]):
        raise HTTPException(status_code=503, detail="Bridge services not initialized")

    return BridgeStatusResponse(
        is_active=network_monitor.is_running,
        current_island=network_monitor.get_current_island(),
        current_mode=mode_detector.get_current_mode().value,
        network_connected=network_monitor.is_connected(),
        sync_in_progress=sync_orchestrator.current_sync is not None,
        effectiveness_score=bridge_metrics.get_effectiveness_score()
    )


@router.get("/network", response_model=NetworkStatusResponse)
async def get_network_status():
    """
    Get current network connection details.

    Returns detailed information about the current network connection,
    including SSID, IP address, island ID, etc.
    """
    if not network_monitor:
        raise HTTPException(status_code=503, detail="Network monitor not initialized")

    current_network = network_monitor.get_current_network()

    if not current_network:
        return NetworkStatusResponse(
            ssid=None,
            island_id=None,
            ip_address=None,
            gateway=None,
            is_solarpunk_network=False,
            status="disconnected"
        )

    return NetworkStatusResponse(
        ssid=current_network.ssid,
        island_id=current_network.island_id,
        ip_address=current_network.ip_address,
        gateway=current_network.gateway,
        is_solarpunk_network=current_network.is_solarpunk_network(),
        status=current_network.status.value
    )


@router.get("/metrics")
async def get_bridge_metrics():
    """
    Get comprehensive bridge metrics.

    Returns:
    - Effectiveness score
    - Total syncs, bundles carried
    - Island visit statistics
    - Transport matrix (island-to-island bundle counts)
    - Recent visits
    """
    if not bridge_metrics:
        raise HTTPException(status_code=503, detail="Bridge metrics not initialized")

    return bridge_metrics.get_summary()


@router.get("/sync/stats")
async def get_sync_stats():
    """
    Get sync operation statistics.

    Returns:
    - Total syncs (completed, failed)
    - Success rate
    - Total bundles transferred
    - Average sync duration
    - Current sync status
    """
    if not sync_orchestrator:
        raise HTTPException(status_code=503, detail="Sync orchestrator not initialized")

    return await sync_orchestrator.get_sync_stats()


@router.get("/sync/history")
async def get_sync_history(limit: int = 10):
    """
    Get recent sync operation history.

    Query parameters:
    - limit: Number of recent syncs to return (default: 10)

    Returns list of recent sync operations with details.
    """
    if not sync_orchestrator:
        raise HTTPException(status_code=503, detail="Sync orchestrator not initialized")

    return {
        "syncs": sync_orchestrator.get_recent_syncs(limit=limit)
    }


@router.post("/sync/manual")
async def trigger_manual_sync(request: ManualSyncRequest, background_tasks: BackgroundTasks):
    """
    Manually trigger a sync operation.

    Useful for testing or forcing a sync without waiting for AP transition.

    Request body:
    - island_id: Optional island ID (uses current network if not specified)

    Returns sync operation details.
    """
    if not all([network_monitor, sync_orchestrator]):
        raise HTTPException(status_code=503, detail="Required services not initialized")

    current_network = network_monitor.get_current_network()

    if not current_network or not current_network.is_solarpunk_network():
        raise HTTPException(
            status_code=400,
            detail="Not connected to Solarpunk network"
        )

    # Trigger sync in background
    async def run_sync():
        sync_op = await sync_orchestrator.manual_sync(current_network)
        logger.info(f"Manual sync completed: {sync_op.sync_id}")

    background_tasks.add_task(run_sync)

    return {
        "message": "Manual sync triggered",
        "island_id": current_network.island_id
    }


@router.get("/mode")
async def get_mode_status():
    """
    Get current mesh mode status.

    Returns:
    - Current active mode (Mode A or Mode C)
    - Mode A availability
    - Mode detection details
    - Failure count
    """
    if not mode_detector:
        raise HTTPException(status_code=503, detail="Mode detector not initialized")

    return mode_detector.get_mode_status()


@router.post("/mode/control")
async def control_mode(request: ModeControlRequest):
    """
    Control mesh mode.

    Actions:
    - force_mode_c: Force fallback to Mode C (DTN-only)
    - attempt_mode_a: Attempt to enable Mode A (BATMAN-adv)

    Useful for testing fallback behavior or manual recovery.
    """
    if not mode_detector:
        raise HTTPException(status_code=503, detail="Mode detector not initialized")

    if request.action == "force_mode_c":
        await mode_detector.force_mode_c()
        return {
            "message": "Forced fallback to Mode C",
            "current_mode": mode_detector.get_current_mode().value
        }

    elif request.action == "attempt_mode_a":
        await mode_detector.attempt_mode_a()
        return {
            "message": "Attempted Mode A activation",
            "current_mode": mode_detector.get_current_mode().value,
            "mode_a_available": mode_detector.is_mode_a_available()
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action: {request.action}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns health status of all bridge services.
    """
    services_status = {
        "network_monitor": network_monitor.is_running if network_monitor else False,
        "mode_detector": mode_detector.is_running if mode_detector else False,
        "sync_orchestrator": sync_orchestrator is not None,
        "bridge_metrics": bridge_metrics is not None
    }

    all_healthy = all(services_status.values())

    return {
        "healthy": all_healthy,
        "services": services_status
    }


@router.post("/session/start")
async def start_session(session_id: Optional[str] = None):
    """
    Start a new bridge session.

    Useful for tracking bridge activity during specific time periods
    (e.g., a particular walk between islands).

    Request body:
    - session_id: Optional custom session ID

    Returns the session ID.
    """
    if not bridge_metrics:
        raise HTTPException(status_code=503, detail="Bridge metrics not initialized")

    # End current session if any
    bridge_metrics.end_session()

    # Start new session
    session_id = bridge_metrics.start_session(session_id)

    return {
        "message": "Bridge session started",
        "session_id": session_id
    }


@router.post("/session/end")
async def end_session():
    """
    End current bridge session.

    Returns session summary.
    """
    if not bridge_metrics:
        raise HTTPException(status_code=503, detail="Bridge metrics not initialized")

    current_session = bridge_metrics.current_session

    if not current_session:
        raise HTTPException(status_code=400, detail="No active session")

    bridge_metrics.end_session()

    return {
        "message": "Bridge session ended",
        "session": current_session.to_dict()
    }


@router.get("/metrics/export")
async def export_metrics(filepath: str = "/tmp/bridge_metrics.json"):
    """
    Export bridge metrics to JSON file.

    Query parameters:
    - filepath: Output file path (default: /tmp/bridge_metrics.json)

    Returns the export file path.
    """
    if not bridge_metrics:
        raise HTTPException(status_code=503, detail="Bridge metrics not initialized")

    try:
        bridge_metrics.export_metrics(filepath)
        return {
            "message": "Metrics exported",
            "filepath": filepath
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
