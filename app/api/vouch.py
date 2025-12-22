"""Web of Trust Vouch API Endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os

from app.models.vouch import (
    Vouch,
    VouchRequest,
    RevocationRequest,
    TrustScore,
    TRUST_THRESHOLDS,
)
from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.auth.middleware import get_current_user


router = APIRouter(prefix="/vouch", tags=["web-of-trust"])


# Dependency injection for services
def get_vouch_repo():
    """Get VouchRepository instance."""
    db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
    return VouchRepository(db_path)


def get_trust_service(repo: VouchRepository = Depends(get_vouch_repo)):
    """Get WebOfTrustService instance."""
    return WebOfTrustService(repo)


@router.post("/", response_model=Vouch, summary="Create a vouch for another user")
async def create_vouch(
    request: VouchRequest,
    current_user=Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service),
    repo: VouchRepository = Depends(get_vouch_repo),
):
    """
    Vouch for another user.

    Requires:
    - Voucher must have trust >= 0.7
    - Cannot vouch for same person twice
    """
    voucher_id = current_user.id

    # Check eligibility
    eligibility = trust_service.get_vouch_eligibility(voucher_id, request.vouchee_id)

    if not eligibility["can_vouch"]:
        raise HTTPException(
            status_code=403,
            detail=eligibility["reason"]
        )

    # Create the vouch
    vouch = repo.create_vouch(
        voucher_id=voucher_id,
        vouchee_id=request.vouchee_id,
        context=request.context,
    )

    # Trigger trust recomputation for vouchee
    trust_service.compute_trust_score(request.vouchee_id, force_recompute=True)

    return vouch


@router.get("/status/{user_id}", response_model=TrustScore, summary="Get trust score for a user")
async def get_trust_status(
    user_id: str,
    current_user=Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Get the computed trust score for a user.

    Returns:
    - Trust level (0.0 - 1.0)
    - Vouch chains to genesis nodes
    - Distance from genesis
    - Vouch/revocation counts
    """
    trust_score = trust_service.compute_trust_score(user_id)
    return trust_score


