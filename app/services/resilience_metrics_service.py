"""Resilience Metrics Service

Computes network health metrics across multiple dimensions:
- Density: Connections per person
- Flow: Resources actually moving
- Redundancy: Multiple paths exist
- Velocity: Speed of resource matching
- Recovery: Bounce back from disruption
- Coverage: Needs being met
- Decentralization: No power concentration

PRIVACY: All metrics are AGGREGATES only. No individual visibility.
ARCHITECTURE: Local-first computation, works offline, no central server.
"""
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, UTC
from collections import defaultdict
import uuid
import statistics

from app.models.resilience_metrics import (
    NetworkHealth,
    CellHealth,
    VulnerabilityReport,
    FlowAnalysis,
    ThreatScenario,
    HealthTrend,
    HealthStatus,
    ResilienceDimension,
)
from app.database.resilience_metrics_repository import ResilienceMetricsRepository


class ResilienceMetricsService:
    """Service for computing and analyzing network resilience metrics."""

    def __init__(self, db_path: str, vouch_db_path: Optional[str] = None, vf_db_path: Optional[str] = None):
        self.db_path = db_path
        self.vouch_db_path = vouch_db_path or db_path
        self.vf_db_path = vf_db_path or "data/vf_node.db"
        self.repository = ResilienceMetricsRepository(db_path)

    # ============================================================
    # NETWORK HEALTH COMPUTATION
    # ============================================================

    async def compute_network_health(
        self,
        period_days: int = 30
    ) -> NetworkHealth:
        """Compute current network health across all dimensions.

        Returns aggregated metrics with NO individual data exposed.
        """
        snapshot_time = datetime.now(UTC)
        snapshot_id = f"health-{uuid.uuid4()}"

        # Get database connections
        conn = sqlite3.connect(self.db_path)
        vouch_conn = sqlite3.connect(self.vouch_db_path)

        # Compute each dimension
        density_score, avg_connections = await self._compute_density(vouch_conn)
        flow_score, total_exchanges = await self._compute_flow(conn, period_days)
        redundancy_score = await self._compute_redundancy(vouch_conn)
        velocity_score, median_hours = await self._compute_velocity(conn, period_days)
        recovery_score = await self._compute_recovery(conn, period_days)
        coverage_score, match_rate = await self._compute_coverage(conn, period_days)
        decentralization_score = await self._compute_decentralization(conn, vouch_conn)

        # Get raw counts
        total_members = await self._get_active_member_count(conn)
        total_cells = await self._get_active_cell_count(conn)

        # Compute overall score (weighted average)
        overall_score = self._compute_overall_score(
            density_score,
            flow_score,
            redundancy_score,
            velocity_score,
            recovery_score,
            coverage_score,
            decentralization_score,
        )

        # Identify critical and warning dimensions
        critical_dims = []
        warning_dims = []

        for dim_name, score in [
            ("density", density_score),
            ("flow", flow_score),
            ("redundancy", redundancy_score),
            ("velocity", velocity_score),
            ("recovery", recovery_score),
            ("coverage", coverage_score),
            ("decentralization", decentralization_score),
        ]:
            if score < 40:
                critical_dims.append(dim_name)
            elif score < 70:
                warning_dims.append(dim_name)

        # Determine overall status
        status = self._score_to_status(overall_score)

        conn.close()
        vouch_conn.close()

        # Create health snapshot
        health = NetworkHealth(
            id=snapshot_id,
            snapshot_time=snapshot_time,
            overall_score=overall_score,
            status=status,
            density_score=density_score,
            flow_score=flow_score,
            redundancy_score=redundancy_score,
            velocity_score=velocity_score,
            recovery_score=recovery_score,
            coverage_score=coverage_score,
            decentralization_score=decentralization_score,
            total_members=total_members,
            total_cells=total_cells,
            total_exchanges=total_exchanges,
            avg_connections_per_member=avg_connections,
            median_match_time_hours=median_hours,
            needs_match_rate=match_rate,
            critical_dimensions=critical_dims,
            warning_dimensions=warning_dims,
            measurement_period_days=period_days,
        )

        # Save to database
        self.repository.save_network_health(health)

        return health

    async def _compute_density(self, vouch_conn: sqlite3.Connection) -> Tuple[float, float]:
        """Compute density score: connections per person.

        Healthy threshold: >= 3 trusted connections per member.
        Returns: (score 0-100, avg_connections)
        """
        cursor = vouch_conn.cursor()

        # Get average connections per user (count vouches given + received)
        cursor.execute("""
            SELECT
                COUNT(DISTINCT voucher_id) + COUNT(DISTINCT vouchee_id) as total_users,
                COUNT(*) as total_vouches
            FROM vouches
            WHERE revoked = 0
        """)

        row = cursor.fetchone()
        total_users = row[0] if row else 0
        total_vouches = row[1] if row else 0

        if total_users == 0:
            return 0.0, 0.0

        # Average vouches per user (each vouch creates 1 connection)
        avg_connections = (total_vouches * 2) / total_users  # *2 because each vouch is counted for both users

        # Score: 3+ connections = 100%, scale linearly below that
        score = min(100.0, (avg_connections / 3.0) * 100.0)

        return score, avg_connections

    async def _compute_flow(self, conn: sqlite3.Connection, period_days: int) -> Tuple[float, int]:
        """Compute flow score: resources actually moving.

        Healthy threshold: >= 1 exchange per member per month.
        Returns: (score 0-100, total_exchanges)
        """
        cursor = conn.cursor()

        # Query actual completed exchanges from ValueFlows database
        since = (datetime.now(UTC) - timedelta(days=period_days)).isoformat()

        try:
            # Connect to ValueFlows database
            vf_conn = sqlite3.connect(self.vf_db_path)
            vf_cursor = vf_conn.cursor()

            # Count completed exchanges in the period
            vf_cursor.execute("""
                SELECT COUNT(*) FROM exchanges
                WHERE status = 'completed'
                AND updated_at >= ?
            """, (since,))
            result = vf_cursor.fetchone()
            total_exchanges = result[0] if result else 0

            vf_conn.close()

        except sqlite3.OperationalError:
            # Table might not exist yet - fall back to zero
            total_exchanges = 0

        active_members = await self._get_active_member_count(conn)

        if active_members == 0:
            return 0.0, 0

        # Expected: 1 exchange per member per month
        expected_monthly_rate = 1.0
        period_months = period_days / 30.0
        expected_exchanges = active_members * expected_monthly_rate * period_months

        if expected_exchanges == 0:
            return 0.0, total_exchanges

        # Score: actual / expected * 100
        score = min(100.0, (total_exchanges / expected_exchanges) * 100.0)

        return score, total_exchanges

    async def _compute_redundancy(self, vouch_conn: sqlite3.Connection) -> float:
        """Compute redundancy score: multiple paths exist.

        Healthy threshold: no single node > 10% of graph centrality.
        Returns: score 0-100
        """
        cursor = vouch_conn.cursor()

        # Get all users and their vouch counts
        cursor.execute("""
            SELECT voucher_id, COUNT(*) as vouch_count
            FROM vouches
            WHERE revoked = 0
            GROUP BY voucher_id
        """)

        rows = cursor.fetchall()

        if not rows:
            return 0.0

        total_vouches = sum(row[1] for row in rows)
        max_vouches = max(row[1] for row in rows)

        if total_vouches == 0:
            return 0.0

        max_centrality = max_vouches / total_vouches

        # Score: penalize if any node has > 10% centrality
        if max_centrality <= 0.10:
            score = 100.0
        else:
            # Linear penalty above 10%
            score = max(0.0, 100.0 - ((max_centrality - 0.10) * 500))

        return score

    async def _compute_velocity(self, conn: sqlite3.Connection, period_days: int) -> Tuple[float, Optional[float]]:
        """Compute velocity score: speed of resource matching.

        Healthy threshold: <= 24 hours from offer to match.
        Returns: (score 0-100, median_hours)
        """
        cursor = conn.cursor()
        period_start = (datetime.now(UTC) - timedelta(days=period_days)).isoformat()

        # Get actual match times: time from need creation to match acceptance
        cursor.execute("""
            SELECT
                (julianday(m.created_at) - julianday(l.created_at)) * 24 as hours_to_match
            FROM matches m
            JOIN listings l ON m.need_id = l.id
            WHERE m.created_at >= ?
            AND m.status IN ('accepted', 'suggested')
            AND l.listing_type = 'need'
        """, (period_start,))

        match_times = [row[0] for row in cursor.fetchall() if row[0] is not None and row[0] >= 0]

        if not match_times:
            # No data - return neutral score
            return 50.0, None

        median_hours = statistics.median(match_times)

        if median_hours <= 24:
            score = 100.0
        else:
            # Penalize for slower matching
            score = max(0.0, 100.0 - ((median_hours - 24) * 2))

        return score, median_hours

    async def _compute_recovery(self, conn: sqlite3.Connection, period_days: int) -> float:
        """Compute recovery score: bounce back from disruption.

        Healthy threshold: cells reform within 1 week after disruption.
        This is hard to measure without actual disruptions, so we use
        proxy metrics: cell formation rate, member retention.
        Returns: score 0-100
        """
        cursor = conn.cursor()

        # Proxy: measure member retention rate
        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        sixty_days_ago = (datetime.now(UTC) - timedelta(days=60)).isoformat()

        # Members who joined 30-60 days ago
        cursor.execute("""
            SELECT COUNT(*) FROM cell_memberships
            WHERE joined_at >= ? AND joined_at < ?
        """, (sixty_days_ago, thirty_days_ago))

        joined_30_60 = cursor.fetchone()[0]

        # Of those, how many are still active?
        cursor.execute("""
            SELECT COUNT(*) FROM cell_memberships
            WHERE joined_at >= ? AND joined_at < ? AND is_active = 1
        """, (sixty_days_ago, thirty_days_ago))

        still_active = cursor.fetchone()[0]

        if joined_30_60 == 0:
            # Not enough data
            return 50.0  # Neutral score

        retention_rate = still_active / joined_30_60

        # Score: 80%+ retention = 100, scale down from there
        score = min(100.0, (retention_rate / 0.80) * 100.0)

        return score

    async def _compute_coverage(self, conn: sqlite3.Connection, period_days: int) -> Tuple[float, float]:
        """Compute coverage score: needs being met.

        Healthy threshold: >= 80% of needs matched.
        Returns: (score 0-100, match_rate)
        """
        cursor = conn.cursor()
        period_start = (datetime.now(UTC) - timedelta(days=period_days)).isoformat()

        # Count total needs posted in period
        cursor.execute("""
            SELECT COUNT(*) FROM listings
            WHERE listing_type = 'need'
            AND created_at >= ?
            AND status != 'cancelled'
        """, (period_start,))

        total_needs = cursor.fetchone()[0]

        if total_needs == 0:
            # No needs posted - return neutral score
            return 50.0, 0.0

        # Count needs that have at least one accepted match
        cursor.execute("""
            SELECT COUNT(DISTINCT l.id)
            FROM listings l
            JOIN matches m ON l.id = m.need_id
            WHERE l.listing_type = 'need'
            AND l.created_at >= ?
            AND l.status != 'cancelled'
            AND m.status IN ('accepted', 'suggested')
        """, (period_start,))

        matched_needs = cursor.fetchone()[0]

        # Calculate match rate as percentage
        match_rate = (matched_needs / total_needs * 100.0) if total_needs > 0 else 0.0

        # Score: 100 if >= 80% match rate, scaled below that
        score = min(100.0, (match_rate / 80.0) * 100.0)

        return score, match_rate

    async def _compute_decentralization(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection
    ) -> float:
        """Compute decentralization score: no power concentration.

        Healthy threshold: no node > 10% of activity.
        Returns: score 0-100
        """
        # Check both vouch centrality and cell stewardship concentration
        vouch_score = await self._compute_redundancy(vouch_conn)

        cursor = conn.cursor()

        # Check steward concentration
        cursor.execute("""
            SELECT COUNT(DISTINCT cell_id) as total_cells
            FROM cells
        """)

        total_cells = cursor.fetchone()[0]

        if total_cells == 0:
            return 100.0

        # Check if any steward manages > 10% of cells
        cursor.execute("""
            SELECT user_id, COUNT(DISTINCT cell_id) as cell_count
            FROM cell_memberships
            WHERE role = 'steward' AND is_active = 1
            GROUP BY user_id
        """)

        rows = cursor.fetchall()

        max_cells = max((row[1] for row in rows), default=0)
        max_steward_ratio = max_cells / total_cells if total_cells > 0 else 0

        if max_steward_ratio <= 0.10:
            steward_score = 100.0
        else:
            steward_score = max(0.0, 100.0 - ((max_steward_ratio - 0.10) * 500))

        # Average the two scores
        score = (vouch_score + steward_score) / 2.0

        return score

    def _compute_overall_score(
        self,
        density: float,
        flow: float,
        redundancy: float,
        velocity: float,
        recovery: float,
        coverage: float,
        decentralization: float,
    ) -> float:
        """Compute weighted overall score.

        Weights:
        - Flow: 25% (most important - is value actually moving?)
        - Coverage: 20% (are needs being met?)
        - Density: 15% (connections)
        - Redundancy: 15% (resilience)
        - Decentralization: 10% (no single points of failure)
        - Velocity: 10% (speed)
        - Recovery: 5% (hard to measure directly)
        """
        weighted = (
            flow * 0.25 +
            coverage * 0.20 +
            density * 0.15 +
            redundancy * 0.15 +
            decentralization * 0.10 +
            velocity * 0.10 +
            recovery * 0.05
        )

        return round(weighted, 1)

    def _score_to_status(self, score: float) -> HealthStatus:
        """Convert score to status."""
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 70:
            return HealthStatus.HEALTHY
        elif score >= 40:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL

    async def _get_active_member_count(self, conn: sqlite3.Connection) -> int:
        """Get count of active members across all cells."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM cell_memberships
            WHERE is_active = 1
        """)
        return cursor.fetchone()[0]

    async def _get_active_cell_count(self, conn: sqlite3.Connection) -> int:
        """Get count of active cells."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cells")
        return cursor.fetchone()[0]

    # ============================================================
    # CELL HEALTH COMPUTATION
    # ============================================================

    async def compute_cell_health(
        self,
        cell_id: str,
        period_days: int = 30
    ) -> CellHealth:
        """Compute health metrics for a specific cell.

        Visible to cell stewards only.
        """
        snapshot_time = datetime.now(UTC)
        snapshot_id = f"cell-health-{uuid.uuid4()}"

        conn = sqlite3.connect(self.db_path)
        vouch_conn = sqlite3.connect(self.vouch_db_path)

        # Get cell metrics
        active_members = await self._get_cell_member_count(conn, cell_id)
        avg_connections = await self._get_cell_avg_connections(conn, vouch_conn, cell_id)
        exchanges_completed = await self._get_cell_exchanges(conn, cell_id, period_days)

        # Compute flow rate
        if active_members > 0:
            period_months = period_days / 30.0
            flow_rate = exchanges_completed / (active_members * period_months)
        else:
            flow_rate = 0.0

        # Get median match time from actual matches in this cell
        cursor = conn.cursor()
        period_start = (datetime.now(UTC) - timedelta(days=period_days)).isoformat()

        cursor.execute("""
            SELECT
                (julianday(m.created_at) - julianday(l.created_at)) * 24 as hours_to_match
            FROM matches m
            JOIN listings l ON m.need_id = l.id
            JOIN cell_memberships cm ON (l.agent_id = cm.user_id AND cm.cell_id = ?)
            WHERE m.created_at >= ?
            AND m.status IN ('accepted', 'suggested')
            AND l.listing_type = 'need'
            AND cm.is_active = 1
        """, (cell_id, period_start))

        match_times = [row[0] for row in cursor.fetchall() if row[0] is not None and row[0] >= 0]
        median_match_time_hours = statistics.median(match_times) if match_times else None

        # Get needs match rate for this cell
        cursor.execute("""
            SELECT COUNT(*) FROM listings l
            JOIN cell_memberships cm ON (l.agent_id = cm.user_id AND cm.cell_id = ?)
            WHERE l.listing_type = 'need'
            AND l.created_at >= ?
            AND l.status != 'cancelled'
            AND cm.is_active = 1
        """, (cell_id, period_start))

        cell_total_needs = cursor.fetchone()[0]

        if cell_total_needs > 0:
            cursor.execute("""
                SELECT COUNT(DISTINCT l.id)
                FROM listings l
                JOIN matches m ON l.id = m.need_id
                JOIN cell_memberships cm ON (l.agent_id = cm.user_id AND cm.cell_id = ?)
                WHERE l.listing_type = 'need'
                AND l.created_at >= ?
                AND l.status != 'cancelled'
                AND m.status IN ('accepted', 'suggested')
                AND cm.is_active = 1
            """, (cell_id, period_start))

            cell_matched_needs = cursor.fetchone()[0]
            needs_match_rate = (cell_matched_needs / cell_total_needs * 100.0) if cell_total_needs > 0 else 0.0
        else:
            needs_match_rate = 0.0

        # Get network averages for comparison
        network_health = self.repository.get_latest_network_health()

        if network_health:
            vs_network_connections = ((avg_connections - network_health.avg_connections_per_member) /
                                     network_health.avg_connections_per_member * 100) if network_health.avg_connections_per_member > 0 else 0
            network_flow_rate = (network_health.total_exchanges / network_health.total_members /
                                (network_health.measurement_period_days / 30.0)) if network_health.total_members > 0 else 0
            vs_network_flow = ((flow_rate - network_flow_rate) / network_flow_rate * 100) if network_flow_rate > 0 else 0
        else:
            vs_network_connections = 0.0
            vs_network_flow = 0.0

        # Compute cell score (simplified - could be more sophisticated)
        connection_score = min(100.0, (avg_connections / 3.0) * 100.0)
        flow_score = min(100.0, (flow_rate / 1.0) * 100.0 * 30)  # Normalize to monthly
        match_score = needs_match_rate

        cell_score = (connection_score * 0.4 + flow_score * 0.4 + match_score * 0.2)

        status = self._score_to_status(cell_score)

        # Generate recommendations
        recommendations = await self._generate_cell_recommendations(
            avg_connections, flow_rate, needs_match_rate, active_members
        )

        conn.close()
        vouch_conn.close()

        # Create health snapshot
        health = CellHealth(
            id=snapshot_id,
            cell_id=cell_id,
            snapshot_time=snapshot_time,
            cell_score=cell_score,
            status=status,
            active_members=active_members,
            avg_connections_per_member=avg_connections,
            exchanges_completed=exchanges_completed,
            flow_rate=flow_rate,
            median_match_time_hours=median_match_time_hours,
            needs_match_rate=needs_match_rate,
            vs_network_connections=vs_network_connections,
            vs_network_flow=vs_network_flow,
            recommendations=recommendations,
            measurement_period_days=period_days,
        )

        # Save to database
        self.repository.save_cell_health(health)

        return health

    async def _get_cell_member_count(self, conn: sqlite3.Connection, cell_id: str) -> int:
        """Get active member count for a cell."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM cell_memberships
            WHERE cell_id = ? AND is_active = 1
        """, (cell_id,))
        return cursor.fetchone()[0]

    async def _get_cell_avg_connections(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection,
        cell_id: str
    ) -> float:
        """Get average connections per member in a cell."""
        # Get cell members
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id FROM cell_memberships
            WHERE cell_id = ? AND is_active = 1
        """, (cell_id,))

        member_ids = [row[0] for row in cursor.fetchall()]

        if not member_ids:
            return 0.0

        # Count vouches for these members
        vouch_cursor = vouch_conn.cursor()
        placeholders = ','.join('?' * len(member_ids))

        vouch_cursor.execute(f"""
            SELECT COUNT(*) FROM vouches
            WHERE (voucher_id IN ({placeholders}) OR vouchee_id IN ({placeholders}))
            AND revoked = 0
        """, member_ids + member_ids)

        total_vouches = vouch_cursor.fetchone()[0]

        return total_vouches / len(member_ids) if member_ids else 0.0

    async def _get_cell_exchanges(
        self,
        conn: sqlite3.Connection,
        cell_id: str,
        period_days: int
    ) -> int:
        """Get exchange count for a cell in period."""
        # TODO: Implement based on ValueFlows
        return 0

    async def _generate_cell_recommendations(
        self,
        avg_connections: float,
        flow_rate: float,
        needs_match_rate: float,
        active_members: int
    ) -> List[str]:
        """Generate specific recommendations for cell improvement."""
        recommendations = []

        if avg_connections < 3.0:
            recommendations.append(
                f"Low connectivity ({avg_connections:.1f} connections per member). "
                "Host a social event to help members connect."
            )

        if flow_rate < 0.5:
            recommendations.append(
                "Low resource flow. Encourage members to post offers and needs."
            )

        if needs_match_rate < 60:
            recommendations.append(
                f"Only {needs_match_rate:.0f}% of needs are being matched. "
                "Consider expanding your cell or partnering with nearby cells."
            )

        if active_members < 10:
            recommendations.append(
                f"Small cell size ({active_members} members). "
                "Recruit more members to increase resilience."
            )

        if not recommendations:
            recommendations.append("Cell is healthy! Keep up the good work.")

        return recommendations

    # ============================================================
    # VULNERABILITY ANALYSIS
    # ============================================================

    async def compute_vulnerability_report(self) -> VulnerabilityReport:
        """Identify single points of failure in the network.

        Returns nodes/edges that if removed would harm network.
        """
        report_time = datetime.now(UTC)
        report_id = f"vuln-{uuid.uuid4()}"

        conn = sqlite3.connect(self.db_path)
        vouch_conn = sqlite3.connect(self.vouch_db_path)

        # Find critical nodes (users with > 10% of vouches)
        critical_nodes = await self._find_critical_nodes(vouch_conn)

        # Find critical edges (single connections between cells)
        critical_edges = await self._find_critical_edges(conn, vouch_conn)

        # Find isolated cells
        isolated_cells = await self._find_isolated_cells(conn, vouch_conn)

        # Generate recommendations
        recommendations = await self._generate_redundancy_recommendations(
            critical_nodes, critical_edges, isolated_cells
        )

        # Compute vulnerability score
        vulnerability_score = self._compute_vulnerability_score(
            critical_nodes, critical_edges, isolated_cells
        )

        conn.close()
        vouch_conn.close()

        report = VulnerabilityReport(
            id=report_id,
            report_time=report_time,
            critical_nodes=critical_nodes,
            critical_edges=critical_edges,
            isolated_cells=isolated_cells,
            redundancy_recommendations=recommendations,
            vulnerability_score=vulnerability_score,
        )

        self.repository.save_vulnerability_report(report)

        return report

    async def _find_critical_nodes(self, vouch_conn: sqlite3.Connection) -> List[Dict]:
        """Find users with >10% of network activity."""
        cursor = vouch_conn.cursor()

        # Get total vouches
        cursor.execute("SELECT COUNT(*) FROM vouches WHERE revoked = 0")
        total_vouches = cursor.fetchone()[0]

        if total_vouches == 0:
            return []

        # Find users with >10% of vouches
        cursor.execute("""
            SELECT voucher_id, COUNT(*) as vouch_count
            FROM vouches
            WHERE revoked = 0
            GROUP BY voucher_id
            HAVING vouch_count > ?
        """, (total_vouches * 0.10,))

        critical = []
        for row in cursor.fetchall():
            user_id = row[0]
            vouch_count = row[1]
            percentage = (vouch_count / total_vouches) * 100

            critical.append({
                "node_id": user_id[:16] + "...",  # Truncate for privacy
                "centrality_score": percentage / 100,
                "vouch_percentage": percentage,
                "resource_percentage": 0.0,  # TODO: compute from ValueFlows
                "risk": f"If this member leaves, {percentage:.1f}% of trust network affected"
            })

        return critical

    async def _find_critical_edges(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection
    ) -> List[Dict]:
        """Find edges that if removed would isolate cells."""
        # TODO: Implement graph analysis to find bridges
        # For now, return empty
        return []

    async def _find_isolated_cells(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection
    ) -> List[str]:
        """Find cells with weak external connections."""
        # TODO: Implement
        return []

    async def _generate_redundancy_recommendations(
        self,
        critical_nodes: List[Dict],
        critical_edges: List[Dict],
        isolated_cells: List[str]
    ) -> List[str]:
        """Generate recommendations for improving redundancy."""
        recommendations = []

        if critical_nodes:
            recommendations.append(
                f"Found {len(critical_nodes)} critical nodes. "
                "Encourage these members to mentor others to distribute trust."
            )

        if critical_edges:
            recommendations.append(
                f"Found {len(critical_edges)} critical connections between cells. "
                "Add redundant connections to prevent isolation."
            )

        if isolated_cells:
            recommendations.append(
                f"Found {len(isolated_cells)} isolated cells. "
                "Connect these cells to the broader network."
            )

        if not recommendations:
            recommendations.append("Network has good redundancy. No critical vulnerabilities found.")

        return recommendations

    def _compute_vulnerability_score(
        self,
        critical_nodes: List[Dict],
        critical_edges: List[Dict],
        isolated_cells: List[str]
    ) -> float:
        """Compute overall vulnerability score (0-100, lower is better)."""
        score = 0.0

        # Penalize for critical nodes
        score += len(critical_nodes) * 10

        # Penalize for critical edges
        score += len(critical_edges) * 15

        # Penalize for isolated cells
        score += len(isolated_cells) * 20

        return min(100.0, score)

    # ============================================================
    # FLOW ANALYSIS
    # ============================================================

    async def compute_flow_analysis(self, period_days: int = 30) -> FlowAnalysis:
        """Analyze resource flows between cells.

        All data is AGGREGATED by cell - no individual transactions exposed.
        """
        analysis_time = datetime.now(UTC)
        analysis_id = f"flow-{uuid.uuid4()}"

        conn = sqlite3.connect(self.db_path)

        # TODO: Implement based on ValueFlows economic events
        # For now, return placeholder

        flows = []
        cell_balances = []
        imbalanced_cells = []

        conn.close()

        analysis = FlowAnalysis(
            id=analysis_id,
            analysis_time=analysis_time,
            period_days=period_days,
            flows=flows,
            cell_balances=cell_balances,
            imbalanced_cells=imbalanced_cells,
        )

        self.repository.save_flow_analysis(analysis)

        return analysis

    # ============================================================
    # THREAT MODELING
    # ============================================================

    async def run_threat_scenario(
        self,
        scenario_name: str,
        scenario_type: str,
        target_ids: List[str],
        run_by: str
    ) -> ThreatScenario:
        """Model impact of a threat scenario.

        Example: "What if Alice is compromised?"
        """
        scenario_id = f"scenario-{uuid.uuid4()}"
        run_at = datetime.now(UTC)

        conn = sqlite3.connect(self.db_path)
        vouch_conn = sqlite3.connect(self.vouch_db_path)

        if scenario_type == "member_compromised":
            result = await self._model_member_compromise(
                conn, vouch_conn, target_ids[0]
            )
        elif scenario_type == "cell_lost":
            result = await self._model_cell_loss(
                conn, vouch_conn, target_ids[0]
            )
        else:
            # Unknown scenario type
            result = {
                "members_affected": 0,
                "cells_affected": 0,
                "trust_graph_impact": 0.0,
                "recovery_time_estimate_days": 0,
                "vouches_invalidated": 0,
                "resources_unreachable": 0,
                "mitigation_steps": ["Unknown scenario type"],
            }

        conn.close()
        vouch_conn.close()

        scenario = ThreatScenario(
            id=scenario_id,
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            target_ids=target_ids,
            members_affected=result["members_affected"],
            cells_affected=result["cells_affected"],
            trust_graph_impact=result["trust_graph_impact"],
            recovery_time_estimate_days=result["recovery_time_estimate_days"],
            vouches_invalidated=result["vouches_invalidated"],
            resources_unreachable=result["resources_unreachable"],
            mitigation_steps=result["mitigation_steps"],
            run_at=run_at,
            run_by=run_by,
        )

        self.repository.save_threat_scenario(scenario)

        return scenario

    async def _model_member_compromise(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection,
        user_id: str
    ) -> Dict:
        """Model impact of a member being compromised."""
        cursor = vouch_conn.cursor()

        # Count vouches by this member
        cursor.execute("""
            SELECT COUNT(*) FROM vouches
            WHERE voucher_id = ? AND revoked = 0
        """, (user_id,))
        vouches_given = cursor.fetchone()[0]

        # Count vouches for this member
        cursor.execute("""
            SELECT COUNT(*) FROM vouches
            WHERE vouchee_id = ? AND revoked = 0
        """, (user_id,))
        vouches_received = cursor.fetchone()[0]

        # Get total vouches in network
        cursor.execute("SELECT COUNT(*) FROM vouches WHERE revoked = 0")
        total_vouches = cursor.fetchone()[0]

        trust_impact = ((vouches_given + vouches_received) / total_vouches * 100) if total_vouches > 0 else 0

        # Get cells affected
        cell_cursor = conn.cursor()
        cell_cursor.execute("""
            SELECT COUNT(DISTINCT cell_id) FROM cell_memberships
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        cells_affected = cell_cursor.fetchone()[0]

        return {
            "members_affected": vouches_given,
            "cells_affected": cells_affected,
            "trust_graph_impact": trust_impact,
            "recovery_time_estimate_days": max(3, vouches_given // 5),
            "vouches_invalidated": vouches_given,
            "resources_unreachable": 0,
            "mitigation_steps": [
                "Revoke all vouches by this member",
                "Alert cells where they are a member",
                "Identify replacement vouchers for affected members",
            ],
        }

    async def _model_cell_loss(
        self,
        conn: sqlite3.Connection,
        vouch_conn: sqlite3.Connection,
        cell_id: str
    ) -> Dict:
        """Model impact of losing an entire cell."""
        cursor = conn.cursor()

        # Get member count
        cursor.execute("""
            SELECT COUNT(*) FROM cell_memberships
            WHERE cell_id = ? AND is_active = 1
        """, (cell_id,))
        members_affected = cursor.fetchone()[0]

        return {
            "members_affected": members_affected,
            "cells_affected": 1,
            "trust_graph_impact": 5.0,  # Estimate
            "recovery_time_estimate_days": 7,
            "vouches_invalidated": 0,
            "resources_unreachable": members_affected * 2,  # Estimate
            "mitigation_steps": [
                "Connect displaced members to nearby cells",
                "Preserve trust relationships",
                "Redistribute resources",
            ],
        }
