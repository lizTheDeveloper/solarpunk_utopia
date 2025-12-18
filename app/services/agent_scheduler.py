"""
Agent Scheduler Service

Runs AI agents on scheduled intervals for proactive commune coordination.
Agents emit proposals that require human approval before taking effect.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.agents import (
    BaseAgent,
    CommonsRouterAgent,
    MutualAidMatchmaker,
    PerishablesDispatcher,
    WorkPartyScheduler,
    PermaculturePlanner,
    EducationPathfinder,
    InventoryAgent,
)
from app.llm import get_llm_client, LLMConfig

logger = logging.getLogger(__name__)


class AgentScheduler:
    """
    Background service that runs agents on scheduled intervals.

    Agents run proactively to:
    - Match mutual aid offers/needs
    - Detect perishable goods
    - Schedule work parties
    - Optimize cache and forwarding
    - Plan seasonal activities
    - Suggest learning paths
    - Monitor inventory levels
    """

    def __init__(
        self,
        agents: Optional[List[BaseAgent]] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        Initialize scheduler.

        Args:
            agents: List of agents to schedule (defaults to all 7 agents)
            llm_config: LLM configuration (defaults to env vars)
        """
        self.llm_config = llm_config or LLMConfig.from_env()
        self.llm_client = get_llm_client(self.llm_config)

        # Initialize agents with LLM client
        self.agents = agents or self._create_default_agents()

        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._stats: Dict[str, int] = {
            "total_runs": 0,
            "total_proposals": 0,
            "errors": 0,
        }

    def _create_default_agents(self) -> List[BaseAgent]:
        """Create all 7 default agents with LLM client"""
        agents = [
            CommonsRouterAgent(),
            MutualAidMatchmaker(),
            PerishablesDispatcher(),
            WorkPartyScheduler(),
            PermaculturePlanner(),
            EducationPathfinder(),
            InventoryAgent(),
        ]

        # Set LLM client on all agents
        for agent in agents:
            agent.llm_client = self.llm_client

        return agents

    async def start(self):
        """Start scheduler - runs agents in background"""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        logger.info(f"Starting agent scheduler with {len(self.agents)} agents")
        logger.info(f"Using LLM backend: {self.llm_config.backend} ({self.llm_config.model})")

        # Create background task for each agent
        for agent in self.agents:
            if agent.enabled:
                task = asyncio.create_task(self._run_agent_loop(agent))
                self._tasks.append(task)
                logger.info(
                    f"Scheduled {agent.agent_name} "
                    f"(interval: {agent.config.get('check_interval_seconds', 300)}s)"
                )

    async def stop(self):
        """Stop scheduler - cancels all agent tasks"""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping agent scheduler...")

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        logger.info("Agent scheduler stopped")

    async def _run_agent_loop(self, agent: BaseAgent):
        """
        Run agent on scheduled interval.

        Args:
            agent: Agent to run
        """
        interval = agent.config.get("check_interval_seconds", 300)

        while self._running:
            try:
                # Run agent
                logger.debug(f"Running {agent.agent_name}...")
                proposals = await agent.run()

                # Update stats
                self._stats["total_runs"] += 1
                self._stats["total_proposals"] += len(proposals)

                if proposals:
                    logger.info(
                        f"{agent.agent_name} created {len(proposals)} proposals: "
                        f"{[p.title for p in proposals]}"
                    )

            except asyncio.CancelledError:
                logger.info(f"Agent {agent.agent_name} cancelled")
                break

            except Exception as e:
                logger.error(f"Error running {agent.agent_name}: {e}", exc_info=True)
                self._stats["errors"] += 1

            # Wait for next interval
            await asyncio.sleep(interval)

    async def run_once(self):
        """Run all agents once (useful for testing)"""
        logger.info("Running all agents once...")

        for agent in self.agents:
            if agent.enabled:
                try:
                    proposals = await agent.run()
                    logger.info(
                        f"{agent.agent_name}: {len(proposals)} proposals"
                    )
                except Exception as e:
                    logger.error(f"Error running {agent.agent_name}: {e}")

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        return {
            "running": self._running,
            "agents": len(self.agents),
            "enabled_agents": len([a for a in self.agents if a.enabled]),
            "llm_backend": self.llm_config.backend,
            "llm_model": self.llm_config.model,
            **self._stats,
        }


# Global scheduler instance
_scheduler: Optional[AgentScheduler] = None


def get_scheduler() -> AgentScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler


async def start_scheduler():
    """Start global scheduler"""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop global scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()
