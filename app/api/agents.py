"""
API endpoints for agent proposals and settings.

Provides:
- List proposals
- Approve/reject proposals
- View proposal details
- Configure agent settings
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.auth.middleware import require_auth, get_current_user
from app.auth.models import User

logger = logging.getLogger(__name__)

from app.agents import (
    approval_tracker,
    Proposal,
    ProposalStatus,
    ProposalType,
    ProposalFilter,
    AgentConfig,
    CommonsRouterAgent,
    MutualAidMatchmaker,
    PerishablesDispatcher,
    WorkPartyScheduler,
    PermaculturePlanner,
    EducationPathfinder,
    InventoryAgent,
)


router = APIRouter(prefix="/agents", tags=["agents"])


# Request/Response models

class ApprovalRequest(BaseModel):
    """Request to approve or reject a proposal"""
    approved: bool = Field(description="True to approve, False to reject")
    reason: Optional[str] = Field(None, description="Optional reason for decision")


class ProposalListResponse(BaseModel):
    """Response for listing proposals"""
    proposals: List[Proposal]
    total: int


class AgentSettingsRequest(BaseModel):
    """Request to update agent settings"""
    enabled: bool = Field(description="Enable or disable agent")
    check_interval_seconds: Optional[int] = Field(None, description="Check interval in seconds")
    proposal_ttl_hours: Optional[int] = Field(None, description="Proposal TTL in hours")
    auto_approve: Optional[bool] = Field(None, description="Auto-approve proposals (use with caution)")


class AgentSettingsResponse(BaseModel):
    """Response for agent settings"""
    agent_name: str
    config: Dict


class AgentStatsResponse(BaseModel):
    """Response for agent statistics"""
    stats: Dict


# Endpoints

@router.get("/proposals", response_model=ProposalListResponse)
async def list_proposals(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    proposal_type: Optional[ProposalType] = Query(None, description="Filter by proposal type"),
    status: Optional[ProposalStatus] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user (proposals requiring approval)"),
) -> ProposalListResponse:
    """
    List proposals with optional filters.

    Returns all proposals matching the filter criteria.
    """
    filter_obj = ProposalFilter(
        agent_name=agent_name,
        proposal_type=proposal_type,
        status=status,
        user_id=user_id,
    )

    proposals = await approval_tracker.list_proposals(filter_obj)

    return ProposalListResponse(
        proposals=proposals,
        total=len(proposals),
    )


@router.get("/proposals/pending/{user_id}")
async def get_pending_approvals(user_id: str) -> ProposalListResponse:
    """
    Get proposals pending approval from a specific user.

    Returns proposals awaiting this user's decision.
    """
    proposals = await approval_tracker.get_pending_approvals(user_id)

    return ProposalListResponse(
        proposals=proposals,
        total=len(proposals),
    )


@router.get("/proposals/pending/{user_id}/count")
async def get_pending_count(user_id: str) -> Dict[str, int]:
    """
    Get count of proposals pending approval from a specific user.

    Returns just the number - useful for badges and notifications.
    """
    proposals = await approval_tracker.get_pending_approvals(user_id)

    return {
        "user_id": user_id,
        "pending_count": len(proposals),
    }


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str) -> Proposal:
    """
    Get a specific proposal by ID.

    Returns full proposal details.
    """
    proposal = await approval_tracker.get_proposal(proposal_id)

    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")

    return proposal


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(require_auth),
) -> Proposal:
    """
    Approve or reject a proposal.

    Records the user's decision (approve/reject) and updates proposal status.
    If all required approvals are granted, proposal status becomes APPROVED
    and the proposal is automatically executed to create VF entities.

    Requires authentication.
    """
    try:
        proposal = await approval_tracker.approve_proposal(
            proposal_id=proposal_id,
            user_id=current_user.id,
            approved=request.approved,
            reason=request.reason,
        )

        # Execute approved proposal to create VF entities
        if proposal.status == ProposalStatus.APPROVED and not proposal.executed_at:
            from app.services import get_executor

            executor = get_executor()
            try:
                execution_result = await executor.execute_proposal(proposal)
                logger.info(
                    f"Executed proposal {proposal_id}: {execution_result}"
                )
            except Exception as e:
                logger.error(f"Failed to execute proposal {proposal_id}: {e}")
                # Don't fail the approval, just log the error
                # Proposal is still approved, just not executed yet

        return proposal

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: str,
    request: ApprovalRequest,
) -> Proposal:
    """
    Reject a proposal.

    Convenience endpoint that sets approved=False.
    """
    try:
        proposal = await approval_tracker.approve_proposal(
            proposal_id=proposal_id,
            user_id=request.user_id,
            approved=False,
            reason=request.reason,
        )

        return proposal

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings")
async def get_all_agent_settings() -> Dict[str, AgentSettingsResponse]:
    """
    Get settings for all agents.

    Returns configuration for each agent including enabled status.
    """
    # TODO: Load from database/config file
    # For now, return default configs
    agents = {
        "commons-router": CommonsRouterAgent,
        "mutual-aid-matchmaker": MutualAidMatchmaker,
        "perishables-dispatcher": PerishablesDispatcher,
        "work-party-scheduler": WorkPartyScheduler,
        "permaculture-planner": PermaculturePlanner,
        "education-pathfinder": EducationPathfinder,
        "inventory-agent": InventoryAgent,
    }

    settings = {}
    for name, agent_class in agents.items():
        # Create default instance to get config
        agent = agent_class()
        settings[name] = AgentSettingsResponse(
            agent_name=name,
            config=dict(agent.config),
        )

    return settings


@router.get("/settings/{agent_name}")
async def get_agent_settings(agent_name: str) -> AgentSettingsResponse:
    """
    Get settings for a specific agent.

    Returns agent configuration.
    """
    # TODO: Load from database/config file
    # For now, return default config

    agent_classes = {
        "commons-router": CommonsRouterAgent,
        "mutual-aid-matchmaker": MutualAidMatchmaker,
        "perishables-dispatcher": PerishablesDispatcher,
        "work-party-scheduler": WorkPartyScheduler,
        "permaculture-planner": PermaculturePlanner,
        "education-pathfinder": EducationPathfinder,
        "inventory-agent": InventoryAgent,
    }

    agent_class = agent_classes.get(agent_name)
    if not agent_class:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    agent = agent_class()

    return AgentSettingsResponse(
        agent_name=agent_name,
        config=dict(agent.config),
    )


@router.put("/settings/{agent_name}")
async def update_agent_settings(
    agent_name: str,
    request: AgentSettingsRequest,
) -> AgentSettingsResponse:
    """
    Update settings for a specific agent.

    Allows enabling/disabling agents and configuring behavior.
    """
    # TODO: Save to database/config file
    # For now, just return the requested settings

    if agent_name not in [
        "commons-router",
        "mutual-aid-matchmaker",
        "perishables-dispatcher",
        "work-party-scheduler",
        "permaculture-planner",
        "education-pathfinder",
        "inventory-agent",
    ]:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    config = {
        "enabled": request.enabled,
    }

    if request.check_interval_seconds is not None:
        config["check_interval_seconds"] = request.check_interval_seconds

    if request.proposal_ttl_hours is not None:
        config["proposal_ttl_hours"] = request.proposal_ttl_hours

    if request.auto_approve is not None:
        config["auto_approve"] = request.auto_approve

    return AgentSettingsResponse(
        agent_name=agent_name,
        config=config,
    )


@router.get("/stats")
async def get_all_agent_stats() -> Dict[str, AgentStatsResponse]:
    """
    Get statistics for all agents.

    Returns run statistics including proposal counts.
    """
    # TODO: Return actual stats from running agents
    # For now, return mock stats

    agents = [
        "commons-router",
        "mutual-aid-matchmaker",
        "perishables-dispatcher",
        "work-party-scheduler",
        "permaculture-planner",
        "education-pathfinder",
        "inventory-agent",
    ]

    stats = {}
    for name in agents:
        stats[name] = AgentStatsResponse(
            stats={
                "agent_name": name,
                "enabled": True if name != "inventory-agent" else False,
                "last_run": None,
                "proposals_created": 0,
            }
        )

    # Add approval tracker stats
    stats["approval_tracker"] = AgentStatsResponse(
        stats=await approval_tracker.get_stats()
    )

    return stats


@router.get("/stats/{agent_name}")
async def get_agent_stats(agent_name: str) -> AgentStatsResponse:
    """
    Get statistics for a specific agent.

    Returns run statistics including proposal counts.
    """
    # TODO: Return actual stats from running agent
    # For now, return mock stats

    if agent_name not in [
        "commons-router",
        "mutual-aid-matchmaker",
        "perishables-dispatcher",
        "work-party-scheduler",
        "permaculture-planner",
        "education-pathfinder",
        "inventory-agent",
    ]:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    return AgentStatsResponse(
        stats={
            "agent_name": agent_name,
            "enabled": True if agent_name != "inventory-agent" else False,
            "last_run": None,
            "proposals_created": 0,
        }
    )


@router.post("/run/{agent_name}")
async def run_agent_manually(agent_name: str) -> Dict:
    """
    Manually trigger an agent run.

    Useful for testing or immediate analysis.
    Returns proposals generated.
    """
    agent_classes = {
        "commons-router": CommonsRouterAgent,
        "mutual-aid-matchmaker": MutualAidMatchmaker,
        "perishables-dispatcher": PerishablesDispatcher,
        "work-party-scheduler": WorkPartyScheduler,
        "permaculture-planner": PermaculturePlanner,
        "education-pathfinder": EducationPathfinder,
        "inventory-agent": InventoryAgent,
    }

    agent_class = agent_classes.get(agent_name)
    if not agent_class:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    # Create and run agent
    agent = agent_class()
    proposals = await agent.run()

    # Store proposals
    for proposal in proposals:
        await approval_tracker.store_proposal(proposal)

    return {
        "agent_name": agent_name,
        "proposals_created": len(proposals),
        "proposals": [p.proposal_id for p in proposals],
    }


@router.post("/{agent_name}/run")
async def run_agent(agent_name: str, context: Optional[Dict] = None) -> Dict:
    """
    Execute an agent and return proposals.

    This endpoint is used by integration tests and external systems.
    Accepts optional context data (offers, needs, etc.) for agent analysis.

    Returns:
        {
            "agent_name": "mutual-aid-matchmaker",
            "proposals": [
                {
                    "id": "prop_123",
                    "agent_name": "mutual-aid-matchmaker",
                    "proposal_type": "match",
                    "explanation": "...",
                    "requires_approval": ["alice", "bob"],
                    "status": "pending",
                    ...
                }
            ]
        }
    """
    agent_classes = {
        "commons-router": CommonsRouterAgent,
        "mutual-aid-matchmaker": MutualAidMatchmaker,
        "perishables-dispatcher": PerishablesDispatcher,
        "work-party-scheduler": WorkPartyScheduler,
        "permaculture-planner": PermaculturePlanner,
        "education-pathfinder": EducationPathfinder,
        "inventory-agent": InventoryAgent,
    }

    agent_class = agent_classes.get(agent_name)
    if not agent_class:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    # Create agent (context data can be passed to agent constructor if needed)
    agent = agent_class()

    # Run agent analysis
    proposals = await agent.run()

    # Store proposals in approval tracker
    for proposal in proposals:
        await approval_tracker.store_proposal(proposal)

    # Return proposals in format expected by integration tests
    return {
        "agent_name": agent_name,
        "proposals": [
            {
                "id": p.proposal_id,
                "agent_name": p.agent_name,
                "proposal_type": p.proposal_type,
                "title": p.title,
                "explanation": p.explanation,
                "inputs_used": p.inputs_used,
                "constraints": p.constraints,
                "data": p.data,
                "requires_approval": p.requires_approval,
                "approvals": p.approvals,
                "approval_reasons": p.approval_reasons,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "expires_at": p.expires_at.isoformat() if p.expires_at else None,
                "bundle_id": p.bundle_id,
            }
            for p in proposals
        ]
    }


@router.post("/{agent_name}/proposals/{proposal_id}/approve")
async def approve_agent_proposal(
    agent_name: str,
    proposal_id: str,
    request: ApprovalRequest,
) -> Proposal:
    """
    Approve a specific agent proposal.

    Alternative endpoint format for agent-specific approval.
    Delegates to the main approval endpoint.
    """
    return await approve_proposal(proposal_id, request)


@router.get("")
async def list_agents() -> Dict:
    """
    List all available agents.

    Returns list of agent names that can be executed.
    """
    agent_names = [
        "commons-router",
        "mutual-aid-matchmaker",
        "perishables-dispatcher",
        "work-party-scheduler",
        "permaculture-planner",
        "education-pathfinder",
        "inventory-agent",
    ]

    return {
        "agents": agent_names,
        "total": len(agent_names)
    }
