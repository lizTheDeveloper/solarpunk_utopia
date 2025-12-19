"""
CSRF Protection Middleware

GAP-56: CSRF Protection
Implements double-submit cookie pattern to prevent cross-site request forgery.
"""

import secrets
import logging
from typing import Optional, Set
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


def generate_csrf_token() -> str:
    """Generate cryptographically secure CSRF token (32 bytes, URL-safe)"""
    return secrets.token_urlsafe(32)


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """
    Extract CSRF token from request header.

    Checks both X-CSRF-Token and X-Csrf-Token (case-insensitive).
    """
    return (
        request.headers.get("X-CSRF-Token") or
        request.headers.get("X-Csrf-Token") or
        request.headers.get("x-csrf-token")
    )


def get_csrf_token_from_cookie(request: Request) -> Optional[str]:
    """Extract CSRF token from cookie"""
    return request.cookies.get("csrf_token")


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double Submit Cookie CSRF protection.

    How it works:
    1. Server sets csrf_token cookie (httponly=False so JS can read it)
    2. Client reads cookie value and sends it in X-CSRF-Token header
    3. Server validates header matches cookie

    Safe methods (GET, HEAD, OPTIONS) bypass validation.
    State-changing methods (POST, PUT, PATCH, DELETE) require matching token.

    GAP-56: Prevents cross-site request forgery attacks.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app, exempt_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or {
            "/docs",  # Swagger UI
            "/openapi.json",  # OpenAPI spec
            "/health",  # Health check
        }
        logger.info(f"CSRF Protection enabled. Exempt paths: {self.exempt_paths}")

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get tokens from header and cookie
        csrf_header = get_csrf_token_from_request(request)
        csrf_cookie = get_csrf_token_from_cookie(request)

        # Validate tokens exist
        if not csrf_header:
            logger.warning(
                f"CSRF token missing from {request.method} {request.url.path}",
                extra={
                    "ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing from request headers. Include X-CSRF-Token header."
            )

        if not csrf_cookie:
            logger.warning(
                f"CSRF cookie missing for {request.method} {request.url.path}",
                extra={
                    "ip": request.client.host if request.client else "unknown",
                }
            )
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing from cookies. Ensure cookies are enabled."
            )

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(csrf_header, csrf_cookie):
            logger.warning(
                f"CSRF token mismatch for {request.method} {request.url.path}",
                extra={
                    "ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            raise HTTPException(
                status_code=403,
                detail="CSRF token mismatch. Token may have expired or been tampered with."
            )

        # Token valid, proceed with request
        logger.debug(f"CSRF validation passed for {request.method} {request.url.path}")
        return await call_next(request)
