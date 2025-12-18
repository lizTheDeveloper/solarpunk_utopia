"""ResourceInstance Repository - CRUD operations for ResourceInstances"""

from typing import List, Optional
import sqlite3
from datetime import datetime
from ...models.vf.resource_instance import ResourceInstance, ResourceState
from .base_repo import BaseRepository


class ResourceInstanceRepository(BaseRepository[ResourceInstance]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "resource_instances", ResourceInstance)

    def create(self, instance: ResourceInstance) -> ResourceInstance:
        if instance.created_at is None:
            instance.created_at = datetime.now()

        query = """
            INSERT INTO resource_instances
            (id, resource_spec_id, quantity, unit, state, current_location_id, label,
             description, image_url, expires_at, current_custodian_id, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (instance.id, instance.resource_spec_id, instance.quantity, instance.unit, instance.state.value,
                 instance.current_location_id, instance.label, instance.description, instance.image_url,
                 instance.expires_at.isoformat() if instance.expires_at else None, instance.current_custodian_id,
                 instance.created_at.isoformat(), instance.updated_at.isoformat() if instance.updated_at else None,
                 instance.author, instance.signature)

        self._execute(query, params)
        self.conn.commit()
        return instance

    def update(self, instance: ResourceInstance) -> ResourceInstance:
        instance.updated_at = datetime.now()
        query = """
            UPDATE resource_instances SET state = ?, current_location_id = ?, current_custodian_id = ?,
                                         quantity = ?, updated_at = ? WHERE id = ?
        """
        params = (instance.state.value, instance.current_location_id, instance.current_custodian_id,
                 instance.quantity, instance.updated_at.isoformat(), instance.id)
        self._execute(query, params)
        self.conn.commit()
        return instance

    def find_by_location(self, location_id: str, state: Optional[ResourceState] = None) -> List[ResourceInstance]:
        query = "SELECT * FROM resource_instances WHERE current_location_id = ?"
        params = [location_id]
        if state:
            query += " AND state = ?"
            params.append(state.value)
        rows = self._fetch_all(query, tuple(params))
        return [ResourceInstance.from_dict(row) for row in rows]

    def find_expiring(self, hours: int = 24) -> List[ResourceInstance]:
        from datetime import timedelta
        threshold = datetime.now() + timedelta(hours=hours)
        query = "SELECT * FROM resource_instances WHERE expires_at IS NOT NULL AND expires_at <= ? ORDER BY expires_at"
        rows = self._fetch_all(query, (threshold.isoformat(),))
        return [ResourceInstance.from_dict(row) for row in rows]
