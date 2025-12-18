"""
Agent framework for Commune OS.

Provides proposal generation, publishing, and approval tracking.
"""

from .proposal import (
    Proposal,
    ProposalType,
    ProposalStatus,
    ProposalFilter,
)
from .base_agent import BaseAgent, AgentConfig
from .approval import ApprovalTracker, approval_tracker

__all__ = [
    "Proposal",
    "ProposalType",
    "ProposalStatus",
    "ProposalFilter",
    "BaseAgent",
    "AgentConfig",
    "ApprovalTracker",
    "approval_tracker",
]
