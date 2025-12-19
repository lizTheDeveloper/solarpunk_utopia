"""
Base agent class with common functionality for all commune OS agents.

All agents inherit from this base class and implement specific reasoning logic.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .proposal import Proposal, ProposalType, ProposalStatus


logger = logging.getLogger(__name__)


class AgentConfig(dict):
    """
    Configuration for an agent.

    Allows agents to be enabled/disabled and behavior to be customized.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault("enabled", True)
        self.setdefault("check_interval_seconds", 300)  # 5 minutes default
        self.setdefault("proposal_ttl_hours", 72)  # 3 days default
        self.setdefault("auto_approve", False)  # Require human approval by default


class BaseAgent(ABC):
    """
    Base class for all commune OS agents.

    Agents analyze data, generate proposals, and publish them as DTN bundles.
    They do NOT make unilateral allocations.
    """

    def __init__(
        self,
        agent_name: str,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        Initialize agent.

        Args:
            agent_name: Unique name for this agent
            config: Agent configuration (enabled, intervals, etc.)
            db_client: Database client for querying VF data
            bundle_publisher: Client for publishing proposals as bundles
            llm_client: Optional LLM client for complex reasoning
        """
        self.agent_name = agent_name
        self.config = config or AgentConfig()
        self.db_client = db_client
        self.bundle_publisher = bundle_publisher
        self.llm_client = llm_client

        self._last_run: Optional[datetime] = None
        self._proposals_created: int = 0

    @property
    def enabled(self) -> bool:
        """Check if agent is enabled"""
        return self.config.get("enabled", True)

    @abstractmethod
    async def analyze(self) -> List[Proposal]:
        """
        Analyze current state and generate proposals.

        Returns:
            List of proposals to be reviewed and published
        """
        pass

    async def run(self) -> List[Proposal]:
        """
        Execute agent analysis and generate proposals.

        Returns:
            List of generated proposals
        """
        if not self.enabled:
            logger.info(f"Agent {self.agent_name} is disabled, skipping run")
            return []

        logger.info(f"Running agent: {self.agent_name}")
        self._last_run = datetime.now(timezone.utc)

        try:
            proposals = await self.analyze()

            # Set TTL and publish
            for proposal in proposals:
                if not proposal.expires_at:
                    ttl_hours = self.config.get("proposal_ttl_hours", 72)
                    proposal.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

                # Auto-approve if configured (opt-in for trusted automation)
                if self.config.get("auto_approve", False):
                    for user_id in proposal.requires_approval:
                        proposal.add_approval(user_id, True, "Auto-approved by agent config")

                # Publish as bundle
                if self.bundle_publisher:
                    await self.publish_proposal(proposal)

            self._proposals_created += len(proposals)
            logger.info(f"Agent {self.agent_name} created {len(proposals)} proposals")

            return proposals

        except Exception as e:
            logger.error(f"Error in agent {self.agent_name}: {e}", exc_info=True)
            return []

    async def publish_proposal(self, proposal: Proposal):
        """
        Publish proposal as DTN bundle.

        Args:
            proposal: Proposal to publish
        """
        if not self.bundle_publisher:
            logger.warning(f"No bundle publisher configured for {self.agent_name}")
            return

        try:
            # Create bundle payload
            bundle_payload = proposal.to_bundle_payload()

            # Determine bundle metadata from proposal type
            topic = self._get_topic_for_proposal(proposal.proposal_type)
            priority = self._get_priority_for_proposal(proposal.proposal_type)

            # Publish
            bundle_id = await self.bundle_publisher.publish(
                payload=bundle_payload,
                topic=topic,
                priority=priority,
                tags=["agent-proposal", proposal.proposal_type.value],
            )

            proposal.bundle_id = bundle_id
            logger.info(f"Published proposal {proposal.proposal_id} as bundle {bundle_id}")

        except Exception as e:
            logger.error(f"Failed to publish proposal: {e}", exc_info=True)

    def _get_topic_for_proposal(self, proposal_type: ProposalType) -> str:
        """Map proposal type to bundle topic"""
        mapping = {
            ProposalType.MATCH: "mutual-aid",
            ProposalType.URGENT_EXCHANGE: "mutual-aid",
            ProposalType.BATCH_COOKING: "coordination",
            ProposalType.WORK_PARTY: "coordination",
            ProposalType.SEASONAL_PLAN: "coordination",
            ProposalType.PROCESS_SEQUENCE: "coordination",
            ProposalType.LEARNING_PATH: "education",
            ProposalType.REPLENISHMENT: "inventory",
            ProposalType.SHORTAGE_WARNING: "inventory",
            ProposalType.CACHE_EVICTION: "coordination",
            ProposalType.CACHE_PRIORITY: "coordination",
            ProposalType.FORWARDING_POLICY: "coordination",
        }
        return mapping.get(proposal_type, "coordination")

    def _get_priority_for_proposal(self, proposal_type: ProposalType) -> str:
        """Map proposal type to bundle priority"""
        if proposal_type in [ProposalType.URGENT_EXCHANGE, ProposalType.BATCH_COOKING]:
            return "perishable"
        return "normal"

    async def query_vf_data(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Query ValueFlows data from database.

        Args:
            query: SQL query or ORM method
            params: Query parameters

        Returns:
            List of matching records
        """
        if not self.db_client:
            logger.warning(f"No database client configured for {self.agent_name}")
            return []

        try:
            # TODO: Implement actual DB query once DB client is available
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            return []

    async def use_llm(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Use LLM for complex reasoning.

        Args:
            prompt: Prompt for LLM
            context: Additional context data

        Returns:
            LLM response text
        """
        if not self.llm_client:
            logger.warning(f"No LLM client configured for {self.agent_name}")
            return ""

        try:
            # Build system prompt with context
            system_prompt = f"You are {self.agent_name}, an AI agent for a solarpunk commune."
            if context:
                system_prompt += f"\n\nContext: {context}"

            # Call LLM
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=512,
            )

            return response.content

        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_name": self.agent_name,
            "enabled": self.enabled,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "proposals_created": self._proposals_created,
            "config": dict(self.config),
        }
