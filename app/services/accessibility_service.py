"""
Accessibility Service

Business logic for accessibility features.
"""

from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any

from app.database.accessibility_repository import AccessibilityRepository
from app.models.accessibility import (
    AccessibilityPreferences,
    AccessibilityFeatureUsage,
    AccessibilityFeedback,
    AccessibilityMetrics,
)


class AccessibilityService:
    """Service for accessibility operations"""

    def __init__(self, repository: AccessibilityRepository):
        self.repo = repository

    # User Preferences

    async def update_preferences(
        self,
        user_id: str,
        uses_screen_reader: Optional[bool] = None,
        uses_voice_control: Optional[bool] = None,
        uses_high_contrast: Optional[bool] = None,
        preferred_font_size: Optional[str] = None,
        reading_level_preference: Optional[str] = None,
    ) -> None:
        """Update user accessibility preferences"""
        await self.repo.update_user_preferences(
            user_id=user_id,
            uses_screen_reader=uses_screen_reader,
            uses_voice_control=uses_voice_control,
            uses_high_contrast=uses_high_contrast,
            preferred_font_size=preferred_font_size,
            reading_level_preference=reading_level_preference,
        )

    async def get_preferences(self, user_id: str) -> Optional[AccessibilityPreferences]:
        """Get user accessibility preferences"""
        return await self.repo.get_user_preferences(user_id)

    # Feature Usage Tracking

    async def track_feature_use(
        self,
        user_id: str,
        feature_name: str,
        platform: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> AccessibilityFeatureUsage:
        """Track usage of accessibility feature"""
        return await self.repo.record_feature_usage(
            user_id=user_id,
            feature_name=feature_name,
            platform=platform,
            device_info=device_info,
        )

    # Feedback

    async def submit_feedback(
        self,
        user_id: str,
        issue_type: str,
        component_affected: str,
        description: str,
        severity: str,
        blocks_usage: bool,
        accessibility_features_used: Optional[List[str]] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> AccessibilityFeedback:
        """Submit accessibility feedback"""
        return await self.repo.create_feedback(
            user_id=user_id,
            issue_type=issue_type,
            component_affected=component_affected,
            description=description,
            severity=severity,
            blocks_usage=blocks_usage,
            accessibility_features_used=accessibility_features_used,
            device_info=device_info,
        )

    async def get_open_issues(
        self, severity: Optional[str] = None
    ) -> List[AccessibilityFeedback]:
        """Get open accessibility issues"""
        return await self.repo.get_open_feedback(severity)

    # Metrics

    async def get_metrics(self, days_back: int = 30) -> AccessibilityMetrics:
        """Get accessibility metrics"""
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=days_back)

        return await self.repo.calculate_accessibility_metrics(period_start, period_end)
