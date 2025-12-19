"""Community data models"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Community(BaseModel):
    """Community model"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    settings: dict = {}
    is_public: bool = True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CommunityCreate(BaseModel):
    """Community creation request"""
    name: str
    description: Optional[str] = None
    is_public: bool = True


class CommunityUpdate(BaseModel):
    """Community update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None
    is_public: Optional[bool] = None


class CommunityMembership(BaseModel):
    """Community membership model"""
    id: str
    user_id: str
    community_id: str
    role: str = "member"  # 'creator', 'admin', 'member'
    joined_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CommunityMembershipCreate(BaseModel):
    """Community membership creation request"""
    user_id: str
    role: str = "member"


class CommunityStats(BaseModel):
    """Community statistics"""
    member_count: int
    listing_count: int
    exchange_count: int
    proposal_count: int
