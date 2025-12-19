"""
Bridge Metrics Tracker

Tracks bridge node performance and effectiveness:
- Bundles carried between islands
- Sync performance (time, volume)
- Island coverage (which islands visited)
- Bridge effectiveness score
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class IslandVisit:
    """Record of visiting an island"""
    island_id: str
    timestamp: datetime
    duration_seconds: float = 0.0
    bundles_received: int = 0
    bundles_sent: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "island_id": self.island_id,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "bundles_received": self.bundles_received,
            "bundles_sent": self.bundles_sent
        }


@dataclass
class BridgeSession:
    """A session of bridge node activity"""
    session_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    islands_visited: List[str] = field(default_factory=list)
    total_syncs: int = 0
    total_bundles_carried: int = 0
    total_distance_km: float = 0.0  # Future: GPS tracking

    def duration_hours(self) -> float:
        """Get session duration in hours"""
        if not self.ended_at:
            duration = datetime.now(timezone.utc) - self.started_at
        else:
            duration = self.ended_at - self.started_at
        return duration.total_seconds() / 3600.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_hours": self.duration_hours(),
            "islands_visited": self.islands_visited,
            "total_syncs": self.total_syncs,
            "total_bundles_carried": self.total_bundles_carried,
            "total_distance_km": self.total_distance_km
        }


class BridgeMetrics:
    """
    Tracks bridge node performance and effectiveness.

    Metrics tracked:
    - Island visit history
    - Bundle transport statistics
    - Sync performance
    - Coverage effectiveness
    - Bridge effectiveness score
    """

    def __init__(self, node_id: str):
        """
        Initialize bridge metrics tracker.

        Args:
            node_id: Unique identifier for this bridge node
        """
        self.node_id = node_id
        self.started_at = datetime.now(timezone.utc)

        # Visit tracking
        self.island_visits: List[IslandVisit] = []
        self.current_island: Optional[str] = None
        self.current_visit_start: Optional[datetime] = None

        # Session tracking
        self.sessions: List[BridgeSession] = []
        self.current_session: Optional[BridgeSession] = None

        # Aggregate statistics
        self.total_bundles_received = 0
        self.total_bundles_sent = 0
        self.total_syncs = 0
        self.total_islands_visited = set()

        # Island-to-island transport tracking
        self.island_pairs: Dict[tuple, int] = defaultdict(int)  # (from, to) -> count

    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new bridge session.

        Args:
            session_id: Optional custom session ID

        Returns:
            Session ID
        """
        if not session_id:
            session_id = f"session_{self.node_id}_{int(datetime.now(timezone.utc).timestamp())}"

        self.current_session = BridgeSession(
            session_id=session_id,
            started_at=datetime.now(timezone.utc)
        )
        self.sessions.append(self.current_session)

        logger.info(f"Bridge session started: {session_id}")
        return session_id

    def end_session(self):
        """End current bridge session"""
        if self.current_session:
            self.current_session.ended_at = datetime.now(timezone.utc)
            logger.info(
                f"Bridge session ended: {self.current_session.session_id} "
                f"(duration: {self.current_session.duration_hours():.1f}h, "
                f"bundles: {self.current_session.total_bundles_carried})"
            )
            self.current_session = None

    def record_island_arrival(self, island_id: str):
        """
        Record arrival at an island.

        Args:
            island_id: ID of island (e.g., 'garden', 'kitchen')
        """
        now = datetime.now(timezone.utc)

        # End previous visit if any
        if self.current_island:
            self._end_island_visit()

        # Start new visit
        self.current_island = island_id
        self.current_visit_start = now
        self.total_islands_visited.add(island_id)

        if self.current_session:
            if island_id not in self.current_session.islands_visited:
                self.current_session.islands_visited.append(island_id)

        logger.debug(f"Arrived at island: {island_id}")

    def record_island_departure(self):
        """Record departure from current island"""
        if self.current_island:
            self._end_island_visit()
            self.current_island = None
            self.current_visit_start = None

    def _end_island_visit(self):
        """Internal: End current island visit"""
        if not self.current_island or not self.current_visit_start:
            return

        duration = (datetime.now(timezone.utc) - self.current_visit_start).total_seconds()

        visit = IslandVisit(
            island_id=self.current_island,
            timestamp=self.current_visit_start,
            duration_seconds=duration
        )
        self.island_visits.append(visit)

    def record_sync(
        self,
        island_id: str,
        bundles_received: int,
        bundles_sent: int,
        from_island: Optional[str] = None
    ):
        """
        Record a sync operation.

        Args:
            island_id: Island we synced with
            bundles_received: Bundles received from island
            bundles_sent: Bundles sent to island
            from_island: Previous island (for tracking transport pairs)
        """
        self.total_syncs += 1
        self.total_bundles_received += bundles_received
        self.total_bundles_sent += bundles_sent

        # Update current visit stats
        if self.island_visits and self.island_visits[-1].island_id == island_id:
            self.island_visits[-1].bundles_received += bundles_received
            self.island_visits[-1].bundles_sent += bundles_sent

        # Update session stats
        if self.current_session:
            self.current_session.total_syncs += 1
            self.current_session.total_bundles_carried += (bundles_received + bundles_sent)

        # Track island-to-island transport
        if from_island and from_island != island_id:
            self.island_pairs[(from_island, island_id)] += bundles_sent

        logger.debug(
            f"Sync recorded: island={island_id}, "
            f"received={bundles_received}, sent={bundles_sent}"
        )

    def get_effectiveness_score(self) -> float:
        """
        Calculate bridge effectiveness score (0.0 to 1.0).

        Factors:
        - Island coverage (more islands = better)
        - Bundle volume (more bundles = better)
        - Sync frequency (regular syncs = better)
        - Island pair diversity (connecting different islands = better)

        Returns:
            Effectiveness score between 0.0 and 1.0
        """
        score = 0.0

        # Factor 1: Island coverage (0-30 points)
        # 4+ islands = full points
        island_count = len(self.total_islands_visited)
        coverage_score = min(island_count / 4.0, 1.0) * 30

        # Factor 2: Bundle volume (0-30 points)
        # 100+ bundles = full points
        total_bundles = self.total_bundles_received + self.total_bundles_sent
        volume_score = min(total_bundles / 100.0, 1.0) * 30

        # Factor 3: Sync frequency (0-20 points)
        # 1+ sync per hour = full points
        hours_active = (datetime.now(timezone.utc) - self.started_at).total_seconds() / 3600.0
        if hours_active > 0:
            syncs_per_hour = self.total_syncs / hours_active
            frequency_score = min(syncs_per_hour, 1.0) * 20
        else:
            frequency_score = 0

        # Factor 4: Island pair diversity (0-20 points)
        # 6+ unique pairs = full points (4 islands can make 12 directional pairs)
        pair_count = len(self.island_pairs)
        diversity_score = min(pair_count / 6.0, 1.0) * 20

        score = (coverage_score + volume_score + frequency_score + diversity_score) / 100.0

        return min(max(score, 0.0), 1.0)

    def get_island_stats(self) -> Dict[str, Any]:
        """
        Get per-island statistics.

        Returns:
            Dictionary mapping island_id to stats
        """
        island_stats = defaultdict(lambda: {
            "visits": 0,
            "total_time_seconds": 0.0,
            "bundles_received": 0,
            "bundles_sent": 0
        })

        for visit in self.island_visits:
            stats = island_stats[visit.island_id]
            stats["visits"] += 1
            stats["total_time_seconds"] += visit.duration_seconds
            stats["bundles_received"] += visit.bundles_received
            stats["bundles_sent"] += visit.bundles_sent

        return dict(island_stats)

    def get_transport_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Get island-to-island transport matrix.

        Shows how many bundles were carried from each island to each other island.

        Returns:
            Nested dict: {from_island: {to_island: bundle_count}}
        """
        matrix = defaultdict(lambda: defaultdict(int))

        for (from_island, to_island), count in self.island_pairs.items():
            matrix[from_island][to_island] = count

        return {k: dict(v) for k, v in matrix.items()}

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            Dictionary with all metrics
        """
        uptime_hours = (datetime.now(timezone.utc) - self.started_at).total_seconds() / 3600.0

        return {
            "node_id": self.node_id,
            "started_at": self.started_at.isoformat(),
            "uptime_hours": uptime_hours,
            "effectiveness_score": self.get_effectiveness_score(),
            "totals": {
                "syncs": self.total_syncs,
                "bundles_received": self.total_bundles_received,
                "bundles_sent": self.total_bundles_sent,
                "islands_visited": len(self.total_islands_visited),
                "island_pairs": len(self.island_pairs)
            },
            "current_island": self.current_island,
            "current_session": self.current_session.to_dict() if self.current_session else None,
            "island_stats": self.get_island_stats(),
            "transport_matrix": self.get_transport_matrix(),
            "recent_visits": [v.to_dict() for v in self.island_visits[-10:]]
        }

    def export_metrics(self, filepath: str):
        """
        Export metrics to JSON file.

        Args:
            filepath: Path to output file
        """
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.get_summary(),
            "all_visits": [v.to_dict() for v in self.island_visits],
            "all_sessions": [s.to_dict() for s in self.sessions]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    def import_metrics(self, filepath: str):
        """
        Import metrics from JSON file.

        Args:
            filepath: Path to import file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Restore aggregate stats
        summary = data.get("summary", {})
        totals = summary.get("totals", {})

        self.total_syncs = totals.get("syncs", 0)
        self.total_bundles_received = totals.get("bundles_received", 0)
        self.total_bundles_sent = totals.get("bundles_sent", 0)

        logger.info(f"Metrics imported from {filepath}")
