"""
Conquest of Bread Agent

Dynamically toggles between "Common Heap" (abundance) and rationing modes.

Key Features:
- Common Heap: When supply > demand * 1.5, disable accounting (just take it)
- Needs-First Rationing: When scarce, prioritize survival needs over comfort
- Well-Being Index: Track satisfaction of basic needs across population

Based on proposal: openspec/changes/conquest-of-bread-agent/proposal.md
Inspired by Kropotkin's "The Conquest of Bread"
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"


class ConquestOfBreadAgent(BaseAgent):
    """
    Dynamically manages economic modes based on resource abundance.

    This agent:
    1. Toggles resources to "Heap Mode" when abundant
    2. Enables rationing when resources become scarce
    3. Prioritizes survival needs over comfort needs
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="conquest-of-bread",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze resource levels and propose mode changes.

        Returns:
            List of heap mode toggle or rationing mode proposals
        """
        proposals = []

        # Get abundance threshold from config
        abundance_multiplier = self.config.get("abundance_multiplier", 1.5)
        scarcity_weeks = self.config.get("scarcity_threshold_weeks", 2)

        # Check all tracked resources
        resources = await self._get_tracked_resources()

        for resource in resources:
            # Check for abundance -> Heap Mode
            if await self._should_enable_heap_mode(resource, abundance_multiplier):
                proposal = await self._create_heap_mode_proposal(resource, enable=True)
                proposals.append(proposal)

            # Check for scarcity -> Rationing Mode
            elif await self._should_enable_rationing(resource, scarcity_weeks):
                proposal = await self._create_rationing_proposal(resource)
                proposals.append(proposal)

            # Check if Heap Mode should be disabled (stock dropping)
            elif await self._should_disable_heap_mode(resource):
                proposal = await self._create_heap_mode_proposal(resource, enable=False)
                proposals.append(proposal)

        return proposals

    async def _get_tracked_resources(self) -> List[Dict[str, Any]]:
        """
        Get all resources that should be tracked for abundance/scarcity.

        Returns:
            List of resource data with current stock and consumption estimates
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_tracked_resources()

        try:
            # Query all resource specs
            resource_specs = await self.db_client.get_resource_specs()

            # For each resource spec, calculate current inventory and consumption
            tracked_resources = []

            for spec in resource_specs:
                # Get current inventory (active offers for this resource)
                offers = await self.db_client.get_active_offers()

                # Filter offers for this resource spec
                resource_offers = [
                    o for o in offers
                    if o.get('resource_spec_id') == spec['id']
                ]

                # Calculate total stock (sum of all offer quantities)
                total_stock = sum(o.get('quantity', 0) for o in resource_offers)

                # Estimate weekly consumption from historical data
                # For now, use a simple heuristic: 10% of current stock per week
                # TODO: Query actual exchange history for accurate consumption rate
                weekly_consumption = total_stock * 0.10 if total_stock > 0 else 1.0

                # Check if heap mode is enabled for this resource
                # TODO: Query from resource_specs table or separate heap_mode_config table
                heap_mode_enabled = spec.get('heap_mode_enabled', False)

                tracked_resources.append({
                    "resource_id": spec['id'],
                    "name": spec['name'],
                    "current_stock_kg": total_stock,
                    "weekly_consumption_kg": weekly_consumption,
                    "heap_mode_enabled": heap_mode_enabled,
                    "category": spec.get('category', 'unknown'),
                    "unit": spec.get('unit', 'units'),
                })

            logger.info(f"Tracked {len(tracked_resources)} resources from ValueFlows database")
            return tracked_resources

        except Exception as e:
            logger.error(f"Error querying tracked resources: {e}", exc_info=True)
            return self._get_mock_tracked_resources()

    def _get_mock_tracked_resources(self) -> List[Dict[str, Any]]:
        """Fallback mock data for testing"""
        logger.warning("Using mock tracked resources data")
        return [
            {
                "resource_id": "resource:tomatoes",
                "name": "Tomatoes",
                "current_stock_kg": 600,
                "weekly_consumption_kg": 80,
                "heap_mode_enabled": False,
            },
            {
                "resource_id": "resource:firewood",
                "name": "Firewood",
                "current_stock_kg": 150,
                "weekly_consumption_kg": 100,
                "heap_mode_enabled": False,
            },
        ]

    async def _should_enable_heap_mode(
        self,
        resource: Dict[str, Any],
        multiplier: float
    ) -> bool:
        """
        Check if resource should enter Heap Mode (abundance).

        Args:
            resource: Resource data
            multiplier: Abundance threshold multiplier

        Returns:
            True if should enable Heap Mode
        """
        if resource.get("heap_mode_enabled"):
            return False  # Already in Heap Mode

        stock = resource["current_stock_kg"]
        weekly_consumption = resource["weekly_consumption_kg"]

        # Heap Mode trigger: Stock > Weekly_Consumption * multiplier
        threshold = weekly_consumption * multiplier

        return stock >= threshold

    async def _should_enable_rationing(
        self,
        resource: Dict[str, Any],
        scarcity_weeks: float
    ) -> bool:
        """
        Check if resource should enter Rationing Mode.

        Args:
            resource: Resource data
            scarcity_weeks: Weeks of supply threshold

        Returns:
            True if should enable rationing
        """
        stock = resource["current_stock_kg"]
        weekly_consumption = resource["weekly_consumption_kg"]

        if weekly_consumption == 0:
            return False

        weeks_remaining = stock / weekly_consumption

        return weeks_remaining < scarcity_weeks

    async def _should_disable_heap_mode(
        self,
        resource: Dict[str, Any]
    ) -> bool:
        """
        Check if Heap Mode should be disabled (stock dropping rapidly).

        Args:
            resource: Resource data

        Returns:
            True if should disable Heap Mode
        """
        if not resource.get("heap_mode_enabled"):
            return False  # Not in Heap Mode

        # Disable if stock drops below 1.2x weekly consumption
        stock = resource["current_stock_kg"]
        weekly_consumption = resource["weekly_consumption_kg"]

        threshold = weekly_consumption * 1.2

        return stock < threshold

    async def _create_heap_mode_proposal(
        self,
        resource: Dict[str, Any],
        enable: bool
    ) -> Proposal:
        """
        Create a proposal to toggle Heap Mode.

        Args:
            resource: Resource data
            enable: True to enable, False to disable

        Returns:
            Heap mode toggle proposal
        """
        resource_name = resource["name"]
        stock = resource["current_stock_kg"]
        weekly_consumption = resource["weekly_consumption_kg"]

        if enable:
            action = "Enable"
            explanation = (
                f"{resource_name} is abundant (stock: {stock}kg, "
                f"weekly consumption: {weekly_consumption}kg). "
                f"Toggle to Heap Mode: no logging required, people can "
                f"just take what they need. This reduces friction and "
                f"honors the gift economy principle."
            )
        else:
            action = "Disable"
            explanation = (
                f"{resource_name} stock is dropping (now {stock}kg). "
                f"Exit Heap Mode and resume normal tracking to prevent "
                f"unexpected shortages."
            )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.HEAP_MODE_TOGGLE,
            title=f"{action} Heap Mode: {resource_name}",
            explanation=explanation,
            inputs_used=[
                f"inventory:{resource['resource_id']}",
                f"consumption_history:{resource['resource_id']}",
            ],
            constraints=[
                "Automatic: Reverts to tracking if stock drops rapidly",
                "Monitoring: Still track total flow for planning",
            ],
            data={
                "resource_id": resource["resource_id"],
                "resource_name": resource_name,
                "enable_heap_mode": enable,
                "current_stock_kg": stock,
                "weekly_consumption_kg": weekly_consumption,
                "weeks_of_supply": stock / weekly_consumption if weekly_consumption > 0 else 999,
            },
            requires_approval=[
                "steward:inventory",  # Inventory steward approves mode changes
            ],
        )

    async def _create_rationing_proposal(
        self,
        resource: Dict[str, Any]
    ) -> Proposal:
        """
        Create a rationing mode proposal.

        Args:
            resource: Resource data

        Returns:
            Rationing mode proposal
        """
        resource_name = resource["name"]
        stock = resource["current_stock_kg"]
        weekly_consumption = resource["weekly_consumption_kg"]
        weeks_remaining = stock / weekly_consumption if weekly_consumption > 0 else 999

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.RATIONING_MODE,
            title=f"Enable rationing: {resource_name}",
            explanation=(
                f"{resource_name} is running low ({stock}kg remaining, "
                f"~{weeks_remaining:.1f} weeks at current consumption). "
                f"Propose rationing mode: prioritize 'Survival Need' requests "
                f"over 'Comfort Need' requests to ensure basic needs are met."
            ),
            inputs_used=[
                f"inventory:{resource['resource_id']}",
                f"consumption_history:{resource['resource_id']}",
            ],
            constraints=[
                "Priority: Survival needs (food, medicine, heating) first",
                "Fairness: Equal access to rationed amounts",
                "Temporary: Rationing ends when supply recovers",
            ],
            data={
                "resource_id": resource["resource_id"],
                "resource_name": resource_name,
                "current_stock_kg": stock,
                "weekly_consumption_kg": weekly_consumption,
                "weeks_remaining": weeks_remaining,
                "rationing_rules": {
                    "survival_needs": "auto_approve",
                    "comfort_needs": "reject",
                    "emergency_override": "steward_discretion",
                },
                "exit_condition": "stock > 4 weeks supply",
            },
            requires_approval=[
                "steward:inventory",
                "community:lazy_consensus",
            ],
        )
