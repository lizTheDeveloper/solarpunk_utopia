"""
Accessibility API Routes

API endpoints for accessibility features and tracking.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database.db import get_db
from app.database.accessibility_repository import AccessibilityRepository
from app.services.accessibility_service import AccessibilityService
from app.auth.middleware import get_current_user

router = APIRouter(prefix="/api/accessibility", tags=["accessibility"])


# Request/Response Models


class PreferencesUpdate(BaseModel):
    """Update accessibility preferences request"""

    uses_screen_reader: Optional[bool] = None
    uses_voice_control: Optional[bool] = None
    uses_high_contrast: Optional[bool] = None
    preferred_font_size: Optional[str] = Field(
        None, description="small, medium, large, extra_large"
    )
    reading_level_preference: Optional[str] = Field(
        None, description="simple, standard, technical"
    )


class PreferencesResponse(BaseModel):
    """Accessibility preferences response"""

    uses_screen_reader: bool
    uses_voice_control: bool
    uses_high_contrast: bool
    preferred_font_size: str
    reading_level_preference: str
    accessibility_mode_enabled: bool


class FeatureUsageTrack(BaseModel):
    """Track feature usage request"""

    feature_name: str = Field(
        ...,
        description="screen_reader, voice_control, high_contrast, large_font, simple_language",
    )
    platform: Optional[str] = Field(None, description="android, web, ios")
    device_info: Optional[dict] = None


class FeedbackCreate(BaseModel):
    """Create accessibility feedback request"""

    issue_type: str = Field(
        ...,
        description="screen_reader_issue, touch_target_too_small, language_too_complex, contrast_too_low, voice_control_broken",
    )
    component_affected: str
    description: str
    severity: str = Field(..., description="low, medium, high, critical")
    blocks_usage: bool
    accessibility_features_used: Optional[List[str]] = None
    device_info: Optional[dict] = None


class FeedbackResponse(BaseModel):
    """Accessibility feedback response"""

    id: str
    user_id: str
    issue_type: str
    component_affected: str
    description: str
    severity: str
    blocks_usage: bool
    status: str
    reported_at: str


class MetricsResponse(BaseModel):
    """Accessibility metrics response"""

    total_active_users: int
    users_with_accessibility_features: int
    screen_reader_users: int
    voice_control_users: int
    high_contrast_users: int
    large_font_users: int
    open_accessibility_issues: int
    critical_issues: int
    accessibility_feature_usage_percentage: float
    period_start: str
    period_end: str


# Dependency injection


async def get_service(db=Depends(get_db)) -> AccessibilityService:
    """Get accessibility service"""
    repo = AccessibilityRepository(db)
    return AccessibilityService(repo)


# Preferences


@router.patch("/preferences", response_model=dict)
async def update_preferences(
    request: PreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    service: AccessibilityService = Depends(get_service),
):
    """Update user accessibility preferences"""
    await service.update_preferences(
        user_id=current_user["id"],
        uses_screen_reader=request.uses_screen_reader,
        uses_voice_control=request.uses_voice_control,
        uses_high_contrast=request.uses_high_contrast,
        preferred_font_size=request.preferred_font_size,
        reading_level_preference=request.reading_level_preference,
    )

    return {"success": True}


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    current_user: dict = Depends(get_current_user),
    service: AccessibilityService = Depends(get_service),
):
    """Get user accessibility preferences"""
    prefs = await service.get_preferences(current_user["id"])

    if not prefs:
        # Return defaults
        return PreferencesResponse(
            uses_screen_reader=False,
            uses_voice_control=False,
            uses_high_contrast=False,
            preferred_font_size="medium",
            reading_level_preference="standard",
            accessibility_mode_enabled=False,
        )

    return PreferencesResponse(
        uses_screen_reader=prefs.uses_screen_reader,
        uses_voice_control=prefs.uses_voice_control,
        uses_high_contrast=prefs.uses_high_contrast,
        preferred_font_size=prefs.preferred_font_size.value,
        reading_level_preference=prefs.reading_level_preference.value,
        accessibility_mode_enabled=prefs.accessibility_mode_enabled,
    )


# Feature Usage Tracking


@router.post("/track-feature", response_model=dict)
async def track_feature_usage(
    request: FeatureUsageTrack,
    current_user: dict = Depends(get_current_user),
    service: AccessibilityService = Depends(get_service),
):
    """Track usage of an accessibility feature"""
    usage = await service.track_feature_use(
        user_id=current_user["id"],
        feature_name=request.feature_name,
        platform=request.platform,
        device_info=request.device_info,
    )

    return {"success": True, "usage_count": usage.usage_count}


# Feedback


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    service: AccessibilityService = Depends(get_service),
):
    """Submit accessibility feedback"""
    feedback = await service.submit_feedback(
        user_id=current_user["id"],
        issue_type=request.issue_type,
        component_affected=request.component_affected,
        description=request.description,
        severity=request.severity,
        blocks_usage=request.blocks_usage,
        accessibility_features_used=request.accessibility_features_used,
        device_info=request.device_info,
    )

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        issue_type=feedback.issue_type.value,
        component_affected=feedback.component_affected,
        description=feedback.description,
        severity=feedback.severity.value,
        blocks_usage=feedback.blocks_usage,
        status=feedback.status.value,
        reported_at=feedback.reported_at.isoformat(),
    )


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_open_feedback(
    severity: Optional[str] = None,
    service: AccessibilityService = Depends(get_service),
):
    """Get open accessibility feedback"""
    issues = await service.get_open_issues(severity)

    return [
        FeedbackResponse(
            id=issue.id,
            user_id=issue.user_id,
            issue_type=issue.issue_type.value,
            component_affected=issue.component_affected,
            description=issue.description,
            severity=issue.severity.value,
            blocks_usage=issue.blocks_usage,
            status=issue.status.value,
            reported_at=issue.reported_at.isoformat(),
        )
        for issue in issues
    ]


# Metrics


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    days_back: int = 30,
    service: AccessibilityService = Depends(get_service),
):
    """Get accessibility metrics"""
    metrics = await service.get_metrics(days_back)

    return MetricsResponse(
        total_active_users=metrics.total_active_users,
        users_with_accessibility_features=metrics.users_with_accessibility_features,
        screen_reader_users=metrics.screen_reader_users,
        voice_control_users=metrics.voice_control_users,
        high_contrast_users=metrics.high_contrast_users,
        large_font_users=metrics.large_font_users,
        open_accessibility_issues=metrics.open_accessibility_issues,
        critical_issues=metrics.critical_issues,
        accessibility_feature_usage_percentage=metrics.accessibility_feature_usage_percentage,
        period_start=metrics.period_start.isoformat(),
        period_end=metrics.period_end.isoformat(),
    )
