"""Repository for Sanctuary Network data access

CRITICAL: This handles sensitive data. Auto-purge is MANDATORY.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.sanctuary import (
    SanctuaryResource,
    SanctuaryRequest,
    SanctuaryMatch,
    RapidAlert,
    SensitivityLevel,
    SanctuaryResourceType,
    VerificationStatus,
)


class SanctuaryRepository:
    """Database access for sanctuary network."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Create sanctuary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sanctuary resources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sanctuary_resources (
                id TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                sensitivity TEXT NOT NULL,
                offered_by TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                description TEXT NOT NULL,
                capacity INTEGER,
                duration_days INTEGER,
                verification_status TEXT NOT NULL,
                verified_by TEXT,
                verified_at TEXT,
                verification_notes TEXT,
                available INTEGER DEFAULT 1,
                available_from TEXT NOT NULL,
                available_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                purge_at TEXT
            )
        """)

        # Sanctuary requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sanctuary_requests (
                id TEXT PRIMARY KEY,
                request_type TEXT NOT NULL,
                urgency TEXT NOT NULL,
                requested_by TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                verified_by TEXT NOT NULL,
                description TEXT NOT NULL,
                people_count INTEGER DEFAULT 1,
                duration_needed_days INTEGER,
                location_hint TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                matched_resource_id TEXT,
                completed_at TEXT,
                purge_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        # Sanctuary matches table (auto-purged)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sanctuary_matches (
                id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                coordinated_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                completed_at TEXT,
                purge_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # Rapid alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rapid_alerts (
                id TEXT PRIMARY KEY,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                reported_by TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                location_hint TEXT NOT NULL,
                coordinates_json TEXT,
                description TEXT NOT NULL,
                people_affected INTEGER,
                responders_json TEXT NOT NULL DEFAULT '[]',
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT,
                purge_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_cell ON sanctuary_resources(cell_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_sensitivity ON sanctuary_resources(sensitivity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_resources_purge ON sanctuary_resources(purge_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_cell ON sanctuary_requests(cell_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_status ON sanctuary_requests(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_requests_purge ON sanctuary_requests(purge_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sanctuary_matches_purge ON sanctuary_matches(purge_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapid_alerts_cell ON rapid_alerts(cell_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapid_alerts_purge ON rapid_alerts(purge_at)")

        conn.commit()
        conn.close()

    # ===== Sanctuary Resources =====

    def create_resource(self, resource: SanctuaryResource) -> SanctuaryResource:
        """Create a new sanctuary resource offer."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sanctuary_resources
            (id, resource_type, sensitivity, offered_by, cell_id, description,
             capacity, duration_days, verification_status, verified_by, verified_at,
             verification_notes, available, available_from, available_until,
             created_at, updated_at, purge_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resource.id,
            resource.resource_type.value,
            resource.sensitivity.value,
            resource.offered_by,
            resource.cell_id,
            resource.description,
            resource.capacity,
            resource.duration_days,
            resource.verification_status.value,
            resource.verified_by,
            resource.verified_at.isoformat() if resource.verified_at else None,
            resource.verification_notes,
            int(resource.available),
            resource.available_from.isoformat(),
            resource.available_until.isoformat() if resource.available_until else None,
            resource.created_at.isoformat(),
            resource.updated_at.isoformat(),
            resource.purge_at.isoformat() if resource.purge_at else None
        ))

        conn.commit()
        conn.close()
        return resource

    def get_resources_by_cell(
        self,
        cell_id: str,
        sensitivity: Optional[SensitivityLevel] = None,
        verified_only: bool = True
    ) -> List[SanctuaryResource]:
        """Get sanctuary resources for a cell."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, resource_type, sensitivity, offered_by, cell_id, description,
                   capacity, duration_days, verification_status, verified_by, verified_at,
                   verification_notes, available, available_from, available_until,
                   created_at, updated_at, purge_at
            FROM sanctuary_resources
            WHERE cell_id = ? AND available = 1
        """
        params = [cell_id]

        if sensitivity:
            query += " AND sensitivity = ?"
            params.append(sensitivity.value)

        if verified_only:
            query += " AND verification_status = 'verified'"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_resource(row) for row in rows]

    def verify_resource(self, resource_id: str, verified_by: str, notes: str):
        """Mark a resource as verified by a steward."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        verified_at = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE sanctuary_resources
            SET verification_status = 'verified',
                verified_by = ?,
                verified_at = ?,
                verification_notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (verified_by, verified_at, notes, verified_at, resource_id))

        conn.commit()
        conn.close()

    # ===== Sanctuary Requests =====

    def create_request(self, request: SanctuaryRequest) -> SanctuaryRequest:
        """Create a new sanctuary request."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sanctuary_requests
            (id, request_type, urgency, requested_by, cell_id, verified_by,
             description, people_count, duration_needed_days, location_hint,
             status, matched_resource_id, completed_at, purge_at, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.id,
            request.request_type.value,
            request.urgency,
            request.requested_by,
            request.cell_id,
            request.verified_by,
            request.description,
            request.people_count,
            request.duration_needed_days,
            request.location_hint,
            request.status,
            request.matched_resource_id,
            request.completed_at.isoformat() if request.completed_at else None,
            request.purge_at.isoformat(),
            request.created_at.isoformat(),
            request.expires_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return request

    def get_pending_requests(self, cell_id: str) -> List[SanctuaryRequest]:
        """Get pending sanctuary requests for a cell."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, request_type, urgency, requested_by, cell_id, verified_by,
                   description, people_count, duration_needed_days, location_hint,
                   status, matched_resource_id, completed_at, purge_at, created_at, expires_at
            FROM sanctuary_requests
            WHERE cell_id = ? AND status = 'pending'
            ORDER BY urgency DESC, created_at ASC
        """, (cell_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_request(row) for row in rows]

    def mark_request_completed(self, request_id: str):
        """Mark a sanctuary request as completed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        completed_at = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE sanctuary_requests
            SET status = 'completed', completed_at = ?
            WHERE id = ?
        """, (completed_at, request_id))

        conn.commit()
        conn.close()

    # ===== Sanctuary Matches =====

    def create_match(self, match: SanctuaryMatch) -> SanctuaryMatch:
        """Create a sanctuary match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sanctuary_matches
            (id, request_id, resource_id, cell_id, coordinated_by,
             status, completed_at, purge_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.id,
            match.request_id,
            match.resource_id,
            match.cell_id,
            match.coordinated_by,
            match.status,
            match.completed_at.isoformat() if match.completed_at else None,
            match.purge_at.isoformat(),
            match.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return match

    def mark_match_completed(self, match_id: str):
        """Mark a match as completed (triggers 24h purge timer)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        from datetime import timedelta
        completed_at = datetime.utcnow()
        purge_at = completed_at + timedelta(hours=24)

        cursor.execute("""
            UPDATE sanctuary_matches
            SET status = 'completed',
                completed_at = ?,
                purge_at = ?
            WHERE id = ?
        """, (completed_at.isoformat(), purge_at.isoformat(), match_id))

        conn.commit()
        conn.close()

    # ===== Rapid Alerts =====

    def create_alert(self, alert: RapidAlert) -> RapidAlert:
        """Create a rapid alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rapid_alerts
            (id, alert_type, severity, reported_by, cell_id, location_hint,
             coordinates_json, description, people_affected, responders_json,
             resolved, resolved_at, purge_at, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.alert_type,
            alert.severity,
            alert.reported_by,
            alert.cell_id,
            alert.location_hint,
            json.dumps(alert.coordinates) if alert.coordinates else None,
            alert.description,
            alert.people_affected,
            json.dumps(alert.responders),
            int(alert.resolved),
            alert.resolved_at.isoformat() if alert.resolved_at else None,
            alert.purge_at.isoformat(),
            alert.created_at.isoformat(),
            alert.expires_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return alert

    def get_active_alerts(self, cell_id: str) -> List[RapidAlert]:
        """Get active alerts for a cell."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute("""
            SELECT id, alert_type, severity, reported_by, cell_id, location_hint,
                   coordinates_json, description, people_affected, responders_json,
                   resolved, resolved_at, purge_at, created_at, expires_at
            FROM rapid_alerts
            WHERE cell_id = ? AND resolved = 0 AND expires_at > ?
            ORDER BY severity DESC, created_at DESC
        """, (cell_id, now))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_alert(row) for row in rows]

    # ===== Auto-Purge Methods =====

    def purge_old_records(self) -> dict:
        """Purge old sanctuary records based on purge_at timestamps.

        Returns count of purged records.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        # Purge old matches
        cursor.execute("DELETE FROM sanctuary_matches WHERE purge_at <= ?", (now,))
        matches_purged = cursor.rowcount

        # Purge old requests
        cursor.execute("DELETE FROM sanctuary_requests WHERE purge_at <= ?", (now,))
        requests_purged = cursor.rowcount

        # Purge old resources (if they have purge_at set)
        cursor.execute("DELETE FROM sanctuary_resources WHERE purge_at <= ?", (now,))
        resources_purged = cursor.rowcount

        # Purge old alerts
        cursor.execute("DELETE FROM rapid_alerts WHERE purge_at <= ?", (now,))
        alerts_purged = cursor.rowcount

        conn.commit()
        conn.close()

        return {
            "matches_purged": matches_purged,
            "requests_purged": requests_purged,
            "resources_purged": resources_purged,
            "alerts_purged": alerts_purged
        }

    # ===== Helper Methods =====

    def _row_to_resource(self, row) -> SanctuaryResource:
        """Convert database row to SanctuaryResource."""
        return SanctuaryResource(
            id=row[0],
            resource_type=SanctuaryResourceType(row[1]),
            sensitivity=SensitivityLevel(row[2]),
            offered_by=row[3],
            cell_id=row[4],
            description=row[5],
            capacity=row[6],
            duration_days=row[7],
            verification_status=VerificationStatus(row[8]),
            verified_by=row[9],
            verified_at=datetime.fromisoformat(row[10]) if row[10] else None,
            verification_notes=row[11],
            available=bool(row[12]),
            available_from=datetime.fromisoformat(row[13]),
            available_until=datetime.fromisoformat(row[14]) if row[14] else None,
            created_at=datetime.fromisoformat(row[15]),
            updated_at=datetime.fromisoformat(row[16]),
            purge_at=datetime.fromisoformat(row[17]) if row[17] else None
        )

    def _row_to_request(self, row) -> SanctuaryRequest:
        """Convert database row to SanctuaryRequest."""
        return SanctuaryRequest(
            id=row[0],
            request_type=SanctuaryResourceType(row[1]),
            urgency=row[2],
            requested_by=row[3],
            cell_id=row[4],
            verified_by=row[5],
            description=row[6],
            people_count=row[7],
            duration_needed_days=row[8],
            location_hint=row[9],
            status=row[10],
            matched_resource_id=row[11],
            completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
            purge_at=datetime.fromisoformat(row[13]),
            created_at=datetime.fromisoformat(row[14]),
            expires_at=datetime.fromisoformat(row[15])
        )

    def _row_to_alert(self, row) -> RapidAlert:
        """Convert database row to RapidAlert."""
        return RapidAlert(
            id=row[0],
            alert_type=row[1],
            severity=row[2],
            reported_by=row[3],
            cell_id=row[4],
            location_hint=row[5],
            coordinates=json.loads(row[6]) if row[6] else None,
            description=row[7],
            people_affected=row[8],
            responders=json.loads(row[9]) if row[9] else [],
            resolved=bool(row[10]),
            resolved_at=datetime.fromisoformat(row[11]) if row[11] else None,
            purge_at=datetime.fromisoformat(row[12]),
            created_at=datetime.fromisoformat(row[13]),
            expires_at=datetime.fromisoformat(row[14])
        )
