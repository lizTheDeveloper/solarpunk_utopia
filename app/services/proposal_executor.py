"""
Proposal Executor Service

Bridges the gap between approved proposals and ValueFlows actions.
When a proposal is approved, this service executes it by creating
the corresponding VF entities (Matches, Exchanges, Events, etc.)
"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.agents.framework import Proposal, ProposalType, ProposalStatus

logger = logging.getLogger(__name__)


class ProposalExecutor:
    """
    Executes approved proposals by creating VF entities.

    This is the critical bridge that turns agent suggestions into real actions.
    """

    def __init__(self, vf_api_base: str = "http://localhost:8001"):
        """
        Initialize executor.

        Args:
            vf_api_base: Base URL for ValueFlows API
        """
        self.vf_api_base = vf_api_base
        self.client = httpx.AsyncClient(timeout=30.0)

    async def execute_proposal(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute an approved proposal.

        Args:
            proposal: The approved proposal to execute

        Returns:
            Execution result with created entity IDs

        Raises:
            ValueError: If proposal not approved or invalid
            httpx.HTTPError: If VF API call fails
        """
        # Verify proposal is approved
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Proposal {proposal.proposal_id} is not approved (status: {proposal.status})")

        # Route to appropriate handler based on type
        handlers = {
            ProposalType.MATCH: self._execute_match_proposal,
            ProposalType.URGENT_EXCHANGE: self._execute_urgent_exchange,
            ProposalType.BATCH_COOKING: self._execute_batch_cooking,
            ProposalType.WORK_PARTY: self._execute_work_party,
            ProposalType.SEASONAL_PLAN: self._execute_seasonal_plan,
            ProposalType.PROCESS_SEQUENCE: self._execute_process_sequence,
            ProposalType.LEARNING_PATH: self._execute_learning_path,
            ProposalType.REPLENISHMENT: self._execute_replenishment,
            ProposalType.SHORTAGE_WARNING: self._execute_shortage_warning,
            ProposalType.CACHE_EVICTION: self._execute_cache_eviction,
            ProposalType.CACHE_PRIORITY: self._execute_cache_priority,
            ProposalType.FORWARDING_POLICY: self._execute_forwarding_policy,
        }

        handler = handlers.get(proposal.proposal_type)
        if not handler:
            raise ValueError(f"No handler for proposal type: {proposal.proposal_type}")

        logger.info(f"Executing {proposal.proposal_type.value} proposal: {proposal.title}")

        try:
            result = await handler(proposal)
            proposal.executed_at = datetime.now(timezone.utc)
            logger.info(f"Successfully executed proposal {proposal.proposal_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute proposal {proposal.proposal_id}: {e}", exc_info=True)
            raise

    async def _execute_match_proposal(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute a MATCH proposal by creating VF Match and Exchange.

        Flow:
        1. Create Match entity linking offer and need
        2. Fetch listing details to get provider/receiver/resource data
        3. Create Exchange entity for the actual transfer
        4. Rollback Match if Exchange creation fails
        """
        data = proposal.data
        offer_id = data.get("offer_id")
        need_id = data.get("need_id")
        matched_quantity = data.get("quantity") or data.get("matched_quantity")
        unit = data.get("unit")

        if not all([offer_id, need_id, matched_quantity, unit]):
            raise ValueError(f"Missing required match data: {data}")

        # Step 1: Create Match
        match_response = await self.client.post(
            f"{self.vf_api_base}/vf/matches",
            json={
                "offer_id": offer_id,
                "need_id": need_id,
                "matched_quantity": matched_quantity,
                "unit": unit,
                "status": "proposed",
                "notes": f"Matched by {proposal.agent_name}: {proposal.explanation}",
            }
        )
        match_response.raise_for_status()
        match_data = match_response.json()
        match_id = match_data["id"]

        logger.info(f"Created Match {match_id} for offer {offer_id} → need {need_id}")

        try:
            # Step 2: Fetch listing details to get provider_id, receiver_id, resource_spec_id
            offer_response = await self.client.get(f"{self.vf_api_base}/vf/listings/{offer_id}")
            offer_response.raise_for_status()
            offer = offer_response.json()

            need_response = await self.client.get(f"{self.vf_api_base}/vf/listings/{need_id}")
            need_response.raise_for_status()
            need = need_response.json()

            # Extract required fields
            provider_id = offer.get("agent_id")
            receiver_id = need.get("agent_id")
            resource_spec_id = offer.get("resource_spec_id")

            if not all([provider_id, receiver_id, resource_spec_id]):
                raise ValueError(
                    f"Missing required listing data: provider_id={provider_id}, "
                    f"receiver_id={receiver_id}, resource_spec_id={resource_spec_id}"
                )

            # Step 3: Create Exchange
            exchange_response = await self.client.post(
                f"{self.vf_api_base}/vf/exchanges",
                json={
                    "match_id": match_id,
                    "provider_id": provider_id,
                    "receiver_id": receiver_id,
                    "resource_spec_id": resource_spec_id,
                    "quantity": matched_quantity,
                    "unit": unit,
                    "status": "planned",
                    "notes": f"Exchange from approved match: {proposal.explanation}",
                    "scheduled_start": data.get("suggested_time"),
                    "location_id": data.get("suggested_location"),
                }
            )
            exchange_response.raise_for_status()
            exchange_data = exchange_response.json()

            logger.info(f"Created Exchange {exchange_data.get('exchange', {}).get('id')} for Match {match_id}")

            return {
                "match_id": match_id,
                "exchange_id": exchange_data.get("exchange", {}).get("id"),
                "offer_id": offer_id,
                "need_id": need_id,
                "quantity": matched_quantity,
                "unit": unit,
            }

        except Exception as e:
            # Step 4: Rollback - delete the Match if Exchange creation failed
            logger.error(f"Failed to create Exchange for Match {match_id}, rolling back: {e}")
            try:
                delete_response = await self.client.delete(f"{self.vf_api_base}/vf/matches/{match_id}")
                delete_response.raise_for_status()
                logger.info(f"Rolled back Match {match_id}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback Match {match_id}: {rollback_error}")

            # Re-raise the original error
            raise ValueError(f"Failed to execute match proposal: {e}") from e

    async def _execute_urgent_exchange(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute URGENT_EXCHANGE by creating immediate Exchange and Events.

        For perishables that need to move NOW.
        """
        data = proposal.data
        provider_id = data.get("provider_id")
        receiver_id = data.get("receiver_id")
        resource_spec_id = data.get("resource_spec_id")
        quantity = data.get("quantity")
        unit = data.get("unit")

        # Create Exchange
        exchange_response = await self.client.post(
            f"{self.vf_api_base}/vf/exchanges",
            json={
                "provider_id": provider_id,
                "receiver_id": receiver_id,
                "resource_spec_id": resource_spec_id,
                "quantity": quantity,
                "unit": unit,
                "status": "proposed",
                "notes": f"Urgent exchange: {proposal.explanation}",
            }
        )
        exchange_response.raise_for_status()
        exchange_data = exchange_response.json()

        logger.info(f"Created urgent Exchange {exchange_data['id']}")

        return {
            "exchange_id": exchange_data["id"],
            "provider_id": provider_id,
            "receiver_id": receiver_id,
        }

    async def _execute_batch_cooking(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute BATCH_COOKING by creating coordination event.

        Creates work party event for batch cooking session.
        """
        data = proposal.data
        recipe = data.get("recipe")
        servings = data.get("servings")
        ingredients = data.get("ingredients", [])

        # Create Event for batch cooking
        event_response = await self.client.post(
            f"{self.vf_api_base}/vf/events",
            json={
                "name": f"Batch Cooking: {recipe}",
                "description": proposal.explanation,
                "event_type": "batch_cooking",
                "agent_id": data.get("organizer_id", "commune"),
                "metadata": {
                    "recipe": recipe,
                    "servings": servings,
                    "ingredients": ingredients,
                    "proposal_id": proposal.proposal_id,
                },
            }
        )
        event_response.raise_for_status()
        event_data = event_response.json()

        logger.info(f"Created batch cooking event {event_data['id']}")

        return {
            "event_id": event_data["id"],
            "recipe": recipe,
            "servings": servings,
        }

    async def _execute_work_party(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute WORK_PARTY by creating coordination event.
        """
        data = proposal.data
        task_name = data.get("task_name")
        required_people = data.get("required_people")
        duration_hours = data.get("duration_hours")

        # Create Event for work party
        event_response = await self.client.post(
            f"{self.vf_api_base}/vf/events",
            json={
                "name": f"Work Party: {task_name}",
                "description": proposal.explanation,
                "event_type": "work_party",
                "agent_id": data.get("organizer_id", "commune"),
                "metadata": {
                    "task": task_name,
                    "required_people": required_people,
                    "duration_hours": duration_hours,
                    "proposal_id": proposal.proposal_id,
                },
            }
        )
        event_response.raise_for_status()
        event_data = event_response.json()

        logger.info(f"Created work party event {event_data['id']}")

        return {
            "event_id": event_data["id"],
            "task": task_name,
        }

    async def _execute_seasonal_plan(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute SEASONAL_PLAN by creating planning event.
        """
        data = proposal.data

        # For now, just log the plan (could create Planning entity in future)
        logger.info(f"Seasonal plan approved: {proposal.title}")

        return {
            "plan_id": proposal.proposal_id,
            "season": data.get("season"),
            "tasks": data.get("tasks", []),
        }

    async def _execute_process_sequence(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute PROCESS_SEQUENCE by creating workflow.
        """
        data = proposal.data

        logger.info(f"Process sequence approved: {proposal.title}")

        return {
            "process_id": proposal.proposal_id,
            "steps": data.get("steps", []),
        }

    async def _execute_learning_path(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute LEARNING_PATH by creating educational event.
        """
        data = proposal.data
        skill = data.get("skill")
        lessons = data.get("lessons", [])

        # Create Event for learning session
        event_response = await self.client.post(
            f"{self.vf_api_base}/vf/events",
            json={
                "name": f"Learning Path: {skill}",
                "description": proposal.explanation,
                "event_type": "learning",
                "agent_id": data.get("learner_id", "commune"),
                "metadata": {
                    "skill": skill,
                    "lessons": lessons,
                    "proposal_id": proposal.proposal_id,
                },
            }
        )
        event_response.raise_for_status()
        event_data = event_response.json()

        logger.info(f"Created learning path event {event_data['id']}")

        return {
            "event_id": event_data["id"],
            "skill": skill,
            "lessons": lessons,
        }

    async def _execute_replenishment(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute REPLENISHMENT by creating need listing.
        """
        data = proposal.data
        resource_spec_id = data.get("resource_spec_id")
        quantity = data.get("quantity")
        unit = data.get("unit")

        # Create Need listing
        listing_response = await self.client.post(
            f"{self.vf_api_base}/vf/listings",
            json={
                "resource_spec_id": resource_spec_id,
                "listing_type": "need",
                "quantity": quantity,
                "unit": unit,
                "status": "active",
                "notes": f"Replenishment needed: {proposal.explanation}",
            }
        )
        listing_response.raise_for_status()
        listing_data = listing_response.json()

        logger.info(f"Created replenishment need {listing_data['id']}")

        return {
            "listing_id": listing_data["id"],
            "resource_spec_id": resource_spec_id,
            "quantity": quantity,
        }

    async def _execute_shortage_warning(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute SHORTAGE_WARNING by logging alert.
        """
        data = proposal.data

        logger.warning(f"Shortage warning: {proposal.title} - {proposal.explanation}")

        return {
            "warning_id": proposal.proposal_id,
            "resource": data.get("resource"),
            "current_stock": data.get("current_stock"),
        }

    async def _execute_cache_eviction(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute CACHE_EVICTION by triggering cache cleanup.
        """
        data = proposal.data

        # TODO: Integrate with CacheService
        logger.info(f"Cache eviction approved: {data.get('target_free_mb')}MB")

        return {
            "eviction_id": proposal.proposal_id,
            "target_free_mb": data.get("target_free_mb"),
        }

    async def _execute_cache_priority(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute CACHE_PRIORITY by updating cache priorities.
        """
        data = proposal.data

        # TODO: Integrate with CacheService
        logger.info(f"Cache priority update approved for role: {data.get('role')}")

        return {
            "priority_id": proposal.proposal_id,
            "role": data.get("role"),
            "adjustments": data.get("adjustments"),
        }

    async def _execute_forwarding_policy(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Execute FORWARDING_POLICY by updating forwarding rules.
        """
        data = proposal.data

        # TODO: Integrate with ForwardingService
        logger.info(f"Forwarding policy approved: {proposal.title}")

        return {
            "policy_id": proposal.proposal_id,
            "policy": data.get("policy"),
        }

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
_executor: Optional[ProposalExecutor] = None


def get_executor() -> ProposalExecutor:
    """Get global executor instance"""
    global _executor
    if _executor is None:
        _executor = ProposalExecutor()
    return _executor
