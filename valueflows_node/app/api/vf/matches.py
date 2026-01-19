"""Matches API Endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid
import sqlite3

from ...models.vf.match import Match, MatchStatus
from ...models.requests.vf_objects import MatchCreate
from ...database import get_database
from ...repositories.vf.match_repo import MatchRepository
from ...services.vf_bundle_publisher import VFBundlePublisher
from ...auth.middleware import require_auth
from ...auth.models import User

router = APIRouter(prefix="/vf/matches", tags=["matches"])


def get_block_repo():
    """Get block repository - import here to avoid circular dependencies"""
    from app.database.block_repository import BlockRepository
    # Use existing solarpunk.db connection
    conn = sqlite3.connect("data/solarpunk.db", check_same_thread=False)
    return BlockRepository(conn)


@router.get("/", response_model=dict)
async def get_matches(status: str = None, agent_id: str = None):
    """Get all matches, optionally filtered by status or agent"""
    try:
        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)

        if agent_id:
            matches = match_repo.find_by_agent(agent_id)
        else:
            matches = match_repo.find_all()
            # Filter by status if provided
            if status:
                matches = [m for m in matches if m.status.value == status]

        db.close()

        return {
            "matches": [m.to_dict() for m in matches],
            "count": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=dict)
async def create_match(match_data: MatchCreate):
    """
    Create a new match (offer + need pairing).

    GAP-43: Now uses Pydantic validation model.

    Validates:
    - Required fields present
    - Field types correct
    - Numeric ranges valid
    """
    try:
        # Convert validated Pydantic model to dict
        data = match_data.model_dump()

        data["id"] = f"match:{uuid.uuid4()}"
        data["created_at"] = datetime.now().isoformat()

        match = Match.from_dict(data)

        # GAP-107: Check if either user has blocked the other
        block_repo = get_block_repo()
        if block_repo.is_blocked(match.provider_id, match.receiver_id):
            # Silently fail - don't reveal that block exists
            raise HTTPException(status_code=404, detail="Match not possible")

        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)
        created_match = match_repo.create(match)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(created_match, "Match")

        db.close()

        return {
            "status": "created",
            "match": created_match.to_dict(),
            "bundle_id": bundle["bundleId"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{match_id}/approve", response_model=dict)
async def approve_match(match_id: str, agent_id: str):
    """Approve a match (provider or receiver)"""
    try:
        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)

        match = match_repo.find_by_id(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        # Determine who is approving
        if match.provider_id == agent_id:
            match.provider_approved = True
            match.provider_approved_at = datetime.now()
        elif match.receiver_id == agent_id:
            match.receiver_approved = True
            match.receiver_approved_at = datetime.now()
        else:
            raise HTTPException(status_code=403, detail="Not authorized to approve this match")

        # Update status if both approved
        if match.is_fully_approved():
            match.status = "accepted"

        updated_match = match_repo.update(match)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_match, "Match")

        db.close()

        return {
            "status": "approved",
            "match": updated_match.to_dict(),
            "fully_approved": updated_match.is_fully_approved()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/accept", response_model=dict)
async def accept_match(
    match_id: str,
    current_user: User = Depends(require_auth)
):
    """
    Accept a match (provider or receiver).

    GAP-65: Frontend-compatible endpoint with authentication.

    Args:
        match_id: ID of the match to accept
        current_user: Authenticated user

    Returns:
        Updated match status

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized (not provider or receiver)
        HTTPException 404: If match not found
    """
    try:
        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)

        match = match_repo.find_by_id(match_id)
        if not match:
            db.close()
            raise HTTPException(status_code=404, detail="Match not found")

        # Verify user is participant in this match
        is_provider = match.provider_id == current_user.id
        is_receiver = match.receiver_id == current_user.id

        if not is_provider and not is_receiver:
            db.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized to accept this match. Only participants can accept matches."
            )

        # Mark approval from the authenticated user
        if is_provider:
            match.provider_approved = True
            match.provider_approved_at = datetime.now()
        if is_receiver:
            match.receiver_approved = True
            match.receiver_approved_at = datetime.now()

        # Update status if both approved
        if match.provider_approved and match.receiver_approved:
            match.status = MatchStatus.ACCEPTED

        updated_match = match_repo.update(match)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_match, "Match")

        db.close()

        return {
            "status": "accepted" if match.status == MatchStatus.ACCEPTED else "pending_other_approval",
            "match": updated_match.to_dict(),
            "bundle_id": bundle["bundleId"],
            "fully_approved": match.provider_approved and match.receiver_approved
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{match_id}/reject", response_model=dict)
async def reject_match(
    match_id: str,
    current_user: User = Depends(require_auth),
    reason: str = None
):
    """
    Reject a match (provider or receiver).

    GAP-65: Frontend-compatible endpoint with authentication.

    Args:
        match_id: ID of the match to reject
        current_user: Authenticated user
        reason: Optional reason for rejection

    Returns:
        Updated match status

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized (not provider or receiver)
        HTTPException 404: If match not found
    """
    try:
        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)

        match = match_repo.find_by_id(match_id)
        if not match:
            db.close()
            raise HTTPException(status_code=404, detail="Match not found")

        # Verify user is participant in this match
        is_provider = match.provider_id == current_user.id
        is_receiver = match.receiver_id == current_user.id

        if not is_provider and not is_receiver:
            db.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized to reject this match. Only participants can reject matches."
            )

        # Reject the match (one rejection is enough)
        match.status = MatchStatus.REJECTED

        updated_match = match_repo.update(match)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_match, "Match")

        db.close()

        return {
            "status": "rejected",
            "match": updated_match.to_dict(),
            "reason": reason,
            "bundle_id": bundle["bundleId"],
            "rejected_by": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agent/{agent_id}", response_model=dict)
async def get_agent_matches(agent_id: str):
    """Get all matches for an agent"""
    try:
        db = get_database()
        db.connect()
        match_repo = MatchRepository(db.conn)
        matches = match_repo.find_by_agent(agent_id)
        db.close()

        return {
            "matches": [m.to_dict() for m in matches],
            "count": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
