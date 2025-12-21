"""
Counter-Power Agent

Automated immune system against centralized authority.

Key Features:
- Authority Audit: Detects power accumulation in hands of few
- Guild Filter: Distinguishes productive guilds from resource hoarders
- Leveling Protocols: Proposes remedies when hierarchy detected
- Safe Eject: Makes leaving/forking easy (voluntary association)

Based on proposal: openspec/changes/counter-power-agent/proposal.md
Inspired by Bakunin's anti-statism
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"


class CounterPowerAgent(BaseAgent):
    """
    Continuously audits the network for power asymmetry.

    This agent:
    1. Detects centralization (few people controlling decisions or resources)
    2. Distinguishes productive concentration from hoarding
    3. Alerts community to power accumulation
    4. Facilitates voluntary secession when needed
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="counter-power",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze power distribution and generate warnings/alerts.

        Returns:
            List of centralization warnings, warlord alerts, and pruning prompts
        """
        proposals = []

        # Check for governance centralization
        governance_centralization = await self._detect_governance_centralization()
        if governance_centralization:
            proposal = await self._create_centralization_warning(
                governance_centralization
            )
            proposals.append(proposal)

        # Check for resource hoarding (warlords)
        warlords = await self._detect_warlords()
        for warlord in warlords:
            proposal = await self._create_warlord_alert(warlord)
            proposals.append(proposal)

        # Check for passive/silent members who might want to leave
        silent_members = await self._detect_silent_members()
        for member in silent_members:
            proposal = await self._create_pruning_prompt(member)
            proposals.append(proposal)

        # Check for saboteurs (active blocking)
        saboteurs = await self._detect_saboteurs()
        for saboteur in saboteurs:
            proposal = await self._create_centralization_warning({
                "type": "saboteur",
                "user_id": saboteur["user_id"],
                "blocking_rate": saboteur["blocking_rate"],
            })
            proposals.append(proposal)

        return proposals

    async def _detect_governance_centralization(self) -> Optional[Dict[str, Any]]:
        """
        Detect if few people are making most decisions.

        Returns:
            Centralization data if detected, None otherwise
        """
        # TODO: Query proposal authorship and approval patterns
        # For now, return mock data

        return {
            "type": "governance",
            "user_id": "user:admindave",
            "role": "node_approver",
            "percentage_of_approvals": 80.0,
            "total_approvals": 120,
            "period_days": 30,
        }

    async def _detect_warlords(self) -> List[Dict[str, Any]]:
        """
        Detect resource hoarders (high stock, low outflow).

        A "warlord" is defined as: high inventory but low circulation rate.
        This distinguishes hoarding from productive guilds (high stock + high flow).

        Returns:
            List of warlord data
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_warlords()

        try:
            # Query active offers
            offers = await self.db_client.get_active_offers()

            # Group offers by agent_id and resource_spec_id
            agent_resources = {}
            for offer in offers:
                agent_id = offer.get('agent_id')
                resource_spec_id = offer.get('resource_spec_id')
                quantity = offer.get('quantity', 0)

                key = f"{agent_id}:{resource_spec_id}"
                if key not in agent_resources:
                    agent_resources[key] = {
                        "user_id": agent_id,
                        "resource_spec_id": resource_spec_id,
                        "resource_type": offer.get('name', 'unknown'),
                        "total_stock": 0,
                        "offer_count": 0,
                    }

                agent_resources[key]["total_stock"] += quantity
                agent_resources[key]["offer_count"] += 1

            # Detect warlord pattern: high stock, low offer_count suggests hoarding
            # (Not circulating despite having resources)
            warlords = []
            for data in agent_resources.values():
                stock = data["total_stock"]
                offer_count = data["offer_count"]

                # Warlord heuristic: stock > 100 units but only 1-2 offers
                # (Suggests holding rather than sharing)
                if stock > 100 and offer_count <= 2:
                    # Estimate outflow: if only posting occasionally, outflow is low
                    avg_weekly_outflow = stock * 0.02  # Assume 2% weekly circulation

                    warlords.append({
                        "user_id": data["user_id"],
                        "resource_type": data["resource_type"],
                        "stock_units": stock,
                        "avg_weekly_outflow": avg_weekly_outflow,
                        "inflow_rate": 0,  # Can't calculate without exchange history
                        "guild_classification": "warlord",
                    })

            logger.info(f"Detected {len(warlords)} potential resource warlords")
            return warlords

        except Exception as e:
            logger.error(f"Error detecting warlords: {e}", exc_info=True)
            return self._get_mock_warlords()

    def _get_mock_warlords(self) -> List[Dict[str, Any]]:
        """Fallback mock data"""
        logger.warning("Using mock warlord data")
        return [
            {
                "user_id": "user:resource_guy",
                "resource_type": "batteries",
                "stock_units": 500,
                "avg_weekly_outflow": 5,
                "inflow_rate": 50,
                "guild_classification": "warlord",
            },
        ]

    async def _detect_silent_members(self) -> List[Dict[str, Any]]:
        """
        Detect members with low activity who might want to leave.

        Looks for agents with old listings but no recent activity.

        Returns:
            List of silent member data
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_silent_members()

        try:
            # Query all listings (offers + needs)
            all_listings = await self.db_client.get_all_listings()

            # Group by agent and track last activity
            agent_activity = {}
            now = datetime.now(timezone.utc)

            for listing in all_listings:
                agent_id = listing.get('agent_id')
                created_at = listing.get('created_at')

                if not agent_id or not created_at:
                    continue

                # Parse created_at timestamp
                try:
                    if isinstance(created_at, str):
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        created_dt = created_at
                except:
                    continue

                if agent_id not in agent_activity:
                    agent_activity[agent_id] = {
                        "user_id": agent_id,
                        "last_activity": created_dt,
                        "total_contributions": 0,
                    }

                # Track latest activity and count
                if created_dt > agent_activity[agent_id]["last_activity"]:
                    agent_activity[agent_id]["last_activity"] = created_dt

                agent_activity[agent_id]["total_contributions"] += 1

            # Detect silent members: > 30 days inactive with <3 contributions total
            silent_members = []
            for data in agent_activity.values():
                days_since_activity = (now - data["last_activity"]).days

                if days_since_activity > 30 and data["total_contributions"] < 3:
                    silent_members.append({
                        "user_id": data["user_id"],
                        "days_since_last_activity": days_since_activity,
                        "total_contributions": data["total_contributions"],
                        "governance_participation": 0,  # Can't calculate yet
                        "pattern": "silence",
                    })

            logger.info(f"Detected {len(silent_members)} silent members")
            return silent_members

        except Exception as e:
            logger.error(f"Error detecting silent members: {e}", exc_info=True)
            return self._get_mock_silent_members()

    def _get_mock_silent_members(self) -> List[Dict[str, Any]]:
        """Fallback mock data"""
        logger.warning("Using mock silent members data")
        return [
            {
                "user_id": "user:quiet_bob",
                "days_since_last_activity": 45,
                "total_contributions": 2,
                "governance_participation": 0,
                "pattern": "silence",
            },
        ]

    async def _detect_saboteurs(self) -> List[Dict[str, Any]]:
        """
        Detect members who repeatedly block without explanation.

        Returns:
            List of saboteur data
        """
        # TODO: Query voting/blocking patterns
        # For now, return mock data

        return [
            {
                "user_id": "user:blocker",
                "total_blocks": 15,
                "total_votes": 20,
                "blocking_rate": 0.75,  # 75% of votes are blocks
                "blocks_with_explanation": 2,
                "pattern": "obstruction",
            },
        ]

    async def _create_centralization_warning(
        self,
        centralization: Dict[str, Any]
    ) -> Proposal:
        """
        Create a centralization warning proposal.

        Args:
            centralization: Centralization data

        Returns:
            Centralization warning proposal
        """
        user_id = centralization["user_id"]
        centralization_type = centralization["type"]

        if centralization_type == "governance":
            percentage = centralization["percentage_of_approvals"]
            role = centralization.get("role", "decision_maker")

            return Proposal(
                agent_name=self.agent_name,
                proposal_type=ProposalType.CENTRALIZATION_WARNING,
                title=f"Centralization warning: {user_id}",
                explanation=(
                    f"{user_id} is performing {percentage:.0f}% of {role} actions. "
                    f"This creates a Single Point of Need and risks hierarchy formation. "
                    f"Consider distributing this responsibility more widely or "
                    f"automating some decisions. This is not a punishment—it's a "
                    f"structural observation."
                ),
                inputs_used=[
                    f"approval_patterns:{role}:last_30_days",
                ],
                constraints=[
                    "Tone: Warning, not punishment",
                    "Community decides response",
                    "Recognize: This person may be helping, not power-seeking",
                ],
                data={
                    "user_id": user_id,
                    "centralization_type": centralization_type,
                    "percentage": percentage,
                    "role": role,
                    "period_days": centralization.get("period_days", 30),
                    "suggestions": [
                        "Rotate this role among multiple people",
                        "Create clear guidelines for others to learn this role",
                        "Automate routine decisions",
                        "Set term limits or rotation schedules",
                    ],
                },
                requires_approval=[],  # Warning only
            )

        elif centralization_type == "saboteur":
            blocking_rate = centralization["blocking_rate"]

            return Proposal(
                agent_name=self.agent_name,
                proposal_type=ProposalType.CENTRALIZATION_WARNING,
                title=f"Obstruction pattern detected: {user_id}",
                explanation=(
                    f"{user_id} is blocking {blocking_rate*100:.0f}% of proposals "
                    f"without providing explanations. This obstructs consensus. "
                    f"The community should discuss whether this pattern serves "
                    f"collective needs or personal grievances."
                ),
                inputs_used=[
                    f"voting_patterns:{user_id}:last_30_days",
                ],
                constraints=[
                    "Restorative: Seek to understand reasons",
                    "Community decides next steps",
                ],
                data={
                    "user_id": user_id,
                    "blocking_rate": blocking_rate,
                    "suggestions": [
                        "Initiate restorative circle",
                        "Request explanations for blocks",
                        "Offer voluntary secession option",
                    ],
                },
                requires_approval=[],
            )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.CENTRALIZATION_WARNING,
            title=f"Centralization detected: {user_id}",
            explanation="Power asymmetry detected. Community review recommended.",
            inputs_used=["network_analysis"],
            constraints=[],
            data=centralization,
            requires_approval=[],
        )

    async def _create_warlord_alert(
        self,
        warlord: Dict[str, Any]
    ) -> Proposal:
        """
        Create a warlord alert proposal.

        Args:
            warlord: Warlord data

        Returns:
            Warlord alert proposal
        """
        user_id = warlord["user_id"]
        resource_type = warlord["resource_type"]
        stock = warlord["stock_units"]
        outflow = warlord["avg_weekly_outflow"]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.WARLORD_ALERT,
            title=f"Resource hoarding detected: {resource_type}",
            explanation=(
                f"{user_id} has accumulated {stock} units of {resource_type} "
                f"but only circulates ~{outflow} units/week. "
                f"This looks like hoarding rather than productive guild formation. "
                f"A Battery Guild would have high stock AND high outflow. "
                f"Consider: Is this serving the commons or creating scarcity?"
            ),
            inputs_used=[
                f"inventory:{user_id}:{resource_type}",
                f"flow_patterns:{user_id}:{resource_type}",
            ],
            constraints=[
                "Guild distinction: High stock + high outflow = productive guild",
                "Warlord pattern: High stock + low outflow = hoarding",
                "Community decides response",
            ],
            data={
                "user_id": user_id,
                "resource_type": resource_type,
                "stock_units": stock,
                "avg_weekly_outflow": outflow,
                "inflow_rate": warlord.get("inflow_rate", 0),
                "classification": warlord["guild_classification"],
                "suggestions": [
                    "Request explanation for accumulation",
                    "Propose resource redistribution",
                    "Initiate governance discussion",
                ],
            },
            requires_approval=[],  # Alert only
        )

    async def _create_pruning_prompt(
        self,
        member: Dict[str, Any]
    ) -> Proposal:
        """
        Create a pruning prompt proposal (private check-in).

        Args:
            member: Silent member data

        Returns:
            Pruning prompt proposal
        """
        user_id = member["user_id"]
        days_inactive = member["days_since_last_activity"]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.PRUNING_PROMPT,
            title=f"Check-in with inactive member: {user_id}",
            explanation=(
                f"{user_id} has been inactive for {days_inactive} days. "
                f"This might mean they're busy, or they might prefer to leave. "
                f"Send a private, supportive check-in: 'Do you want to stay? "
                f"Do you want to leave? Both are okay.' "
                f"Voluntary association means exit must be easy and stigma-free."
            ),
            inputs_used=[
                f"activity:{user_id}:last_90_days",
            ],
            constraints=[
                "Privacy: Private message, not public",
                "Supportive: Not a punishment",
                "Voluntary: Leaving is okay",
            ],
            data={
                "user_id": user_id,
                "days_inactive": days_inactive,
                "pattern": member.get("pattern", "silence"),
                "suggested_message": (
                    "Hey! We noticed you've been quiet lately. No judgment—life "
                    "happens. Just checking in: Do you want to stay in the network? "
                    "If you'd prefer to leave, that's totally okay and we can help "
                    "make that easy. What works for you?"
                ),
            },
            requires_approval=[
                "steward:community_care",  # Care steward sends the message
            ],
        )
