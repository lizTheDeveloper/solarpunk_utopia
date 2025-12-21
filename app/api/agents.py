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
    current_user: Optional[User] = Depends(get_current_user),
) -> ProposalListResponse:
    """
    List proposals with optional filters.

    Returns all proposals matching the filter criteria.
    GAP-42: Now uses authenticated user instead of user_id query parameter.
    """
    # Use current_user.id if authenticated, otherwise None (public view)
    user_id = current_user.id if current_user else None

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


@router.get("/proposals/pending")
async def get_pending_approvals(
    current_user: User = Depends(require_auth),
) -> ProposalListResponse:
    """
    Get proposals pending approval from the current user.

    Returns proposals awaiting this user's decision.
    GAP-42: Now requires authentication and uses current user.
    """
    proposals = await approval_tracker.get_pending_approvals(current_user.id)

    return ProposalListResponse(
        proposals=proposals,
        total=len(proposals),
    )


@router.get("/proposals/pending/count")
async def get_pending_count(
    current_user: User = Depends(require_auth),
) -> Dict[str, int]:
    """
    Get count of proposals pending approval from the current user.

    Returns just the number - useful for badges and notifications.
    GAP-42: Now requires authentication and uses current user.
    """
    proposals = await approval_tracker.get_pending_approvals(current_user.id)

    return {
        "user_id": current_user.id,
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
                # Mark proposal as executed and save to database
                await approval_tracker.mark_executed(proposal_id)
                # Refresh proposal from database to get updated status
                proposal = await approval_tracker.get_proposal(proposal_id)
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
    current_user: User = Depends(require_auth),
) -> Proposal:
    """
    Reject a proposal.

    Convenience endpoint that sets approved=False.
    Fixed GAP-72: Now uses current_user from auth instead of request.user_id
    """
    try:
        proposal = await approval_tracker.approve_proposal(
            proposal_id=proposal_id,
            user_id=current_user.id,
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
    from app.database.agent_settings_repository import AgentSettingsRepository

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

    # Try to load saved settings from database
    settings_repo = AgentSettingsRepository()
    saved_settings = await settings_repo.get_settings(agent_name)

    if saved_settings:
        # Return saved settings
        config = saved_settings
    else:
        # Return default config from agent class
        agent = agent_class()
        config = dict(agent.config)

    return AgentSettingsResponse(
        agent_name=agent_name,
        config=config,
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
    from app.database.agent_settings_repository import AgentSettingsRepository

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

    # Save settings to database
    settings_repo = AgentSettingsRepository()
    await settings_repo.save_settings(agent_name, config)

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
    from app.database.agent_stats_repository import AgentStatsRepository

    stats_repo = AgentStatsRepository()

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
        agent_stats = await stats_repo.get_stats(name)
        stats[name] = AgentStatsResponse(
            stats={
                "agent_name": name,
                "enabled": True if name != "inventory-agent" else False,
                "last_run": agent_stats.last_run,
                "proposals_created": agent_stats.proposals_created,
                "total_runs": agent_stats.total_runs,
                "avg_duration_seconds": agent_stats.avg_duration_seconds,
                "error_count": agent_stats.error_count,
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
    from app.database.agent_stats_repository import AgentStatsRepository

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

    stats_repo = AgentStatsRepository()
    agent_stats = await stats_repo.get_stats(agent_name)

    return AgentStatsResponse(
        stats={
            "agent_name": agent_name,
            "enabled": True if agent_name != "inventory-agent" else False,
            "last_run": agent_stats.last_run,
            "proposals_created": agent_stats.proposals_created,
            "total_runs": agent_stats.total_runs,
            "avg_duration_seconds": agent_stats.avg_duration_seconds,
            "error_count": agent_stats.error_count,
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
    List all available agents with full metadata.

    Returns list of agent objects with configuration and stats.
    GAP-55: Enhanced to return full agent details instead of just names.
    """
    from app.database.agent_settings_repository import AgentSettingsRepository
    from app.database.agent_stats_repository import AgentStatsRepository

    agent_configs = {
        "commons-router": {
            "type": "unused_resource_matcher",
            "name": "Commons Router",
            "description": "Matches unused resources with community needs"
        },
        "mutual-aid-matchmaker": {
            "type": "unused_resource_matcher",
            "name": "Mutual Aid Matchmaker",
            "description": "Connects people who can help with those who need help"
        },
        "perishables-dispatcher": {
            "type": "resource_lifespan_tracker",
            "name": "Perishables Dispatcher",
            "description": "Ensures perishable resources are used before expiration"
        },
        "work-party-scheduler": {
            "type": "need_aggregator",
            "name": "Work Party Scheduler",
            "description": "Coordinates group work sessions for large tasks"
        },
        "permaculture-planner": {
            "type": "seasonal_need_predictor",
            "name": "Permaculture Planner",
            "description": "Plans seasonal growing and harvesting cycles"
        },
        "education-pathfinder": {
            "type": "knowledge_sharer",
            "name": "Education Pathfinder",
            "description": "Connects learners with teachers and resources"
        },
        "inventory-agent": {
            "type": "unused_resource_matcher",
            "name": "Inventory Agent",
            "description": "Tracks and optimizes community resource inventory"
        },
    }

    settings_repo = AgentSettingsRepository()
    stats_repo = AgentStatsRepository()

    agents = []
    for agent_name, config in agent_configs.items():
        # Get settings (enabled status, config)
        settings = await settings_repo.get_settings(agent_name) or {"enabled": True}

        # Get stats (last run, etc)
        stats = await stats_repo.get_stats(agent_name)

        agents.append({
            "id": agent_name,
            "type": config["type"],
            "name": config["name"],
            "description": config["description"],
            "enabled": settings.get("enabled", True),
            "opt_in": settings.get("opt_in", True),
            "last_run": stats.last_run.isoformat() if stats and stats.last_run else None,
            "next_scheduled_run": None,  # TODO: implement scheduling
            "run_interval_seconds": settings.get("check_interval_seconds", 3600),
            "config": settings
        })

    return {
        "agents": agents,
        "total": len(agents)
    }
