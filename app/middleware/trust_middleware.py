"""Trust Threshold Middleware

Enforces trust score requirements for protected API endpoints.
"""
from fastapi import Request, HTTPException
from typing import Callable
import os

from app.database.vouch_repository import VouchRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.models.vouch import TRUST_THRESHOLDS


def require_trust(action: str):
    """Decorator to require minimum trust score for an endpoint.

    Usage:
        @router.post("/offers")
        @require_trust("post_offers_needs")
        async def create_offer(...):
            ...

    Args:
        action: One of TRUST_THRESHOLDS keys
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request: Request = kwargs.get("request")
            if not request:
                # Try to find it in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Cannot find request object for trust check"
                )

            # Get current user from request state (set by auth middleware)
            if not hasattr(request.state, "user"):
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            user = request.state.user
            user_id = user.id

            # Check trust threshold
            db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
            repo = VouchRepository(db_path)
            trust_service = WebOfTrustService(repo)

            meets_threshold, actual_trust = trust_service.check_trust_threshold(user_id, action)

            if not meets_threshold:
                required_trust = TRUST_THRESHOLDS[action]
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient trust for {action}. Required: {required_trust}, have: {actual_trust:.2f}"
                )

            # User has sufficient trust, proceed
            return await func(*args, **kwargs)

        return wrapper
    return decorator


class TrustMiddleware:
    """Middleware to attach trust score to all authenticated requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive=receive)

            # Only check trust for authenticated requests
            if hasattr(request.state, "user"):
                user_id = request.state.user.id

                # Compute and attach trust score
                db_path = os.getenv("DATABASE_PATH", "data/valueflows.db")
                repo = VouchRepository(db_path)
                trust_service = WebOfTrustService(repo)

                trust_score = trust_service.compute_trust_score(user_id)

                # Attach to request state
                request.state.trust_score = trust_score

        await self.app(scope, receive, send)
