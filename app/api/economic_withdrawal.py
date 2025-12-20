"""Economic Withdrawal API

Endpoints for coordinated wealth deconcentration campaigns.

Every transaction in the gift economy is a transaction that DIDN'T go to Bezos.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.services.economic_withdrawal_service import EconomicWithdrawalService
from app.models.economic_withdrawal import (
    CampaignType,
    CampaignStatus,
    PledgeStatus,
)
from app.auth.middleware import get_current_user, require_steward
from app.auth.models import User

router = APIRouter(prefix="/api/economic-withdrawal", tags=["economic-withdrawal"])


# ===== Request/Response Models =====

class CreateCampaignRequest(BaseModel):
    """Request to create a new campaign."""
    campaign_type: CampaignType
    name: str = Field(..., description="Campaign name (e.g., 'No Amazon November')")
    description: str
    target_corporation: str
    target_category: Optional[str] = None
    cell_id: Optional[str] = Field(default=None, description="Cell ID if cell-scoped")
    network_wide: bool = Field(default=False, description="Is this network-wide?")
    threshold_participants: int = Field(..., description="Minimum participants to activate")
    pledge_deadline: datetime
    campaign_start: datetime
    campaign_end: datetime


class CreatePledgeRequest(BaseModel):
    """Request to pledge participation in a campaign."""
    campaign_id: str
    commitment_level: str = Field(default="full", description="full, partial, or explore")
    commitment_notes: Optional[str] = None
    buddy_id: Optional[str] = Field(default=None, description="Accountability buddy")


class MarkAvoidedRequest(BaseModel):
    """Request to mark avoiding target corporation."""
    pledge_id: str
    estimated_value: Optional[float] = Field(default=None, description="Estimated $ avoided")


class MarkAlternativeUsedRequest(BaseModel):
    """Request to mark using an alternative."""
    pledge_id: str
    alternative_id: Optional[str] = None


class CreateAlternativeRequest(BaseModel):
    """Request to create a corporate alternative."""
    campaign_type: CampaignType
    replaces_corporation: str
    replaces_service: str
    alternative_type: str = Field(..., description="network_sharing, local_business, co_op, mutual_aid")
    name: str
    description: str
    cell_id: Optional[str] = None
    network_wide: bool = False
    contact_user_id: Optional[str] = None
    access_instructions: Optional[str] = None


class CreateBulkBuyRequest(BaseModel):
    """Request to create a bulk buy order."""
    item_name: str
    item_description: str
    unit: str
    retail_price_per_unit: float
    wholesale_price_per_unit: float
    minimum_units: int
    cell_id: str
    commitment_deadline: datetime
    delivery_date: datetime
    distribution_location: Optional[str] = None
    supplier: Optional[str] = None
    campaign_id: Optional[str] = None


class CommitToBulkBuyRequest(BaseModel):
    """Request to commit to a bulk buy."""
    bulk_buy_id: str
    units: int


# ===== Dependency Injection =====

def get_economic_withdrawal_service() -> EconomicWithdrawalService:
    """Get economic withdrawal service instance."""
    return EconomicWithdrawalService(db_path="data/dtn_bundles.db")


# ===== Campaign Endpoints =====

@router.post("/campaigns/create")
async def create_campaign(
    request: CreateCampaignRequest,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Create a new economic withdrawal campaign (stewards only).

    Campaigns coordinate collective action to redirect spending from
    extractive corporations to regenerative community systems.
    """
    # Verify user is steward
    await require_steward(user_id)

    campaign = service.create_campaign(
        created_by=user_id,
        campaign_type=request.campaign_type,
        name=request.name,
        description=request.description,
        target_corporation=request.target_corporation,
        target_category=request.target_category,
        cell_id=request.cell_id,
        network_wide=request.network_wide,
        threshold_participants=request.threshold_participants,
        pledge_deadline=request.pledge_deadline,
        campaign_start=request.campaign_start,
        campaign_end=request.campaign_end,
    )

    return {
        "success": True,
        "campaign_id": campaign.id,
        "status": campaign.status.value,
        "threshold_participants": campaign.threshold_participants,
        "pledge_deadline": campaign.pledge_deadline.isoformat(),
        "message": f"Campaign '{campaign.name}' created. Gathering pledges until {campaign.pledge_deadline.date()}."
    }


