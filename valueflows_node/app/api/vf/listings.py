"""
Listings API Endpoints

POST /vf/listings - Create offer/need
GET /vf/listings - Browse offers/needs
GET /vf/listings/{id} - Get listing details
PATCH /vf/listings/{id} - Update listing
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from datetime import datetime
import uuid

from ...models.vf.listing import Listing, ListingType
from ...models.vf.resource_spec import ResourceCategory
from ...models.requests.listings import ListingCreate, ListingUpdate, ListingQuery
from ...database import get_database
from ...repositories.vf.listing_repo import ListingRepository
from ...services.signing_service import SigningService
from ...services.vf_bundle_publisher import VFBundlePublisher

router = APIRouter(prefix="/vf/listings", tags=["listings"])


@router.post("", response_model=dict)
async def create_listing(listing_data: ListingCreate):
    """
    Create a new listing (offer or need).

    GAP-43: Now uses validated Pydantic model instead of raw dict.

    Request body validated for:
    - Required fields present
    - Correct types and formats
    - String length limits
    - Numeric ranges
    - Enum values
    """
    try:
        # Convert validated Pydantic model to dict
        data = listing_data.model_dump()

        # Generate ID
        data["id"] = f"listing:{uuid.uuid4()}"

        # Set timestamps
        data["created_at"] = datetime.now().isoformat()

        # Create Listing object
        listing = Listing.from_dict(data)

        # Sign the listing
        # Use the node's signing service
        signer = SigningService()
        signer.sign_and_update(listing, listing.agent_id)

        # Save to database
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)
        created_listing = listing_repo.create(listing)

        # Publish as DTN bundle
        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(created_listing, "Listing")

        db.close()

        # Return the listing object directly for compatibility with tests
        return created_listing.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=dict)
async def browse_listings(
    listing_type: Optional[str] = Query(None, description="Filter by type: offer or need"),
    category: Optional[str] = Query(None, description="Filter by resource category"),
    location_id: Optional[str] = Query(None, description="Filter by location"),
    status: str = Query("active", description="Filter by status"),
    limit: int = Query(100, description="Maximum results")
):
    """
    Browse listings with filters.

    Query parameters:
    - listing_type: "offer" or "need"
    - category: Resource category
    - location_id: Location ID
    - status: Listing status
    - limit: Maximum results
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        # Convert category string to enum if provided
        category_enum = ResourceCategory(category) if category else None

        # Fetch listings based on type
        if listing_type == "offer":
            listings = listing_repo.find_offers(
                category=category_enum,
                location_id=location_id,
                status=status,
                limit=limit
            )
        elif listing_type == "need":
            listings = listing_repo.find_needs(
                category=category_enum,
                location_id=location_id,
                status=status,
                limit=limit
            )
        else:
            # Get both
            offers = listing_repo.find_offers(category=category_enum, location_id=location_id, status=status, limit=limit//2)
            needs = listing_repo.find_needs(category=category_enum, location_id=location_id, status=status, limit=limit//2)
            listings = offers + needs

        db.close()

        return {
            "listings": [l.to_dict() for l in listings],
            "count": len(listings)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{listing_id}", response_model=dict)
async def get_listing(listing_id: str):
    """Get listing by ID"""
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)
        listing = listing_repo.find_by_id(listing_id)
        db.close()

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        return listing.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{listing_id}", response_model=dict)
async def update_listing(listing_id: str, updates: ListingUpdate):
    """
    Update listing (e.g., mark as fulfilled).

    GAP-43: Now uses validated Pydantic model instead of raw dict.
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        listing = listing_repo.find_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Convert validated model to dict, excluding unset fields
        update_data = updates.model_dump(exclude_unset=True)

        # Apply updates
        if "status" in update_data:
            listing.status = update_data["status"]
        if "quantity" in update_data:
            listing.quantity = update_data["quantity"]
        if "description" in update_data:
            listing.description = update_data["description"]
        if "title" in update_data:
            listing.title = update_data["title"]
        if "unit" in update_data:
            listing.unit = update_data["unit"]
        if "location_id" in update_data:
            listing.location_id = update_data["location_id"]
        if "available_from" in update_data:
            listing.available_from = update_data["available_from"]
        if "available_until" in update_data:
            listing.available_until = update_data["available_until"]
        if "image_url" in update_data:
            listing.image_url = update_data["image_url"]

        # Update in database
        updated_listing = listing_repo.update(listing)

        # Publish update as bundle
        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_listing, "Listing")

        db.close()

        # Return the listing object directly for compatibility with tests
        return updated_listing.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: str):
    """
    Delete a listing.

    NOTE: Ownership verification requires GAP-02 (User Identity System).
    Currently allows deletion without auth checks.
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        # Check if listing exists
        listing = listing_repo.find_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # TODO (GAP-02): Add ownership verification when auth is implemented
        # if listing.agent_id != request.state.user.id:
        #     raise HTTPException(status_code=403, detail="Not authorized to delete this listing")

        # Delete listing
        deleted = listing_repo.delete(listing_id)

        db.close()

        if not deleted:
            raise HTTPException(status_code=404, detail="Listing not found")

        # 204 No Content - FastAPI handles this automatically with status_code=204
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
