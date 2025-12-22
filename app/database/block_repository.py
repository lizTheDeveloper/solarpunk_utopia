"""
Block Repository - Database operations for block list (GAP-107)
"""

import sqlite3
from datetime import datetime, UTC
from typing import List, Optional
from app.models.block import BlockEntry


class BlockRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create blocks table if it doesn't exist"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id TEXT PRIMARY KEY,
                blocker_id TEXT NOT NULL,
                blocked_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                reason TEXT,
                UNIQUE(blocker_id, blocked_id)
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blocks_blocker ON blocks(blocker_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_blocks_blocked ON blocks(blocked_id)
        """)
        self.conn.commit()

    def block_user(self, blocker_id: str, blocked_id: str, reason: str = None) -> BlockEntry:
        """
        Block a user.

        Args:
            blocker_id: User initiating the block
            blocked_id: User being blocked
            reason: Optional private reason

        Returns:
            BlockEntry: The created block record

        Raises:
            sqlite3.IntegrityError: If block already exists
        """
        import uuid

        block_id = f"block:{uuid.uuid4()}"
        created_at = datetime.now(UTC)

        entry = BlockEntry(
            id=block_id,
            blocker_id=blocker_id,
            blocked_id=blocked_id,
            created_at=created_at,
            reason=reason,
        )

        self.conn.execute(
            """
            INSERT INTO blocks (id, blocker_id, blocked_id, created_at, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (block_id, blocker_id, blocked_id, created_at.isoformat(), reason),
        )
        self.conn.commit()

        return entry

    def unblock_user(self, blocker_id: str, blocked_id: str) -> bool:
        """
        Remove a block.

        Args:
            blocker_id: User who initiated the block
            blocked_id: User who was blocked

        Returns:
            bool: True if block was removed, False if no block existed
        """
        cursor = self.conn.execute(
            "DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
            (blocker_id, blocked_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def is_blocked(self, user_a: str, user_b: str) -> bool:
        """
        Check if either user has blocked the other.

        Args:
            user_a: First user ID
            user_b: Second user ID

        Returns:
            bool: True if either user has blocked the other
        """
        cursor = self.conn.execute(
            """
            SELECT COUNT(*) FROM blocks
            WHERE (blocker_id = ? AND blocked_id = ?)
               OR (blocker_id = ? AND blocked_id = ?)
            """,
            (user_a, user_b, user_b, user_a),
        )
        count = cursor.fetchone()[0]
        return count > 0

    def get_blocked_by_user(self, user_id: str) -> List[str]:
        """
        Get list of user IDs that this user has blocked.

        Args:
            user_id: User ID

        Returns:
            List[str]: List of blocked user IDs
        """
        cursor = self.conn.execute(
            "SELECT blocked_id FROM blocks WHERE blocker_id = ?", (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_blocks_against_user(self, user_id: str) -> List[str]:
        """
        Get list of user IDs who have blocked this user.

        Note: This is sensitive information - only use for admin/debug purposes.

        Args:
            user_id: User ID

        Returns:
            List[str]: List of blocker user IDs
        """
        cursor = self.conn.execute(
            "SELECT blocker_id FROM blocks WHERE blocked_id = ?", (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_block(self, blocker_id: str, blocked_id: str) -> Optional[BlockEntry]:
        """Get a specific block record"""
        cursor = self.conn.execute(
            """
            SELECT id, blocker_id, blocked_id, created_at, reason
            FROM blocks
            WHERE blocker_id = ? AND blocked_id = ?
            """,
            (blocker_id, blocked_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return BlockEntry(
            id=row[0],
            blocker_id=row[1],
            blocked_id=row[2],
            created_at=datetime.fromisoformat(row[3]),
            reason=row[4],
        )
