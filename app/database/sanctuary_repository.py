"""Repository for Sanctuary Network data access

CRITICAL: This handles sensitive data. Auto-purge is MANDATORY.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, UTC
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

    def _get_connection(self):
        """Get database connection with WAL mode for better concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_tables(self):
        """Create sanctuary tables if they don't exist."""
        conn = self._get_connection()
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
                purge_at TEXT,
                first_verified_at TEXT,
                last_check TEXT,
                expires_at TEXT,
                successful_uses INTEGER DEFAULT 0
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

        # Sanctuary verifications table (multi-steward verification)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sanctuary_verifications (
                id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                steward_id TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                verification_method TEXT NOT NULL,
                notes TEXT,
                escape_routes_verified INTEGER DEFAULT 0,
                capacity_verified INTEGER DEFAULT 0,
                buddy_protocol_available INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(resource_id, steward_id)
            )
        """)

        # Sanctuary uses table (for tracking successful uses)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sanctuary_uses (
                id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                request_id TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                outcome TEXT NOT NULL,
                purge_at TEXT NOT NULL,
                created_at TEXT NOT NULL
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()

        verified_at = datetime.now(UTC).isoformat()

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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()

        completed_at = datetime.now(UTC).isoformat()

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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()

        from datetime import timedelta
        completed_at = datetime.now(UTC)
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

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
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()

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

    # ===== Multi-Steward Verification (GAP-109) =====

    def create_verification(self, verification: 'VerificationRecord') -> 'VerificationRecord':
        """Create a verification record for a sanctuary resource."""
        from app.models.sanctuary import VerificationRecord

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sanctuary_verifications
            (id, resource_id, steward_id, verified_at, verification_method, notes,
             escape_routes_verified, capacity_verified, buddy_protocol_available, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            verification.id,
            verification.resource_id,
            verification.steward_id,
            verification.verified_at.isoformat(),
            verification.verification_method.value,
            verification.notes,
            int(verification.escape_routes_verified),
            int(verification.capacity_verified),
            int(verification.buddy_protocol_available),
            verification.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return verification

    def get_verifications_for_resource(self, resource_id: str) -> List['VerificationRecord']:
        """Get all verifications for a sanctuary resource."""
        from app.models.sanctuary import VerificationRecord, VerificationMethod

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, resource_id, steward_id, verified_at, verification_method, notes,
                   escape_routes_verified, capacity_verified, buddy_protocol_available, created_at
            FROM sanctuary_verifications
            WHERE resource_id = ?
            ORDER BY verified_at ASC
        """, (resource_id,))

        rows = cursor.fetchall()
        conn.close()

        verifications = []
        for row in rows:
            verifications.append(VerificationRecord(
                id=row[0],
                resource_id=row[1],
                steward_id=row[2],
                verified_at=datetime.fromisoformat(row[3]),
                verification_method=VerificationMethod(row[4]),
                notes=row[5],
                escape_routes_verified=bool(row[6]),
                capacity_verified=bool(row[7]),
                buddy_protocol_available=bool(row[8]),
                created_at=datetime.fromisoformat(row[9])
            ))

        return verifications

    def get_verification_aggregate(self, resource_id: str) -> Optional['SanctuaryVerification']:
        """Get verification aggregate (all verifications + metadata) for a resource."""
        from app.models.sanctuary import SanctuaryVerification

        # Get verifications
        verifications = self.get_verifications_for_resource(resource_id)

        # Get resource metadata for verification fields
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT first_verified_at, last_check, expires_at, successful_uses
            FROM sanctuary_resources
            WHERE id = ?
        """, (resource_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return SanctuaryVerification(
            resource_id=resource_id,
            verifications=verifications,
            first_verified_at=datetime.fromisoformat(row[0]) if row[0] else None,
            last_check=datetime.fromisoformat(row[1]) if row[1] else None,
            expires_at=datetime.fromisoformat(row[2]) if row[2] else None,
            successful_uses=row[3] or 0
        )

    def update_resource_verification_metadata(
        self,
        resource_id: str,
        first_verified_at: Optional[datetime],
        last_check: datetime,
        expires_at: datetime
    ):
        """Update verification metadata for a resource."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # If first_verified_at is provided, update it
        if first_verified_at:
            cursor.execute("""
                UPDATE sanctuary_resources
                SET first_verified_at = ?,
                    last_check = ?,
                    expires_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                first_verified_at.isoformat(),
                last_check.isoformat(),
                expires_at.isoformat(),
                datetime.now(UTC).isoformat(),
                resource_id
            ))
        else:
            # Just update last_check and expires_at
            cursor.execute("""
                UPDATE sanctuary_resources
                SET last_check = ?,
                    expires_at = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                last_check.isoformat(),
                expires_at.isoformat(),
                datetime.now(UTC).isoformat(),
                resource_id
            ))

        conn.commit()
        conn.close()

    def update_verification_status(
        self,
        resource_id: str,
        status: VerificationStatus
    ):
        """Update verification status for a resource."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sanctuary_resources
            SET verification_status = ?,
                updated_at = ?
            WHERE id = ?
        """, (status.value, datetime.now(UTC).isoformat(), resource_id))

        conn.commit()
        conn.close()

    def create_sanctuary_use(self, use: 'SanctuaryUse') -> 'SanctuaryUse':
        """Record a sanctuary use."""
        from app.models.sanctuary import SanctuaryUse

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sanctuary_uses
            (id, resource_id, request_id, completed_at, outcome, purge_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            use.id,
            use.resource_id,
            use.request_id,
            use.completed_at.isoformat(),
            use.outcome,
            use.purge_at.isoformat(),
            use.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return use

    def increment_successful_uses(self, resource_id: str):
        """Increment successful_uses counter for a resource."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sanctuary_resources
            SET successful_uses = successful_uses + 1,
                updated_at = ?
            WHERE id = ?
        """, (datetime.now(UTC).isoformat(), resource_id))

        conn.commit()
        conn.close()

    def get_resources_needing_verification(
        self,
        cell_id: str,
        exclude_steward_id: Optional[str] = None
    ) -> dict:
        """Get resources that need verification or re-verification.

        Returns:
            {
                'pending': [resources with only 1 verification],
                'expiring': [resources expiring in next 14 days]
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get resources needing 2nd verification (only 1 verification so far)
        # Exclude resources this steward has already verified
        if exclude_steward_id:
            cursor.execute("""
                SELECT DISTINCT r.id, r.resource_type, r.sensitivity, r.offered_by, r.cell_id, r.description,
                       r.capacity, r.duration_days, r.verification_status, r.verified_by, r.verified_at,
                       r.verification_notes, r.available, r.available_from, r.available_until,
                       r.created_at, r.updated_at, r.purge_at
                FROM sanctuary_resources r
                WHERE r.cell_id = ?
                  AND r.verification_status = 'pending'
                  AND r.id IN (
                      SELECT resource_id FROM sanctuary_verifications GROUP BY resource_id HAVING COUNT(*) = 1
                  )
                  AND r.id NOT IN (
                      SELECT resource_id FROM sanctuary_verifications WHERE steward_id = ?
                  )
                ORDER BY r.created_at DESC
            """, (cell_id, exclude_steward_id))
        else:
            cursor.execute("""
                SELECT DISTINCT r.id, r.resource_type, r.sensitivity, r.offered_by, r.cell_id, r.description,
                       r.capacity, r.duration_days, r.verification_status, r.verified_by, r.verified_at,
                       r.verification_notes, r.available, r.available_from, r.available_until,
                       r.created_at, r.updated_at, r.purge_at
                FROM sanctuary_resources r
                WHERE r.cell_id = ?
                  AND r.verification_status = 'pending'
                  AND r.id IN (
                      SELECT resource_id FROM sanctuary_verifications GROUP BY resource_id HAVING COUNT(*) = 1
                  )
                ORDER BY r.created_at DESC
            """, (cell_id,))

        pending_rows = cursor.fetchall()

        # Get resources expiring in next 14 days
        expires_soon = datetime.now(UTC) + timedelta(days=14)
        cursor.execute("""
            SELECT id, resource_type, sensitivity, offered_by, cell_id, description,
                   capacity, duration_days, verification_status, verified_by, verified_at,
                   verification_notes, available, available_from, available_until,
                   created_at, updated_at, purge_at
            FROM sanctuary_resources
            WHERE cell_id = ?
              AND verification_status = 'verified'
              AND expires_at IS NOT NULL
              AND expires_at <= ?
              AND expires_at > ?
            ORDER BY expires_at ASC
        """, (cell_id, expires_soon.isoformat(), datetime.now(UTC).isoformat()))

        expiring_rows = cursor.fetchall()

        conn.close()

        return {
            'pending': [self._row_to_resource(row) for row in pending_rows],
            'expiring': [self._row_to_resource(row) for row in expiring_rows]
        }
