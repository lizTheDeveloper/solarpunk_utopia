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

        GAP-66: Now records agent runs to database for stats tracking.

        Returns:
            List of generated proposals
        """
        if not self.enabled:
            logger.info(f"Agent {self.agent_name} is disabled, skipping run")
            return []

        logger.info(f"Running agent: {self.agent_name}")
        start_time = datetime.now(timezone.utc)
        self._last_run = start_time
        error_msg = None
        status = "completed"

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

            # Record successful run to database
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._record_run(
                proposals_created=len(proposals),
                duration_seconds=duration,
                status=status,
                errors=None
            )

            return proposals

        except Exception as e:
            logger.error(f"Error in agent {self.agent_name}: {e}", exc_info=True)
            error_msg = str(e)
            status = "failed"

            # Record failed run to database
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            await self._record_run(
                proposals_created=0,
                duration_seconds=duration,
                status=status,
                errors=error_msg
            )

            return []

    async def _record_run(
        self,
        proposals_created: int,
        duration_seconds: float,
        status: str,
        errors: Optional[str]
    ):
        """
        Record agent run to database for statistics tracking.

        Args:
            proposals_created: Number of proposals created
            duration_seconds: Run duration in seconds
            status: Run status (completed, failed, partial)
            errors: Error message if run failed
        """
        try:
            from app.database.agent_stats_repository import AgentStatsRepository
            stats_repo = AgentStatsRepository()
            await stats_repo.record_run(
                agent_name=self.agent_name,
                proposals_created=proposals_created,
                errors=errors,
                duration_seconds=duration_seconds,
                status=status
            )
        except Exception as e:
            # Don't fail the agent run if stats recording fails
            logger.warning(f"Failed to record agent run stats: {e}")

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
            query: Query type - "offers", "needs", "matches", "exchanges", "commitments", "listings"
            params: Query parameters (category, location_id, limit, etc.)

        Returns:
            List of matching records

        Raises:
            ValueError: If query type is not supported
            Exception: If database query fails
        """
        if not self.db_client:
            # Initialize VFClient if not provided
            from app.clients.vf_client import VFClient
            self.db_client = VFClient()
            logger.info(f"Initialized VFClient for {self.agent_name}")

        params = params or {}

        try:
            if query == "offers":
                return await self.db_client.get_active_offers(**params)
            elif query == "needs":
                return await self.db_client.get_active_needs(**params)
            elif query == "matches":
                return await self.db_client.get_matches(**params) if hasattr(self.db_client, 'get_matches') else []
            elif query == "exchanges":
                return await self.db_client.get_exchanges(**params) if hasattr(self.db_client, 'get_exchanges') else []
            elif query == "commitments":
                return await self.db_client.get_commitments(**params) if hasattr(self.db_client, 'get_commitments') else []
            elif query == "listings":
                # Get both offers and needs
                offers = await self.db_client.get_active_offers(**params)
                needs = await self.db_client.get_active_needs(**params)
                return offers + needs
            else:
                logger.error(f"Unknown query type: {query}")
                raise ValueError(f"Unsupported query type: {query}")
        except Exception as e:
            logger.error(f"ValueFlows query failed for {query}: {e}", exc_info=True)
            raise  # Don't mask errors - let caller handle them

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
