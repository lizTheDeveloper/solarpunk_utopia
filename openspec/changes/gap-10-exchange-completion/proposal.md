# GAP-10: Exchange Completion Flow

**Status**: Draft
**Priority**: P2 - Core Experience
**Estimated Effort**: 3-4 hours
**Assigned**: Unclaimed

## Problem Statement

Alice and Bob meet, exchange tomatoes, but have no way to mark the exchange complete in the app. Backend has `/vf/exchanges/{id}/complete` endpoint but no frontend UI.

## Current Reality

Backend endpoint exists, frontend UI missing. Exchange flow feels incomplete.

## Required Implementation

1. Frontend MUST show "My Upcoming Exchanges" list
2. Frontend MUST show "Mark as Complete" button for each party
3. Frontend MUST call completion endpoint
4. Frontend MUST show completion confirmation
5. Completed exchanges MUST move to "Past Exchanges" section

## Files to Modify

- `frontend/src/pages/ExchangesPage.tsx` - Add completion UI
- `frontend/src/hooks/useExchanges.ts` - Add complete mutation
- `frontend/src/api/valueflows.ts` - Add completeExchange method

## Success Criteria

- [ ] Users can mark exchanges complete
- [ ] Both parties can confirm
- [ ] UI shows completion status
- [ ] Celebration/confirmation shown

**Reference**: `VISION_REALITY_DELTA.md:GAP-10`
