# Tasks: GAP-61 Anonymous Gifts (Emma Goldman)

## Overview

Implement anonymous gift-giving to resist surveillance, maintain freedom, and preserve the purity of spontaneous mutual aid.

## Phase 1: Database Schema (1-2 hours)

### Task 1.1: Add anonymous field to listings
**File**: Database migration
**Estimated**: 1 hour

```sql
ALTER TABLE listings ADD COLUMN anonymous BOOLEAN DEFAULT FALSE;
ALTER TABLE listings ALTER COLUMN agent_id DROP NOT NULL;  -- Can be NULL if anonymous

ALTER TABLE exchanges ADD COLUMN anonymous BOOLEAN DEFAULT FALSE;
ALTER TABLE exchanges ALTER COLUMN provider_id DROP NOT NULL;  -- Can be NULL

CREATE INDEX idx_listings_anonymous ON listings(anonymous) WHERE anonymous = TRUE;
```

**Acceptance criteria**:
- Anonymous listings supported
- Agent ID nullable for anonymous offers
- Database queries updated

### Task 1.2: Update repository layer
**File**: `valueflows_node/app/repositories/listing_repository.py`
**Estimated**: 1 hour

```python
async def create_anonymous_listing(self, data: dict):
    """Create listing without agent attribution"""
    data['anonymous'] = True
    data['agent_id'] = None  # No attribution
    return await self.create_listing(data)

async def get_anonymous_listings(self):
    """Fetch all anonymous gifts (community shelf)"""
    return await self.db.execute(
        "SELECT * FROM listings WHERE anonymous = TRUE AND taken = FALSE"
    )
```

**Acceptance criteria**:
- Anonymous creation supported
- Query methods work correctly
- No agent tracking for anonymous

## Phase 2: API Endpoints (1-2 hours)

### Task 2.1: Add anonymous flag to create endpoint
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 1 hour

```python
from pydantic import BaseModel

class ListingCreate(BaseModel):
    # ... existing fields ...
    anonymous: bool = False

    @validator('agent_id')
    def validate_agent_id_required_if_not_anonymous(cls, v, values):
        if not values.get('anonymous') and not v:
            raise ValueError("agent_id required for non-anonymous listings")
        return v

@router.post("/")
async def create_listing(data: ListingCreate):
    if data.anonymous:
        data.agent_id = None  # Strip agent ID
    return await repo.create_listing(data.dict())
```

**Acceptance criteria**:
- Anonymous flag accepted
- Agent ID stripped for anonymous
- Validation works correctly

### Task 2.2: Create community shelf endpoint
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 30 minutes

```python
@router.get("/community-shelf")
async def get_community_shelf():
    """Get all anonymous gifts available for taking"""
    return await repo.get_anonymous_listings()
```

**Acceptance criteria**:
- Returns only anonymous, untaken listings
- No agent info exposed

### Task 2.3: Update take/claim endpoint
**Estimated**: 30 minutes

```python
@router.post("/{listing_id}/take")
async def take_anonymous_gift(listing_id: str, taker_id: str):
    listing = await repo.get_listing(listing_id)

    if listing.anonymous:
        # Mark as taken, but don't create exchange record
        # (true Goldman style - no trace!)
        await repo.mark_taken(listing_id)
        return {"status": "taken", "message": "Pure gift received"}
    else:
        # Normal matched exchange flow
        return await create_exchange(listing_id, taker_id)
```

**Acceptance criteria**:
- Anonymous gifts taken without exchange record
- Normal gifts use existing flow

## Phase 3: Frontend Components (3-4 hours)

### Task 3.1: Add anonymous toggle to offer creation
**File**: `frontend/src/pages/CreateOfferPage.tsx`
**Estimated**: 1 hour

```tsx
<FormControlLabel
  control={
    <Switch
      checked={anonymous}
      onChange={(e) => setAnonymous(e.target.checked)}
    />
  }
  label="Make this an anonymous gift"
/>

{anonymous && (
  <Alert severity="info">
    <strong>Anonymous Gift</strong>
    <p>Leave it on the community shelf. No one will know it's from you.</p>
    <p>Why anonymous? Sometimes the best gifts are those with no strings attached.</p>
  </Alert>
)}
```

**Acceptance criteria**:
- Toggle visible and functional
- Explanation clear
- Goldman quote included

### Task 3.2: Create Community Shelf page
**File**: `frontend/src/pages/CommunityShelfPage.tsx` (new)
**Estimated**: 2 hours

