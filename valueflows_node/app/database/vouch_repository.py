"""Repository for Vouch and Trust Score data access"""
import sqlite3
from typing import List, Optional, Union
from datetime import datetime, UTC
import uuid
from app.models.vouch import Vouch, TrustScore


class VouchRepository:
    """Database access for vouches and trust scores."""

    def __init__(self, db_path_or_conn: Union[str, sqlite3.Connection]):
        """Initialize repository with either a path or existing connection."""
        if isinstance(db_path_or_conn, sqlite3.Connection):
            self.conn = db_path_or_conn
            self.db_path = None
            self._owns_connection = False
        else:
            self.conn = None
            self.db_path = db_path_or_conn
            self._owns_connection = True
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection (either owned or external)."""
        if self.conn is not None:
            return self.conn
        return sqlite3.connect(self.db_path)

    def _close_conn(self, conn: sqlite3.Connection):
        """Close connection only if we own it."""
        if self._owns_connection and conn is not None:
            conn.close()

    def _init_tables(self):
        """Create vouch and trust_score tables if they don't exist."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Vouch table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vouches (
                id TEXT PRIMARY KEY,
                voucher_id TEXT NOT NULL,
                vouchee_id TEXT NOT NULL,
                context TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                revoked_reason TEXT,
                UNIQUE(voucher_id, vouchee_id)
            )
        """)

        # Trust scores table (computed and cached)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trust_scores (
                user_id TEXT PRIMARY KEY,
                computed_trust REAL NOT NULL,
                vouch_chains_json TEXT,
                best_chain_distance INTEGER,
                is_genesis INTEGER DEFAULT 0,
                last_computed TEXT NOT NULL,
                vouch_count INTEGER DEFAULT 0,
                revocation_count INTEGER DEFAULT 0
            )
        """)

        # Genesis nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genesis_nodes (
                user_id TEXT PRIMARY KEY,
                added_at TEXT NOT NULL,
                added_by TEXT,
                notes TEXT
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vouches_vouchee ON vouches(vouchee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vouches_voucher ON vouches(voucher_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vouches_revoked ON vouches(revoked)")

        conn.commit()
        self._close_conn(conn)

    def create_vouch(self, voucher_id: str, vouchee_id: str, context: str) -> Vouch:
        """Create a new vouch."""
        vouch_id = f"vouch-{uuid.uuid4()}"
        created_at = datetime.now(UTC).isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO vouches (id, voucher_id, vouchee_id, context, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (vouch_id, voucher_id, vouchee_id, context, created_at))
            conn.commit()
        except sqlite3.IntegrityError:
            # Vouch already exists
            cursor.execute("""
                SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
                FROM vouches WHERE voucher_id = ? AND vouchee_id = ?
            """, (voucher_id, vouchee_id))
            row = cursor.fetchone()
            self._close_conn(conn)
            if row:
                return self._row_to_vouch(row)
            raise
        finally:
            if conn:
                self._close_conn(conn)

        return Vouch(
            id=vouch_id,
            voucher_id=voucher_id,
            vouchee_id=vouchee_id,
            context=context,
            created_at=datetime.fromisoformat(created_at),
            revoked=False,
        )

    def get_vouch(self, vouch_id: str) -> Optional[Vouch]:
        """Get a vouch by ID."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
            FROM vouches WHERE id = ?
        """, (vouch_id,))

        row = cursor.fetchone()
        self._close_conn(conn)

        if not row:
            return None

        return self._row_to_vouch(row)

    def get_vouches_for_user(self, user_id: str, include_revoked: bool = False) -> List[Vouch]:
        """Get all vouches received by a user."""
        conn = self._get_conn()
        cursor = conn.cursor()

        if include_revoked:
            cursor.execute("""
                SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
                FROM vouches WHERE vouchee_id = ?
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
                FROM vouches WHERE vouchee_id = ? AND revoked = 0
            """, (user_id,))

        rows = cursor.fetchall()
        self._close_conn(conn)

        return [self._row_to_vouch(row) for row in rows]

    def get_vouches_by_user(self, user_id: str) -> List[Vouch]:
        """Get all vouches given by a user."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
            FROM vouches WHERE voucher_id = ?
        """, (user_id,))

        rows = cursor.fetchall()
        self._close_conn(conn)

        return [self._row_to_vouch(row) for row in rows]

    def get_vouches_since(self, user_id: str, since: datetime) -> List[Vouch]:
        """Get all vouches created by a user since a specific datetime.

        Args:
            user_id: The voucher's user ID
            since: Only return vouches created after this datetime

        Returns:
            List of Vouch objects created since the given datetime
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, voucher_id, vouchee_id, context, created_at, revoked, revoked_at, revoked_reason
            FROM vouches
            WHERE voucher_id = ? AND created_at >= ?
        """, (user_id, since.isoformat()))

        rows = cursor.fetchall()
        self._close_conn(conn)

        return [self._row_to_vouch(row) for row in rows]

    def revoke_vouch(self, vouch_id: str, reason: str) -> bool:
        """Revoke a vouch."""
        conn = self._get_conn()
        cursor = conn.cursor()

        revoked_at = datetime.now(UTC).isoformat()
        cursor.execute("""
            UPDATE vouches
            SET revoked = 1, revoked_at = ?, revoked_reason = ?
            WHERE id = ?
        """, (revoked_at, reason, vouch_id))

        updated = cursor.rowcount > 0
        conn.commit()
        self._close_conn(conn)

        return updated

    def add_genesis_node(self, user_id: str, added_by: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Add a user as a genesis node (trusted seed)."""
        conn = self._get_conn()
        cursor = conn.cursor()

        added_at = datetime.now(UTC).isoformat()

        try:
            cursor.execute("""
                INSERT INTO genesis_nodes (user_id, added_at, added_by, notes)
                VALUES (?, ?, ?, ?)
            """, (user_id, added_at, added_by, notes))
            conn.commit()
            result = True
        except sqlite3.IntegrityError:
            result = False  # Already a genesis node
        finally:
            self._close_conn(conn)

        return result

    def get_genesis_nodes(self) -> List[str]:
        """Get list of all genesis node user IDs."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM genesis_nodes")
        rows = cursor.fetchall()
        self._close_conn(conn)

        return [row[0] for row in rows]

    def is_genesis_node(self, user_id: str) -> bool:
        """Check if a user is a genesis node."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM genesis_nodes WHERE user_id = ?", (user_id,))
        result = cursor.fetchone() is not None
        self._close_conn(conn)

        return result

    def save_trust_score(self, trust_score: TrustScore):
        """Save a computed trust score to database (for caching)."""
        import json

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO trust_scores
            (user_id, computed_trust, vouch_chains_json, best_chain_distance,
             is_genesis, last_computed, vouch_count, revocation_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trust_score.user_id,
            trust_score.computed_trust,
            json.dumps(trust_score.vouch_chains),
            trust_score.best_chain_distance,
            1 if trust_score.is_genesis else 0,
            trust_score.last_computed.isoformat(),
            trust_score.vouch_count,
            trust_score.revocation_count,
        ))

        conn.commit()
        self._close_conn(conn)

    def get_trust_score(self, user_id: str) -> Optional[TrustScore]:
        """Get cached trust score for a user."""
        import json

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, computed_trust, vouch_chains_json, best_chain_distance,
                   is_genesis, last_computed, vouch_count, revocation_count
            FROM trust_scores WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        self._close_conn(conn)

        if not row:
            return None

        return TrustScore(
            user_id=row[0],
            computed_trust=row[1],
            vouch_chains=json.loads(row[2]) if row[2] else [],
            best_chain_distance=row[3],
            is_genesis=bool(row[4]),
            last_computed=datetime.fromisoformat(row[5]),
            vouch_count=row[6],
            revocation_count=row[7],
        )

    def _row_to_vouch(self, row) -> Vouch:
        """Convert database row to Vouch model."""
        return Vouch(
            id=row[0],
            voucher_id=row[1],
            vouchee_id=row[2],
            context=row[3],
            created_at=datetime.fromisoformat(row[4]),
            revoked=bool(row[5]),
            revoked_at=datetime.fromisoformat(row[6]) if row[6] else None,
            revoked_reason=row[7],
        )
