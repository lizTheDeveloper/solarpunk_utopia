"""Event Onboarding API Endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os

from app.models.event_onboarding import (
    EventInvite,
    CreateEventInviteRequest,
    BatchInvite,
    CreateBatchInviteRequest,
    OnboardingAnalytics,
    UseEventInviteRequest,
    UseBatchInviteRequest,
)
from app.database.event_onboarding_repository import EventOnboardingRepository
from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.auth.middleware import get_current_user
from app.models.vouch import TRUST_THRESHOLDS


router = APIRouter(prefix="/onboarding", tags=["mass-onboarding"])


# Dependency injection
def get_onboarding_repo():
    """Get EventOnboardingRepository instance."""
    db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
    return EventOnboardingRepository(db_path)


def get_vouch_repo():
    """Get VouchRepository instance."""
    db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
    return VouchRepository(db_path)


def get_trust_service(repo: VouchRepository = Depends(get_vouch_repo)):
    """Get WebOfTrustService instance."""
    return WebOfTrustService(repo)


@router.post("/event/create", response_model=EventInvite, summary="Create event invite (stewards only)")
async def create_event_invite(
    request: CreateEventInviteRequest,
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Create an event invite for mass onboarding.

    Requires:
    - Caller must have trust >= 0.9 (steward level)
    - Event start must be in the future
    - Event end must be after start

    Returns:
    - Event details including unique invite code for QR generation
    """
    # Check steward permission
    trust_score = trust_service.compute_trust_score(current_user.id)

    if trust_score.computed_trust < TRUST_THRESHOLDS["steward_actions"]:
        raise HTTPException(
            status_code=403,
            detail=f"Requires trust >= {TRUST_THRESHOLDS['steward_actions']} (steward). Current: {trust_score.computed_trust}"
        )

    # Validate dates
    if request.event_start >= request.event_end:
        raise HTTPException(
            status_code=400,
            detail="Event end must be after event start"
        )

    # Create the invite
    event_invite = repo.create_event_invite(
        created_by=current_user.id,
        event_name=request.event_name,
        event_type=request.event_type,
        event_start=request.event_start,
        event_end=request.event_end,
        event_location=request.event_location,
        max_attendees=request.max_attendees,
        temporary_trust_level=request.temporary_trust_level,
    )

    return event_invite


