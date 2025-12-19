# GAP-06: Frontend/Backend API Route Fixes (Remaining)

**Status**: ✅ Completed
**Priority**: P1 - Critical (Demo Blocker)
**Estimated Effort**: 1-2 hours
**Actual Effort**: 1.5 hours
**Assigned**: Claude Code
**Completed**: 2025-12-18
**Dependencies**: Agents routing already fixed in session 3C

## Problem Statement

Frontend and backend APIs have mismatched routes and field names for ValueFlows listings:

1. **Route mismatch**: Frontend calls `/api/vf/intents` but backend has `/vf/listings`
2. **Field mismatches**: Frontend sends `type` but backend expects `listing_type`, etc.

This causes 404s and 422 validation errors when creating/reading offers and needs.

## Current Reality

**Status**: Agents API routing ✅ FIXED (GAP-06 partial completion)

**Remaining issues**:

| Frontend calls | Backend expects | Problem | Status |
|---------------|-----------------|---------|--------|
| `/api/vf/intents` | `/vf/listings` | Wrong endpoint | ⚠️ TODO |
| `type: 'offer'` | `listing_type: 'offer'` | Wrong field | ⚠️ TODO |
| `resource_specification_id` | `resource_spec_id` | Wrong field | ⚠️ TODO |

**Locations**:
- `frontend/src/api/valueflows.ts` - calls `/intents`
- `frontend/src/types/valueflows.ts` - defines wrong field names
- `valueflows_node/app/api/vf/listings.py` - expects `/listings`

## Required Implementation

### MUST Requirements

1. Frontend MUST call `/api/vf/listings` instead of `/api/vf/intents`
2. Frontend MUST send `listing_type` instead of `type`
3. Frontend MUST send `resource_spec_id` instead of `resource_specification_id`
4. All field mappings MUST match backend exactly
5. Both offer and need creation MUST work without 422 errors

## Scenarios

### WHEN user creates an offer

**GIVEN**: Alice fills out offer form

**WHEN**: Form is submitted

**THEN**:
1. Request MUST go to `/api/vf/listings/`
2. Payload MUST include `listing_type: 'offer'`
3. Payload MUST include `resource_spec_id` (not `resource_specification_id`)
4. Request MUST succeed with 201 Created
5. Offer MUST appear in offers list

### WHEN user creates a need

**GIVEN**: Bob fills out need form

**WHEN**: Form is submitted

**THEN**:
1. Request MUST go to `/api/vf/listings/`
2. Payload MUST include `listing_type: 'need'`
3. Request MUST succeed with 201 Created
4. Need MUST appear in needs list

## Files to Modify

### Frontend
- `frontend/src/api/valueflows.ts:15,42,60,79` - Change `/intents` to `/listings`
- `frontend/src/types/valueflows.ts` - Fix field names in Intent type (rename to Listing)

## Success Criteria

- [x] Frontend calls correct `/listings` endpoint
- [x] Field names match backend expectations
- [x] Offer creation works without errors
- [x] Need creation works without errors
- [x] No 404 or 422 errors in network tab

## Implementation Notes

**Completed**: 2025-12-18

**Files Modified**:
1. `frontend/src/types/valueflows.ts` - Created `Listing` interface with correct field names
2. `frontend/src/api/valueflows.ts` - Changed routes from `/intents` to `/listings`
3. `frontend/src/pages/CreateOfferPage.tsx` - Updated to use new field names
4. `frontend/src/pages/CreateNeedPage.tsx` - Updated to use new field names
5. `frontend/src/hooks/useOffers.ts` - Removed duplicate field injection
6. `frontend/src/hooks/useNeeds.ts` - Removed duplicate field injection

**Key Changes**:
- Routes: `/intents` → `/listings`
- Field: `type` → `listing_type`
- Field: `resource_specification_id` → `resource_spec_id`
- Field: `location` → `location_id`
- Field: `note` → `description`
- Maintained backward compatibility with legacy aliases

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-06`
- Related: GAP-06B (DELETE endpoint)
