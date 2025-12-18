"""Commitment Repository - CRUD operations for Commitments"""

import sqlite3
from datetime import datetime
from typing import List
from ...models.vf.commitment import Commitment, CommitmentStatus
from .base_repo import BaseRepository


class CommitmentRepository(BaseRepository[Commitment]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "commitments", Commitment)

    def create(self, commitment: Commitment) -> Commitment:
        if commitment.created_at is None:
            commitment.created_at = datetime.now()

        query = """
            INSERT INTO commitments
            (id, agent_id, action, resource_spec_id, quantity, unit, due_date, status, exchange_id,
             process_id, plan_id, fulfilled_by_event_id, note, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (commitment.id, commitment.agent_id, commitment.action, commitment.resource_spec_id,
                 commitment.quantity, commitment.unit,
                 commitment.due_date.isoformat() if commitment.due_date else None,
                 commitment.status.value, commitment.exchange_id, commitment.process_id, commitment.plan_id,
                 commitment.fulfilled_by_event_id, commitment.note, commitment.created_at.isoformat(),
                 commitment.updated_at.isoformat() if commitment.updated_at else None,
                 commitment.author, commitment.signature)

        self._execute(query, params)
        self.conn.commit()
        return commitment

    def update(self, commitment: Commitment) -> Commitment:
        commitment.updated_at = datetime.now()
        query = "UPDATE commitments SET status = ?, fulfilled_by_event_id = ?, updated_at = ? WHERE id = ?"
        params = (commitment.status.value, commitment.fulfilled_by_event_id, commitment.updated_at.isoformat(), commitment.id)
        self._execute(query, params)
        self.conn.commit()
        return commitment

    def find_by_agent(self, agent_id: str, status: CommitmentStatus = None) -> List[Commitment]:
        query = "SELECT * FROM commitments WHERE agent_id = ?"
        params = [agent_id]
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY due_date"
        rows = self._fetch_all(query, tuple(params))
        return [Commitment.from_dict(row) for row in rows]
