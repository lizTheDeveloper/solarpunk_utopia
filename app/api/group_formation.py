"""
Group Formation Protocol API

Fractal group formation with physical key exchange, nesting, and fission/fusion.
"""

import logging
from datetime import UTC
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.group_formation_service import GroupFormationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/group-formation", tags=["group-formation"])

# Global service instance
group_service = GroupFormationService()


class FounderKey(BaseModel):
    """Founding member key info"""
    user_id: str
    public_key: str  # Base64 encoded


class CreateGroupRequest(BaseModel):
    """Request to create a new group"""
    founder_keys: List[FounderKey]
    group_name: str
    parent_group_id: Optional[str] = None
    metadata: Optional[dict] = None


class GroupResponse(BaseModel):
    """Group creation response"""
    id: str
    name: str
    created_at: str
    parent_group_id: Optional[str]
    shared_key: str  # Base64 encoded
    founding_members: List[str]
    member_count: int
    formation_method: str
    resources: dict
    nesting_level: int


class InvitationRequest(BaseModel):
    """Request to create group invitation"""
    group_id: str
    inviter_user_id: str
    inviter_private_key: str  # Base64 encoded
    invitee_public_key: str  # Base64 encoded
    group_shared_key: str  # Base64 encoded


class AcceptInvitationRequest(BaseModel):
    """Request to accept invitation"""
    invitation: dict
    invitee_user_id: str
    invitee_private_key: str  # Base64 encoded
    inviter_public_key: str  # Base64 encoded


class QRFormationRequest(BaseModel):
    """Request to generate QR formation token"""
    group_id: str
    inviter_user_id: str
    group_shared_key: str  # Base64 encoded
    expiry_minutes: int = 30


class QRJoinRequest(BaseModel):
    """Request to join via QR code"""
    qr_token: str
    otp: str
    joiner_user_id: str


class NestedGroupRequest(BaseModel):
    """Request to create nested subgroup"""
    parent_group_id: str
    parent_group_key: str  # Base64 encoded
    founder_keys: List[FounderKey]
    subgroup_name: str
    inherit_members: bool = False


class MergeGroupsRequest(BaseModel):
    """Request to merge two groups"""
    group_a_id: str
    group_a_key: str  # Base64 encoded
    group_b_id: str
    group_b_key: str  # Base64 encoded
    merged_name: str
    consensus_required: bool = True


class SplitGroupRequest(BaseModel):
    """Request to split a group"""
    original_group_id: str
    original_group_key: str  # Base64 encoded
    departing_member_ids: List[str]
    new_group_name: str
    secession_reason: Optional[str] = None


@router.post("/create", response_model=GroupResponse)
async def create_group(request: CreateGroupRequest):
    """
    Create a new group via physical key exchange.

    Requires minimum 3 founding members (commune, not couple).
    Each founder provides their public key for future invitations.

    Returns:
        Group info including shared symmetric key
    """
    try:
        from nacl.encoding import Base64Encoder

        # Convert founder keys to proper format
        founder_keys = [
            {
                "user_id": fk.user_id,
                "public_key": Base64Encoder.decode(fk.public_key.encode('utf-8'))
            }
            for fk in request.founder_keys
        ]

        group = group_service.create_initial_group(
            founder_keys=founder_keys,
            group_name=request.group_name,
            parent_group_id=request.parent_group_id,
            metadata=request.metadata
        )

        return group

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.post("/invite")
async def create_invitation(request: InvitationRequest):
    """
    Create encrypted invitation for new member.

    Uses NaCl Box to encrypt group key from inviter to invitee.

    Returns:
        Encrypted invitation dict
    """
    try:
        from nacl.encoding import Base64Encoder

        invitation = group_service.create_formation_invitation(
            group_id=request.group_id,
            inviter_user_id=request.inviter_user_id,
            inviter_private_key=Base64Encoder.decode(request.inviter_private_key.encode('utf-8')),
            invitee_public_key=Base64Encoder.decode(request.invitee_public_key.encode('utf-8')),
            group_shared_key=Base64Encoder.decode(request.group_shared_key.encode('utf-8'))
        )

        return invitation

    except Exception as e:
        logger.error(f"Error creating invitation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create invitation: {str(e)}")


