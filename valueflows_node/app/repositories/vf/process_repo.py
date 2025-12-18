"""Process Repository - CRUD operations for Processes"""

import sqlite3
from datetime import datetime
import json
from ...models.vf.process import Process, ProcessStatus
from .base_repo import BaseRepository


class ProcessRepository(BaseRepository[Process]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "processes", Process)

    def create(self, process: Process) -> Process:
        if process.created_at is None:
            process.created_at = datetime.now()

        query = """
            INSERT INTO processes
            (id, name, status, protocol_id, description, location_id, planned_start, planned_end,
             actual_start, actual_end, inputs, outputs, participant_ids, plan_id, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (process.id, process.name, process.status.value, process.protocol_id, process.description,
                 process.location_id,
                 process.planned_start.isoformat() if process.planned_start else None,
                 process.planned_end.isoformat() if process.planned_end else None,
                 process.actual_start.isoformat() if process.actual_start else None,
                 process.actual_end.isoformat() if process.actual_end else None,
                 json.dumps([i.__dict__ for i in process.inputs]) if process.inputs else "[]",
                 json.dumps([o.__dict__ for o in process.outputs]) if process.outputs else "[]",
                 json.dumps(process.participant_ids) if process.participant_ids else "[]",
                 process.plan_id, process.created_at.isoformat(),
                 process.updated_at.isoformat() if process.updated_at else None,
                 process.author, process.signature)

        self._execute(query, params)
        self.conn.commit()
        return process

    def update(self, process: Process) -> Process:
        process.updated_at = datetime.now()
        query = "UPDATE processes SET status = ?, actual_start = ?, actual_end = ?, updated_at = ? WHERE id = ?"
        params = (process.status.value,
                 process.actual_start.isoformat() if process.actual_start else None,
                 process.actual_end.isoformat() if process.actual_end else None,
                 process.updated_at.isoformat(), process.id)
        self._execute(query, params)
        self.conn.commit()
        return process
