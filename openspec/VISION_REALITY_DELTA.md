# Vision Reality Delta

**Autonomous Gap Analysis Report**
**Generated**: 2025-12-19
**Analyzer**: Claude Autonomous Gap Analysis Agent

This document identifies gaps between what the codebase claims to implement and what actually works. Each gap includes severity, location, and recommended fix.

---

## Executive Summary

**Total Gaps Found**: 34 (8 CRITICAL, 12 HIGH, 10 MEDIUM, 4 LOW)

### Critical Issues (Demo Blockers)
1. Frontend calls endpoints that don't exist (`/matches/{id}/accept`, `/matches/{id}/reject`)
2. Agent stats and settings return hardcoded mock data
3. Base agent `query_vf_data` always returns empty list (TODO in code)
4. No `/vf/commitments` endpoint exists but frontend expects it
5. LLM integration returns mock responses by default
6. Auth delete listing has no ownership verification (TODO in code)

### Key Patterns Found
- 26 TODO comments indicating incomplete implementation
- Multiple `return []` patterns masking missing functionality
- Frontend/backend API mismatches
- Tests may pass but functionality doesn't actually work

---

## Priority 1: CRITICAL (Demo Blockers)

### GAP-65: Missing `/matches/{id}/accept` and `/matches/{id}/reject` Endpoints
**Severity**: CRITICAL
**Location**: `frontend/src/api/valueflows.ts:137-145`, `valueflows_node/app/api/vf/matches.py`
**Claimed**: Frontend can accept/reject matches via POST to `/matches/{id}/accept|reject`
**Reality**: These endpoints don't exist. Backend has `/matches/{match_id}/approve` with different signature.
**Evidence**:
```typescript
// Frontend calls this (valueflows.ts:137-145):
acceptMatch: async (id: string): Promise<Match> => {
  const response = await api.post<Match>(`/matches/${id}/accept`);
  ...
}
```
```python
# Backend has this instead (matches.py:70):
@router.patch("/{match_id}/approve", response_model=dict)
async def approve_match(match_id: str, agent_id: str):  # Requires agent_id!
```
**Fix**: Either add `/accept` and `/reject` endpoints to backend, or update frontend to use `/approve` with correct parameters.

---

