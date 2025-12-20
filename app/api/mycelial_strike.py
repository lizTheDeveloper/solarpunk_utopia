"""Mycelial Strike API

Endpoints for automated solidarity defense against extractive behavior.

'Mutual Aid includes Mutual Defense.' - Peter Kropotkin
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.mycelial_strike_service import MycelialStrikeService
from app.models.mycelial_strike import AbuseType, OverrideAction, ThrottleLevel
from app.auth.middleware import get_current_user, require_steward
from app.auth.models import User

router = APIRouter(prefix="/api/mycelial-strike", tags=["mycelial-strike"])


# ===== Request/Response Models =====

class EvidenceItemRequest(BaseModel):
    """Evidence for a warlord alert."""
    type: str
    details: str
    reliability_score: float = 1.0


class CreateWarlordAlertRequest(BaseModel):
    """Request to create a Warlord Alert."""
    target_user_id: str
    severity: int = Field(..., ge=1, le=10)
    abuse_type: AbuseType
    evidence: List[EvidenceItemRequest]
    reporting_node_fingerprint: str
    reporting_user_id: Optional[str] = None
    trusted_source: bool = True


class UpdateBehaviorRequest(BaseModel):
    """Request to update user behavior tracking."""
    user_id: str
    exchanges_given: int = 0
    exchanges_received: int = 0
    offers_posted: int = 0
    needs_posted: int = 0


class OverrideStrikeRequest(BaseModel):
    """Request to override a strike."""
    strike_id: str
    action: OverrideAction
    reason: str = Field(..., min_length=10)


class WhitelistUserRequest(BaseModel):
    """Request to whitelist a user from automatic strikes."""
    user_id: str
    reason: str = Field(..., min_length=10)
    scope: str = Field(default='all', description="'all' or 'specific_abuse_type'")
    abuse_type: Optional[AbuseType] = None
    is_permanent: bool = False
    duration_days: Optional[int] = 30


class WarlordAlertResponse(BaseModel):
    """Response for a Warlord Alert."""
    id: str
    target_user_id: str
    severity: int
    abuse_type: str
    evidence: List[Dict[str, Any]]
    reporting_node_fingerprint: str
    reporting_user_id: Optional[str]
    trusted_source: bool
    propagation_count: int
    created_at: datetime
    expires_at: datetime
    cancelled: bool
    cancelled_by: Optional[str]
    cancellation_reason: Optional[str]
    cancelled_at: Optional[datetime]


class LocalStrikeResponse(BaseModel):
    """Response for a Local Strike."""
    id: str
    alert_id: str
    target_user_id: str
    throttle_level: str
    throttle_actions: Dict[str, Any]
    status: str
    automatic: bool
    behavior_score_at_start: float
    current_behavior_score: float
    activated_at: datetime
    deactivated_at: Optional[datetime]
    overridden_by: Optional[str]
    override_reason: Optional[str]
    overridden_at: Optional[datetime]


class StrikeStatusResponse(BaseModel):
    """Response for strike status (transparency view)."""
    under_strike: bool
    strikes: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    current_behavior: Optional[Dict[str, Any]]
    how_to_improve: List[str]


# ===== Dependency Injection =====

def get_mycelial_strike_service() -> MycelialStrikeService:
    """Get Mycelial Strike service instance."""
    return MycelialStrikeService(db_path="data/dtn_bundles.db")


# ===== Alert Endpoints =====

@router.post("/alert", response_model=WarlordAlertResponse)
async def create_warlord_alert(
    request: CreateWarlordAlertRequest,
    current_user: dict = Depends(get_current_user),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Create a Warlord Alert about extractive behavior.

    Called by Counter-Power Agent when abuse is detected.
    Automatically propagates through the mesh to trigger solidarity strikes.
    """
    try:
        from app.models.mycelial_strike import EvidenceItem

        evidence = [
            EvidenceItem(
                type=e.type,
                details=e.details,
                reliability_score=e.reliability_score
            )
            for e in request.evidence
        ]

        alert = service.create_warlord_alert(
            target_user_id=request.target_user_id,
            severity=request.severity,
            abuse_type=request.abuse_type,
            evidence=evidence,
            reporting_node_fingerprint=request.reporting_node_fingerprint,
            reporting_user_id=request.reporting_user_id,
            trusted_source=request.trusted_source,
        )

        return WarlordAlertResponse(
            id=alert.id,
            target_user_id=alert.target_user_id,
            severity=alert.severity,
            abuse_type=alert.abuse_type.value,
            evidence=[
                {
                    'type': e.type,
                    'details': e.details,
                    'reliability_score': e.reliability_score
                }
                for e in alert.evidence
            ],
            reporting_node_fingerprint=alert.reporting_node_fingerprint,
            reporting_user_id=alert.reporting_user_id,
            trusted_source=alert.trusted_source,
            propagation_count=alert.propagation_count,
            created_at=alert.created_at,
            expires_at=alert.expires_at,
            cancelled=alert.cancelled,
            cancelled_by=alert.cancelled_by,
            cancellation_reason=alert.cancellation_reason,
            cancelled_at=alert.cancelled_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Strike Endpoints =====

@router.get("/strike/status/{user_id}", response_model=StrikeStatusResponse)
async def get_strike_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Get strike status for a user (transparency view).

    Shows:
    - What behavior triggered the strike
    - Current throttle level
    - What to do to improve
    - How to appeal to stewards

    The system teaches, not just punishes.
    """
    status = service.get_strike_status_for_user(user_id)
    return StrikeStatusResponse(**status)


@router.get("/strike/active/{user_id}", response_model=List[LocalStrikeResponse])
async def get_active_strikes(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Get all active strikes against a user."""
    strikes = service.get_active_strikes_for_user(user_id)

    return [
        LocalStrikeResponse(
            id=strike.id,
            alert_id=strike.alert_id,
            target_user_id=strike.target_user_id,
            throttle_level=strike.throttle_level.value,
            throttle_actions={
                'deprioritize_matching': strike.throttle_actions.deprioritize_matching,
                'add_message_latency': strike.throttle_actions.add_message_latency,
                'reduce_proposal_visibility': strike.throttle_actions.reduce_proposal_visibility,
                'show_warning_indicator': strike.throttle_actions.show_warning_indicator,
                'block_high_value_exchanges': strike.throttle_actions.block_high_value_exchanges,
            },
            status=strike.status.value,
            automatic=strike.automatic,
            behavior_score_at_start=strike.behavior_score_at_start,
            current_behavior_score=strike.current_behavior_score,
            activated_at=strike.activated_at,
            deactivated_at=strike.deactivated_at,
            overridden_by=strike.overridden_by,
            override_reason=strike.override_reason,
            overridden_at=strike.overridden_at,
        )
        for strike in strikes
    ]


# ===== Behavior Tracking Endpoints =====

@router.post("/behavior/update")
async def update_behavior(
    request: UpdateBehaviorRequest,
    current_user: dict = Depends(get_current_user),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Update behavior tracking for a user.

    Called when user completes exchanges, posts offers/needs.
    Automatically checks for de-escalation if behavior improves.
    """
    try:
        service.update_user_behavior(
            user_id=request.user_id,
            exchanges_given=request.exchanges_given,
            exchanges_received=request.exchanges_received,
            offers_posted=request.offers_posted,
            needs_posted=request.needs_posted,
        )
        return {"status": "behavior_updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Steward Oversight Endpoints =====

@router.post("/strike/override")
async def override_strike(
    request: OverrideStrikeRequest,
    current_user: User = Depends(require_steward),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Override a strike (steward action).

    Actions:
    - Cancel strike
    - Cancel alert
    - Adjust severity
    - Whitelist user

    Used for false positives or special cases.
    All overrides are logged for accountability.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        service.override_strike(
            strike_id=request.strike_id,
            steward_user_id=current_user.id,
            action=request.action,
            reason=request.reason,
        )
        return {"status": "strike_overridden"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user/whitelist")
async def whitelist_user(
    request: WhitelistUserRequest,
    current_user: User = Depends(require_steward),
    service: MycelialStrikeService = Depends(get_mycelial_strike_service)
):
    """Whitelist a user from automatic strikes (steward action).

    Used for:
    - False positives
    - Special circumstances
    - Users under manual oversight

    Can be scoped to all abuse types or specific ones.
    Can be permanent or temporary.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        entry = service.whitelist_user(
            user_id=request.user_id,
            steward_user_id=current_user.id,
            reason=request.reason,
            scope=request.scope,
            abuse_type=request.abuse_type,
            is_permanent=request.is_permanent,
            duration_days=request.duration_days,
        )
        return {
            "status": "user_whitelisted",
            "whitelist_id": entry.id,
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Health Check Endpoint =====

@router.get("/health")
async def health_check():
    """Health check for Mycelial Strike system.

    Returns system status and basic metrics.
    """
    return {
        "status": "operational",
        "system": "mycelial_strike",
        "description": "Automated solidarity defense - No committee meetings required",
    }
