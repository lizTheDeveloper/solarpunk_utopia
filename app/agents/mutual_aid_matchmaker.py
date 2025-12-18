"""
Mutual Aid Matchmaker Agent

Matches offers with needs based on category, location, time, and quantity.
Creates match proposals that require approval from both parties.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class MutualAidMatchmaker(BaseAgent):
    """
    Analyzes offers and needs to propose mutually beneficial matches.

    Scores matches based on:
    - Category match (exact or compatible)
    - Location proximity
    - Time overlap (availability windows)
    - Quantity fit
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="mutual-aid-matchmaker",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Find and propose offer/need matches.

        Returns:
            List of match proposals
        """
        proposals = []

        # Get active offers and needs
        offers = await self._get_active_offers()
        needs = await self._get_active_needs()

        logger.info(f"Analyzing {len(offers)} offers and {len(needs)} needs")

        # Find matches
        matches = await self._find_matches(offers, needs)

        # Create proposals for high-scoring matches
        for match in matches:
            if match["score"] >= self.config.get("min_match_score", 0.6):
                proposal = await self._create_match_proposal(match)
                if proposal:
                    proposals.append(proposal)

        logger.info(f"Created {len(proposals)} match proposals")
        return proposals

    async def _get_active_offers(self) -> List[Dict[str, Any]]:
        """
        Query active offers from VF database.

        Returns:
            List of offer records
        """
        # TODO: Query actual VF database
        # For now, return mock data
        return [
            {
                "id": "offer:alice-tomatoes",
                "user_id": "alice",
                "user_name": "Alice",
                "resource": "tomatoes",
                "category": "food:produce",
                "quantity": 5.0,
                "unit": "lbs",
                "location": "Community Garden",
                "location_coords": (37.7749, -122.4194),  # SF
                "available_from": datetime(2025, 12, 18, 9, 0),
                "available_until": datetime(2025, 12, 20, 18, 0),
                "preferences": ["morning handoff preferred"],
                "bundle_id": "bundle:offer-alice-tomatoes",
            },
            {
                "id": "offer:carol-seeds",
                "user_id": "carol",
                "user_name": "Carol",
                "resource": "tomato seeds",
                "category": "seeds:vegetables",
                "quantity": 10,
                "unit": "packets",
                "location": "Seed Library",
                "location_coords": (37.7750, -122.4195),
                "available_from": datetime(2025, 12, 17, 10, 0),
                "available_until": datetime(2025, 12, 30, 17, 0),
                "preferences": ["heirloom varieties"],
                "bundle_id": "bundle:offer-carol-seeds",
            },
        ]

    async def _get_active_needs(self) -> List[Dict[str, Any]]:
        """
        Query active needs from VF database.

        Returns:
            List of need records
        """
        # TODO: Query actual VF database
        return [
            {
                "id": "need:bob-tomatoes",
                "user_id": "bob",
                "user_name": "Bob",
                "resource": "tomatoes",
                "category": "food:produce",
                "quantity": 3.0,
                "unit": "lbs",
                "location": "Community Kitchen",
                "location_coords": (37.7748, -122.4193),
                "needed_by": datetime(2025, 12, 19, 12, 0),
                "purpose": "sauce making",
                "constraints": ["will provide container"],
                "bundle_id": "bundle:need-bob-tomatoes",
            },
            {
                "id": "need:dave-seeds",
                "user_id": "dave",
                "user_name": "Dave",
                "resource": "vegetable seeds",
                "category": "seeds:vegetables",
                "quantity": 5,
                "unit": "packets",
                "location": "Home Garden",
                "location_coords": (37.7751, -122.4196),
                "needed_by": datetime(2025, 12, 25, 0, 0),
                "purpose": "spring planting",
                "constraints": ["organic preferred"],
                "bundle_id": "bundle:need-dave-seeds",
            },
        ]

    async def _find_matches(
        self,
        offers: List[Dict[str, Any]],
        needs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find and score potential matches.

        Returns:
            List of matches with scores
        """
        matches = []

        for offer in offers:
            for need in needs:
                score, match_data = await self._score_match(offer, need)
                if score > 0:
                    matches.append({
                        "score": score,
                        "offer": offer,
                        "need": need,
                        "match_data": match_data,
                    })

        # Sort by score descending
        matches.sort(key=lambda m: m["score"], reverse=True)
        return matches

    async def _score_match(
        self,
        offer: Dict[str, Any],
        need: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Score a potential match between offer and need.

        Returns:
            Tuple of (score 0-1, match details)
        """
        score = 0.0
        match_data = {}

        # Category match (0-0.4)
        category_score = self._score_category_match(
            offer.get("category", ""),
            need.get("category", "")
        )
        score += category_score * 0.4
        match_data["category_score"] = category_score

        # Location proximity (0-0.3)
        location_score = self._score_location_proximity(
            offer.get("location_coords"),
            need.get("location_coords")
        )
        score += location_score * 0.3
        match_data["location_score"] = location_score

        # Time overlap (0-0.2)
        time_score = self._score_time_overlap(offer, need)
        score += time_score * 0.2
        match_data["time_score"] = time_score

        # Quantity fit (0-0.1)
        quantity_score = self._score_quantity_fit(offer, need)
        score += quantity_score * 0.1
        match_data["quantity_score"] = quantity_score

        return score, match_data

    def _score_category_match(self, offer_cat: str, need_cat: str) -> float:
        """Score category match (exact or compatible)"""
        if not offer_cat or not need_cat:
            return 0.0

        # Exact match
        if offer_cat == need_cat:
            return 1.0

        # Parent category match (e.g., "food:produce" matches "food:*")
        offer_parts = offer_cat.split(":")
        need_parts = need_cat.split(":")

        if offer_parts[0] == need_parts[0]:
            return 0.7  # Same top-level category

        # Semantic similarity (if LLM available)
        # For now, simple keyword matching
        offer_keywords = set(offer_cat.lower().split(":"))
        need_keywords = set(need_cat.lower().split(":"))
        overlap = len(offer_keywords & need_keywords)
        if overlap > 0:
            return 0.5

        return 0.0

    def _score_location_proximity(
        self,
        offer_coords: Optional[Tuple[float, float]],
        need_coords: Optional[Tuple[float, float]]
    ) -> float:
        """Score location proximity (closer is better)"""
        if not offer_coords or not need_coords:
            return 0.5  # Unknown distance, neutral score

        # Simple distance calculation (Haversine would be more accurate)
        lat_diff = abs(offer_coords[0] - need_coords[0])
        lon_diff = abs(offer_coords[1] - need_coords[1])
        distance = (lat_diff**2 + lon_diff**2)**0.5

        # Score: 1.0 for <0.01 degrees (~1km), 0.5 for 0.05 degrees (~5km), 0 for >0.1 degrees
        if distance < 0.01:
            return 1.0
        elif distance < 0.05:
            return 0.7
        elif distance < 0.1:
            return 0.4
        else:
            return 0.1  # Still possible but not ideal

    def _score_time_overlap(self, offer: Dict, need: Dict) -> float:
        """Score time availability overlap"""
        offer_start = offer.get("available_from")
        offer_end = offer.get("available_until")
        need_by = need.get("needed_by")

        if not offer_start or not offer_end or not need_by:
            return 0.5  # Unknown times, neutral score

        # Check if need can be fulfilled within offer window
        if offer_start <= need_by <= offer_end:
            # Calculate how much time buffer exists
            buffer_hours = (offer_end - need_by).total_seconds() / 3600
            if buffer_hours > 24:
                return 1.0  # Plenty of time
            elif buffer_hours > 6:
                return 0.8
            else:
                return 0.5  # Tight timing
        else:
            return 0.0  # No overlap

    def _score_quantity_fit(self, offer: Dict, need: Dict) -> float:
        """Score quantity fit (offer meets or exceeds need)"""
        offer_qty = offer.get("quantity", 0)
        need_qty = need.get("quantity", 0)
        offer_unit = offer.get("unit", "")
        need_unit = need.get("unit", "")

        if not offer_qty or not need_qty:
            return 0.5  # Unknown quantities

        if offer_unit != need_unit:
            return 0.5  # Unit conversion needed

        if offer_qty >= need_qty:
            # Exact match or slight overage is ideal
            ratio = offer_qty / need_qty
            if ratio <= 1.5:
                return 1.0  # Good fit
            else:
                return 0.7  # Much more than needed, but workable
        else:
            # Partial fulfillment
            return offer_qty / need_qty * 0.6

    async def _create_match_proposal(self, match: Dict[str, Any]) -> Optional[Proposal]:
        """
        Create a match proposal from scored match.

        Args:
            match: Match data including offer, need, and scores

        Returns:
            Match proposal
        """
        offer = match["offer"]
        need = match["need"]
        score = match["score"]
        match_data = match["match_data"]

        # Build explanation
        explanation = (
            f"{offer['user_name']} has {offer['quantity']} {offer['unit']} {offer['resource']} "
            f"available for {self._format_time_window(offer)}. "
            f"{need['user_name']} needs {need['resource']} for {need.get('purpose', 'use')}. "
            f"Both are near {self._describe_location(offer, need)}."
        )

        # Collect constraints from both parties
        constraints = []
        if offer.get("preferences"):
            constraints.extend([f"Offer: {p}" for p in offer["preferences"]])
        if need.get("constraints"):
            constraints.extend([f"Need: {c}" for c in need["constraints"]])

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.MATCH,
            title=f"Match: {offer['resource']} ({offer['user_name']} → {need['user_name']})",
            explanation=explanation,
            inputs_used=[
                offer["bundle_id"],
                need["bundle_id"],
                "location_data",
            ],
            constraints=constraints,
            data={
                "offer_id": offer["id"],
                "need_id": need["id"],
                "match_score": score,
                "scores_breakdown": match_data,
                "quantity": min(offer["quantity"], need["quantity"]),
                "unit": offer["unit"],
                "suggested_time": self._suggest_handoff_time(offer, need),
                "suggested_location": self._suggest_handoff_location(offer, need),
            },
            requires_approval=[offer["user_id"], need["user_id"]],
        )

    def _format_time_window(self, offer: Dict) -> str:
        """Format time availability window"""
        start = offer.get("available_from")
        end = offer.get("available_until")
        if not start or not end:
            return "flexible timing"

        days_available = (end - start).days
        if days_available == 0:
            return "today"
        elif days_available == 1:
            return "1 day"
        else:
            return f"{days_available} days"

    def _describe_location(self, offer: Dict, need: Dict) -> str:
        """Describe relative locations"""
        offer_loc = offer.get("location", "unspecified location")
        need_loc = need.get("location", "unspecified location")

        if offer_loc == need_loc:
            return offer_loc
        else:
            return f"{offer_loc} and {need_loc}"

    def _suggest_handoff_time(self, offer: Dict, need: Dict) -> str:
        """Suggest optimal handoff time"""
        # Simple heuristic: midpoint of overlap
        offer_start = offer.get("available_from")
        need_by = need.get("needed_by")

        if offer_start and need_by:
            # Suggest a time that gives some buffer
            buffer_hours = (need_by - offer_start).total_seconds() / 3600
            if buffer_hours > 24:
                # Suggest tomorrow morning if plenty of time
                return "Tomorrow morning (9-10am)"
            else:
                # Suggest ASAP
                return "As soon as convenient"

        return "Coordinate directly"

    def _suggest_handoff_location(self, offer: Dict, need: Dict) -> str:
        """Suggest optimal handoff location"""
        offer_loc = offer.get("location", "")
        need_loc = need.get("location", "")

        # Prefer public commons spaces
        if "Community" in offer_loc or "Community" in need_loc:
            return "Community Kitchen or Garden"

        return f"{offer_loc} (or {need_loc})"
