"""
Abundance Osmosis API Endpoints (GAP-63)

Kropotkin: "In nature, abundance spreads without explicit transactions."

Endpoints for community shelves, circulating resources,
overflow detection, and knowledge ripples.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, UTC
import uuid
from typing import Optional

from ..models.abundance_osmosis import (
    CommunityShelf,
    ShelfItem,
    CirculatingResource,
    OverflowPrompt,
    KnowledgeRipple,
)
from ..database import get_database
from ..repositories.abundance_osmosis_repo import AbundanceOsmosisRepository
from ..repositories.vf.listing_repo import ListingRepository

router = APIRouter(prefix="/abundance-osmosis", tags=["abundance-osmosis"])


# === Community Shelves ===


@router.post("/shelves", response_model=dict)
async def create_shelf(
    name: str,
    location: str,
    created_by: str,
    cell_id: str,
    is_virtual: bool = False,
):
    """
    Create a community shelf.

    Shelves are "take what you need" spaces where giving and taking are anonymous.
    """
    try:
        shelf = CommunityShelf(
            id=f"shelf:{uuid.uuid4()}",
            name=name,
            location=location,
            created_by=created_by,
            cell_id=cell_id,
            is_virtual=is_virtual,
        )

        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        created = repo.create_shelf(shelf)
        db.close()

        return {"status": "created", "shelf": created.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shelves/cell/{cell_id}", response_model=dict)
async def get_cell_shelves(cell_id: str):
    """Get all community shelves in a cell"""
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        shelves = repo.get_shelves_by_cell(cell_id)
        db.close()

        return {"shelves": [s.to_dict() for s in shelves]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shelves/{shelf_id}/items", response_model=dict)
async def add_item_to_shelf(
    shelf_id: str, description: str, category: str, added_by: Optional[str] = None
):
    """
    Add an item to a community shelf.

    added_by can be None for anonymous giving (GAP-61).
    """
    try:
        item = ShelfItem(
            id=f"shelf-item:{uuid.uuid4()}",
            shelf_id=shelf_id,
            description=description,
            category=category,
            added_by=added_by,  # None for anonymous
        )

        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        created = repo.add_item_to_shelf(item)
        db.close()

        return {"status": "added", "item": created.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shelves/{shelf_id}/items", response_model=dict)
async def get_shelf_items(shelf_id: str):
    """Get all available items on a shelf"""
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        items = repo.get_available_items(shelf_id)
        db.close()

        return {"items": [i.to_dict() for i in items]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/shelves/items/{item_id}", response_model=dict)
async def take_item(item_id: str):
    """
    Mark item as taken.

    NOTE: We don't track who took it. The item is just deleted.
    The abundance flows anonymously.
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        repo.mark_item_taken(item_id)
        db.close()

        return {
            "status": "taken",
            "message": "Item removed from shelf. No record of who took it.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shelves/{shelf_id}/stats", response_model=dict)
async def get_shelf_stats(shelf_id: str, days: int = 7):
    """
    Get aggregate stats for a shelf (for stewards).

    Returns counts only - no individual tracking.
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        stats = repo.get_shelf_stats(shelf_id, days)
        db.close()

        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Circulating Resources ===


@router.post("/circulating-resources", response_model=dict)
async def create_circulating_resource(
    description: str,
    category: str,
    current_location: str,
    cell_id: str,
    notes: Optional[str] = None,
):
    """
    Register a resource that belongs to the community.

    We track WHERE it is, not WHO OWNS it.
    """
    try:
        resource = CirculatingResource(
            id=f"circulating:{uuid.uuid4()}",
            description=description,
            category=category,
            current_location=current_location,
            current_holder_notes=notes,
            cell_id=cell_id,
        )

        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        created = repo.create_circulating_resource(resource)
        db.close()

        return {"status": "created", "resource": created.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/circulating-resources/{resource_id}/location", response_model=dict)
async def update_resource_location(
    resource_id: str, new_location: str, notes: Optional[str] = None
):
    """
    Update where a circulating resource currently is.

    "Drill is now at Bob's place" - just location, not ownership.
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        repo.update_resource_location(resource_id, new_location, notes)
        db.close()

        return {"status": "updated", "new_location": new_location}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/circulating-resources/cell/{cell_id}", response_model=dict)
