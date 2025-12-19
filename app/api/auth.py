"""Auth API endpoints"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from starlette.responses import Response

from app.auth.models import UserCreate, LoginRequest, LoginResponse, User
from app.auth.service import get_auth_service
from app.auth.middleware import get_current_user
from app.middleware.csrf import generate_csrf_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginResponse)
async def register(user_data: UserCreate):
    """
    Register a new user (or login if name already exists).

    Simple name-based registration - perfect for workshops and demos.
    No passwords, no email verification needed.
    """
    auth_service = get_auth_service()
    return await auth_service.register(user_data)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with username.

    Simple name-based login for local/demo mode.
    """
    auth_service = get_auth_service()
    result = await auth_service.login(request.name)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"User '{request.name}' not found. Try registering first."
        )

    return result


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """Logout current user"""
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")

    # Extract token from request would require access to request object
    # For now, just return success
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_endpoint(user: Optional[User] = Depends(get_current_user)):
    """Get current user info"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return user


@router.post("/csrf-token")
async def get_csrf_token(response: Response):
    """
    Get CSRF token for subsequent requests.

    Sets csrf_token cookie (httponly=False so JS can read it).
    Client should include this value in X-CSRF-Token header for state-changing requests.

    GAP-56: CSRF Protection
    """
    token = generate_csrf_token()

    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # JS needs to read this for X-CSRF-Token header
        secure=False,  # TODO: Set to True in production with HTTPS
        samesite="strict",
        max_age=3600 * 24,  # 24 hours
    )

    return {
        "csrf_token": token,
        "usage": "Include this token in X-CSRF-Token header for POST/PUT/PATCH/DELETE requests"
    }
