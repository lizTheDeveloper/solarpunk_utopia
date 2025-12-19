"""
Inventory/Pantry Agent (Opt-In)

Analyzes usage patterns and predicts shortages.
Proposes replenishment or alternatives.

PRIVACY: This agent is opt-in and disabled by default.
No surveillance required to participate in commune.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class InventoryAgent(BaseAgent):
    """
    Predicts inventory shortages and proposes replenishment (opt-in).

    Analyzes:
    - Current inventory levels
    - Historical usage rates (from Events)
    - Upcoming Plans requiring resources
    - Seasonal patterns

    Privacy-preserving: Users opt-in to share inventory data.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        # Default to disabled - users must opt-in
        if config:
            config.setdefault("enabled", False)
        else:
            config = AgentConfig(enabled=False)

        super().__init__(
            agent_name="inventory-agent",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze inventory and predict shortages.

        Only analyzes for users who have opted in.

        Returns:
            List of replenishment/shortage proposals
        """
        if not self.enabled:
            logger.info("Inventory agent is disabled (opt-in required)")
            return []

        proposals = []

        # Get current inventory (only from opted-in users)
        inventory = await self._get_inventory()

        # Get upcoming resource needs from Plans
        upcoming_needs = await self._get_upcoming_resource_needs()

        # Check each inventory item against upcoming needs
        for item in inventory:
            shortage_check = await self._check_for_shortage(item, upcoming_needs)

            if shortage_check["is_short"]:
                proposal = await self._propose_replenishment(item, shortage_check)
                if proposal:
                    proposals.append(proposal)
            elif shortage_check.get("warn_low"):
                proposal = await self._propose_shortage_warning(item, shortage_check)
                if proposal:
                    proposals.append(proposal)

        logger.info(f"Created {len(proposals)} inventory proposals")
        return proposals

    async def _get_inventory(self) -> List[Dict[str, Any]]:
        """
        Query current inventory (opted-in users only).

        Returns:
            List of inventory items
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get all active offers (current inventory)
            inventory = await self.db_client.get_inventory_by_location()
            return inventory
        except Exception as e:
            logger.warning(f"Failed to query VF database: {e}")
            # Fallback to mock data if DB unavailable
            return [
                {
                    "id": "inv:tomato-seeds",
                    "resource": "tomato seeds",
                    "category": "seeds:vegetables",
                    "quantity": 5,
                    "unit": "packets",
                    "location": "Seed Library",
                    "owner": "community",
                "opt_in": True,  # Community pantry is opt-in by default
                "bundle_id": "bundle:inv-tomato-seeds",
            },
            {
                "id": "inv:compost",
                "resource": "compost",
                "category": "soil:amendments",
                "quantity": 200,
                "unit": "lbs",
                "location": "Garden Shed",
                "owner": "community",
                "opt_in": True,
                "bundle_id": "bundle:inv-compost",
            },
            {
                "id": "inv:canning-jars",
                "resource": "canning jars",
                "category": "tools:preservation",
                "quantity": 50,
                "unit": "jars",
                "location": "Community Kitchen",
                "owner": "community",
                "opt_in": True,
                "bundle_id": "bundle:inv-jars",
            },
        ]

    async def _get_upcoming_resource_needs(self) -> List[Dict[str, Any]]:
        """
        Query upcoming resource needs from Plans and Processes.

        Returns:
            List of resource requirements with dates
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get all active needs
            needs = await self.db_client.get_active_needs()
            return needs
        except Exception as e:
            logger.warning(f"Failed to query VF database for needs: {e}")
            # Fallback to mock data if DB unavailable
            return [
                {
                    "plan_id": "plan:spring-planting-2025",
                    "plan_name": "Spring Planting 2025",
                    "resource": "tomato seeds",
                    "quantity": 20,
                    "unit": "packets",
                    "needed_by": datetime(2025, 12, 28),
                    "purpose": "Spring planting work party",
            },
            {
                "plan_id": "plan:spring-planting-2025",
                "plan_name": "Spring Planting 2025",
                "resource": "compost",
                "quantity": 500,
                "unit": "lbs",
                "needed_by": datetime(2025, 12, 25),
                "purpose": "Soil preparation",
            },
        ]

    async def _check_for_shortage(
        self,
        item: Dict[str, Any],
        upcoming_needs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if item will be short for upcoming needs.

        Returns:
            Shortage analysis
        """
        current_qty = item["quantity"]
        resource = item["resource"]

        # Find matching upcoming needs
        matching_needs = [
            need for need in upcoming_needs
            if need["resource"] == resource and need["unit"] == item["unit"]
        ]

        if not matching_needs:
            return {"is_short": False}

        # Calculate total needed
        total_needed = sum(need["quantity"] for need in matching_needs)

        # Calculate gap
        gap = total_needed - current_qty

        # Check historical usage rate
        usage_rate = await self._calculate_usage_rate(item)

        # Days until first need
        days_until_needed = min(
            (need["needed_by"] - datetime.now(timezone.utc)).days
            for need in matching_needs
        )

        # Predict inventory at time of need
        predicted_qty = current_qty - (usage_rate * days_until_needed)

        return {
            "is_short": gap > 0,
            "warn_low": predicted_qty < total_needed * 0.5,  # Warn if <50% needed
            "gap": gap if gap > 0 else 0,
            "current_qty": current_qty,
            "total_needed": total_needed,
            "predicted_qty": predicted_qty,
            "days_until_needed": days_until_needed,
            "matching_needs": matching_needs,
            "usage_rate_per_day": usage_rate,
        }

    async def _calculate_usage_rate(self, item: Dict[str, Any]) -> float:
        """
        Calculate average usage rate from historical Events.

        Returns:
            Usage rate per day
        """
        # TODO: Query actual VF Events (consume) for this resource
        # For now, return estimated rate

        # Simple heuristic based on category
        category = item.get("category", "")

        if category.startswith("seeds:"):
            return 0.1  # Seeds used slowly
        elif category.startswith("soil:"):
            return 5.0  # Soil amendments used moderately
        elif category.startswith("tools:"):
            return 0.0  # Tools don't get consumed
        else:
            return 1.0  # Default moderate usage

    async def _propose_replenishment(
        self,
        item: Dict[str, Any],
        shortage_check: Dict[str, Any]
    ) -> Optional[Proposal]:
        """
        Propose creating Need for replenishment.

        Args:
            item: Inventory item
            shortage_check: Shortage analysis

        Returns:
            Replenishment proposal
        """
        gap = shortage_check["gap"]
        days_until = shortage_check["days_until_needed"]
        matching_needs = shortage_check["matching_needs"]

        # Find alternatives
        alternatives = await self._find_alternatives(item)

        explanation = (
            f"Current inventory: {item['quantity']} {item['unit']} {item['resource']}. "
            f"Upcoming needs require {shortage_check['total_needed']} {item['unit']} "
            f"in {days_until} days. "
            f"Gap: {gap} {item['unit']}."
        )

        constraints = []
        if item.get("preferences"):
            constraints.extend(item["preferences"])

        # Add plan-specific constraints
        for need in matching_needs[:2]:  # First 2 needs
            if need.get("constraints"):
                constraints.extend(need["constraints"])

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.REPLENISHMENT,
            title=f"Replenish: {item['resource']} ({gap} {item['unit']} needed)",
            explanation=explanation,
            inputs_used=[
                item["bundle_id"],
                *[need.get("bundle_id", f"plan:{need['plan_id']}") for need in matching_needs],
                "usage_analysis",
            ],
            constraints=constraints,
            data={
                "item": item,
                "gap_quantity": gap,
                "gap_unit": item["unit"],
                "days_until_needed": days_until,
                "matching_needs": matching_needs,
                "alternatives": alternatives,
                "suggested_action": self._suggest_replenishment_action(item, gap),
            },
            requires_approval=["pantry-manager"],
        )

    async def _propose_shortage_warning(
        self,
        item: Dict[str, Any],
        shortage_check: Dict[str, Any]
    ) -> Optional[Proposal]:
        """
        Propose warning for low (but not yet short) inventory.

        Args:
            item: Inventory item
            shortage_check: Shortage analysis

        Returns:
            Warning proposal
        """
        predicted = shortage_check["predicted_qty"]
        needed = shortage_check["total_needed"]
        days_until = shortage_check["days_until_needed"]

        explanation = (
            f"Low inventory warning: {item['resource']}. "
            f"Current: {item['quantity']} {item['unit']}, "
            f"predicted at {predicted:.1f} {item['unit']} in {days_until} days. "
            f"Needed: {needed} {item['unit']}. "
            f"Consider replenishing soon."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.SHORTAGE_WARNING,
            title=f"Low inventory: {item['resource']}",
            explanation=explanation,
            inputs_used=[
                item["bundle_id"],
                "usage_analysis",
            ],
            constraints=[],
            data={
                "item": item,
                "predicted_qty": predicted,
                "needed_qty": needed,
                "days_until_needed": days_until,
                "urgency": "low" if days_until > 14 else "medium",
            },
            requires_approval=["pantry-manager"],
        )

    async def _find_alternatives(self, item: Dict[str, Any]) -> List[str]:
        """
        Find alternative sources or substitutes.

        Returns:
            List of alternative suggestions
        """
        alternatives = []
        category = item.get("category", "")

        if category.startswith("seeds:"):
            alternatives.extend([
                "Check with members for saved seeds",
                "Request from regional seed library",
                "Order from cooperative seed company",
            ])
        elif category.startswith("soil:"):
            alternatives.extend([
                "Make compost from food scraps",
                "Source from community leaf collection",
                "Trade with neighboring gardens",
            ])
        elif category.startswith("tools:"):
            alternatives.extend([
                "Borrow from tool library",
                "Request as mutual aid offer",
                "DIY construction work party",
            ])
        else:
            alternatives.extend([
                "Check for internal sourcing first",
                "Request as mutual aid offer",
                "Purchase from cooperative supplier",
            ])

        return alternatives

    def _suggest_replenishment_action(
        self,
        item: Dict[str, Any],
        gap: float
    ) -> str:
        """
        Suggest best replenishment action.

        Returns:
            Action suggestion
        """
        if gap < 10:
            return f"Create mutual aid Need for {gap} {item['unit']} {item['resource']}"
        elif gap < 50:
            return f"Request from regional network or purchase small batch"
        else:
            return f"Coordinate bulk purchase with neighboring communes to reduce cost"
