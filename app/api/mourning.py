"""Mourning Protocol API - GAP-67

Creating space for grief in the community.
"The moment we choose to love we begin to move against domination." - bell hooks
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, UTC
import uuid

from app.models.mourning import (
    MourningPeriod,
    Memorial,
    MemorialEntry,
    GriefSupport,
    MourningBanner
)
from app.repositories.mourning_repository import MourningRepository
from app.auth.middleware import require_steward, require_auth
from app.auth.models import User
from fastapi import Depends

router = APIRouter(prefix="/api/mourning", tags=["mourning"])


# ===== Request Models =====

class ActivateMourningRequest(BaseModel):
    """Request to activate mourning mode."""
    cell_id: str
    trigger: str  # "death", "departure", "collective_trauma", "other"
    honoring: Optional[str] = None
    description: Optional[str] = None
    duration_days: int = 7


class AddMemorialEntryRequest(BaseModel):
    """Request to add entry to memorial."""
    memorial_id: str
    content: str
    media_url: Optional[str] = None


class OfferSupportRequest(BaseModel):
    """Request to offer support during mourning."""
    mourning_id: str
    support_type: str  # "meals", "childcare", "errands", "presence", "other"
    details: str


# ===== Endpoints =====

@router.post("/activate")
async def activate_mourning(
    request: ActivateMourningRequest,
    steward: User = Depends(require_steward)
):
    """Activate mourning mode for a community.

    When activated:
    - Metrics tracking pauses
    - Non-urgent notifications stop
    - Memorial space created
    - Support offers enabled

    "Grief is not something to get over, but something to move through." - bell hooks

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        repo = MourningRepository()

        # Create mourning period
        mourning_id = f"mourning-{uuid.uuid4()}"
        mourning = MourningPeriod(
            id=mourning_id,
            cell_id=request.cell_id,
            trigger=request.trigger,
            honoring=request.honoring,
            description=request.description,
            duration_days=request.duration_days,
            created_by=steward.id
        )

        repo.create_mourning_period(mourning)

        # Create memorial if requested
        memorial_id = f"memorial-{uuid.uuid4()}"
        memorial = Memorial(
            id=memorial_id,
            mourning_id=mourning_id,
            person_name=request.honoring,
            created_at=datetime.now(UTC)
        )
        repo.create_memorial(memorial)

        return {
            "status": "success",
            "message": "Mourning mode activated",
            "mourning_id": mourning_id,
            "memorial_id": memorial_id,
            "ends_at": mourning.ends_at.isoformat(),
            "note": "Community metrics paused. Take the time you need."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate mourning: {str(e)}")


@router.get("/active/{cell_id}")
async def get_active_mourning(cell_id: str):
    """Get active mourning period for a cell (if any)."""
    try:
        repo = MourningRepository()
        mourning = repo.get_active_mourning(cell_id)

        if not mourning:
            return {
                "status": "no_mourning",
                "message": "No active mourning period"
            }

        memorial = repo.get_memorial(mourning.id)

        return {
            "status": "mourning_active",
            "mourning": mourning.dict(),
            "memorial_id": memorial.id if memorial else None,
            "banner": {
                "message": f"We are honoring the memory of {mourning.honoring}." if mourning.honoring else "Our community is in mourning.",
                "quote": "Grief is not something to get over, but something to move through. - bell hooks"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mourning status: {str(e)}")


@router.post("/memorial/add-entry")
async def add_memorial_entry(
    request: AddMemorialEntryRequest,
    current_user: User = Depends(require_auth)
):
    """Add an entry to a memorial.

    Share a memory, reflection, or photo.
    """
    try:
        repo = MourningRepository()

        entry = MemorialEntry(
            id=f"entry-{uuid.uuid4()}",
            memorial_id=request.memorial_id,
            author_id=current_user.id,
            content=request.content,
            media_url=request.media_url,
            created_at=datetime.now(UTC)
        )

        repo.add_memorial_entry(entry)

        return {
            "status": "success",
            "message": "Entry added to memorial",
            "entry_id": entry.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add entry: {str(e)}")


@router.get("/memorial/{memorial_id}/entries")
async def get_memorial_entries(memorial_id: str):
    """Get all entries for a memorial."""
    try:
        repo = MourningRepository()
        entries = repo.get_memorial_entries(memorial_id)

        return {
            "status": "success",
            "entries": [e.dict() for e in entries],
            "count": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entries: {str(e)}")


@router.post("/support/offer")
async def offer_support(
    request: OfferSupportRequest,
    current_user: User = Depends(require_auth)
):
    """Offer support during mourning.

    Simple options: meals, childcare, errands, presence.
    """
    try:
        repo = MourningRepository()

        support = GriefSupport(
            id=f"support-{uuid.uuid4()}",
            mourning_id=request.mourning_id,
            offered_by=current_user.id,
            support_type=request.support_type,
            details=request.details,
            created_at=datetime.now(UTC)
        )

        repo.add_support_offer(support)

        return {
            "status": "success",
            "message": "Support offer created",
            "support_id": support.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to offer support: {str(e)}")


@router.get("/support/{mourning_id}")
async def get_support_offers(mourning_id: str):
    """Get all support offers for a mourning period."""
    try:
        repo = MourningRepository()
        offers = repo.get_support_offers(mourning_id)

        return {
            "status": "success",
            "offers": [o.dict() for o in offers],
            "count": len(offers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get offers: {str(e)}")


@router.post("/extend")
async def extend_mourning(
    mourning_id: str,
    additional_days: int,
    steward: User = Depends(require_steward)
):
    """Extend a mourning period.

    Grief takes time. Community can extend when needed.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        repo = MourningRepository()
        repo.extend_mourning(mourning_id, additional_days)

        return {
            "status": "success",
            "message": f"Mourning extended by {additional_days} days",
            "note": "Take the time you need."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extend: {str(e)}")


@router.post("/end-early")
async def end_mourning_early(
    mourning_id: str,
    steward: User = Depends(require_steward)
):
    """End mourning period early (if community is ready).

    Memorial remains accessible.

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        repo = MourningRepository()
        repo.end_mourning_early(mourning_id)

        return {
            "status": "success",
            "message": "Mourning period ended",
            "note": "Memorial remains accessible for remembrance."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end mourning: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "feature": "mourning-protocol",
        "gap": "GAP-67",
        "philosophy": "The moment we choose to love we begin to move against domination - bell hooks"
    }