@router.get("/campaigns/active")
async def get_active_campaigns(
    cell_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get active campaigns (GATHERING or ACTIVE status)."""
    campaigns = service.get_active_campaigns(cell_id)

    return {
        "campaigns": [
            {
                "id": c.id,
                "campaign_type": c.campaign_type.value,
                "name": c.name,
                "description": c.description,
                "target_corporation": c.target_corporation,
                "target_category": c.target_category,
                "status": c.status.value,
                "current_participants": c.current_participants,
                "threshold_participants": c.threshold_participants,
                "progress_percent": (c.current_participants / c.threshold_participants * 100) if c.threshold_participants > 0 else 0,
                "pledge_deadline": c.pledge_deadline.isoformat(),
                "campaign_start": c.campaign_start.isoformat(),
                "campaign_end": c.campaign_end.isoformat(),
                "network_wide": c.network_wide,
                "cell_id": c.cell_id,
            }
            for c in campaigns
        ]
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign_detail(
    campaign_id: str,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get full details for a campaign."""
    campaign = service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    pledges = service.get_campaign_pledges(campaign_id)
    alternatives = service.get_alternatives_for_campaign(campaign_id)

    return {
        "campaign": {
            "id": campaign.id,
            "campaign_type": campaign.campaign_type.value,
            "name": campaign.name,
            "description": campaign.description,
            "target_corporation": campaign.target_corporation,
            "target_category": campaign.target_category,
            "status": campaign.status.value,
            "current_participants": campaign.current_participants,
            "threshold_participants": campaign.threshold_participants,
            "pledge_deadline": campaign.pledge_deadline.isoformat(),
            "campaign_start": campaign.campaign_start.isoformat(),
            "campaign_end": campaign.campaign_end.isoformat(),
            "estimated_economic_impact": campaign.estimated_economic_impact,
            "network_value_circulated": campaign.network_value_circulated,
            "local_transactions_facilitated": campaign.local_transactions_facilitated,
            "created_by": campaign.created_by,
            "created_at": campaign.created_at.isoformat(),
            "activated_at": campaign.activated_at.isoformat() if campaign.activated_at else None,
            "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            "network_wide": campaign.network_wide,
            "cell_id": campaign.cell_id,
        },
        "pledge_count": len(pledges),
        "alternatives_count": len(alternatives),
        "alternatives": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "alternative_type": a.alternative_type,
                "times_used": a.times_used,
                "contact_user_id": a.contact_user_id,
                "access_instructions": a.access_instructions,
            }
            for a in alternatives
        ]
    }