### GAP-66: Agent Stats Return Mock Data
**Severity**: CRITICAL
**Location**: `app/api/agents.py:324-392`
**Claimed**: Agent stats endpoint returns real statistics
**Reality**: Returns hardcoded mock values (`proposals_created: 0`, `last_run: None`)
**Evidence**:
```python
# agents.py:331-352
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
**Fix**: Track actual agent runs and proposal counts in database/memory.

---

### GAP-67: Agent Settings Not Persisted
**Severity**: CRITICAL
**Location**: `app/api/agents.py:218-321`
**Claimed**: Agent settings can be saved and loaded
**Reality**: Settings are never persisted - PUT returns the request, GET returns defaults
**Evidence**:
```python
# agents.py:225, 256, 291
# TODO: Load from database/config file
# For now, return default configs
# ...
# TODO: Save to database/config file
# For now, just return the requested settings
```
**Fix**: Add database tables for agent settings and implement persistence.

---

### GAP-68: Base Agent Database Queries Return Empty
**Severity**: CRITICAL
**Location**: `app/agents/framework/base_agent.py:180-201`
**Claimed**: Agents can query VF data via `query_vf_data()`
**Reality**: Always returns empty list when no db_client
**Evidence**:
```python
# base_agent.py:193-201
async def query_vf_data(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
    if not self.db_client:
        logger.warning(f"No database client configured for {self.agent_name}")
        return []  # Always empty!

    try:
        # TODO: Implement actual DB query once DB client is available
        # For now, return empty list
        return []  # Always empty even with db_client!
```
**Fix**: Implement actual database queries using the VFClient that exists.

---

### GAP-69: No `/vf/commitments` Endpoint
**Severity**: CRITICAL
**Location**: `frontend/src/api/valueflows.ts:148-156`, `valueflows_node/app/api/vf/`
**Claimed**: Frontend can fetch/manage commitments
**Reality**: No commitments.py endpoint exists in backend
**Evidence**:
```typescript
// Frontend expects (valueflows.ts:148-156):
getCommitments: async (): Promise<Commitment[]> => {
  const response = await api.get<Commitment[]>('/commitments');
  ...
}
```
No corresponding file: `valueflows_node/app/api/vf/commitments.py` doesn't exist
**Fix**: Create commitments API endpoint or remove frontend calls.

---

### GAP-70: LLM Integration Uses Mock by Default
**Severity**: CRITICAL
**Location**: `app/llm/backends.py:421-453`
**Claimed**: LLM backends (Ollama, MLX, Remote) provide AI reasoning
**Reality**: Falls back to MockBackend which returns `"Mock response to: ..."`
**Evidence**:
```python
# backends.py:446-453
def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    ...
    else:
        logger.warning(
            f"Unknown backend '{backend}', falling back to mock. "
            ...
        )
        return MockBackend(config)  # Default!
```
**Fix**: Document LLM setup requirements, ensure proper backend selection.

---

### GAP-71: Delete Listing Has No Ownership Verification
**Severity**: CRITICAL
**Location**: `valueflows_node/app/api/vf/listings.py:213-249`
**Claimed**: Only owners can delete their listings
**Reality**: Anyone can delete any listing
**Evidence**:
```python
# listings.py:231-233
# TODO (GAP-02): Add ownership verification when auth is implemented
# if listing.agent_id != request.state.user.id:
#     raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
```
**Fix**: Implement auth check after GAP-02 user identity system is complete.

---

### GAP-72: Proposal Approval Missing User ID on Reject Endpoint
**Severity**: CRITICAL
**Location**: `app/api/agents.py:194-215`
**Claimed**: Reject endpoint uses authenticated user
**Reality**: Uses `request.user_id` which doesn't exist in ApprovalRequest
**Evidence**:
```python
# agents.py:205
proposal = await approval_tracker.approve_proposal(
    proposal_id=proposal_id,
    user_id=request.user_id,  # ApprovalRequest has no user_id field!
    ...
)
```
**Fix**: Add user_id to ApprovalRequest or use auth dependency like approve endpoint.

---

## Priority 2: HIGH (Core Experience Gaps)

### GAP-73: Inventory Agent Queries Return Empty
**Location**: `app/agents/inventory_agent.py:247`
**Evidence**: `# TODO: Query actual VF Events (consume) for this resource`
**Fix**: Implement VF Events query via VFClient.

---

### GAP-74: Commons Router Cache State Unknown
**Location**: `app/agents/commons_router.py:83`
**Evidence**: `# TODO: Query actual cache state from database`
**Fix**: Integrate with cache database.

---

### GAP-75: Work Party Scheduler Availability Not Queried
**Location**: `app/agents/work_party_scheduler.py:161,385`
**Evidence**:
- `# TODO: Query actual participant availability from VF Commitments`
- `# TODO: Integrate with weather API`
**Fix**: Implement commitment queries and weather API integration.

---

### GAP-76: Education Pathfinder Skills Not Queried
**Location**: `app/agents/education_pathfinder.py:88,120`
**Evidence**:
- `# TODO: Query actual VF Commitments`
- `# TODO: Query actual user skills from database`
**Fix**: Implement VF Commitments and skills queries.

---

### GAP-77: Permaculture Planner LLM Not Called
**Location**: `app/agents/permaculture_planner.py:74,152`
**Evidence**:
- `# TODO: Query actual VF goals`
- `# TODO: Implement actual LLM call`
**Fix**: Implement LLM integration for planting recommendations.

---

### GAP-78: Proposal Executor Cache/Forwarding Services Not Integrated
**Location**: `app/services/proposal_executor.py:411,425,440`
**Evidence**:
- `# TODO: Integrate with CacheService` (2 instances)
- `# TODO: Integrate with ForwardingService`
**Fix**: Complete CacheService and ForwardingService integration.

---

### GAP-79: Mutual Aid Matchmaker Returns Empty When VFClient Fails
**Location**: `app/agents/mutual_aid_matchmaker.py:86-107`
**Evidence**: On VFClient error, silently returns `[]` instead of mock data or error
**Fix**: Add better error handling or ensure VFClient is always available.

---

### GAP-80: TTL Service Silently Catches Exceptions
**Location**: `app/services/ttl_service.py:59`
**Evidence**: `pass` in exception handler - errors silently ignored
**Fix**: Add logging or proper error handling.

---

### GAP-81: Forwarding Service Abstract Method
**Location**: `app/services/forwarding_service.py:23`
**Evidence**: `pass` - method body not implemented
**Fix**: Implement forwarding logic.

---

### GAP-82: Discovery Search LRU Eviction Not Implemented
**Location**: `discovery_search/services/cache_manager.py:169`
**Evidence**: `# TODO: Implement LRU eviction if needed`
**Fix**: Implement LRU cache eviction when cache full.

---

### GAP-83: Auth Cookie Not Secure in Production
**Location**: `app/api/auth.py:83`
**Evidence**: `secure=False,  # TODO: Set to True in production with HTTPS`
**Fix**: Use environment variable to enable secure cookies in production.

---

### GAP-84: File Chunking Downloads Not Listable
**Location**: `file_chunking/api/downloads.py:169`
**Evidence**: `# TODO: Implement list all downloads`
**Fix**: Implement download listing endpoint.

---

## Priority 3: MEDIUM (Polish & Integration)

### GAP-85: Perishables Dispatcher Returns Empty on DB Failure
**Location**: `app/agents/perishables_dispatcher.py:100`
**Evidence**: Returns `[]` on exception
**Fix**: Add proper error handling/logging.

---

### GAP-86: Library Cache Tags Not Retrieved
**Location**: `file_chunking/services/library_cache_service.py:247`
**Evidence**: `# TODO: Get tags from manifest`
**Fix**: Implement tag extraction from manifests.

---

### GAP-87: Bundle Processor Query Response Not Stored
**Location**: `discovery_search/bundle_processor.py:157`
**Evidence**: `# TODO: Store response for query initiator to retrieve`
**Fix**: Implement response storage mechanism.

---

### GAP-88: Listing Validation TODOs
**Location**: `valueflows_node/app/models/requests/listings.py:73,84`
**Evidence**:
- `# TODO (GAP-43 Phase 3): Add database validation` (2 instances)
**Fix**: Implement foreign key validation after GAP-43.

---

### GAP-89: Exchange Repository find_by_agent May Not Exist
**Location**: `valueflows_node/app/api/vf/exchanges.py:24`
**Evidence**: `if hasattr(exchange_repo, 'find_by_agent')` - conditional check
**Fix**: Ensure ExchangeRepository has find_by_agent method.

---

### GAP-90: Response Builder Empty Returns
**Location**: `discovery_search/services/response_builder.py:196,235`
**Evidence**: Multiple `return []` and `return {}` on errors
**Fix**: Add proper error handling instead of silent empty returns.

---

### GAP-91: Index Publisher Empty Return
**Location**: `discovery_search/services/index_publisher.py:281`
**Evidence**: `return {}` on error
**Fix**: Add error handling/logging.

---

### GAP-92: Chunk Publisher Returns Empty on Error
**Location**: `file_chunking/services/chunk_publisher_service.py:253`
**Evidence**: `return []` on exception
**Fix**: Add proper error handling.

---

### GAP-93: Reassembly Service Silent Failures
**Location**: `file_chunking/services/reassembly_service.py:176,192`
**Evidence**: Multiple `return []` patterns
**Fix**: Add error reporting.

---

### GAP-94: Download Model Returns Empty
**Location**: `file_chunking/models/download.py:153`
**Evidence**: `return []`
**Fix**: Review if this is intentional or error case.

---

## Priority 4: LOW (Minor Issues)

### GAP-95: Mesh Network Tests May Use Mocks
**Location**: `mesh_network/bridge_node/tests/test_*.py`
**Evidence**: Tests exist but may not test real network functionality
**Fix**: Review test coverage and add integration tests.

---

### GAP-96: Sync Orchestrator Empty Return
**Location**: `mesh_network/bridge_node/services/sync_orchestrator.py:296`
**Evidence**: `return []`
**Fix**: Review if intentional.

---

### GAP-97: Library Cache Silent Failures
**Location**: `file_chunking/services/library_cache_service.py:135,173`
**Evidence**: `return []` and `return {}` on errors
**Fix**: Add logging.

---

### GAP-98: Cache Manager Empty Return
**Location**: `discovery_search/services/cache_manager.py:197`
**Evidence**: `return {}`
**Fix**: Add proper error handling.

---

## Summary of Patterns

### Files with Most Issues
1. `app/api/agents.py` - 4 TODOs (settings, stats not persisted)
2. `app/agents/framework/base_agent.py` - 2 TODOs (db query, empty returns)
3. `app/services/proposal_executor.py` - 3 TODOs (service integration)
4. `app/agents/*.py` - Multiple agents with incomplete queries

### Common Anti-Patterns Found
1. **Silent `return []`**: 20+ instances where errors return empty instead of failing
2. **TODO comments**: 26 TODO/FIXME comments indicating known incomplete code
3. **Conditional checks for methods**: Code checks if methods exist (indicates unstable interfaces)
4. **Mock data fallbacks**: Several places return mock data without warning

### Frontend/Backend Mismatches
1. `/matches/{id}/accept` vs `/matches/{match_id}/approve`
2. `/commitments` endpoint missing entirely
3. Field name mismatches fixed by GAP-06 but pattern may recur

---

## Recommended Fix Order

### Week 1: Critical Demo Blockers
1. GAP-65: Add accept/reject match endpoints (30 min)
2. GAP-72: Fix reject endpoint user_id (15 min)
3. GAP-69: Add commitments endpoint or remove frontend calls (1 hour)
4. GAP-71: Add ownership check with current auth system (30 min)

### Week 2: Agent Functionality
5. GAP-68: Implement base agent VF queries using VFClient (2-3 hours)
6. GAP-66: Track real agent stats (2 hours)
7. GAP-67: Persist agent settings (2 hours)
8. GAP-70: Document LLM setup, verify backend selection (1 hour)

### Week 3: Complete Agent Integrations
9. GAP-73 through GAP-84: Agent TODOs (4-6 hours total)

### Ongoing: Error Handling
10. Replace silent `return []` with proper logging/errors

---

## Verification Commands

Test critical paths:
```bash
# Test match accept/reject (should fail until fixed)
curl -X POST http://localhost:8001/vf/matches/test-id/accept

# Test commitments endpoint (should 404 until fixed)
curl http://localhost:8001/vf/commitments

# Test agent stats (should show mock data)
curl http://localhost:8000/agents/stats

# Run integration tests
pytest tests/integration/test_end_to_end_gift_economy.py -v
```

---

---

## Session 2 Gaps (2025-12-19)

Additional gaps discovered during autonomous analysis session:

### GAP-99: VFClient Connection Not Closed in Agents
**Location**: `app/agents/mutual_aid_matchmaker.py:81-89, 99-107`
**Severity**: MEDIUM
**Evidence**: Creates VFClient but never closes connection; may leak DB connections
**Fix**: Use context manager or explicit close() in agent cleanup

### GAP-100: Frontend getAgents Returns Empty Array Intentionally
**Location**: `frontend/src/api/agents.ts:17-22`
**Severity**: MEDIUM
**Evidence**:
```typescript
getAgents: async (): Promise<Agent[]> => {
    // For now, return empty array - proper implementation needs agent list endpoint
    return [];
}
```
**Fix**: Implement transformation from backend `{agents: string[]}` to `Agent[]`

### GAP-101: WorkPartyScheduler Falls Back to Mock on ANY Exception
**Location**: `app/agents/work_party_scheduler.py:91-141`
**Severity**: HIGH
**Evidence**: Even database connection errors silently use mock work session data
**Fix**: Distinguish between "no data" vs "DB unavailable" errors

### GAP-102: PermaculturePlanner ALWAYS Uses Mock Goals
**Location**: `app/agents/permaculture_planner.py:67-93`
**Severity**: HIGH
**Evidence**: `_get_unplanned_goals()` has no VFClient integration attempt, always returns hardcoded data
**Fix**: Implement VFClient.get_goals() query

---

**Document Status**: Living document. Update as gaps are fixed.
**Last Updated**: 2025-12-19 (Session 2 autonomous analysis)
**Next Review**: After Workshop Sprint items complete.
