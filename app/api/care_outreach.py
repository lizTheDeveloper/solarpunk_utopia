"""Care Outreach API - Saboteur Conversion Through Care

API endpoints for managing care-based outreach to struggling members.

Routes:
- POST /api/care/volunteers - Register as care volunteer
- GET /api/care/volunteers/available - Get available volunteers
- POST /api/care/flag - Flag user for outreach
- GET /api/care/assignments/active - Get active assignments
- GET /api/care/assignments/{user_id} - Get assignment for user
- POST /api/care/notes - Add note to assignment
- POST /api/care/convert - Mark someone as converted
- POST /api/care/assess - Assess needs
- GET /api/care/access/{user_id} - Get access level for user
- GET /api/care/metrics - Get conversion metrics
- GET /api/care/experiences - Get conversion experiences
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database.care_outreach_repository import CareOutreachRepository
from app.services.care_outreach_service import CareOutreachService
from app.services.web_of_trust_service import WebOfTrustService
from app.database.vouch_repository import VouchRepository
from app.models.care_outreach import (
    AccessLevel,
    DetectionReason,
    OutreachStatus,
)


router = APIRouter(prefix="/api/care", tags=["care_outreach"])


# --- Request/Response Models ---

class RegisterVolunteerRequest(BaseModel):
    user_id: str
    name: str
    training: List[str]
    supervision_partner_id: str
    max_capacity: int = 3


class FlagForOutreachRequest(BaseModel):
    user_id: str
    reason: str  # DetectionReason value
    details: Optional[str] = None


class AddNoteRequest(BaseModel):
    assignment_id: str
    volunteer_id: str
    note: str
    needs_identified: Optional[List[str]] = None
    resources_connected: Optional[List[str]] = None
    sentiment: Optional[str] = None


class MarkConvertedRequest(BaseModel):
    assignment_id: str
    conversion_story: Optional[str] = None


class AssessNeedsRequest(BaseModel):
    user_id: str
    volunteer_id: str
    housing_insecure: bool = False
    food_insecure: bool = False
    employment_unstable: bool = False
    healthcare_access: bool = False
    isolated: bool = False
    past_trauma_with_orgs: bool = False
    trust_issues: bool = False
    being_paid_to_sabotage: Optional[str] = None
    law_enforcement: Optional[str] = None


# --- Dependency Injection ---

def get_care_service() -> CareOutreachService:
    """Dependency injection for CareOutreachService"""
    from app.database import get_db_connection

    conn = get_db_connection()
    outreach_repo = CareOutreachRepository(conn)
    vouch_repo = VouchRepository(conn)
    trust_service = WebOfTrustService(vouch_repo)

    return CareOutreachService(outreach_repo, trust_service)


# --- Endpoints ---

@router.post("/volunteers")
def register_volunteer(
    request: RegisterVolunteerRequest,
    service: CareOutreachService = Depends(get_care_service)
):
    """Register as a care volunteer

    You cannot care for someone through a bot. This requires real humans.
    """
    volunteer = service.register_volunteer(
        user_id=request.user_id,
        name=request.name,
        training=request.training,
        supervision_partner_id=request.supervision_partner_id,
        max_capacity=request.max_capacity,
    )

    return {
        "success": True,
        "volunteer": {
            "user_id": volunteer.user_id,
            "name": volunteer.name,
            "training": volunteer.training,
            "max_capacity": volunteer.max_capacity,
            "joined_at": volunteer.joined_at.isoformat(),
        }
    }


@router.get("/volunteers/available")
def get_available_volunteers(
    service: CareOutreachService = Depends(get_care_service)
):
    """Get volunteers who have capacity"""
    volunteers = service.outreach_repo.get_available_volunteers()

    return {
        "volunteers": [
            {
                "user_id": v.user_id,
                "name": v.name,
                "training": v.training,
                "currently_supporting": v.currently_supporting,
                "max_capacity": v.max_capacity,
                "has_capacity": v.has_capacity,
            }
            for v in volunteers
        ]
    }


@router.post("/flag")
def flag_for_outreach(
    request: FlagForOutreachRequest,
    service: CareOutreachService = Depends(get_care_service)
):
    """Flag a user for care outreach

    Detection is not condemnation. It's an invitation to care.
    """
    try:
        reason = DetectionReason(request.reason)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid detection reason. Must be one of: {[r.value for r in DetectionReason]}"
        )

    assignment = service.flag_for_outreach(
        user_id=request.user_id,
        reason=reason,
        details=request.details,
    )

    return {
        "success": True,
        "assignment": {
            "id": assignment.id,
            "flagged_user_id": assignment.flagged_user_id,
            "volunteer_id": assignment.outreach_volunteer_id,
            "detection_reason": assignment.detection_reason.value,
            "status": assignment.status.value,
            "started_at": assignment.started_at.isoformat(),
        }
    }


@router.get("/assignments/active")
def get_active_assignments(
    service: CareOutreachService = Depends(get_care_service)
):
    """Get all active outreach assignments"""
    assignments = service.outreach_repo.get_active_assignments()

    return {
        "assignments": [
            {
                "id": a.id,
                "flagged_user_id": a.flagged_user_id,
                "volunteer_id": a.outreach_volunteer_id,
                "detection_reason": a.detection_reason.value,
                "status": a.status.value,
                "started_at": a.started_at.isoformat(),
                "duration_days": a.duration_days,
            }
            for a in assignments
        ]
    }


@router.get("/assignments/{user_id}")
def get_assignment_for_user(
    user_id: str,
    service: CareOutreachService = Depends(get_care_service)
):
    """Get outreach assignment for a user"""
    assignment = service.outreach_repo.get_assignment_for_user(user_id)

    if not assignment:
        return {"assignment": None}

    return {
        "assignment": {
            "id": assignment.id,
            "flagged_user_id": assignment.flagged_user_id,
            "volunteer_id": assignment.outreach_volunteer_id,
            "detection_reason": assignment.detection_reason.value,
            "status": assignment.status.value,
            "started_at": assignment.started_at.isoformat(),
            "duration_days": assignment.duration_days,
            "notes_count": len(assignment.notes) if assignment.notes else 0,
        }
    }


@router.post("/notes")
def add_outreach_note(
    request: AddNoteRequest,
    service: CareOutreachService = Depends(get_care_service)
):
    """Add a note to an outreach assignment

    Private notes for continuity. Not shared with the flagged person.
    """
    note = service.add_outreach_note(
        assignment_id=request.assignment_id,
        volunteer_id=request.volunteer_id,
        note_text=request.note,
        needs_identified=request.needs_identified,
        resources_connected=request.resources_connected,
        sentiment=request.sentiment,
    )

    return {
        "success": True,
        "note": {
            "id": note.id,
            "assignment_id": note.assignment_id,
            "timestamp": note.timestamp.isoformat(),
            "sentiment": note.sentiment,
        }
    }


@router.post("/convert")
def mark_converted(
    request: MarkConvertedRequest,
    service: CareOutreachService = Depends(get_care_service)
):
    """Mark someone as having converted / come around

    They were flagged. Now they're a builder.
    """
    service.mark_converted(
        assignment_id=request.assignment_id,
        conversion_story=request.conversion_story,
    )

    return {
        "success": True,
        "message": "Conversion recorded. Welcome them fully."
    }


@router.post("/chose-to-leave")
def mark_chose_to_leave(
    assignment_id: str,
    service: CareOutreachService = Depends(get_care_service)
):
    """Mark someone as having chosen to leave

    They left on their own terms. Door is always open.
    """
    service.mark_chose_to_leave(assignment_id)

    return {
        "success": True,
        "message": "Marked as chose to leave. Door always open."
    }


@router.post("/assess")
def assess_needs(
    request: AssessNeedsRequest,
    service: CareOutreachService = Depends(get_care_service)
):
    """Assess needs and connect to resources

    Figure out what they need and connect them WITHOUT requiring "good behavior"
    """
    assessment = service.assess_and_provide(
        user_id=request.user_id,
        volunteer_id=request.volunteer_id,
        housing_insecure=request.housing_insecure,
        food_insecure=request.food_insecure,
        employment_unstable=request.employment_unstable,
        healthcare_access=request.healthcare_access,
        isolated=request.isolated,
        past_trauma_with_orgs=request.past_trauma_with_orgs,
        trust_issues=request.trust_issues,
        being_paid_to_sabotage=request.being_paid_to_sabotage,
        law_enforcement=request.law_enforcement,
    )

    return {
        "success": True,
        "assessment": {
            "user_id": assessment.user_id,
            "assessed_at": assessment.assessed_at.isoformat(),
            "housing_insecure": assessment.housing_insecure,
            "food_insecure": assessment.food_insecure,
            "employment_unstable": assessment.employment_unstable,
            "isolated": assessment.isolated,
        }
    }


@router.get("/access/{user_id}")
def get_access_level(
    user_id: str,
    service: CareOutreachService = Depends(get_care_service)
):
    """Get access level for a user

    Access based on trust, but never zero.
    """
    access_level = service.determine_access_level(user_id)
    permissions = service.get_access_permissions(access_level)

    return {
        "user_id": user_id,
        "access_level": access_level.value,
        "permissions": permissions,
        "message": "Even at MINIMAL_BUT_HUMAN: can still receive help, attend events, be treated with dignity"
    }


@router.get("/metrics")
def get_conversion_metrics(
    service: CareOutreachService = Depends(get_care_service)
):
    """Get conversion metrics

    How are we doing at caring for everyone?
    """
    metrics = service.get_metrics()

    return {
        "outreach_active": metrics.outreach_active,
        "converted_this_month": metrics.converted_this_month,
        "chose_to_leave": metrics.chose_to_leave,
        "still_trying": metrics.still_trying,
        "average_time_to_first_real_conversation": metrics.average_time_to_first_real_conversation,
        "conversion_stories_count": len(metrics.conversion_stories),
        "message": "The metric we care about most: How quickly do people feel safe enough to be real with us?"
    }


@router.get("/experiences")
def get_conversion_experiences(
    user_id: Optional[str] = None,
    service: CareOutreachService = Depends(get_care_service)
):
    """Get conversion experiences

    Not lectures. Not pamphlets. Experience.
    Let them feel it, not hear about it.
    """
    if user_id:
        suggested = service.suggest_experience(user_id)
        return {
            "suggested_experience": suggested,
            "all_experiences": service.get_all_experiences(),
        }

    return {
        "experiences": service.get_all_experiences(),
        "message": "The point is: let them feel it, not hear about it."
    }


@router.post("/infiltrator")
def handle_suspected_infiltrator(
    user_id: str,
    service: CareOutreachService = Depends(get_care_service)
):
    """Handle suspected law enforcement / paid informant

    They might be a cop. But they're also a person.

    Process:
    1. Protect the network (limit access)
    2. Reach out anyway
    3. Message: "We know. We're not angry. If you ever want out, we'll help you."
    """
    assignment = service.handle_suspected_infiltrator(user_id)

    return {
        "success": True,
        "assignment_id": assignment.id,
        "message": "Network protected. Outreach volunteer assigned. Some cops have turned. The door is open."
    }