@router.get("/status", response_model=TrustScore, summary="Get your own trust score")
async def get_my_trust_status(
    current_user=Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Get your own trust score.
    """
    trust_score = trust_service.compute_trust_score(current_user.id)
    return trust_score


@router.get("/received", response_model=List[Vouch], summary="Get vouches you've received")
async def get_received_vouches(
    current_user=Depends(get_current_user),
    repo: VouchRepository = Depends(get_vouch_repo),
    include_revoked: bool = False,
):
    """
    Get all vouches you've received.
    """
    vouches = repo.get_vouches_for_user(current_user.id, include_revoked=include_revoked)
    return vouches


@router.get("/given", response_model=List[Vouch], summary="Get vouches you've given")
async def get_given_vouches(
    current_user=Depends(get_current_user),
    repo: VouchRepository = Depends(get_vouch_repo),
):
    """
    Get all vouches you've given to others.
    """
    vouches = repo.get_vouches_by_user(current_user.id)
    return vouches


@router.post("/revoke", summary="Revoke a vouch")
async def revoke_vouch(
    request: RevocationRequest,
    current_user=Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service),
    repo: VouchRepository = Depends(get_vouch_repo),
):
    """
    Revoke a vouch you previously gave.

    GAP-105: Implements 48-hour cooloff grace period:
    - Within 48 hours: revoke without consequence, reason optional
    - After 48 hours: requires reason, causes trust cascade

    This will:
    1. Mark the vouch as revoked
    2. Recompute trust for the vouchee (trust drops)
    3. Cascade recomputation for anyone they vouched (if past cooloff)

    Requires:
    - You must be the voucher (can't revoke someone else's vouch)
    """
    from datetime import datetime, timedelta
    from app.models.vouch import VOUCH_COOLOFF_HOURS

    vouch = repo.get_vouch(request.vouch_id)

    if not vouch:
        raise HTTPException(status_code=404, detail="Vouch not found")

    # Verify you're the voucher
    if vouch.voucher_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only revoke vouches you gave"
        )

    if vouch.revoked:
        raise HTTPException(status_code=400, detail="Vouch already revoked")

    # GAP-105: Check cooloff period
    hours_since_vouch = (datetime.now(UTC) - vouch.created_at).total_seconds() / 3600

    if hours_since_vouch <= VOUCH_COOLOFF_HOURS:
        # Within cooloff - revoke without cascade, no reason required
        success = repo.revoke_vouch(
            request.vouch_id,
            request.reason or "Revoked within cooloff period"
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to revoke vouch")

        # Just recompute the vouchee's trust, no cascade
        trust_service.compute_trust_score(vouch.vouchee_id, force_recompute=True)

        return {
            "success": True,
            "vouch_id": request.vouch_id,
            "cooloff": True,
            "message": "Vouch revoked (within cooloff period - no consequences)"
        }

    # After cooloff - require reason and cascade
    if not request.reason:
        raise HTTPException(
            status_code=400,
            detail=f"Reason required for revocation after {VOUCH_COOLOFF_HOURS}h cooloff period"
        )

    # Revoke with cascade
    result = trust_service.revoke_vouch_with_cascade(request.vouch_id, request.reason)

    return {
        "success": True,
        "vouch_id": request.vouch_id,
        "cooloff": False,
        "affected_users": result["affected_users"],
        "message": f"Vouch revoked, {len(result['affected_users'])} users' trust recomputed"
    }


@router.get("/eligibility/{vouchee_id}", summary="Check if you can vouch for someone")
async def check_vouch_eligibility(
    vouchee_id: str,
    current_user=Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Check if you're eligible to vouch for another user.

    Returns:
    - can_vouch: bool
    - reason: why or why not
    - voucher_trust: your current trust level
    """
    eligibility = trust_service.get_vouch_eligibility(current_user.id, vouchee_id)
    return eligibility


@router.get("/thresholds", summary="Get trust thresholds for actions")
async def get_trust_thresholds():
    """
    Get the trust score thresholds required for various actions.
    """
    return {
        "thresholds": TRUST_THRESHOLDS,
        "description": {
            "view_public_offers": "Minimum trust to view public offers",
            "post_offers_needs": "Minimum trust to post offers and needs",
            "send_messages": "Minimum trust to send direct messages",
            "vouch_others": "Minimum trust to vouch for new members",
            "steward_actions": "Minimum trust for steward/admin actions",
        }
    }


@router.post("/genesis/add/{user_id}", summary="Add a genesis node (admin only)")
async def add_genesis_node(
    user_id: str,
    notes: str = "",
    current_user=Depends(get_current_user),
    repo: VouchRepository = Depends(get_vouch_repo),
    trust_service: WebOfTrustService = Depends(get_trust_service),
):
    """
    Add a user as a genesis node (trust seed).

    This is a privileged operation for initial network bootstrap.
    In production, this should require multi-sig or steward consensus.

    For MVP, requires the caller to already be a genesis node or the first user.
    """
    # Check if caller is genesis node (or if no genesis nodes exist yet)
    genesis_nodes = repo.get_genesis_nodes()

    if genesis_nodes:
        # Existing genesis nodes - verify caller is one
        if not repo.is_genesis_node(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Only existing genesis nodes can add new genesis nodes"
            )

    # Add the genesis node
    success = repo.add_genesis_node(
        user_id=user_id,
        added_by=current_user.id,
        notes=notes,
    )

    if not success:
        raise HTTPException(status_code=400, detail="User is already a genesis node")

    # Recompute their trust (should now be 1.0)
    trust_score = trust_service.compute_trust_score(user_id, force_recompute=True)

    return {
        "success": True,
        "user_id": user_id,
        "trust_score": trust_score.computed_trust,
        "message": f"Added {user_id} as genesis node"
    }


@router.get("/genesis", summary="List all genesis nodes")
async def list_genesis_nodes(
    repo: VouchRepository = Depends(get_vouch_repo),
):
    """
    List all genesis nodes (trust seeds) in the network.
    """
    genesis_nodes = repo.get_genesis_nodes()
    return {
        "genesis_nodes": genesis_nodes,
        "count": len(genesis_nodes),
    }
