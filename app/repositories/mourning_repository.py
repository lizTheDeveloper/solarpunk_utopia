"""Mourning Repository - GAP-67

Data layer for mourning periods and memorials.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List
from app.models.mourning import (
    MourningPeriod,
    Memorial,
    MemorialEntry,
    GriefSupport
)


class MourningRepository:
    """Repository for mourning and memorial data."""

    def __init__(self, db_path: str = "data/valueflows.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize mourning tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Mourning periods
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mourning_periods (
                id TEXT PRIMARY KEY,
                cell_id TEXT NOT NULL,
                trigger TEXT NOT NULL,
                honoring TEXT,
                description TEXT,
                started_at TEXT NOT NULL,
                duration_days INTEGER NOT NULL DEFAULT 7,
                ends_at TEXT NOT NULL,
                extended_count INTEGER DEFAULT 0,
                ended_early INTEGER DEFAULT 0,
                created_by TEXT NOT NULL,
                pause_metrics INTEGER DEFAULT 1,
                silence_non_urgent INTEGER DEFAULT 1,
                create_memorial INTEGER DEFAULT 1,
                enable_support_offers INTEGER DEFAULT 1
            )
        """)

        # Memorials
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memorials (
                id TEXT PRIMARY KEY,
                mourning_id TEXT NOT NULL,
                person_name TEXT,
                event_name TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (mourning_id) REFERENCES mourning_periods(id)
            )
        """)

        # Memorial entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memorial_entries (
                id TEXT PRIMARY KEY,
                memorial_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                content TEXT NOT NULL,
                media_url TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (memorial_id) REFERENCES memorials(id)
            )
        """)

        # Grief support offers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grief_support (
                id TEXT PRIMARY KEY,
                mourning_id TEXT NOT NULL,
                offered_by TEXT NOT NULL,
                support_type TEXT NOT NULL,
                details TEXT NOT NULL,
                claimed_by TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (mourning_id) REFERENCES mourning_periods(id)
            )
        """)

        conn.commit()
        conn.close()

    # Mourning Periods
    def create_mourning_period(self, mourning: MourningPeriod) -> MourningPeriod:
        """Create a new mourning period."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mourning_periods
            (id, cell_id, trigger, honoring, description, started_at, duration_days, ends_at,
             extended_count, ended_early, created_by, pause_metrics, silence_non_urgent,
             create_memorial, enable_support_offers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mourning.id, mourning.cell_id, mourning.trigger, mourning.honoring,
            mourning.description, mourning.started_at.isoformat(), mourning.duration_days,
            mourning.ends_at.isoformat(), mourning.extended_count, int(mourning.ended_early),
            mourning.created_by, int(mourning.pause_metrics), int(mourning.silence_non_urgent),
            int(mourning.create_memorial), int(mourning.enable_support_offers)
        ))

        conn.commit()
        conn.close()
        return mourning

    def get_active_mourning(self, cell_id: str) -> Optional[MourningPeriod]:
        """Get active mourning period for a cell."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM mourning_periods
            WHERE cell_id = ? AND ended_early = 0 AND datetime(ends_at) > datetime('now')
            ORDER BY started_at DESC
            LIMIT 1
        """, (cell_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_mourning(row)

    def extend_mourning(self, mourning_id: str, additional_days: int):
        """Extend a mourning period."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE mourning_periods
            SET ends_at = datetime(ends_at, '+' || ? || ' days'),
                duration_days = duration_days + ?,
                extended_count = extended_count + 1
            WHERE id = ?
        """, (additional_days, additional_days, mourning_id))

        conn.commit()
        conn.close()

    def end_mourning_early(self, mourning_id: str):
        """End a mourning period early."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE mourning_periods
            SET ended_early = 1, ends_at = datetime('now')
            WHERE id = ?
        """, (mourning_id,))

        conn.commit()
        conn.close()

    # Memorials
    def create_memorial(self, memorial: Memorial) -> Memorial:
        """Create a memorial."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memorials (id, mourning_id, person_name, event_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            memorial.id, memorial.mourning_id, memorial.person_name,
            memorial.event_name, memorial.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return memorial

    def get_memorial(self, mourning_id: str) -> Optional[Memorial]:
        """Get memorial for a mourning period."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM memorials WHERE mourning_id = ?
        """, (mourning_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Memorial(
            id=row["id"],
            mourning_id=row["mourning_id"],
            person_name=row["person_name"],
            event_name=row["event_name"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    # Memorial Entries
    def add_memorial_entry(self, entry: MemorialEntry) -> MemorialEntry:
        """Add an entry to a memorial."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memorial_entries (id, memorial_id, author_id, content, media_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entry.id, entry.memorial_id, entry.author_id,
            entry.content, entry.media_url, entry.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return entry

    def get_memorial_entries(self, memorial_id: str) -> List[MemorialEntry]:
        """Get all entries for a memorial."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM memorial_entries
            WHERE memorial_id = ?
            ORDER BY created_at ASC
        """, (memorial_id,))

        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            entries.append(MemorialEntry(
                id=row["id"],
                memorial_id=row["memorial_id"],
                author_id=row["author_id"],
                content=row["content"],
                media_url=row["media_url"],
                created_at=datetime.fromisoformat(row["created_at"])
            ))

        return entries

    # Grief Support
    def add_support_offer(self, support: GriefSupport) -> GriefSupport:
        """Add a support offer."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO grief_support (id, mourning_id, offered_by, support_type, details, claimed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            support.id, support.mourning_id, support.offered_by,
            support.support_type, support.details, support.claimed_by,
            support.created_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return support

    def get_support_offers(self, mourning_id: str) -> List[GriefSupport]:
        """Get all support offers for a mourning period."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM grief_support
            WHERE mourning_id = ?
            ORDER BY created_at DESC
        """, (mourning_id,))

        rows = cursor.fetchall()
        conn.close()

        offers = []
        for row in rows:
            offers.append(GriefSupport(
                id=row["id"],
                mourning_id=row["mourning_id"],
                offered_by=row["offered_by"],
                support_type=row["support_type"],
                details=row["details"],
                claimed_by=row["claimed_by"],
                created_at=datetime.fromisoformat(row["created_at"])
            ))

        return offers

    def claim_support(self, support_id: str, claimed_by: str):
        """Claim a support offer."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE grief_support
            SET claimed_by = ?
            WHERE id = ?
        """, (claimed_by, support_id))

        conn.commit()
        conn.close()

    # Helper methods
    def _row_to_mourning(self, row) -> MourningPeriod:
        """Convert database row to MourningPeriod model."""
        return MourningPeriod(
            id=row["id"],
            cell_id=row["cell_id"],
            trigger=row["trigger"],
            honoring=row["honoring"],
            description=row["description"],
            started_at=datetime.fromisoformat(row["started_at"]),
            duration_days=row["duration_days"],
            ends_at=datetime.fromisoformat(row["ends_at"]),
            extended_count=row["extended_count"],
            ended_early=bool(row["ended_early"]),
            created_by=row["created_by"],
            pause_metrics=bool(row["pause_metrics"]),
            silence_non_urgent=bool(row["silence_non_urgent"]),
            create_memorial=bool(row["create_memorial"]),
            enable_support_offers=bool(row["enable_support_offers"])
        )
