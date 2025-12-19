"""Resilience Metrics - Network Health Monitoring

How do we know if the network is working? Not just "are there users" but:
- Are cells healthy or dying?
- Are resources actually flowing?
- Are we building real resilience or just LARPing?
- Where are the weak points an adversary could exploit?

RESILIENCE DIMENSIONS:
- Density: Connections per person (>3 trusted connections)
- Flow: Resources actually moving (>1 exchange per member per month)
- Redundancy: Multiple paths exist (no single point of failure)
- Velocity: Speed of resource matching (<24 hours offer→match)
- Recovery: Bounce back from disruption (cells reform within 1 week)
- Coverage: Needs being met (>80% needs matched)
- Decentralization: No power concentration (no node >10% of activity)
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class HealthStatus(str, Enum):
    """Health status levels."""
    CRITICAL = "critical"    # Below 40%
    WARNING = "warning"      # 40-70%
    HEALTHY = "healthy"      # 70-90%
    EXCELLENT = "excellent"  # Above 90%


class ResilienceDimension(str, Enum):
    """Resilience measurement dimensions."""
    DENSITY = "density"                    # Connections per person
    FLOW = "flow"                          # Resources moving
    REDUNDANCY = "redundancy"              # Multiple paths
    VELOCITY = "velocity"                  # Match speed
    RECOVERY = "recovery"                  # Bounce back from disruption
    COVERAGE = "coverage"                  # Needs being met
    DECENTRALIZATION = "decentralization"  # No power concentration


class NetworkHealth(BaseModel):
    """Overall network health snapshot.

    Aggregated metrics across the entire network.
    """
    id: str = Field(description="Unique snapshot ID")
    snapshot_time: datetime = Field(description="When this was calculated")

    # Overall score (0-100)
    overall_score: float = Field(
        description="Composite resilience score (0-100)",
        ge=0,
        le=100
    )
    status: HealthStatus = Field(description="Overall health status")

    # Dimension scores (0-100 each)
    density_score: float = Field(description="Connections per person", ge=0, le=100)
    flow_score: float = Field(description="Resources moving", ge=0, le=100)
    redundancy_score: float = Field(description="Multiple paths exist", ge=0, le=100)
    velocity_score: float = Field(description="Match speed", ge=0, le=100)
    recovery_score: float = Field(description="Bounce back ability", ge=0, le=100)
    coverage_score: float = Field(description="Needs being met", ge=0, le=100)
    decentralization_score: float = Field(description="No power concentration", ge=0, le=100)

    # Raw metrics
    total_members: int = Field(description="Total active members")
    total_cells: int = Field(description="Total active cells")
    total_exchanges: int = Field(description="Exchanges in measurement period")
    avg_connections_per_member: float = Field(description="Average trusted connections")
    median_match_time_hours: Optional[float] = Field(
        default=None,
        description="Median time from offer to match (hours)"
    )
    needs_match_rate: float = Field(
        description="Percentage of needs that got matched",
        ge=0,
        le=100
    )

    # Alerts
    critical_dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensions below critical threshold"
    )
    warning_dimensions: List[str] = Field(
        default_factory=list,
        description="Dimensions below warning threshold"
    )

    # Metadata
    measurement_period_days: int = Field(
        default=30,
        description="How many days this measurement covers"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_status_from_score(score: float) -> HealthStatus:
        """Convert score to status."""
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 70:
            return HealthStatus.HEALTHY
        elif score >= 40:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL

    class Config:
        json_schema_extra = {
            "example": {
                "id": "snapshot-001",
                "snapshot_time": "2025-12-19T12:00:00Z",
                "overall_score": 78.5,
                "status": "healthy",
                "density_score": 85.0,
                "flow_score": 72.0,
                "redundancy_score": 90.0,
                "velocity_score": 65.0,
                "recovery_score": 80.0,
                "coverage_score": 75.0,
                "decentralization_score": 88.0,
                "total_members": 5420,
                "total_cells": 127,
                "total_exchanges": 1234,
                "avg_connections_per_member": 4.2,
                "median_match_time_hours": 18.5,
                "needs_match_rate": 75.0,
                "critical_dimensions": [],
                "warning_dimensions": ["velocity"],
                "measurement_period_days": 30,
            }
        }


class CellHealth(BaseModel):
    """Health metrics for a specific cell.

    Per-cell breakdown visible to cell stewards.
    """
    id: str = Field(description="Unique snapshot ID")
    cell_id: str = Field(description="Cell being measured")
    snapshot_time: datetime = Field(description="When this was calculated")

    # Overall cell score
    cell_score: float = Field(
        description="Overall cell health (0-100)",
        ge=0,
        le=100
    )
    status: HealthStatus = Field(description="Cell health status")

    # Cell metrics
    active_members: int = Field(description="Active members in cell")
    avg_connections_per_member: float = Field(description="Average connections")
    exchanges_completed: int = Field(description="Exchanges in period")
    flow_rate: float = Field(description="Exchanges per member per month")
    median_match_time_hours: Optional[float] = Field(
        default=None,
        description="Median match time (hours)"
    )
    needs_match_rate: float = Field(
        description="Percentage of needs matched",
        ge=0,
        le=100
    )

    # Comparison to network
    vs_network_connections: float = Field(
        description="% difference from network average connections"
    )
    vs_network_flow: float = Field(
        description="% difference from network average flow"
    )

    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Specific suggestions for improvement"
    )

    # Metadata
    measurement_period_days: int = Field(default=30)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "cell-snapshot-001",
                "cell_id": "cell-downtown",
                "snapshot_time": "2025-12-19T12:00:00Z",
                "cell_score": 72.0,
                "status": "healthy",
                "active_members": 45,
                "avg_connections_per_member": 3.8,
                "exchanges_completed": 23,
                "flow_rate": 0.51,
                "median_match_time_hours": 22.0,
                "needs_match_rate": 68.0,
                "vs_network_connections": -5.0,
                "vs_network_flow": +12.0,
                "recommendations": [
                    "Your cell needs more tool offers - only 2 tools listed",
                    "Consider organizing a skill share event to increase flow"
                ],
                "measurement_period_days": 30,
            }
        }


class VulnerabilityReport(BaseModel):
    """Single points of failure and network vulnerabilities.

    Identifies nodes/edges that if removed would harm network.
    """
    id: str = Field(description="Unique report ID")
    report_time: datetime = Field(description="When this was generated")

    # Critical nodes (too important)
    critical_nodes: List[Dict] = Field(
        default_factory=list,
        description="Nodes with >10% of network activity"
    )
    # Example:
    # {
    #   "node_id": "user-alice",
    #   "centrality_score": 0.15,
    #   "vouch_percentage": 12.0,
    #   "resource_percentage": 8.0,
    #   "risk": "If this member leaves, 15% of trust network lost"
    # }

    # Critical edges (bridges)
    critical_edges: List[Dict] = Field(
        default_factory=list,
        description="Edges that if removed isolate cells"
    )
    # Example:
    # {
    #   "from_cell": "cell-downtown",
    #   "to_cell": "cell-suburbs",
    #   "connection_count": 1,
    #   "risk": "Only one connection between these cells"
    # }

    # Isolated cells
    isolated_cells: List[str] = Field(
        default_factory=list,
        description="Cells with only one external connection"
    )

    # Recommendations
    redundancy_recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for adding redundancy"
    )

    # Overall vulnerability score
    vulnerability_score: float = Field(
        description="Overall vulnerability (0-100, lower is better)",
        ge=0,
        le=100
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "vuln-report-001",
                "report_time": "2025-12-19T12:00:00Z",
                "critical_nodes": [
                    {
                        "node_id": "user-alice",
                        "centrality_score": 0.15,
                        "vouch_percentage": 12.0,
                        "resource_percentage": 8.0,
                        "risk": "If this member leaves, 15% of trust network lost"
                    }
                ],
                "critical_edges": [
                    {
                        "from_cell": "cell-downtown",
                        "to_cell": "cell-suburbs",
                        "connection_count": 1,
                        "risk": "Only one connection between these cells"
                    }
                ],
                "isolated_cells": ["cell-rural-west"],
                "redundancy_recommendations": [
                    "Add connections between cell-downtown and cell-suburbs",
                    "Encourage user-alice to mentor new stewards",
                    "Create backup vouchers for isolated cells"
                ],
                "vulnerability_score": 35.0,
            }
        }


class FlowAnalysis(BaseModel):
    """Resource flow analysis between cells.

    Tracks actual resource movement (aggregates only).
    """
    id: str = Field(description="Unique analysis ID")
    analysis_time: datetime = Field(description="When this was generated")
    period_days: int = Field(description="Analysis period in days")

    # Cell-to-cell flows (aggregated)
    flows: List[Dict] = Field(
        default_factory=list,
        description="Aggregate flows between cells"
    )
    # Example:
    # {
    #   "from_cell": "cell-downtown",
    #   "to_cell": "cell-suburbs",
    #   "exchange_count": 23,
    #   "estimated_value": 1250.0,
    #   "primary_categories": ["tools", "food", "skills"]
    # }

    # Cell balance analysis
    cell_balances: List[Dict] = Field(
        default_factory=list,
        description="Each cell's giving vs receiving balance"
    )
    # Example:
    # {
    #   "cell_id": "cell-downtown",
    #   "resources_given": 45,
    #   "resources_received": 32,
    #   "balance": +13,
    #   "status": "net_giver"
    # }

    # Imbalances to monitor
    imbalanced_cells: List[Dict] = Field(
        default_factory=list,
        description="Cells with significant imbalance (>3:1 ratio)"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "flow-analysis-001",
                "analysis_time": "2025-12-19T12:00:00Z",
                "period_days": 30,
                "flows": [
                    {
                        "from_cell": "cell-downtown",
                        "to_cell": "cell-suburbs",
                        "exchange_count": 23,
                        "estimated_value": 1250.0,
                        "primary_categories": ["tools", "food"]
                    }
                ],
                "cell_balances": [
                    {
                        "cell_id": "cell-downtown",
                        "resources_given": 45,
                        "resources_received": 32,
                        "balance": +13,
                        "status": "net_giver"
                    }
                ],
                "imbalanced_cells": [],
            }
        }


class ThreatScenario(BaseModel):
    """Threat modeling scenario and impact analysis.

    "What if" analysis for resilience testing.
    """
    id: str = Field(description="Unique scenario ID")
    scenario_name: str = Field(description="Name of scenario")
    scenario_type: str = Field(
        description="Type: member_compromised, cell_lost, bridge_broken, etc."
    )

    # Scenario parameters
    target_ids: List[str] = Field(
        description="IDs of affected entities (users, cells, etc.)"
    )

    # Impact analysis
    members_affected: int = Field(description="Number of members impacted")
    cells_affected: int = Field(description="Number of cells impacted")
    trust_graph_impact: float = Field(
        description="% of trust graph affected (0-100)",
        ge=0,
        le=100
    )
    recovery_time_estimate_days: int = Field(
        description="Estimated days to recover"
    )

    # Specific impacts
    vouches_invalidated: int = Field(
        default=0,
        description="Trust relationships broken"
    )
    resources_unreachable: int = Field(
        default=0,
        description="Resources that become unavailable"
    )

    # Recommendations
    mitigation_steps: List[str] = Field(
        default_factory=list,
        description="Steps to mitigate this scenario"
    )

    # Metadata
    run_at: datetime = Field(default_factory=datetime.utcnow)
    run_by: str = Field(description="Who ran this scenario")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "scenario-001",
                "scenario_name": "Alice compromised",
                "scenario_type": "member_compromised",
                "target_ids": ["user-alice"],
                "members_affected": 47,
                "cells_affected": 3,
                "trust_graph_impact": 15.0,
                "recovery_time_estimate_days": 5,
                "vouches_invalidated": 23,
                "resources_unreachable": 8,
                "mitigation_steps": [
                    "Add redundant vouchers for Alice's vouches",
                    "Identify backup steward for her cells",
                    "Document her key relationships"
                ],
                "run_at": "2025-12-19T12:00:00Z",
                "run_by": "steward-pk-123"
            }
        }


class HealthTrend(BaseModel):
    """Historical trend of health metrics.

    Track network health over time.
    """
    id: str = Field(description="Unique trend ID")
    dimension: ResilienceDimension = Field(description="Which dimension")
    cell_id: Optional[str] = Field(
        default=None,
        description="Cell ID (null for network-wide)"
    )

    # Time series data
    datapoints: List[Dict] = Field(
        description="Time series of scores"
    )
    # Example:
    # {
    #   "timestamp": "2025-12-01T00:00:00Z",
    #   "score": 75.0,
    #   "status": "healthy"
    # }

    # Trend analysis
    trend_direction: str = Field(
        description="improving, declining, stable"
    )
    rate_of_change: float = Field(
        description="Score change per day"
    )

    # Metadata
    start_date: datetime = Field(description="Start of trend period")
    end_date: datetime = Field(description="End of trend period")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "trend-001",
                "dimension": "flow",
                "cell_id": None,
                "datapoints": [
                    {"timestamp": "2025-11-19T00:00:00Z", "score": 68.0, "status": "warning"},
                    {"timestamp": "2025-12-19T00:00:00Z", "score": 72.0, "status": "healthy"}
                ],
                "trend_direction": "improving",
                "rate_of_change": +0.13,
                "start_date": "2025-11-19T00:00:00Z",
                "end_date": "2025-12-19T00:00:00Z",
            }
        }
