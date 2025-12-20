"""
Auth middleware for FastAPI

Extracts user from Authorization header and attaches to request.state
"""

import os
import logging
from functools import wraps
from fastapi import Request, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .models import User
from .service import get_auth_service
from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService

logger = logging.getLogger(__name__)


security = HTTPBearer(auto_error=False)

# Admin API key from environment (for background worker endpoints)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", None)


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


async def require_admin_key(x_admin_key: Optional[str] = Header(None)):
    """
    Require admin API key for admin-only endpoints.

    Use this for background worker endpoints that need to be protected
    but don't have user authentication.

    Usage:
        @router.post("/admin/purge")
        async def admin_endpoint(auth: None = Depends(require_admin_key)):
            ...
    """
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Admin API key not configured (set ADMIN_API_KEY environment variable)"
        )

    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing admin API key"
        )

    return None


# Steward trust threshold from FRAUD_ABUSE_SAFETY.md
STEWARD_TRUST_THRESHOLD = 0.9


def get_vouch_repo():
    """Get vouch repository instance."""
    return VouchRepository(db_path="data/solarpunk.db")


def get_trust_service(repo: VouchRepository = Depends(get_vouch_repo)):
    """Get WebOfTrustService instance."""
    return WebOfTrustService(repo)


async def require_steward(
    user: User = Depends(require_auth),
    trust_service: WebOfTrustService = Depends(get_trust_service)
) -> User:
    """
    Require user to have steward-level trust (>= 0.9).

    This is a FastAPI dependency that verifies the authenticated user
    has high enough trust score to perform steward-only actions.

    Args:
        user: Current authenticated user (from require_auth)
        trust_service: WebOfTrustService instance

    Returns:
        User object if verification passes

    Raises:
        HTTPException(403): If user trust < 0.9

    Usage:
        @router.post("/steward-only-endpoint")
        async def endpoint(user: User = Depends(require_steward)):
            # User has been verified as steward
            ...

    GAP-134: Fix Steward Verification
    """
    user_id = user.id
    trust_score = trust_service.compute_trust_score(user_id)

    if trust_score.computed_trust < STEWARD_TRUST_THRESHOLD:
        # Log failed attempt for security audit
        logger.warning(
            f"Steward access denied for user {user_id}: "
            f"trust {trust_score.computed_trust:.2f} < {STEWARD_TRUST_THRESHOLD}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Steward access required (trust >= {STEWARD_TRUST_THRESHOLD})"
        )

    # Log successful verification
    logger.info(f"Steward access granted for user {user_id} (trust: {trust_score.computed_trust:.2f})")
    return user