@router.post("/accept-invitation")
async def accept_invitation(request: AcceptInvitationRequest):
    """
    Accept group invitation and decrypt group key.

    Returns:
        Decrypted group shared key (Base64 encoded)
    """
    try:
        from nacl.encoding import Base64Encoder

        group_key = group_service.accept_invitation(
            invitation=request.invitation,
            invitee_user_id=request.invitee_user_id,
            invitee_private_key=Base64Encoder.decode(request.invitee_private_key.encode('utf-8')),
            inviter_public_key=Base64Encoder.decode(request.inviter_public_key.encode('utf-8'))
        )

        return {
            "group_id": request.invitation["group_id"],
            "group_shared_key": Base64Encoder.encode(group_key).decode('utf-8'),
            "accepted_at": request.invitation.get("created_at")
        }

    except Exception as e:
        logger.error(f"Error accepting invitation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to accept invitation: {str(e)}")


@router.post("/qr-formation")
async def generate_qr_token(request: QRFormationRequest):
    """
    Generate QR code token for physical group formation.

    Returns QR data and one-time password (OTP) for display/verbal sharing.

    Returns:
        dict with qr_token and otp
    """
    try:
        from nacl.encoding import Base64Encoder

        qr_token, otp = group_service.generate_qr_formation_token(
            group_id=request.group_id,
            inviter_user_id=request.inviter_user_id,
            group_shared_key=Base64Encoder.decode(request.group_shared_key.encode('utf-8')),
            expiry_minutes=request.expiry_minutes
        )

        return {
            "qr_token": qr_token,
            "otp": otp,
            "expires_in_minutes": request.expiry_minutes,
            "instructions": "Display QR code to joiner. Share OTP verbally or on screen."
        }

    except Exception as e:
        logger.error(f"Error generating QR token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate QR token: {str(e)}")


@router.post("/qr-join")
async def join_via_qr(request: QRJoinRequest):
    """
    Scan QR code and join group using OTP.

    Returns:
        Decrypted group shared key
    """
    try:
        from nacl.encoding import Base64Encoder

        group_key = group_service.scan_qr_and_join(
            qr_token=request.qr_token,
            otp=request.otp,
            joiner_user_id=request.joiner_user_id
        )

        return {
            "group_shared_key": Base64Encoder.encode(group_key).decode('utf-8'),
            "joined_at": group_service._get_current_timestamp()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error joining via QR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to join via QR: {str(e)}")


@router.post("/create-nested", response_model=GroupResponse)
async def create_nested_group(request: NestedGroupRequest):
    """
    Create nested subgroup within parent group.

    Implements subsidiarity: child has privacy from parent,
    but inherits parent's trusted roots.

    Returns:
        Subgroup info
    """
    try:
        from nacl.encoding import Base64Encoder

        founder_keys = [
            {
                "user_id": fk.user_id,
                "public_key": Base64Encoder.decode(fk.public_key.encode('utf-8'))
            }
            for fk in request.founder_keys
        ]

        subgroup = group_service.create_nested_group(
            parent_group_id=request.parent_group_id,
            parent_group_key=Base64Encoder.decode(request.parent_group_key.encode('utf-8')),
            founder_keys=founder_keys,
            subgroup_name=request.subgroup_name,
            inherit_members=request.inherit_members
        )

        return subgroup

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating nested group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create nested group: {str(e)}")


@router.post("/merge")
async def merge_groups(request: MergeGroupsRequest):
    """
    Merge two groups into new federated group (fusion).

    Both groups' members must consent if consensus_required=True.

    Returns:
        Merged group info
    """
    try:
        from nacl.encoding import Base64Encoder

        merged = group_service.merge_groups(
            group_a_id=request.group_a_id,
            group_a_key=Base64Encoder.decode(request.group_a_key.encode('utf-8')),
            group_b_id=request.group_b_id,
            group_b_key=Base64Encoder.decode(request.group_b_key.encode('utf-8')),
            merged_name=request.merged_name,
            consensus_required=request.consensus_required
        )

        return merged

    except Exception as e:
        logger.error(f"Error merging groups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to merge groups: {str(e)}")


@router.post("/split")
async def split_group(request: SplitGroupRequest):
    """
    Split group into two (fission/secession).

    Departing members form new group. Original group continues
    with new shared key.

    Returns:
        dict with new_group and original_group_new_key
    """
    try:
        from nacl.encoding import Base64Encoder

        result = group_service.split_group(
            original_group_id=request.original_group_id,
            original_group_key=Base64Encoder.decode(request.original_group_key.encode('utf-8')),
            departing_member_ids=request.departing_member_ids,
            new_group_name=request.new_group_name,
            secession_reason=request.secession_reason
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error splitting group: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to split group: {str(e)}")


# Helper method to add to service (for timestamp)
GroupFormationService._get_current_timestamp = lambda self: __import__('datetime').datetime.now(UTC).isoformat()
