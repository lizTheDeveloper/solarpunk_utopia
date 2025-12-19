# Tasks: GAP-42 Authentication System

## Note: Addressed by GAP-02

**This gap is fully addressed by implementing GAP-02 (User Identity System).**

See: `openspec/changes/gap-02-user-identity-system/tasks.md`

## Additional Cleanup Tasks (After GAP-02)

### Task 1: Remove user_id query parameters
**Estimated**: 1 hour

Find and remove all instances:

```bash
# Find all user_id query params
grep -r "user_id.*Query" app/ valueflows_node/

# Remove from endpoint signatures
# Before:
@router.get("/proposals")
async def get_proposals(user_id: str = Query(...)):
    ...

# After:
@router.get("/proposals")
async def get_proposals(request: Request):
    user_id = request.state.user.id
    ...
```

### Task 2: Add 401/403 error handling
**Estimated**: 30 minutes

```python
# Centralized error responses
from fastapi import HTTPException

def require_auth(request: Request) -> User:
    """Ensure user is authenticated"""
    if not hasattr(request.state, 'user') or not request.state.user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return request.state.user

def require_ownership(resource_owner_id: str, current_user: User):
    """Ensure user owns the resource"""
    if resource_owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this resource"
        )
```

### Task 3: Update frontend to remove hardcoded user_id
**Estimated**: 30 minutes

```typescript
// Before
const createOffer = async (data: OfferCreate) => {
  return api.post('/vf/listings/', {
    ...data,
    agent_id: 'demo-user'  // ❌ Hardcoded
  });
};

// After (user_id from auth context, set by backend)
const createOffer = async (data: OfferCreate) => {
  return api.post('/vf/listings/', data);  // ✅ Backend sets agent_id from session
};
```

### Task 4: Security audit
**Estimated**: 1 hour

- [ ] Verify no user_id query params remain
- [ ] Verify all protected endpoints require auth
- [ ] Test impersonation attempts fail
- [ ] Verify error messages don't leak info

## Verification

- [ ] GAP-02 implementation complete
- [ ] All query params removed
- [ ] Frontend uses auth context
- [ ] Security audit passes
- [ ] Penetration testing shows no auth bypass

**Total: 3 hours (after GAP-02 complete)**
