"""
Commune OS Agent System

7 specialized agents that provide intelligent coordination for the gift economy.
All agents emit proposals (not allocations) that require human approval.
"""

from .framework import (
    BaseAgent,
    AgentConfig,
    Proposal,
    ProposalType,
    ProposalStatus,
    ProposalFilter,
    ApprovalTracker,
    approval_tracker,
)

from .commons_router import CommonsRouterAgent
from .mutual_aid_matchmaker import MutualAidMatchmaker
from .perishables_dispatcher import PerishablesDispatcher
from .work_party_scheduler import WorkPartyScheduler
from .permaculture_planner import PermaculturePlanner
from .education_pathfinder import EducationPathfinder
from .inventory_agent import InventoryAgent


__all__ = [
    # Framework
    "BaseAgent",
    "AgentConfig",
    "Proposal",
    "ProposalType",
    "ProposalStatus",
    "ProposalFilter",
    "ApprovalTracker",
    "approval_tracker",
    # Agents
    "CommonsRouterAgent",
    "MutualAidMatchmaker",
    "PerishablesDispatcher",
    "WorkPartyScheduler",
    "PermaculturePlanner",
    "EducationPathfinder",
    "InventoryAgent",
]
