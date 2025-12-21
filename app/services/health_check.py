"""
Health Check Service

Provides health and readiness checks for the DTN Bundle System.
Verifies that all critical dependencies are functioning correctly.
"""

import asyncio
from typing import Dict, Any
from enum import Enum

import aiosqlite
from ..config import settings
from ..logging_config import get_logger

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
            # Try to connect and run a simple query
            async with aiosqlite.connect(settings.database_url.replace("sqlite:///", "")) as db:
                await db.execute("SELECT 1")
                return {"status": HealthStatus.HEALTHY}
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e), error_type=type(e).__name__)
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(e)
            }

    @staticmethod
    async def check_crypto_service() -> Dict[str, Any]:
        """
        Check crypto service (keypair exists).

        Returns:
            Dict with status and optional error
        """
        try:
            from ..services import CryptoService
            crypto = CryptoService()
            fingerprint = crypto.get_public_key_fingerprint()
            return {
                "status": HealthStatus.HEALTHY,
                "fingerprint": fingerprint[:16] + "..."  # Show first 16 chars
            }
        except Exception as e:
            logger.error("crypto_health_check_failed", error=str(e), error_type=type(e).__name__)
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
        database_check, crypto_check = await asyncio.gather(
            HealthCheckService.check_database(),
            HealthCheckService.check_crypto_service(),
            return_exceptions=True
        )

        # Handle any exceptions from gather
        if isinstance(database_check, Exception):
            database_check = {
                "status": HealthStatus.UNHEALTHY,
                "error": str(database_check)
            }
        if isinstance(crypto_check, Exception):
            crypto_check = {
                "status": HealthStatus.UNHEALTHY,
                "error": str(crypto_check)
            }

        # Determine overall status
        checks = {
            "database": database_check,
            "crypto": crypto_check,
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
            "service": "dtn-bundle-system",
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
            "service": "dtn-bundle-system"
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
            "service": "dtn-bundle-system"
        }
