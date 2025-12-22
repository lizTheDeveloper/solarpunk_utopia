"""
Accessibility Repository

Database operations for accessibility tracking and compliance.
"""

import json
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional, Dict, Any
import aiosqlite

from app.models.accessibility import (
    AccessibilityPreferences,
    AccessibilityFeatureUsage,
    AccessibilityFeedback,
    AccessibilityMetrics,
    FeatureName,
    IssueType,
    Severity,
    IssueStatus,
    FontSize,
    ReadingLevel,
)


class AccessibilityRepository:
    """Repository for accessibility operations"""

    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self.db = db

    # User Preferences

    async def update_user_preferences(
        self,
        user_id: str,
        uses_screen_reader: Optional[bool] = None,
        uses_voice_control: Optional[bool] = None,
        uses_high_contrast: Optional[bool] = None,
        preferred_font_size: Optional[str] = None,
        reading_level_preference: Optional[str] = None,
    ) -> None:
        """Update user accessibility preferences"""
        updates = []
        values = []

        if uses_screen_reader is not None:
            updates.append("uses_screen_reader = ?")
            values.append(1 if uses_screen_reader else 0)

        if uses_voice_control is not None:
            updates.append("uses_voice_control = ?")
            values.append(1 if uses_voice_control else 0)

        if uses_high_contrast is not None:
            updates.append("uses_high_contrast = ?")
            values.append(1 if uses_high_contrast else 0)

        if preferred_font_size is not None:
            updates.append("preferred_font_size = ?")
            values.append(preferred_font_size)

        if reading_level_preference is not None:
            updates.append("reading_level_preference = ?")
            values.append(reading_level_preference)

        # Enable accessibility mode if any feature is enabled
        if uses_screen_reader or uses_voice_control or uses_high_contrast:
            updates.append("accessibility_mode_enabled = 1")

        if updates:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            await self.db.execute(query, values)
            await self.db.commit()

    async def get_user_preferences(self, user_id: str) -> Optional[AccessibilityPreferences]:
        """Get user accessibility preferences"""
        cursor = await self.db.execute(
            """
            SELECT
                uses_screen_reader,
                uses_voice_control,
                uses_high_contrast,
                preferred_font_size,
                reading_level_preference,
                accessibility_mode_enabled,
                accessibility_preferences
            FROM users WHERE id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return AccessibilityPreferences(
            uses_screen_reader=bool(row[0]),
            uses_voice_control=bool(row[1]),
            uses_high_contrast=bool(row[2]),
            preferred_font_size=FontSize(row[3]) if row[3] else FontSize.MEDIUM,
            reading_level_preference=(
                ReadingLevel(row[4]) if row[4] else ReadingLevel.STANDARD
            ),
            accessibility_mode_enabled=bool(row[5]),
            custom_preferences=json.loads(row[6]) if row[6] else {},
        )

    # Feature Usage Tracking

    async def record_feature_usage(
        self,
        user_id: str,
        feature_name: str,
        platform: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> AccessibilityFeatureUsage:
        """Record usage of an accessibility feature"""
        now = datetime.now(UTC).isoformat()

        # Check if already exists
        cursor = await self.db.execute(
            "SELECT id, usage_count FROM accessibility_feature_usage WHERE user_id = ? AND feature_name = ?",
            (user_id, feature_name),
        )
        row = await cursor.fetchone()

        if row:
            # Update existing
            usage_id = row[0]
            new_count = row[1] + 1

            await self.db.execute(
                """
                UPDATE accessibility_feature_usage
                SET last_used_at = ?, usage_count = ?
                WHERE id = ?
                """,
                (now, new_count, usage_id),
            )
        else:
            # Create new
            usage_id = str(uuid.uuid4())

            await self.db.execute(
                """
                INSERT INTO accessibility_feature_usage (
                    id, user_id, feature_name, first_used_at, last_used_at,
                    usage_count, platform, device_info, created_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    usage_id,
                    user_id,
                    feature_name,
                    now,
                    now,
                    platform,
                    json.dumps(device_info) if device_info else None,
                    now,
                ),
            )

        await self.db.commit()

        # Return the usage record
        cursor = await self.db.execute(
            "SELECT * FROM accessibility_feature_usage WHERE id = ?", (usage_id,)
        )
        row = await cursor.fetchone()

        return AccessibilityFeatureUsage(
            id=row[0],
            user_id=row[1],
            feature_name=FeatureName(row[2]),
            first_used_at=datetime.fromisoformat(row[3]),
            last_used_at=datetime.fromisoformat(row[4]),
            usage_count=row[5],
            platform=row[6],
            device_info=json.loads(row[7]) if row[7] else None,
            created_at=datetime.fromisoformat(row[8]),
        )

    # Feedback

    async def create_feedback(
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
        """Create accessibility feedback"""
        feedback_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        await self.db.execute(
            """
            INSERT INTO accessibility_feedback (
                id, user_id, issue_type, component_affected, description,
                severity, blocks_usage, accessibility_features_used,
                device_info, status, reported_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                feedback_id,
                user_id,
                issue_type,
                component_affected,
                description,
                severity,
                1 if blocks_usage else 0,
                json.dumps(accessibility_features_used) if accessibility_features_used else None,
                json.dumps(device_info) if device_info else None,
                now,
            ),
        )
        await self.db.commit()

        return AccessibilityFeedback(
            id=feedback_id,
            user_id=user_id,
            issue_type=IssueType(issue_type),
            component_affected=component_affected,
            description=description,
            severity=Severity(severity),
            blocks_usage=blocks_usage,
            accessibility_features_used=accessibility_features_used,
            device_info=device_info,
            status=IssueStatus.OPEN,
            resolved_by=None,
            resolved_at=None,
            resolution_notes=None,
            reported_at=datetime.fromisoformat(now),
        )

    async def get_open_feedback(
        self, severity: Optional[str] = None
    ) -> List[AccessibilityFeedback]:
        """Get open accessibility feedback"""
        query = "SELECT * FROM accessibility_feedback WHERE status = 'open'"
        params = []

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY severity DESC, reported_at DESC"

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_feedback(row) for row in rows]

    def _row_to_feedback(self, row) -> AccessibilityFeedback:
        """Convert database row to AccessibilityFeedback"""
        return AccessibilityFeedback(
            id=row[0],
            user_id=row[1],
            issue_type=IssueType(row[2]),
            component_affected=row[3],
            description=row[4],
            severity=Severity(row[5]),
            blocks_usage=bool(row[6]),
            accessibility_features_used=json.loads(row[7]) if row[7] else None,
            device_info=json.loads(row[8]) if row[8] else None,
            status=IssueStatus(row[9]),
            resolved_by=row[10],
            resolved_at=datetime.fromisoformat(row[11]) if row[11] else None,
            resolution_notes=row[12],
            reported_at=datetime.fromisoformat(row[13]),
        )

    # Metrics

    async def calculate_accessibility_metrics(
        self, period_start: datetime, period_end: datetime
    ) -> AccessibilityMetrics:
        """Calculate accessibility metrics"""
        metrics_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        # Total active users
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM users WHERE created_at <= ?",
            (period_end.isoformat(),),
        )
        total_active = (await cursor.fetchone())[0]

        # Users with accessibility features enabled
        cursor = await self.db.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM accessibility_feature_usage
            WHERE first_used_at BETWEEN ? AND ?
            """,
            (period_start.isoformat(), period_end.isoformat()),
        )
        users_with_features = (await cursor.fetchone())[0]

        # Screen reader users
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM users WHERE uses_screen_reader = 1 AND created_at <= ?",
            (period_end.isoformat(),),
        )
        screen_reader_users = (await cursor.fetchone())[0]

        # Voice control users
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM users WHERE uses_voice_control = 1 AND created_at <= ?",
            (period_end.isoformat(),),
        )
        voice_control_users = (await cursor.fetchone())[0]

        # High contrast users
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM users WHERE uses_high_contrast = 1 AND created_at <= ?",
            (period_end.isoformat(),),
        )
        high_contrast_users = (await cursor.fetchone())[0]

        # Large font users
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE preferred_font_size IN ('large', 'extra_large')
            AND created_at <= ?
            """,
            (period_end.isoformat(),),
        )
        large_font_users = (await cursor.fetchone())[0]

        # Open accessibility issues
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM accessibility_feedback WHERE status = 'open'"
        )
        open_issues = (await cursor.fetchone())[0]

        # Critical issues
        cursor = await self.db.execute(
            """
            SELECT COUNT(*) FROM accessibility_feedback
            WHERE severity = 'critical' AND status = 'open'
            """
        )
        critical_issues = (await cursor.fetchone())[0]

        # Calculate success metric
        usage_percentage = (
            (users_with_features / total_active * 100) if total_active > 0 else 0.0
        )

        # Store metrics
        await self.db.execute(
            """
            INSERT INTO accessibility_metrics (
                id, period_start, period_end, total_active_users,
                users_with_accessibility_features, screen_reader_users,
                voice_control_users, high_contrast_users, large_font_users,
                components_audited, components_passing, open_accessibility_issues,
                critical_issues, accessibility_feature_usage_percentage,
                calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)
            """,
            (
                metrics_id,
                period_start.isoformat(),
                period_end.isoformat(),
                total_active,
                users_with_features,
                screen_reader_users,
                voice_control_users,
                high_contrast_users,
                large_font_users,
                open_issues,
                critical_issues,
                usage_percentage,
                now.isoformat(),
            ),
        )
        await self.db.commit()

        return AccessibilityMetrics(
            id=metrics_id,
            period_start=period_start,
            period_end=period_end,
            total_active_users=total_active,
            users_with_accessibility_features=users_with_features,
            screen_reader_users=screen_reader_users,
            voice_control_users=voice_control_users,
            high_contrast_users=high_contrast_users,
            large_font_users=large_font_users,
            components_audited=0,
            components_passing=0,
            open_accessibility_issues=open_issues,
            critical_issues=critical_issues,
            accessibility_feature_usage_percentage=usage_percentage,
            calculated_at=now,
        )
