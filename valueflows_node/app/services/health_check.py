"""
Health Check Service for ValueFlows Node

Provides health and readiness checks for the ValueFlows coordination system.
Verifies that all critical dependencies are functioning correctly.
"""

import asyncio
from typing import Dict, Any
from enum import Enum

from valueflows_node.app.config import settings
from valueflows_node.app.logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheckService:
    """Service for performing health checks"""

    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """
        Check database connectivity.

        Returns:
            Dict with status and optional error
        """
        try:
            from valueflows_node.app.database import get_database
            db = get_database()
            db.connect()
            # Run a simple query
            cursor = db.conn.execute("SELECT 1")
            cursor.fetchone()
            db.close()
            return {"status": HealthStatus.HEALTHY}
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e), error_type=type(e).__name__)
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """
        Perform complete health check of all dependencies.

        Returns:
            Dict with overall status and individual check results
        """
        # Run all checks concurrently
        database_check = await HealthCheckService.check_database()

        # Determine overall status
        checks = {
            "database": database_check,
        }

        # Overall is unhealthy if any check is unhealthy
        all_statuses = [check["status"] for check in checks.values()]
        if HealthStatus.UNHEALTHY in all_statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in all_statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            "status": overall_status,
            "service": "valueflows-node",
            "version": "1.0.0",
            "checks": checks
        }

    @staticmethod
    async def readiness_check() -> Dict[str, Any]:
        """
        Check if service is ready to accept requests.
        More strict than liveness check - ensures all systems are operational.

        Returns:
            Dict with readiness status
        """
        health = await HealthCheckService.health_check()

        # Ready only if fully healthy
        is_ready = health["status"] == HealthStatus.HEALTHY

        return {
            "ready": is_ready,
            "status": health["status"],
            "service": "valueflows-node"
        }

    @staticmethod
    async def liveness_check() -> Dict[str, Any]:
        """
        Check if service is alive (can respond to requests).
        Less strict than readiness - service is alive if it can respond.

        Returns:
            Dict with liveness status
        """
        # Liveness check is simple - if we can respond, we're alive
        return {
            "alive": True,
            "service": "valueflows-node"
        }
