"""
Temporal Justice API Routes

API endpoints for temporal justice features.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from app.database.db import get_db
from app.database.temporal_justice_repository import TemporalJusticeRepository
from app.services.temporal_justice_service import TemporalJusticeService
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/api/temporal-justice", tags=["temporal-justice"])


# Request/Response Models


class AvailabilityWindowCreate(BaseModel):
    """Create availability window request"""

    duration_minutes: int = Field(..., description="Duration in minutes")
    recurrence_type: str = Field(..., description="weekly, one_time, or flexible")
    day_of_week: Optional[int] = Field(
        None, description="0-6 (Sunday-Saturday) for weekly"
    )
    start_time: Optional[str] = Field(None, description="HH:MM format")
    end_time: Optional[str] = Field(None, description="HH:MM format")
    specific_date: Optional[str] = Field(None, description="YYYY-MM-DD for one-time")
    specific_start_time: Optional[str] = Field(None, description="HH:MM for one-time")
    description: Optional[str] = Field(
        None, description="Context like 'After kids sleep'"
    )


class AvailabilityWindowResponse(BaseModel):
    """Availability window response"""

    id: str
    user_id: str
    duration_minutes: int
    recurrence_type: str
    day_of_week: Optional[int]
    start_time: Optional[str]
    end_time: Optional[str]
    specific_date: Optional[str]
    specific_start_time: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: str


class SlowExchangeCreate(BaseModel):
    """Create slow exchange request"""

    offerer_id: str
    requester_id: str
    what: str
    category: str
    expected_duration_days: int
    proposal_id: Optional[str] = None
    deadline_days: Optional[int] = None


class SlowExchangeUpdate(BaseModel):
    """Update slow exchange request"""

    status: str = Field(
        ..., description="coordinating, in_progress, paused, completed, cancelled"
    )
    note: Optional[str] = None


class SlowExchangeResponse(BaseModel):
    """Slow exchange response"""

    id: str
    proposal_id: Optional[str]
    offerer_id: str
    requester_id: str
    what: str
    category: str
    expected_duration_days: int
    deadline: Optional[str]
    status: str
    last_contact_at: Optional[str]
    check_ins_count: int
    created_at: str


class TimeContributionCreate(BaseModel):
    """Record time contribution request"""

    contribution_type: str = Field(
        ..., description="care_work, community_labor, availability_sharing, coordination"
    )
    description: str
    hours_contributed: float
    category: Optional[str] = None
    related_exchange_id: Optional[str] = None
    related_cell_id: Optional[str] = None


class TimeContributionResponse(BaseModel):
    """Time contribution response"""

    id: str
    user_id: str
    contribution_type: str
    description: str
    hours_contributed: float
    contributed_at: str
    acknowledgment_count: int


class ChunkOfferCreate(BaseModel):
    """Create chunk offer request"""

    proposal_id: str
    availability_window_id: str
    what_offered: str
    category: str


class ChunkOfferResponse(BaseModel):
    """Chunk offer response"""

    id: str
    proposal_id: str
    user_id: str
    availability_window_id: str
    what_offered: str
    category: str
    status: str
    claimed_by_user_id: Optional[str]
    created_at: str


class TemporalJusticeMetricsResponse(BaseModel):
    """Temporal justice metrics response"""

    total_active_members: int
    members_with_fragmented_availability: int
    members_with_care_responsibilities: int
    slow_exchanges_count: int
    slow_exchanges_completed: int
    avg_slow_exchange_duration_days: float
    total_time_contributions_hours: float
    care_work_acknowledged_hours: float
    fragmented_availability_percentage: float
    period_start: str
    period_end: str


class AsyncVoteCreate(BaseModel):
    """Record async vote request"""

    proposal_id: str
    vote: str = Field(..., description="approve, reject, or abstain")
    voting_notes: Optional[str] = None


# Dependency injection


async def get_service(db=Depends(get_db)) -> TemporalJusticeService:
    """Get temporal justice service"""
    repo = TemporalJusticeRepository(db)
    return TemporalJusticeService(repo)


# Availability Windows


@router.post("/availability-windows", response_model=AvailabilityWindowResponse)
async def create_availability_window(
    request: AvailabilityWindowCreate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Create an availability window"""
    window = await service.add_availability_window(
        user_id=current_user["id"],
        duration_minutes=request.duration_minutes,
        recurrence_type=request.recurrence_type,
        day_of_week=request.day_of_week,
        start_time=request.start_time,
        end_time=request.end_time,
        specific_date=request.specific_date,
        specific_start_time=request.specific_start_time,
        description=request.description,
    )

    return AvailabilityWindowResponse(
        id=window.id,
        user_id=window.user_id,
        duration_minutes=window.duration_minutes,
        recurrence_type=window.recurrence_type.value,
        day_of_week=window.day_of_week,
        start_time=window.start_time,
        end_time=window.end_time,
        specific_date=window.specific_date,
        specific_start_time=window.specific_start_time,
        description=window.description,
        is_active=window.is_active,
        created_at=window.created_at.isoformat(),
    )


