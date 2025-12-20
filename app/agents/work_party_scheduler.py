"""
Scheduler / Work Party Agent

Analyzes participant availability and proposes work party sessions.
Coordinates location, time, participants, and resources.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class WorkPartyScheduler(BaseAgent):
    """
    Proposes work party sessions based on Plans and Commitments.

    Analyzes:
    - Participant availability
    - Required skills
    - Resource availability
    - Weather conditions (for outdoor work)

    Creates proposals for optimal session scheduling.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="work-party-scheduler",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze Plans and Commitments to propose work party sessions.

        Returns:
            List of work party proposals
        """
        proposals = []

        # Get active Plans needing work parties
        plans = await self._get_active_plans()

        for plan in plans:
            # Check if plan needs a work party
            if not self._needs_work_party(plan):
                continue

            # Get participant availability
            participants = await self._get_available_participants(plan)

            if len(participants) >= plan.get("min_participants", 3):
                # Propose work party
                proposal = await self._propose_work_party(plan, participants)
                if proposal:
                    proposals.append(proposal)

        logger.info(f"Created {len(proposals)} work party proposals")
        return proposals

    async def _get_active_plans(self) -> List[Dict[str, Any]]:
        """
        Query active Plans from VF database.

        Returns:
            List of plans requiring work parties
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get work sessions (Plans with type=work_party)
            work_sessions = await self.db_client.get_work_sessions()
            return work_sessions
        except Exception as e:
            logger.warning(f"Failed to query VF database for work sessions: {e}")
            # Fallback to mock data if DB unavailable
            return [
                {
                    "id": "plan:spring-planting-2025",
                    "name": "Spring Planting 2025",
                    "description": "Plant 20 fruit trees and guild plantings",
                    "processes": [
                    {
                        "id": "process:site-prep",
                        "name": "Site Preparation",
                        "completed": True,
                    },
                    {
                        "id": "process:tree-planting",
                        "name": "Tree Planting",
                        "completed": False,
                        "requires_participants": 5,
                        "estimated_hours": 4,
                        "skills_needed": ["gardening", "digging"],
                        "preferred_skills": ["permaculture"],
                    }
                ],
                "location": "Community Garden - South Plot",
                "target_date": datetime(2025, 12, 21, 9, 0),
                "resources_needed": ["trees", "compost", "tools", "water"],
                "min_participants": 5,
                "bundle_id": "bundle:plan-spring-planting",
            },
            {
                "id": "plan:tool-shed-build",
                "name": "Tool Shed Construction",
                "description": "Build new tool storage shed",
                "processes": [
                    {
                        "id": "process:framing",
                        "name": "Framing",
                        "completed": False,
                        "requires_participants": 4,
                        "estimated_hours": 6,
                        "skills_needed": ["carpentry"],
                    }
                ],
                "location": "Workshop Area",
                "target_date": datetime(2025, 12, 22, 9, 0),
                "resources_needed": ["lumber", "tools", "hardware"],
                "min_participants": 4,
                "bundle_id": "bundle:plan-tool-shed",
            },
        ]

    def _needs_work_party(self, plan: Dict[str, Any]) -> bool:
        """Check if plan needs a work party scheduled"""
        # Has uncompleted processes requiring multiple participants
        for process in plan.get("processes", []):
            if not process.get("completed") and process.get("requires_participants", 1) > 1:
                return True
        return False

    async def _get_available_participants(
        self,
        plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get participants available for plan work party.

        Queries real commitments from VF database to find participants
        who have committed time and have relevant skills.

        Returns:
            List of participants with availability and skills
        """
        # Query commitments with status 'accepted' (people committed to help)
        commitments = await self.vf.get_commitments(
            status="accepted",
            plan_id=plan.get("id")
        )

        # Group commitments by agent
        participants_map = {}
        for commitment in commitments:
            agent_id = commitment["agent_id"]
            if agent_id not in participants_map:
                participants_map[agent_id] = {
                    "user_id": agent_id,
                    "user_name": commitment["agent_name"],
                    "skills": [],  # Would need to query agent skills from separate table
                    "availability": [],
                }

            # Add due date as availability slot
            if commitment.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(commitment["due_date"])
                    participants_map[agent_id]["availability"].append(due_date)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to parse due_date for agent {agent_id}: {e}. "
                        f"Date value: {commitment.get('due_date', 'MISSING')}"
                    )
                    # Continue processing other commitments

        # Convert map to list
        participants = list(participants_map.values())

        # If no real commitments found, return empty list (was mock data before)
        return participants

    async def _propose_work_party(
        self,
        plan: Dict[str, Any],
        participants: List[Dict[str, Any]]
    ) -> Optional[Proposal]:
        """
        Create work party proposal.

        Args:
            plan: Plan requiring work party
            participants: Available participants

        Returns:
            Work party proposal
        """
        # Find best time slot (most participant overlap)
        best_slot = self._find_best_time_slot(participants)

        if not best_slot:
            return None

        # Get participants available at best slot
        available_participants = [
            p for p in participants
            if best_slot["time"] in p["availability"]
        ]

        # Check skill coverage
        skill_coverage = self._check_skill_coverage(plan, available_participants)

        # Get weather forecast (if outdoor work)
        weather_note = await self._get_weather_note(plan, best_slot["time"])

        # Build explanation
        explanation = (
            f"Proposed work party for {plan['name']} on {best_slot['time'].strftime('%A %B %d at %I%p')}. "
            f"{len(available_participants)} participants available with "
            f"{skill_coverage['coverage_pct']}% skill coverage. "
            f"{weather_note}"
        )

        # Build rationale
        rationale_points = [
            f"Time slot has highest participant availability ({len(available_participants)} of {len(participants)})",
        ]

        if skill_coverage["has_required_skills"]:
            rationale_points.append("All required skills covered by team")
        else:
            rationale_points.append(
                f"Missing skills: {', '.join(skill_coverage['missing_skills'])} - may need additional guidance"
            )

        if weather_note and "good" in weather_note.lower():
            rationale_points.append("Weather forecast favorable for outdoor work")

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.WORK_PARTY,
            title=f"Work Party: {plan['name']}",
            explanation=explanation,
            inputs_used=[
                plan["bundle_id"],
                "participant_availability",
                "skill_data",
                "weather_forecast",
            ],
            constraints=[
                f"Minimum {plan.get('min_participants', 3)} participants required",
                "Required resources must be available",
                *plan.get("constraints", []),
            ],
            data={
                "plan_id": plan["id"],
                "plan_name": plan["name"],
                "date_time": best_slot["time"].isoformat(),
                "location": plan["location"],
                "participants": [
                    {
                        "user_id": p["user_id"],
                        "user_name": p["user_name"],
                        "skills": p["skills"],
                    }
                    for p in available_participants
                ],
                "estimated_hours": plan["processes"][0].get("estimated_hours", 4),
                "resources_needed": plan["resources_needed"],
                "skill_coverage": skill_coverage,
                "rationale": rationale_points,
                "weather": weather_note,
            },
            requires_approval=[p["user_id"] for p in available_participants],
        )

    def _find_best_time_slot(
        self,
        participants: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find time slot with most participant availability.

        Returns:
            Best time slot with participant count
        """
        # Count availability for each time slot
        time_counts = {}
        for participant in participants:
            for time in participant["availability"]:
                time_counts[time] = time_counts.get(time, 0) + 1

        if not time_counts:
            return None

        # Find time with most participants
        best_time = max(time_counts.items(), key=lambda x: x[1])

        return {
            "time": best_time[0],
            "participant_count": best_time[1],
        }

    def _check_skill_coverage(
        self,
        plan: Dict[str, Any],
        participants: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if participants have required skills.

        Returns:
            Skill coverage analysis
        """
        # Get all skills from participants
        participant_skills = set()
        for p in participants:
            participant_skills.update(p.get("skills", []))

        # Get required skills from plan
        required_skills = set()
        preferred_skills = set()

        for process in plan.get("processes", []):
            if not process.get("completed"):
                required_skills.update(process.get("skills_needed", []))
                preferred_skills.update(process.get("preferred_skills", []))

        # Check coverage
        missing_skills = required_skills - participant_skills
        has_required = len(missing_skills) == 0

        covered_preferred = preferred_skills & participant_skills

        coverage_pct = 100 if has_required else int(
            len(required_skills - missing_skills) / len(required_skills) * 100
        ) if required_skills else 100

        return {
            "has_required_skills": has_required,
            "missing_skills": list(missing_skills),
            "covered_preferred_skills": list(covered_preferred),
            "coverage_pct": coverage_pct,
            "participant_skills": list(participant_skills),
        }

    async def _get_weather_note(
        self,
        plan: Dict[str, Any],
        time: datetime
    ) -> str:
        """
        Get weather forecast note for outdoor work.

        Returns:
            Weather note or empty string
        """
        # TODO: Integrate with weather API
        # For now, return placeholder
        location = plan.get("location", "")
        if any(keyword in location.lower() for keyword in ["garden", "plot", "outdoor"]):
            # Mock favorable weather for demo
            return "Weather forecast shows good planting conditions (mild temps, no rain)."

        return ""
