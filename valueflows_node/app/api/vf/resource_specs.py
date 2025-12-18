"""
Resource Specs API Endpoints

POST /vf/resource_specs - Create resource spec
GET /vf/resource_specs - List resource specs
GET /vf/resource_specs/{id} - Get resource spec
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import uuid

from ...models.vf.resource_spec import ResourceSpec, ResourceCategory
from ...database import get_database
from ...repositories.vf.resource_spec_repo import ResourceSpecRepository
from ...services.signing_service import SigningService

router = APIRouter(prefix="/vf/resource_specs", tags=["resource_specs"])


@router.post("", response_model=dict)
async def create_resource_spec(spec_data: dict):
    """
    Create a new resource specification.

    Request body should contain:
    - name: Resource spec name (e.g., "Tomatoes")
    - category: Resource category (e.g., "food", "tools", "skills")
    - unit (optional): Default unit of measure (e.g., "lbs", "hours", "items")
    - description (optional): Description of resource spec
    - subcategory (optional): Subcategory (e.g., "Vegetables")
    - image_url (optional): URL to image
    """
    try:
        # Generate ID if not provided
        if "id" not in spec_data:
            spec_data["id"] = f"resource_spec:{uuid.uuid4()}"

        # Set timestamps
        spec_data["created_at"] = datetime.now().isoformat()

        # Handle field name mapping: "unit" in request -> "default_unit" in model
        if "unit" in spec_data:
            spec_data["default_unit"] = spec_data.pop("unit")

        # Create ResourceSpec object
        spec = ResourceSpec.from_dict(spec_data)

        # Sign the resource spec
        # In production, get private key from authenticated user context
        # For now, generate a mock keypair
        keypair = SigningService.generate_keypair()
        signer = SigningService(keypair['private_key'])
        signer.sign_and_update(spec, spec.id)

        # Save to database
        db = get_database()
        db.connect()
        spec_repo = ResourceSpecRepository(db.conn)
        created_spec = spec_repo.create(spec)
        db.close()

        return created_spec.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=dict)
async def list_resource_specs(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, description="Maximum results")
):
    """
    List resource specs with filters.

    Query parameters:
    - category: Filter by category (e.g., "food", "tools", "skills")
    - limit: Maximum results
    """
    try:
        db = get_database()
        db.connect()
        spec_repo = ResourceSpecRepository(db.conn)

        # Apply filters
        if category:
            category_enum = ResourceCategory(category)
            specs = spec_repo.find_by_category(category_enum)
        else:
            specs = spec_repo.find_all(limit=limit)

        db.close()

        return {
            "resource_specs": [s.to_dict() for s in specs],
            "count": len(specs)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{spec_id}", response_model=dict)
async def get_resource_spec(spec_id: str):
    """Get resource spec by ID"""
    try:
        db = get_database()
        db.connect()
        spec_repo = ResourceSpecRepository(db.conn)
        spec = spec_repo.find_by_id(spec_id)
        db.close()

        if not spec:
            raise HTTPException(status_code=404, detail="Resource spec not found")

        return spec.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
