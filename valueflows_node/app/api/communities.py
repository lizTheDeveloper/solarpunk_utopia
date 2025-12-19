"""Communities API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.auth.models import User
from app.auth.middleware import require_auth
from ..models.community import (
    Community,
    CommunityCreate,
    CommunityUpdate,
    CommunityMembership,
    CommunityMembershipCreate,
    CommunityStats,
)
from ..services.community_service import get_community_service


router = APIRouter(prefix="/communities", tags=["communities"])


@router.post("", response_model=Community, status_code=201)
async def create_community(
    community_data: CommunityCreate,
    current_user: User = Depends(require_auth),
):
    """
    Create a new community.
    Current user becomes the creator and first member.
    """
    service = get_community_service()
    try:
        return await service.create_community(community_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Community])
async def list_communities(current_user: User = Depends(require_auth)):
    """Get all communities the current user is a member of"""
    service = get_community_service()
    return await service.get_user_communities(current_user.id)


@router.get("/{community_id}", response_model=Community)
async def get_community(
    community_id: str,
    current_user: User = Depends(require_auth),
):
    """Get community details"""
    service = get_community_service()
    community = await service.get_community(community_id)

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Check if user is a member
    is_member = await service.is_member(community_id, current_user.id)
    if not is_member and not community.is_public:
        raise HTTPException(
            status_code=403, detail="You are not a member of this private community"
        )

    return community


@router.patch("/{community_id}", response_model=Community)
async def update_community(
    community_id: str,
    updates: CommunityUpdate,
    current_user: User = Depends(require_auth),
):
    """Update community settings (admin or creator only)"""
    service = get_community_service()

    # Check if user is admin or creator
    role = await service.get_member_role(community_id, current_user.id)
    if role not in ["creator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only community creators and admins can update settings",
        )

    community = await service.update_community(community_id, updates)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    return community


@router.delete("/{community_id}", status_code=204)
async def delete_community(
    community_id: str,
    current_user: User = Depends(require_auth),
):
    """Delete a community (creator only)"""
    service = get_community_service()

    # Check if user is creator
    role = await service.get_member_role(community_id, current_user.id)
    if role != "creator":
        raise HTTPException(
            status_code=403, detail="Only community creators can delete communities"
        )

    await service.delete_community(community_id)
    return None


@router.post("/{community_id}/members", response_model=CommunityMembership, status_code=201)
async def add_member(
    community_id: str,
    membership_data: CommunityMembershipCreate,
    current_user: User = Depends(require_auth),
):
    """Add a member to the community (admin or creator only)"""
    service = get_community_service()

    # Check if requesting user is admin or creator
    role = await service.get_member_role(community_id, current_user.id)
    if role not in ["creator", "admin"]:
        raise HTTPException(
            status_code=403, detail="Only creators and admins can add members"
        )

    try:
        return await service.add_member(community_id, membership_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{community_id}/members", response_model=List[CommunityMembership])
async def list_members(
    community_id: str,
    current_user: User = Depends(require_auth),
):
    """Get all members of a community"""
    service = get_community_service()

    # Check if user is a member or community is public
    community = await service.get_community(community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    is_member = await service.is_member(community_id, current_user.id)
    if not is_member and not community.is_public:
        raise HTTPException(
            status_code=403, detail="You are not a member of this private community"
        )

    return await service.get_members(community_id)


@router.delete("/{community_id}/members/{user_id}", status_code=204)
async def remove_member(
    community_id: str,
    user_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Remove a member from the community.
    Admins and creators can remove anyone.
    Users can remove themselves.
    """
    service = get_community_service()

    # Check permissions
    role = await service.get_member_role(community_id, current_user.id)
    is_self_removal = user_id == current_user.id

    if not is_self_removal and role not in ["creator", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Only creators and admins can remove other members",
        )

    # Don't allow removing the creator
    target_role = await service.get_member_role(community_id, user_id)
    if target_role == "creator" and not is_self_removal:
        raise HTTPException(
            status_code=403, detail="Cannot remove the community creator"
        )

    await service.remove_member(community_id, user_id)
    return None


@router.get("/{community_id}/stats", response_model=CommunityStats)
async def get_community_stats(
    community_id: str,
    current_user: User = Depends(require_auth),
):
    """Get statistics for a community"""
    service = get_community_service()

    # Check if user is a member or community is public
    community = await service.get_community(community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    is_member = await service.is_member(community_id, current_user.id)
    if not is_member and not community.is_public:
        raise HTTPException(
            status_code=403, detail="You are not a member of this private community"
        )

    return await service.get_stats(community_id)
