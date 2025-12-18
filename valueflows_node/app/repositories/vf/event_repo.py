"""Event Repository - CRUD operations for Events"""

import sqlite3
from datetime import datetime
from typing import List
from ...models.vf.event import Event, EventAction
from .base_repo import BaseRepository


class EventRepository(BaseRepository[Event]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "events", Event)

    def create(self, event: Event) -> Event:
        if event.created_at is None:
            event.created_at = datetime.now()
        if event.occurred_at is None:
            event.occurred_at = datetime.now()

        query = """
            INSERT INTO events
            (id, action, resource_spec_id, resource_instance_id, quantity, unit, agent_id, to_agent_id,
             from_agent_id, location_id, occurred_at, process_id, exchange_id, commitment_id, note,
             image_url, created_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (event.id, event.action.value, event.resource_spec_id, event.resource_instance_id,
                 event.quantity, event.unit, event.agent_id, event.to_agent_id, event.from_agent_id,
                 event.location_id, event.occurred_at.isoformat(), event.process_id, event.exchange_id,
                 event.commitment_id, event.note, event.image_url, event.created_at.isoformat(),
                 event.author, event.signature)

        self._execute(query, params)
        self.conn.commit()
        return event

    def find_by_exchange(self, exchange_id: str) -> List[Event]:
        query = "SELECT * FROM events WHERE exchange_id = ? ORDER BY occurred_at"
        rows = self._fetch_all(query, (exchange_id,))
        return [Event.from_dict(row) for row in rows]

    def find_by_resource_instance(self, instance_id: str) -> List[Event]:
        """Get provenance chain for a resource instance"""
        query = "SELECT * FROM events WHERE resource_instance_id = ? ORDER BY occurred_at"
        rows = self._fetch_all(query, (instance_id,))
        return [Event.from_dict(row) for row in rows]
