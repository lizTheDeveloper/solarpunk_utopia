# Tasks: GAP-09 Notification System

## MVP Implementation (2-3 hours)

### Task 1: Add pending count endpoint
**File**: `app/api/agents.py`
**Estimated**: 30 minutes

```python
@router.get("/proposals/pending-count")
async def get_pending_count(
    request: Request,
    tracker: ApprovalTracker = Depends(get_approval_tracker)
):
    """Get count of proposals pending current user's approval"""
    user_id = request.state.user.id
    count = await tracker.get_pending_count_for_user(user_id)
    return {"count": count}
```

### Task 2: Display badge on navigation
**File**: `frontend/src/components/Navigation.tsx`
**Estimated**: 1 hour

```typescript
const { data: pendingCount } = useQuery(
  ['pending-proposals'],
  () => getPendingProposalCount(),
  { refetchInterval: 30000 } // Poll every 30s
);

// In nav items
{pendingCount > 0 && (
  <span className="badge">{pendingCount}</span>
)}
```

### Task 3: Homepage proposal card
**File**: `frontend/src/pages/HomePage.tsx`
**Estimated**: 1 hour

Show prominent card if proposals pending.

**Total: 2.5 hours**
