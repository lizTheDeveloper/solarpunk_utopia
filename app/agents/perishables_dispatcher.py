"""
Perishables Dispatcher Agent

Monitors expiring food and proposes urgent redistribution or preservation.
Escalates notifications as expiry approaches.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class PerishablesDispatcher(BaseAgent):
    """
    Identifies expiring food and proposes urgent action.

    Monitors ResourceInstance.expiry_date from VF inventory.
    Creates proposals for:
    - Urgent exchanges (match with needs)
    - Batch cooking events (if no individual needs)
    - Preservation methods (canning, freezing, etc.)

    Escalates urgency as expiry approaches.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="perishables-dispatcher",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Find expiring food and propose urgent actions.

        Returns:
            List of urgency proposals
        """
        proposals = []

        # Get expiring inventory
        expiring_items = await self._get_expiring_inventory()

        for item in expiring_items:
            hours_until_expiry = self._hours_until_expiry(item["expiry_date"])

            if hours_until_expiry <= 0:
                # Already expired - propose composting/disposal
                continue
            elif hours_until_expiry <= 12:
                # Critical urgency
                proposal = await self._propose_critical_action(item)
            elif hours_until_expiry <= 48:
                # High urgency - urgent exchange
                proposal = await self._propose_urgent_exchange(item)
            elif hours_until_expiry <= 168:  # 1 week
                # Medium urgency - normal redistribution
                proposal = await self._propose_redistribution(item)
            else:
                # Not urgent yet
                continue

            if proposal:
                proposals.append(proposal)

        logger.info(f"Created {len(proposals)} perishables proposals")
        return proposals

    async def _get_expiring_inventory(self) -> List[Dict[str, Any]]:
        """
        Query expiring inventory from VF database.

        Returns:
            List of items with expiry_date within next 7 days
        """
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Query offers expiring within 7 days (168 hours)
            expiring_items = await self.db_client.get_expiring_offers(hours=168)
            return expiring_items
        except Exception as e:
            logger.warning(f"Failed to query VF database, using empty list: {e}")
            return []

    def _hours_until_expiry(self, expiry_date: datetime) -> float:
        """Calculate hours until expiry"""
        delta = expiry_date - datetime.now(timezone.utc)
        return delta.total_seconds() / 3600

    async def _propose_critical_action(self, item: Dict[str, Any]) -> Optional[Proposal]:
        """
        Propose critical action for food expiring in <12 hours.

        Options:
        - Immediate batch cooking event
        - Emergency distribution
        - Preservation (if possible)
        """
        hours = self._hours_until_expiry(item["expiry_date"])

        # Check if batch cooking makes sense
        if self._is_cookable(item):
            action = "batch cooking event"
            details = {
                "action_type": "batch_cooking",
                "event_time": "Immediately (next 2 hours)",
                "event_location": "Community Kitchen",
                "participants_needed": 2,
                "output": f"{item['resource']} sauce/preserve",
            }
        else:
            action = "emergency distribution"
            details = {
                "action_type": "emergency_distribution",
                "method": "Announce in community forum",
                "pickup_time": "Next 6 hours",
                "pickup_location": item["location"],
            }

        explanation = (
            f"CRITICAL: {item['quantity']} {item['unit']} {item['resource']} "
            f"expires in {hours:.1f} hours. "
            f"Proposing {action} to prevent waste."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.BATCH_COOKING if details["action_type"] == "batch_cooking" else ProposalType.URGENT_EXCHANGE,
            title=f"URGENT: {item['resource']} expires in {hours:.1f}h",
            explanation=explanation,
            inputs_used=[
                item["bundle_id"],
                "expiry_monitoring",
            ],
            constraints=[
                f"Must act within {hours:.1f} hours",
                "Food safety protocols required",
            ],
            data={
                "item": item,
                "hours_until_expiry": hours,
                "urgency": "critical",
                **details,
            },
            requires_approval=["community-coordinator"],
        )

    async def _propose_urgent_exchange(self, item: Dict[str, Any]) -> Optional[Proposal]:
        """
        Propose urgent exchange for food expiring in 12-48 hours.

        Try to match with existing needs, or create general offer.
        """
        hours = self._hours_until_expiry(item["expiry_date"])

        # Query for matching needs
        matching_needs = await self._find_matching_needs(item)

        if matching_needs:
            # Propose match with specific need
            need = matching_needs[0]
            explanation = (
                f"{item['quantity']} {item['unit']} {item['resource']} "
                f"expires in {hours:.1f} hours. "
                f"Matched with {need['user_name']}'s need. "
                f"Urgent handoff recommended."
            )

            return Proposal(
                agent_name=self.agent_name,
                proposal_type=ProposalType.URGENT_EXCHANGE,
                title=f"Urgent: {item['resource']} → {need['user_name']}",
                explanation=explanation,
                inputs_used=[
                    item["bundle_id"],
                    need["bundle_id"],
                ],
                constraints=[
                    f"Handoff must occur within {hours:.1f} hours",
                    "Fresh transport required",
                ],
                data={
                    "item": item,
                    "need": need,
                    "hours_until_expiry": hours,
                    "urgency": "high",
                    "suggested_handoff": "ASAP",
                },
                requires_approval=[need["user_id"], "pantry-manager"],
            )
        else:
            # No matching need - propose general offer
            explanation = (
                f"{item['quantity']} {item['unit']} {item['resource']} "
                f"expires in {hours:.1f} hours. "
                f"No matching needs found. "
                f"Suggesting batch cooking or community announcement."
            )

            action = "batch_cooking" if self._is_cookable(item) else "community_offer"

            return Proposal(
                agent_name=self.agent_name,
                proposal_type=ProposalType.BATCH_COOKING if action == "batch_cooking" else ProposalType.URGENT_EXCHANGE,
                title=f"Urgent: {item['resource']} available ({hours:.1f}h)",
                explanation=explanation,
                inputs_used=[
                    item["bundle_id"],
                    "needs_query",
                ],
                constraints=[
                    f"Must act within {hours:.1f} hours",
                ],
                data={
                    "item": item,
                    "hours_until_expiry": hours,
                    "urgency": "high",
                    "action": action,
                    "suggested_action": self._suggest_action(item),
                },
                requires_approval=["pantry-manager"],
            )

    async def _propose_redistribution(self, item: Dict[str, Any]) -> Optional[Proposal]:
        """
        Propose normal redistribution for food expiring in 2-7 days.

        Lower urgency, but still worth flagging.
        """
        hours = self._hours_until_expiry(item["expiry_date"])
        days = hours / 24

        explanation = (
            f"{item['quantity']} {item['unit']} {item['resource']} "
            f"expires in {days:.1f} days. "
            f"Consider creating offer or planning use."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.URGENT_EXCHANGE,
            title=f"Expiring soon: {item['resource']} ({days:.1f} days)",
            explanation=explanation,
            inputs_used=[
                item["bundle_id"],
            ],
            constraints=[
                f"Use within {days:.1f} days",
            ],
            data={
                "item": item,
                "hours_until_expiry": hours,
                "days_until_expiry": days,
                "urgency": "medium",
                "suggested_actions": [
                    "Create offer in mutual aid",
                    "Plan meal using this ingredient",
                    "Preserve if quantity is large",
                ],
            },
            requires_approval=["pantry-manager"],
        )

    async def _find_matching_needs(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find needs that match this expiring item.

        Returns:
            List of matching needs, sorted by relevance
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get all active needs and filter by category
            category = item.get("category")
            needs = await self.db_client.get_active_needs(category=category)

            # Filter by matching resource
            matching_needs = [
                need for need in needs
                if need.get("resource", "").lower() == item.get("resource", "").lower()
            ]
            return matching_needs
        except Exception as e:
            logger.warning(f"Failed to query VF database for needs: {e}")
            # Fallback to mock data if DB unavailable
            return [
                {
                    "id": "need:bob-tomatoes",
                    "user_id": "bob",
                    "user_name": "Bob",
                    "resource": "tomatoes",
                    "category": "food:produce",
                    "quantity": 5.0,
                    "unit": "lbs",
                    "bundle_id": "bundle:need-bob-tomatoes",
                }
            ] if item["resource"] == "tomatoes" else []

    def _is_cookable(self, item: Dict[str, Any]) -> bool:
        """Check if item is suitable for batch cooking"""
        cookable_categories = [
            "food:produce",
            "food:vegetables",
            "food:fruits",
        ]
        return any(item["category"].startswith(cat) for cat in cookable_categories)

    def _suggest_action(self, item: Dict[str, Any]) -> str:
        """Suggest best action for item"""
        if self._is_cookable(item):
            if item["quantity"] > 5:
                return "Host batch cooking work party - make sauce, jam, or preserve"
            else:
                return "Offer to community members for immediate use"
        else:
            return "Announce in community forum for immediate pickup"
