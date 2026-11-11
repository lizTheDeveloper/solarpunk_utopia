"""Durable, single-node asynchronous workflow kernel for Community Familiar.

No model, credentials, messaging, or external write tools are connected by
default. Steps execute only through an explicit caller-supplied tool registry.
SQLite WAL enables reboot recovery and concurrent callers on one host.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS familiar_plans (
 id TEXT PRIMARY KEY, community_id TEXT NOT NULL, title TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active', created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS familiar_steps (
 id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES familiar_plans(id),
 title TEXT NOT NULL, tool TEXT NOT NULL, args_json TEXT NOT NULL,
 payload_hash TEXT NOT NULL, dependencies TEXT NOT NULL DEFAULT '[]',
 status TEXT NOT NULL DEFAULT 'queued', result_json TEXT,
 attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
 available_at REAL NOT NULL, lease_owner TEXT, lease_until REAL,
 requires_approval INTEGER NOT NULL DEFAULT 0,
 approved_by TEXT, failure TEXT, created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS familiar_steps_ready ON familiar_steps(status,available_at);
CREATE TABLE IF NOT EXISTS familiar_approvals (
 id TEXT PRIMARY KEY, step_id TEXT NOT NULL UNIQUE REFERENCES familiar_steps(id),
 community_id TEXT NOT NULL, approver_id TEXT NOT NULL,
 payload_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 decision_at REAL, expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS familiar_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
 plan_id TEXT, step_id TEXT, kind TEXT NOT NULL, details TEXT NOT NULL
);
"""

def _id():
    return uuid.uuid4().hex

