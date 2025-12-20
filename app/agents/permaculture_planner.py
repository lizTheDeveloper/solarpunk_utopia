"""
Permaculture Seasonal Planner Agent

Transforms high-level goals into seasonal plans with processes and dependencies.
Uses permaculture knowledge (guilds, companion planting, seasonal cycles).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .framework import BaseAgent, AgentConfig, Proposal, ProposalType


logger = logging.getLogger(__name__)


class PermaculturePlanner(BaseAgent):
    """
    Generates seasonal plans from goals using permaculture principles.

    Creates:
    - Process sequences with dependencies
    - Timeline based on climate/season
    - Resource requirements
    - Guild plantings (companion species)
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        db_client: Optional[Any] = None,
        bundle_publisher: Optional[Any] = None,
        llm_client: Optional[Any] = None,
        climate_zone: str = "9b",  # USDA hardiness zone
    ):
        super().__init__(
            agent_name="permaculture-planner",
            config=config,
            db_client=db_client,
            bundle_publisher=bundle_publisher,
            llm_client=llm_client,
        )
        self.climate_zone = climate_zone

    async def analyze(self) -> List[Proposal]:
        """
        Analyze goals and generate seasonal plans.

        Returns:
            List of seasonal plan proposals
        """
        proposals = []

        # Get goals needing planning
        goals = await self._get_unplanned_goals()

        for goal in goals:
            # Generate plan using permaculture knowledge
            plan_proposal = await self._generate_seasonal_plan(goal)
            if plan_proposal:
                proposals.append(plan_proposal)

        logger.info(f"Created {len(proposals)} permaculture plan proposals")
        return proposals

    async def _get_unplanned_goals(self) -> List[Dict[str, Any]]:
        """
        Query goals without associated plans.

        Returns:
            List of goals needing planning
        """
        if not self.vf:
            return []

        try:
            # Try to query goals table if it exists
            # NOTE: goals table doesn't exist yet in VF schema
            # When it's added, this will automatically start working
            self.vf.connect()
            cursor = self.vf.conn.cursor()

            # Check if goals table exists
            table_check = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='goals'"
            ).fetchone()

            if not table_check:
                # Goals table doesn't exist yet
                return []

            # Query goals without associated plans
            rows = cursor.execute("""
                SELECT g.*
                FROM goals g
                LEFT JOIN plans p ON p.goal_id = g.id
                WHERE p.id IS NULL
                ORDER BY g.target_completion
            """).fetchall()

            results = []
            for row in rows:
                row_dict = dict(row)
                results.append({
                    "id": row_dict["id"],
                    "name": row_dict.get("name", "Unnamed Goal"),
                    "description": row_dict.get("description", ""),
                    "target_completion": datetime.fromisoformat(row_dict["target_completion"]) if row_dict.get("target_completion") else None,
                    "constraints": [],  # Would need to parse from JSON field if exists
                    "bundle_id": f"bundle:goal-{row_dict['id']}",
                })

            return results

        except Exception as e:
            logger.warning(f"Could not query goals table (may not exist yet): {e}")
            return []

    async def _generate_seasonal_plan(self, goal: Dict[str, Any]) -> Optional[Proposal]:
        """
        Generate comprehensive seasonal plan from goal.

        Uses LLM for complex reasoning if available, otherwise uses
        rule-based permaculture knowledge.

        Args:
            goal: Goal to plan for

        Returns:
            Seasonal plan proposal
        """
        # Use LLM for complex planning if available
        if self.llm_client:
            plan_data = await self._llm_generate_plan(goal)
        else:
            plan_data = await self._rule_based_plan(goal)

        if not plan_data:
            return None

        # Build explanation
        explanation = (
            f"Generated {len(plan_data['processes'])}-step plan for '{goal['name']}'. "
            f"Timeline spans {plan_data['duration_weeks']} weeks from "
            f"{plan_data['start_date'].strftime('%B %Y')} to "
            f"{plan_data['end_date'].strftime('%B %Y')}. "
            f"Incorporates permaculture principles: {', '.join(plan_data['principles'][:2])}."
        )

        return Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.SEASONAL_PLAN,
            title=f"Seasonal Plan: {goal['name']}",
            explanation=explanation,
            inputs_used=[
                goal["bundle_id"],
                f"climate_zone:{self.climate_zone}",
                "permaculture_knowledge",
                "seasonal_calendar",
            ],
            constraints=[
                *goal.get("constraints", []),
                "Follow permaculture ethics (earth care, people care, fair share)",
            ],
            data=plan_data,
            requires_approval=["garden-coordinator"],
        )

    async def _llm_generate_plan(self, goal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to generate plan with permaculture reasoning.

        Returns:
            Plan data structure
        """
        # TODO: Implement actual LLM call
        # For now, fall back to rule-based
        return await self._rule_based_plan(goal)

    async def _rule_based_plan(self, goal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate plan using rule-based permaculture knowledge.

        Returns:
            Plan data structure
        """
        goal_id = goal["id"]

        # Food forest plan
        if "food-forest" in goal_id or "food forest" in goal["description"].lower():
            return self._create_food_forest_plan(goal)

        # Seed saving plan
        elif "seed" in goal_id or "seed" in goal["description"].lower():
            return self._create_seed_saving_plan(goal)

        # Generic plan
        else:
            return self._create_generic_plan(goal)

    def _create_food_forest_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create food forest establishment plan.

        Follows permaculture design process:
        1. Site analysis
        2. Design (guilds, spacing, access)
        3. Soil preparation
        4. Tree selection and sourcing
        5. Planting
        6. Guild establishment (nitrogen fixers, pest deterrents)
        7. Mulching
        8. Maintenance schedule
        """
        start_date = datetime(2025, 1, 15)  # Mid-January start
        current_date = start_date

        processes = [
            {
                "name": "Site Analysis",
                "description": "Analyze sun exposure, water flow, soil composition, and microclimates",
                "duration_weeks": 1,
                "dependencies": [],
                "resources_needed": ["soil test kit", "measuring tape", "compass"],
                "skills_needed": ["permaculture design", "soil analysis"],
                "start_date": current_date,
            }
        ]
        current_date += timedelta(weeks=1)

        processes.append({
            "name": "Permaculture Design",
            "description": "Design guilds, spacing, paths, and water management",
            "duration_weeks": 2,
            "dependencies": ["Site Analysis"],
            "resources_needed": ["design software or paper", "guild references"],
            "skills_needed": ["permaculture design"],
            "start_date": current_date,
        })
        current_date += timedelta(weeks=2)

        processes.append({
            "name": "Soil Preparation",
            "description": "Amend soil with compost, create swales for water retention",
            "duration_weeks": 2,
            "dependencies": ["Permaculture Design"],
            "resources_needed": ["compost (500 lbs)", "mulch", "tools"],
            "skills_needed": ["soil building", "earthworks"],
            "start_date": current_date,
        })
        current_date += timedelta(weeks=2)

        processes.append({
            "name": "Tree Selection and Sourcing",
            "description": "Select climate-appropriate fruit trees, source from local nurseries",
            "duration_weeks": 1,
            "dependencies": ["Permaculture Design"],
            "resources_needed": ["tree catalog", "budget allocation"],
            "skills_needed": ["plant knowledge"],
            "start_date": current_date,
        })
        current_date += timedelta(weeks=1)

        processes.append({
            "name": "Tree Planting",
            "description": "Plant 20 fruit trees at designed locations",
            "duration_weeks": 2,
            "dependencies": ["Soil Preparation", "Tree Selection and Sourcing"],
            "resources_needed": ["20 fruit trees", "compost", "tools", "water", "stakes"],
            "skills_needed": ["tree planting"],
            "participants_needed": 5,
            "start_date": current_date,
        })
        current_date += timedelta(weeks=2)

        processes.append({
            "name": "Guild Establishment",
            "description": "Plant nitrogen fixers, dynamic accumulators, and pest deterrents around trees",
            "duration_weeks": 2,
            "dependencies": ["Tree Planting"],
            "resources_needed": [
                "comfrey starts (40)",
                "clover seed",
                "yarrow plants (20)",
                "allium bulbs (100)",
            ],
            "skills_needed": ["companion planting"],
            "start_date": current_date,
            "guild_species": {
                "nitrogen_fixers": ["white clover", "vetch"],
                "dynamic_accumulators": ["comfrey", "yarrow"],
                "pest_deterrents": ["garlic", "chives", "marigold"],
                "pollinator_attractors": ["borage", "lavender"],
            },
        })
        current_date += timedelta(weeks=2)

        processes.append({
            "name": "Mulching",
            "description": "Apply deep mulch around all plantings for moisture retention and weed suppression",
            "duration_weeks": 1,
            "dependencies": ["Guild Establishment"],
            "resources_needed": ["wood chips (10 cubic yards)", "straw bales (20)"],
            "skills_needed": ["mulching"],
            "participants_needed": 3,
            "start_date": current_date,
        })
        current_date += timedelta(weeks=1)

        processes.append({
            "name": "Maintenance Schedule",
            "description": "Set up watering, pruning, and observation schedule",
            "duration_weeks": 1,
            "dependencies": ["Mulching"],
            "resources_needed": ["calendar", "observation journal"],
            "skills_needed": ["tree care"],
            "start_date": current_date,
            "ongoing": True,
        })

        return {
            "goal_id": goal["id"],
            "goal_name": goal["name"],
            "start_date": start_date,
            "end_date": current_date,
            "duration_weeks": (current_date - start_date).days // 7,
            "processes": processes,
            "principles": [
                "Observe and interact (site analysis first)",
                "Use and value diversity (guild plantings)",
                "Catch and store energy (water management)",
                "Obtain a yield (food production)",
                "Design from patterns to details",
            ],
            "expected_outcomes": [
                "20 productive fruit trees established",
                "Self-fertilizing guild ecosystem",
                "Increased biodiversity",
                "Educational demonstration site",
            ],
            "long_term_maintenance": [
                "Weekly watering for first 2 years",
                "Annual pruning in dormant season",
                "Mulch replenishment twice per year",
                "Harvest tracking and sharing",
            ],
        }

    def _create_seed_saving_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Create seed saving program plan"""
        start_date = datetime(2025, 2, 1)
        current_date = start_date

        processes = [
            {
                "name": "Seed Library Setup",
                "description": "Create physical seed library with organization system",
                "duration_weeks": 2,
                "dependencies": [],
                "resources_needed": ["cabinets", "envelopes", "labels", "catalog"],
                "start_date": current_date,
            },
            {
                "name": "Initial Seed Acquisition",
                "description": "Source heirloom seeds from seed libraries and exchanges",
                "duration_weeks": 2,
                "dependencies": ["Seed Library Setup"],
                "resources_needed": ["seed exchange contacts", "budget"],
                "start_date": current_date + timedelta(weeks=2),
            },
            {
                "name": "Growing Season",
                "description": "Grow selected varieties with isolation for seed purity",
                "duration_weeks": 20,
                "dependencies": ["Initial Seed Acquisition"],
                "resources_needed": ["garden space", "isolation barriers"],
                "start_date": current_date + timedelta(weeks=4),
            },
            {
                "name": "Seed Harvest and Processing",
                "description": "Harvest, clean, dry, and package seeds",
                "duration_weeks": 4,
                "dependencies": ["Growing Season"],
                "resources_needed": ["drying racks", "screens", "envelopes"],
                "start_date": current_date + timedelta(weeks=24),
            },
            {
                "name": "Documentation and Distribution",
                "description": "Document varieties and make available to community",
                "duration_weeks": 2,
                "dependencies": ["Seed Harvest and Processing"],
                "resources_needed": ["database or catalog"],
                "start_date": current_date + timedelta(weeks=28),
            },
        ]

        return {
            "goal_id": goal["id"],
            "goal_name": goal["name"],
            "start_date": start_date,
            "end_date": current_date + timedelta(weeks=30),
            "duration_weeks": 30,
            "processes": processes,
            "principles": [
                "Use and value diversity (heirloom varieties)",
                "Produce no waste (save seeds)",
                "Obtain a yield (seed abundance)",
                "Apply self-regulation (isolation for purity)",
            ],
            "expected_outcomes": [
                "Community seed library established",
                "50+ heirloom varieties saved",
                "Seed saving knowledge shared",
                "Food sovereignty increased",
            ],
        }

    def _create_generic_plan(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Create generic plan for unknown goal types"""
        start_date = datetime.now(timezone.utc) + timedelta(days=7)

        return {
            "goal_id": goal["id"],
            "goal_name": goal["name"],
            "start_date": start_date,
            "end_date": goal.get("target_completion", start_date + timedelta(weeks=12)),
            "duration_weeks": 12,
            "processes": [
                {
                    "name": "Planning and Design",
                    "description": "Define approach and gather resources",
                    "duration_weeks": 2,
                    "dependencies": [],
                    "start_date": start_date,
                },
                {
                    "name": "Implementation",
                    "description": "Execute plan",
                    "duration_weeks": 8,
                    "dependencies": ["Planning and Design"],
                    "start_date": start_date + timedelta(weeks=2),
                },
                {
                    "name": "Review and Refinement",
                    "description": "Assess outcomes and adjust",
                    "duration_weeks": 2,
                    "dependencies": ["Implementation"],
                    "start_date": start_date + timedelta(weeks=10),
                },
            ],
            "principles": ["Observe and interact", "Integrate rather than segregate"],
            "expected_outcomes": [goal["description"]],
        }