async def get_circulating_resources(cell_id: str, search: Optional[str] = None):
    """Get all circulating resources in a cell, optionally filtered by search term"""
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)

        if search:
            resources = repo.find_resource(cell_id, search)
        else:
            resources = repo.get_circulating_resources(cell_id)

        db.close()

        return {"resources": [r.to_dict() for r in resources]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Overflow Detection ===


@router.get("/overflow-prompts/{user_id}", response_model=dict)
async def get_overflow_prompts(user_id: str):
    """
    Get overflow prompts for a user.

    "Your tomatoes have been available for 3 days. Let them flow to the community shelf?"
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        prompts = repo.get_pending_overflow_prompts(user_id)
        db.close()

        return {"prompts": [p.to_dict() for p in prompts]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/overflow-prompts/{prompt_id}/respond", response_model=dict)
async def respond_to_overflow_prompt(
    prompt_id: str, response: str, snooze_days: Optional[int] = None
):
    """
    Respond to an overflow prompt.

    response: "accepted", "declined", "snoozed"
    """
    try:
        snooze_until = None
        if response == "snoozed" and snooze_days:
            snooze_until = datetime.now(UTC) + timedelta(days=snooze_days)

        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        repo.update_overflow_prompt_status(prompt_id, response, snooze_until)
        db.close()

        return {"status": "updated", "response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Background job to detect overflow (would run periodically) ===


@router.post("/jobs/detect-overflow", response_model=dict)
async def detect_overflow(days_threshold: int = 3):
    """
    Background job: Detect offers that have been sitting for too long.

    Suggests moving them to community shelf.
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)
        osmosis_repo = AbundanceOsmosisRepository(db.conn)

        # Find old active offers
        all_offers = listing_repo.find_offers(status="active", limit=1000)
        threshold = datetime.now(UTC) - timedelta(days=days_threshold)

        prompts_created = 0
        for offer in all_offers:
            offer_age = datetime.now(UTC) - offer.created_at
            if offer_age.days >= days_threshold:
                # Check if we already prompted for this
                existing = osmosis_repo.get_pending_overflow_prompts(offer.provider_id)
                if not any(p.listing_id == offer.id for p in existing):
                    # Create new prompt
                    prompt = OverflowPrompt(
                        id=f"overflow:{uuid.uuid4()}",
                        user_id=offer.provider_id,
                        listing_id=offer.id,
                        days_available=offer_age.days,
                    )
                    osmosis_repo.create_overflow_prompt(prompt)
                    prompts_created += 1

        db.close()

        return {
            "status": "complete",
            "prompts_created": prompts_created,
            "message": f"Created {prompts_created} overflow prompts for offers older than {days_threshold} days",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Knowledge Ripples ===


@router.get("/knowledge-ripples/ready", response_model=dict)
async def get_ready_knowledge_ripples(weeks_ago: int = 2):
    """
    Get learning exchanges ready for teaching suggestion.

    "You learned bicycle repair 2 weeks ago. Feeling confident? Maybe teach someone else?"
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        ripples = repo.get_ripe_knowledge_ripples(weeks_ago)
        db.close()

        return {"ripples": [r.to_dict() for r in ripples]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge-ripples/{ripple_id}/prompted", response_model=dict)
async def mark_ripple_prompted(ripple_id: str):
    """Mark that we showed the teaching suggestion to the user"""
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        repo.mark_ripple_prompted(ripple_id)
        db.close()

        return {"status": "prompted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge-ripples/{ripple_id}/dismiss", response_model=dict)
async def dismiss_ripple(ripple_id: str, permanently: bool = False):
    """
    User declined to teach.

    permanently=True: "Stop suggesting I teach this"
    """
    try:
        db = get_database()
        db.connect()
        repo = AbundanceOsmosisRepository(db.conn)
        repo.dismiss_ripple(ripple_id, permanently)
        db.close()

        return {"status": "dismissed", "permanently": permanently}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
