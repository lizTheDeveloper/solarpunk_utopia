"""
Transparency Repository

Data access layer for algorithmic transparency features.
"""

import logging
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC
import json

from app.models.algorithmic_transparency import (
    MatchExplanation,
    MatchingWeights,
    MatchingAuditLog,
    BiasDetectionReport,
    TransparencyPreferences,
    BiasReportStatus,
)


logger = logging.getLogger(__name__)


class TransparencyRepository:
    """Repository for algorithmic transparency data"""

    def __init__(self, db_path: str = "commune.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================== Match Explanations ====================

    async def create_match_explanation(self, explanation: MatchExplanation) -> MatchExplanation:
        """Store match explanation"""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO match_explanations (
                    id, match_id, category_score, location_score, time_score,
                    quantity_score, total_score, category_weight, location_weight,
                    time_weight, quantity_weight, explanation_text, distance_km,
                    distance_description, category_match_type, time_buffer_hours,
                    quantity_ratio, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    explanation.id,
                    explanation.match_id,
                    explanation.category_score,
                    explanation.location_score,
                    explanation.time_score,
                    explanation.quantity_score,
                    explanation.total_score,
                    explanation.category_weight,
                    explanation.location_weight,
                    explanation.time_weight,
                    explanation.quantity_weight,
                    explanation.explanation_text,
                    explanation.distance_km,
                    explanation.distance_description,
                    explanation.category_match_type.value if explanation.category_match_type else None,
                    explanation.time_buffer_hours,
                    explanation.quantity_ratio,
                    explanation.created_at.isoformat() if explanation.created_at else datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()
            return explanation
        finally:
            conn.close()

    async def get_match_explanation(self, match_id: str) -> Optional[MatchExplanation]:
        """Get explanation for a match"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM match_explanations WHERE match_id = ?",
                (match_id,)
            ).fetchone()

            if not row:
                return None

            return MatchExplanation.from_dict(dict(row))
        finally:
            conn.close()

    # ==================== Matching Weights ====================

    async def create_matching_weights(self, weights: MatchingWeights) -> MatchingWeights:
        """Create new weights configuration"""
        if not weights.validate_weights():
            raise ValueError("Weights must sum to 1.0")

        conn = self._get_connection()
        try:
            # If this is active, deactivate other configs for this community
            if weights.is_active:
                conn.execute(
                    """
                    UPDATE matching_weights
                    SET is_active = FALSE, updated_at = ?
                    WHERE community_id IS ? AND is_active = TRUE
                    """,
                    (datetime.now(UTC).isoformat(), weights.community_id)
                )

            conn.execute(
                """
                INSERT INTO matching_weights (
                    id, community_id, category_weight, location_weight,
                    time_weight, quantity_weight, name, description,
                    is_active, created_at, updated_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    weights.id,
                    weights.community_id,
                    weights.category_weight,
                    weights.location_weight,
                    weights.time_weight,
                    weights.quantity_weight,
                    weights.name,
                    weights.description,
                    weights.is_active,
                    weights.created_at.isoformat() if weights.created_at else datetime.now(UTC).isoformat(),
                    weights.updated_at.isoformat() if weights.updated_at else datetime.now(UTC).isoformat(),
                    weights.created_by,
                ),
            )
            conn.commit()
            return weights
        finally:
            conn.close()

    async def get_active_weights(self, community_id: Optional[str] = None) -> MatchingWeights:
        """Get active weights for community (or system default)"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT * FROM matching_weights
                WHERE community_id IS ? AND is_active = TRUE
                LIMIT 1
                """,
                (community_id,)
            ).fetchone()

            if not row:
                # Fall back to system default
                row = conn.execute(
                    """
                    SELECT * FROM matching_weights
                    WHERE community_id IS NULL AND is_active = TRUE
                    LIMIT 1
                    """
                ).fetchone()

            if not row:
                # Shouldn't happen due to migration, but return default
                return MatchingWeights(
                    id="weights:default",
                    community_id=None,
                    name="Default",
                )

            return MatchingWeights.from_dict(dict(row))
        finally:
            conn.close()

    async def list_weights(self, community_id: Optional[str] = None) -> List[MatchingWeights]:
        """List all weight configurations for community"""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM matching_weights
                WHERE community_id IS ?
                ORDER BY created_at DESC
                """,
                (community_id,)
            ).fetchall()

            return [MatchingWeights.from_dict(dict(row)) for row in rows]
        finally:
            conn.close()

    async def update_matching_weights(self, weights: MatchingWeights) -> MatchingWeights:
        """Update existing weights configuration"""
        if not weights.validate_weights():
            raise ValueError("Weights must sum to 1.0")

        conn = self._get_connection()
        try:
            # If activating, deactivate others
            if weights.is_active:
                conn.execute(
                    """
                    UPDATE matching_weights
                    SET is_active = FALSE, updated_at = ?
                    WHERE community_id IS ? AND id != ? AND is_active = TRUE
                    """,
                    (datetime.now(UTC).isoformat(), weights.community_id, weights.id)
                )

            conn.execute(
                """
                UPDATE matching_weights
                SET category_weight = ?, location_weight = ?, time_weight = ?,
                    quantity_weight = ?, name = ?, description = ?,
                    is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    weights.category_weight,
                    weights.location_weight,
                    weights.time_weight,
                    weights.quantity_weight,
                    weights.name,
                    weights.description,
                    weights.is_active,
                    datetime.now(UTC).isoformat(),
                    weights.id,
                ),
            )
            conn.commit()
            return weights
        finally:
            conn.close()

    # ==================== Audit Log ====================

    async def create_audit_log(self, log: MatchingAuditLog) -> MatchingAuditLog:
        """Create audit log entry"""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO matching_audit_log (
                    id, match_id, offer_id, need_id, match_score, threshold_score,
                    matched, weights_config_id, provider_demographic_hash,
                    receiver_demographic_hash, provider_zone, receiver_zone,
                    offer_category, need_category, created_at, agent_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.match_id,
                    log.offer_id,
                    log.need_id,
                    log.match_score,
                    log.threshold_score,
                    log.matched,
                    log.weights_config_id,
                    log.provider_demographic_hash,
                    log.receiver_demographic_hash,
                    log.provider_zone,
                    log.receiver_zone,
                    log.offer_category,
                    log.need_category,
                    log.created_at.isoformat() if log.created_at else datetime.now(UTC).isoformat(),
                    log.agent_version,
                ),
            )
            conn.commit()
            return log
        finally:
            conn.close()

    async def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        community_id: Optional[str] = None,
        matched_only: bool = False,
        limit: int = 100,
    ) -> List[MatchingAuditLog]:
        """Get audit logs for analysis"""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM matching_audit_log WHERE 1=1"
            params: List[Any] = []

            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time.isoformat())

            if matched_only:
                query += " AND matched = TRUE"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [MatchingAuditLog.from_dict(dict(row)) for row in rows]
        finally:
            conn.close()

    # ==================== Bias Detection ====================

    async def create_bias_report(self, report: BiasDetectionReport) -> BiasDetectionReport:
        """Create bias detection report"""
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO bias_detection_reports (
                    id, analysis_start, analysis_end, community_id, category,
                    total_matches_analyzed, geographic_bias_score,
                    geographic_bias_details, category_bias_score,
                    category_bias_details, demographic_bias_score,
                    demographic_bias_details, overall_bias_score, bias_detected,
                    recommendations, created_at, created_by, status,
                    community_reviewed, community_response
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.id,
                    report.analysis_start.isoformat(),
                    report.analysis_end.isoformat(),
                    report.community_id,
                    report.category,
                    report.total_matches_analyzed,
                    report.geographic_bias_score,
                    report.geographic_bias_details,
                    report.category_bias_score,
                    report.category_bias_details,
                    report.demographic_bias_score,
                    report.demographic_bias_details,
                    report.overall_bias_score,
                    report.bias_detected,
                    report.recommendations,
                    report.created_at.isoformat() if report.created_at else datetime.now(UTC).isoformat(),
                    report.created_by,
                    report.status.value,
                    report.community_reviewed,
                    report.community_response,
                ),
            )
            conn.commit()
            return report
        finally:
            conn.close()

    async def get_bias_report(self, report_id: str) -> Optional[BiasDetectionReport]:
        """Get bias detection report"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM bias_detection_reports WHERE id = ?",
                (report_id,)
            ).fetchone()

            if not row:
                return None

            return BiasDetectionReport.from_dict(dict(row))
        finally:
            conn.close()

    async def list_bias_reports(
        self,
        community_id: Optional[str] = None,
        status: Optional[BiasReportStatus] = None,
        bias_detected_only: bool = False,
        limit: int = 20,
    ) -> List[BiasDetectionReport]:
        """List bias detection reports"""
        conn = self._get_connection()
        try:
            query = "SELECT * FROM bias_detection_reports WHERE 1=1"
            params: List[Any] = []

            if community_id:
                query += " AND community_id = ?"
                params.append(community_id)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if bias_detected_only:
                query += " AND bias_detected = TRUE"

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [BiasDetectionReport.from_dict(dict(row)) for row in rows]
        finally:
            conn.close()

    # ==================== Transparency Preferences ====================

    async def get_transparency_preferences(self, user_id: str) -> TransparencyPreferences:
        """Get user transparency preferences (or default)"""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM transparency_preferences WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if not row:
                # Return default preferences
                return TransparencyPreferences(user_id=user_id)

            return TransparencyPreferences.from_dict(dict(row))
        finally:
            conn.close()

    async def update_transparency_preferences(
        self, prefs: TransparencyPreferences
    ) -> TransparencyPreferences:
        """Update user transparency preferences"""
        conn = self._get_connection()
        try:
            # Upsert
            conn.execute(
                """
                INSERT INTO transparency_preferences (
                    user_id, detail_level, show_score_breakdown, show_weights,
                    show_rejection_reasons, receive_bias_reports,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    detail_level = excluded.detail_level,
                    show_score_breakdown = excluded.show_score_breakdown,
                    show_weights = excluded.show_weights,
                    show_rejection_reasons = excluded.show_rejection_reasons,
                    receive_bias_reports = excluded.receive_bias_reports,
                    updated_at = excluded.updated_at
                """,
                (
                    prefs.user_id,
                    prefs.detail_level.value,
                    prefs.show_score_breakdown,
                    prefs.show_weights,
                    prefs.show_rejection_reasons,
                    prefs.receive_bias_reports,
                    prefs.created_at.isoformat() if prefs.created_at else datetime.now(UTC).isoformat(),
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()
            return prefs
        finally:
            conn.close()
