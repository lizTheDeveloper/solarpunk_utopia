"""
API endpoints for Resilience Metrics

Network health monitoring: density, flow, redundancy, velocity, recovery, coverage, decentralization.

PRIVACY: All metrics are AGGREGATES. No individual data exposed.
ARCHITECTURE: Local-first computation, works offline.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.resilience_metrics import (
    NetworkHealth,
    CellHealth,
    VulnerabilityReport,
    FlowAnalysis,
    ThreatScenario,
    HealthTrend,
    ResilienceDimension,
)
from app.services.resilience_metrics_service import ResilienceMetricsService
from app.api.cells import get_current_user
from app.auth.middleware import require_steward
from app.auth.models import User

router = APIRouter(prefix="/resilience", tags=["resilience"])


# Request models
class ComputeHealthRequest(BaseModel):
    """Request to compute network or cell health."""
    period_days: int = 30


class ThreatScenarioRequest(BaseModel):
    """Request to run a threat scenario."""
    scenario_name: str
    scenario_type: str  # 'member_compromised', 'cell_lost', 'bridge_broken'
    target_ids: List[str]


# ============================================================
# NETWORK HEALTH ENDPOINTS
# ============================================================

@router.get("/network/health", response_model=NetworkHealth)
async def get_network_health(
    compute_fresh: bool = False,
    period_days: int = 30
):
    """
    Get network health metrics.

    If compute_fresh=true, computes new snapshot.
    Otherwise returns latest cached snapshot.

    Available to all members (aggregate data only).
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    if compute_fresh:
        health = await service.compute_network_health(period_days=period_days)
    else:
        health = service.repository.get_latest_network_health()

        if not health:
            # No cached data, compute fresh
            health = await service.compute_network_health(period_days=period_days)

    return health


@router.get("/network/health/history", response_model=List[NetworkHealth])
async def get_network_health_history(days: int = 30):
    """
    Get network health history for the last N days.

    Returns time series of health snapshots.
    Available to all members.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    history = service.repository.get_network_health_history(days=days)

    return history


@router.post("/network/health/compute", response_model=NetworkHealth)
async def compute_network_health(
    request: ComputeHealthRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Manually trigger network health computation.

    Requires authentication. Useful for stewards to get fresh data.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    health = await service.compute_network_health(period_days=request.period_days)

    return health


# ============================================================
# CELL HEALTH ENDPOINTS
# ============================================================

@router.get("/cells/{cell_id}/health", response_model=CellHealth)
async def get_cell_health(
    cell_id: str,
    compute_fresh: bool = False,
    period_days: int = 30,
    user_id: str = Depends(get_current_user)
):
    """
    Get health metrics for a specific cell.

    Only visible to cell stewards (privacy).
    If compute_fresh=true, computes new snapshot.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    # Verify user is a steward of this cell
    await _verify_cell_steward(cell_id, user_id)

    if compute_fresh:
        health = await service.compute_cell_health(cell_id=cell_id, period_days=period_days)
    else:
        health = service.repository.get_latest_cell_health(cell_id=cell_id)

        if not health:
            # No cached data, compute fresh
            health = await service.compute_cell_health(cell_id=cell_id, period_days=period_days)

    return health


@router.get("/cells/health", response_model=List[CellHealth])
async def get_all_cell_health(
    user_id: str = Depends(get_current_user)
):
    """
    Get health for all cells.

    Network-wide view. Only shows aggregate cell data, no individual members.
    Available to all authenticated users.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    health_list = service.repository.get_all_cell_health()

    return health_list


@router.post("/cells/{cell_id}/health/compute", response_model=CellHealth)
async def compute_cell_health(
    cell_id: str,
    request: ComputeHealthRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Manually trigger cell health computation.

    Only cell stewards can trigger computation.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    # Verify user is a steward of this cell
    await _verify_cell_steward(cell_id, user_id)

    health = await service.compute_cell_health(cell_id=cell_id, period_days=request.period_days)

    return health


# ============================================================
# VULNERABILITY ANALYSIS ENDPOINTS
# ============================================================

@router.get("/vulnerability", response_model=VulnerabilityReport)
async def get_vulnerability_report(
    compute_fresh: bool = False,
    user_id: str = Depends(get_current_user)
):
    """
    Get vulnerability report showing single points of failure.

    Requires authentication (sensitive data).
    If compute_fresh=true, computes new report.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    if compute_fresh:
        report = await service.compute_vulnerability_report()
    else:
        report = service.repository.get_latest_vulnerability_report()

        if not report:
            # No cached data, compute fresh
            report = await service.compute_vulnerability_report()

    return report


