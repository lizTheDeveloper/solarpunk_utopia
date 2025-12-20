"""Ancestor Voting API

Endpoints for managing Memorial Funds and Ghost Reputation allocations.

'The only good authority is a dead one.' - Mikhail Bakunin
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.ancestor_voting_service import AncestorVotingService
from app.models.ancestor_voting import DepartureType, ProposalStatus
from app.auth.middleware import get_current_user, require_steward
from app.auth.models import User

router = APIRouter(prefix="/api/ancestor-voting", tags=["ancestor-voting"])


# ===== Request/Response Models =====

class CreateMemorialFundRequest(BaseModel):
    """Request to create a Memorial Fund on user departure."""
    user_id: str
    user_name: str
    display_name: Optional[str] = None
    final_reputation: float = Field(..., ge=0.0)
    departure_type: DepartureType
    departure_reason: Optional[str] = None


class AllocateGhostReputationRequest(BaseModel):
    """Request to allocate Ghost Reputation to a proposal."""
    fund_id: str
    proposal_id: str
    amount: float = Field(..., gt=0.0)
    reason: str = Field(..., min_length=10, description="Required justification for allocation")

    # Proposal metadata for priority calculation
    proposal_metadata: Dict[str, Any] = Field(
        ...,
        description="Metadata including author_id, author_tenure_months, author_reputation, etc."
    )


class VetoAllocationRequest(BaseModel):
    """Request to veto an allocation."""
    allocation_id: str
    veto_reason: str = Field(..., min_length=10)


class RefundAllocationRequest(BaseModel):
    """Request to refund an allocation."""
    allocation_id: str
    refund_reason: str


class CompleteAllocationRequest(BaseModel):
    """Request to mark allocation as completed."""
    allocation_id: str
    proposal_status: ProposalStatus


class RequestFundRemovalRequest(BaseModel):
    """Request removal of a Memorial Fund."""
    fund_id: str


class MemorialFundResponse(BaseModel):
    """Response for a Memorial Fund."""
    id: str
    created_from_user_id: str
    departed_user_name: str
    departed_user_display_name: Optional[str]
    initial_reputation: float
    current_balance: float
    created_at: datetime
    updated_at: datetime
    family_requested_removal: bool
    removal_requested_at: Optional[datetime]


class GhostReputationAllocationResponse(BaseModel):
    """Response for a Ghost Reputation allocation."""
    id: str
    fund_id: str
    proposal_id: str
    amount: float
    allocated_by: str
    reason: str
    status: str
    refunded: bool
    refund_reason: Optional[str]
    allocated_at: datetime
    refunded_at: Optional[datetime]
    completed_at: Optional[datetime]
    veto_deadline: datetime
    vetoed: bool
    vetoed_by: Optional[str]
    veto_reason: Optional[str]
    vetoed_at: Optional[datetime]


class ProposalAncestorResponse(BaseModel):
    """Response for proposal ancestor attribution."""
    ancestor_name: str
    reputation_amount: float
    attributed_at: datetime
    fund_id: str


class FundImpactResponse(BaseModel):
    """Response for Memorial Fund impact metrics."""
    fund: Dict[str, Any]
    impact: Dict[str, Any]
    attributions: List[Dict[str, Any]]
    allocations: List[Dict[str, Any]]


class AuditLogResponse(BaseModel):
    """Response for allocation audit log."""
    id: str
    allocation_id: str
    action: str
    actor_id: str
    actor_role: str
    details: Optional[str]
    logged_at: datetime


# ===== Dependency Injection =====

def get_ancestor_voting_service() -> AncestorVotingService:
    """Get Ancestor Voting service instance."""
    return AncestorVotingService(db_path="data/dtn_bundles.db")


# ===== Memorial Fund Endpoints =====

@router.post("/memorial-fund", response_model=MemorialFundResponse)
async def create_memorial_fund(
    request: CreateMemorialFundRequest,
    current_user: User = Depends(require_steward),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Create a Memorial Fund when a user departs.

    Only stewards or authorized administrators can create Memorial Funds.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        fund = service.create_memorial_fund_on_departure(
            user_id=request.user_id,
            user_name=request.user_name,
            display_name=request.display_name,
            final_reputation=request.final_reputation,
            departure_type=request.departure_type,
            departure_reason=request.departure_reason,
            recorded_by=current_user["id"]
        )

        return MemorialFundResponse(
            id=fund.id,
            created_from_user_id=fund.created_from_user_id,
            departed_user_name=fund.departed_user_name,
            departed_user_display_name=fund.departed_user_display_name,
            initial_reputation=fund.initial_reputation,
            current_balance=fund.current_balance,
            created_at=fund.created_at,
            updated_at=fund.updated_at,
            family_requested_removal=fund.family_requested_removal,
            removal_requested_at=fund.removal_requested_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memorial-fund/{fund_id}", response_model=MemorialFundResponse)
async def get_memorial_fund(
    fund_id: str,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Get a Memorial Fund by ID."""
    fund = service.get_memorial_fund(fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="Memorial Fund not found")

    return MemorialFundResponse(
        id=fund.id,
        created_from_user_id=fund.created_from_user_id,
        departed_user_name=fund.departed_user_name,
        departed_user_display_name=fund.departed_user_display_name,
        initial_reputation=fund.initial_reputation,
        current_balance=fund.current_balance,
        created_at=fund.created_at,
        updated_at=fund.updated_at,
        family_requested_removal=fund.family_requested_removal,
        removal_requested_at=fund.removal_requested_at,
    )


