"""Fork Rights API - GAP-65

Data portability and community forking endpoints.
"Freedom without socialism is privilege, injustice;
socialism without freedom is slavery and brutality." - Bakunin
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.services.fork_rights_service import ForkRightsService
from app.models.fork_rights import (
    DataExportRequest,
    DataExport,
    ConnectionExportConsent,
    CommunityFork,
    ForkInvitation
)

router = APIRouter(prefix="/api/fork-rights", tags=["fork-rights"])


# ===== Request/Response Models =====

class ExportDataRequest(BaseModel):
    """Request to export user data."""
    export_type: str = Field(
        ...,
        description="Export type: data_only, with_connections, or fork"
    )


class ConnectionConsentResponse(BaseModel):
    """Response to a connection export consent request."""
    consent_id: str
    allow: bool = Field(..., description="True to allow, False to deny")


class ForkCommunityRequest(BaseModel):
    """Request to fork a community."""
    original_cell_id: str
    new_cell_name: str
    fork_reason: Optional[str] = None
    members_to_invite: List[str] = Field(default_factory=list)


class ForkInvitationResponse(BaseModel):
    """Response to a fork invitation."""
    invitation_id: str
    accept: bool = Field(..., description="True to accept, False to decline")


class LeaveCommunityRequest(BaseModel):
    """Request to leave a community."""
    cell_id: str


# ===== Endpoints =====

@router.post("/export-data")
async def request_data_export(
    request: ExportDataRequest,
    user_id: str  # TODO: Get from auth middleware
):
    """Request a data export.

    **Privacy guarantee:** Your data belongs to you. Always exportable.
    No permission needed from community.

    Supports three export types:
    - data_only: Just your data
    - with_connections: Data + connections (requires consent)
    - fork: Full fork with community creation

    Returns export request. Export will be generated asynchronously.
    Check status with GET /export-data/status
    """
    try:
        service = ForkRightsService()
        export_request = service.request_data_export(
            user_id=user_id,
            export_type=request.export_type
        )

        return {
            "status": "success",
            "message": "Export request created",
            "export_request": export_request.dict(),
            "note": "Export will be generated. Check /export-data/status for completion."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export request failed: {str(e)}")


@router.get("/export-data/status")
async def get_export_status(
    user_id: str  # TODO: Get from auth middleware
):
    """Get status of most recent data export request."""
    try:
        service = ForkRightsService()
        export_request = service.repo.get_export_request(user_id)

        if not export_request:
            return {
                "status": "no_export",
                "message": "No export request found"
            }

        return {
            "status": "success",
            "export_request": export_request.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get export status: {str(e)}")


@router.get("/export-data/download")
async def download_export(
    user_id: str  # TODO: Get from auth middleware
):
    """Download completed export file.

    Returns local file path (no cloud storage - local-first).
    """
    try:
        service = ForkRightsService()
        export_request = service.repo.get_export_request(user_id)

        if not export_request:
            raise HTTPException(status_code=404, detail="No export request found")

        if export_request.status != "complete":
            raise HTTPException(
                status_code=400,
                detail=f"Export not ready. Status: {export_request.status}"
            )

        return {
            "status": "success",
            "export_url": export_request.export_url,
            "note": "Export is stored locally. Transfer via mesh or local file share."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/export-data/generate")
async def generate_export_now(
    user_id: str  # TODO: Get from auth middleware
):
    """Generate data export immediately (synchronous).

    For testing or when you want export right now.
    For production, use async request + polling instead.
    """
    try:
        service = ForkRightsService()

        # Create request
        request = service.request_data_export(
            user_id=user_id,
            export_type="data_only"
        )

        # Generate export file
        export_path = service.generate_export_file(user_id)

        # Update request status
        service.repo.update_export_status(
            user_id=user_id,
            requested_at=request.requested_at,
            status="complete",
            export_url=export_path
        )

        return {
            "status": "success",
            "message": "Export generated",
            "export_path": export_path,
            "note": "SQLite database with all your data. Works offline."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


# Connection Export Consent
@router.get("/connection-consents/pending")
async def get_pending_consents(
    user_id: str  # TODO: Get from auth middleware
):
    """Get pending connection export consent requests.

    Someone is leaving and wants to take your connection info.
    You can allow or deny.
    """
    try:
        service = ForkRightsService()
        consents = service.get_pending_consents(user_id)

        return {
            "status": "success",
            "pending_consents": [c.dict() for c in consents],
            "count": len(consents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consents: {str(e)}")


@router.post("/connection-consents/respond")
async def respond_to_consent(
    response: ConnectionConsentResponse,
    user_id: str  # TODO: Get from auth middleware
):
    """Respond to a connection export consent request.

    allow=True: They can take your contact info
    allow=False: They get just their side of the relationship
    """
    try:
        service = ForkRightsService()
        service.respond_to_connection_consent(
            consent_id=response.consent_id,
            response="allow" if response.allow else "deny"
        )

        return {
            "status": "success",
            "message": f"Consent {'granted' if response.allow else 'denied'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consent response failed: {str(e)}")


# Community Forking
@router.post("/fork-community")
async def fork_community(
    request: ForkCommunityRequest,
    user_id: str  # TODO: Get from auth middleware
):
    """Fork a community.

    Creates new cell with you as steward.
    Invites members you choose.
    Original cell continues unchanged.

    **Bakunin:** "The liberty of man consists solely in this,
    that he obeys the laws of nature because he has himself recognized them as such."

    If the community no longer feels right, fork it.
    """
    try:
        service = ForkRightsService()
        fork = service.fork_community(
            user_id=user_id,
            original_cell_id=request.original_cell_id,
            new_cell_name=request.new_cell_name,
            fork_reason=request.fork_reason,
            members_to_invite=request.members_to_invite
        )

        return {
            "status": "success",
            "message": "Community forked",
            "fork": fork.dict(),
            "note": f"New cell created: {fork.new_cell_id}. You are steward. Invitations sent."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fork failed: {str(e)}")


@router.get("/fork-invitations/pending")
async def get_pending_fork_invitations(
    user_id: str  # TODO: Get from auth middleware
):
    """Get pending fork invitations.

    Someone forked a community and invited you to join.
    You can accept, decline, or join both communities.
    """
    try:
        service = ForkRightsService()
        invitations = service.get_pending_fork_invitations(user_id)

        return {
            "status": "success",
            "pending_invitations": [inv.dict() for inv in invitations],
            "count": len(invitations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get invitations: {str(e)}")


@router.post("/fork-invitations/respond")
async def respond_to_fork_invitation(
    response: ForkInvitationResponse,
    user_id: str  # TODO: Get from auth middleware
):
    """Respond to a fork invitation.

    accept=True: Join the new community
    accept=False: Stay where you are (or do nothing)

    You can be in both communities if you want.
    """
    try:
        service = ForkRightsService()
        service.respond_to_fork_invitation(
            user_id=user_id,
            invitation_id=response.invitation_id,
            accept=response.accept
        )

        return {
            "status": "success",
            "message": f"Invitation {'accepted' if response.accept else 'declined'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response failed: {str(e)}")


# Leave Community
@router.post("/leave-community")
async def leave_community(
    request: LeaveCommunityRequest,
    user_id: str  # TODO: Get from auth middleware
):
    """Leave a community.

    No exit interview. No surveillance. Just leave.
    Your data is yours. You can export it first if you want.

    **Freedom to exit is fundamental.**
    """
    try:
        service = ForkRightsService()
        service.leave_community(
            user_id=user_id,
            cell_id=request.cell_id
        )

        return {
            "status": "success",
            "message": "You have left the community",
            "note": "You can rejoin anytime (subject to normal vouch requirements)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leave failed: {str(e)}")


# Cleanup
@router.post("/admin/cleanup-expired")
async def cleanup_expired_data(
    admin_key: str  # TODO: Get from admin auth
):
    """Clean up expired consent requests and declined invitations.

    Data minimization - don't keep unnecessary records.
    Admin endpoint for periodic cleanup.
    """
    try:
        service = ForkRightsService()
        deleted_count = service.cleanup_expired_data()

        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} expired records",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "feature": "fork-rights",
        "gap": "GAP-65",
        "philosophy": "Freedom includes freedom to exit - Bakunin"
    }
