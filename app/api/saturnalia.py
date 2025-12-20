"""Saturnalia Protocol API

Endpoints for managing role inversions and preventing power crystallization.

'All authority is a mask, not a face.' - Paulo Freire
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.services.saturnalia_service import SaturnaliaService
from app.models.saturnalia import SaturnaliaMode
from app.auth.middleware import get_current_user, require_steward
from app.auth.models import User

router = APIRouter(prefix="/api/saturnalia", tags=["saturnalia"])


# ===== Request/Response Models =====

class CreateConfigRequest(BaseModel):
    """Request to create a Saturnalia configuration."""
    enabled_modes: List[SaturnaliaMode] = Field(..., description="Which modes to enable")
    frequency: str = Field(..., description="annually, biannually, quarterly, or manual")
    duration_hours: int = Field(..., description="How long each event lasts")
    cell_id: Optional[str] = Field(default=None, description="Cell ID if cell-scoped")
    community_id: Optional[str] = Field(default=None, description="Community ID if community-scoped")
    exclude_safety_critical: bool = Field(default=True, description="Exclude panic/sanctuary/rapid response")
    allow_individual_opt_out: bool = Field(default=True, description="Allow users to opt out")


class UpdateConfigRequest(BaseModel):
    """Request to update a configuration."""
    enabled_modes: Optional[List[SaturnaliaMode]] = None
    frequency: Optional[str] = None
    duration_hours: Optional[int] = None
    enabled: Optional[bool] = None


class TriggerEventRequest(BaseModel):
    """Request to manually trigger a Saturnalia event."""
    config_id: str


class CancelEventRequest(BaseModel):
    """Request to cancel an active event."""
    event_id: str
    reason: str


class CreateOptOutRequest(BaseModel):
    """Request to opt out of a Saturnalia mode."""
    mode: SaturnaliaMode
    scope_type: str = Field(..., description="all, cell, or community")
    scope_id: Optional[str] = None
    reason: Optional[str] = None
    is_permanent: bool = False
    duration_days: Optional[int] = None


class CreateReflectionRequest(BaseModel):
    """Request to submit a post-event reflection."""
    event_id: str
    what_learned: str
    what_surprised: Optional[str] = None
    what_changed: Optional[str] = None
    suggestions: Optional[str] = None
    overall_rating: Optional[int] = Field(default=None, ge=1, le=5)
    would_do_again: bool = True


class SaturnaliaConfigResponse(BaseModel):
    """Response for a Saturnalia configuration."""
    id: str
    cell_id: Optional[str]
    community_id: Optional[str]
    enabled: bool
    enabled_modes: List[str]
    frequency: str
    duration_hours: int
    exclude_safety_critical: bool
    allow_individual_opt_out: bool
    next_scheduled_start: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: str


class SaturnaliaEventResponse(BaseModel):
    """Response for a Saturnalia event."""
    id: str
    config_id: str
    start_time: datetime
    end_time: datetime
    active_modes: List[str]
    status: str
    trigger_type: str
    triggered_by: Optional[str]
    created_at: datetime
    activated_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]


class SaturnaliaReflectionResponse(BaseModel):
    """Response for a reflection."""
    id: str
    event_id: str
    user_id: str
    what_learned: str
    what_surprised: Optional[str]
    what_changed: Optional[str]
    suggestions: Optional[str]
    overall_rating: Optional[int]
    would_do_again: bool
    submitted_at: datetime


class ActiveEventStatusResponse(BaseModel):
    """Response for active event status."""
    is_active: bool
    event: Optional[SaturnaliaEventResponse]
    active_modes: List[str]


# ===== Dependency Injection =====

def get_saturnalia_service() -> SaturnaliaService:
    """Get Saturnalia service instance."""
    return SaturnaliaService(db_path="data/dtn_bundles.db")


# ===== Configuration Endpoints =====

@router.post("/config", response_model=SaturnaliaConfigResponse)
async def create_config(
    request: CreateConfigRequest,
    current_user: User = Depends(require_steward),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Create a new Saturnalia configuration.

    Only stewards can create configurations.

    GAP-134: Steward verification via trust score >= 0.9
    """
    config = service.create_config(
        created_by=current_user.id,
        enabled_modes=request.enabled_modes,
        frequency=request.frequency,
        duration_hours=request.duration_hours,
        cell_id=request.cell_id,
        community_id=request.community_id,
        exclude_safety_critical=request.exclude_safety_critical,
        allow_individual_opt_out=request.allow_individual_opt_out,
    )

    return SaturnaliaConfigResponse(
        id=config.id,
        cell_id=config.cell_id,
        community_id=config.community_id,
        enabled=config.enabled,
        enabled_modes=[mode.value for mode in config.enabled_modes],
        frequency=config.frequency,
        duration_hours=config.duration_hours,
        exclude_safety_critical=config.exclude_safety_critical,
        allow_individual_opt_out=config.allow_individual_opt_out,
        next_scheduled_start=config.next_scheduled_start,
        created_at=config.created_at,
        updated_at=config.updated_at,
        created_by=config.created_by,
    )


