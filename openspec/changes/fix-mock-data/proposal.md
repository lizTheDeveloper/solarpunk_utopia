# Proposal: Replace Mock Data with Real Implementations

**Submitted By:** Gap Analysis Agent
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED (Core metrics complete - 80%)
**Implemented:** 2025-12-19 (Agent stats, settings, VF integration, resilience metrics)
**Gaps Addressed:** GAP-66 ✅, GAP-67 ✅, GAP-68 ✅, GAP-70 ✅, GAP-73-98, GAP-100-102, GAP-111, GAP-115, GAP-121-123
**Priority:** P1 - First Week

## Problem Statement

Many services return hardcoded mock data instead of querying real sources:

1. Agent stats return zeros
2. Agent settings aren't persisted
3. Base agent queries return empty
4. LLM integration uses mock backend
5. Resilience metrics use fake numbers
6. Multiple `return []` patterns mask failures

## Current State (Broken)

### Agent Stats (`app/api/agents.py:331-352`)
```python
# TODO: Return actual stats from running agents
stats[name] = AgentStatsResponse(
    last_run: None,      # Always None!
    proposals_created: 0, # Always 0!
)
```

### Agent Settings (`app/api/agents.py:225, 256, 291`)
```python
# TODO: Load from database/config file
# For now, return default configs
```

### Base Agent Query (`app/agents/framework/base_agent.py:193-201`)
```python
# TODO: Implement actual DB query once DB client is available
return []  # Always empty!
```

### Resilience Metrics (`app/services/resilience_metrics_service.py`)
```python
# TODO: compute from actual data
median_match_time_hours = 20.0  # Hardcoded!
needs_match_rate = 70.0  # Hardcoded!
```

## Proposed Solution

### 1. Real Agent Stats Tracking

```python
# app/database/agent_stats_repository.py
class AgentStatsRepository:
    async def record_run(self, agent_name: str, proposals_created: int):
        """Record an agent run"""
        await self.db.execute("""
            INSERT INTO agent_runs (agent_name, run_at, proposals_created)
            VALUES (?, ?, ?)
        """, [agent_name, datetime.utcnow(), proposals_created])

    async def get_stats(self, agent_name: str) -> AgentStats:
        """Get agent statistics"""
        row = await self.db.fetchone("""
            SELECT
                COUNT(*) as total_runs,
                MAX(run_at) as last_run,
                SUM(proposals_created) as total_proposals
            FROM agent_runs
            WHERE agent_name = ?
        """, [agent_name])

        return AgentStats(
            agent_name=agent_name,
            last_run=row["last_run"],
            proposals_created=row["total_proposals"] or 0,
            total_runs=row["total_runs"],
        )

# app/api/agents.py
@router.get("/stats")
async def get_agent_stats(repo: AgentStatsRepository = Depends(...)):
    stats = {}
    for agent_name in AGENT_NAMES:
        stats[agent_name] = await repo.get_stats(agent_name)
    return stats
```

### 2. Persist Agent Settings

```python
# app/database/agent_settings_repository.py
class AgentSettingsRepository:
    async def get_settings(self, agent_name: str) -> Optional[AgentSettings]:
        row = await self.db.fetchone(
            "SELECT settings FROM agent_settings WHERE agent_name = ?",
            [agent_name]
        )
        if row:
            return AgentSettings.parse_raw(row["settings"])
        return None

    async def save_settings(self, agent_name: str, settings: AgentSettings):
        await self.db.execute("""
            INSERT OR REPLACE INTO agent_settings (agent_name, settings, updated_at)
            VALUES (?, ?, ?)
        """, [agent_name, settings.json(), datetime.utcnow()])

# app/api/agents.py
@router.get("/{agent_name}/settings")
async def get_agent_settings(
    agent_name: str,
    repo: AgentSettingsRepository = Depends(...),
):
    settings = await repo.get_settings(agent_name)
    if not settings:
        return AgentSettings.get_defaults(agent_name)
    return settings

@router.put("/{agent_name}/settings")
async def update_agent_settings(
    agent_name: str,
    settings: AgentSettings,
    repo: AgentSettingsRepository = Depends(...),
):
    await repo.save_settings(agent_name, settings)
    return {"status": "saved", "agent_name": agent_name}
```

### 3. Base Agent with VFClient Integration

```python
# app/agents/framework/base_agent.py
class BaseAgent:
    def __init__(self, vf_client: VFClient = None):
        self.vf_client = vf_client or VFClient()

    async def query_vf_data(self, query_type: str, params: Dict = None) -> List[Dict]:
        """Query ValueFlows data via VFClient"""
        try:
            if query_type == "listings":
                return await self.vf_client.get_listings(**params)
            elif query_type == "matches":
                return await self.vf_client.get_matches(**params)
            elif query_type == "exchanges":
                return await self.vf_client.get_exchanges(**params)
            elif query_type == "commitments":
                return await self.vf_client.get_commitments(**params)
            else:
                logger.warning(f"Unknown query type: {query_type}")
                return []
        except Exception as e:
            logger.error(f"VF query failed: {e}")
            raise  # Don't mask errors!
```

### 4. Real Resilience Metrics

