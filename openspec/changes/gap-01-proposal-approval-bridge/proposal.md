# GAP-01: Agent Proposal Approval → VF Bridge

**Status**: Implemented
**Priority**: P1 - Critical (Demo Blocker)
**Estimated Effort**: 2-3 hours
**Assigned**: Claude Agent 1
**Completed**: December 19, 2025

## Problem Statement

WHEN Alice and Bob both approve a mutual aid match proposal created by an agent, the approval is recorded in memory but NOTHING happens in the ValueFlows system. The proposal just sits there "approved" with no follow-through.

This breaks the entire demo flow: match suggestions are useless if they don't actually connect people.

## Current Reality

**Location**: `app/api/agents.py:130-152` (approve_proposal endpoint)

The approval endpoint:
1. Records the approval in ApprovalTracker
2. Checks if all parties have approved
3. Returns success
4. **Does nothing else**

No VF Match is created. No VF Exchange is created. The proposal status remains "pending" forever.

## Implementation Summary

**Implemented in**: `app/services/proposal_executor.py`

The `_execute_match_proposal()` method now:
1. ✅ Creates a VF Match linking the offer and need
2. ✅ Fetches listing details to get provider_id, receiver_id, and resource_spec_id
3. ✅ Creates a VF Exchange with all required fields
4. ✅ Implements atomic rollback: if Exchange creation fails, the Match is deleted
5. ✅ Returns both match_id and exchange_id in the execution result
6. ✅ Logs all operations for audit trail

**Key Changes**:
- Enhanced `_execute_match_proposal()` to query listings and create Exchange after Match
- Added try/except block to rollback Match if Exchange creation fails
- Proper error handling and logging throughout
- Integration with existing approval flow (no changes needed to `/proposals/{id}/approve` endpoint)

The approval flow now works end-to-end:
```
Proposal Created → Both Parties Approve → Match Created → Exchange Created → Proposal Marked Executed
```

## Required Implementation

The system SHALL implement the following when a proposal receives all required approvals:

### MUST Requirements

1. The system MUST create a VF Match object via `POST /vf/matches/` linking the matched parties
2. The system MUST create a VF Exchange object via `POST /vf/exchanges/` with the transfer details
3. The system MUST update the proposal status to "executed"
4. The system MUST handle errors gracefully if VF API calls fail
5. The system MUST maintain atomic transaction semantics (all-or-nothing execution)

### SHOULD Requirements

1. The system SHOULD trigger notifications to both parties about the created exchange
2. The system SHOULD log the execution for audit purposes
3. The system SHOULD include the proposal ID in the VF Match metadata

## Scenarios

### WHEN both parties approve a mutual aid match proposal

**GIVEN**:
- A proposal from mutual-aid-matchmaker agent
- Alice offers tomatoes, Bob needs tomatoes
- Proposal requires approval from both alice_id and bob_id

**WHEN**:
1. Alice calls `POST /agents/proposals/{id}/approve` with `approved: true`
2. Bob calls `POST /agents/proposals/{id}/approve` with `approved: true`

**THEN**:
1. A VF Match MUST be created with:
   - `offer_id`: Alice's offer
   - `need_id`: Bob's need
   - `status`: "matched"
2. A VF Exchange MUST be created with:
   - Provider: Alice
   - Receiver: Bob
   - Resource: tomatoes
   - Status: "planned"
3. Proposal status MUST be updated to "executed"
4. Both API calls MUST return 200 with the created VF object IDs

### WHEN approval execution fails partway through

**GIVEN**:
- Proposal is fully approved
- VF Match creation succeeds
- VF Exchange creation fails (network error, validation error, etc.)

**WHEN**: Execute proposal is called

**THEN**:
1. The VF Match MUST be rolled back (deleted)
2. The proposal status MUST remain "pending" (not "executed")
3. An error MUST be logged with full context
4. The approval records MUST be preserved (for retry)

### WHEN a proposal requires 3+ approvals

**GIVEN**:
- A work party proposal requires 5 participants
- 4 have approved so far

**WHEN**: The 4th person approves

**THEN**:
1. The approval MUST be recorded
2. No VF objects MUST be created yet
3. The response MUST indicate "waiting for 1 more approval"

**WHEN**: The 5th person approves

**THEN**:
1. VF objects MUST be created
2. All 5 participants MUST be linked to the created VF Commitment

## Files to Modify

### Backend
- `app/api/agents.py` - Extend `approve_proposal` endpoint to call executor
- `app/agents/framework/approval.py` - Add `execute_proposal()` method
- `app/services/proposal_executor.py` - May need updates for new proposal types

### Models
- `app/models/` - Ensure proposal status enum includes "executed"

## Testing Requirements

1. Integration test: full flow from proposal creation → dual approval → VF objects created
2. Error handling test: VF API failure during execution
3. Partial approval test: verify execution only happens when all approvals are in
4. Idempotency test: re-approving an already executed proposal should not duplicate VF objects

## Success Criteria

- [x] All tests pass
- [x] Demo flow works: agent creates proposal → users approve → exchange appears in /exchanges page
- [x] No data corruption on errors
- [x] Clear error messages if execution fails

## Dependencies

- GAP-05 (Proposal Persistence) - COMPLETE
- ValueFlows node API must be running
- Database must support transactions

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-01`
- Related code: `app/agents/mutual_aid_matchmaker.py`
- VF API: `valueflows_node/app/api/vf/matches.py`, `valueflows_node/app/api/vf/exchanges.py`
