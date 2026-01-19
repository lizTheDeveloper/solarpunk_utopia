"""Commitments API Endpoints - GAP-69"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional, List
import uuid

from ...models.vf.commitment import Commitment, CommitmentStatus
from ...models.requests.vf_objects import CommitmentCreate, CommitmentUpdate
from ...database import get_database
from ...repositories.vf.commitment_repo import CommitmentRepository
from ...services.vf_bundle_publisher import VFBundlePublisher
from ...auth.middleware import require_auth
from ...auth.models import User

router = APIRouter(prefix="/vf/commitments", tags=["commitments"])


@router.get("/", response_model=dict)
async def get_commitments(agent_id: str = None, status: str = None):
    """Get all commitments, optionally filtered by agent or status"""
    try:
        db = get_database()
        db.connect()
        commitment_repo = CommitmentRepository(db.conn)

        if agent_id:
            # Filter by agent
            status_enum = CommitmentStatus(status) if status else None
            commitments = commitment_repo.find_by_agent(agent_id, status_enum)
        else:
            # Get all commitments
            commitments = commitment_repo.find_all()
            # Filter by status if provided
            if status:
                commitments = [c for c in commitments if c.status.value == status]

        db.close()

        return {
            "commitments": [c.to_dict() for c in commitments],
            "count": len(commitments)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{commitment_id}", response_model=dict)
async def get_commitment(commitment_id: str):
    """Get a specific commitment"""
    try:
        db = get_database()
        db.connect()
        commitment_repo = CommitmentRepository(db.conn)

        commitment = commitment_repo.find_by_id(commitment_id)
        db.close()

        if not commitment:
            raise HTTPException(status_code=404, detail="Commitment not found")

        return commitment.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/", response_model=dict)
async def create_commitment(commitment_data: CommitmentCreate):
    """
    Create a new commitment.

    GAP-43: Now uses Pydantic validation model.

    Validates:
    - Required fields present
    - Field types correct
    - Numeric ranges valid
    - String lengths reasonable
    """
    try:
        # Convert validated Pydantic model to dict
        data = commitment_data.model_dump()

        data["id"] = f"commitment:{uuid.uuid4()}"
        data["created_at"] = datetime.now().isoformat()

        commitment = Commitment.from_dict(data)

        db = get_database()
        db.connect()
        commitment_repo = CommitmentRepository(db.conn)
        created_commitment = commitment_repo.create(commitment)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(created_commitment, "Commitment")

        db.close()

        return {
            "status": "created",
            "commitment": created_commitment.to_dict(),
            "bundle_id": bundle["bundleId"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{commitment_id}", response_model=dict)
async def update_commitment(commitment_id: str, updates: CommitmentUpdate):
    """
    Update a commitment's status.

    GAP-43: Now uses Pydantic validation model.
    """
    try:
        db = get_database()
        db.connect()
        commitment_repo = CommitmentRepository(db.conn)

        commitment = commitment_repo.find_by_id(commitment_id)
        if not commitment:
            raise HTTPException(status_code=404, detail="Commitment not found")

        # Convert validated Pydantic model to dict
        update_dict = updates.model_dump(exclude_unset=True)

        # Update fields from validated model
        for key, value in update_dict.items():
            if hasattr(commitment, key):
                setattr(commitment, key, value)

        updated_commitment = commitment_repo.update(commitment)

        publisher = VFBundlePublisher()
        bundle = publisher.publish_vf_object(updated_commitment, "Commitment")

        db.close()

        return {
            "status": "updated",
            "commitment": updated_commitment.to_dict(),
            "bundle_id": bundle["bundleId"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{commitment_id}", response_model=dict)
async def delete_commitment(
    commitment_id: str,
    current_user: User = Depends(require_auth)
):
    """
    Delete a commitment (provider or receiver only).

    Only the provider or receiver of a commitment can delete it.

    Args:
        commitment_id: ID of the commitment to delete
        current_user: Authenticated user

    Returns:
        Status message

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not authorized (not provider or receiver)
        HTTPException 404: If commitment not found
    """
    try:
        db = get_database()
        db.connect()
        commitment_repo = CommitmentRepository(db.conn)

        commitment = commitment_repo.find_by_id(commitment_id)
        if not commitment:
            db.close()
            raise HTTPException(status_code=404, detail="Commitment not found")

        # Check authorization - only provider or receiver can delete
        is_provider = commitment.provider == current_user.id
        is_receiver = commitment.receiver == current_user.id

        if not is_provider and not is_receiver:
            db.close()
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this commitment. Only the provider or receiver can delete commitments."
            )

        commitment_repo.delete(commitment_id)
        db.close()

        return {
            "status": "deleted",
            "commitment_id": commitment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
