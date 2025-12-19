"""
Pydantic Validation Models for Agent API

GAP-43: Input Validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from enum import Enum
import json


class AgentType(str, Enum):
    """Valid agent types"""
    MUTUAL_AID_MATCHMAKER = "mutual-aid-matchmaker"
    COMMONS_ROUTER = "commons-router"
    WORK_PARTY_SCHEDULER = "work-party-scheduler"
    EDUCATION_PATHFINDER = "education-pathfinder"
    PERMACULTURE_PLANNER = "permaculture-planner"
    PROPOSAL_EXECUTOR = "proposal-executor"
    INVENTORY_AGENT = "inventory-agent"
    PERISHABLES_DISPATCHER = "perishables-dispatcher"


class AgentInvokeRequest(BaseModel):
    """
    Request model for invoking an agent.

    Validates:
    - Agent type is valid
    - Context object size is reasonable
    - User ID format if provided
    """

    agent_type: AgentType
    context: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = Field(None, min_length=1, max_length=200)

    @field_validator('context')
    @classmethod
    def validate_context_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Prevent DOS via huge context objects"""
        size = len(json.dumps(v))
        if size > 100000:  # 100KB max
            raise ValueError(f"Context object too large ({size} bytes, max 100KB)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "agent_type": "mutual-aid-matchmaker",
                "context": {
                    "location": "Portland",
                    "urgency": "high"
                },
                "user_id": "agent:alice"
            }
        }


class ProposalApproval(BaseModel):
    """
    Request model for approving a proposal.

    Validates:
    - Approval decision is boolean
    - User ID is valid
    - Comment length is reasonable
    """

    approved: bool
    user_id: str = Field(..., min_length=1, max_length=200)
    comment: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "user_id": "agent:alice",
                "comment": "Looks good to me!"
            }
        }