```tsx
export function CommunityShelfPage() {
  const { data: anonymousOffers } = useQuery(['community-shelf'],
    () => api.get('/vf/listings/community-shelf')
  );

  return (
    <Page title="Community Shelf">
      <Alert severity="info">
        "The individual is the heart of society." - Emma Goldman
        <p>These gifts were left anonymously. Take what you need, no questions asked.</p>
      </Alert>

      <Grid container spacing={2}>
        {anonymousOffers?.map(offer => (
          <Grid item xs={12} sm={6} md={4} key={offer.id}>
            <OfferCard
              {...offer}
              giver="Someone in your community"
              anonymous
              onTake={() => takeAnonymousGift(offer.id)}
            />
          </Grid>
        ))}
      </Grid>

      {anonymousOffers?.length === 0 && (
        <EmptyState>
          No anonymous gifts right now. Be the first to leave one!
        </EmptyState>
      )}
    </Page>
  );
}
```

**Acceptance criteria**:
- Lists anonymous offers
- No giver attribution
- Taking is frictionless
- Beautiful UI

### Task 3.3: Update statistics to handle anonymous
**File**: `frontend/src/pages/StatsPage.tsx`
**Estimated**: 1 hour

```tsx
<Card>
  <CardContent>
    <Typography variant="h6">Your Contributions</Typography>
    <Stat label="Tracked gifts" value={trackedGifts} />
    <Stat
      label="Anonymous gifts given"
      value={<LockIcon />}
      helperText="[HIDDEN - that's the point!]"
    />
    <Stat
      label="Anonymous gifts received"
      value={anonymousReceived}
      helperText="from unknown givers"
    />

    <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
      "Some of the best gifts can't be counted."
    </Typography>
  </CardContent>
</Card>
```

**Acceptance criteria**:
- Anonymous giving not counted publicly
- Anonymous receiving shown
- Celebrates unquantified generosity

## Phase 4: Privacy & Settings (2 hours)

### Task 4.1: Add privacy settings
**File**: `frontend/src/pages/SettingsPage.tsx`
**Estimated**: 1 hour

```tsx
<Section title="Privacy">
  <Toggle
    label="Always make my gifts anonymous"
    description="All your offers will be anonymous by default"
  />

  <Toggle
    label="Hide my statistics from others"
    description="Keep your contribution data private"
  />
</Section>
```

**Acceptance criteria**:
- User can default to anonymous
- Statistics hideable

### Task 4.2: Retroactive anonymization
**File**: API endpoint + UI
**Estimated**: 1 hour

```python
@router.post("/listings/{listing_id}/anonymize")
async def anonymize_listing(listing_id: str, user_id: str):
    """Convert existing listing to anonymous"""
    listing = await repo.get_listing(listing_id)

    if listing.agent_id != user_id:
        raise HTTPException(403, "Not your listing")

    await repo.update_listing(listing_id, {
        'anonymous': True,
        'agent_id': None
    })

    return {"status": "anonymized"}
```

**Acceptance criteria**:
- Users can anonymize old gifts
- Permission check in place

## Phase 5: Testing (2-3 hours)

### Task 5.1: Unit tests
**Estimated**: 1.5 hours

```python
def test_create_anonymous_listing():
    listing = create_listing({
        'anonymous': True,
        'quantity': 5
    })
    assert listing.agent_id is None
    assert listing.anonymous is True

def test_anonymous_listing_not_in_personal_stats():
    stats = get_user_stats(user_id)
    # Anonymous gifts should not appear in public stats
    assert 'anonymous_given' not in stats
```

**Acceptance criteria**:
- All anonymous flows tested
- Privacy guarantees verified

### Task 5.2: E2E tests
**Estimated**: 1.5 hours

Test full flow:
1. Create anonymous offer
2. Verify not attributed to user
3. Take anonymous gift
4. Verify no exchange record
5. Check statistics hide anonymous giving

**Acceptance criteria**:
- End-to-end flow works
- No data leakage

## Verification Checklist

- [ ] Users can make anonymous offers
- [ ] Anonymous gifts don't appear in personal stats
- [ ] Community shelf page exists
- [ ] Taking anonymous gifts is frictionless
- [ ] System doesn't guilt-trip anonymous givers
- [ ] UI celebrates untracked generosity
- [ ] Privacy settings work
- [ ] Retroactive anonymization supported
- [ ] Tests pass
- [ ] Documentation complete

## Estimated Total Time

- Phase 1: 2 hours (database)
- Phase 2: 2 hours (API)
- Phase 3: 4 hours (frontend)
- Phase 4: 2 hours (privacy)
- Phase 5: 3 hours (testing)

**Total: 3-4 days (13 hours)**

## Dependencies

- Database migration support
- User authentication
- Existing listing/exchange system

## Philosophical Principles

- Freedom from surveillance is a right
- Not everything should be measured
- Pure gifts have no strings attached
- Privacy enables dignity

## Success Metrics

- 20%+ of gifts are anonymous
- Users report feeling "free" to give without tracking
- Privacy-conscious users adopt the feature
- No reports of feeling pressured to use tracking mode
