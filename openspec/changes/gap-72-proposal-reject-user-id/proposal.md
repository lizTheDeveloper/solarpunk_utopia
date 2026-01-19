# GAP-72: Proposal Approval Missing User ID on Reject Endpoint

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Code References Non-Existent Field
**Source**: VISION_REALITY_DELTA.md Gap #72

## Problem Statement

The reject proposal endpoint tries to access `request.user_id`, but the `ApprovalRequest` model has no `user_id` field. This causes a runtime error when anyone tries to reject an agent proposal, making the rejection feature completely broken.

**Impact**:
- Proposal rejection is completely non-functional
- Runtime error (AttributeError) when trying to reject
- Demo blocker - users cannot reject bad proposals
- Frontend shows rejection UI but backend crashes
- Inconsistent with approve endpoint which uses auth dependency correctly

**Evidence**:
```python
# app/api/agents.py:205
@router.post("/{proposal_id}/reject", response_model=dict)
async def reject_proposal(proposal_id: str, request: ApprovalRequest):
    proposal = await approval_tracker.approve_proposal(  # Wrong method name too!
        proposal_id=proposal_id,
        user_id=request.user_id,  # ApprovalRequest has no user_id field!
        approved=False,
        reason=request.reason
    )
    return {"status": "rejected", "proposal_id": proposal_id}

# Compare with approve endpoint (correct):
@router.post("/{proposal_id}/approve", response_model=dict)
async def approve_proposal(
    proposal_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(require_auth)  # Uses auth dependency!
):
    proposal = await approval_tracker.approve_proposal(
        proposal_id=proposal_id,
        user_id=current_user.id,  # Gets user from auth!
        approved=True,
        reason=request.reason
    )
```

**ApprovalRequest model**:
```python
class ApprovalRequest(BaseModel):
    reason: Optional[str] = None
    # NO user_id field!
```

## Requirements

### MUST

- Reject endpoint MUST use authentication dependency like approve endpoint
- Reject endpoint MUST get user_id from authenticated user (not request body)
- Both approve and reject MUST have consistent signatures
- Rejection MUST be audited with user ID and timestamp
- Unauthenticated rejection attempts MUST return 401

### SHOULD

- Rejection reason SHOULD be required (not optional)
- Approval/rejection SHOULD be idempotent
- Users SHOULD only be able to approve/reject proposals visible to them
- Notification SHOULD be sent to proposing agent when rejected

### MAY

- Rejection MAY allow attaching feedback for the agent
- Rejection MAY trigger agent learning/adjustment
- Bulk approve/reject MAY be supported for admins

## Root Cause

The endpoints were implemented at different times:
1. `approve` was fixed to use `require_auth` dependency (correct)
2. `reject` still has old broken code referencing non-existent field

## Proposed Solution

### 1. Fix Reject Endpoint Signature

```python
# app/api/agents.py
from app.auth import require_auth, User

@router.post("/{proposal_id}/reject", response_model=dict)
async def reject_proposal(
    proposal_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(require_auth)  # Add auth dependency!
):
    """Reject an agent proposal

    Args:
        proposal_id: ID of the proposal to reject
        request: Rejection details (reason)
        current_user: Authenticated user (from dependency)

    Returns:
        Dict with rejection status

    Raises:
        HTTPException: If proposal not found or user not authorized
    """

    # Verify proposal exists and user has permission
    proposal = await approval_tracker.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Call reject method (not approve with approved=False!)
    result = await approval_tracker.reject_proposal(
        proposal_id=proposal_id,
        user_id=current_user.id,  # Use authenticated user!
        reason=request.reason or "No reason provided"
    )

    # Notify the agent that proposed this
    await notify_proposal_rejected(proposal, rejected_by=current_user, reason=request.reason)

    return {
        "status": "rejected",
        "proposal_id": proposal_id,
        "rejected_by": current_user.id,
        "rejected_at": result.rejected_at.isoformat()
    }
```

### 2. Add Separate Reject Method to ApprovalTracker

```python
# app/agents/framework/approval_tracker.py
class ApprovalTracker:
    async def approve_proposal(
        self,
        proposal_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Proposal:
        """Approve a proposal"""

        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal.status = "approved"
        proposal.approved_by = user_id
        proposal.approved_at = datetime.utcnow()
        proposal.approval_reason = reason

        await self.save_proposal(proposal)
        return proposal

    async def reject_proposal(
        self,
        proposal_id: str,
        user_id: str,
        reason: str
    ) -> Proposal:
        """Reject a proposal

        Args:
            proposal_id: Proposal to reject
            user_id: User rejecting the proposal
            reason: Why the proposal was rejected (required for learning)

        Returns:
            Updated proposal with rejection details
        """

        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        # Check proposal is still pending
        if proposal.status != "pending":
            raise ValueError(
                f"Cannot reject proposal with status '{proposal.status}'. "
                f"Only pending proposals can be rejected."
            )

        proposal.status = "rejected"
        proposal.rejected_by = user_id
        proposal.rejected_at = datetime.utcnow()
        proposal.rejection_reason = reason

        await self.save_proposal(proposal)

        # Log for agent learning
        await self.log_rejection(proposal, user_id, reason)

        return proposal

    async def log_rejection(self, proposal: Proposal, user_id: str, reason: str):
        """Log rejection for agent learning and analytics"""

        log = ProposalRejectionLog(
            proposal_id=proposal.id,
            agent_name=proposal.agent_name,
            rejected_by=user_id,
            reason=reason,
            proposal_type=proposal.title,
            timestamp=datetime.utcnow()
        )

        self.db.add(log)
        self.db.commit()

        # Could trigger agent feedback/learning here
        logger.info(
            f"Proposal {proposal.id} from {proposal.agent_name} rejected by {user_id}. "
            f"Reason: {reason}"
        )
```

