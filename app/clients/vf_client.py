"""
ValueFlows Database Client

Provides a clean interface for agents to query the ValueFlows database.
Handles connection management and repository instantiation.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import VF repositories
import sys
vf_path = Path(__file__).parent.parent.parent / "valueflows_node"
sys.path.insert(0, str(vf_path))

from app.database import get_database
from app.repositories.vf.listing_repo import ListingRepository
from app.repositories.vf.agent_repo import AgentRepository
from app.repositories.vf.location_repo import LocationRepository
from app.repositories.vf.resource_spec_repo import ResourceSpecRepository
from app.models.vf.listing import Listing, ListingType
from app.models.vf.resource_spec import ResourceCategory


class VFClient:
    """
    Client for querying ValueFlows database from agents.

    Provides high-level query methods that return dictionaries
    suitable for agent analysis.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize VF client.

        Args:
            db_path: Optional path to ValueFlows database
        """
        if db_path is None:
            # Default to valueflows_node/app/database/valueflows.db
            db_path = str(Path(__file__).parent.parent.parent / "valueflows_node" / "app" / "database" / "valueflows.db")

        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    async def get_active_offers(
        self,
        category: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active offer listings.

        Args:
            category: Filter by category (e.g., "food:produce")
            location_id: Filter by location
            limit: Maximum results

        Returns:
            List of offer dictionaries with denormalized data for analysis
        """
        self.connect()
        listing_repo = ListingRepository(self.conn)

        # Parse category if provided
        category_enum = None
        if category:
            # Map string categories to enum (simplified mapping)
            category_map = {
                "food:produce": ResourceCategory.FOOD,
                "seeds:vegetables": ResourceCategory.SEEDS,
                "tools": ResourceCategory.TOOLS,
                "services": ResourceCategory.SERVICES,
            }
            category_enum = category_map.get(category)

        # Query listings
        listings = listing_repo.find_offers(
            category=category_enum,
            location_id=location_id,
            status="active",
            limit=limit
        )

        # Convert to dictionaries with denormalized data
        results = []
        for listing in listings:
            # Get related objects
            agent = self._get_agent(listing.agent_id)
            location = self._get_location(listing.location_id) if listing.location_id else None
            resource_spec = self._get_resource_spec(listing.resource_spec_id)

            results.append({
                "id": listing.id,
                "user_id": listing.agent_id,
                "user_name": agent.get("name") if agent else "Unknown",
                "resource": resource_spec.get("name") if resource_spec else "Unknown",
                "category": category or "general",
                "quantity": listing.quantity,
                "unit": listing.unit,
                "location": location.get("name") if location else "Unknown",
                "location_coords": (location.get("latitude"), location.get("longitude")) if location else None,
                "available_from": listing.available_from,
                "available_until": listing.available_until,
                "title": listing.title,
                "description": listing.description,
                "preferences": [listing.description] if listing.description else [],
                "bundle_id": f"bundle:offer-{listing.id}",
                "listing_obj": listing,  # Include original object
            })

        return results

    async def get_active_needs(
        self,
        category: Optional[str] = None,
        location_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active need listings.

        Args:
            category: Filter by category
            location_id: Filter by location
            limit: Maximum results

        Returns:
            List of need dictionaries with denormalized data for analysis
        """
        self.connect()
        listing_repo = ListingRepository(self.conn)

        # Parse category if provided
        category_enum = None
        if category:
            category_map = {
                "food:produce": ResourceCategory.FOOD,
                "seeds:vegetables": ResourceCategory.SEEDS,
                "tools": ResourceCategory.TOOLS,
                "services": ResourceCategory.SERVICES,
            }
            category_enum = category_map.get(category)

        # Query listings
        listings = listing_repo.find_needs(
            category=category_enum,
            location_id=location_id,
            status="active",
            limit=limit
        )

        # Convert to dictionaries with denormalized data
        results = []
        for listing in listings:
            # Get related objects
            agent = self._get_agent(listing.agent_id)
            location = self._get_location(listing.location_id) if listing.location_id else None
            resource_spec = self._get_resource_spec(listing.resource_spec_id)

            results.append({
                "id": listing.id,
                "user_id": listing.agent_id,
                "user_name": agent.get("name") if agent else "Unknown",
                "resource": resource_spec.get("name") if resource_spec else "Unknown",
                "category": category or "general",
                "quantity": listing.quantity,
                "unit": listing.unit,
                "location": location.get("name") if location else "Unknown",
                "location_coords": (location.get("latitude"), location.get("longitude")) if location else None,
                "needed_by": listing.available_until,
                "title": listing.title,
                "description": listing.description,
                "purpose": listing.description,
                "constraints": [listing.description] if listing.description else [],
                "bundle_id": f"bundle:need-{listing.id}",
                "listing_obj": listing,  # Include original object
            })

        return results

    def _get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        try:
            cursor = self.conn.cursor()
            row = cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error fetching agent {agent_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching agent {agent_id}: {e}", exc_info=True)
            raise

    def _get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get location by ID"""
        try:
            cursor = self.conn.cursor()
            row = cursor.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error fetching location {location_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching location {location_id}: {e}", exc_info=True)
            raise

    def _get_resource_spec(self, resource_spec_id: str) -> Optional[Dict[str, Any]]:
        """Get resource spec by ID"""
        try:
            cursor = self.conn.cursor()
            row = cursor.execute("SELECT * FROM resource_specs WHERE id = ?", (resource_spec_id,)).fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error fetching resource_spec {resource_spec_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching resource_spec {resource_spec_id}: {e}", exc_info=True)
            raise

    async def get_inventory_by_location(self, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get current inventory (active offers) by location.

        Args:
            location_id: Filter by location

        Returns:
            List of inventory items
        """
        return await self.get_active_offers(location_id=location_id)

    async def get_resource_specs(self) -> List[Dict[str, Any]]:
        """Get all resource specifications"""
        self.connect()
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM resource_specs").fetchall()
        return [dict(row) for row in rows]

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get all locations"""
        self.connect()
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM locations").fetchall()
        return [dict(row) for row in rows]

    async def get_all_listings(self, status: str = "active") -> List[Dict[str, Any]]:
        """Get all listings (offers and needs)"""
        all_listings = []
        all_listings.extend(await self.get_active_offers())
        all_listings.extend(await self.get_active_needs())
        return all_listings

    async def get_work_sessions(self) -> List[Dict[str, Any]]:
        """Get work party sessions (Plans with type=work_party)"""
        self.connect()
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM plans WHERE planned_start IS NOT NULL ORDER BY planned_start"
        ).fetchall()
        return [dict(row) for row in rows]

    async def get_lessons(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get educational lessons"""
        self.connect()
        cursor = self.conn.cursor()
        if topic:
            rows = cursor.execute(
                "SELECT * FROM lessons WHERE topic LIKE ?", (f"%{topic}%",)
            ).fetchall()
        else:
            rows = cursor.execute("SELECT * FROM lessons").fetchall()
        return [dict(row) for row in rows]

    async def get_protocols(self) -> List[Dict[str, Any]]:
        """Get protocols (repeatable processes)"""
        self.connect()
        cursor = self.conn.cursor()
        rows = cursor.execute("SELECT * FROM protocols").fetchall()
        return [dict(row) for row in rows]

    async def get_expiring_offers(self, hours: int = 168) -> List[Dict[str, Any]]:
        """
        Get offers expiring within specified hours.

        Args:
            hours: Time window (default: 168 hours = 1 week)

        Returns:
            List of expiring offer dictionaries
        """
        self.connect()
        listing_repo = ListingRepository(self.conn)

        # Query expiring listings
        listings = listing_repo.find_expiring_soon(hours=hours)

        # Filter for offers only
        offers = [l for l in listings if l.listing_type == ListingType.OFFER]

        # Convert to dictionaries with denormalized data
        results = []
        for listing in offers:
            agent = self._get_agent(listing.agent_id)
            location = self._get_location(listing.location_id) if listing.location_id else None
            resource_spec = self._get_resource_spec(listing.resource_spec_id)

            # Calculate hours until expiry
            if listing.available_until:
                from datetime import datetime
                hours_left = (listing.available_until - datetime.now()).total_seconds() / 3600
            else:
                hours_left = 99999  # No expiry

            results.append({
                "id": listing.id,
                "resource": resource_spec.get("name") if resource_spec else "Unknown",
                "category": "food",  # Simplified
                "quantity": listing.quantity,
                "unit": listing.unit,
                "expiry_date": listing.available_until,
                "hours_until_expiry": hours_left,
                "location": location.get("name") if location else "Unknown",
                "owner": agent.get("name") if agent else "Unknown",
                "title": listing.title,
                "description": listing.description,
                "bundle_id": f"bundle:offer-{listing.id}",
                "listing_obj": listing,
            })

        return results

    async def get_commitments(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        plan_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get commitments (promises to do work or deliver resources).

        Args:
            agent_id: Filter by agent who made commitment
            status: Filter by status (proposed, accepted, in_progress, fulfilled, cancelled)
            plan_id: Filter by plan

        Returns:
            List of commitment dictionaries
        """
        self.connect()

        # Build query
        query = "SELECT * FROM commitments WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        if plan_id:
            query += " AND plan_id = ?"
            params.append(plan_id)

        query += " ORDER BY due_date"

        cursor = self.conn.cursor()
        rows = cursor.execute(query, tuple(params)).fetchall()

        # Convert to dictionaries with denormalized data
        results = []
        for row in rows:
            row_dict = dict(row)
            agent = self._get_agent(row_dict["agent_id"])
            resource_spec = self._get_resource_spec(row_dict["resource_spec_id"]) if row_dict.get("resource_spec_id") else None

            results.append({
                "id": row_dict["id"],
                "agent_id": row_dict["agent_id"],
                "agent_name": agent.get("name") if agent else "Unknown",
                "action": row_dict["action"],
                "resource": resource_spec.get("name") if resource_spec else None,
                "quantity": row_dict.get("quantity"),
                "unit": row_dict.get("unit"),
                "due_date": row_dict.get("due_date"),
                "status": row_dict.get("status"),
                "plan_id": row_dict.get("plan_id"),
                "exchange_id": row_dict.get("exchange_id"),
                "note": row_dict.get("note"),
                "created_at": row_dict.get("created_at"),
            })

        return results
