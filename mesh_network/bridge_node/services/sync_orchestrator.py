"""
Sync Orchestrator Service

Orchestrates DTN bundle synchronization when bridge nodes transition between islands.
Triggers sync on AP change, manages sync priority, and handles errors.
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .network_monitor import NetworkInfo

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status of a sync operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class SyncOperation:
    """Record of a sync operation"""
    sync_id: str
    island_id: str
    network_info: NetworkInfo
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    bundles_received: int = 0
    bundles_sent: int = 0
    bytes_transferred: int = 0
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "sync_id": self.sync_id,
            "island_id": self.island_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "bundles_received": self.bundles_received,
            "bundles_sent": self.bundles_sent,
            "bytes_transferred": self.bytes_transferred,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message
        }


class SyncOrchestrator:
    """
    Orchestrates DTN bundle synchronization for bridge nodes.

    Responsibilities:
    - Trigger sync when AP transition detected
    - Coordinate with DTN sync endpoints
    - Track sync performance
    - Handle sync errors and retries
    - Prioritize emergency/perishable bundles
    """

    def __init__(
        self,
        dtn_base_url: str = "http://localhost:8000",
        sync_timeout: int = 300,  # 5 minutes
        max_bundles_per_sync: int = 100
    ):
        """
        Initialize sync orchestrator.

        Args:
            dtn_base_url: Base URL for DTN node API
            sync_timeout: Maximum time for sync operation (seconds)
            max_bundles_per_sync: Maximum bundles to sync in one operation
        """
        self.dtn_base_url = dtn_base_url.rstrip("/")
        self.sync_timeout = sync_timeout
        self.max_bundles_per_sync = max_bundles_per_sync

        self.sync_history: List[SyncOperation] = []
        self.current_sync: Optional[SyncOperation] = None
        self.sync_counter = 0

    async def sync_on_ap_transition(
        self,
        old_network: NetworkInfo,
        new_network: NetworkInfo
    ) -> SyncOperation:
        """
        Perform sync when transitioning between APs.

        This is the main entry point called by the network monitor
        when an island transition is detected.

        Args:
            old_network: Network we disconnected from
            new_network: Network we connected to

        Returns:
            SyncOperation record
        """
        self.sync_counter += 1
        sync_id = f"sync_{new_network.island_id}_{self.sync_counter}_{int(datetime.utcnow().timestamp())}"

        sync_op = SyncOperation(
            sync_id=sync_id,
            island_id=new_network.island_id or "unknown",
            network_info=new_network,
            status=SyncStatus.PENDING,
            started_at=datetime.utcnow()
        )

        self.current_sync = sync_op
        self.sync_history.append(sync_op)

        logger.info(
            f"Starting sync operation {sync_id} "
            f"(transition: {old_network.island_id} -> {new_network.island_id})"
        )

        try:
            sync_op.status = SyncStatus.IN_PROGRESS

            # Step 1: Pull bundles from new island
            bundles_received = await self._pull_bundles(new_network)
            sync_op.bundles_received = bundles_received

            # Step 2: Push bundles we're carrying to new island
            bundles_sent = await self._push_bundles(new_network)
            sync_op.bundles_sent = bundles_sent

            # Mark complete
            sync_op.status = SyncStatus.COMPLETED
            sync_op.completed_at = datetime.utcnow()
            sync_op.duration_seconds = (
                sync_op.completed_at - sync_op.started_at
            ).total_seconds()

            logger.info(
                f"Sync {sync_id} completed: "
                f"received={bundles_received}, sent={bundles_sent}, "
                f"duration={sync_op.duration_seconds:.1f}s"
            )

        except asyncio.TimeoutError:
            sync_op.status = SyncStatus.TIMEOUT
            sync_op.error_message = f"Sync timed out after {self.sync_timeout}s"
            sync_op.completed_at = datetime.utcnow()
            logger.error(f"Sync {sync_id} timed out")

        except Exception as e:
            sync_op.status = SyncStatus.FAILED
            sync_op.error_message = str(e)
            sync_op.completed_at = datetime.utcnow()
            logger.error(f"Sync {sync_id} failed: {e}")

        finally:
            self.current_sync = None

        return sync_op

    async def _pull_bundles(self, network: NetworkInfo) -> int:
        """
        Pull bundles from the island we just connected to.

        Uses the DTN /sync/pull endpoint to get bundles ready for forwarding.

        Returns:
            Number of bundles received
        """
        try:
            # Construct DTN endpoint URL using gateway address
            if not network.gateway:
                logger.warning("No gateway address, using localhost")
                dtn_url = self.dtn_base_url
            else:
                dtn_url = f"http://{network.gateway}:8000"

            url = f"{dtn_url}/sync/pull"

            logger.debug(f"Pulling bundles from {url}")

            async with httpx.AsyncClient(timeout=self.sync_timeout) as client:
                response = await client.get(
                    url,
                    params={
                        "max_bundles": self.max_bundles_per_sync,
                        "peer_trust_score": 1.0,  # Bridge node has high trust
                        "peer_is_local": True
                    }
                )

                response.raise_for_status()
                data = response.json()

                bundles = data.get("bundles", [])
                logger.info(f"Pulled {len(bundles)} bundles from {network.island_id}")

                # Store bundles locally (push to our own inbox)
                if bundles:
                    await self._store_bundles_locally(bundles)

                return len(bundles)

        except Exception as e:
            logger.error(f"Failed to pull bundles: {e}")
            raise

    async def _push_bundles(self, network: NetworkInfo) -> int:
        """
        Push bundles we're carrying to the island we just connected to.

        Gets bundles from our local forwarding queue and pushes them
        to the new island's DTN node.

        Returns:
            Number of bundles sent
        """
        try:
            # Step 1: Get bundles from our local forwarding queue
            bundles_to_send = await self._get_local_forwarding_bundles()

            if not bundles_to_send:
                logger.debug("No bundles to forward")
                return 0

            # Step 2: Push to new island's DTN node
            if not network.gateway:
                logger.warning("No gateway address, using localhost")
                dtn_url = self.dtn_base_url
            else:
                dtn_url = f"http://{network.gateway}:8000"

            url = f"{dtn_url}/sync/push"

            logger.debug(f"Pushing {len(bundles_to_send)} bundles to {url}")

            async with httpx.AsyncClient(timeout=self.sync_timeout) as client:
                response = await client.post(
                    url,
                    json=bundles_to_send
                )

                response.raise_for_status()
                data = response.json()

                accepted = data.get("accepted", 0)
                logger.info(f"Pushed {accepted}/{len(bundles_to_send)} bundles to {network.island_id}")

                return accepted

        except Exception as e:
            logger.error(f"Failed to push bundles: {e}")
            raise

    async def _get_local_forwarding_bundles(self) -> List[Dict[str, Any]]:
        """
        Get bundles from local forwarding queue.

        Queries our own DTN node for bundles ready to forward.

        Returns:
            List of bundle dictionaries
        """
        try:
            url = f"{self.dtn_base_url}/sync/pull"

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url,
                    params={
                        "max_bundles": self.max_bundles_per_sync,
                        "peer_trust_score": 1.0,
                        "peer_is_local": True
                    }
                )

                response.raise_for_status()
                data = response.json()

                return data.get("bundles", [])

        except Exception as e:
            logger.error(f"Failed to get local forwarding bundles: {e}")
            return []

    async def _store_bundles_locally(self, bundles: List[Dict[str, Any]]):
        """
        Store received bundles in our local DTN node.

        Pushes bundles to our own inbox for later forwarding.

        Args:
            bundles: List of bundle dictionaries to store
        """
        try:
            url = f"{self.dtn_base_url}/sync/push"

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=bundles)
                response.raise_for_status()

                data = response.json()
                logger.debug(f"Stored {data.get('accepted', 0)} bundles locally")

        except Exception as e:
            logger.error(f"Failed to store bundles locally: {e}")
            raise

    async def get_sync_stats(self) -> Dict[str, Any]:
        """
        Get sync statistics.

        Returns:
            Dictionary with sync performance metrics
        """
        total_syncs = len(self.sync_history)
        completed_syncs = [s for s in self.sync_history if s.status == SyncStatus.COMPLETED]
        failed_syncs = [s for s in self.sync_history if s.status == SyncStatus.FAILED]

        total_bundles_received = sum(s.bundles_received for s in self.sync_history)
        total_bundles_sent = sum(s.bundles_sent for s in self.sync_history)

        avg_duration = 0.0
        if completed_syncs:
            avg_duration = sum(s.duration_seconds for s in completed_syncs) / len(completed_syncs)

        return {
            "total_syncs": total_syncs,
            "completed_syncs": len(completed_syncs),
            "failed_syncs": len(failed_syncs),
            "success_rate": len(completed_syncs) / total_syncs if total_syncs > 0 else 0.0,
            "total_bundles_received": total_bundles_received,
            "total_bundles_sent": total_bundles_sent,
            "average_sync_duration_seconds": avg_duration,
            "current_sync": self.current_sync.to_dict() if self.current_sync else None
        }

    def get_recent_syncs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sync operations.

        Args:
            limit: Maximum number of syncs to return

        Returns:
            List of sync operation dictionaries
        """
        recent = self.sync_history[-limit:]
        return [s.to_dict() for s in reversed(recent)]

    async def manual_sync(self, network: NetworkInfo) -> SyncOperation:
        """
        Manually trigger a sync operation.

        Useful for testing or forcing a sync without AP transition.

        Args:
            network: Network to sync with

        Returns:
            SyncOperation record
        """
        logger.info(f"Manual sync triggered for {network.island_id}")

        # Create a dummy old network for the transition
        old_network = NetworkInfo(
            ssid=None,
            bssid=None,
            ip_address=None,
            gateway=None,
            subnet=None,
            island_id="manual",
            status=network.status,
            timestamp=datetime.utcnow()
        )

        return await self.sync_on_ap_transition(old_network, network)
