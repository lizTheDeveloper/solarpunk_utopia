"""Auth data models"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class User(BaseModel):
    """User model"""
    id: str
    name: str
    email: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    settings: dict = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class UserCreate(BaseModel):
    """User creation request"""
    name: str
    email: Optional[str] = None


class Session(BaseModel):
    """Session model"""
    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime


class LoginRequest(BaseModel):
    """Login request (name-based for local mode)"""
    name: str


class LoginResponse(BaseModel):
    """Login response"""
    user: User
    token: str
    expires_at: datetime
