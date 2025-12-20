"""Rapid Response API

Endpoints for immediate danger coordination (ICE raids, detentions, threats).

CRITICAL:
- 2-tap trigger (POST /alerts/trigger)
- <30 second propagation
- High trust required (CRITICAL >= 0.7, URGENT >= 0.5)
- Auto-purge after 24 hours
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.rapid_response_service import RapidResponseService
from app.services.web_of_trust_service import WebOfTrustService
from app.database.vouch_repository import VouchRepository
from app.auth.middleware import get_current_user, require_admin_key, require_steward
from app.auth.models import User
from app.models.rapid_response import (
    AlertLevel,
    AlertType,
    ResponderStatus,
    ResponderRole,
)

router = APIRouter(prefix="/api/rapid-response", tags=["rapid-response"])


# ===== Request/Response Models =====

class TriggerAlertRequest(BaseModel):
    """Request to trigger a rapid alert (2-tap flow)."""
    alert_type: AlertType
    alert_level: AlertLevel
    cell_id: str
    location_hint: str = Field(..., description="General location (intersection, neighborhood)")
    description: str = Field(..., description="Brief description of situation")
    people_affected: Optional[int] = None
    include_coordinates: bool = Field(
        default=False,
        description="Include GPS coordinates? (OPSEC: only if safe)"
    )


class RespondToAlertRequest(BaseModel):
    """Request to respond to an alert."""
    alert_id: str
    status: ResponderStatus
    role: ResponderRole
    eta_minutes: Optional[int] = None
    notes: Optional[str] = Field(default=None, description="Brief notes (e.g., 'bringing camera')")


class PostUpdateRequest(BaseModel):
    """Request to post an alert update (coordinator)."""
    alert_id: str
    update_type: str = Field(..., description="status_change, escalation, de_escalation, info")
    message: str
    new_alert_level: Optional[AlertLevel] = None


class ResolveAlertRequest(BaseModel):
    """Request to resolve an alert (coordinator)."""
    alert_id: str
    resolution_notes: str


class UploadMediaRequest(BaseModel):
    """Request to upload encrypted media (photo/video/audio)."""
    alert_id: str
    media_type: str = Field(..., description="photo, video, audio, document")
    encrypted_data: str = Field(..., description="Base64 encoded encrypted data")
    file_size_bytes: int
    encrypted_metadata: Optional[str] = Field(
        default=None,
        description="Encrypted metadata (GPS, timestamp, device)"
    )


class CreateReviewRequest(BaseModel):
    """Request to create after-action review."""
    alert_id: str
    response_time_minutes: Optional[int] = None
    successes: str
    challenges: str
    lessons: str
    recommendations: str


# ===== Dependency Injection =====

def get_rapid_response_service() -> RapidResponseService:
    """Get rapid response service instance."""
    return RapidResponseService(db_path="data/solarpunk.db")


def get_trust_service() -> WebOfTrustService:
    """Get web of trust service instance."""
    vouch_repo = VouchRepository(db_path="data/solarpunk.db")
    return WebOfTrustService(vouch_repo=vouch_repo)


# ===== Alert Endpoints =====

@router.post("/alerts/trigger")
async def trigger_alert(
    request: TriggerAlertRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service),
    trust_service: WebOfTrustService = Depends(get_trust_service)
):
    """Trigger a rapid response alert (BIG RED BUTTON).

    This is the 2-tap flow:
    1. User taps "EMERGENCY" button
    2. User confirms alert type and level
    3. Alert propagates via high-priority DTN bundle

    Trust requirements:
    - CRITICAL: trust >= 0.7
    - URGENT: trust >= 0.5
    - WATCH: trust >= 0.3
    """
    # Get user's actual trust score from Web of Trust
    trust_score = trust_service.compute_trust_score(user_id)
    user_trust = trust_score.computed_trust

    # TODO: Get coordinates if requested
    coordinates = None
    if request.include_coordinates:
        # In production, get from device GPS
        coordinates = None

    try:
        alert = service.create_alert(
            user_id=user_id,
            cell_id=request.cell_id,
            alert_type=request.alert_type,
            alert_level=request.alert_level,
            location_hint=request.location_hint,
            description=request.description,
            people_affected=request.people_affected,
            coordinates=coordinates,
            user_trust_score=user_trust
        )

        return {
            "success": True,
            "alert_id": alert.id,
            "alert_level": alert.alert_level.value,
            "bundle_id": alert.bundle_id,
            "propagating": True,
            "confirmation_required": alert.alert_level == AlertLevel.CRITICAL,
            "auto_downgrade_at": alert.auto_downgrade_at.isoformat() if alert.auto_downgrade_at else None,
            "message": "Alert triggered. Propagating to nearby members via mesh."
        }

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/alerts/active/{cell_id}")
async def get_active_alerts(
    cell_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get all active alerts for a cell."""
    alerts = service.get_active_alerts(cell_id)

    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type.value,
                "alert_level": a.alert_level.value,
                "status": a.status.value,
                "location_hint": a.location_hint,
                "description": a.description,
                "people_affected": a.people_affected,
                "coordinator_id": a.coordinator_id,
                "confirmed": a.confirmed,
                "created_at": a.created_at.isoformat(),
                "expires_at": a.expires_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.get("/alerts/{alert_id}")
