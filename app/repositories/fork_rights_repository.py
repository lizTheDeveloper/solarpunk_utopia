"""Fork Rights Repository - GAP-65

Local-first data export and community forking.
All data stored in local SQLite, synced via DTN mesh.
"""
import sqlite3
import json
from datetime import datetime, timedelta, UTC
from typing import Optional, List
from app.models.fork_rights import (
    DataExportRequest,
    DataExport,
    ConnectionExportConsent,
    CommunityFork,
    ForkInvitation,
    ExitRecord
)


class ForkRightsRepository:
    """Repository for fork rights (data portability)."""

    def __init__(self, db_path: str = "data/valueflows.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_tables(self):
        """Initialize fork rights tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Data export requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_export_requests (
                user_id TEXT NOT NULL,
                export_type TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                export_url TEXT,
                completed_at TEXT,
                error_message TEXT,
                PRIMARY KEY (user_id, requested_at)
            )
        """)

        # Connection export consent requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_export_consents (
                id TEXT PRIMARY KEY,
                requester_id TEXT NOT NULL,
                connection_id TEXT NOT NULL,
                asked_at TEXT NOT NULL,
                response TEXT,
                responded_at TEXT,
                expires_at TEXT NOT NULL
            )
        """)

        # Community forks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_forks (
                id TEXT PRIMARY KEY,
                original_cell_id TEXT NOT NULL,
                new_cell_name TEXT NOT NULL,
                new_cell_id TEXT NOT NULL,
                forked_by TEXT NOT NULL,
                fork_reason TEXT,
                forked_at TEXT NOT NULL
            )
        """)

        # Fork invitations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fork_invitations (
                id TEXT PRIMARY KEY,
                fork_id TEXT NOT NULL,
                inviter_id TEXT NOT NULL,
                invitee_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                invited_at TEXT NOT NULL,
                responded_at TEXT,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (fork_id) REFERENCES community_forks(id)
            )
        """)

        # Exit records (minimal tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exit_records (
                user_id TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                left_at TEXT NOT NULL,
                PRIMARY KEY (user_id, cell_id, left_at)
            )
        """)

        conn.commit()
        conn.close()

    # Data Export
    def create_export_request(self, request: DataExportRequest) -> DataExportRequest:
        """Create a new data export request."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data_export_requests
            (user_id, export_type, requested_at, status)
            VALUES (?, ?, ?, ?)
        """, (
            request.user_id,
            request.export_type,
            request.requested_at.isoformat(),
            request.status
        ))

        conn.commit()
        conn.close()
        return request

    def get_export_request(self, user_id: str) -> Optional[DataExportRequest]:
        """Get most recent export request for user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM data_export_requests
            WHERE user_id = ?
            ORDER BY requested_at DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DataExportRequest(
            user_id=row["user_id"],
            export_type=row["export_type"],
            requested_at=datetime.fromisoformat(row["requested_at"]),
            status=row["status"],
            export_url=row["export_url"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            error_message=row["error_message"]
        )

    def update_export_status(
        self,
        user_id: str,
        requested_at: datetime,
        status: str,
        export_url: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update export request status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        completed_at = datetime.now(UTC).isoformat() if status == "complete" else None

        cursor.execute("""
            UPDATE data_export_requests
            SET status = ?, export_url = ?, completed_at = ?, error_message = ?
            WHERE user_id = ? AND requested_at = ?
        """, (status, export_url, completed_at, error_message, user_id, requested_at.isoformat()))

        conn.commit()
        conn.close()

    # Connection Export Consent
    def create_consent_request(self, consent: ConnectionExportConsent) -> ConnectionExportConsent:
        """Request consent to export a connection."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO connection_export_consents
            (id, requester_id, connection_id, asked_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            consent.id,
            consent.requester_id,
            consent.connection_id,
            consent.asked_at.isoformat(),
            consent.expires_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return consent

    def respond_to_consent(self, consent_id: str, response: str):
        """Respond to a connection export consent request."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE connection_export_consents
            SET response = ?, responded_at = ?
            WHERE id = ?
        """, (response, datetime.now(UTC).isoformat(), consent_id))

        conn.commit()
        conn.close()

    def get_pending_consents(self, user_id: str) -> List[ConnectionExportConsent]:
        """Get pending consent requests for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM connection_export_consents
            WHERE connection_id = ? AND response IS NULL
            ORDER BY asked_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        consents = []
        for row in rows:
            consents.append(ConnectionExportConsent(
                id=row["id"],
                requester_id=row["requester_id"],
                connection_id=row["connection_id"],
                asked_at=datetime.fromisoformat(row["asked_at"]),
                response=row["response"],
                responded_at=datetime.fromisoformat(row["responded_at"]) if row["responded_at"] else None,
                expires_at=datetime.fromisoformat(row["expires_at"])
            ))

        return consents

    def get_approved_consents(self, requester_id: str) -> List[str]:
        """Get list of connection IDs that approved export."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT connection_id FROM connection_export_consents
            WHERE requester_id = ? AND response = 'allow'
        """, (requester_id,))

        rows = cursor.fetchall()
        conn.close()

        return [row["connection_id"] for row in rows]

    # Community Forking
    def create_fork(self, fork: CommunityFork) -> CommunityFork:
        """Create a community fork."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO community_forks
            (id, original_cell_id, new_cell_name, new_cell_id, forked_by, fork_reason, forked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fork.id,
            fork.original_cell_id,
            fork.new_cell_name,
            fork.new_cell_id,
            fork.forked_by,
            fork.fork_reason,
            fork.forked_at.isoformat()
        ))

        # Create invitations (using same connection to avoid locks)
        for invitee_id in fork.members_invited:
            cursor.execute("""
                INSERT INTO fork_invitations
                (id, fork_id, inviter_id, invitee_id, status, invited_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{fork.id}-{invitee_id}",
                fork.id,
                fork.forked_by,
                invitee_id,
                "pending",
                datetime.now(UTC).isoformat(),
                (datetime.now(UTC) + timedelta(days=30)).isoformat()
            ))

        conn.commit()
        conn.close()
        return fork

    def create_fork_invitation(self, invitation: ForkInvitation) -> ForkInvitation:
        """Create a fork invitation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO fork_invitations
            (id, fork_id, inviter_id, invitee_id, status, invited_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            invitation.id,
            invitation.fork_id,
            invitation.inviter_id,
            invitation.invitee_id,
            invitation.status,
            invitation.invited_at.isoformat(),
            invitation.expires_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return invitation

    def respond_to_fork_invitation(self, invitation_id: str, status: str):
        """Respond to a fork invitation."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fork_invitations
            SET status = ?, responded_at = ?
            WHERE id = ?
        """, (status, datetime.now(UTC).isoformat(), invitation_id))

        conn.commit()
        conn.close()

    def get_pending_fork_invitations(self, user_id: str) -> List[ForkInvitation]:
        """Get pending fork invitations for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM fork_invitations
            WHERE invitee_id = ? AND status = 'pending'
            ORDER BY invited_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        invitations = []
        for row in rows:
            invitations.append(ForkInvitation(
                id=row["id"],
                fork_id=row["fork_id"],
                inviter_id=row["inviter_id"],
                invitee_id=row["invitee_id"],
                status=row["status"],
                invited_at=datetime.fromisoformat(row["invited_at"]),
                responded_at=datetime.fromisoformat(row["responded_at"]) if row["responded_at"] else None,
                expires_at=datetime.fromisoformat(row["expires_at"])
            ))

        return invitations

    def cleanup_expired_invitations(self):
        """Delete declined fork invitations past expiration."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM fork_invitations
            WHERE status = 'declined' AND expires_at < ?
        """, (datetime.now(UTC).isoformat(),))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    # Exit Records
    def record_exit(self, exit_record: ExitRecord):
        """Record that someone left a community (minimal tracking)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO exit_records (user_id, cell_id, left_at)
            VALUES (?, ?, ?)
        """, (
            exit_record.user_id,
            exit_record.cell_id,
            exit_record.left_at.isoformat()
        ))

        conn.commit()
        conn.close()
