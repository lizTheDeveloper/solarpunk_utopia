"""Plan Repository - CRUD operations for Plans"""

import sqlite3
from datetime import datetime
import json
from ...models.vf.plan import Plan, PlanStatus
from .base_repo import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn, "plans", Plan)

    def create(self, plan: Plan) -> Plan:
        if plan.created_at is None:
            plan.created_at = datetime.now()

        query = """
            INSERT INTO plans
            (id, name, status, description, goal, start_date, end_date, process_ids, commitment_ids,
             dependencies, location_id, created_at, updated_at, author, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (plan.id, plan.name, plan.status.value, plan.description, plan.goal,
                 plan.start_date.isoformat() if plan.start_date else None,
                 plan.end_date.isoformat() if plan.end_date else None,
                 json.dumps(plan.process_ids) if plan.process_ids else "[]",
                 json.dumps(plan.commitment_ids) if plan.commitment_ids else "[]",
                 json.dumps([d.__dict__ for d in plan.dependencies]) if plan.dependencies else "[]",
                 plan.location_id, plan.created_at.isoformat(),
                 plan.updated_at.isoformat() if plan.updated_at else None,
                 plan.author, plan.signature)

        self._execute(query, params)
        self.conn.commit()
        return plan

    def update(self, plan: Plan) -> Plan:
        plan.updated_at = datetime.now()
        query = "UPDATE plans SET status = ?, updated_at = ? WHERE id = ?"
        params = (plan.status.value, plan.updated_at.isoformat(), plan.id)
        self._execute(query, params)
        self.conn.commit()
        return plan
