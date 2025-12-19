"""
Request Validation Models for Agent API

GAP-43: Input Validation
"""

from .agents import AgentInvokeRequest, ProposalApproval

__all__ = [
    "AgentInvokeRequest",
    "ProposalApproval",
]