@router.post("/vulnerability/compute", response_model=VulnerabilityReport)
async def compute_vulnerability_report(
    user_id: str = Depends(get_current_user)
):
    """
    Manually trigger vulnerability analysis.

    Requires authentication. Computationally intensive.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    report = await service.compute_vulnerability_report()

    return report


# ============================================================
# FLOW ANALYSIS ENDPOINTS
# ============================================================

@router.get("/flow", response_model=FlowAnalysis)
async def get_flow_analysis(
    compute_fresh: bool = False,
    period_days: int = 30,
    user_id: str = Depends(get_current_user)
):
    """
    Get resource flow analysis between cells.

    Shows aggregate flows only - no individual transactions.
    Requires authentication.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    if compute_fresh:
        analysis = await service.compute_flow_analysis(period_days=period_days)
    else:
        analysis = service.repository.get_latest_flow_analysis()

        if not analysis:
            # No cached data, compute fresh
            analysis = await service.compute_flow_analysis(period_days=period_days)

    return analysis


@router.post("/flow/compute", response_model=FlowAnalysis)
async def compute_flow_analysis(
    request: ComputeHealthRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Manually trigger flow analysis.

    Requires authentication.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    analysis = await service.compute_flow_analysis(period_days=request.period_days)

    return analysis


# ============================================================
# THREAT MODELING ENDPOINTS
# ============================================================

@router.post("/threat/scenario", response_model=ThreatScenario)
async def run_threat_scenario(
    request: ThreatScenarioRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Run a "what if" threat scenario.

    Examples:
    - "What if Alice is compromised?"
    - "What if we lose the downtown cell?"
    - "What if the bridge connection breaks?"

    Requires authentication. Stewards use this for resilience planning.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    scenario = await service.run_threat_scenario(
        scenario_name=request.scenario_name,
        scenario_type=request.scenario_type,
        target_ids=request.target_ids,
        run_by=user_id,
    )

    return scenario


@router.get("/threat/scenarios", response_model=List[ThreatScenario])
async def get_threat_scenarios(
    limit: int = 10,
    user_id: str = Depends(get_current_user)
):
    """
    Get recent threat scenario runs.

    Shows history of "what if" analyses.
    Requires authentication.
    """
    service = ResilienceMetricsService(db_path="data/cells.db")
    scenarios = service.repository.get_threat_scenarios(limit=limit)

    return scenarios


# ============================================================
# TREND ANALYSIS ENDPOINTS
# ============================================================

@router.get("/trends/{dimension}", response_model=Optional[HealthTrend])
async def get_health_trend(
    dimension: ResilienceDimension,
    cell_id: Optional[str] = None,
    days: int = 30,
    user: User = Depends(get_current_user)
):
    """
    Get health trend for a specific dimension.

    Shows how a dimension has changed over time.
    If cell_id provided, shows cell-level trend. Otherwise network-level.

    Available to all members for network trends.
    Cell trends require steward access.

    GAP-134: Steward verification via trust score >= 0.9 (for cell-level trends)
    """
    service = ResilienceMetricsService(db_path="data/cells.db")

    # Verify steward access for cell-level trends
    if cell_id:
        from app.auth.middleware import get_vouch_repo, get_trust_service, STEWARD_TRUST_THRESHOLD
        vouch_repo = get_vouch_repo()
        trust_service = get_trust_service(vouch_repo)
        trust_score = trust_service.compute_trust_score(user.id)

        if trust_score.computed_trust < STEWARD_TRUST_THRESHOLD:
            raise HTTPException(
                status_code=403,
                detail=f"Steward access required for cell-level trends (trust >= {STEWARD_TRUST_THRESHOLD})"
            )

    trend = service.repository.get_health_trend(
        dimension=dimension,
        cell_id=cell_id,
        days=days
    )

    return trend


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _verify_cell_steward(cell_id: str, user_id: str):
    """Verify that user is a steward of the given cell."""
    from app.database import get_db

    db = await get_db()

    cursor = await db.execute("""
        SELECT role FROM cell_memberships
        WHERE cell_id = ? AND user_id = ? AND is_active = 1
    """, (cell_id, user_id))

    membership = await cursor.fetchone()

    if not membership or membership[0] != 'steward':
        raise HTTPException(
            status_code=403,
            detail="Only cell stewards can access this endpoint"
        )
