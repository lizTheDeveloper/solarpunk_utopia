"""
Commons Router Agent

Decides what to cache and forward based on node role and budgets.
Optimizes cache for node's specific role (citizen, bridge, AP, library).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class CommonsRouterAgent(BaseAgent):
    """
    Optimizes cache and forwarding decisions based on node role.

    Proposes:
    - Cache evictions when budget exceeded
    - Priority adjustments for cached bundles
    - Forwarding policies for bridge nodes
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        node_role: str = "citizen",
        cache_budget_mb: int = 1024,
    ):
        super().__init__(
            agent_name="commons-router",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
        )
        self.node_role = node_role
        self.cache_budget_mb = cache_budget_mb

    async def analyze(self) -> List[Proposal]:
        """
        Analyze cache usage and generate optimization proposals.

        Returns:
            List of cache management proposals
        """
        proposals = []

        # Get current cache state
        cache_state = await self._get_cache_state()

        # Check if budget exceeded
        if cache_state["used_mb"] > self.cache_budget_mb:
            eviction_proposal = await self._propose_cache_eviction(cache_state)
            if eviction_proposal:
                proposals.append(eviction_proposal)

        # Propose priority adjustments for role optimization
        priority_proposal = await self._propose_priority_adjustments(cache_state)
        if priority_proposal:
            proposals.append(priority_proposal)

        # For bridge nodes, propose forwarding optimizations
        if self.node_role == "bridge":
            forwarding_proposal = await self._propose_forwarding_policy(cache_state)
            if forwarding_proposal:
                proposals.append(forwarding_proposal)

        return proposals

    async def _get_cache_state(self) -> Dict[str, Any]:
        """
        Get current cache state from database.

        Returns:
            Cache state including usage, bundle counts, etc.
        """
        # TODO: Query actual cache state from database
        # For now, return mock data
        return {
            "used_mb": 800,
            "bundle_count": 150,
            "bundles_by_priority": {
                "emergency": 5,
                "perishable": 20,
                "normal": 100,
                "low": 25,
            },
            "bundles_by_topic": {
                "mutual-aid": 40,
                "knowledge": 60,
                "coordination": 30,
                "inventory": 20,
            },
            "oldest_bundle_age_days": 45,
        }

    async def _propose_cache_eviction(
        self,
        cache_state: Dict[str, Any]
    ) -> Optional[Proposal]:
        """
        Propose cache evictions when budget exceeded.

        Strategy:
        - KEEP: Emergency bundles (always)
        - KEEP: Perishables with <48h TTL (high priority)
        - KEEP: Popular knowledge indexes (high access frequency)
        - EVICT: Old low-priority bundles
        - EVICT: Bundles past TTL
        """
        used_mb = cache_state["used_mb"]
        overage_mb = used_mb - self.cache_budget_mb

        if overage_mb <= 0:
            return None

        # Build eviction strategy based on node role
        keep_criteria = self._get_keep_criteria_for_role()
        evict_criteria = [
            "Bundles past TTL expiration",
            "Low-priority bundles older than 30 days",
            "Duplicate knowledge bundles (keep latest version)",
        ]

        # Estimate space to free (conservative: overage + 10% buffer)
        target_free_mb = int(overage_mb * 1.1)

        explanation = (
            f"Cache exceeds {self.cache_budget_mb}MB budget by {overage_mb}MB. "
            f"Prioritizing {', '.join(keep_criteria[:2])} to support {self.node_role} role. "
            f"Evicting old low-priority bundles to free ~{target_free_mb}MB."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.CACHE_EVICTION,
            title=f"Evict {target_free_mb}MB from cache",
            explanation=explanation,
            inputs_used=[
                "cache_metrics",
                f"node_role:{self.node_role}",
                f"budget:{self.cache_budget_mb}MB",
            ],
            constraints=[
                "Never evict emergency bundles",
                "Never evict perishables <48h from expiry",
                "Preserve knowledge indexes with recent access",
            ],
            data={
                "target_free_mb": target_free_mb,
                "overage_mb": overage_mb,
                "keep_criteria": keep_criteria,
                "evict_criteria": evict_criteria,
                "cache_state": cache_state,
            },
            requires_approval=["system-admin"],  # Auto-approve in production config
        )

    async def _propose_priority_adjustments(
        self,
        cache_state: Dict[str, Any]
    ) -> Optional[Proposal]:
        """
        Propose priority adjustments to optimize for node role.
        """
        adjustments = []

        # Role-specific priority logic
        if self.node_role == "bridge":
            adjustments.extend([
                "Boost perishables for rapid forwarding",
                "Boost coordination bundles for work party scheduling",
                "Maintain knowledge indexes for query responses",
            ])
        elif self.node_role == "library":
            adjustments.extend([
                "Boost knowledge bundles for serving",
                "Boost education content for learning paths",
                "Cache large files for chunked retrieval",
            ])
        elif self.node_role == "ap":
            adjustments.extend([
                "Boost indexes for portal queries",
                "Boost mutual-aid for local discovery",
                "Cache frequently accessed content",
            ])
        else:  # citizen
            adjustments.extend([
                "Prioritize own subscribed topics",
                "Cache only time-sensitive bundles",
                "Minimize storage footprint",
            ])

        if not adjustments:
            return None

        explanation = (
            f"Optimizing cache priorities for {self.node_role} node role. "
            f"Adjusting {len(adjustments)} categories to better serve community needs."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.CACHE_PRIORITY,
            title=f"Optimize cache for {self.node_role} role",
            explanation=explanation,
            inputs_used=[
                "cache_metrics",
                f"node_role:{self.node_role}",
            ],
            constraints=[
                "Emergency bundles always highest priority",
                "Respect user-defined topic preferences",
            ],
            data={
                "role": self.node_role,
                "adjustments": adjustments,
                "cache_state": cache_state,
            },
            requires_approval=["system-admin"],
        )

    async def _propose_forwarding_policy(
        self,
        cache_state: Dict[str, Any]
    ) -> Optional[Proposal]:
        """
        Propose forwarding optimizations for bridge nodes.

        Bridge nodes should aggressively forward:
        - Perishables (time-sensitive)
        - Emergency bundles
        - Coordination bundles
        - Index updates

        And be selective about:
        - Large knowledge bundles (forward on request)
        - Low-priority bundles (forward opportunistically)
        """
        if self.node_role != "bridge":
            return None

        policy = {
            "aggressive_forward": [
                "emergency",
                "perishable",
                "coordination",
                "indexes",
            ],
            "on_request": [
                "large_knowledge",
            ],
            "opportunistic": [
                "low_priority",
                "historical_data",
            ],
            "bandwidth_budget_mbps": 5.0,  # Conservative mobile bandwidth
        }

        explanation = (
            "Bridge node forwarding policy optimized for mobile bandwidth. "
            "Prioritizing time-sensitive bundles (emergency, perishables, coordination). "
            "Large knowledge bundles forwarded on request only to conserve bandwidth."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.FORWARDING_POLICY,
            title="Optimize bridge forwarding policy",
            explanation=explanation,
            inputs_used=[
                "cache_metrics",
                "node_role:bridge",
                "bandwidth_constraints",
            ],
            constraints=[
                "Emergency bundles always forwarded",
                "Respect recipient's cache budget",
                "Honor privacy/audience settings",
            ],
            data={
                "policy": policy,
                "cache_state": cache_state,
            },
            requires_approval=["system-admin"],
        )

    def _get_keep_criteria_for_role(self) -> List[str]:
        """Get cache keep criteria based on node role"""
        base_criteria = [
            "Emergency bundles (always)",
            "Perishables <48h from expiry",
        ]

        role_criteria = {
            "bridge": [
                "Popular knowledge indexes",
                "Coordination bundles",
            ],
            "library": [
                "All knowledge bundles",
                "Education content",
            ],
            "ap": [
                "All indexes",
                "Frequently accessed content",
            ],
            "citizen": [
                "User's subscribed topics",
            ],
        }

        return base_criteria + role_criteria.get(self.node_role, [])
