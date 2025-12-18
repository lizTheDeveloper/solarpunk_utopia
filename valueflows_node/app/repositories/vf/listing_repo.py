"""
Listing Repository

CRUD operations for Listings (offers and needs).
This is the primary UX object.
"""

from typing import Optional, List
import sqlite3
from datetime import datetime

from ...models.vf.listing import Listing, ListingType
from ...models.vf.resource_spec import ResourceCategory
from .base_repo import BaseRepository


class ListingRepository(BaseRepository[Listing]):
    """Repository for Listing objects"""

    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "listings", Listing)

    def create(self, listing: Listing) -> Listing:
        """Create a new listing"""
        if listing.created_at is None:
            listing.created_at = datetime.now()

        query = """
            INSERT INTO listings (
                id, listing_type, resource_spec_id, agent_id, location_id,
                quantity, unit, available_from, available_until,
                title, description, image_url, status, resource_instance_id,
                created_at, updated_at, author, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            listing.id,
            listing.listing_type.value,
            listing.resource_spec_id,
            listing.agent_id,
            listing.location_id,
            listing.quantity,
            listing.unit,
            listing.available_from.isoformat() if listing.available_from else None,
            listing.available_until.isoformat() if listing.available_until else None,
            listing.title,
            listing.description,
            listing.image_url,
            listing.status,
            listing.resource_instance_id,
            listing.created_at.isoformat(),
            listing.updated_at.isoformat() if listing.updated_at else None,
            listing.author,
            listing.signature,
        )

        self._execute(query, params)
        self.conn.commit()

        return listing

    def update(self, listing: Listing) -> Listing:
        """Update existing listing"""
        listing.updated_at = datetime.now()

        query = """
            UPDATE listings SET
                status = ?,
                title = ?,
                description = ?,
                quantity = ?,
                unit = ?,
                available_from = ?,
                available_until = ?,
                updated_at = ?
            WHERE id = ?
        """

        params = (
            listing.status,
            listing.title,
            listing.description,
            listing.quantity,
            listing.unit,
            listing.available_from.isoformat() if listing.available_from else None,
            listing.available_until.isoformat() if listing.available_until else None,
            listing.updated_at.isoformat(),
            listing.id,
        )

        self._execute(query, params)
        self.conn.commit()

        return listing

    def find_offers(
        self,
        category: Optional[ResourceCategory] = None,
        location_id: Optional[str] = None,
        status: str = "active",
        limit: Optional[int] = None
    ) -> List[Listing]:
        """
        Find offer listings with filters.

        Args:
            category: Filter by resource category
            location_id: Filter by location
            status: Filter by status (default: active)
            limit: Maximum results

        Returns:
            List of matching offers
        """
        query = """
            SELECT l.* FROM listings l
            LEFT JOIN resource_specs rs ON l.resource_spec_id = rs.id
            WHERE l.listing_type = 'offer'
            AND l.status = ?
        """
        params = [status]

        if category:
            query += " AND rs.category = ?"
            params.append(category.value)

        if location_id:
            query += " AND l.location_id = ?"
            params.append(location_id)

        query += " ORDER BY l.created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        rows = self._fetch_all(query, tuple(params))
        return [Listing.from_dict(row) for row in rows]

    def find_needs(
        self,
        category: Optional[ResourceCategory] = None,
        location_id: Optional[str] = None,
        status: str = "active",
        limit: Optional[int] = None
    ) -> List[Listing]:
        """Find need listings with filters"""
        query = """
            SELECT l.* FROM listings l
            LEFT JOIN resource_specs rs ON l.resource_spec_id = rs.id
            WHERE l.listing_type = 'need'
            AND l.status = ?
        """
        params = [status]

        if category:
            query += " AND rs.category = ?"
            params.append(category.value)

        if location_id:
            query += " AND l.location_id = ?"
            params.append(location_id)

        query += " ORDER BY l.created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        rows = self._fetch_all(query, tuple(params))
        return [Listing.from_dict(row) for row in rows]

    def find_by_agent(self, agent_id: str, listing_type: Optional[ListingType] = None) -> List[Listing]:
        """Find listings created by an agent"""
        query = "SELECT * FROM listings WHERE agent_id = ?"
        params = [agent_id]

        if listing_type:
            query += " AND listing_type = ?"
            params.append(listing_type.value)

        query += " ORDER BY created_at DESC"

        rows = self._fetch_all(query, tuple(params))
        return [Listing.from_dict(row) for row in rows]

    def find_expiring_soon(self, hours: int = 24) -> List[Listing]:
        """Find listings expiring within specified hours"""
        from datetime import timedelta
        threshold = datetime.now() + timedelta(hours=hours)

        query = """
            SELECT * FROM listings
            WHERE status = 'active'
            AND available_until IS NOT NULL
            AND available_until <= ?
            ORDER BY available_until ASC
        """

        rows = self._fetch_all(query, (threshold.isoformat(),))
        return [Listing.from_dict(row) for row in rows]
