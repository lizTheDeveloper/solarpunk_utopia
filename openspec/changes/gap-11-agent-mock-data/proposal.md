# GAP-11: Replace Remaining Agent Mock Data

**Status**: ✅ IMPLEMENTED
**Priority**: P2 - Core Experience
**Estimated Effort**: 4-6 hours
**Assigned**: Completed

## Problem Statement

5 of 7 agents now use live VF database, but 2 still return hardcoded mock data:
- Work Party Scheduler: `_get_available_participants()`
- Permaculture Planner: `_get_active_goals()`, `_suggest_guilds()`

## Current Reality

**Completed** (Session 2):
- ✅ Mutual Aid Matchmaker
- ✅ Perishables Dispatcher
- ✅ Inventory Agent
- ✅ Work Party Scheduler (plans only)
- ✅ Education Pathfinder

**Remaining**:
- ⚠️ Work Party Scheduler: participant availability (needs VF Commitments)
- ⚠️ Permaculture Planner: goals and guild suggestions (needs LLM + VF Goals)

## Required Implementation

1. VFClient MUST add `get_commitments()` method
2. Work Party Scheduler MUST query real availability via commitments
3. Permaculture Planner MUST query VF Goals
4. Permaculture Planner MUST integrate LLM for guild suggestions

## Files to Modify

- `app/clients/vf_client.py` - Add commitments query
- `app/agents/work_party_scheduler.py:151-198`
- `app/agents/permaculture_planner.py`

## Success Criteria

- [ ] All agents query live data
- [ ] No hardcoded mock responses
- [ ] Agent proposals reflect reality

**Reference**: `VISION_REALITY_DELTA.md:GAP-11`
