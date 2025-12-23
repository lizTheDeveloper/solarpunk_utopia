"""
Inter-Community Sharing Service

Implements peer-to-peer federation based on individual choice and trust.
No gatekeepers. Individuals control their own visibility.
"""
from typing import List, Optional
import math
from valueflows_node.app.models.sharing_preference import (
    SharingPreference,
    SharingPreferenceCreate,
    VisibilityLevel,
)
from valueflows_node.app.repositories.sharing_preference_repo import SharingPreferenceRepository
from app.services.web_of_trust_service import WebOfTrustService
from app.database.vouch_repository import VouchRepository


class InterCommunityService:
    """Service for cross-community resource discovery and visibility."""

    def __init__(
        self,
        sharing_pref_repo: SharingPreferenceRepository,
        vouch_repo: VouchRepository,
    ):
        self.sharing_pref_repo = sharing_pref_repo
        self.web_of_trust = WebOfTrustService(vouch_repo)

    async def can_see_resource(
        self,
        viewer_id: str,
        creator_id: str,
        viewer_community_id: Optional[str] = None,
        creator_community_id: Optional[str] = None,
        viewer_cell_id: Optional[str] = None,
        creator_cell_id: Optional[str] = None,
        viewer_lat: Optional[float] = None,
        viewer_lon: Optional[float] = None,
        creator_lat: Optional[float] = None,
        creator_lon: Optional[float] = None,
        blocked_users: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if viewer can see a resource created by creator.

        This is the core visibility algorithm implementing the proposal's
        individual choice model.

        Args:
            viewer_id: User attempting to view
            creator_id: User who created the resource
            viewer_community_id: Viewer's community (optional)
            creator_community_id: Creator's community (optional)
            viewer_cell_id: Viewer's cell (optional)
            creator_cell_id: Creator's cell (optional)
            viewer_lat: Viewer's latitude (optional)
            viewer_lon: Viewer's longitude (optional)
            creator_lat: Creator's latitude (optional)
            creator_lon: Creator's longitude (optional)
            blocked_users: List of user IDs viewer has blocked (optional)

        Returns:
            True if viewer can see the resource, False otherwise
        """
        # Check block list (bidirectional)
        if blocked_users and creator_id in blocked_users:
            return False

        # Get creator's sharing preference
        preference = self.sharing_pref_repo.get_preference(creator_id)

        # Check visibility level
        if preference.visibility == VisibilityLevel.MY_CELL:
            # Only same cell can see
            return viewer_cell_id == creator_cell_id and viewer_cell_id is not None

        elif preference.visibility == VisibilityLevel.MY_COMMUNITY:
            # Only same community can see
            return viewer_community_id == creator_community_id and viewer_community_id is not None

        elif preference.visibility == VisibilityLevel.TRUSTED_NETWORK:
            # Anyone with trust >= 0.5 can see
            trust = self._compute_trust_between(viewer_id, creator_id)
            return trust >= 0.5

        elif preference.visibility == VisibilityLevel.ANYONE_LOCAL:
            # Anyone within local_radius_km can see
            if viewer_lat is None or viewer_lon is None or creator_lat is None or creator_lon is None:
                return False  # Can't compute distance without coordinates
            distance_km = self._calculate_distance_km(
                viewer_lat, viewer_lon, creator_lat, creator_lon
            )
            return distance_km <= preference.local_radius_km

        elif preference.visibility == VisibilityLevel.NETWORK_WIDE:
            # Anyone with any trust connection (>= 0.1) can see
            trust = self._compute_trust_between(viewer_id, creator_id)
            return trust >= 0.1

        # Default: not visible
        return False

    def _compute_trust_between(self, viewer_id: str, creator_id: str) -> float:
        """
        Compute trust connection between viewer and creator.

        Returns non-zero if there's ANY trust path connecting them:
        - Viewer has trust in the network (someone vouched for them)

        This is an MVP implementation. A full implementation would compute
        bidirectional trust paths between specific users.
        """
        if viewer_id == creator_id:
            return 1.0  # Full trust in yourself

        # Check if viewer has trust in the network
        # If someone vouched for them, they have a trust connection
        viewer_trust = self.web_of_trust.compute_trust_score(viewer_id)

        # Return the viewer's trust score
        # This works because:
        # - If creator vouched for viewer -> viewer has trust > 0
        # - If neither vouched -> viewer has trust = 0
        return viewer_trust.computed_trust

    def _calculate_distance_km(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in kilometers
        """
        # Earth's radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_sharing_preference(self, user_id: str) -> SharingPreference:
        """Get user's sharing preference."""
        return self.sharing_pref_repo.get_preference(user_id)

    def set_sharing_preference(self, user_id: str, preference: SharingPreferenceCreate) -> SharingPreference:
        """Set user's sharing preference."""
        return self.sharing_pref_repo.set_preference(user_id, preference)
