"""
Abundance Osmosis Repository (GAP-63)

Database operations for community shelves, circulating resources,
overflow detection, and knowledge ripples.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from ..models.abundance_osmosis import (
    CommunityShelf,
    ShelfItem,
    CirculatingResource,
    OverflowPrompt,
    KnowledgeRipple,
)


class AbundanceOsmosisRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    # === Community Shelves ===

    def create_shelf(self, shelf: CommunityShelf) -> CommunityShelf:
        """Create a new community shelf"""
        self.conn.execute(
            """
            INSERT INTO community_shelves
            (id, name, location, created_by, cell_id, is_virtual, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shelf.id,
                shelf.name,
                shelf.location,
                shelf.created_by,
                shelf.cell_id,
                1 if shelf.is_virtual else 0,
                shelf.created_at.isoformat(),
            ),
        )
        self.conn.commit()
        return shelf

    def get_shelves_by_cell(self, cell_id: str) -> List[CommunityShelf]:
        """Get all shelves in a cell"""
        cursor = self.conn.execute(
            """
            SELECT * FROM community_shelves
            WHERE cell_id = ?
            ORDER BY created_at DESC
            """,
            (cell_id,),
        )
        return [self._row_to_shelf(row) for row in cursor.fetchall()]

    def get_shelf_by_id(self, shelf_id: str) -> Optional[CommunityShelf]:
        """Get a specific shelf"""
        cursor = self.conn.execute(
            "SELECT * FROM community_shelves WHERE id = ?", (shelf_id,)
        )
        row = cursor.fetchone()
        return self._row_to_shelf(row) if row else None

    # === Shelf Items ===

    def add_item_to_shelf(self, item: ShelfItem) -> ShelfItem:
        """Add an item to a community shelf"""
        self.conn.execute(
            """
            INSERT INTO shelf_items
            (id, shelf_id, description, category, added_at, added_by, still_available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.shelf_id,
                item.description,
                item.category,
                item.added_at.isoformat(),
                item.added_by,  # Can be NULL for anonymous
                1 if item.still_available else 0,
            ),
        )
        self.conn.commit()
        return item

    def get_available_items(self, shelf_id: str) -> List[ShelfItem]:
        """Get all available items on a shelf"""
        cursor = self.conn.execute(
            """
            SELECT * FROM shelf_items
            WHERE shelf_id = ? AND still_available = 1
            ORDER BY added_at DESC
            """,
            (shelf_id,),
        )
        return [self._row_to_shelf_item(row) for row in cursor.fetchall()]

    def mark_item_taken(self, item_id: str) -> None:
        """
        Mark item as taken (delete it - no tracking of who took it).

        This is intentional: we don't track who takes from community shelves.
        The abundance flows anonymously.
        """
        self.conn.execute("DELETE FROM shelf_items WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_shelf_stats(self, shelf_id: str, days: int = 7) -> dict:
        """
        Get aggregate stats for a shelf (for stewards).

        NOTE: Returns aggregate only - no individual tracking.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as items_added
            FROM shelf_items
            WHERE shelf_id = ? AND added_at >= ?
            """,
            (shelf_id, cutoff),
        )
        row = cursor.fetchone()

        # We can't know exactly how many were taken (we deleted them)
        # but we can estimate: items added minus items still there
        cursor2 = self.conn.execute(
            """
            SELECT COUNT(*) as items_remaining
            FROM shelf_items
            WHERE shelf_id = ? AND still_available = 1
            """,
            (shelf_id,),
        )
        row2 = cursor2.fetchone()

        return {
            "items_added_last_7_days": row["items_added"] if row else 0,
            "items_currently_available": row2["items_remaining"] if row2 else 0,
            "estimated_items_taken": max(
                0, (row["items_added"] if row else 0) - (row2["items_remaining"] if row2 else 0)
            ),
        }

    # === Circulating Resources ===

    def create_circulating_resource(
        self, resource: CirculatingResource
    ) -> CirculatingResource:
        """Register a resource that circulates in the community"""
        self.conn.execute(
            """
            INSERT INTO circulating_resources
            (id, description, category, current_location, current_holder_notes, last_updated, cell_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resource.id,
                resource.description,
                resource.category,
                resource.current_location,
                resource.current_holder_notes,
                resource.last_updated.isoformat(),
                resource.cell_id,
            ),
        )
        self.conn.commit()
        return resource

    def update_resource_location(
        self, resource_id: str, new_location: str, notes: Optional[str] = None
    ) -> None:
        """Update where a circulating resource currently is"""
        self.conn.execute(
            """
            UPDATE circulating_resources
            SET current_location = ?,
                current_holder_notes = ?,
                last_updated = ?
            WHERE id = ?
            """,
            (new_location, notes, datetime.now(UTC).isoformat(), resource_id),
        )
        self.conn.commit()

    def get_circulating_resources(self, cell_id: str) -> List[CirculatingResource]:
        """Get all circulating resources in a cell"""
        cursor = self.conn.execute(
            """
            SELECT * FROM circulating_resources
            WHERE cell_id = ?
            ORDER BY description
            """,
            (cell_id,),
        )
        return [self._row_to_circulating_resource(row) for row in cursor.fetchall()]

    def find_resource(self, cell_id: str, search_term: str) -> List[CirculatingResource]:
        """Find circulating resources by description"""
        cursor = self.conn.execute(
            """
            SELECT * FROM circulating_resources
            WHERE cell_id = ? AND description LIKE ?
            ORDER BY description
            """,
            (cell_id, f"%{search_term}%"),
        )
        return [self._row_to_circulating_resource(row) for row in cursor.fetchall()]

    # === Overflow Detection ===

    def create_overflow_prompt(self, prompt: OverflowPrompt) -> OverflowPrompt:
        """Create a gentle overflow suggestion"""
        self.conn.execute(
            """
            INSERT INTO overflow_prompts
            (id, user_id, listing_id, days_available, prompted_at, status, snoozed_until)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt.id,
                prompt.user_id,
                prompt.listing_id,
                prompt.days_available,
                prompt.prompted_at.isoformat(),
                prompt.status,
                prompt.snoozed_until.isoformat() if prompt.snoozed_until else None,
            ),
        )
        self.conn.commit()
        return prompt

    def get_pending_overflow_prompts(self, user_id: str) -> List[OverflowPrompt]:
        """Get overflow prompts for a user that haven't been answered"""
        now = datetime.now(UTC).isoformat()
        cursor = self.conn.execute(
            """
            SELECT * FROM overflow_prompts
            WHERE user_id = ?
            AND status = 'pending'
            AND (snoozed_until IS NULL OR snoozed_until <= ?)
            ORDER BY prompted_at DESC
            """,
            (user_id, now),
        )
        return [self._row_to_overflow_prompt(row) for row in cursor.fetchall()]

    def update_overflow_prompt_status(
        self, prompt_id: str, status: str, snooze_until: Optional[datetime] = None
    ) -> None:
        """Update status of an overflow prompt"""
        self.conn.execute(
            """
            UPDATE overflow_prompts
            SET status = ?, snoozed_until = ?
            WHERE id = ?
            """,
            (status, snooze_until.isoformat() if snooze_until else None, prompt_id),
        )
        self.conn.commit()

    # === Knowledge Ripples ===

    def create_knowledge_ripple(self, ripple: KnowledgeRipple) -> KnowledgeRipple:
        """Track a learning exchange for potential ripple"""
        self.conn.execute(
            """
            INSERT INTO knowledge_ripples
            (id, user_id, exchange_id, skill_learned, learned_at, prompted_at, status, permanently_dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ripple.id,
                ripple.user_id,
                ripple.exchange_id,
                ripple.skill_learned,
                ripple.learned_at.isoformat(),
                ripple.prompted_at.isoformat() if ripple.prompted_at else None,
                ripple.status,
                1 if ripple.permanently_dismissed else 0,
            ),
        )
        self.conn.commit()
        return ripple

    def get_ripe_knowledge_ripples(self, weeks_ago: int = 2) -> List[KnowledgeRipple]:
        """
        Get learning exchanges that are ready for teaching suggestion.

        "You learned bicycle repair 2 weeks ago. Ready to teach?"
        """
        cutoff = (datetime.now(UTC) - timedelta(weeks=weeks_ago)).isoformat()
        now = datetime.now(UTC).isoformat()

        cursor = self.conn.execute(
            """
            SELECT * FROM knowledge_ripples
            WHERE learned_at <= ?
            AND learned_at >= ?
            AND status = 'pending'
            AND permanently_dismissed = 0
            """,
            (cutoff, (datetime.now(UTC) - timedelta(weeks=weeks_ago + 1)).isoformat()),
        )
        return [self._row_to_knowledge_ripple(row) for row in cursor.fetchall()]

    def mark_ripple_prompted(self, ripple_id: str) -> None:
        """Mark that we prompted the user to teach"""
        self.conn.execute(
            """
            UPDATE knowledge_ripples
            SET prompted_at = ?, status = 'prompted'
            WHERE id = ?
            """,
            (datetime.now(UTC).isoformat(), ripple_id),
        )
        self.conn.commit()

    def dismiss_ripple(self, ripple_id: str, permanently: bool = False) -> None:
        """User declined to teach (optionally permanently)"""
        self.conn.execute(
            """
            UPDATE knowledge_ripples
            SET status = 'dismissed', permanently_dismissed = ?
            WHERE id = ?
            """,
            (1 if permanently else 0, ripple_id),
        )
        self.conn.commit()

    # === Helper methods to convert rows to models ===

    def _row_to_shelf(self, row: sqlite3.Row) -> CommunityShelf:
        return CommunityShelf(
            id=row["id"],
            name=row["name"],
            location=row["location"],
            created_by=row["created_by"],
            cell_id=row["cell_id"],
            is_virtual=bool(row["is_virtual"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_shelf_item(self, row: sqlite3.Row) -> ShelfItem:
        return ShelfItem(
            id=row["id"],
            shelf_id=row["shelf_id"],
            description=row["description"],
            category=row["category"],
            added_at=datetime.fromisoformat(row["added_at"]),
            added_by=row["added_by"],
            still_available=bool(row["still_available"]),
        )

    def _row_to_circulating_resource(self, row: sqlite3.Row) -> CirculatingResource:
        return CirculatingResource(
            id=row["id"],
            description=row["description"],
            category=row["category"],
            current_location=row["current_location"],
            current_holder_notes=row["current_holder_notes"],
            last_updated=datetime.fromisoformat(row["last_updated"]),
            cell_id=row["cell_id"],
        )

    def _row_to_overflow_prompt(self, row: sqlite3.Row) -> OverflowPrompt:
        return OverflowPrompt(
            id=row["id"],
            user_id=row["user_id"],
            listing_id=row["listing_id"],
            days_available=row["days_available"],
            prompted_at=datetime.fromisoformat(row["prompted_at"]),
            status=row["status"],
            snoozed_until=(
                datetime.fromisoformat(row["snoozed_until"])
                if row["snoozed_until"]
                else None
            ),
        )

    def _row_to_knowledge_ripple(self, row: sqlite3.Row) -> KnowledgeRipple:
        return KnowledgeRipple(
            id=row["id"],
            user_id=row["user_id"],
            exchange_id=row["exchange_id"],
            skill_learned=row["skill_learned"],
            learned_at=datetime.fromisoformat(row["learned_at"]),
            prompted_at=(
                datetime.fromisoformat(row["prompted_at"])
                if row["prompted_at"]
                else None
            ),
            status=row["status"],
            permanently_dismissed=bool(row["permanently_dismissed"]),
        )