def _digest(tool, args):
    return hashlib.sha256(json.dumps([tool, args], sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()

class FamiliarStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._tx() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _tx(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _event(db, kind, plan_id=None, step_id=None, details=None):
        db.execute("INSERT INTO familiar_events (at,plan_id,step_id,kind,details) VALUES (?,?,?,?,?)",
                   (time.time(), plan_id, step_id, kind, json.dumps(details or {})))

    def create_plan(self, community_id, title, steps):
        """Steps have keys id, title, tool, args, depends_on, approval_for.
        approval_for is a specific authorized user ID, never a role inferred
        by an LLM. IDs and dependencies must be unique and acyclic.
        """
        if not steps:
            raise ValueError("Plan must contain at least one step")
        ids = [s.get('id') or _id() for s in steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate step ID")
        edges = {i: set(s.get('depends_on', [])) for i, s in zip(ids, steps)}
        for i, deps in edges.items():
            if i in deps or not deps.issubset(edges):
                raise ValueError("Unknown or self-referencing dependency")
        visited, active = set(), set()
        def visit(i):
            if i in active:
                raise ValueError("Cyclic dependency")
            if i not in visited:
                active.add(i)
                for dep in edges[i]:
                    visit(dep)
                active.remove(i)
                visited.add(i)
        for i in ids:
            visit(i)
        plan_id = _id()
        now = time.time()
        with self._tx() as db:
            db.execute("INSERT INTO familiar_plans VALUES (?,?,?,?,?)",
                       (plan_id, community_id, title, 'active', now))
            for sid, s in zip(ids, steps):
                tool, args = s['tool'], s.get('args', {})
                reviewer = s.get('approval_for')
                db.execute("""INSERT INTO familiar_steps
                    (id,plan_id,title,tool,args_json,payload_hash,dependencies,
                     available_at,requires_approval,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (sid, plan_id, s['title'], tool, json.dumps(args), _digest(tool,args),
                     json.dumps(sorted(edges[sid])), now, int(bool(reviewer)), now))
                if reviewer:
                    db.execute("""INSERT INTO familiar_approvals
                        (id,step_id,community_id,approver_id,payload_hash,expires_at)
                        VALUES (?,?,?,?,?,?)""",
                        (_id(),sid,community_id,reviewer,_digest(tool,args),
                         now + s.get('approval_ttl_seconds',604800)))
            self._event(db, 'plan_created', plan_id)
        return plan_id

    def get_plan(self, plan_id):
        with self._tx() as db:
            plan = db.execute("SELECT * FROM familiar_plans WHERE id=?", (plan_id,)).fetchone()
            if not plan:
                return None
            steps = db.execute("SELECT * FROM familiar_steps WHERE plan_id=? ORDER BY created_at,id",
                               (plan_id,)).fetchall()
            return {"plan":dict(plan), "steps":[dict(s) for s in steps]}

    def approvals_for(self, user_id, community_id=None):
        with self._tx() as db:
            query = """SELECT a.*,s.title,s.tool,s.args_json,p.title AS plan_title
                       FROM familiar_approvals a
                       JOIN familiar_steps s ON a.step_id=s.id
                       JOIN familiar_plans p ON p.id=s.plan_id
                       WHERE a.approver_id=? AND a.status='pending'"""
            params = [user_id]
            if community_id:
                query += " AND a.community_id=?"
                params.append(community_id)
            return [dict(r) for r in db.execute(query,params).fetchall()]

    def decide(self, approval_id, actor_id, accepted):
        with self._tx() as db:
            row = db.execute("""SELECT a.*,s.payload_hash AS actual_hash,s.plan_id,
                        s.status AS step_status,p.status AS plan_status
                        FROM familiar_approvals a JOIN familiar_steps s ON s.id=a.step_id
                        JOIN familiar_plans p ON p.id=s.plan_id WHERE a.id=?""",
                        (approval_id,)).fetchone()
            if not row or row['approver_id'] != actor_id:
                raise PermissionError("Not an authorized approver")
            if row['status'] != 'pending' or row['expires_at'] <= time.time():
                raise ValueError("Approval no longer pending")
            if row['payload_hash'] != row['actual_hash']:
                raise ValueError("Payload changed since approval request")
            if row['plan_status'] != 'active' or row['step_status'] not in ('queued','waiting_approval'):
                raise ValueError("Step not available for approval")
            status = 'approved' if accepted else 'rejected'
            db.execute("UPDATE familiar_approvals SET status=?,decision_at=? WHERE id=?",
                       (status,time.time(),approval_id))
            db.execute("UPDATE familiar_steps SET status=?,approved_by=? WHERE id=?",
                       (('queued' if accepted else 'rejected'),
                        actor_id if accepted else None,row['step_id']))
            self._event(db,'approval_'+status,row['plan_id'],row['step_id'],{'actor':actor_id})
            return status

    def claim(self, worker_id, lease_seconds=60):
        """Claim one runnable step atomically; skip blocked approvals and DAG nodes."""
        now=time.time()
        with self._tx() as db:
            db.execute("""UPDATE familiar_steps SET status='queued',lease_owner=NULL,
                          lease_until=NULL WHERE status='running' AND lease_until < ?""",(now,))
            rows = db.execute("""SELECT s.* FROM familiar_steps s JOIN familiar_plans p
                           ON p.id=s.plan_id WHERE p.status='active'
                           AND s.status IN ('queued','waiting_approval')
                           AND s.available_at <= ? ORDER BY s.created_at LIMIT 100""",(now,)).fetchall()
            for row in rows:
                deps=json.loads(row['dependencies'])
                if deps:
                    statuses = {r['id']:r['status'] for r in db.execute(
                        "SELECT id,status FROM familiar_steps WHERE plan_id=?",(row['plan_id'],))}
                    if any(statuses.get(dep) in ('failed','rejected','canceled') for dep in deps):
                        db.execute("UPDATE familiar_steps SET status='canceled',failure='Dependency failed' WHERE id=?",(row['id'],))
                        continue
                    if not all(statuses.get(dep)=='succeeded' for dep in deps):
                        continue
                if row['requires_approval'] and not row['approved_by']:
                    db.execute("UPDATE familiar_steps SET status='waiting_approval' WHERE id=?",(row['id'],))
                    continue
                db.execute("""UPDATE familiar_steps SET status='running',lease_owner=?,
                      lease_until=?,attempts=attempts+1 WHERE id=?""",
                      (worker_id,now+lease_seconds,row['id']))
                self._event(db,'step_claimed',row['plan_id'],row['id'],{'worker':worker_id})
                return dict(db.execute("SELECT * FROM familiar_steps WHERE id=?",(row['id'],)).fetchone())
        return None

    def finish(self, step_id, worker_id, result=None, error=None):
        with self._tx() as db:
            row=db.execute("SELECT * FROM familiar_steps WHERE id=?",(step_id,)).fetchone()
            if not row or row['status']!='running' or row['lease_owner']!=worker_id:
                raise ValueError("Step not leased to this worker")
            if error:
                failed=row['attempts']>=row['max_attempts']
                status='failed' if failed else 'queued'
                delay=0 if failed else min(3600,2 ** min(row['attempts'],10))
                db.execute("""UPDATE familiar_steps SET status=?,failure=?,available_at=?,
                    lease_owner=NULL,lease_until=NULL WHERE id=?""",
                    (status,str(error)[:1000],time.time()+delay,step_id))
            else:
                status='succeeded'
                db.execute("""UPDATE familiar_steps SET status=?,result_json=?,
                    lease_owner=NULL,lease_until=NULL WHERE id=?""",
                    (status,json.dumps(result),step_id))
            self._event(db,'step_'+status,row['plan_id'],step_id,{'error':str(error) if error else None})
            states=[r[0] for r in db.execute("SELECT status FROM familiar_steps WHERE plan_id=?",(row['plan_id'],))]
            if all(s in ('succeeded','failed','rejected','canceled') for s in states):
                final='completed' if all(s=='succeeded' for s in states) else 'failed'
                db.execute("UPDATE familiar_plans SET status=? WHERE id=?",(final,row['plan_id']))
            return status

    def cancel_plan(self, plan_id):
        with self._tx() as db:
            db.execute("UPDATE familiar_plans SET status='canceled' WHERE id=? AND status='active'",(plan_id,))
            db.execute("""UPDATE familiar_steps SET status='canceled' WHERE plan_id=?
                       AND status NOT IN ('succeeded','failed','rejected','canceled')""",(plan_id,))
            db.execute("""UPDATE familiar_approvals SET status='revoked' WHERE status='pending'
                          AND step_id IN (SELECT id FROM familiar_steps WHERE plan_id=?)""",(plan_id,))
            self._event(db,'plan_canceled',plan_id)

    def audit(self, plan_id):
        with self._tx() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM familiar_events WHERE plan_id=? ORDER BY id",(plan_id,))]

async def run_one(store, worker_id, tools):
    """Execute one scoped tool. Only a trusted application supplies tool handlers.
    No irreversible external tools should be registered without an action ledger.
    """
    step=store.claim(worker_id)
    if not step:
        return False
    try:
        handler=tools[step['tool']]
        result=await handler(**json.loads(step['args_json']))
    except Exception as exc:
        store.finish(step['id'],worker_id,error=str(exc))
    else:
        store.finish(step['id'],worker_id,result=result)
    return True
