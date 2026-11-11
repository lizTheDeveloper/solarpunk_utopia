"""Unit tests for the local-first familiar workflow kernel (stdlib + pytest)."""
import asyncio
import tempfile
from pathlib import Path

import pytest
from app.agents.familiar_runtime import FamiliarStore, run_one

@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as d:
        yield FamiliarStore(Path(d) / "familiar.sqlite")

def test_independent_step_progresses_while_other_waits(store):
    pid=store.create_plan("ranch","Garden research",[
        {"id":"read","title":"Research soil","tool":"research"},
        {"id":"buy","title":"Order seeds","tool":"purchase","approval_for":"steward"},
        {"id":"write","title":"Write guide","tool":"document","depends_on":["read"]},
    ])
    first=store.claim("worker-a")
    assert first["id"]=="read"
    store.finish("read","worker-a",{"ok":True})
    second=store.claim("worker-a")
    assert second["id"]=="write"  # purchase approval cannot block independent work
    store.finish("write","worker-a",{"ok":True})
    assert store.claim("worker-a") is None
    assert next(s for s in store.get_plan(pid)["steps"] if s["id"]=="buy")["status"]=="waiting_approval"
    approvals=store.approvals_for("steward")
    assert len(approvals)==1
    with pytest.raises(PermissionError):
        store.decide(approvals[0]["id"],"stranger",True)
    store.decide(approvals[0]["id"],"steward",True)
    assert store.claim("worker-a")["id"]=="buy"
    store.finish("buy","worker-a",{"receipt":"example"})
    assert store.get_plan(pid)["plan"]["status"]=="completed"

def test_reject_and_cancel_block_execution(store):
    pid=store.create_plan("ranch","Test",[{"id":"a","title":"Spend","tool":"purchase","approval_for":"steward"}])
    approval=store.approvals_for("steward")[0]
    assert store.claim("w") is None
    store.decide(approval["id"],"steward",False)
    assert store.claim("w") is None
    store.cancel_plan(pid)
    assert store.get_plan(pid)["plan"]["status"]=="canceled"

def test_cycles_and_unknown_dependencies_rejected(store):
    with pytest.raises(ValueError):
        store.create_plan("ranch","Cycle",[
            {"id":"a","title":"A","tool":"read","depends_on":["b"]},
            {"id":"b","title":"B","tool":"read","depends_on":["a"]},
        ])
    with pytest.raises(ValueError):
        store.create_plan("ranch","Missing",[{"id":"a","title":"A","tool":"read","depends_on":["missing"]}])

def test_lease_recovery(store):
    store.create_plan("ranch","Recovery",[{"id":"a","title":"A","tool":"read"}])
    assert store.claim("dead-worker", lease_seconds=-1)["id"]=="a"
    recovered=store.claim("new-worker")
    assert recovered["id"]=="a"
    with pytest.raises(ValueError):
        store.finish("a","dead-worker",{})
    store.finish("a","new-worker",{})

def test_run_one_with_registry(store):
    pid=store.create_plan("ranch","Draft",[{"id":"one","title":"Read","tool":"read","args":{"plant":"kale"}}])
    async def read(plant):
        return {"crop":plant,"source":"example"}
    assert asyncio.run(run_one(store,"w",{"read":read}))
    assert store.get_plan(pid)["plan"]["status"]=="completed"
    assert len(store.audit(pid))>=3