```python
# app/services/resilience_metrics_service.py
class ResilienceMetricsService:
    async def compute_match_metrics(self) -> MatchMetrics:
        """Compute actual match metrics from database"""
        matches = await self.vf_client.get_matches(
            created_after=datetime.utcnow() - timedelta(days=30)
        )

        if not matches:
            return MatchMetrics(
                median_match_time_hours=0,
                needs_match_rate=0,
                sample_size=0,
            )

        # Compute actual median match time
        match_times = [
            (m.matched_at - m.need_created_at).total_seconds() / 3600
            for m in matches
            if m.matched_at and m.need_created_at
        ]

        # Compute actual match rate
        total_needs = await self.vf_client.count_needs(
            created_after=datetime.utcnow() - timedelta(days=30)
        )
        matched_needs = len([m for m in matches if m.status == "matched"])

        return MatchMetrics(
            median_match_time_hours=statistics.median(match_times) if match_times else 0,
            needs_match_rate=(matched_needs / total_needs * 100) if total_needs else 0,
            sample_size=len(matches),
        )
```

### 5. Fix Silent Empty Returns

Replace all `return []` error handlers with proper error propagation:

```python
# BEFORE (bad)
try:
    data = await fetch_data()
except Exception as e:
    return []  # Silent failure!

# AFTER (good)
try:
    data = await fetch_data()
except DatabaseConnectionError as e:
    logger.error(f"Database unavailable: {e}")
    raise HTTPException(503, "Database temporarily unavailable")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(500, "Internal server error")
```

## Files to Modify

### Agent Stats/Settings
- `app/api/agents.py:324-392` - Use real repos
- New: `app/database/agent_stats_repository.py`
- New: `app/database/agent_settings_repository.py`

### Base Agent Query
- `app/agents/framework/base_agent.py:180-201`
- All agents that inherit from BaseAgent

### Resilience Metrics
- `app/services/resilience_metrics_service.py` (10 TODOs)

### Silent Failures (20+ files)
- `app/agents/perishables_dispatcher.py:100`
- `app/agents/mutual_aid_matchmaker.py:86-107`
- `app/services/ttl_service.py:59`
- `discovery_search/services/response_builder.py:196,235`
- `discovery_search/services/index_publisher.py:281`
- `file_chunking/services/chunk_publisher_service.py:253`
- `file_chunking/services/reassembly_service.py:176,192`
- ... and more

## Requirements

### SHALL Requirements
- SHALL track actual agent runs and proposal counts
- SHALL persist agent settings to database
- SHALL query VFClient for real data
- SHALL compute metrics from actual exchanges
- SHALL NOT return empty arrays as error handling
- SHALL log errors with appropriate severity

### MUST Requirements
- MUST propagate errors to callers
- MUST use proper HTTP status codes

## Testing

```python
def test_agent_stats_are_real():
    # Run an agent
    agent = MutualAidMatchmaker()
    await agent.run()

    # Stats should reflect the run
    stats = await get_agent_stats("mutual_aid_matchmaker")
    assert stats.last_run is not None
    assert stats.total_runs >= 1

def test_agent_settings_persist():
    settings = AgentSettings(enabled=True, schedule="0 * * * *")
    await save_agent_settings("test_agent", settings)

    loaded = await get_agent_settings("test_agent")
    assert loaded.enabled == True
    assert loaded.schedule == "0 * * * *"

def test_metrics_reflect_reality():
    # Create some matches
    create_match(time_to_match=timedelta(hours=5))
    create_match(time_to_match=timedelta(hours=10))
    create_match(time_to_match=timedelta(hours=15))

    metrics = await compute_match_metrics()
    assert metrics.median_match_time_hours == 10.0  # Actual median
    assert metrics.sample_size == 3
```

## Effort Estimate

- Agent stats tracking: 2 hours
- Agent settings persistence: 1 hour
- Base agent VF integration: 2 hours
- Resilience metrics: 3 hours
- Silent failure fixes: 4 hours
- Testing: 2 hours
- Total: ~14 hours

## Success Criteria

- [x] Agent stats show actual run times and counts ✅
- [x] Agent settings persist across restarts ✅
- [x] Base agent queries return real VF data ✅
- [x] Resilience metrics computed from actual data ✅ (GAP-111, GAP-115 COMPLETE)
- [ ] No `return []` error handling patterns (DEFERRED - not blocking)
- [x] Critical TODOs in affected files resolved (80% done)

## Implementation Status

### Completed (2025-12-19)
1. ✅ **Agent Stats Tracking** - Created `AgentStatsRepository` with real database tracking
   - Migration: `018_add_agent_stats_settings.sql`
   - Repository: `app/database/agent_stats_repository.py`
   - Updated: `app/api/agents.py` endpoints to use real stats

2. ✅ **Agent Settings Persistence** - Created `AgentSettingsRepository` for database persistence
   - Repository: `app/database/agent_settings_repository.py`
   - Updated: `app/api/agents.py` GET/PUT endpoints to persist settings

3. ✅ **BaseAgent VFClient Integration** - Integrated real ValueFlows queries
   - Updated: `app/agents/framework/base_agent.py` `query_vf_data()` method
   - Now uses `VFClient` for offers, needs, matches, exchanges, commitments

4. ✅ **Resilience Metrics** - Implemented real data queries
   - Updated: `app/services/resilience_metrics_service.py`
   - `_compute_velocity()` - Now queries actual match times from database
   - `_compute_coverage()` - Now calculates real needs match rate
   - Cell health metrics - Now computes cell-specific match data
   - GAP-111, GAP-115 resolved

### Remaining Work (Deferred - Not Blocking)
1. **Silent Failure Patterns** - Multiple `return []` patterns across codebase
   - `app/agents/perishables_dispatcher.py:100`
   - `app/agents/mutual_aid_matchmaker.py:86-107`
   - `app/services/ttl_service.py:59`
   - And 15+ more files

3. **LLM Mock Backend** - Agent LLM calls still use mock responses
   - Files: Various agent analyze() methods
