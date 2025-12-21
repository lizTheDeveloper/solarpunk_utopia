# GAP-55: Frontend Agent List Empty

**Status:** ✅ Implemented
**Priority:** P3 - Bug Fix
**Effort:** 1-2 hours (Actual: 1 hour)

## Problem

Frontend shows empty agent list. Either API route wrong or data not loading.

## Investigation

1. Check API response:
   ```bash
   curl http://localhost:8000/api/agents
   ```

2. Check frontend fetch:
   ```typescript
   // Does this URL match the backend?
   const response = await fetch('/api/agents');
   ```

3. Check backend route:
   ```python
   @router.get("/agents")
   async def list_agents():
       # Is this returning data?
       return agents
   ```

## Likely Issues

1. **Route mismatch**: Frontend calls `/agents`, backend serves `/api/agents`
2. **Empty response**: Backend returns `[]` due to error handling
3. **CORS**: API blocked by browser
4. **Auth**: Endpoint requires auth, frontend not sending token

## Tasks

1. Debug API response
2. Check route paths match
3. Verify data exists
4. Fix whatever's broken

## Solution Implemented

**Root Cause:** Backend endpoint `/api/agents` returned only agent names (strings), but frontend expected full Agent objects with metadata.

**Fix:**
1. Enhanced backend endpoint (`app/api/agents.py:558-634`) to:
   - Fetch agent settings from AgentSettingsRepository
   - Fetch agent stats from AgentStatsRepository
   - Return full agent objects with: id, type, name, description, enabled, opt_in, last_run, config
2. Updated frontend API client (`frontend/src/api/agents.ts:17-21`) to:
   - Actually use the response data instead of returning empty array
   - Remove TODO comment

**Files Changed:**
- `app/api/agents.py` - Enhanced `list_agents()` endpoint
- `frontend/src/api/agents.ts` - Fixed `getAgents()` to return actual data

## Success Criteria

- [x] Agent list renders in frontend
- [x] API returns actual agent data with full metadata
- [x] Settings and stats integrated from repositories