### 3. Update Proposal Model

```python
# app/models/proposal.py
class Proposal(Base):
    __tablename__ = "agent_proposals"

    id: str
    agent_name: str
    title: str
    description: Optional[str]
    status: str  # "pending", "approved", "rejected"
    priority: str

    # Approval fields
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None

    # Rejection fields
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None  # Should be required

    created_at: datetime
    updated_at: datetime
```

### 4. Make Rejection Reason Required

```python
# app/models/approval_request.py
class ApprovalRequest(BaseModel):
    reason: str  # Required! (was Optional)

    @validator('reason')
    def reason_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Rejection reason is required and cannot be empty")
        if len(v) < 10:
            raise ValueError("Rejection reason must be at least 10 characters (provide meaningful feedback)")
        return v.strip()
```

### 5. Add Notification System

```python
# app/notifications/proposal_notifications.py
async def notify_proposal_rejected(
    proposal: Proposal,
    rejected_by: User,
    reason: Optional[str]
):
    """Notify agent owner that proposal was rejected"""

    notification = {
        "type": "proposal_rejected",
        "proposal_id": proposal.id,
        "agent_name": proposal.agent_name,
        "rejected_by": rejected_by.name,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Could send via:
    # - NATS pub/sub
    # - WebSocket to frontend
    # - Email if configured
    # - Matrix message

    logger.info(f"Notifying proposal rejection: {notification}")
```

## Test Scenarios

### WHEN an authenticated user rejects a proposal with a reason
THEN the proposal status MUST change to "rejected"
AND the rejected_by field MUST be set to the user's ID
AND the rejection_reason MUST be stored
AND a notification MUST be sent to the agent

### WHEN an unauthenticated user tries to reject a proposal
THEN the request MUST return 401 Unauthorized
AND the proposal status MUST NOT change

### WHEN a user tries to reject a proposal without a reason
THEN the request MUST return 422 Unprocessable Entity
AND the error MUST explain that reason is required

### WHEN a user tries to reject an already-approved proposal
THEN the request MUST return 409 Conflict
AND the error MUST explain that only pending proposals can be rejected

### WHEN approval and reject endpoints are called
THEN both MUST require authentication
AND both MUST audit the action with user ID
AND both MUST have consistent behavior

## Implementation Steps

1. Add `require_auth` dependency to reject endpoint
2. Change `user_id=request.user_id` to `user_id=current_user.id`
3. Create separate `reject_proposal()` method in ApprovalTracker
4. Add rejection fields to Proposal model if missing
5. Make rejection `reason` required (not optional)
6. Add `ProposalRejectionLog` model for analytics
7. Implement `notify_proposal_rejected()` function
8. Add comprehensive tests for both approve and reject
9. Update frontend to handle required reason field
10. Add rejection analytics to agent dashboard

## Database Migration

```sql
-- Add rejection fields if missing
ALTER TABLE agent_proposals
ADD COLUMN IF NOT EXISTS rejected_by VARCHAR(36),
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Create rejection log for agent learning
CREATE TABLE proposal_rejection_logs (
    id VARCHAR(36) PRIMARY KEY,
    proposal_id VARCHAR(36) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    rejected_by VARCHAR(36) NOT NULL,
    reason TEXT NOT NULL,
    proposal_type VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES agent_proposals(id),
    INDEX idx_agent (agent_name),
    INDEX idx_timestamp (timestamp)
);
```

## Files to Modify

- `app/api/agents.py` - Fix reject endpoint signature
- `app/agents/framework/approval_tracker.py` - Add reject_proposal method
- `app/models/proposal.py` - Add rejection fields
- `app/models/approval_request.py` - Make reason required
- `app/notifications/proposal_notifications.py` - New notification system
- `app/database/migrations/` - Add migration
- `tests/test_proposal_approval.py` - Test both endpoints

## Frontend Changes Needed

The frontend must be updated to require rejection reason:

```typescript
// frontend/src/components/ProposalApprovalModal.tsx
const handleReject = async () => {
  if (!rejectReason.trim()) {
    toast.error('Please provide a reason for rejection');  // Already has this!
    return;
  }

  // Minimum length check
  if (rejectReason.length < 10) {
    toast.error('Please provide a more detailed reason (at least 10 characters)');
    return;
  }

  await onReject(proposal.id, rejectReason);
  // ... rest of the code
};
```

## Related Gaps

- GAP-65: Match accept/reject (similar auth pattern)
- GAP-71: Delete listing auth (same auth dependency pattern)
- Agent learning system (uses rejection logs)

## Comparison: Before vs After

**Before (Broken)**:
```python
async def reject_proposal(proposal_id: str, request: ApprovalRequest):
    user_id=request.user_id,  # ❌ Doesn't exist!
```

**After (Fixed)**:
```python
async def reject_proposal(
    proposal_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(require_auth)  # ✅ Proper auth!
):
    user_id=current_user.id,  # ✅ From auth context!
```
