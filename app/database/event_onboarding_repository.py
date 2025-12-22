"""Event Onboarding Repository - Database operations for event and batch invites"""
import sqlite3
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional
import secrets

from app.models.event_onboarding import (
    EventInvite,
    BatchInvite,
    EventAttendee,
    OnboardingAnalytics,
    TrustLevel,
)


class EventOnboardingRepository:
    """Repository for event onboarding data"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize event onboarding tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Event invites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_invites (
                    id TEXT PRIMARY KEY,
                    created_by TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_start TEXT NOT NULL,
                    event_end TEXT NOT NULL,
                    event_location TEXT,
                    max_attendees INTEGER,
                    invite_code TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    attendee_count INTEGER NOT NULL DEFAULT 0,
                    temporary_trust_level REAL NOT NULL DEFAULT 0.3
                )
            """)

            # Batch invites table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_invites (
                    id TEXT PRIMARY KEY,
                    created_by TEXT NOT NULL,
                    invite_link TEXT UNIQUE NOT NULL,
                    max_uses INTEGER NOT NULL,
                    used_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    context TEXT NOT NULL
                )
            """)

            # Event attendees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_attendees (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    joined_at TEXT NOT NULL,
                    upgraded_to_member INTEGER NOT NULL DEFAULT 0,
                    upgraded_at TEXT,
                    FOREIGN KEY (event_id) REFERENCES event_invites(id),
                    UNIQUE(event_id, user_id)
                )
            """)

            # Batch invite uses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_invite_uses (
                    id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    used_at TEXT NOT NULL,
                    FOREIGN KEY (batch_id) REFERENCES batch_invites(id),
                    UNIQUE(batch_id, user_id)
                )
            """)

            conn.commit()

    def _generate_invite_code(self) -> str:
        """Generate a unique invite code"""
        return secrets.token_urlsafe(12).upper()[:12]

    def create_event_invite(
        self,
        created_by: str,
        event_name: str,
        event_type: str,
        event_start: datetime,
        event_end: datetime,
        event_location: Optional[str] = None,
        max_attendees: Optional[int] = None,
        temporary_trust_level: float = 0.3,
    ) -> EventInvite:
        """Create a new event invite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            event_id = f"event-{uuid.uuid4()}"
            invite_code = self._generate_invite_code()
            created_at = datetime.now(UTC)
            # Event invite expires 1 day after event ends
            expires_at = event_end + timedelta(days=1)

            cursor.execute("""
                INSERT INTO event_invites (
                    id, created_by, event_name, event_type, event_start, event_end,
                    event_location, max_attendees, invite_code, created_at, expires_at,
                    active, attendee_count, temporary_trust_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
            """, (
                event_id, created_by, event_name, event_type,
                event_start.isoformat(), event_end.isoformat(),
                event_location, max_attendees, invite_code,
                created_at.isoformat(), expires_at.isoformat(),
                temporary_trust_level
            ))

            conn.commit()

            return EventInvite(
                id=event_id,
                created_by=created_by,
                event_name=event_name,
                event_type=event_type,
                event_start=event_start,
                event_end=event_end,
                event_location=event_location,
                max_attendees=max_attendees,
                invite_code=invite_code,
                created_at=created_at,
                expires_at=expires_at,
                active=True,
                attendee_count=0,
                temporary_trust_level=temporary_trust_level,
            )

    def get_event_invite(self, event_id: str) -> Optional[EventInvite]:
        """Get an event invite by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM event_invites WHERE id = ?", (event_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_event_invite(row)

    def get_event_invite_by_code(self, invite_code: str) -> Optional[EventInvite]:
        """Get an event invite by invite code"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM event_invites WHERE invite_code = ?", (invite_code,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_event_invite(row)

    def get_event_invites_by_creator(self, creator_id: str) -> List[EventInvite]:
        """Get all event invites created by a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM event_invites WHERE created_by = ? ORDER BY created_at DESC",
                (creator_id,)
            )
            rows = cursor.fetchall()

            return [self._row_to_event_invite(row) for row in rows]

    def use_event_invite(self, invite_code: str, user_id: str) -> Optional[EventAttendee]:
        """Use an event invite to onboard a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get the event
            event = self.get_event_invite_by_code(invite_code)
            if not event:
                return None

            # Check if invite is valid
            if not event.active:
                return None

            if datetime.fromisoformat(event.expires_at.isoformat()) < datetime.now(UTC):
                return None

            if event.max_attendees and event.attendee_count >= event.max_attendees:
                return None

            # Check if user already used this invite
            cursor.execute(
                "SELECT id FROM event_attendees WHERE event_id = ? AND user_id = ?",
                (event.id, user_id)
            )
            if cursor.fetchone():
                return None  # Already used

            # Create attendee record
            attendee_id = f"attendee-{uuid.uuid4()}"
            joined_at = datetime.now(UTC)

            cursor.execute("""
                INSERT INTO event_attendees (id, event_id, user_id, joined_at, upgraded_to_member)
                VALUES (?, ?, ?, ?, 0)
            """, (attendee_id, event.id, user_id, joined_at.isoformat()))

            # Increment attendee count
            cursor.execute(
                "UPDATE event_invites SET attendee_count = attendee_count + 1 WHERE id = ?",
                (event.id,)
            )

            conn.commit()

            return EventAttendee(
                id=attendee_id,
                event_id=event.id,
                user_id=user_id,
                joined_at=joined_at,
                upgraded_to_member=False,
            )

    def create_batch_invite(
        self,
        created_by: str,
        max_uses: int,
        days_valid: int,
        context: str,
    ) -> BatchInvite:
        """Create a batch invite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            batch_id = f"batch-{uuid.uuid4()}"
            invite_link = f"BATCH-{self._generate_invite_code()}"
            created_at = datetime.now(UTC)
            expires_at = created_at + timedelta(days=days_valid)

            cursor.execute("""
                INSERT INTO batch_invites (
                    id, created_by, invite_link, max_uses, used_count,
                    created_at, expires_at, active, context
                ) VALUES (?, ?, ?, ?, 0, ?, ?, 1, ?)
            """, (
                batch_id, created_by, invite_link, max_uses,
                created_at.isoformat(), expires_at.isoformat(), context
            ))

            conn.commit()

            return BatchInvite(
                id=batch_id,
                created_by=created_by,
                invite_link=invite_link,
                max_uses=max_uses,
                used_count=0,
                created_at=created_at,
                expires_at=expires_at,
                active=True,
                context=context,
            )

    def use_batch_invite(self, invite_link: str, user_id: str) -> bool:
        """Use a batch invite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get the batch invite
            cursor.execute("SELECT * FROM batch_invites WHERE invite_link = ?", (invite_link,))
            row = cursor.fetchone()

            if not row:
                return False

            batch = self._row_to_batch_invite(row)

            # Validate
            if not batch.active:
                return False

            if datetime.fromisoformat(batch.expires_at.isoformat()) < datetime.now(UTC):
                return False

            if batch.used_count >= batch.max_uses:
                return False

            # Check if user already used this invite
            cursor.execute(
                "SELECT id FROM batch_invite_uses WHERE batch_id = ? AND user_id = ?",
                (batch.id, user_id)
            )
            if cursor.fetchone():
                return False  # Already used

            # Record use
            use_id = f"use-{uuid.uuid4()}"
            used_at = datetime.now(UTC)

            cursor.execute("""
                INSERT INTO batch_invite_uses (id, batch_id, user_id, used_at)
                VALUES (?, ?, ?, ?)
            """, (use_id, batch.id, user_id, used_at.isoformat()))

            # Increment used count
            cursor.execute(
                "UPDATE batch_invites SET used_count = used_count + 1 WHERE id = ?",
                (batch.id,)
            )

            conn.commit()
            return True

    def get_analytics(self) -> OnboardingAnalytics:
        """Get onboarding analytics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total invites
            cursor.execute("SELECT COUNT(*) FROM event_invites")
            total_event_invites = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM batch_invites")
            total_batch_invites = cursor.fetchone()[0]

            # Total attendees/members
            cursor.execute("SELECT COUNT(*) FROM event_attendees")
            total_event_attendees = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM batch_invite_uses")
            total_batch_members = cursor.fetchone()[0]

            # Upgrade rate
            cursor.execute("SELECT COUNT(*) FROM event_attendees WHERE upgraded_to_member = 1")
            upgraded_count = cursor.fetchone()[0]

            upgrade_rate = (upgraded_count / total_event_attendees) if total_event_attendees > 0 else 0.0

            # Active events
            cursor.execute("""
                SELECT COUNT(*) FROM event_invites
                WHERE active = 1 AND datetime(expires_at) > datetime('now')
            """)
            active_events = cursor.fetchone()[0]

            # Recent joins (24h)
            cursor.execute("""
                SELECT COUNT(*) FROM event_attendees
                WHERE datetime(joined_at) > datetime('now', '-1 day')
            """)
            recent_joins_24h = cursor.fetchone()[0]

            return OnboardingAnalytics(
                total_event_invites=total_event_invites,
                total_batch_invites=total_batch_invites,
                total_event_attendees=total_event_attendees,
                total_batch_members=total_batch_members,
                upgrade_rate=upgrade_rate,
                active_events=active_events,
                recent_joins_24h=recent_joins_24h,
                trust_level_distribution={},  # Will be populated by trust service
            )

    def _row_to_event_invite(self, row) -> EventInvite:
        """Convert database row to EventInvite model"""
        return EventInvite(
            id=row[0],
            created_by=row[1],
            event_name=row[2],
            event_type=row[3],
            event_start=datetime.fromisoformat(row[4]),
            event_end=datetime.fromisoformat(row[5]),
            event_location=row[6],
            max_attendees=row[7],
            invite_code=row[8],
            created_at=datetime.fromisoformat(row[9]),
            expires_at=datetime.fromisoformat(row[10]),
            active=bool(row[11]),
            attendee_count=row[12],
            temporary_trust_level=row[13],
        )

    def _row_to_batch_invite(self, row) -> BatchInvite:
        """Convert database row to BatchInvite model"""
        return BatchInvite(
            id=row[0],
            created_by=row[1],
            invite_link=row[2],
            max_uses=row[3],
            used_count=row[4],
            created_at=datetime.fromisoformat(row[5]),
            expires_at=datetime.fromisoformat(row[6]),
            active=bool(row[7]),
            context=row[8],
        )
