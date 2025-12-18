"""
ValueFlows Query Service

High-level queries for gift economy coordination.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3

from ..models.vf.listing import Listing, ListingType
from ..models.vf.resource_spec import ResourceCategory
from ..models.vf.resource_instance import ResourceInstance
from ..models.vf.exchange import Exchange
from ..repositories.vf.listing_repo import ListingRepository
from ..repositories.vf.resource_instance_repo import ResourceInstanceRepository
from ..repositories.vf.exchange_repo import ExchangeRepository


class VFQueryService:
    """High-level query service for VF objects"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.listing_repo = ListingRepository(conn)
        self.resource_instance_repo = ResourceInstanceRepository(conn)
        self.exchange_repo = ExchangeRepository(conn)

    def find_offers(
        self,
        category: Optional[ResourceCategory] = None,
        location_id: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Listing]:
        """
        Find offers with filters.

        Args:
            category: Filter by resource category
            location_id: Filter by location
            active_only: Only return active offers
            limit: Maximum results

        Returns:
            List of matching offers
        """
        status = "active" if active_only else None
        return self.listing_repo.find_offers(
            category=category,
            location_id=location_id,
            status=status,
            limit=limit
        )

    def find_needs(
        self,
        category: Optional[ResourceCategory] = None,
        location_id: Optional[str] = None,
        active_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Listing]:
        """
        Find needs with filters.

        Args:
            category: Filter by resource category
            location_id: Filter by location
            active_only: Only return active needs
            limit: Maximum results

        Returns:
            List of matching needs
        """
        status = "active" if active_only else None
        return self.listing_repo.find_needs(
            category=category,
            location_id=location_id,
            status=status,
            limit=limit
        )

    def get_inventory(
        self,
        location_id: str,
        include_unavailable: bool = False
    ) -> List[ResourceInstance]:
        """
        Get inventory at a location.

        Args:
            location_id: Location ID
            include_unavailable: Include non-available resources

        Returns:
            List of resource instances
        """
        from ..models.vf.resource_instance import ResourceState

        if include_unavailable:
            return self.resource_instance_repo.find_by_location(location_id)
        else:
            return self.resource_instance_repo.find_by_location(
                location_id,
                state=ResourceState.AVAILABLE
            )

    def get_upcoming_exchanges(
        self,
        agent_id: Optional[str] = None,
        days_ahead: int = 7
    ) -> List[Exchange]:
        """
        Get upcoming exchanges.

        Args:
            agent_id: Filter by agent (provider or receiver)
            days_ahead: Look ahead this many days

        Returns:
            List of upcoming exchanges
        """
        return self.exchange_repo.find_upcoming(agent_id=agent_id)

    def find_expiring_resources(self, hours: int = 24) -> List[ResourceInstance]:
        """
        Find resources expiring soon.

        Args:
            hours: Hours until expiry

        Returns:
            List of expiring resource instances
        """
        return self.resource_instance_repo.find_expiring(hours=hours)

    def find_expiring_offers(self, hours: int = 24) -> List[Listing]:
        """
        Find offers expiring soon.

        Args:
            hours: Hours until expiry

        Returns:
            List of expiring offers
        """
        return self.listing_repo.find_expiring_soon(hours=hours)

    def get_perishables_alert(self, hours: int = 24) -> dict:
        """
        Get perishables alert (for Perishables Dispatcher agent).

        Returns:
            Dictionary with expiring resources and offers
        """
        return {
            "expiring_resources": self.find_expiring_resources(hours),
            "expiring_offers": self.find_expiring_offers(hours),
            "alert_threshold_hours": hours,
            "generated_at": datetime.now().isoformat()
        }