async def get_alert_detail(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get full details for an alert (including responders and timeline)."""
    alert = service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    responders = service.get_alert_responders(alert_id)
    timeline = service.get_alert_timeline(alert_id)

    return {
        "alert": {
            "id": alert.id,
            "alert_type": alert.alert_type.value,
            "alert_level": alert.alert_level.value,
            "status": alert.status.value,
            "reported_by": alert.reported_by,
            "cell_id": alert.cell_id,
            "location_hint": alert.location_hint,
            "description": alert.description,
            "people_affected": alert.people_affected,
            "coordinator_id": alert.coordinator_id,
            "coordinator_claimed_at": alert.coordinator_claimed_at.isoformat() if alert.coordinator_claimed_at else None,
            "confirmed": alert.confirmed,
            "confirmed_by": alert.confirmed_by,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "resolution_notes": alert.resolution_notes,
            "created_at": alert.created_at.isoformat(),
            "expires_at": alert.expires_at.isoformat()
        },
        "responders": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "status": r.status.value,
                "role": r.role.value,
                "eta_minutes": r.eta_minutes,
                "notes": r.notes,
                "responded_at": r.responded_at.isoformat(),
                "arrived_at": r.arrived_at.isoformat() if r.arrived_at else None
            }
            for r in responders
        ],
        "timeline": [
            {
                "id": u.id,
                "posted_by": u.posted_by,
                "update_type": u.update_type,
                "message": u.message,
                "new_alert_level": u.new_alert_level.value if u.new_alert_level else None,
                "posted_at": u.posted_at.isoformat()
            }
            for u in timeline
        ]
    }


@router.post("/alerts/{alert_id}/confirm")
async def confirm_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Confirm an alert (prevents auto-downgrade for CRITICAL alerts)."""
    try:
        alert = service.confirm_alert(alert_id, user_id)

        return {
            "success": True,
            "alert_id": alert.id,
            "confirmed": alert.confirmed,
            "confirmed_by": alert.confirmed_by,
            "message": "Alert confirmed. Auto-downgrade cancelled."
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/claim-coordinator")
async def claim_coordinator(
    alert_id: str,
    user: User = Depends(require_steward),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Claim coordinator role for an alert (stewards only, first come first serve).

    GAP-134: Steward verification via trust score >= 0.9
    """
    try:
        alert = service.claim_coordinator(alert_id, user.id)

        return {
            "success": True,
            "alert_id": alert.id,
            "coordinator_id": alert.coordinator_id,
            "message": "You are now coordinating this response."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/resolve")
async def resolve_alert(
    request: ResolveAlertRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Resolve an alert (coordinator only)."""
    try:
        alert = service.resolve_alert(
            alert_id=request.alert_id,
            coordinator_id=user_id,
            resolution_notes=request.resolution_notes
        )

        return {
            "success": True,
            "alert_id": alert.id,
            "status": alert.status.value,
            "resolved_at": alert.resolved_at.isoformat(),
            "purge_at": alert.purge_at.isoformat() if alert.purge_at else None,
            "message": "Alert resolved. All Clear broadcast sent. Data will be purged in 24 hours."
        }

    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ===== Responder Endpoints =====

@router.post("/responders/respond")
async def respond_to_alert(
    request: RespondToAlertRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Indicate response to an alert."""
    responder = service.add_responder(
        alert_id=request.alert_id,
        user_id=user_id,
        status=request.status,
        role=request.role,
        eta_minutes=request.eta_minutes,
        notes=request.notes
    )

    return {
        "success": True,
        "responder_id": responder.id,
        "status": responder.status.value,
        "role": responder.role.value,
        "message": f"Response recorded: {responder.status.value} as {responder.role.value}"
    }


@router.get("/responders/{alert_id}")
async def get_responders(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get all responders for an alert."""
    responders = service.get_alert_responders(alert_id)

    return {
        "alert_id": alert_id,
        "total_responders": len(responders),
        "responders": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "status": r.status.value,
                "role": r.role.value,
                "eta_minutes": r.eta_minutes,
                "notes": r.notes,
                "responded_at": r.responded_at.isoformat(),
                "arrived_at": r.arrived_at.isoformat() if r.arrived_at else None
            }
            for r in responders
        ]
    }


# ===== Update Endpoints =====

@router.post("/updates/post")
async def post_update(
    request: PostUpdateRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Post a status update (usually coordinator)."""
    update = service.add_update(
        alert_id=request.alert_id,
        posted_by=user_id,
        update_type=request.update_type,
        message=request.message,
        new_alert_level=request.new_alert_level
    )

    return {
        "success": True,
        "update_id": update.id,
        "bundle_id": update.bundle_id,
        "message": "Update posted and propagating via mesh."
    }


@router.get("/updates/{alert_id}")
async def get_alert_timeline(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get chronological timeline of updates for an alert."""
    updates = service.get_alert_timeline(alert_id)

    return {
        "alert_id": alert_id,
        "updates": [
            {
                "id": u.id,
                "posted_by": u.posted_by,
                "update_type": u.update_type,
                "message": u.message,
                "new_alert_level": u.new_alert_level.value if u.new_alert_level else None,
                "posted_at": u.posted_at.isoformat()
            }
            for u in updates
        ]
    }


# ===== Media Endpoints =====

@router.post("/media/upload")
async def upload_media(
    request: UploadMediaRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Upload encrypted media documentation."""
    media = service.add_media(
        alert_id=request.alert_id,
        captured_by=user_id,
        media_type=request.media_type,
        encrypted_data=request.encrypted_data,
        file_size_bytes=request.file_size_bytes,
        encrypted_metadata=request.encrypted_metadata
    )

    return {
        "success": True,
        "media_id": media.id,
        "storage_bundle_id": media.storage_bundle_id,
        "purge_at": media.purge_at.isoformat(),
        "message": "Media encrypted and stored in distributed mesh. Will be purged in 24 hours after alert resolution."
    }


@router.get("/media/{alert_id}")
async def get_alert_media(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get all media for an alert."""
    media_list = service.get_alert_media(alert_id)

    return {
        "alert_id": alert_id,
        "media": [
            {
                "id": m.id,
                "media_type": m.media_type,
                "file_size_bytes": m.file_size_bytes,
                "storage_bundle_id": m.storage_bundle_id,
                "shared_with_legal": m.shared_with_legal,
                "shared_with_media": m.shared_with_media,
                "captured_at": m.captured_at.isoformat(),
                "purge_at": m.purge_at.isoformat()
            }
            for m in media_list
        ]
    }


# ===== After Action Review Endpoints =====

@router.post("/reviews/create")
async def create_review(
    request: CreateReviewRequest,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Create an after-action review (coordinator)."""
    # Get responder count
    responders = service.get_alert_responders(request.alert_id)
    total_responders = len(responders)

    review = service.create_review(
        alert_id=request.alert_id,
        completed_by=user_id,
        total_responders=total_responders,
        response_time_minutes=request.response_time_minutes,
        successes=request.successes,
        challenges=request.challenges,
        lessons=request.lessons,
        recommendations=request.recommendations
    )

    return {
        "success": True,
        "review_id": review.id,
        "message": "After-action review created."
    }


@router.get("/reviews/{alert_id}")
async def get_review(
    alert_id: str,
    user_id: str = Depends(get_current_user),
    service: RapidResponseService = Depends(get_rapid_response_service)
):
    """Get after-action review for an alert."""
    review = service.get_review(alert_id)

    if not review:
        raise HTTPException(status_code=404, detail="No review found for this alert")

    return {
        "review": {
            "id": review.id,
            "alert_id": review.alert_id,
            "completed_by": review.completed_by,
            "response_time_minutes": review.response_time_minutes,
            "total_responders": review.total_responders,
            "successes": review.successes,
            "challenges": review.challenges,
            "lessons": review.lessons,
            "recommendations": review.recommendations,
            "completed_at": review.completed_at.isoformat()
        }
    }


# ===== Admin/Background Worker Endpoints =====

@router.post("/admin/auto-purge")
async def run_auto_purge(
    service: RapidResponseService = Depends(get_rapid_response_service),
    auth: None = Depends(require_admin_key)
):
    """Run auto-purge of old alerts (background worker only).

    Requires X-Admin-Key header matching ADMIN_API_KEY environment variable.
    """
    result = service.run_auto_purge()

    return {
        "success": True,
        "purged": result,
        "message": f"Purged {result['alerts_purged']} alerts and {result['media_purged']} media items."
    }


@router.post("/admin/process-downgrades")
async def process_auto_downgrades(
    service: RapidResponseService = Depends(get_rapid_response_service),
    auth: None = Depends(require_admin_key)
):
    """Process auto-downgrades for unconfirmed CRITICAL alerts (background worker only).

    Requires X-Admin-Key header matching ADMIN_API_KEY environment variable.
    """
    downgraded = service.process_auto_downgrades()

    return {
        "success": True,
        "downgraded_count": len(downgraded),
        "downgraded_alerts": [a.id for a in downgraded],
        "message": f"Auto-downgraded {len(downgraded)} unconfirmed CRITICAL alerts to WATCH."
    }
