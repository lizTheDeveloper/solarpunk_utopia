"""Fork Rights Service - GAP-65

Business logic for data export and community forking.
"""
import uuid
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.models.fork_rights import (
    DataExportRequest,
    DataExport,
    ConnectionExportConsent,
    CommunityFork,
    ForkInvitation,
    ExitRecord
)
from app.repositories.fork_rights_repository import ForkRightsRepository


class ForkRightsService:
    """Service for fork rights operations."""

    def __init__(self, db_path: str = "data/valueflows.db"):
        self.db_path = db_path
        self.repo = ForkRightsRepository(db_path)

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Data Export
    def request_data_export(
        self,
        user_id: str,
        export_type: str
    ) -> DataExportRequest:
        """Request a data export.

        export_type: "data_only", "with_connections", or "fork"
        """
        request = DataExportRequest(
            user_id=user_id,
            export_type=export_type,
            requested_at=datetime.utcnow(),
            status="pending"
        )

        self.repo.create_export_request(request)

        # If requesting connection export, create consent requests
        if export_type == "with_connections":
            self._request_connection_consents(user_id)

        return request

    def _request_connection_consents(self, user_id: str):
        """Request consent from all connections to export."""
        # Get user's connections (people they've exchanged with)
        connections = self._get_user_connections(user_id)

        for connection_id in connections:
            consent = ConnectionExportConsent(
                id=f"consent-{uuid.uuid4()}",
                requester_id=user_id,
                connection_id=connection_id,
                asked_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            self.repo.create_consent_request(consent)

    def _get_user_connections(self, user_id: str) -> List[str]:
        """Get list of user IDs this user has connections with.

        Connections = people they've exchanged with or messaged.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get unique user IDs from exchanges
        cursor.execute("""
            SELECT DISTINCT
                CASE
                    WHEN provider_id = ? THEN receiver_id
                    WHEN receiver_id = ? THEN provider_id
                END as connection_id
            FROM exchanges
            WHERE provider_id = ? OR receiver_id = ?
        """, (user_id, user_id, user_id, user_id))

        rows = cursor.fetchall()
        conn.close()

        return [row["connection_id"] for row in rows if row["connection_id"]]

    def export_user_data(self, user_id: str) -> DataExport:
        """Generate complete data export for user.

        Returns all data that belongs to the user.
        Works OFFLINE - no cloud dependencies.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get user profile
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        profile_row = cursor.fetchone()
        my_profile = dict(profile_row) if profile_row else {}

        # Get offers
        cursor.execute("SELECT * FROM offers WHERE user_id = ?", (user_id,))
        my_offers = [dict(row) for row in cursor.fetchall()]

        # Get needs
        cursor.execute("SELECT * FROM needs WHERE user_id = ?", (user_id,))
        my_needs = [dict(row) for row in cursor.fetchall()]

        # Get exchanges
        cursor.execute("""
            SELECT * FROM exchanges
            WHERE provider_id = ? OR receiver_id = ?
        """, (user_id, user_id))
        my_exchanges = [dict(row) for row in cursor.fetchall()]

        # Get vouches given
        cursor.execute("SELECT * FROM vouches WHERE voucher_id = ?", (user_id,))
        my_vouches_given = [dict(row) for row in cursor.fetchall()]

        # Get vouches received
        cursor.execute("SELECT * FROM vouches WHERE vouchee_id = ?", (user_id,))
        my_vouches_received = [dict(row) for row in cursor.fetchall()]

        # Get connections (if consent approved)
        my_connections = []
        approved_connections = self.repo.get_approved_consents(user_id)
        if approved_connections:
            placeholders = ','.join('?' * len(approved_connections))
            cursor.execute(f"""
                SELECT * FROM users WHERE id IN ({placeholders})
            """, approved_connections)
            my_connections = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return DataExport(
            user_id=user_id,
            exported_at=datetime.utcnow(),
            my_profile=my_profile,
            my_offers=my_offers,
            my_needs=my_needs,
            my_exchanges=my_exchanges,
            my_vouches_given=my_vouches_given,
            my_vouches_received=my_vouches_received,
            my_connections=my_connections
        )

    def generate_export_file(self, user_id: str) -> str:
        """Generate SQLite export file for user.

        Returns: file path to export (local storage, not cloud)
        """
        export_data = self.export_user_data(user_id)

        # Create export-specific SQLite database
        export_path = f"data/exports/{user_id}-{datetime.utcnow().isoformat()}.db"
        export_conn = sqlite3.connect(export_path)
        export_cursor = export_conn.cursor()

        # Create tables
        export_cursor.execute("""
            CREATE TABLE profile (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE offers (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE needs (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE exchanges (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE vouches_given (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE vouches_received (
                data TEXT NOT NULL
            )
        """)
        export_cursor.execute("""
            CREATE TABLE connections (
                data TEXT NOT NULL
            )
        """)

        # Insert data
        export_cursor.execute("INSERT INTO profile (data) VALUES (?)",
                            (json.dumps(export_data.my_profile),))
        for offer in export_data.my_offers:
            export_cursor.execute("INSERT INTO offers (data) VALUES (?)",
                                (json.dumps(offer),))
        for need in export_data.my_needs:
            export_cursor.execute("INSERT INTO needs (data) VALUES (?)",
                                (json.dumps(need),))
        for exchange in export_data.my_exchanges:
            export_cursor.execute("INSERT INTO exchanges (data) VALUES (?)",
                                (json.dumps(exchange),))
        for vouch in export_data.my_vouches_given:
            export_cursor.execute("INSERT INTO vouches_given (data) VALUES (?)",
                                (json.dumps(vouch),))
        for vouch in export_data.my_vouches_received:
            export_cursor.execute("INSERT INTO vouches_received (data) VALUES (?)",
                                (json.dumps(vouch),))
        for connection in export_data.my_connections:
            export_cursor.execute("INSERT INTO connections (data) VALUES (?)",
                                (json.dumps(connection),))

        export_conn.commit()
        export_conn.close()

        return export_path

    # Connection Consent
    def respond_to_connection_consent(
        self,
        consent_id: str,
        response: str
    ):
        """Respond to a connection export consent request.

        response: "allow" or "deny"
        """
        self.repo.respond_to_consent(consent_id, response)

    def get_pending_consents(self, user_id: str) -> List[ConnectionExportConsent]:
        """Get pending consent requests for user."""
        return self.repo.get_pending_consents(user_id)

    # Community Forking
    def fork_community(
        self,
        user_id: str,
        original_cell_id: str,
        new_cell_name: str,
        fork_reason: Optional[str],
        members_to_invite: List[str]
    ) -> CommunityFork:
        """Fork a community.

        Creates new cell with forker as initial steward.
        Invites specified members (they can accept/decline).
        Original cell continues unchanged.
        """
        fork_id = f"fork-{uuid.uuid4()}"
        new_cell_id = f"cell-{uuid.uuid4()}"

        # Create new cell
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO cells (id, name, created_by, created_at)
            VALUES (?, ?, ?, ?)
        """, (new_cell_id, new_cell_name, user_id, datetime.utcnow().isoformat()))

        # Add forker as steward
        cursor.execute("""
            INSERT INTO cell_members (cell_id, user_id, role, joined_at)
            VALUES (?, ?, 'steward', ?)
        """, (new_cell_id, user_id, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        # Create fork record
        fork = CommunityFork(
            id=fork_id,
            original_cell_id=original_cell_id,
            new_cell_name=new_cell_name,
            new_cell_id=new_cell_id,
            forked_by=user_id,
            fork_reason=fork_reason,
            members_invited=members_to_invite,
            forked_at=datetime.utcnow()
        )

        self.repo.create_fork(fork)
        return fork

    def respond_to_fork_invitation(
        self,
        user_id: str,
        invitation_id: str,
        accept: bool
    ):
        """Respond to a fork invitation."""
        status = "accepted" if accept else "declined"
        self.repo.respond_to_fork_invitation(invitation_id, status)

        if accept:
            # Add user to new cell
            # Get fork details
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT fi.fork_id, cf.new_cell_id
                FROM fork_invitations fi
                JOIN community_forks cf ON fi.fork_id = cf.id
                WHERE fi.id = ?
            """, (invitation_id,))

            row = cursor.fetchone()
            if row:
                new_cell_id = row["new_cell_id"]
                cursor.execute("""
                    INSERT INTO cell_members (cell_id, user_id, role, joined_at)
                    VALUES (?, ?, 'member', ?)
                """, (new_cell_id, user_id, datetime.utcnow().isoformat()))

                conn.commit()

            conn.close()

    def get_pending_fork_invitations(self, user_id: str) -> List[ForkInvitation]:
        """Get pending fork invitations."""
        return self.repo.get_pending_fork_invitations(user_id)

    # Exit
    def leave_community(
        self,
        user_id: str,
        cell_id: str
    ):
        """Leave a community.

        No exit interview. No surveillance. Just leave.
        """
        # Remove from cell
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM cell_members
            WHERE cell_id = ? AND user_id = ?
        """, (cell_id, user_id))

        conn.commit()
        conn.close()

        # Record exit (minimal)
        exit_record = ExitRecord(
            user_id=user_id,
            cell_id=cell_id,
            left_at=datetime.utcnow()
        )
        self.repo.record_exit(exit_record)

    # Cleanup
    def cleanup_expired_data(self):
        """Remove expired consent requests and declined invitations.

        Data minimization - don't keep unnecessary records.
        """
        return self.repo.cleanup_expired_invitations()