@router.patch("/config/{config_id}", response_model=SaturnaliaConfigResponse)
async def update_config(
    config_id: str,
    request: UpdateConfigRequest,
    current_user: User = Depends(require_steward),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Update a Saturnalia configuration.

    GAP-134: Steward verification via trust score >= 0.9
    """
    config = service.update_config(
        config_id=config_id,
        enabled_modes=request.enabled_modes,
        frequency=request.frequency,
        duration_hours=request.duration_hours,
        enabled=request.enabled,
    )

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    return SaturnaliaConfigResponse(
        id=config.id,
        cell_id=config.cell_id,
        community_id=config.community_id,
        enabled=config.enabled,
        enabled_modes=[mode.value for mode in config.enabled_modes],
        frequency=config.frequency,
        duration_hours=config.duration_hours,
        exclude_safety_critical=config.exclude_safety_critical,
        allow_individual_opt_out=config.allow_individual_opt_out,
        next_scheduled_start=config.next_scheduled_start,
        created_at=config.created_at,
        updated_at=config.updated_at,
        created_by=config.created_by,
    )


@router.get("/config/{config_id}", response_model=SaturnaliaConfigResponse)
async def get_config(
    config_id: str,
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Get a Saturnalia configuration."""
    config = service.get_config(config_id)

    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    return SaturnaliaConfigResponse(
        id=config.id,
        cell_id=config.cell_id,
        community_id=config.community_id,
        enabled=config.enabled,
        enabled_modes=[mode.value for mode in config.enabled_modes],
        frequency=config.frequency,
        duration_hours=config.duration_hours,
        exclude_safety_critical=config.exclude_safety_critical,
        allow_individual_opt_out=config.allow_individual_opt_out,
        next_scheduled_start=config.next_scheduled_start,
        created_at=config.created_at,
        updated_at=config.updated_at,
        created_by=config.created_by,
    )


@router.get("/config/cell/{cell_id}", response_model=Optional[SaturnaliaConfigResponse])
async def get_config_for_cell(
    cell_id: str,
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Get Saturnalia configuration for a cell."""
    config = service.get_config_for_cell(cell_id)

    if not config:
        return None

    return SaturnaliaConfigResponse(
        id=config.id,
        cell_id=config.cell_id,
        community_id=config.community_id,
        enabled=config.enabled,
        enabled_modes=[mode.value for mode in config.enabled_modes],
        frequency=config.frequency,
        duration_hours=config.duration_hours,
        exclude_safety_critical=config.exclude_safety_critical,
        allow_individual_opt_out=config.allow_individual_opt_out,
        next_scheduled_start=config.next_scheduled_start,
        created_at=config.created_at,
        updated_at=config.updated_at,
        created_by=config.created_by,
    )


# ===== Event Endpoints =====

@router.post("/event/trigger", response_model=SaturnaliaEventResponse)
async def trigger_event(
    request: TriggerEventRequest,
    current_user: User = Depends(require_steward),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Manually trigger a Saturnalia event.

    Only stewards can trigger events.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        event = service.trigger_event(
            config_id=request.config_id,
            triggered_by=current_user.id,
            manual=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _event_to_response(event)


@router.post("/event/cancel")
async def cancel_event(
    request: CancelEventRequest,
    current_user: User = Depends(require_steward),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Cancel an active Saturnalia event.

    Only stewards can cancel events.

    GAP-134: Steward verification via trust score >= 0.9
    """
    event = service.cancel_event(request.event_id, request.reason)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return _event_to_response(event)


@router.get("/event/active", response_model=List[SaturnaliaEventResponse])
async def get_active_events(
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Get all currently active Saturnalia events."""
    events = service.get_active_events()
    return [_event_to_response(event) for event in events]


@router.get("/event/active/cell/{cell_id}", response_model=ActiveEventStatusResponse)
async def get_active_event_status(
    cell_id: str,
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Get active event status for a cell."""
    event = service.get_active_event_for_cell(cell_id)

    if not event:
        return ActiveEventStatusResponse(
            is_active=False,
            event=None,
            active_modes=[],
        )

    return ActiveEventStatusResponse(
        is_active=True,
        event=_event_to_response(event),
        active_modes=[mode.value for mode in event.active_modes],
    )


# ===== Opt-Out Endpoints =====

@router.post("/opt-out")
async def create_opt_out(
    request: CreateOptOutRequest,
    current_user: dict = Depends(get_current_user),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Opt out of a Saturnalia mode.

    No shame in opting out - this is about safety and choice.
    """
    opt_out = service.create_opt_out(
        user_id=current_user["id"],
        mode=request.mode,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        reason=request.reason,
        is_permanent=request.is_permanent,
        duration_days=request.duration_days,
    )

    return {
        "id": opt_out.id,
        "mode": opt_out.mode.value,
        "scope_type": opt_out.scope_type,
        "message": "Opt-out recorded. Your preferences are respected."
    }


@router.get("/opt-out/check/{mode}")
async def check_opt_out(
    mode: str,
    scope_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Check if current user has opted out of a mode."""
    try:
        saturnalia_mode = SaturnaliaMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")

    is_opted_out = service.is_user_opted_out(
        user_id=current_user["id"],
        mode=saturnalia_mode,
        scope_id=scope_id,
    )

    return {"opted_out": is_opted_out}


# ===== Reflection Endpoints =====

@router.post("/reflection", response_model=SaturnaliaReflectionResponse)
async def create_reflection(
    request: CreateReflectionRequest,
    current_user: dict = Depends(get_current_user),
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Submit a post-event reflection.

    Learning from Saturnalia is as important as experiencing it.
    """
    reflection = service.create_reflection(
        event_id=request.event_id,
        user_id=current_user["id"],
        what_learned=request.what_learned,
        what_surprised=request.what_surprised,
        what_changed=request.what_changed,
        suggestions=request.suggestions,
        overall_rating=request.overall_rating,
        would_do_again=request.would_do_again,
    )

    return SaturnaliaReflectionResponse(
        id=reflection.id,
        event_id=reflection.event_id,
        user_id=reflection.user_id,
        what_learned=reflection.what_learned,
        what_surprised=reflection.what_surprised,
        what_changed=reflection.what_changed,
        suggestions=reflection.suggestions,
        overall_rating=reflection.overall_rating,
        would_do_again=reflection.would_do_again,
        submitted_at=reflection.submitted_at,
    )


@router.get("/reflection/event/{event_id}", response_model=List[SaturnaliaReflectionResponse])
async def get_reflections_for_event(
    event_id: str,
    service: SaturnaliaService = Depends(get_saturnalia_service)
):
    """Get all reflections for an event."""
    reflections = service.get_reflections_for_event(event_id)

    return [
        SaturnaliaReflectionResponse(
            id=r.id,
            event_id=r.event_id,
            user_id=r.user_id,
            what_learned=r.what_learned,
            what_surprised=r.what_surprised,
            what_changed=r.what_changed,
            suggestions=r.suggestions,
            overall_rating=r.overall_rating,
            would_do_again=r.would_do_again,
            submitted_at=r.submitted_at,
        )
        for r in reflections
    ]


# ===== Helper Functions =====

def _event_to_response(event) -> SaturnaliaEventResponse:
    """Convert event model to response."""
    return SaturnaliaEventResponse(
        id=event.id,
        config_id=event.config_id,
        start_time=event.start_time,
        end_time=event.end_time,
        active_modes=[mode.value for mode in event.active_modes],
        status=event.status.value,
        trigger_type=event.trigger_type.value,
        triggered_by=event.triggered_by,
        created_at=event.created_at,
        activated_at=event.activated_at,
        completed_at=event.completed_at,
        cancelled_at=event.cancelled_at,
        cancellation_reason=event.cancellation_reason,
    )
