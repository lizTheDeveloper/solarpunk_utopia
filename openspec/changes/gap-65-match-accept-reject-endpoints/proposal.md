# GAP-65: Missing Match Accept/Reject Endpoints

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Frontend/Backend API Mismatch
**Source**: VISION_REALITY_DELTA.md Gap #65

## Problem Statement

Frontend code expects `/matches/{id}/accept` and `/matches/{id}/reject` endpoints, but the backend only provides `/matches/{match_id}/approve` with a different signature requiring an `agent_id` parameter.

**Impact**:
- Match acceptance/rejection is completely non-functional
- Demo blocker - core economic matching feature doesn't work
- Frontend makes requests to non-existent endpoints (404 errors)

**Evidence**:
```typescript
// Frontend: frontend/src/api/valueflows.ts:137-145
acceptMatch: async (id: string): Promise<Match> => {
  const response = await api.post<Match>(`/matches/${id}/accept`);
  return response.data;
}

rejectMatch: async (id: string): Promise<void> => {
  await api.post(`/matches/${id}/reject`);
}
```

```python
# Backend: valueflows_node/app/api/vf/matches.py:70
@router.patch("/{match_id}/approve", response_model=dict)
async def approve_match(match_id: str, agent_id: str):
    # Different name, different method, requires agent_id
```

## Requirements

### MUST

- Frontend and backend MUST have matching API endpoints for match operations
- Match acceptance MUST verify the user has permission to accept
- Match rejection MUST be allowed by either party (offerer or needers)
- API responses MUST return updated match status

### SHOULD

- Accept/reject operations SHOULD be idempotent
- Rejected matches SHOULD include optional rejection reason
- Matches SHOULD transition through proper states (pending → accepted/rejected)

## Proposed Solutions

### Option 1: Add Frontend-Compatible Endpoints (Recommended)

Add new endpoints matching frontend expectations:

```python
# valueflows_node/app/api/vf/matches.py

@router.post("/{match_id}/accept", response_model=Match)
async def accept_match(
    match_id: str,
    current_user: User = Depends(require_auth)
):
    """Accept a match between offer and need"""
    match = await match_repo.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Verify user is either the offerer or needer
    if current_user.id not in [match.offer.agent_id, match.need.agent_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    match.status = "accepted"
    match.accepted_by = current_user.id
    match.accepted_at = datetime.utcnow()

    await match_repo.update(match)
    return match

@router.post("/{match_id}/reject", response_model=Match)
async def reject_match(
    match_id: str,
    rejection: Optional[MatchRejection] = None,
    current_user: User = Depends(require_auth)
):
    """Reject a match"""
    match = await match_repo.get_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Verify user is either the offerer or needer
    if current_user.id not in [match.offer.agent_id, match.need.agent_id]:
        raise HTTPException(status_code=403, detail="Not authorized")

    match.status = "rejected"
    match.rejected_by = current_user.id
    match.rejected_at = datetime.utcnow()
    match.rejection_reason = rejection.reason if rejection else None

    await match_repo.update(match)
    return match
```

**Pros**:
- Matches frontend expectations exactly
- Clean REST semantics (POST for state change)
- Supports optional rejection reason

**Cons**:
- Need to migrate existing `/approve` endpoint users (if any)

### Option 2: Update Frontend to Use Existing Endpoint

Update frontend to use `/approve` endpoint:

```typescript
// frontend/src/api/valueflows.ts
acceptMatch: async (id: string, agentId: string): Promise<Match> => {
  const response = await api.patch<Match>(`/matches/${id}/approve`, { agent_id: agentId });
  return response.data;
}
```

**Pros**:
- No backend changes needed
- Uses existing endpoint

**Cons**:
- Frontend needs to pass agent_id (should come from auth context)
- No reject endpoint - would need to add
- PATCH is less semantic than POST for acceptance

## Recommended Implementation

**Use Option 1**: Add new `/accept` and `/reject` endpoints to match frontend expectations.

**Implementation Steps**:

1. Add `MatchRejection` model for optional rejection data:
   ```python
   class MatchRejection(BaseModel):
       reason: Optional[str] = None
   ```

2. Add `accept_match` endpoint (POST `/matches/{id}/accept`)
3. Add `reject_match` endpoint (POST `/matches/{id}/reject`)
4. Add auth middleware to verify user permissions
5. Update match status properly (pending → accepted/rejected)
6. Add tests for both endpoints
7. Consider deprecating old `/approve` endpoint if unused

## Test Scenarios

### WHEN a user accepts a match they are part of
THEN the match status MUST change to "accepted"
AND the accepted_by field MUST be set to the user's ID
AND the accepted_at timestamp MUST be recorded

### WHEN a user tries to accept a match they're not part of
THEN the request MUST return 403 Forbidden
AND the match status MUST NOT change

### WHEN a user rejects a match with a reason
THEN the match status MUST change to "rejected"
AND the rejection_reason MUST be stored
AND the rejected_by and rejected_at fields MUST be set

### WHEN a user tries to accept an already-accepted match
THEN the request SHOULD be idempotent and return the existing match
OR return 409 Conflict with clear message

## Files to Modify

- `valueflows_node/app/api/vf/matches.py` - Add new endpoints
- `valueflows_node/app/models/match.py` - Add status fields if missing
- `valueflows_node/app/repositories/match_repo.py` - Add update methods
- `valueflows_node/tests/test_matches.py` - Add comprehensive tests

## Related Gaps

- GAP-71: Delete listing has no ownership verification (same auth pattern needed)
- GAP-02: User identity system (auth dependency used here)
