# GAP-66: Agent Stats Return Mock Data

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Mock Data in Production
**Source**: VISION_REALITY_DELTA.md Gap #66

## Problem Statement

The agent stats endpoint (`GET /api/agents/stats`) returns hardcoded mock values instead of real statistics from actual agent executions. This makes the AI agent system appear non-functional and breaks monitoring/debugging.

**Impact**:
- Cannot monitor agent activity
- No visibility into which agents are running or failing
- Proposal counts always show 0
- Last run time always shows None
- Demo blocker - agents appear broken even when working

**Evidence**:
```python
# app/api/agents.py:331-352
# TODO: Return actual stats from running agents
# For now, return mock stats
stats = {}
for name in agents:
    stats[name] = AgentStatsResponse(
        stats={
            "agent_name": name,
            "enabled": True if name != "inventory-agent" else False,
            "last_run": None,      # Always None!
            "proposals_created": 0, # Always 0!
        }
    )
```

## Requirements

### MUST

- Agent stats MUST reflect actual agent execution history
- Stats MUST include: last_run timestamp, proposals_created count, success/failure counts
- Stats MUST be persisted across server restarts
- Stats MUST update when agents actually run

### SHOULD

- Stats SHOULD include execution duration metrics
- Stats SHOULD track proposal approval/rejection rates
- Stats SHOULD include error counts and last error message
- Historical stats SHOULD be queryable (last 24h, 7d, 30d)

### MAY

- Stats MAY include resource usage (CPU, memory)
- Stats MAY include agent-specific metrics (matches found, resources scheduled, etc.)

## Proposed Solution

### 1. Create Agent Execution Log Table

```python
# app/models/agent_execution.py
class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str  # "running", "success", "failed"
    error_message: Optional[str] = None
    proposals_created: int = 0
    resources_processed: int = 0
    metadata: dict = Field(default_factory=dict)
```

### 2. Update Agent Stats Endpoint

```python
# app/api/agents.py
@router.get("/stats", response_model=Dict[str, AgentStatsResponse])
async def get_agent_stats(db: Session = Depends(get_db)):
    """Get real agent statistics from execution logs"""

    stats = {}
    for agent_name in agents:
        # Get most recent execution
        last_execution = db.query(AgentExecution)\
            .filter(AgentExecution.agent_name == agent_name)\
            .order_by(AgentExecution.started_at.desc())\
            .first()

        # Count total proposals created (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        total_proposals = db.query(func.sum(AgentExecution.proposals_created))\
            .filter(
                AgentExecution.agent_name == agent_name,
                AgentExecution.started_at >= thirty_days_ago
            )\
            .scalar() or 0

        # Count successes and failures
        success_count = db.query(func.count())\
            .filter(
                AgentExecution.agent_name == agent_name,
                AgentExecution.status == "success",
                AgentExecution.started_at >= thirty_days_ago
            )\
            .scalar()

        failure_count = db.query(func.count())\
            .filter(
                AgentExecution.agent_name == agent_name,
                AgentExecution.status == "failed",
                AgentExecution.started_at >= thirty_days_ago
            )\
            .scalar()

        stats[agent_name] = AgentStatsResponse(
            stats={
                "agent_name": agent_name,
                "enabled": True,  # TODO: Get from agent settings
                "last_run": last_execution.started_at if last_execution else None,
                "last_status": last_execution.status if last_execution else None,
                "last_duration_ms": last_execution.duration_ms if last_execution else None,
                "proposals_created_30d": total_proposals,
                "success_count_30d": success_count,
                "failure_count_30d": failure_count,
                "last_error": last_execution.error_message if last_execution and last_execution.status == "failed" else None,
            }
        )

    return stats
```

### 3. Log Agent Executions

```python
# app/agents/framework/base_agent.py
async def execute(self, context: dict) -> dict:
    """Execute agent with execution logging"""

    execution = AgentExecution(
        agent_name=self.agent_name,
        started_at=datetime.utcnow(),
        status="running"
    )
    db.add(execution)
    db.commit()

    try:
        result = await self._execute_internal(context)

        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        execution.status = "success"
        execution.proposals_created = len(result.get("proposals", []))
        execution.resources_processed = len(result.get("resources_processed", []))
        execution.metadata = result.get("metadata", {})

        db.commit()
        return result

    except Exception as e:
        execution.completed_at = datetime.utcnow()
        execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)
        execution.status = "failed"
        execution.error_message = str(e)
        db.commit()
        raise
```

## Implementation Steps

1. Create `agent_executions` database table
2. Add `AgentExecution` model
3. Update `base_agent.execute()` to log executions
4. Update `GET /api/agents/stats` to query real data
5. Add database migration
6. Add indices on `agent_name` and `started_at` for query performance
7. Add cleanup job to archive old execution logs (>90 days)

## Test Scenarios

### WHEN an agent successfully executes
THEN a new execution record MUST be created
AND the execution status MUST be "success"
AND the duration MUST be recorded
AND proposals_created MUST reflect actual proposals

### WHEN an agent fails during execution
THEN the execution status MUST be "failed"
AND the error_message MUST contain the exception details
AND the record MUST still be persisted

### WHEN stats are requested
THEN last_run MUST show the most recent execution timestamp
AND proposals_created_30d MUST sum all proposals from last 30 days
AND success/failure counts MUST be accurate

### WHEN no executions exist for an agent
THEN last_run MUST be None
AND all counts MUST be 0
AND no errors should occur

## Database Schema

```sql
CREATE TABLE agent_executions (
    id VARCHAR(36) PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    proposals_created INTEGER DEFAULT 0,
    resources_processed INTEGER DEFAULT 0,
    metadata JSON,
    INDEX idx_agent_started (agent_name, started_at DESC)
);
```

## Files to Modify

- `app/models/agent_execution.py` - New model
- `app/api/agents.py` - Update stats endpoint
- `app/agents/framework/base_agent.py` - Add execution logging
- `app/database/migrations/` - Add migration
- `app/api/agents.py` - Update AgentStatsResponse model
- `tests/test_agent_stats.py` - Add comprehensive tests

## Related Gaps

- GAP-67: Agent settings not persisted (similar persistence pattern)
- GAP-68: Base agent database queries return empty (agents need to actually work)
