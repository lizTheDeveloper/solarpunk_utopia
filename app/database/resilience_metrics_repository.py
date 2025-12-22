"""Repository for Resilience Metrics data access

Network health monitoring: density, flow, redundancy, velocity, recovery, coverage, decentralization.
All metrics are AGGREGATES - no individual visibility (privacy by design).
"""
import sqlite3
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, UTC
import uuid
import json
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


class ResilienceMetricsRepository:
    """Database access for resilience metrics.

    PRIVACY: All metrics are aggregates. No individual data exposed.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Create resilience metrics tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Network health snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_health_snapshots (
                id TEXT PRIMARY KEY,
                snapshot_time TEXT NOT NULL,
                overall_score REAL NOT NULL,
                status TEXT NOT NULL,
                density_score REAL NOT NULL,
                flow_score REAL NOT NULL,
                redundancy_score REAL NOT NULL,
                velocity_score REAL NOT NULL,
                recovery_score REAL NOT NULL,
                coverage_score REAL NOT NULL,
                decentralization_score REAL NOT NULL,
                total_members INTEGER NOT NULL,
                total_cells INTEGER NOT NULL,
                total_exchanges INTEGER NOT NULL,
                avg_connections_per_member REAL NOT NULL,
                median_match_time_hours REAL,
                needs_match_rate REAL NOT NULL,
                critical_dimensions TEXT,
                warning_dimensions TEXT,
                measurement_period_days INTEGER DEFAULT 30,
                created_at TEXT NOT NULL
            )
        """)

        # Cell health snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cell_health_snapshots (
                id TEXT PRIMARY KEY,
                cell_id TEXT NOT NULL,
                snapshot_time TEXT NOT NULL,
                cell_score REAL NOT NULL,
                status TEXT NOT NULL,
                active_members INTEGER NOT NULL,
                avg_connections_per_member REAL NOT NULL,
                exchanges_completed INTEGER NOT NULL,
                flow_rate REAL NOT NULL,
                median_match_time_hours REAL,
                needs_match_rate REAL NOT NULL,
                vs_network_connections REAL NOT NULL,
                vs_network_flow REAL NOT NULL,
                recommendations TEXT,
                measurement_period_days INTEGER DEFAULT 30,
                created_at TEXT NOT NULL
            )
        """)

        # Vulnerability reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerability_reports (
                id TEXT PRIMARY KEY,
                report_time TEXT NOT NULL,
                critical_nodes TEXT,
                critical_edges TEXT,
                isolated_cells TEXT,
                redundancy_recommendations TEXT,
                vulnerability_score REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Flow analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flow_analyses (
                id TEXT PRIMARY KEY,
                analysis_time TEXT NOT NULL,
                period_days INTEGER NOT NULL,
                flows TEXT,
                cell_balances TEXT,
                imbalanced_cells TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # Threat scenarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_scenarios (
                id TEXT PRIMARY KEY,
                scenario_name TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                target_ids TEXT NOT NULL,
                members_affected INTEGER NOT NULL,
                cells_affected INTEGER NOT NULL,
                trust_graph_impact REAL NOT NULL,
                recovery_time_estimate_days INTEGER NOT NULL,
                vouches_invalidated INTEGER DEFAULT 0,
                resources_unreachable INTEGER DEFAULT 0,
                mitigation_steps TEXT,
                run_at TEXT NOT NULL,
                run_by TEXT NOT NULL
            )
        """)

        # Health trends
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_trends (
                id TEXT PRIMARY KEY,
                dimension TEXT NOT NULL,
                cell_id TEXT,
                datapoints TEXT NOT NULL,
                trend_direction TEXT NOT NULL,
                rate_of_change REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_network_health_time ON network_health_snapshots(snapshot_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cell_health_cell ON cell_health_snapshots(cell_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cell_health_time ON cell_health_snapshots(snapshot_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vulnerability_time ON vulnerability_reports(report_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_flow_time ON flow_analyses(analysis_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_dimension ON health_trends(dimension)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_cell ON health_trends(cell_id)")

        conn.commit()
        conn.close()

    # ============================================================
    # NETWORK HEALTH
    # ============================================================

    def save_network_health(self, health: NetworkHealth) -> NetworkHealth:
        """Save a network health snapshot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO network_health_snapshots (
                id, snapshot_time, overall_score, status,
                density_score, flow_score, redundancy_score, velocity_score,
                recovery_score, coverage_score, decentralization_score,
                total_members, total_cells, total_exchanges,
                avg_connections_per_member, median_match_time_hours, needs_match_rate,
                critical_dimensions, warning_dimensions, measurement_period_days, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            health.id,
            health.snapshot_time.isoformat(),
            health.overall_score,
            health.status.value,
            health.density_score,
            health.flow_score,
            health.redundancy_score,
            health.velocity_score,
            health.recovery_score,
            health.coverage_score,
            health.decentralization_score,
            health.total_members,
            health.total_cells,
            health.total_exchanges,
            health.avg_connections_per_member,
            health.median_match_time_hours,
            health.needs_match_rate,
            json.dumps(health.critical_dimensions),
            json.dumps(health.warning_dimensions),
            health.measurement_period_days,
            health.created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return health

    def get_latest_network_health(self) -> Optional[NetworkHealth]:
        """Get the most recent network health snapshot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM network_health_snapshots
            ORDER BY snapshot_time DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_network_health(row)

    def get_network_health_history(self, days: int = 30) -> List[NetworkHealth]:
        """Get network health history for the last N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        cursor.execute("""
            SELECT * FROM network_health_snapshots
            WHERE snapshot_time >= ?
            ORDER BY snapshot_time ASC
        """, (since,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_network_health(row) for row in rows]

    def _row_to_network_health(self, row) -> NetworkHealth:
        """Convert database row to NetworkHealth model."""
        return NetworkHealth(
            id=row[0],
            snapshot_time=datetime.fromisoformat(row[1]),
            overall_score=row[2],
            status=HealthStatus(row[3]),
            density_score=row[4],
            flow_score=row[5],
            redundancy_score=row[6],
            velocity_score=row[7],
            recovery_score=row[8],
            coverage_score=row[9],
            decentralization_score=row[10],
            total_members=row[11],
            total_cells=row[12],
            total_exchanges=row[13],
            avg_connections_per_member=row[14],
            median_match_time_hours=row[15],
            needs_match_rate=row[16],
            critical_dimensions=json.loads(row[17]) if row[17] else [],
            warning_dimensions=json.loads(row[18]) if row[18] else [],
            measurement_period_days=row[19],
            created_at=datetime.fromisoformat(row[20]),
        )

    # ============================================================
    # CELL HEALTH
    # ============================================================

    def save_cell_health(self, health: CellHealth) -> CellHealth:
        """Save a cell health snapshot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cell_health_snapshots (
                id, cell_id, snapshot_time, cell_score, status,
                active_members, avg_connections_per_member, exchanges_completed,
                flow_rate, median_match_time_hours, needs_match_rate,
                vs_network_connections, vs_network_flow,
                recommendations, measurement_period_days, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            health.id,
            health.cell_id,
            health.snapshot_time.isoformat(),
            health.cell_score,
            health.status.value,
            health.active_members,
            health.avg_connections_per_member,
            health.exchanges_completed,
            health.flow_rate,
            health.median_match_time_hours,
            health.needs_match_rate,
            health.vs_network_connections,
            health.vs_network_flow,
            json.dumps(health.recommendations),
            health.measurement_period_days,
            health.created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return health

    def get_latest_cell_health(self, cell_id: str) -> Optional[CellHealth]:
        """Get the most recent health snapshot for a cell."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cell_health_snapshots
            WHERE cell_id = ?
            ORDER BY snapshot_time DESC
            LIMIT 1
        """, (cell_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_cell_health(row)

    def get_all_cell_health(self) -> List[CellHealth]:
        """Get latest health for all cells."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get latest snapshot for each cell
        cursor.execute("""
            SELECT * FROM cell_health_snapshots
            WHERE id IN (
                SELECT id FROM cell_health_snapshots AS chs1
                WHERE snapshot_time = (
                    SELECT MAX(snapshot_time) FROM cell_health_snapshots AS chs2
                    WHERE chs2.cell_id = chs1.cell_id
                )
            )
            ORDER BY cell_score ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_cell_health(row) for row in rows]

    def _row_to_cell_health(self, row) -> CellHealth:
        """Convert database row to CellHealth model."""
        return CellHealth(
            id=row[0],
            cell_id=row[1],
            snapshot_time=datetime.fromisoformat(row[2]),
            cell_score=row[3],
            status=HealthStatus(row[4]),
            active_members=row[5],
            avg_connections_per_member=row[6],
            exchanges_completed=row[7],
            flow_rate=row[8],
            median_match_time_hours=row[9],
            needs_match_rate=row[10],
            vs_network_connections=row[11],
            vs_network_flow=row[12],
            recommendations=json.loads(row[13]) if row[13] else [],
            measurement_period_days=row[14],
            created_at=datetime.fromisoformat(row[15]),
        )

    # ============================================================
    # VULNERABILITY REPORTS
    # ============================================================

    def save_vulnerability_report(self, report: VulnerabilityReport) -> VulnerabilityReport:
        """Save a vulnerability report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO vulnerability_reports (
                id, report_time, critical_nodes, critical_edges,
                isolated_cells, redundancy_recommendations, vulnerability_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report.id,
            report.report_time.isoformat(),
            json.dumps(report.critical_nodes),
            json.dumps(report.critical_edges),
            json.dumps(report.isolated_cells),
            json.dumps(report.redundancy_recommendations),
            report.vulnerability_score,
            report.created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return report

    def get_latest_vulnerability_report(self) -> Optional[VulnerabilityReport]:
        """Get the most recent vulnerability report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM vulnerability_reports
            ORDER BY report_time DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_vulnerability_report(row)

    def _row_to_vulnerability_report(self, row) -> VulnerabilityReport:
        """Convert database row to VulnerabilityReport model."""
        return VulnerabilityReport(
            id=row[0],
            report_time=datetime.fromisoformat(row[1]),
            critical_nodes=json.loads(row[2]) if row[2] else [],
            critical_edges=json.loads(row[3]) if row[3] else [],
            isolated_cells=json.loads(row[4]) if row[4] else [],
            redundancy_recommendations=json.loads(row[5]) if row[5] else [],
            vulnerability_score=row[6],
            created_at=datetime.fromisoformat(row[7]),
        )

    # ============================================================
    # FLOW ANALYSIS
    # ============================================================

    def save_flow_analysis(self, analysis: FlowAnalysis) -> FlowAnalysis:
        """Save a flow analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO flow_analyses (
                id, analysis_time, period_days, flows, cell_balances,
                imbalanced_cells, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis.id,
            analysis.analysis_time.isoformat(),
            analysis.period_days,
            json.dumps(analysis.flows),
            json.dumps(analysis.cell_balances),
            json.dumps(analysis.imbalanced_cells),
            analysis.created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return analysis

    def get_latest_flow_analysis(self) -> Optional[FlowAnalysis]:
        """Get the most recent flow analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM flow_analyses
            ORDER BY analysis_time DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_flow_analysis(row)

    def _row_to_flow_analysis(self, row) -> FlowAnalysis:
        """Convert database row to FlowAnalysis model."""
        return FlowAnalysis(
            id=row[0],
            analysis_time=datetime.fromisoformat(row[1]),
            period_days=row[2],
            flows=json.loads(row[3]) if row[3] else [],
            cell_balances=json.loads(row[4]) if row[4] else [],
            imbalanced_cells=json.loads(row[5]) if row[5] else [],
            created_at=datetime.fromisoformat(row[6]),
        )

    # ============================================================
    # THREAT SCENARIOS
    # ============================================================

    def save_threat_scenario(self, scenario: ThreatScenario) -> ThreatScenario:
        """Save a threat scenario analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO threat_scenarios (
                id, scenario_name, scenario_type, target_ids,
                members_affected, cells_affected, trust_graph_impact,
                recovery_time_estimate_days, vouches_invalidated,
                resources_unreachable, mitigation_steps, run_at, run_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scenario.id,
            scenario.scenario_name,
            scenario.scenario_type,
            json.dumps(scenario.target_ids),
            scenario.members_affected,
            scenario.cells_affected,
            scenario.trust_graph_impact,
            scenario.recovery_time_estimate_days,
            scenario.vouches_invalidated,
            scenario.resources_unreachable,
            json.dumps(scenario.mitigation_steps),
            scenario.run_at.isoformat(),
            scenario.run_by,
        ))

        conn.commit()
        conn.close()

        return scenario

    def get_threat_scenarios(self, limit: int = 10) -> List[ThreatScenario]:
        """Get recent threat scenarios."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM threat_scenarios
            ORDER BY run_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_threat_scenario(row) for row in rows]

    def _row_to_threat_scenario(self, row) -> ThreatScenario:
        """Convert database row to ThreatScenario model."""
        return ThreatScenario(
            id=row[0],
            scenario_name=row[1],
            scenario_type=row[2],
            target_ids=json.loads(row[3]) if row[3] else [],
            members_affected=row[4],
            cells_affected=row[5],
            trust_graph_impact=row[6],
            recovery_time_estimate_days=row[7],
            vouches_invalidated=row[8],
            resources_unreachable=row[9],
            mitigation_steps=json.loads(row[10]) if row[10] else [],
            run_at=datetime.fromisoformat(row[11]),
            run_by=row[12],
        )

    # ============================================================
    # HEALTH TRENDS
    # ============================================================

    def save_health_trend(self, trend: HealthTrend) -> HealthTrend:
        """Save a health trend analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO health_trends (
                id, dimension, cell_id, datapoints, trend_direction,
                rate_of_change, start_date, end_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trend.id,
            trend.dimension.value,
            trend.cell_id,
            json.dumps(trend.datapoints),
            trend.trend_direction,
            trend.rate_of_change,
            trend.start_date.isoformat(),
            trend.end_date.isoformat(),
            trend.created_at.isoformat(),
        ))

        conn.commit()
        conn.close()

        return trend

    def get_health_trend(
        self,
        dimension: ResilienceDimension,
        cell_id: Optional[str] = None,
        days: int = 30
    ) -> Optional[HealthTrend]:
        """Get health trend for a dimension."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        since = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        if cell_id:
            cursor.execute("""
                SELECT * FROM health_trends
                WHERE dimension = ? AND cell_id = ? AND end_date >= ?
                ORDER BY end_date DESC
                LIMIT 1
            """, (dimension.value, cell_id, since))
        else:
            cursor.execute("""
                SELECT * FROM health_trends
                WHERE dimension = ? AND cell_id IS NULL AND end_date >= ?
                ORDER BY end_date DESC
                LIMIT 1
            """, (dimension.value, since))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_health_trend(row)

    def _row_to_health_trend(self, row) -> HealthTrend:
        """Convert database row to HealthTrend model."""
        return HealthTrend(
            id=row[0],
            dimension=ResilienceDimension(row[1]),
            cell_id=row[2],
            datapoints=json.loads(row[3]) if row[3] else [],
            trend_direction=row[4],
            rate_of_change=row[5],
            start_date=datetime.fromisoformat(row[6]),
            end_date=datetime.fromisoformat(row[7]),
            created_at=datetime.fromisoformat(row[8]),
        )
