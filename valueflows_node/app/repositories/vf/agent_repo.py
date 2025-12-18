"""
Agent Repository

CRUD operations for Agents.
"""

from typing import Optional, List
import sqlite3
from datetime import datetime

from ...models.vf.agent import Agent, AgentType
from .base_repo import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    """Repository for Agent objects"""

    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "agents", Agent)

    def create(self, agent: Agent) -> Agent:
        """
        Create a new agent.

        Args:
            agent: Agent object

        Returns:
            Created agent
        """
        if agent.created_at is None:
            agent.created_at = datetime.now()

        query = """
            INSERT INTO agents (
                id, name, agent_type, description, image_url, primary_location_id,
                contact_info, created_at, updated_at, author, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            agent.id,
            agent.name,
            agent.agent_type.value,
            agent.description,
            agent.image_url,
            agent.primary_location_id,
            agent.contact_info,
            agent.created_at.isoformat() if agent.created_at else None,
            agent.updated_at.isoformat() if agent.updated_at else None,
            agent.author,
            agent.signature,
        )

        self._execute(query, params)
        self.conn.commit()

        return agent

    def update(self, agent: Agent) -> Agent:
        """
        Update existing agent.

        Args:
            agent: Agent object

        Returns:
            Updated agent
        """
        agent.updated_at = datetime.now()

        query = """
            UPDATE agents SET
                name = ?,
                agent_type = ?,
                description = ?,
                image_url = ?,
                primary_location_id = ?,
                contact_info = ?,
                updated_at = ?
            WHERE id = ?
        """

        params = (
            agent.name,
            agent.agent_type.value,
            agent.description,
            agent.image_url,
            agent.primary_location_id,
            agent.contact_info,
            agent.updated_at.isoformat(),
            agent.id,
        )

        self._execute(query, params)
        self.conn.commit()

        return agent

    def find_by_type(self, agent_type: AgentType) -> List[Agent]:
        """Find agents by type"""
        query = "SELECT * FROM agents WHERE agent_type = ? ORDER BY name"
        rows = self._fetch_all(query, (agent_type.value,))
        return [Agent.from_dict(row) for row in rows]

    def find_by_name(self, name: str) -> List[Agent]:
        """Find agents by name (partial match)"""
        query = "SELECT * FROM agents WHERE name LIKE ? ORDER BY name"
        rows = self._fetch_all(query, (f"%{name}%",))
        return [Agent.from_dict(row) for row in rows]