@router.get("/memorial-funds", response_model=List[MemorialFundResponse])
async def list_memorial_funds(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """List all Memorial Funds."""
    funds = service.list_memorial_funds(limit=limit, offset=offset)

    return [
        MemorialFundResponse(
            id=fund.id,
            created_from_user_id=fund.created_from_user_id,
            departed_user_name=fund.departed_user_name,
            departed_user_display_name=fund.departed_user_display_name,
            initial_reputation=fund.initial_reputation,
            current_balance=fund.current_balance,
            created_at=fund.created_at,
            updated_at=fund.updated_at,
            family_requested_removal=fund.family_requested_removal,
            removal_requested_at=fund.removal_requested_at,
        )
        for fund in funds
    ]


@router.post("/memorial-fund/request-removal")
async def request_memorial_removal(
    request: RequestFundRemovalRequest,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Request removal of a Memorial Fund (family request).

    Privacy consideration: Families can request removal of deceased member's memorial.
    """
    try:
        service.request_memorial_removal(request.fund_id)
        return {"status": "removal_requested"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memorial-fund/{fund_id}/impact", response_model=FundImpactResponse)
async def get_fund_impact(
    fund_id: str,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Get impact metrics for a Memorial Fund.

    Shows how this ancestor's reputation has amplified marginalized voices.
    """
    impact = service.get_fund_impact(fund_id)
    if not impact:
        raise HTTPException(status_code=404, detail="Memorial Fund not found")

    return FundImpactResponse(**impact)


# ===== Ghost Reputation Allocation Endpoints =====

@router.post("/allocate", response_model=GhostReputationAllocationResponse)
async def allocate_ghost_reputation(
    request: AllocateGhostReputationRequest,
    current_user: User = Depends(require_steward),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Allocate Ghost Reputation to boost a proposal.

    Only stewards can allocate Ghost Reputation.

    Anti-abuse protections:
    - Steward cannot allocate to their own proposals
    - Cannot allocate more than 20% of fund to a single proposal
    - Must provide written justification
    - Other stewards can veto within 24 hours

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        allocation = service.allocate_ghost_reputation(
            fund_id=request.fund_id,
            proposal_id=request.proposal_id,
            amount=request.amount,
            allocated_by=current_user.id,
            reason=request.reason,
            proposal_metadata=request.proposal_metadata,
        )

        return GhostReputationAllocationResponse(
            id=allocation.id,
            fund_id=allocation.fund_id,
            proposal_id=allocation.proposal_id,
            amount=allocation.amount,
            allocated_by=allocation.allocated_by,
            reason=allocation.reason,
            status=allocation.status.value,
            refunded=allocation.refunded,
            refund_reason=allocation.refund_reason,
            allocated_at=allocation.allocated_at,
            refunded_at=allocation.refunded_at,
            completed_at=allocation.completed_at,
            veto_deadline=allocation.veto_deadline,
            vetoed=allocation.vetoed,
            vetoed_by=allocation.vetoed_by,
            veto_reason=allocation.veto_reason,
            vetoed_at=allocation.vetoed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate/veto")
async def veto_allocation(
    request: VetoAllocationRequest,
    current_user: User = Depends(require_steward),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Veto an allocation within the 24-hour window.

    Only stewards can veto allocations.
    Cannot veto your own allocation.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        service.veto_allocation(
            allocation_id=request.allocation_id,
            vetoed_by=current_user.id,
            veto_reason=request.veto_reason,
        )
        return {"status": "vetoed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate/refund")
async def refund_allocation(
    request: RefundAllocationRequest,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Refund an allocation (e.g., proposal rejected).

    System-triggered when a proposal is rejected.
    """
    try:
        service.refund_allocation(
            allocation_id=request.allocation_id,
            refund_reason=request.refund_reason,
        )
        return {"status": "refunded"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/allocate/complete")
async def complete_allocation(
    request: CompleteAllocationRequest,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Mark allocation as completed (proposal implemented).

    System-triggered when a proposal is approved/implemented.
    """
    try:
        service.complete_allocation(
            allocation_id=request.allocation_id,
            proposal_status=request.proposal_status,
        )
        return {"status": "completed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/allocations/pending-veto", response_model=List[GhostReputationAllocationResponse])
async def get_pending_veto_allocations(
    current_user: User = Depends(require_steward),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Get allocations still within veto window.

    Stewards use this to review recent allocations and decide whether to veto.

    GAP-134: Steward verification via trust score >= 0.9
    """
    allocations = service.get_allocations_pending_veto()

    return [
        GhostReputationAllocationResponse(
            id=allocation.id,
            fund_id=allocation.fund_id,
            proposal_id=allocation.proposal_id,
            amount=allocation.amount,
            allocated_by=allocation.allocated_by,
            reason=allocation.reason,
            status=allocation.status.value,
            refunded=allocation.refunded,
            refund_reason=allocation.refund_reason,
            allocated_at=allocation.allocated_at,
            refunded_at=allocation.refunded_at,
            completed_at=allocation.completed_at,
            veto_deadline=allocation.veto_deadline,
            vetoed=allocation.vetoed,
            vetoed_by=allocation.vetoed_by,
            veto_reason=allocation.veto_reason,
            vetoed_at=allocation.vetoed_at,
        )
        for allocation in allocations
    ]


# ===== Proposal Attribution Endpoints =====

@router.get("/proposal/{proposal_id}/ancestors", response_model=List[ProposalAncestorResponse])
async def get_proposal_ancestors(
    proposal_id: str,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Get all ancestors who boosted a proposal.

    Shows which departed members' reputation was used to amplify this proposal.
    """
    ancestors = service.get_proposal_ancestors(proposal_id)

    return [
        ProposalAncestorResponse(**ancestor)
        for ancestor in ancestors
    ]


# ===== Transparency Endpoints =====

@router.get("/allocation/{allocation_id}/audit-log", response_model=List[AuditLogResponse])
async def get_allocation_audit_log(
    allocation_id: str,
    current_user: dict = Depends(get_current_user),
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    """Get audit log for an allocation (transparency).

    Shows all actions taken on this allocation: allocated, vetoed, refunded, completed.
    """
    logs = service.get_audit_logs(allocation_id)

    return [
        AuditLogResponse(
            id=log.id,
            allocation_id=log.allocation_id,
            action=log.action.value,
            actor_id=log.actor_id,
            actor_role=log.actor_role,
            details=log.details,
            logged_at=log.logged_at,
        )
        for log in logs
    ]
