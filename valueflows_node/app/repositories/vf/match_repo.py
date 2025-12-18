"""Match Repository - CRUD operations for Matches"""

from typing import List
import sqlite3
from datetime import datetime
from ...models.vf.match import Match, MatchStatus
from .base_repo import BaseRepository


class MatchRepository(BaseRepository[Match]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "matches", Match)

    def create(self, match: Match) -> Match:
        if match.created_at is None:
            match.created_at = datetime.now()

        query = """
            INSERT INTO matches
            (id, offer_id, need_id, provider_id, receiver_id, status, provider_approved, receiver_approved,
             provider_approved_at, receiver_approved_at, match_score, match_reason, proposed_quantity,
             proposed_unit, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (match.id, match.offer_id, match.need_id, match.provider_id, match.receiver_id, match.status.value,
                 1 if match.provider_approved else 0, 1 if match.receiver_approved else 0,
                 match.provider_approved_at.isoformat() if match.provider_approved_at else None,
                 match.receiver_approved_at.isoformat() if match.receiver_approved_at else None,
                 match.match_score, match.match_reason, match.proposed_quantity, match.proposed_unit,
                 match.created_at.isoformat(), match.updated_at.isoformat() if match.updated_at else None,
                 match.author, match.signature)

        self._execute(query, params)
        self.conn.commit()
        return match

    def update(self, match: Match) -> Match:
        match.updated_at = datetime.now()
        query = """
            UPDATE matches SET status = ?, provider_approved = ?, receiver_approved = ?,
                             provider_approved_at = ?, receiver_approved_at = ?, updated_at = ? WHERE id = ?
        """
        params = (match.status.value, 1 if match.provider_approved else 0, 1 if match.receiver_approved else 0,
                 match.provider_approved_at.isoformat() if match.provider_approved_at else None,
                 match.receiver_approved_at.isoformat() if match.receiver_approved_at else None,
                 match.updated_at.isoformat(), match.id)
        self._execute(query, params)
        self.conn.commit()
        return match

    def find_by_agent(self, agent_id: str, status: MatchStatus = None) -> List[Match]:
        query = "SELECT * FROM matches WHERE (provider_id = ? OR receiver_id = ?)"
        params = [agent_id, agent_id]
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC"
        rows = self._fetch_all(query, tuple(params))
        return [Match.from_dict(row) for row in rows]
