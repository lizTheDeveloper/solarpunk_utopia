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
from ...auth.middleware import require_auth, require_steward
from ...auth.models import User

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
        # For anonymous gifts (GAP-61), sign with "anonymous" identifier
        # For attributed listings, sign with the agent_id
        signer = SigningService()
        signing_id = "anonymous" if listing.anonymous else listing.agent_id
        signer.sign_and_update(listing, signing_id)

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


@router.get("/community-shelf", response_model=dict)
async def browse_community_shelf(
    category: Optional[str] = Query(None, description="Filter by resource category"),
    location_id: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(100, description="Maximum results")
):
    """
    Browse the community shelf - anonymous gifts from generous neighbors.

    GAP-61: Emma Goldman - "The most violent element in society is ignorance."
    Anonymous gifts allow pure generosity without expectation of reciprocity or recognition.

    Returns only active offers marked as anonymous.

    Query parameters:
    - category: Resource category (food, tools, etc.)
    - location_id: Location ID
    - limit: Maximum results
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        # Convert category string to enum if provided
        category_enum = ResourceCategory(category) if category else None

        # Get anonymous gifts
        gifts = listing_repo.find_anonymous_gifts(
            category=category_enum,
            location_id=location_id,
            limit=limit
        )

        db.close()

        return {
            "gifts": [g.to_dict() for g in gifts],
            "count": len(gifts),
            "message": "These gifts are offered anonymously - take what you need, give what you can."
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
async def update_listing(
    listing_id: str,
    updates: ListingUpdate,
    current_user: User = Depends(require_auth)
):
    """
    Update listing (owner only).

    GAP-43: Now uses validated Pydantic model instead of raw dict.
    GAP-71: Now requires authentication and ownership verification.

    Args:
        listing_id: ID of the listing to update
        updates: Fields to update
        current_user: Authenticated user (from require_auth dependency)

    Returns:
        Updated listing

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized (not owner)
        HTTPException 404: If listing not found
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        listing = listing_repo.find_by_id(listing_id)
        if not listing:
            db.close()
            raise HTTPException(status_code=404, detail="Listing not found")

        # Check ownership - only owner can edit
        if listing.agent_id != current_user.id:
            db.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized to edit this listing. Only the owner can edit listings."
            )

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
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(require_auth)
):
    """
    Delete a listing (owner or steward only).

    GAP-71: Now requires authentication and ownership verification.
    Only the listing owner or community stewards (trust >= 0.9) can delete listings.

    Args:
        listing_id: ID of the listing to delete
        current_user: Authenticated user (from require_auth dependency)

    Returns:
        204 No Content on success

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized (not owner and not steward)
        HTTPException 404: If listing not found
    """
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        # Check if listing exists
        listing = listing_repo.find_by_id(listing_id)
        if not listing:
            db.close()
            raise HTTPException(status_code=404, detail="Listing not found")

        # Check ownership
        is_owner = listing.agent_id == current_user.id

        # Check if user is a steward (trust >= 0.9)
        # Import here to avoid circular dependencies
        from ...services.web_of_trust_service import WebOfTrustService
        from ...database.vouch_repository import VouchRepository

        vouch_repo = VouchRepository(db_path="data/solarpunk.db")
        trust_service = WebOfTrustService(vouch_repo)
        trust_score = trust_service.compute_trust_score(current_user.id)
        is_steward = trust_score.computed_trust >= 0.9

        # Verify authorization
        if not is_owner and not is_steward:
            db.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this listing. Only the owner or community stewards can delete listings."
            )

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
