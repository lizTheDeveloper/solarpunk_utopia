# Tasks: GAP-06 API Route Fixes (Remaining)

## Phase 1: Frontend API Client Updates (1 hour)

### Task 1.1: Update valueflows.ts routes
**File**: `frontend/src/api/valueflows.ts`
**Estimated**: 30 minutes

Find and replace:
- `/intents` → `/listings`

Update methods:
```typescript
// OLD
export const getIntents = async () => {
  const response = await api.get('/vf/intents');
  return response.data;
};

// NEW
export const getListings = async () => {
  const response = await api.get('/vf/listings');
  return response.data;
};

// OLD
export const createIntent = async (data: IntentCreate) => {
  const response = await api.post('/vf/intents', data);
  return response.data;
};

// NEW
export const createListing = async (data: ListingCreate) => {
  const response = await api.post('/vf/listings', data);
  return response.data;
};
```

### Task 1.2: Update type definitions
**File**: `frontend/src/types/valueflows.ts`
**Estimated**: 30 minutes

Fix field names:
```typescript
// OLD
export interface Intent {
  id: string;
  type: 'offer' | 'need';  // ❌ Wrong field name
  resource_specification_id: string;  // ❌ Wrong field name
  agent_id: string;
  // ...
}

// NEW
export interface Listing {
  id: string;
  listing_type: 'offer' | 'need';  // ✅ Correct
  resource_spec_id: string;  // ✅ Correct
  agent_id: string;
  // ...
}

// Update create types
export interface ListingCreate {
  listing_type: 'offer' | 'need';
  resource_spec_id: string;
  agent_id: string;
  quantity: number;
  location?: string;
  note?: string;
  ttl_hours?: number;
}
```

## Phase 2: Update Frontend Consumers (30 minutes)

### Task 2.1: Update pages using VF API
**Files**: `frontend/src/pages/OffersPage.tsx`, `frontend/src/pages/NeedsPage.tsx`
**Estimated**: 30 minutes

Update imports and usages:
```typescript
// OLD
import { getIntents, createIntent } from '../api/valueflows';

// NEW
import { getListings, createListing } from '../api/valueflows';

// In component
const { data: listings } = useQuery(['listings'], getListings);
const offers = listings?.filter(l => l.listing_type === 'offer');
const needs = listings?.filter(l => l.listing_type === 'need');
```

Update form submissions:
```typescript
// OLD
await createIntent({
  type: 'offer',
  resource_specification_id: selectedSpec.id,
  // ...
});

// NEW
await createListing({
  listing_type: 'offer',
  resource_spec_id: selectedSpec.id,
  // ...
});
```

## Phase 3: Testing (30 minutes)

### Task 3.1: Manual testing
**Estimated**: 20 minutes

1. Start frontend and backend
2. Open browser dev tools Network tab
3. Create an offer:
   - Fill form
   - Submit
   - Verify request goes to `/api/vf/listings/` (not `/intents`)
   - Verify payload has `listing_type: 'offer'`
   - Verify payload has `resource_spec_id`
   - Verify 201 Created response
4. Create a need:
   - Same verification as offer
5. View offers page:
   - Verify offers load
   - Verify no 404 errors

### Task 3.2: Check for remaining references
**Estimated**: 10 minutes

```bash
# Search for any remaining /intents references
grep -r "intents" frontend/src/

# Search for old field names
grep -r "resource_specification_id" frontend/src/
grep -r '"type":' frontend/src/ | grep -v listing_type

# Fix any found issues
```

## Verification Checklist

- [ ] All `/intents` routes changed to `/listings`
- [ ] All `type` fields changed to `listing_type`
- [ ] All `resource_specification_id` changed to `resource_spec_id`
- [ ] TypeScript types updated
- [ ] No TypeScript errors
- [ ] Offer creation works
- [ ] Need creation works
- [ ] No 404 or 422 errors
- [ ] All pages render correctly

## Estimated Total Time

- Phase 1: 1 hour
- Phase 2: 30 minutes
- Phase 3: 30 minutes

**Total: 2 hours**