@router.get("/availability-windows", response_model=List[AvailabilityWindowResponse])
async def get_availability_windows(
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Get user's availability windows"""
    windows = await service.get_user_availability(current_user["id"])

    return [
        AvailabilityWindowResponse(
            id=w.id,
            user_id=w.user_id,
            duration_minutes=w.duration_minutes,
            recurrence_type=w.recurrence_type.value,
            day_of_week=w.day_of_week,
            start_time=w.start_time,
            end_time=w.end_time,
            specific_date=w.specific_date,
            specific_start_time=w.specific_start_time,
            description=w.description,
            is_active=w.is_active,
            created_at=w.created_at.isoformat(),
        )
        for w in windows
    ]


# Slow Exchanges


@router.post("/slow-exchanges", response_model=SlowExchangeResponse)
async def create_slow_exchange(
    request: SlowExchangeCreate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Create a slow exchange"""
    exchange = await service.create_slow_exchange(
        offerer_id=request.offerer_id,
        requester_id=request.requester_id,
        what=request.what,
        category=request.category,
        expected_duration_days=request.expected_duration_days,
        proposal_id=request.proposal_id,
        deadline_days=request.deadline_days,
    )

    return SlowExchangeResponse(
        id=exchange.id,
        proposal_id=exchange.proposal_id,
        offerer_id=exchange.offerer_id,
        requester_id=exchange.requester_id,
        what=exchange.what,
        category=exchange.category,
        expected_duration_days=exchange.expected_duration_days,
        deadline=exchange.deadline.isoformat() if exchange.deadline else None,
        status=exchange.status.value,
        last_contact_at=(
            exchange.last_contact_at.isoformat() if exchange.last_contact_at else None
        ),
        check_ins_count=exchange.check_ins_count,
        created_at=exchange.created_at.isoformat(),
    )


@router.patch("/slow-exchanges/{exchange_id}", response_model=dict)
async def update_slow_exchange(
    exchange_id: str,
    request: SlowExchangeUpdate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Update a slow exchange"""
    await service.update_slow_exchange(
        exchange_id=exchange_id,
        status=request.status,
        note=request.note,
    )

    return {"success": True, "exchange_id": exchange_id}


@router.get("/slow-exchanges", response_model=List[SlowExchangeResponse])
async def get_slow_exchanges(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Get user's slow exchanges"""
    exchanges = await service.get_user_slow_exchanges(current_user["id"], status)

    return [
        SlowExchangeResponse(
            id=e.id,
            proposal_id=e.proposal_id,
            offerer_id=e.offerer_id,
            requester_id=e.requester_id,
            what=e.what,
            category=e.category,
            expected_duration_days=e.expected_duration_days,
            deadline=e.deadline.isoformat() if e.deadline else None,
            status=e.status.value,
            last_contact_at=e.last_contact_at.isoformat() if e.last_contact_at else None,
            check_ins_count=e.check_ins_count,
            created_at=e.created_at.isoformat(),
        )
        for e in exchanges
    ]


# Time Contributions


@router.post("/time-contributions", response_model=TimeContributionResponse)
async def record_time_contribution(
    request: TimeContributionCreate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Record a time contribution"""
    contribution = await service.record_contribution(
        user_id=current_user["id"],
        contribution_type=request.contribution_type,
        description=request.description,
        hours_contributed=request.hours_contributed,
        category=request.category,
        related_exchange_id=request.related_exchange_id,
        related_cell_id=request.related_cell_id,
    )

    return TimeContributionResponse(
        id=contribution.id,
        user_id=contribution.user_id,
        contribution_type=contribution.contribution_type.value,
        description=contribution.description,
        hours_contributed=contribution.hours_contributed,
        contributed_at=contribution.contributed_at.isoformat(),
        acknowledgment_count=contribution.acknowledgment_count,
    )


@router.post("/time-contributions/{contribution_id}/acknowledge", response_model=dict)
async def acknowledge_time_contribution(
    contribution_id: str,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Acknowledge someone's time contribution"""
    await service.acknowledge_contribution(contribution_id, current_user["id"])

    return {"success": True, "contribution_id": contribution_id}


# Chunk Offers


@router.post("/chunk-offers", response_model=ChunkOfferResponse)
async def create_chunk_offer(
    request: ChunkOfferCreate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Create a chunk offer"""
    chunk = await service.create_chunk_offer(
        proposal_id=request.proposal_id,
        user_id=current_user["id"],
        availability_window_id=request.availability_window_id,
        what_offered=request.what_offered,
        category=request.category,
    )

    return ChunkOfferResponse(
        id=chunk.id,
        proposal_id=chunk.proposal_id,
        user_id=chunk.user_id,
        availability_window_id=chunk.availability_window_id,
        what_offered=chunk.what_offered,
        category=chunk.category,
        status=chunk.status.value,
        claimed_by_user_id=chunk.claimed_by_user_id,
        created_at=chunk.created_at.isoformat(),
    )


@router.get("/chunk-offers", response_model=List[ChunkOfferResponse])
async def get_chunk_offers(
    category: Optional[str] = None,
    service: TemporalJusticeService = Depends(get_service),
):
    """Get available chunk offers"""
    chunks = await service.get_available_chunk_offers(category)

    return [
        ChunkOfferResponse(
            id=c.id,
            proposal_id=c.proposal_id,
            user_id=c.user_id,
            availability_window_id=c.availability_window_id,
            what_offered=c.what_offered,
            category=c.category,
            status=c.status.value,
            claimed_by_user_id=c.claimed_by_user_id,
            created_at=c.created_at.isoformat(),
        )
        for c in chunks
    ]


@router.post("/chunk-offers/{chunk_id}/claim", response_model=ChunkOfferResponse)
async def claim_chunk_offer(
    chunk_id: str,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Claim a chunk offer"""
    chunk = await service.claim_chunk_offer(chunk_id, current_user["id"])

    return ChunkOfferResponse(
        id=chunk.id,
        proposal_id=chunk.proposal_id,
        user_id=chunk.user_id,
        availability_window_id=chunk.availability_window_id,
        what_offered=chunk.what_offered,
        category=chunk.category,
        status=chunk.status.value,
        claimed_by_user_id=chunk.claimed_by_user_id,
        created_at=chunk.created_at.isoformat(),
    )


# Metrics


@router.get("/metrics", response_model=TemporalJusticeMetricsResponse)
async def get_temporal_justice_metrics(
    days_back: int = 30,
    service: TemporalJusticeService = Depends(get_service),
):
    """Get temporal justice metrics"""
    metrics = await service.get_temporal_justice_metrics(days_back)

    return TemporalJusticeMetricsResponse(
        total_active_members=metrics.total_active_members,
        members_with_fragmented_availability=metrics.members_with_fragmented_availability,
        members_with_care_responsibilities=metrics.members_with_care_responsibilities,
        slow_exchanges_count=metrics.slow_exchanges_count,
        slow_exchanges_completed=metrics.slow_exchanges_completed,
        avg_slow_exchange_duration_days=metrics.avg_slow_exchange_duration_days,
        total_time_contributions_hours=metrics.total_time_contributions_hours,
        care_work_acknowledged_hours=metrics.care_work_acknowledged_hours,
        fragmented_availability_percentage=metrics.fragmented_availability_percentage,
        period_start=metrics.period_start.isoformat(),
        period_end=metrics.period_end.isoformat(),
    )


# Async Voting


@router.post("/async-vote", response_model=dict)
async def record_async_vote(
    request: AsyncVoteCreate,
    current_user: dict = Depends(get_current_user),
    service: TemporalJusticeService = Depends(get_service),
):
    """Record an async vote on a proposal"""
    vote = await service.record_vote(
        proposal_id=request.proposal_id,
        user_id=current_user["id"],
        vote=request.vote,
        voting_notes=request.voting_notes,
    )

    return {
        "success": True,
        "vote_id": vote.id,
        "time_to_vote_hours": vote.time_to_vote_hours,
    }
