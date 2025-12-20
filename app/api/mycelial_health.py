"""
Mycelial Health Monitor API

Endpoints for hardware health monitoring and reporting.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.mycelial_health_monitor_service import MycelialHealthMonitorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mycelial-health", tags=["mycelial-health"])

# Global service instance
health_monitor = MycelialHealthMonitorService()


class HealthReportResponse(BaseModel):
    """Full health report response"""
    node_id: str
    timestamp: str
    platform: str
    is_android: bool
    battery: dict
    storage: dict
    temperature: dict
    network: dict
    overall_status: str
    recommendations: List[dict]


class BatteryHealthResponse(BaseModel):
    """Battery health response"""
    available: bool
    percent: Optional[float] = None
    is_charging: Optional[bool] = None
    time_remaining_seconds: Optional[int] = None
    charge_cycles: Optional[int] = None
    capacity_percent: Optional[int] = None
    temperature_celsius: Optional[float] = None
    health_status: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class StorageHealthResponse(BaseModel):
    """Storage health response"""
    available: bool
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    free_percent: Optional[float] = None
    io_errors: Optional[int] = None
    health_status: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class PowerOutageAlert(BaseModel):
    """Power outage detection alert"""
    detected: bool
    timestamp: Optional[str] = None
    affected_nodes: Optional[List[str]] = None
    node_count: Optional[int] = None
    alert_type: Optional[str] = None
    priority: Optional[str] = None


@router.get("/report", response_model=HealthReportResponse)
async def get_health_report():
    """
    Get comprehensive health report for this node.

    Returns:
        Full health report including battery, storage, temperature, network
    """
    try:
        report = health_monitor.get_full_health_report()
        return report
    except Exception as e:
        logger.error(f"Error generating health report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate health report: {str(e)}")


@router.get("/battery", response_model=BatteryHealthResponse)
async def get_battery_health():
    """
    Get battery health metrics.

    Returns:
        Battery health including charge level, cycles, capacity, temperature
    """
    try:
        return health_monitor.get_battery_health()
    except Exception as e:
        logger.error(f"Error getting battery health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get battery health: {str(e)}")


@router.get("/storage", response_model=StorageHealthResponse)
async def get_storage_health():
    """
    Get storage health metrics.

    Returns:
        Storage health including capacity, free space, I/O errors
    """
    try:
        return health_monitor.get_storage_health()
    except Exception as e:
        logger.error(f"Error getting storage health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage health: {str(e)}")


@router.get("/temperature")
async def get_temperature():
    """
    Get system temperature metrics.

    Returns:
        Temperature readings from all available sensors
    """
    try:
        return health_monitor.get_system_temperature()
    except Exception as e:
        logger.error(f"Error getting temperature: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get temperature: {str(e)}")


@router.get("/network")
async def get_network_health():
    """
    Get network interface health metrics.

    Returns:
        Network interface statistics including errors and drops
    """
    try:
        return health_monitor.get_network_health()
    except Exception as e:
        logger.error(f"Error getting network health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get network health: {str(e)}")


@router.post("/detect-outage", response_model=PowerOutageAlert)
async def detect_power_outage(node_reports: List[dict]):
    """
    Detect power outage based on multiple node reports.

    Args:
        node_reports: List of recent health reports from nearby nodes

    Returns:
        Power outage alert if cluster detected, otherwise None
    """
    try:
        outage = health_monitor.detect_power_outage_cluster(node_reports)
        if outage:
            return outage
        return {"detected": False}
    except Exception as e:
        logger.error(f"Error detecting power outage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to detect power outage: {str(e)}")


@router.get("/recommendations")
async def get_recommendations():
    """
    Get actionable hardware maintenance recommendations.

    Returns:
        List of recommended actions based on current health status
    """
    try:
        report = health_monitor.get_full_health_report()
        return {
            "node_id": report["node_id"],
            "timestamp": report["timestamp"],
            "overall_status": report["overall_status"],
            "recommendations": report["recommendations"]
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")