@router.post("/campaigns/{campaign_id}/complete")
async def complete_campaign(
    campaign_id: str,
    user: User = Depends(require_steward),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Complete a campaign and calculate final impact (coordinator only).

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        campaign = service.complete_campaign(campaign_id)

        return {
            "success": True,
            "campaign_id": campaign.id,
            "status": campaign.status.value,
            "participants": campaign.current_participants,
            "estimated_economic_impact": campaign.estimated_economic_impact,
            "local_transactions_facilitated": campaign.local_transactions_facilitated,
            "network_value_circulated": campaign.network_value_circulated,
            "completed_at": campaign.completed_at.isoformat(),
            "message": f"Campaign complete! ${campaign.estimated_economic_impact:.2f} redirected from {campaign.target_corporation}."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Pledge Endpoints =====

@router.post("/pledges/create")
async def create_pledge(
    request: CreatePledgeRequest,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Pledge to participate in a campaign."""
    try:
        pledge = service.create_pledge(
            user_id=user_id,
            campaign_id=request.campaign_id,
            commitment_level=request.commitment_level,
            commitment_notes=request.commitment_notes,
            buddy_id=request.buddy_id,
        )

        # Check if this pushed campaign over threshold
        campaign = service.get_campaign(request.campaign_id)

        return {
            "success": True,
            "pledge_id": pledge.id,
            "campaign_id": pledge.campaign_id,
            "commitment_level": pledge.commitment_level,
            "status": pledge.status.value,
            "campaign_participants": campaign.current_participants if campaign else 0,
            "campaign_threshold": campaign.threshold_participants if campaign else 0,
            "campaign_activated": campaign.status == CampaignStatus.ACTIVE if campaign else False,
            "message": "Pledge created! You're part of the collective action."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pledges/my-pledges")
async def get_my_pledges(
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get all of current user's pledges."""
    pledges = service.get_user_pledges(user_id)

    # Get campaign info for each pledge
    result = []
    for p in pledges:
        campaign = service.get_campaign(p.campaign_id)
        result.append({
            "pledge_id": p.id,
            "campaign_id": p.campaign_id,
            "campaign_name": campaign.name if campaign else "Unknown",
            "campaign_status": campaign.status.value if campaign else "unknown",
            "commitment_level": p.commitment_level,
            "status": p.status.value,
            "times_avoided_target": p.times_avoided_target,
            "estimated_spending_redirected": p.estimated_spending_redirected,
            "alternatives_used": p.alternatives_used,
            "pledged_at": p.pledged_at.isoformat(),
        })

    return {"pledges": result}


@router.post("/pledges/mark-avoided")
async def mark_avoided(
    request: MarkAvoidedRequest,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Mark that you avoided the target corporation.

    Use this when you almost bought from Amazon but didn't!
    """
    try:
        pledge = service.mark_avoided(
            pledge_id=request.pledge_id,
            estimated_value=request.estimated_value
        )

        return {
            "success": True,
            "pledge_id": pledge.id,
            "times_avoided_target": pledge.times_avoided_target,
            "estimated_spending_redirected": pledge.estimated_spending_redirected,
            "message": f"Nice! You've avoided the target {pledge.times_avoided_target} times."
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/pledges/mark-alternative-used")
async def mark_alternative_used(
    request: MarkAlternativeUsedRequest,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Mark that you used a community alternative."""
    try:
        pledge = service.mark_alternative_used(
            pledge_id=request.pledge_id,
            alternative_id=request.alternative_id
        )

        return {
            "success": True,
            "pledge_id": pledge.id,
            "alternatives_used": pledge.alternatives_used,
            "message": f"Awesome! You've used alternatives {pledge.alternatives_used} times."
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===== Alternative Endpoints =====

@router.post("/alternatives/create")
async def create_alternative(
    request: CreateAlternativeRequest,
    user: User = Depends(require_steward),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Create a corporate alternative (stewards or trusted members).

    GAP-134: Steward verification via trust score >= 0.9
    """
    alternative = service.create_alternative(
        created_by=user.id,
        campaign_type=request.campaign_type,
        replaces_corporation=request.replaces_corporation,
        replaces_service=request.replaces_service,
        alternative_type=request.alternative_type,
        name=request.name,
        description=request.description,
        cell_id=request.cell_id,
        network_wide=request.network_wide,
        contact_user_id=request.contact_user_id,
        access_instructions=request.access_instructions,
    )

    return {
        "success": True,
        "alternative_id": alternative.id,
        "name": alternative.name,
        "message": f"Alternative '{alternative.name}' created!"
    }


@router.get("/alternatives/{campaign_type}")
async def get_alternatives_for_type(
    campaign_type: CampaignType,
    cell_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get alternatives for a campaign type."""
    alternatives = service.get_alternatives_for_type(campaign_type, cell_id)

    return {
        "campaign_type": campaign_type.value,
        "alternatives": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "alternative_type": a.alternative_type,
                "replaces_corporation": a.replaces_corporation,
                "replaces_service": a.replaces_service,
                "times_used": a.times_used,
                "contact_user_id": a.contact_user_id,
                "access_instructions": a.access_instructions,
                "cell_id": a.cell_id,
                "network_wide": a.network_wide,
            }
            for a in alternatives
        ]
    }


# ===== Exit Progress Endpoints =====

@router.get("/exit-progress/my-progress")
async def get_my_exit_progress(
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get your personal exit progress (journey away from extractive economy)."""
    progress = service.get_or_create_exit_progress(user_id)

    return {
        "user_id": progress.user_id,
        "categories": progress.categories,
        "total_estimated_redirected": progress.total_estimated_redirected,
        "campaigns_participated": progress.campaigns_participated,
        "campaigns_completed": progress.campaigns_completed,
        "completion_rate": (progress.campaigns_completed / progress.campaigns_participated * 100) if progress.campaigns_participated > 0 else 0,
        "created_at": progress.created_at.isoformat(),
        "updated_at": progress.updated_at.isoformat(),
    }


# ===== Bulk Buy Endpoints =====

@router.post("/bulk-buy/create")
async def create_bulk_buy(
    request: CreateBulkBuyRequest,
    user: User = Depends(require_steward),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Create a bulk buy order (stewards only).

    GAP-134: Steward verification via trust score >= 0.9
    """
    bulk_buy = service.create_bulk_buy(
        coordinator_id=user.id,
        cell_id=request.cell_id,
        item_name=request.item_name,
        item_description=request.item_description,
        unit=request.unit,
        retail_price_per_unit=request.retail_price_per_unit,
        wholesale_price_per_unit=request.wholesale_price_per_unit,
        minimum_units=request.minimum_units,
        commitment_deadline=request.commitment_deadline,
        delivery_date=request.delivery_date,
        distribution_location=request.distribution_location,
        supplier=request.supplier,
        campaign_id=request.campaign_id,
    )

    return {
        "success": True,
        "bulk_buy_id": bulk_buy.id,
        "item_name": bulk_buy.item_name,
        "wholesale_price_per_unit": bulk_buy.wholesale_price_per_unit,
        "savings_percent": bulk_buy.savings_percent,
        "minimum_units": bulk_buy.minimum_units,
        "commitment_deadline": bulk_buy.commitment_deadline.isoformat(),
        "message": f"Bulk buy for {bulk_buy.item_name} created! {bulk_buy.savings_percent:.1f}% savings if we hit {bulk_buy.minimum_units} {bulk_buy.unit}."
    }


@router.post("/bulk-buy/commit")
async def commit_to_bulk_buy(
    request: CommitToBulkBuyRequest,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Commit to a bulk buy order."""
    try:
        commitment = service.commit_to_bulk_buy(
            user_id=user_id,
            bulk_buy_id=request.bulk_buy_id,
            units=request.units,
        )

        bulk_buy = service.get_bulk_buy(request.bulk_buy_id)

        return {
            "success": True,
            "commitment_id": commitment.id,
            "bulk_buy_id": commitment.bulk_buy_id,
            "units": commitment.units,
            "total_cost": commitment.total_cost,
            "current_committed_units": bulk_buy.current_committed_units if bulk_buy else 0,
            "minimum_units": bulk_buy.minimum_units if bulk_buy else 0,
            "threshold_met": bulk_buy.can_order() if bulk_buy else False,
            "message": f"Committed to {commitment.units} units for ${commitment.total_cost:.2f}!"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bulk-buy/{bulk_buy_id}")
async def get_bulk_buy_detail(
    bulk_buy_id: str,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get details for a bulk buy."""
    bulk_buy = service.get_bulk_buy(bulk_buy_id)
    if not bulk_buy:
        raise HTTPException(status_code=404, detail="Bulk buy not found")

    commitments = service.get_bulk_buy_commitments(bulk_buy_id)

    return {
        "bulk_buy": {
            "id": bulk_buy.id,
            "item_name": bulk_buy.item_name,
            "item_description": bulk_buy.item_description,
            "unit": bulk_buy.unit,
            "retail_price_per_unit": bulk_buy.retail_price_per_unit,
            "wholesale_price_per_unit": bulk_buy.wholesale_price_per_unit,
            "savings_percent": bulk_buy.savings_percent,
            "minimum_units": bulk_buy.minimum_units,
            "current_committed_units": bulk_buy.current_committed_units,
            "progress_percent": (bulk_buy.current_committed_units / bulk_buy.minimum_units * 100) if bulk_buy.minimum_units > 0 else 0,
            "threshold_met": bulk_buy.can_order(),
            "status": bulk_buy.status,
            "cell_id": bulk_buy.cell_id,
            "coordinator_id": bulk_buy.coordinator_id,
            "supplier": bulk_buy.supplier,
            "commitment_deadline": bulk_buy.commitment_deadline.isoformat(),
            "delivery_date": bulk_buy.delivery_date.isoformat(),
            "distribution_location": bulk_buy.distribution_location,
            "created_at": bulk_buy.created_at.isoformat(),
        },
        "commitment_count": len(commitments),
        "total_savings": (bulk_buy.retail_price_per_unit - bulk_buy.wholesale_price_per_unit) * bulk_buy.current_committed_units,
    }


@router.get("/bulk-buy/cell/{cell_id}")
async def get_bulk_buys_for_cell(
    cell_id: str,
    user_id: str = Depends(get_current_user),
    service: EconomicWithdrawalService = Depends(get_economic_withdrawal_service)
):
    """Get all bulk buys for a cell."""
    bulk_buys = service.get_bulk_buys_by_cell(cell_id)

    return {
        "cell_id": cell_id,
        "bulk_buys": [
            {
                "id": b.id,
                "item_name": b.item_name,
                "wholesale_price_per_unit": b.wholesale_price_per_unit,
                "savings_percent": b.savings_percent,
                "minimum_units": b.minimum_units,
                "current_committed_units": b.current_committed_units,
                "threshold_met": b.can_order(),
                "status": b.status,
                "commitment_deadline": b.commitment_deadline.isoformat(),
                "delivery_date": b.delivery_date.isoformat(),
            }
            for b in bulk_buys
        ]
    }
