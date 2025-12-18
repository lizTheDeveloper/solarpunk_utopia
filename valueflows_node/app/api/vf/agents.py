"""
Agents API Endpoints

POST /vf/agents - Create agent
GET /vf/agents - List agents
GET /vf/agents/{id} - Get agent
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import uuid

from ...models.vf.agent import Agent, AgentType
from ...database import get_database
from ...repositories.vf.agent_repo import AgentRepository
from ...services.signing_service import SigningService

router = APIRouter(prefix="/vf/agents", tags=["agents"])


@router.post("", response_model=dict)
async def create_agent(agent_data: dict):
    """
    Create a new agent.

    Request body should contain:
    - name: Agent name
    - type: Agent type ("person", "group", or "place")
    - description (optional): Description of agent
    - image_url (optional): URL to image
    - primary_location_id (optional): Primary location ID
    - contact_info (optional): Contact information
    """
    try:
        # Generate ID if not provided
        if "id" not in agent_data:
            agent_data["id"] = f"agent:{uuid.uuid4()}"

        # Set timestamps
        agent_data["created_at"] = datetime.now().isoformat()

        # Handle field name mapping: "type" in request -> "agent_type" in model
        if "type" in agent_data:
            agent_data["agent_type"] = agent_data.pop("type")

        # Create Agent object
        agent = Agent.from_dict(agent_data)

        # Sign the agent
        # In production, get private key from authenticated user context
        # For now, generate a mock keypair
        keypair = SigningService.generate_keypair()
        signer = SigningService(keypair['private_key'])
        signer.sign_and_update(agent, agent.id)

        # Save to database
        db = get_database()
        db.connect()
        agent_repo = AgentRepository(db.conn)
        created_agent = agent_repo.create(agent)
        db.close()

        return created_agent.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=dict)
async def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by type: person, group, or place"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    limit: int = Query(100, description="Maximum results")
):
    """
    List agents with filters.

    Query parameters:
    - agent_type: Filter by type ("person", "group", or "place")
    - name: Filter by name (partial match)
    - limit: Maximum results
    """
    try:
        db = get_database()
        db.connect()
        agent_repo = AgentRepository(db.conn)

        # Apply filters
        if agent_type:
            agent_type_enum = AgentType(agent_type)
            agents = agent_repo.find_by_type(agent_type_enum)
        elif name:
            agents = agent_repo.find_by_name(name)
        else:
            agents = agent_repo.find_all(limit=limit)

        db.close()

        return {
            "agents": [a.to_dict() for a in agents],
            "count": len(agents)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}", response_model=dict)
async def get_agent(agent_id: str):
    """Get agent by ID"""
    try:
        db = get_database()
        db.connect()
        agent_repo = AgentRepository(db.conn)
        agent = agent_repo.find_by_id(agent_id)
        db.close()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
