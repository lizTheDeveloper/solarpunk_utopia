"""
Mutual Aid Matchmaker Agent

Matches offers with needs based on category, location, time, and quantity.
Creates match proposals that require approval from both parties.

Now with algorithmic transparency:
- Detailed match explanations
- Adjustable weights per community
- Bias detection and audit trail
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType
from app.models.algorithmic_transparency import (
    MatchExplanation,
    MatchingAuditLog,
    CategoryMatchType,
)
from app.repositories.transparency_repository import TransparencyRepository


logger = logging.getLogger(__name__)

# Agent version for audit trail
AGENT_VERSION = "1.0.0-transparency"


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
        transparency_repo: Optional[TransparencyRepository] = None,
    ):
        super().__init__(
            agent_name="mutual-aid-matchmaker",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )
        self.transparency_repo = transparency_repo or TransparencyRepository()
        self._weights = None  # Will be loaded on first use

    async def analyze(self) -> List[Proposal]:
        """
        Find and propose offer/need matches.

        Returns:
            List of match proposals
        """
        proposals = []

        # Load weights configuration for this community
        community_id = self.config.get("community_id")
        weights = await self.transparency_repo.get_active_weights(community_id)
        self._weights = weights

        logger.info(f"Using weights: category={weights.category_weight}, "
                   f"location={weights.location_weight}, time={weights.time_weight}, "
                   f"quantity={weights.quantity_weight}")

        # Get active offers and needs
        offers = await self._get_active_offers()
        needs = await self._get_active_needs()

        logger.info(f"Analyzing {len(offers)} offers and {len(needs)} needs")

        # Find matches
        matches = await self._find_matches(offers, needs)

        # Get threshold from config
        threshold_score = self.config.get("min_match_score", 0.6)

        # Create proposals for high-scoring matches AND log all decisions
        for match in matches:
            # Log to audit trail (whether matched or not)
            await self._log_audit_trail(
                match,
                matched=match["score"] >= threshold_score,
                threshold_score=threshold_score,
            )

            if match["score"] >= threshold_score:
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
        if self.db_client is None:
            # Import here to avoid circular dependencies
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            offers = await self.db_client.get_active_offers()
            return offers
        except Exception as e:
            logger.warning(f"Failed to query VF database, using empty list: {e}")
            return []

    async def _get_active_needs(self) -> List[Dict[str, Any]]:
        """
        Query active needs from VF database.

        Returns:
            List of need records
        """
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            needs = await self.db_client.get_active_needs()
            return needs
        except Exception as e:
            logger.warning(f"Failed to query VF database, using empty list: {e}")
            return []

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

        Uses community-configured weights for transparency and adjustability.

        Returns:
            Tuple of (score 0-1, match details)
        """
        score = 0.0
        match_data = {}

        # Get weights (loaded in analyze())
        weights = self._weights
        if not weights:
            # Fallback to defaults if not loaded
            weights = type('obj', (object,), {
                'category_weight': 0.4,
                'location_weight': 0.3,
                'time_weight': 0.2,
                'quantity_weight': 0.1,
            })()

        # Category match
        category_score, category_details = self._score_category_match(
            offer.get("category", ""),
            need.get("category", "")
        )
        score += category_score * weights.category_weight
        match_data["category_score"] = category_score
        match_data["category_weight"] = weights.category_weight
        match_data.update(category_details)

        # Location proximity
        location_score, location_details = self._score_location_proximity(
            offer.get("location_coords"),
            need.get("location_coords")
        )
        score += location_score * weights.location_weight
        match_data["location_score"] = location_score
        match_data["location_weight"] = weights.location_weight
        match_data.update(location_details)

        # Time overlap
        time_score, time_details = self._score_time_overlap(offer, need)
        score += time_score * weights.time_weight
        match_data["time_score"] = time_score
        match_data["time_weight"] = weights.time_weight
        match_data.update(time_details)

        # Quantity fit
        quantity_score, quantity_details = self._score_quantity_fit(offer, need)
        score += quantity_score * weights.quantity_weight
        match_data["quantity_score"] = quantity_score
        match_data["quantity_weight"] = weights.quantity_weight
        match_data.update(quantity_details)

        return score, match_data

    def _score_category_match(self, offer_cat: str, need_cat: str) -> Tuple[float, Dict[str, Any]]:
        """Score category match (exact or compatible)"""
        if not offer_cat or not need_cat:
            return 0.0, {"category_match_type": CategoryMatchType.NONE}

        # Exact match
        if offer_cat == need_cat:
            return 1.0, {"category_match_type": CategoryMatchType.EXACT}

        # Parent category match (e.g., "food:produce" matches "food:*")
        offer_parts = offer_cat.split(":")
        need_parts = need_cat.split(":")

        if offer_parts[0] == need_parts[0]:
            return 0.7, {"category_match_type": CategoryMatchType.PARENT}

        # Semantic similarity (if LLM available)
        # For now, simple keyword matching
        offer_keywords = set(offer_cat.lower().split(":"))
        need_keywords = set(need_cat.lower().split(":"))
        overlap = len(offer_keywords & need_keywords)
        if overlap > 0:
            return 0.5, {"category_match_type": CategoryMatchType.SEMANTIC}

        return 0.0, {"category_match_type": CategoryMatchType.NONE}

    def _score_location_proximity(
        self,
        offer_coords: Optional[Tuple[float, float]],
        need_coords: Optional[Tuple[float, float]]
    ) -> Tuple[float, Dict[str, Any]]:
        """Score location proximity (closer is better)"""
        if not offer_coords or not need_coords:
            return 0.5, {"distance_km": None, "distance_description": "Distance unknown"}

        # Simple distance calculation (Haversine would be more accurate)
        lat_diff = abs(offer_coords[0] - need_coords[0])
        lon_diff = abs(offer_coords[1] - need_coords[1])
        distance_degrees = (lat_diff**2 + lon_diff**2)**0.5
        distance_km = distance_degrees * 111  # Rough conversion: 1 degree ≈ 111 km

        # Score: 1.0 for <1km, 0.7 for <5km, 0.4 for <10km, 0.1 for >10km
        if distance_degrees < 0.01:
            score = 1.0
            description = f"Very close ({distance_km:.1f} km)"
        elif distance_degrees < 0.05:
            score = 0.7
            description = f"Nearby ({distance_km:.1f} km)"
        elif distance_degrees < 0.1:
            score = 0.4
            description = f"Moderate distance ({distance_km:.1f} km)"
        else:
            score = 0.1
            description = f"Far apart ({distance_km:.1f} km)"

        return score, {
            "distance_km": round(distance_km, 1),
            "distance_description": description,
        }

    def _score_time_overlap(self, offer: Dict, need: Dict) -> Tuple[float, Dict[str, Any]]:
        """Score time availability overlap"""
        offer_start = offer.get("available_from")
        offer_end = offer.get("available_until")
        need_by = need.get("needed_by")

        if not offer_start or not offer_end or not need_by:
            return 0.5, {"time_buffer_hours": None}

        # Check if need can be fulfilled within offer window
        if offer_start <= need_by <= offer_end:
            # Calculate how much time buffer exists
            buffer_hours = (offer_end - need_by).total_seconds() / 3600
            if buffer_hours > 24:
                score = 1.0
            elif buffer_hours > 6:
                score = 0.8
            else:
                score = 0.5
            return score, {"time_buffer_hours": round(buffer_hours, 1)}
        else:
            return 0.0, {"time_buffer_hours": 0.0}

    def _score_quantity_fit(self, offer: Dict, need: Dict) -> Tuple[float, Dict[str, Any]]:
        """Score quantity fit (offer meets or exceeds need)"""
        offer_qty = offer.get("quantity", 0)
        need_qty = need.get("quantity", 0)
        offer_unit = offer.get("unit", "")
        need_unit = need.get("unit", "")

        if not offer_qty or not need_qty:
            return 0.5, {"quantity_ratio": None}

        if offer_unit != need_unit:
            return 0.5, {"quantity_ratio": None}

        ratio = offer_qty / need_qty if need_qty > 0 else 0

        if offer_qty >= need_qty:
            # Exact match or slight overage is ideal
            if ratio <= 1.5:
                score = 1.0
            else:
                score = 0.7
        else:
            # Partial fulfillment
            score = ratio * 0.6

        return score, {"quantity_ratio": round(ratio, 2)}

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

    async def _log_audit_trail(
        self,
        match: Dict[str, Any],
        matched: bool,
        threshold_score: float,
    ) -> None:
        """
        Log matching decision to audit trail for bias detection.

        Logs both successful matches and rejected candidates.
        """
        offer = match["offer"]
        need = match["need"]
        match_data = match["match_data"]

        audit_log = MatchingAuditLog(
            id=f"audit:{uuid.uuid4()}",
            match_id=match.get("match_id") if matched else None,
            offer_id=offer["id"],
            need_id=need["id"],
            match_score=match["score"],
            threshold_score=threshold_score,
            matched=matched,
            weights_config_id=self._weights.id if self._weights else "weights:system:default",
            provider_zone=offer.get("location_zone"),
            receiver_zone=need.get("location_zone"),
            offer_category=offer.get("category"),
            need_category=need.get("category"),
            agent_version=AGENT_VERSION,
        )

        try:
            await self.transparency_repo.create_audit_log(audit_log)
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")

    async def create_match_explanation(
        self,
        match_id: str,
        match: Dict[str, Any],
    ) -> MatchExplanation:
        """
        Create detailed explanation for a match.

        Called after match proposal is accepted.
        """
        offer = match["offer"]
        need = match["need"]
        match_data = match["match_data"]

        # Build human-readable explanation
        explanation_parts = []
        explanation_parts.append(
            f"Matched because {offer['user_name']} offers {offer['resource']} "
            f"and {need['user_name']} needs it."
        )

        # Add key factors
        if match_data.get("distance_description"):
            explanation_parts.append(match_data["distance_description"])

        if match_data.get("category_match_type") == CategoryMatchType.EXACT:
            explanation_parts.append("Exact category match")

        if match_data.get("time_buffer_hours", 0) > 24:
            explanation_parts.append("Plenty of time available")

        explanation_text = ". ".join(explanation_parts) + "."

        explanation = MatchExplanation(
            id=f"explanation:{uuid.uuid4()}",
            match_id=match_id,
            category_score=match_data["category_score"],
            location_score=match_data["location_score"],
            time_score=match_data["time_score"],
            quantity_score=match_data["quantity_score"],
            total_score=match["score"],
            category_weight=match_data["category_weight"],
            location_weight=match_data["location_weight"],
            time_weight=match_data["time_weight"],
            quantity_weight=match_data["quantity_weight"],
            explanation_text=explanation_text,
            distance_km=match_data.get("distance_km"),
            distance_description=match_data.get("distance_description"),
            category_match_type=match_data.get("category_match_type"),
            time_buffer_hours=match_data.get("time_buffer_hours"),
            quantity_ratio=match_data.get("quantity_ratio"),
        )

        # Store explanation
        try:
            await self.transparency_repo.create_match_explanation(explanation)
        except Exception as e:
            logger.error(f"Failed to create match explanation: {e}")

        return explanation
