"""Matches API Endpoints"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid

from ...models.vf.match import Match
from ...database import get_database
from ...repositories.vf.match_repo import MatchRepository
from ...services.vf_bundle_publisher import VFBundlePublisher

router = APIRouter(prefix="/vf/matches", tags=["matches"])


@router.post("/", response_model=dict)
async def create_match(match_data: dict):
    """Create a new match (offer + need pairing)"""
    try:
        if "id" not in match_data:
            match_data["id"] = f"match:{uuid.uuid4()}"
        match_data["created_at"] = datetime.now().isoformat()

        match = Match.from_dict(match_data)

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
