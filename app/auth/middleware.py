"""
Auth middleware for FastAPI

Extracts user from Authorization header and attaches to request.state
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .models import User
from .service import get_auth_service


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Extract current user from Authorization header.

    Returns None if no auth provided (for optional auth endpoints).
    Raises 401 if invalid token provided.
    """
    if not credentials:
        return None

    token = credentials.credentials
    auth_service = get_auth_service()

    user = await auth_service.get_user_from_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session token"
        )

    return user


async def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Require authentication - raises 401 if not authenticated.

    Use this as a dependency for protected endpoints.
    """
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    return user
