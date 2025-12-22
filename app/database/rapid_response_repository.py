"""Repository for Rapid Response data access

CRITICAL: This handles sensitive alert data. Auto-purge is MANDATORY.
All location data, responder info, and media purged 24 hours after resolution.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, UTC
import uuid

from app.models.rapid_response import (
    RapidAlert,
    AlertResponder,
    AlertUpdate,
    AlertMedia,
    AfterActionReview,
    AlertLevel,
    AlertType,
    AlertStatus,
    ResponderStatus,
    ResponderRole,
)


class RapidResponseRepository:
    """Database access for rapid response coordination."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ===== Rapid Alerts =====

    def create_alert(self, alert: RapidAlert) -> RapidAlert:
        """Create a new rapid alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rapid_alerts (
                id, alert_type, alert_level, status,
                reported_by, cell_id,
                location_hint, coordinates,
                description, people_affected,
                coordinator_id, coordinator_claimed_at,
                resolved_at, resolution_notes,
                confirmed, confirmed_by, confirmed_at, auto_downgrade_at,
                bundle_id, propagation_radius_km,
                purge_at, created_at, updated_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.alert_type.value,
            alert.alert_level.value,
            alert.status.value,
            alert.reported_by,
            alert.cell_id,
            alert.location_hint,
            json.dumps(alert.coordinates) if alert.coordinates else None,
            alert.description,
            alert.people_affected,
            alert.coordinator_id,
            alert.coordinator_claimed_at.isoformat() if alert.coordinator_claimed_at else None,
            alert.resolved_at.isoformat() if alert.resolved_at else None,
            alert.resolution_notes,
            1 if alert.confirmed else 0,
            alert.confirmed_by,
            alert.confirmed_at.isoformat() if alert.confirmed_at else None,
            alert.auto_downgrade_at.isoformat() if alert.auto_downgrade_at else None,
            alert.bundle_id,
            alert.propagation_radius_km,
            alert.purge_at.isoformat() if alert.purge_at else None,
            alert.created_at.isoformat(),
            alert.updated_at.isoformat(),
            alert.expires_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return alert

    def get_alert(self, alert_id: str) -> Optional[RapidAlert]:
        """Get an alert by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM rapid_alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_alert(row)

    def get_active_alerts(self, cell_id: str) -> List[RapidAlert]:
        """Get all active alerts for a cell."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM rapid_alerts
            WHERE cell_id = ? AND status = 'active'
            ORDER BY created_at DESC
        """, (cell_id,))

        alerts = [self._row_to_alert(row) for row in cursor.fetchall()]
        conn.close()
        return alerts

    def get_alerts_by_status(self, status: AlertStatus, limit: int = 50) -> List[RapidAlert]:
        """Get alerts by status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM rapid_alerts
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (status.value, limit))

        alerts = [self._row_to_alert(row) for row in cursor.fetchall()]
        conn.close()
        return alerts

    def update_alert(self, alert: RapidAlert) -> RapidAlert:
        """Update an existing alert."""
        alert.updated_at = datetime.now(UTC)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rapid_alerts SET
                alert_level = ?,
                status = ?,
                coordinator_id = ?,
                coordinator_claimed_at = ?,
                resolved_at = ?,
                resolution_notes = ?,
                confirmed = ?,
                confirmed_by = ?,
                confirmed_at = ?,
                auto_downgrade_at = ?,
                bundle_id = ?,
                purge_at = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            alert.alert_level.value,
            alert.status.value,
            alert.coordinator_id,
            alert.coordinator_claimed_at.isoformat() if alert.coordinator_claimed_at else None,
            alert.resolved_at.isoformat() if alert.resolved_at else None,
            alert.resolution_notes,
            1 if alert.confirmed else 0,
            alert.confirmed_by,
            alert.confirmed_at.isoformat() if alert.confirmed_at else None,
            alert.auto_downgrade_at.isoformat() if alert.auto_downgrade_at else None,
            alert.bundle_id,
            alert.purge_at.isoformat() if alert.purge_at else None,
            alert.updated_at.isoformat(),
            alert.id,
        ))

        conn.commit()
        conn.close()
        return alert

    def _row_to_alert(self, row: sqlite3.Row) -> RapidAlert:
        """Convert database row to RapidAlert model."""
        return RapidAlert(
            id=row['id'],
            alert_type=AlertType(row['alert_type']),
            alert_level=AlertLevel(row['alert_level']),
            status=AlertStatus(row['status']),
            reported_by=row['reported_by'],
            cell_id=row['cell_id'],
            location_hint=row['location_hint'],
            coordinates=json.loads(row['coordinates']) if row['coordinates'] else None,
            description=row['description'],
            people_affected=row['people_affected'],
            coordinator_id=row['coordinator_id'],
            coordinator_claimed_at=datetime.fromisoformat(row['coordinator_claimed_at']) if row['coordinator_claimed_at'] else None,
            resolved_at=datetime.fromisoformat(row['resolved_at']) if row['resolved_at'] else None,
            resolution_notes=row['resolution_notes'],
            confirmed=bool(row['confirmed']),
            confirmed_by=row['confirmed_by'],
            confirmed_at=datetime.fromisoformat(row['confirmed_at']) if row['confirmed_at'] else None,
            auto_downgrade_at=datetime.fromisoformat(row['auto_downgrade_at']) if row['auto_downgrade_at'] else None,
            bundle_id=row['bundle_id'],
            propagation_radius_km=row['propagation_radius_km'],
            purge_at=datetime.fromisoformat(row['purge_at']) if row['purge_at'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            expires_at=datetime.fromisoformat(row['expires_at']),
        )

    # ===== Alert Responders =====

    def add_responder(self, responder: AlertResponder) -> AlertResponder:
        """Add a responder to an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alert_responders (
                id, alert_id, user_id,
                status, role,
                eta_minutes, notes,
                responded_at, arrived_at, departed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            responder.id,
            responder.alert_id,
            responder.user_id,
            responder.status.value,
            responder.role.value,
            responder.eta_minutes,
            responder.notes,
            responder.responded_at.isoformat(),
            responder.arrived_at.isoformat() if responder.arrived_at else None,
            responder.departed_at.isoformat() if responder.departed_at else None,
        ))

        conn.commit()
        conn.close()
        return responder

    def get_alert_responders(self, alert_id: str) -> List[AlertResponder]:
        """Get all responders for an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alert_responders
            WHERE alert_id = ?
            ORDER BY responded_at ASC
        """, (alert_id,))

        responders = [self._row_to_responder(row) for row in cursor.fetchall()]
        conn.close()
        return responders

    def update_responder(self, responder: AlertResponder) -> AlertResponder:
        """Update a responder's status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE alert_responders SET
                status = ?,
                eta_minutes = ?,
                notes = ?,
                arrived_at = ?,
                departed_at = ?
            WHERE id = ?
        """, (
            responder.status.value,
            responder.eta_minutes,
            responder.notes,
            responder.arrived_at.isoformat() if responder.arrived_at else None,
            responder.departed_at.isoformat() if responder.departed_at else None,
            responder.id,
        ))

        conn.commit()
        conn.close()
        return responder

    def _row_to_responder(self, row: sqlite3.Row) -> AlertResponder:
        """Convert database row to AlertResponder model."""
        return AlertResponder(
            id=row['id'],
            alert_id=row['alert_id'],
            user_id=row['user_id'],
            status=ResponderStatus(row['status']),
            role=ResponderRole(row['role']),
            eta_minutes=row['eta_minutes'],
            notes=row['notes'],
            responded_at=datetime.fromisoformat(row['responded_at']),
            arrived_at=datetime.fromisoformat(row['arrived_at']) if row['arrived_at'] else None,
            departed_at=datetime.fromisoformat(row['departed_at']) if row['departed_at'] else None,
        )

    # ===== Alert Updates =====

    def add_update(self, update: AlertUpdate) -> AlertUpdate:
        """Add a status update to an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alert_updates (
                id, alert_id, posted_by,
                update_type, message,
                new_alert_level, bundle_id, posted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            update.id,
            update.alert_id,
            update.posted_by,
            update.update_type,
            update.message,
            update.new_alert_level.value if update.new_alert_level else None,
            update.bundle_id,
            update.posted_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return update

    def get_alert_updates(self, alert_id: str) -> List[AlertUpdate]:
        """Get all updates for an alert (chronological timeline)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alert_updates
            WHERE alert_id = ?
            ORDER BY posted_at ASC
        """, (alert_id,))

        updates = [self._row_to_update(row) for row in cursor.fetchall()]
        conn.close()
        return updates

    def _row_to_update(self, row: sqlite3.Row) -> AlertUpdate:
        """Convert database row to AlertUpdate model."""
        return AlertUpdate(
            id=row['id'],
            alert_id=row['alert_id'],
            posted_by=row['posted_by'],
            update_type=row['update_type'],
            message=row['message'],
            new_alert_level=AlertLevel(row['new_alert_level']) if row['new_alert_level'] else None,
            bundle_id=row['bundle_id'],
            posted_at=datetime.fromisoformat(row['posted_at']),
        )

    # ===== Alert Media =====

    def add_media(self, media: AlertMedia) -> AlertMedia:
        """Add media documentation to an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alert_media (
                id, alert_id, captured_by,
                media_type, encrypted_data, storage_bundle_id, file_size_bytes,
                encrypted_metadata,
                shared_with_legal, shared_with_media,
                purge_at, captured_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            media.id,
            media.alert_id,
            media.captured_by,
            media.media_type,
            media.encrypted_data,
            media.storage_bundle_id,
            media.file_size_bytes,
            media.encrypted_metadata,
            1 if media.shared_with_legal else 0,
            1 if media.shared_with_media else 0,
            media.purge_at.isoformat(),
            media.captured_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return media

    def get_alert_media(self, alert_id: str) -> List[AlertMedia]:
        """Get all media for an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alert_media
            WHERE alert_id = ?
            ORDER BY captured_at ASC
        """, (alert_id,))

        media_list = [self._row_to_media(row) for row in cursor.fetchall()]
        conn.close()
        return media_list

    def _row_to_media(self, row: sqlite3.Row) -> AlertMedia:
        """Convert database row to AlertMedia model."""
        return AlertMedia(
            id=row['id'],
            alert_id=row['alert_id'],
            captured_by=row['captured_by'],
            media_type=row['media_type'],
            encrypted_data=row['encrypted_data'],
            storage_bundle_id=row['storage_bundle_id'],
            file_size_bytes=row['file_size_bytes'],
            encrypted_metadata=row['encrypted_metadata'],
            shared_with_legal=bool(row['shared_with_legal']),
            shared_with_media=bool(row['shared_with_media']),
            purge_at=datetime.fromisoformat(row['purge_at']),
            captured_at=datetime.fromisoformat(row['captured_at']),
        )

    # ===== After Action Reviews =====

    def add_review(self, review: AfterActionReview) -> AfterActionReview:
        """Add an after-action review for a resolved alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO after_action_reviews (
                id, alert_id, completed_by,
                response_time_minutes, total_responders,
                successes, challenges, lessons, recommendations,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review.id,
            review.alert_id,
            review.completed_by,
            review.response_time_minutes,
            review.total_responders,
            review.successes,
            review.challenges,
            review.lessons,
            review.recommendations,
            review.completed_at.isoformat(),
        ))

        conn.commit()
        conn.close()
        return review

    def get_review(self, alert_id: str) -> Optional[AfterActionReview]:
        """Get after-action review for an alert."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM after_action_reviews
            WHERE alert_id = ?
        """, (alert_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return AfterActionReview(
            id=row['id'],
            alert_id=row['alert_id'],
            completed_by=row['completed_by'],
            response_time_minutes=row['response_time_minutes'],
            total_responders=row['total_responders'],
            successes=row['successes'],
            challenges=row['challenges'],
            lessons=row['lessons'],
            recommendations=row['recommendations'],
            completed_at=datetime.fromisoformat(row['completed_at']),
        )

    # ===== Auto-Purge =====

    def purge_old_alerts(self) -> dict:
        """Purge alerts and related data past their purge_at timestamp.

        Returns counts of what was purged.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now(UTC).isoformat()

        # Purge media first (foreign key cascade handles)
        cursor.execute("DELETE FROM alert_media WHERE purge_at <= ?", (now,))
        media_purged = cursor.rowcount

        # Purge alerts (cascade will handle responders, updates, reviews)
        cursor.execute("DELETE FROM rapid_alerts WHERE purge_at <= ?", (now,))
        alerts_purged = cursor.rowcount

        conn.commit()
        conn.close()

        return {
            "alerts_purged": alerts_purged,
            "media_purged": media_purged,
        }

    def get_alerts_needing_downgrade(self) -> List[RapidAlert]:
        """Get CRITICAL alerts that need auto-downgrade (unconfirmed past 5 min)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now(UTC).isoformat()

        cursor.execute("""
            SELECT * FROM rapid_alerts
            WHERE alert_level = 'critical'
            AND confirmed = 0
            AND auto_downgrade_at <= ?
            AND status = 'active'
        """, (now,))

        alerts = [self._row_to_alert(row) for row in cursor.fetchall()]
        conn.close()
        return alerts
