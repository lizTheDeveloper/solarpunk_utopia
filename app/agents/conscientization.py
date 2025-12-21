"""
Conscientization Agent

Bridges the gap between consuming content and taking action.

Key Features:
- Resource Gap Identification: Parses content to identify needed tools/materials
- Mentor Connection: Finds local experts willing to teach
- Culture Circle Formation: Auto-matches people learning same topics
- Praxis Linking: Connects theory to physical action opportunities

Based on proposal: openspec/changes/conscientization-agent/proposal.md
Inspired by Paulo Freire's pedagogy of the oppressed
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"


class ConscientizationAgent(BaseAgent):
    """
    Transforms passive content consumption into active praxis.

    This agent:
    1. Identifies resource gaps when users consume learning content
    2. Matches learners with nearby mentors/teachers
    3. Forms culture circles when multiple people study same topic
    4. Links educational content to practical action opportunities
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="conscientization",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze learning patterns and generate proposals.

        Returns:
            List of resource requests, mentor matches, and culture circle proposals
        """
        proposals = []

        # Check for recent content consumption
        recent_learners = await self._get_recent_content_consumers()

        for learner in recent_learners:
            # Check if they need resources to act on what they learned
            resource_gaps = await self._identify_resource_gaps(learner)
            for gap in resource_gaps:
                proposal = await self._create_resource_request_proposal(learner, gap)
                proposals.append(proposal)

            # Find mentors for this topic
            mentors = await self._find_mentors(learner)
            if mentors:
                proposal = await self._create_mentor_match_proposal(learner, mentors)
                proposals.append(proposal)

        # Detect culture circle opportunities (multiple people learning same thing)
        culture_circles = await self._detect_culture_circle_opportunities()
        for circle in culture_circles:
            proposal = await self._create_culture_circle_proposal(circle)
            proposals.append(proposal)

        return proposals

    async def _get_recent_content_consumers(self) -> List[Dict[str, Any]]:
        """
        Get users who recently consumed learning content.

        Since there's no consumption tracking table yet, this infers learning
        activity from active NEED listings in the 'skills' category - someone
        posting a need for a skill is implicitly a learner.

        Returns:
            List of learner data
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_content_consumers()

        try:
            # Query active needs in the 'skills' category
            # These represent people wanting to learn
            needs = await self.db_client.get_active_needs()

            learners = []
            for need in needs:
                # Check if this is a skill-learning need
                if need.get('category') == 'skills':
                    learners.append({
                        "user_id": need.get('agent_id', 'unknown'),
                        "content_id": f"need:{need.get('id')}",
                        "content_title": need.get('title', 'Untitled'),
                        "content_type": "skill_need",
                        "topic": need.get('name', 'unknown'),
                        "consumed_at": datetime.fromisoformat(need['created_at']) if 'created_at' in need else datetime.now(timezone.utc),
                    })

            logger.info(f"Found {len(learners)} active learners from skill needs")
            return learners

        except Exception as e:
            logger.error(f"Error querying recent learners: {e}", exc_info=True)
            return self._get_mock_content_consumers()

    def _get_mock_content_consumers(self) -> List[Dict[str, Any]]:
        """Fallback mock data"""
        logger.warning("Using mock content consumers data")
        return [
            {
                "user_id": "user:alice",
                "content_id": "content:hydroponics_101",
                "content_title": "Hydroponics 101",
                "content_type": "video",
                "topic": "hydroponics",
                "consumed_at": datetime.now(timezone.utc) - timedelta(hours=2),
            },
        ]

    async def _identify_resource_gaps(
        self,
        learner: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify tools/materials needed for the learned skill.

        Args:
            learner: Learner data

        Returns:
            List of resource gaps
        """
        # TODO: Parse content metadata or use LLM to extract resource requirements
        # For now, return mock data

        topic = learner["topic"]

        if topic == "hydroponics":
            return [
                {
                    "resource_type": "water_pump",
                    "description": "Small water pump for circulation",
                    "required": True,
                },
                {
                    "resource_type": "nutrients",
                    "description": "Hydroponic nutrients (NPK)",
                    "required": True,
                },
            ]

        return []

    async def _find_mentors(
        self,
        learner: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find nearby mentors for this topic.

        Looks for active OFFER listings in the 'skills' category matching the topic.

        Args:
            learner: Learner data

        Returns:
            List of potential mentors
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_mentors(learner["topic"])

        try:
            # Query active skill offers
            offers = await self.db_client.get_active_offers()

            mentors = []
            topic = learner["topic"].lower()

            for offer in offers:
                # Check if this is a skill offer matching the topic
                if offer.get('category') == 'skills':
                    skill_name = offer.get('name', '').lower()
                    # Simple matching: if topic is in skill name or vice versa
                    if topic in skill_name or skill_name in topic:
                        mentors.append({
                            "user_id": offer.get('agent_id', 'unknown'),
                            "skill": offer.get('name', 'unknown'),
                            "skill_level": "available",  # We don't track skill level yet
                            "distance_km": 1.0,  # TODO: Calculate from location data
                            "available_to_teach": True,
                            "teaching_schedule": offer.get('notes', 'flexible'),
                        })

            logger.info(f"Found {len(mentors)} potential mentors for {topic}")
            return mentors

        except Exception as e:
            logger.error(f"Error finding mentors: {e}", exc_info=True)
            return self._get_mock_mentors(learner["topic"])

    def _get_mock_mentors(self, topic: str) -> List[Dict[str, Any]]:
        """Fallback mock mentors"""
        logger.warning(f"Using mock mentors for {topic}")
        if topic == "hydroponics":
            return [
                {
                    "user_id": "user:maria",
                    "skill": "hydroponics",
                    "skill_level": "expert",
                    "distance_km": 0.5,
                    "available_to_teach": True,
                    "teaching_schedule": "Tuesdays",
                },
            ]
        return []

    async def _detect_culture_circle_opportunities(self) -> List[Dict[str, Any]]:
        """
        Detect when multiple people are learning same topic.

        Groups people with skill NEEDs for the same topic - they could learn together.

        Returns:
            List of culture circle opportunities
        """
        if not self.db_client:
            logger.warning("No db_client available, using mock data")
            return self._get_mock_culture_circles()

        try:
            # Query active needs
            needs = await self.db_client.get_active_needs()

            # Group by topic (skill name)
            topic_groups = {}
            for need in needs:
                if need.get('category') == 'skills':
                    topic = need.get('name', 'unknown')
                    if topic not in topic_groups:
                        topic_groups[topic] = []

                    topic_groups[topic].append({
                        "user_id": need.get('agent_id', 'unknown'),
                        "need_id": need.get('id'),
                        "consumed_at": datetime.fromisoformat(need['created_at']) if 'created_at' in need else datetime.now(timezone.utc),
                    })

            # Find topics with 2+ learners
            circles = []
            for topic, learners in topic_groups.items():
                if len(learners) >= 2:  # Culture circle needs at least 2 people
                    circles.append({
                        "topic": topic,
                        "content_id": f"skill_learning:{topic}",
                        "learners": learners,
                        "count": len(learners),
                    })

            logger.info(f"Found {len(circles)} culture circle opportunities")
            return circles

        except Exception as e:
            logger.error(f"Error detecting culture circles: {e}", exc_info=True)
            return self._get_mock_culture_circles()

    def _get_mock_culture_circles(self) -> List[Dict[str, Any]]:
        """Fallback mock data"""
        logger.warning("Using mock culture circle data")
        return [
            {
                "topic": "data_sovereignty",
                "content_id": "content:marx_in_data_center",
                "learners": [
                    {"user_id": "user:alice", "consumed_at": datetime.now(timezone.utc)},
                    {"user_id": "user:bob", "consumed_at": datetime.now(timezone.utc) - timedelta(hours=12)},
                    {"user_id": "user:carol", "consumed_at": datetime.now(timezone.utc) - timedelta(hours=18)},
                ],
                "count": 3,
            },
        ]

    async def _create_resource_request_proposal(
        self,
        learner: Dict[str, Any],
        resource_gap: Dict[str, Any]
    ) -> Proposal:
        """
        Create a resource request proposal.

        Args:
            learner: Learner data
            resource_gap: Resource gap data

        Returns:
            Resource request proposal
        """
        user_id = learner["user_id"]
        content_title = learner["content_title"]
        resource_type = resource_gap["resource_type"]
        description = resource_gap["description"]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.RESOURCE_REQUEST,
            title=f"Resource request: {resource_type} for {user_id}",
            explanation=(
                f"{user_id} just watched '{content_title}' and needs "
                f"{description} to put this learning into practice. "
                f"Can the community provide this from the Common Heap?"
            ),
            inputs_used=[
                f"content_access:{learner['content_id']}:{user_id}",
                f"content_metadata:{learner['content_id']}",
            ],
            constraints=[
                "Timing: Resource needed soon to maintain momentum",
                "Availability: Check Common Heap first",
            ],
            data={
                "user_id": user_id,
                "content_id": learner["content_id"],
                "content_title": content_title,
                "resource_type": resource_type,
                "resource_description": description,
                "required": resource_gap.get("required", False),
                "alternatives": resource_gap.get("alternatives", []),
            },
            requires_approval=[
                "steward:inventory",  # Inventory steward approves resource allocation
            ],
        )

    async def _create_mentor_match_proposal(
        self,
        learner: Dict[str, Any],
        mentors: List[Dict[str, Any]]
    ) -> Proposal:
        """
        Create a mentor match proposal.

        Args:
            learner: Learner data
            mentors: List of potential mentors

        Returns:
            Mentor match proposal
        """
        user_id = learner["user_id"]
        content_title = learner["content_title"]
        topic = learner["topic"]

        mentor_options = [
            f"{m['user_id']} ({m['distance_km']}km away, teaches {m['teaching_schedule']})"
            for m in mentors
        ]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.MENTOR_MATCH,
            title=f"Mentor match: {topic} for {user_id}",
            explanation=(
                f"{user_id} is learning {topic} (watched '{content_title}'). "
                f"Found {len(mentors)} nearby mentor(s) who can teach: "
                f"{', '.join(mentor_options)}. "
                f"Would you like an introduction?"
            ),
            inputs_used=[
                f"content_access:{learner['content_id']}:{user_id}",
                f"user_skills:topic:{topic}",
                f"user_location:{user_id}",
            ],
            constraints=[
                "Consent: Both parties must agree to connection",
                "Respect: Mentors volunteer their time as a gift",
            ],
            data={
                "learner_id": user_id,
                "topic": topic,
                "content_id": learner["content_id"],
                "mentors": [
                    {
                        "user_id": m["user_id"],
                        "skill_level": m["skill_level"],
                        "distance_km": m["distance_km"],
                        "teaching_schedule": m["teaching_schedule"],
                    }
                    for m in mentors
                ],
            },
            requires_approval=[
                user_id,  # Learner approves connection
                mentors[0]["user_id"],  # At least one mentor must approve
            ],
        )

    async def _create_culture_circle_proposal(
        self,
        circle: Dict[str, Any]
    ) -> Proposal:
        """
        Create a culture circle formation proposal.

        Args:
            circle: Culture circle opportunity data

        Returns:
            Culture circle proposal
        """
        topic = circle["topic"]
        learners = circle["learners"]
        count = circle["count"]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.CULTURE_CIRCLE,
            title=f"Form culture circle: {topic}",
            explanation=(
                f"{count} people have recently studied content about {topic}. "
                f"A Culture Circle could form to discuss and apply these ideas "
                f"together. Collective study deepens understanding and builds "
                f"solidarity."
            ),
            inputs_used=[
                f"content_access:{circle['content_id']}:recent",
            ],
            constraints=[
                "Voluntary: Opt-in participation",
                "Facilitation: Needs a facilitator (can rotate)",
                "Format: Study circle, not lecture",
            ],
            data={
                "topic": topic,
                "content_id": circle["content_id"],
                "potential_participants": [l["user_id"] for l in learners],
                "participant_count": count,
                "suggested_format": "weekly_study_circle",
                "suggested_duration_weeks": 4,
                "facilitator_role": "rotating",
            },
            requires_approval=[
                l["user_id"] for l in learners  # All learners must opt in
            ],
        )
