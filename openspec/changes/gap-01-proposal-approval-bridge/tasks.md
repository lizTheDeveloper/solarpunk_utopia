# Tasks: GAP-01 Proposal Approval → VF Bridge

## Phase 1: Extend Approval Framework (1 hour)

### Task 1.1: Add execute_proposal() method to ApprovalTracker
**File**: `app/agents/framework/approval.py`
**Estimated**: 30 minutes

```python
async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
    """
    Execute an approved proposal by creating corresponding VF objects.

    Returns:
        Dict with created VF object IDs or error details
    """
    # 1. Retrieve proposal from database
    # 2. Verify it's fully approved
    # 3. Call appropriate executor based on proposal type
    # 4. Update proposal status to "executed"
    # 5. Return created VF object references
```

**Acceptance criteria**:
- Method validates proposal is fully approved before executing
- Method delegates to type-specific executors
- Method updates proposal status atomically
- Method returns structured result with VF object IDs

### Task 1.2: Create MutualAidExecutor class
**File**: `app/agents/executors/mutual_aid_executor.py` (new file)
**Estimated**: 30 minutes

```python
class MutualAidExecutor:
    """Executes mutual aid match proposals by creating VF Match + Exchange"""

    def __init__(self, vf_client: VFClient):
        self.vf_client = vf_client

    async def execute(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Create VF Match and Exchange for approved match proposal.

        Returns:
            {
                "vf_match_id": "...",
                "vf_exchange_id": "...",
                "status": "executed"
            }
        """
        # 1. Extract offer_id, need_id from proposal data
        # 2. Create VF Match
        # 3. Create VF Exchange
        # 4. Handle rollback on errors
```

**Acceptance criteria**:
- Creates VF Match with correct offer/need linkage
- Creates VF Exchange with correct provider/receiver
- Implements transaction rollback on partial failure
- Returns structured result with created IDs

## Phase 2: Integrate with Approval Endpoint (30 minutes)

### Task 2.1: Update approve_proposal endpoint
**File**: `app/api/agents.py:130-152`
**Estimated**: 30 minutes

**Changes**:
```python
@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    approval_data: ApprovalData,
    tracker: ApprovalTracker = Depends(get_approval_tracker)
):
    # Existing approval recording...
    result = await tracker.approve_proposal(proposal_id, approval_data)

    # NEW: Check if fully approved and execute
    if result.get("all_approved"):
        execution_result = await tracker.execute_proposal(proposal_id)
        result["execution"] = execution_result

    return result
```

**Acceptance criteria**:
- Endpoint records approval (existing behavior preserved)
- Endpoint automatically executes if all approvals are in
- Endpoint returns execution results in response
- Endpoint handles execution errors gracefully

## Phase 3: Error Handling & Rollback (30 minutes)

### Task 3.1: Implement transaction rollback
**File**: `app/agents/executors/mutual_aid_executor.py`
**Estimated**: 20 minutes

**Logic**:
```python
try:
    match = await self.vf_client.create_match(...)
    try:
        exchange = await self.vf_client.create_exchange(...)
        return {"success": True, "vf_match_id": match.id, ...}
    except Exception as e:
        # Rollback: delete the match
        await self.vf_client.delete_match(match.id)
        raise
except Exception as e:
    logger.error(f"Execution failed: {e}")
    return {"success": False, "error": str(e)}
```

**Acceptance criteria**:
- VF Match is deleted if Exchange creation fails
- Proposal status is NOT updated to "executed" on errors
- Detailed error context is logged
- Error response includes actionable message

### Task 3.2: Add execution audit logging
**File**: `app/agents/framework/approval.py`
**Estimated**: 10 minutes

**Add**:
- Log when execution starts
- Log created VF object IDs
- Log execution failures with full stack trace
- Include proposal ID, agent type, and approval timestamps

## Phase 4: Testing (30-45 minutes)

### Task 4.1: Integration test - happy path
**File**: `tests/integration/test_proposal_execution.py` (new)
**Estimated**: 15 minutes

```python
async def test_mutual_aid_proposal_execution():
    # 1. Create offer and need via VF API
    # 2. Run mutual-aid-matchmaker agent
    # 3. Get proposal ID from agent response
    # 4. Approve as user 1
    # 5. Approve as user 2
    # 6. Verify VF Match created
    # 7. Verify VF Exchange created
    # 8. Verify proposal status is "executed"
```

### Task 4.2: Integration test - error handling
**File**: Same as above
**Estimated**: 15 minutes

```python
async def test_proposal_execution_rollback():
    # Mock VF Exchange creation to fail
    # Verify Match is rolled back
    # Verify proposal status remains "pending"
    # Verify approvals are preserved
```

### Task 4.3: Unit test - partial approvals
**File**: `tests/unit/test_approval_tracker.py`
**Estimated**: 15 minutes

```python
async def test_execution_waits_for_all_approvals():
    # Approve with 2 out of 3 users
    # Verify execute_proposal is NOT called
    # Approve with 3rd user
    # Verify execute_proposal IS called
```

## Phase 5: Documentation (15 minutes)

### Task 5.1: Update API documentation
**File**: `docs/API.md` or inline docstrings
**Estimated**: 10 minutes

- Document new response fields in `/proposals/{id}/approve`
- Document execution field in response
- Document possible error codes

### Task 5.2: Add logging documentation
**File**: Code comments or `docs/LOGGING.md`
**Estimated**: 5 minutes

- Document what events are logged during execution
- Document log levels (INFO for success, ERROR for failures)

## Verification Checklist

Before marking this as complete:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual test: Create offer → Create need → Run agent → Approve × 2 → See exchange in UI
- [ ] Manual test: Trigger execution error → Verify rollback → Verify proposal still pending
- [ ] Code review: Check error handling comprehensiveness
- [ ] Code review: Check transaction atomicity
- [ ] Logs contain sufficient debug information
- [ ] No new lint errors or warnings

## Estimated Total Time

- Phase 1: 1 hour
- Phase 2: 30 minutes
- Phase 3: 30 minutes
- Phase 4: 45 minutes
- Phase 5: 15 minutes

**Total: ~3 hours**

## Dependencies

- VFClient must have `create_match()` and `create_exchange()` methods
- VFClient should have `delete_match()` for rollback
- Database must support async operations
- Tests require test database setup
