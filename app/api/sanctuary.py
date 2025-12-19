"""Sanctuary Network API

OPSEC-critical endpoints for underground railroad coordination.

CRITICAL:
- High trust required (>0.8 for HIGH sensitivity)
- Steward verification mandatory
- Auto-purge after 24 hours
- No permanent records of who helped whom
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.sanctuary_service import SanctuaryService
from app.models.sanctuary import SanctuaryResourceType
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/api/sanctuary", tags=["sanctuary"])


# ===== Request/Response Models =====

class OfferResourceRequest(BaseModel):
    """Request to offer a sanctuary resource."""
    resource_type: SanctuaryResourceType
    cell_id: str
    description: str = Field(..., description="Brief description (use code words)")
    capacity: Optional[int] = None
    duration_days: Optional[int] = None


class CreateRequestRequest(BaseModel):
    """Request to create sanctuary request (steward-only)."""
    request_type: SanctuaryResourceType
    cell_id: str
    urgency: str = Field(..., description="critical, urgent, or soon")
    description: str
    people_count: int = 1
    duration_needed_days: Optional[int] = None
    location_hint: Optional[str] = None


class CreateAlertRequest(BaseModel):
    """Request to create rapid alert."""
    alert_type: str = Field(..., description="ice_raid, checkpoint, detention, threat")
    severity: str = Field(..., description="critical, high, medium")
    cell_id: str
    location_hint: str
    description: str
    people_affected: Optional[int] = None


# ===== Dependency Injection =====

def get_sanctuary_service() -> SanctuaryService:
    """Get sanctuary service instance."""
    return SanctuaryService(db_path="data/solarpunk.db")


# ===== Sanctuary Resource Endpoints =====

@router.post("/resources/offer")
async def offer_resource(
    request: OfferResourceRequest,
    user_id: str = Depends(get_current_user),
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Offer a sanctuary resource.

    High-sensitivity resources (safe space, transport, intel) require
    steward verification before becoming available.
    """
    resource = service.offer_resource(
        user_id=user_id,
        cell_id=request.cell_id,
        resource_type=request.resource_type,
        description=request.description,
        capacity=request.capacity,
        duration_days=request.duration_days
    )

    return {
        "success": True,
        "resource_id": resource.id,
        "verification_required": resource.verification_status.value == "pending",
        "message": "Resource offered. Steward verification required." if resource.verification_status.value == "pending" else "Resource available."
    }


@router.get("/resources/available/{cell_id}")
async def get_available_resources(
    cell_id: str,
    user_id: str = Depends(get_current_user),
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Get available sanctuary resources for a cell.

    Filtered by user's trust level:
    - HIGH sensitivity requires >0.8 trust
    - MEDIUM sensitivity requires >0.6 trust
    """
    # TODO: Get user's actual trust score from trust service
    user_trust = 0.9  # Placeholder

    resources = service.get_available_resources(cell_id, user_trust)

    return {
        "resources": [
            {
                "id": r.id,
                "resource_type": r.resource_type.value,
                "description": r.description,
                "capacity": r.capacity,
                "duration_days": r.duration_days,
                "verification_status": r.verification_status.value
            }
            for r in resources
        ]
    }


# ===== Sanctuary Request Endpoints =====

@router.post("/requests/create")
async def create_sanctuary_request(
    request: CreateRequestRequest,
    user_id: str = Depends(get_current_user),
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Create a sanctuary request (steward-verified only).

    This creates an urgent need for sanctuary resources.
    Only stewards can create these requests.
    """
    # TODO: Verify user is steward

    sanctuary_request = service.create_request(
        user_id=user_id,
        cell_id=request.cell_id,
        steward_id=user_id,  # TODO: Get actual steward ID
        request_type=request.request_type,
        urgency=request.urgency,
        description=request.description,
        people_count=request.people_count,
        duration_needed_days=request.duration_needed_days,
        location_hint=request.location_hint
    )

    return {
        "success": True,
        "request_id": sanctuary_request.id,
        "urgency": sanctuary_request.urgency,
        "expires_at": sanctuary_request.expires_at.isoformat()
    }


# ===== Rapid Alert Endpoints =====

@router.post("/alerts/create")
async def create_rapid_alert(
    request: CreateAlertRequest,
    user_id: str = Depends(get_current_user),
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Create a rapid alert for immediate danger.

    Broadcasts to nearby high-trust members immediately.
    """
    alert = service.create_rapid_alert(
        user_id=user_id,
        cell_id=request.cell_id,
        alert_type=request.alert_type,
        severity=request.severity,
        location_hint=request.location_hint,
        description=request.description,
        people_affected=request.people_affected
    )

    return {
        "success": True,
        "alert_id": alert.id,
        "severity": alert.severity,
        "expires_at": alert.expires_at.isoformat()
    }


@router.get("/alerts/active/{cell_id}")
async def get_active_alerts(
    cell_id: str,
    user_id: str = Depends(get_current_user),
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Get active rapid alerts for a cell."""
    alerts = service.get_active_alerts(cell_id)

    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "location_hint": a.location_hint,
                "description": a.description,
                "people_affected": a.people_affected,
                "created_at": a.created_at.isoformat(),
                "expires_at": a.expires_at.isoformat()
            }
            for a in alerts
        ]
    }


# ===== Auto-Purge Endpoint (Background Worker) =====

@router.post("/admin/purge")
async def run_auto_purge(
    service: SanctuaryService = Depends(get_sanctuary_service)
):
    """Run auto-purge of old sanctuary records.

    Should be called by background worker every hour.
    """
    # TODO: Add authentication - this should only be callable by background worker

    result = service.run_auto_purge()

    return {
        "success": True,
        "purged": result
    }
