"""Repository for agent settings persistence"""
import aiosqlite
from datetime import datetime, UTC
from typing import Optional, Dict
import json

from app.database.db import get_db


class AgentSettingsRepository:
    """Repository for agent settings persistence"""

    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self.db = db

    async def _get_db(self) -> aiosqlite.Connection:
        """Get database connection"""
        if self.db:
            return self.db
        return await get_db()

    async def get_settings(self, agent_name: str) -> Optional[Dict]:
        """Get settings for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Settings dictionary or None if not found
        """
        db = await self._get_db()

        cursor = await db.execute(
            "SELECT settings FROM agent_settings WHERE agent_name = ?",
            (agent_name,),
        )
        row = await cursor.fetchone()

        if row:
            return json.loads(row[0])
        return None

    async def save_settings(self, agent_name: str, settings: Dict) -> None:
        """Save settings for an agent

        Args:
            agent_name: Name of the agent
            settings: Settings dictionary to save
        """
        db = await self._get_db()
        updated_at = datetime.now(UTC).isoformat()
        settings_json = json.dumps(settings)

        await db.execute(
            """
            INSERT OR REPLACE INTO agent_settings (agent_name, settings, updated_at)
            VALUES (?, ?, ?)
            """,
            (agent_name, settings_json, updated_at),
        )
        await db.commit()

    async def get_all_settings(self) -> Dict[str, Dict]:
        """Get settings for all agents

        Returns:
            Dictionary mapping agent names to their settings
        """
        db = await self._get_db()

        cursor = await db.execute(
            "SELECT agent_name, settings FROM agent_settings"
        )
        rows = await cursor.fetchall()

        return {
            row[0]: json.loads(row[1])
            for row in rows
        }

    async def delete_settings(self, agent_name: str) -> bool:
        """Delete settings for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            True if settings were deleted, False if not found
        """
        db = await self._get_db()

        cursor = await db.execute(
            "DELETE FROM agent_settings WHERE agent_name = ?",
            (agent_name,),
        )
        await db.commit()

        return cursor.rowcount > 0