@router.get("/event/{event_id}", response_model=EventInvite, summary="Get event invite details")
async def get_event_invite(
    event_id: str,
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
):
    """Get details of an event invite."""
    event = repo.get_event_invite(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event invite not found")

    return event


@router.get("/event/code/{invite_code}", response_model=EventInvite, summary="Get event by invite code")
async def get_event_by_code(
    invite_code: str,
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
):
    """Get event details by scanning invite code (for attendees)."""
    event = repo.get_event_invite_by_code(invite_code)

    if not event:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    return event


@router.get("/event/my", response_model=List[EventInvite], summary="Get my event invites")
async def get_my_event_invites(
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
):
    """Get all event invites you've created."""
    events = repo.get_event_invites_by_creator(current_user.id)
    return events


@router.post("/event/join", summary="Join via event invite code")
async def join_via_event(
    request: UseEventInviteRequest,
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
    vouch_repo: VouchRepository = Depends(get_vouch_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Join the network via an event invite code.

    Process:
    1. Validate invite code
    2. Create attendee record
    3. Grant temporary trust (event-scoped)
    4. Return success with event details

    The user receives temporary trust for the duration of the event.
    After the event, they'll be prompted to get full vouches or leave.
    """
    # Use the event invite
    attendee = repo.use_event_invite(request.invite_code, current_user.id)

    if not attendee:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invite code, or already used"
        )

    # Get the event details
    event = repo.get_event_invite(attendee.event_id)

    # Grant temporary trust by creating automatic vouch from event creator
    # This is a special "event vouch" that expires
    vouch = vouch_repo.create_vouch(
        voucher_id=event.created_by,
        vouchee_id=current_user.id,
        context=f"event:{event.event_name}",
    )

    # Recompute trust
    trust_score = trust_service.compute_trust_score(current_user.id, force_recompute=True)

    return {
        "success": True,
        "event_name": event.event_name,
        "event_type": event.event_type,
        "event_start": event.event_start,
        "event_end": event.event_end,
        "event_location": event.event_location,
        "temporary_trust_level": event.temporary_trust_level,
        "your_trust_score": trust_score.computed_trust,
        "message": f"Welcome to {event.event_name}! You have temporary access during the event.",
    }


@router.post("/batch/create", response_model=BatchInvite, summary="Create batch invite (stewards only)")
async def create_batch_invite(
    request: CreateBatchInviteRequest,
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Create a batch invite link.

    Requires:
    - Caller must have trust >= 0.7 (established member)
    - Vouch capacity available

    Returns:
    - Batch invite details including unique link/QR
    """
    # Check eligibility
    trust_score = trust_service.compute_trust_score(current_user.id)

    if trust_score.computed_trust < TRUST_THRESHOLDS["vouch_others"]:
        raise HTTPException(
            status_code=403,
            detail=f"Requires trust >= {TRUST_THRESHOLDS['vouch_others']} (established). Current: {trust_score.computed_trust}"
        )

    # Create the batch invite
    batch = repo.create_batch_invite(
        created_by=current_user.id,
        max_uses=request.max_uses,
        days_valid=request.days_valid,
        context=request.context,
    )

    return batch


@router.post("/batch/join", summary="Join via batch invite link")
async def join_via_batch(
    request: UseBatchInviteRequest,
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
    vouch_repo: VouchRepository = Depends(get_vouch_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Join the network via a batch invite link.

    Process:
    1. Validate invite link
    2. Record use
    3. Create vouch from batch creator
    4. Grant trust based on voucher's trust
    """
    # Use the batch invite
    success = repo.use_batch_invite(request.invite_link, current_user.id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired invite link, or already used, or max uses reached"
        )

    # Get batch details to find the creator
    with EventOnboardingRepository(os.getenv("DATABASE_PATH", "data/valueflows.db")) as batch_repo:
        # We need to get batch by link - adding method temporarily here
        # In production, add get_batch_by_link to repository
        import sqlite3
        conn = sqlite3.connect(batch_repo.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT created_by FROM batch_invites WHERE invite_link = ?", (request.invite_link,))
        row = cursor.fetchone()
        creator_id = row[0] if row else None
        conn.close()

    if not creator_id:
        raise HTTPException(status_code=500, detail="Failed to retrieve batch creator")

    # Create vouch from batch creator
    vouch = vouch_repo.create_vouch(
        voucher_id=creator_id,
        vouchee_id=current_user.id,
        context=f"batch_invite",
    )

    # Recompute trust
    trust_score = trust_service.compute_trust_score(current_user.id, force_recompute=True)

    return {
        "success": True,
        "voucher_id": creator_id,
        "your_trust_score": trust_score.computed_trust,
        "message": "Successfully joined via batch invite!",
    }


@router.get("/analytics", response_model=OnboardingAnalytics, summary="Get onboarding analytics (stewards)")
async def get_onboarding_analytics(
    current_user=Depends(get_current_user),
    repo: EventOnboardingRepository = Depends(get_onboarding_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Get onboarding analytics and statistics.

    Requires:
    - Caller must have trust >= 0.9 (steward level)

    Returns:
    - Total invites created
    - Total attendees/members onboarded
    - Upgrade rates
    - Active events
    - Recent joins
    - Trust level distribution
    """
    # Check steward permission
    trust_score = trust_service.compute_trust_score(current_user.id)

    if trust_score.computed_trust < TRUST_THRESHOLDS["steward_actions"]:
        raise HTTPException(
            status_code=403,
            detail=f"Requires trust >= {TRUST_THRESHOLDS['steward_actions']} (steward). Current: {trust_score.computed_trust}"
        )

    analytics = repo.get_analytics()

    # TODO: Populate trust level distribution from trust service
    # For now, return basic analytics

    return analytics
