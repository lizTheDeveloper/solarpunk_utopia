"""
Education Pathfinder Agent

Recommends lessons and protocols tied to upcoming work commitments.
Creates just-in-time learning paths with prerequisites.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class EducationPathfinder(BaseAgent):
    """
    Recommends just-in-time learning for upcoming tasks.

    Analyzes:
    - Upcoming Commitments
    - Processes in active Plans
    - User's existing skills
    - Available Lessons and Protocols

    Creates learning path proposals with prerequisites ordered.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(
            agent_name="education-pathfinder",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )

    async def analyze(self) -> List[Proposal]:
        """
        Analyze upcoming commitments and recommend learning paths.

        Returns:
            List of learning path proposals
        """
        proposals = []

        # Get upcoming commitments
        commitments = await self._get_upcoming_commitments()

        for commitment in commitments:
            # Check if user needs learning for this commitment
            user_id = commitment["user_id"]
            user_skills = await self._get_user_skills(user_id)
            required_skills = commitment.get("skills_needed", [])

            # Find skill gaps
            skill_gaps = set(required_skills) - user_skills

            if skill_gaps:
                # Recommend learning path
                learning_proposal = await self._recommend_learning_path(
                    commitment,
                    user_id,
                    skill_gaps,
                    user_skills,
                )
                if learning_proposal:
                    proposals.append(learning_proposal)

        logger.info(f"Created {len(proposals)} learning path proposals")
        return proposals

    async def _get_upcoming_commitments(self) -> List[Dict[str, Any]]:
        """
        Query upcoming commitments from VF database.

        Returns:
            List of commitments in next 14 days
        """
        # TODO: Query actual VF Commitments
        # For now, return mock data
        return [
            {
                "id": "commit:bob-hive-inspection",
                "user_id": "bob",
                "user_name": "Bob",
                "task": "Assist with hive inspection",
                "scheduled_date": datetime.now(timezone.utc) + timedelta(days=7),
                "skills_needed": ["beekeeping", "safety"],
                "process_id": "process:hive-management",
                "bundle_id": "bundle:commit-bob-hive",
            },
            {
                "id": "commit:eve-grafting",
                "user_id": "eve",
                "user_name": "Eve",
                "task": "Learn fruit tree grafting",
                "scheduled_date": datetime.now(timezone.utc) + timedelta(days=10),
                "skills_needed": ["grafting", "tree_care"],
                "process_id": "process:tree-propagation",
                "bundle_id": "bundle:commit-eve-grafting",
            },
        ]

    async def _get_user_skills(self, user_id: str) -> Set[str]:
        """
        Get user's existing skills.

        Returns:
            Set of skill names
        """
        # TODO: Query actual user skills from database
        # For now, return mock data
        user_skills_db = {
            "bob": {"gardening", "composting"},
            "eve": {"gardening", "permaculture", "cooking"},
            "alice": {"beekeeping", "herbalism", "foraging"},
        }
        return user_skills_db.get(user_id, set())

    async def _recommend_learning_path(
        self,
        commitment: Dict[str, Any],
        user_id: str,
        skill_gaps: Set[str],
        existing_skills: Set[str],
    ) -> Optional[Proposal]:
        """
        Create learning path proposal for commitment.

        Args:
            commitment: Commitment requiring learning
            user_id: User who needs learning
            skill_gaps: Skills user needs to learn
            existing_skills: Skills user already has

        Returns:
            Learning path proposal
        """
        # Find lessons for skill gaps
        lessons = await self._find_lessons_for_skills(skill_gaps, commitment)

        if not lessons:
            return None

        # Order lessons by prerequisites
        ordered_lessons = self._order_by_prerequisites(lessons)

        # Calculate recommended schedule
        days_until_commitment = (
            commitment["scheduled_date"] - datetime.now(timezone.utc)
        ).days
        schedule = self._create_learning_schedule(
            ordered_lessons,
            days_until_commitment
        )

        # Build explanation
        skill_list = ", ".join(skill_gaps)
        explanation = (
            f"{commitment['user_name']} has commitment '{commitment['task']}' "
            f"in {days_until_commitment} days. "
            f"Recommending {len(ordered_lessons)} lessons to learn: {skill_list}. "
            f"Lessons ordered by prerequisites for effective learning."
        )

        # Identify critical prerequisites
        prerequisites = [
            lesson["title"]
            for lesson in ordered_lessons
            if lesson.get("is_prerequisite")
        ]

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.LEARNING_PATH,
            title=f"Learning Path: {commitment['task']}",
            explanation=explanation,
            inputs_used=[
                commitment["bundle_id"],
                f"user_skills:{user_id}",
                "lesson_database",
            ],
            constraints=[
                f"Complete before {commitment['scheduled_date'].strftime('%B %d')}",
                *[f"Prerequisite: {p}" for p in prerequisites],
            ],
            data={
                "commitment_id": commitment["id"],
                "user_id": user_id,
                "skill_gaps": list(skill_gaps),
                "existing_skills": list(existing_skills),
                "lessons": ordered_lessons,
                "schedule": schedule,
                "days_until_commitment": days_until_commitment,
            },
            requires_approval=[user_id],
        )

    async def _find_lessons_for_skills(
        self,
        skills: Set[str],
        commitment: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find lessons that teach required skills.

        Returns:
            List of relevant lessons
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get lessons for each skill
            all_lessons_list = []
            for skill in skills:
                lessons = await self.db_client.get_lessons(topic=skill)
                all_lessons_list.extend(lessons)
            return all_lessons_list
        except Exception as e:
            logger.warning(f"Failed to query VF database for lessons: {e}")
            # Fallback to mock lesson data if DB unavailable

        all_lessons = {
            "beekeeping": [
                {
                    "id": "lesson:beekeeping-safety",
                    "title": "Beekeeping Safety Basics",
                    "description": "Essential safety protocols for working with bees",
                    "format": "video",
                    "duration_minutes": 5,
                    "tags": ["beekeeping", "safety"],
                    "is_prerequisite": True,
                    "prerequisites": [],
                    "bundle_id": "bundle:lesson-bee-safety",
                },
                {
                    "id": "lesson:hive-inspection-checklist",
                    "title": "Hive Inspection Checklist",
                    "description": "Step-by-step inspection procedure",
                    "format": "pdf",
                    "duration_minutes": 10,
                    "tags": ["beekeeping", "inspection"],
                    "is_prerequisite": False,
                    "prerequisites": ["lesson:beekeeping-safety"],
                    "bundle_id": "bundle:lesson-hive-inspection",
                },
                {
                    "id": "lesson:bee-behavior",
                    "title": "Reading Bee Behavior",
                    "description": "Understanding bee communication and colony health",
                    "format": "interactive",
                    "duration_minutes": 10,
                    "tags": ["beekeeping", "observation"],
                    "is_prerequisite": False,
                    "prerequisites": ["lesson:beekeeping-safety"],
                    "bundle_id": "bundle:lesson-bee-behavior",
                },
            ],
            "grafting": [
                {
                    "id": "lesson:grafting-basics",
                    "title": "Grafting Fundamentals",
                    "description": "Introduction to grafting techniques",
                    "format": "video",
                    "duration_minutes": 15,
                    "tags": ["grafting", "propagation"],
                    "is_prerequisite": True,
                    "prerequisites": [],
                    "bundle_id": "bundle:lesson-grafting-basics",
                },
                {
                    "id": "lesson:whip-graft",
                    "title": "Whip and Tongue Graft",
                    "description": "Learn the whip and tongue grafting technique",
                    "format": "video",
                    "duration_minutes": 20,
                    "tags": ["grafting", "technique"],
                    "is_prerequisite": False,
                    "prerequisites": ["lesson:grafting-basics"],
                    "bundle_id": "bundle:lesson-whip-graft",
                },
            ],
            "safety": [
                {
                    "id": "lesson:general-safety",
                    "title": "General Safety Protocols",
                    "description": "Basic safety for commune work parties",
                    "format": "pdf",
                    "duration_minutes": 5,
                    "tags": ["safety"],
                    "is_prerequisite": True,
                    "prerequisites": [],
                    "bundle_id": "bundle:lesson-safety",
                },
            ],
            "tree_care": [
                {
                    "id": "lesson:tree-anatomy",
                    "title": "Tree Anatomy and Physiology",
                    "description": "Understanding how trees grow and heal",
                    "format": "interactive",
                    "duration_minutes": 15,
                    "tags": ["tree_care", "botany"],
                    "is_prerequisite": True,
                    "prerequisites": [],
                    "bundle_id": "bundle:lesson-tree-anatomy",
                },
            ],
        }

        # Collect lessons for all required skills
        relevant_lessons = []
        for skill in skills:
            skill_lessons = all_lessons.get(skill, [])
            relevant_lessons.extend(skill_lessons)

        # Add relevant protocols
        if commitment.get("process_id"):
            protocols = await self._find_relevant_protocols(commitment["process_id"])
            relevant_lessons.extend(protocols)

        return relevant_lessons

    async def _find_relevant_protocols(self, process_id: str) -> List[Dict[str, Any]]:
        """
        Find protocols relevant to process.

        Returns:
            List of protocol documents
        """
        # Query actual VF database via client
        if self.db_client is None:
            from ..clients.vf_client import VFClient
            self.db_client = VFClient()

        try:
            # Get all protocols (repeatable processes)
            protocols_list = await self.db_client.get_protocols()
            return protocols_list
        except Exception as e:
            logger.warning(f"Failed to query VF database for protocols: {e}")
            # Fallback to mock protocols if DB unavailable

        protocols = {
            "process:hive-management": [
                {
                    "id": "protocol:hive-inspection",
                    "title": "Community Hive Inspection Protocol",
                    "description": "Standard procedure for inspecting community hives",
                    "format": "pdf",
                    "duration_minutes": 5,
                    "tags": ["beekeeping", "protocol"],
                    "is_prerequisite": False,
                    "prerequisites": ["lesson:beekeeping-safety"],
                    "bundle_id": "bundle:protocol-hive-inspection",
                }
            ],
        }
        return protocols.get(process_id, [])

    def _order_by_prerequisites(
        self,
        lessons: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Order lessons by prerequisite dependencies.

        Returns:
            Lessons ordered so prerequisites come first
        """
        # Build dependency graph
        lesson_map = {lesson["id"]: lesson for lesson in lessons}
        ordered = []
        processed = set()

        def add_lesson(lesson_id: str):
            if lesson_id in processed:
                return
            if lesson_id not in lesson_map:
                return

            lesson = lesson_map[lesson_id]

            # Add prerequisites first
            for prereq_id in lesson.get("prerequisites", []):
                add_lesson(prereq_id)

            # Add this lesson
            if lesson_id not in processed:
                ordered.append(lesson)
                processed.add(lesson_id)

        # Process all lessons
        for lesson in lessons:
            add_lesson(lesson["id"])

        return ordered

    def _create_learning_schedule(
        self,
        lessons: List[Dict[str, Any]],
        days_until_commitment: int
    ) -> List[Dict[str, Any]]:
        """
        Create recommended learning schedule.

        Returns:
            Schedule with recommended completion dates
        """
        if days_until_commitment < 1:
            days_until_commitment = 1

        # Calculate total learning time
        total_minutes = sum(lesson.get("duration_minutes", 0) for lesson in lessons)

        # Space out lessons over available time
        # Leave buffer of 2 days before commitment
        available_days = max(1, days_until_commitment - 2)

        schedule = []
        current_offset = 0

        for i, lesson in enumerate(lessons):
            # Spread lessons evenly, with prerequisites first
            if lesson.get("is_prerequisite"):
                # Prerequisites should be done early (first 1/3 of time)
                offset_days = min(current_offset, available_days // 3)
            else:
                offset_days = current_offset

            recommended_date = datetime.now(timezone.utc) + timedelta(days=offset_days)

            schedule.append({
                "lesson_id": lesson["id"],
                "lesson_title": lesson["title"],
                "recommended_date": recommended_date.isoformat(),
                "duration_minutes": lesson.get("duration_minutes", 0),
                "format": lesson.get("format", "unknown"),
                "is_prerequisite": lesson.get("is_prerequisite", False),
            })

            # Increment offset for next lesson
            current_offset += max(1, available_days // len(lessons))

        return schedule
