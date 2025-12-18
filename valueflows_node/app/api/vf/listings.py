"""
Listings API Endpoints

POST /vf/listings - Create offer/need
GET /vf/listings - Browse offers/needs
GET /vf/listings/{id} - Get listing details
PATCH /vf/listings/{id} - Update listing
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import uuid

from ...models.vf.listing import Listing, ListingType
from ...models.vf.resource_spec import ResourceCategory
from ...database import get_database
from ...repositories.vf.listing_repo import ListingRepository
from ...services.signing_service import SigningService
from ...services.vf_bundle_publisher import VFBundlePublisher

router = APIRouter(prefix="/vf/listings", tags=["listings"])


@router.post("", response_model=dict)
async def create_listing(listing_data: dict):
    """
    Create a new listing (offer or need).

    Request body should contain:
    - listing_type: "offer" or "need"
    - resource_spec_id: ID of resource spec
    - agent_id: ID of agent creating listing
    - quantity, unit, location_id, etc.
    """
    try:
        # Generate ID if not provided
        if "id" not in listing_data:
            listing_data["id"] = f"listing:{uuid.uuid4()}"

        # Set timestamps
        listing_data["created_at"] = datetime.now().isoformat()

        # Handle field name mapping: "provider_agent_id" in request -> "agent_id" in model
        if "provider_agent_id" in listing_data:
            listing_data["agent_id"] = listing_data.pop("provider_agent_id")

        # Create Listing object
        listing = Listing.from_dict(listing_data)

        # Sign the listing
        # In production, get private key from authenticated user context
        # For now, generate a mock keypair
        keypair = SigningService.generate_keypair()
        signer = SigningService(keypair['private_key'])
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
async def update_listing(listing_id: str, updates: dict):
    """Update listing (e.g., mark as fulfilled)"""
    try:
        db = get_database()
        db.connect()
        listing_repo = ListingRepository(db.conn)

        listing = listing_repo.find_by_id(listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Apply updates
        if "status" in updates:
            listing.status = updates["status"]
        if "quantity" in updates:
            listing.quantity = updates["quantity"]
        if "description" in updates:
            listing.description = updates["description"]

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
