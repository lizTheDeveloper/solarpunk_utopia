"""Exchange Repository - CRUD operations for Exchanges"""

from typing import List
import sqlite3
from datetime import datetime
from ...models.vf.exchange import Exchange, ExchangeStatus
from .base_repo import BaseRepository


class ExchangeRepository(BaseRepository[Exchange]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "exchanges", Exchange)

    def create(self, exchange: Exchange) -> Exchange:
        if exchange.created_at is None:
            exchange.created_at = datetime.now()

        query = """
            INSERT INTO exchanges
            (id, match_id, provider_id, receiver_id, resource_spec_id, quantity, unit, location_id,
             scheduled_start, scheduled_end, status, constraints, notes, provider_completed, receiver_completed,
             provider_event_id, receiver_event_id, provider_commitment_id, receiver_commitment_id,
             created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (exchange.id, exchange.match_id, exchange.provider_id, exchange.receiver_id,
                 exchange.resource_spec_id, exchange.quantity, exchange.unit, exchange.location_id,
                 exchange.scheduled_start.isoformat() if exchange.scheduled_start else None,
                 exchange.scheduled_end.isoformat() if exchange.scheduled_end else None,
                 exchange.status.value, exchange.constraints, exchange.notes,
                 1 if exchange.provider_completed else 0, 1 if exchange.receiver_completed else 0,
                 exchange.provider_event_id, exchange.receiver_event_id,
                 exchange.provider_commitment_id, exchange.receiver_commitment_id,
                 exchange.created_at.isoformat(), exchange.updated_at.isoformat() if exchange.updated_at else None,
                 exchange.author, exchange.signature)

        self._execute(query, params)
        self.conn.commit()
        return exchange

    def update(self, exchange: Exchange) -> Exchange:
        exchange.updated_at = datetime.now()
        query = """
            UPDATE exchanges SET status = ?, provider_completed = ?, receiver_completed = ?,
                               provider_event_id = ?, receiver_event_id = ?, updated_at = ? WHERE id = ?
        """
        params = (exchange.status.value, 1 if exchange.provider_completed else 0,
                 1 if exchange.receiver_completed else 0, exchange.provider_event_id,
                 exchange.receiver_event_id, exchange.updated_at.isoformat(), exchange.id)
        self._execute(query, params)
        self.conn.commit()
        return exchange

    def find_upcoming(self, agent_id: str = None) -> List[Exchange]:
        query = """
            SELECT * FROM exchanges WHERE status IN ('planned', 'in_progress')
            AND scheduled_start >= datetime('now')
        """
        params = []
        if agent_id:
            query += " AND (provider_id = ? OR receiver_id = ?)"
            params = [agent_id, agent_id]
        query += " ORDER BY scheduled_start"
        rows = self._fetch_all(query, tuple(params))
        return [Exchange.from_dict(row) for row in rows]
