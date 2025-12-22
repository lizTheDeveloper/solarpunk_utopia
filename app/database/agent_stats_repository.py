"""Repository for agent statistics tracking"""
import aiosqlite
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Dict
from uuid import uuid4
import json

from app.database.db import get_db


class AgentStats:
    """Agent statistics model"""
    def __init__(
        self,
        agent_name: str,
        last_run: Optional[str],
        proposals_created: int,
        total_runs: int,
        avg_duration_seconds: Optional[float] = None,
        error_count: int = 0,
    ):
        self.agent_name = agent_name
        self.last_run = last_run
        self.proposals_created = proposals_created
        self.total_runs = total_runs
        self.avg_duration_seconds = avg_duration_seconds
        self.error_count = error_count

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "last_run": self.last_run,
            "proposals_created": self.proposals_created,
            "total_runs": self.total_runs,
            "avg_duration_seconds": self.avg_duration_seconds,
            "error_count": self.error_count,
        }


class AgentStatsRepository:
    """Repository for agent run statistics"""

    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self.db = db

    async def _get_db(self) -> aiosqlite.Connection:
        """Get database connection"""
        if self.db:
            return self.db
        return await get_db()

    async def record_run(
        self,
        agent_name: str,
        proposals_created: int = 0,
        errors: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        status: str = "completed",
    ) -> str:
        """Record an agent run

        Args:
            agent_name: Name of the agent
            proposals_created: Number of proposals created during run
            errors: JSON string of errors if any occurred
            duration_seconds: How long the run took
            status: Status of the run (completed, failed, partial)

        Returns:
            Run ID
        """
        db = await self._get_db()
        run_id = str(uuid4())
        run_at = datetime.now(UTC).isoformat()

        await db.execute(
            """
            INSERT INTO agent_runs (id, agent_name, run_at, proposals_created, errors, duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, agent_name, run_at, proposals_created, errors, duration_seconds, status),
        )
        await db.commit()

        return run_id

    async def get_stats(self, agent_name: str) -> AgentStats:
        """Get agent statistics

        Args:
            agent_name: Name of the agent

        Returns:
            AgentStats object with aggregated statistics
        """
        db = await self._get_db()

        # Get aggregated stats
        cursor = await db.execute(
            """
            SELECT
                COUNT(*) as total_runs,
                MAX(run_at) as last_run,
                SUM(proposals_created) as total_proposals,
                AVG(duration_seconds) as avg_duration,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as error_count
            FROM agent_runs
            WHERE agent_name = ?
            """,
            (agent_name,),
        )
        row = await cursor.fetchone()

        if not row or row[0] == 0:
            # No runs recorded
            return AgentStats(
                agent_name=agent_name,
                last_run=None,
                proposals_created=0,
                total_runs=0,
                avg_duration_seconds=None,
                error_count=0,
            )

        return AgentStats(
            agent_name=agent_name,
            last_run=row[1],
            proposals_created=int(row[2] or 0),
            total_runs=int(row[0]),
            avg_duration_seconds=float(row[3]) if row[3] else None,
            error_count=int(row[4] or 0),
        )

    async def get_recent_runs(
        self,
        agent_name: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get recent runs for an agent

        Args:
            agent_name: Name of the agent
            limit: Maximum number of runs to return

        Returns:
            List of run dictionaries
        """
        db = await self._get_db()

        cursor = await db.execute(
            """
            SELECT id, run_at, proposals_created, errors, duration_seconds, status
            FROM agent_runs
            WHERE agent_name = ?
            ORDER BY run_at DESC
            LIMIT ?
            """,
            (agent_name, limit),
        )
        rows = await cursor.fetchall()

        return [
            {
                "id": row[0],
                "run_at": row[1],
                "proposals_created": row[2],
                "errors": json.loads(row[3]) if row[3] else None,
                "duration_seconds": row[4],
                "status": row[5],
            }
            for row in rows
        ]

    async def get_all_agent_stats(self) -> List[AgentStats]:
        """Get statistics for all agents that have run

        Returns:
            List of AgentStats for all agents
        """
        db = await self._get_db()

        cursor = await db.execute(
            """
            SELECT DISTINCT agent_name FROM agent_runs
            """
        )
        rows = await cursor.fetchall()

        stats = []
        for row in rows:
            agent_stats = await self.get_stats(row[0])
            stats.append(agent_stats)

        return stats

    async def cleanup_old_runs(self, days_to_keep: int = 30) -> int:
        """Clean up old agent run records

        Args:
            days_to_keep: How many days of history to keep

        Returns:
            Number of records deleted
        """
        db = await self._get_db()

        cutoff_date = (datetime.now(UTC) - timedelta(days=days_to_keep)).isoformat()

        cursor = await db.execute(
            """
            DELETE FROM agent_runs
            WHERE run_at < ?
            """,
            (cutoff_date,),
        )
        await db.commit()

        return cursor.rowcount
