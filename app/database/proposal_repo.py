"""
Proposal Repository

Handles persistence of agent proposals to SQLite database.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
import aiosqlite

from app.agents.framework import Proposal, ProposalStatus, ProposalType, ProposalFilter
from .db import get_db

logger = logging.getLogger(__name__)


class ProposalRepository:
    """Repository for persisting agent proposals"""

    @staticmethod
    async def save(proposal: Proposal) -> None:
        """
        Save or update a proposal in the database.

        Args:
            proposal: Proposal to save
        """
        db = await get_db()

        # Serialize complex fields to JSON
        data_row = {
            'proposal_id': proposal.proposal_id,
            'agent_name': proposal.agent_name,
            'proposal_type': proposal.proposal_type.value,
            'title': proposal.title,
            'explanation': proposal.explanation,
            'inputs_used': json.dumps(proposal.inputs_used),
            'constraints': json.dumps(proposal.constraints),
            'data': json.dumps(proposal.data),
            'requires_approval': json.dumps(proposal.requires_approval),
            'approvals': json.dumps(proposal.approvals),
            'approval_reasons': json.dumps(proposal.approval_reasons),
            'status': proposal.status.value,
            'created_at': proposal.created_at.isoformat(),
            'expires_at': proposal.expires_at.isoformat() if proposal.expires_at else None,
            'executed_at': proposal.executed_at.isoformat() if proposal.executed_at else None,
            'bundle_id': proposal.bundle_id,
        }

        await db.execute("""
            INSERT OR REPLACE INTO proposals (
                proposal_id, agent_name, proposal_type, title, explanation,
                inputs_used, constraints, data, requires_approval, approvals,
                approval_reasons, status, created_at, expires_at, executed_at, bundle_id
            ) VALUES (
                :proposal_id, :agent_name, :proposal_type, :title, :explanation,
                :inputs_used, :constraints, :data, :requires_approval, :approvals,
                :approval_reasons, :status, :created_at, :expires_at, :executed_at, :bundle_id
            )
        """, data_row)

        await db.commit()
        logger.debug(f"Saved proposal {proposal.proposal_id} to database")

    @staticmethod
    async def get_by_id(proposal_id: str) -> Optional[Proposal]:
        """
        Get a proposal by ID.

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal or None if not found
        """
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM proposals WHERE proposal_id = ?",
            (proposal_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return ProposalRepository._row_to_proposal(row)

    @staticmethod
    async def list_all(filter: Optional[ProposalFilter] = None) -> List[Proposal]:
        """
        List all proposals, optionally filtered.

        Args:
            filter: Optional filter criteria

        Returns:
            List of proposals
        """
        db = await get_db()

        # Build query based on filter
        query = "SELECT * FROM proposals"
        params = []
        where_clauses = []

        if filter:
            if filter.agent_name:
                where_clauses.append("agent_name = ?")
                params.append(filter.agent_name)

            if filter.proposal_type:
                where_clauses.append("proposal_type = ?")
                params.append(filter.proposal_type.value)

            if filter.status:
                where_clauses.append("status = ?")
                params.append(filter.status.value)

            if filter.created_after:
                where_clauses.append("created_at >= ?")
                params.append(filter.created_after.isoformat())

            if filter.created_before:
                where_clauses.append("created_at <= ?")
                params.append(filter.created_before.isoformat())

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY created_at DESC"

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        proposals = [ProposalRepository._row_to_proposal(row) for row in rows]

        # Apply user_id filter (needs to check JSON field)
        if filter and filter.user_id:
            proposals = [
                p for p in proposals
                if filter.user_id in p.requires_approval
            ]

        return proposals

    @staticmethod
    async def delete(proposal_id: str) -> bool:
        """
        Delete a proposal.

        Args:
            proposal_id: Proposal ID

        Returns:
            True if deleted, False if not found
        """
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM proposals WHERE proposal_id = ?",
            (proposal_id,)
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def count_by_status(status: ProposalStatus) -> int:
        """
        Count proposals by status.

        Args:
            status: Proposal status

        Returns:
            Count of proposals with that status
        """
        db = await get_db()
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM proposals WHERE status = ?",
            (status.value,)
        )
        row = await cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    def _row_to_proposal(row: aiosqlite.Row) -> Proposal:
        """
        Convert database row to Proposal object.

        Args:
            row: Database row

        Returns:
            Proposal object
        """
        return Proposal(
            proposal_id=row['proposal_id'],
            agent_name=row['agent_name'],
            proposal_type=ProposalType(row['proposal_type']),
            title=row['title'],
            explanation=row['explanation'],
            inputs_used=json.loads(row['inputs_used']),
            constraints=json.loads(row['constraints']),
            data=json.loads(row['data']),
            requires_approval=json.loads(row['requires_approval']),
            approvals=json.loads(row['approvals']),
            approval_reasons=json.loads(row['approval_reasons']),
            status=ProposalStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
            executed_at=datetime.fromisoformat(row['executed_at']) if row['executed_at'] else None,
            bundle_id=row['bundle_id'],
        )
