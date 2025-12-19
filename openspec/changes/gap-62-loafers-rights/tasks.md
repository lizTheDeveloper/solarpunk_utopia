# Tasks: GAP-62 Loafer's Rights (Goldman + Kropotkin)

## Overview

Implement the "right to be lazy" - remove contribution pressure, celebrate rest, and normalize receiving without giving.

## Phase 1: Remove Guilt-Trips (2-3 hours)

### Task 1.1: Audit and remove pressure notifications
**Files**: All notification/badge systems
**Estimated**: 1.5 hours

Find and remove:
```typescript
// ❌ REMOVE these guilt-trips
"You haven't posted an offer in 2 weeks!"
"Come on, you can do better!"
"Your contribution is low this month"
"Top Contributors" leaderboards

// ✅ KEEP helpful reminders (optional, user-controlled)
"New matches available for your needs"
"Your offer was accepted"
```

**Acceptance criteria**:
- No "you should contribute" messages
- No contribution comparisons
- No leaderboards
- Notifications are informational only

### Task 1.2: Make contribution stats opt-in
**File**: `frontend/src/pages/StatsPage.tsx`
**Estimated**: 1 hour

```tsx
export function StatsPage() {
  const [showPersonalStats, setShowPersonalStats] = useState(false);

  return (
    <Page title="Community Abundance">
      <Card>
        <CardContent>
          <Typography variant="h6">Community This Month</Typography>
          <Stat label="Gifts shared" value={347} />
          <Stat label="Needs met" value={89} />
          <Stat label="People in rest mode" value={23} helperText="we're holding you" />
        </CardContent>
      </Card>

      <Button
        variant="outlined"
        onClick={() => setShowPersonalStats(!showPersonalStats)}
      >
        {showPersonalStats ? 'Hide' : 'Show'} my personal stats
      </Button>

      {showPersonalStats && (
        <Card>
          <CardContent>
            <Typography variant="h6">Your Contributions</Typography>
            <Stat label="Gifts given" value={userStats.given} />
            <Stat label="Gifts received" value={userStats.received} />
            <Typography variant="caption" color="text.secondary">
              Stats are for your awareness only. There's no "right" amount to contribute.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Page>
  );
}
```

**Acceptance criteria**:
- Community stats shown by default
- Personal stats hidden by default
- No judgment in messaging

### Task 1.3: Update settings to disable all contribution reminders
**File**: `frontend/src/pages/SettingsPage.tsx`
**Estimated**: 30 minutes

```tsx
<Section title="Notifications">
  <Toggle
    label="Suggest posting offers when I haven't in a while"
    defaultValue={false}
    description="Some find this helpful. Others find it guilt-trippy. You decide."
  />

  <Toggle
    label="Show my contribution statistics"
    defaultValue={false}
    description="If numbers make you feel bad, hide them. You know your own capacity."
  />
</Section>
```

**Acceptance criteria**:
- All contribution reminders optional
- Default is OFF
- Clear explanations

## Phase 2: Rest Mode (3-4 hours)

### Task 2.1: Add user status field
**File**: Database migration
**Estimated**: 30 minutes

```sql
ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active';
-- Values: 'active', 'resting', 'sabbatical'

ALTER TABLE users ADD COLUMN status_note TEXT;
ALTER TABLE users ADD COLUMN status_updated_at TIMESTAMP;

CREATE INDEX idx_users_status ON users(status);
```

**Acceptance criteria**:
- Status field added
- Note field for context
- Timestamped

### Task 2.2: Create rest mode UI
**File**: `frontend/src/components/RestModeToggle.tsx` (new)
**Estimated**: 2 hours

```tsx
export function RestModeToggle() {
  const { user } = useAuth();
  const [restMode, setRestMode] = useState(user.status === 'resting');
  const [note, setNote] = useState(user.status_note || '');

  const handleToggle = async () => {
    await updateUserStatus({
      status: restMode ? 'active' : 'resting',
      note: restMode ? null : note
    });
    setRestMode(!restMode);
  };

  return (
    <Card>
      <CardContent>
        <FormControlLabel
          control={
            <Switch checked={restMode} onChange={handleToggle} />
          }
          label="Rest Mode"
        />

        {restMode && (
          <>
            <Alert severity="info" sx={{ mt: 2 }}>
              <strong>What rest mode means:</strong>
              <ul>
                <li>No notifications about matches or proposals</li>
                <li>Profile shows "Taking time to rest"</li>
                <li>You can still receive gifts if needed</li>
                <li>No judgment, no timeline to return</li>
              </ul>
              <Typography variant="body2" sx={{ fontStyle: 'italic', mt: 1 }}>
                "Sometimes life is hard. Rest is resistance to productivity culture."
              </Typography>
            </Alert>

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Optional note (visible to community)"
              placeholder="e.g., 'Recovering from burnout', 'Caring for sick parent', or just 'Need rest'"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              sx={{ mt: 2 }}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
```

**Acceptance criteria**:
- Toggle works
- Explanation clear
- Optional note supported
- Goldman quote included

### Task 2.3: Update profile display
**File**: `frontend/src/pages/ProfilePage.tsx`
**Estimated**: 1 hour

```tsx
{user.status === 'resting' && (
  <Banner variant="info" icon={<MoonIcon />}>
    🌙 {user.name} is taking time to rest.
    {user.status_note && <p>{user.status_note}</p>}
    <Quote>"The right to be lazy is sacred." - Emma Goldman</Quote>
  </Banner>
)}

{user.offers.length === 0 && user.needs.length > 0 && (
  <Message variant="supportive">
    Right now, {user.name} is in a season of needing support.
    Mutual aid means we support each other through all seasons.
  </Message>
)}
```

**Acceptance criteria**:
- Rest mode visible
- Supportive messaging
- Normalizes receiving without giving

### Task 2.4: Disable notifications in rest mode
**File**: Notification service
**Estimated**: 30 minutes

```python
async def should_send_notification(user_id: str, notification_type: str) -> bool:
    user = await get_user(user_id)

    if user.status in ['resting', 'sabbatical']:
        # Only send critical notifications in rest mode
        return notification_type in ['urgent_message', 'safety_alert']

    return True
```

**Acceptance criteria**:
- Rest mode blocks non-critical notifications
- Safety alerts still work

## Phase 3: Normalize "Needs Only" Profiles (2 hours)

### Task 3.1: Update empty profile messaging
**File**: `frontend/src/pages/ProfilePage.tsx`
**Estimated**: 1 hour

```tsx
{user.offers.length === 0 && (
  <Card>
    <CardContent>
      <Typography variant="h6">Offers</Typography>
      <Typography color="text.secondary">
        None right now, and that's okay.
      </Typography>
      <Alert severity="info" sx={{ mt: 2 }}>
        Everyone goes through seasons of capacity and need.
        Right now, {user.name} needs support. That's what mutual aid is for.
      </Alert>

      <Quote author="Peter Kropotkin">
        "In a well-organized society, all will have a right to live and to enjoy life."
      </Quote>
    </CardContent>
  </Card>
)}
```

**Acceptance criteria**:
- Empty offers normalized
- Supportive messaging
- Kropotkin quote

### Task 3.2: Add "seasons of capacity" explanation
**File**: `frontend/src/pages/AboutPage.tsx` or onboarding
**Estimated**: 1 hour

```tsx
<Section title="Seasons of Capacity">
  <p>
    In our community, we recognize that people go through different seasons:
  </p>

  <ul>
    <li><strong>Abundance:</strong> You have capacity to give</li>
    <li><strong>Balance:</strong> Giving and receiving in flow</li>
    <li><strong>Need:</strong> You need support right now</li>
    <li><strong>Rest:</strong> You're recovering and that's valid</li>
  </ul>

  <p>
    All seasons are welcome. There's no pressure to be in "abundance" all the time.
    The community holds you through all seasons.
  </p>

  <Quote author="Emma Goldman">
    "The right to be lazy is not the enemy of solidarity. It's its foundation."
  </Quote>
</Section>
```

**Acceptance criteria**:
- Seasons explained
- All seasons validated
- No productivity pressure

## Phase 4: Testing (2 hours)

### Task 4.1: User testing
**Estimated**: 1.5 hours

Test with users in different states:
- New users with no offers
- Users in rest mode
- Users with only needs
- Active contributors

Questions:
- Do you feel pressure to contribute?
- Is rest mode invitational?
- Do empty profiles feel shameful?

**Acceptance criteria**:
- No reports of feeling pressured
- Rest mode feels supportive
- Needs-only profiles feel valid

### Task 4.2: Automated tests
**Estimated**: 30 minutes

```python
def test_rest_mode_blocks_contribution_reminders():
    user = set_rest_mode(user_id, True)
    notifications = get_pending_notifications(user_id)

    # No contribution reminders
    assert not any(n.type == 'contribution_reminder' for n in notifications)

def test_empty_profile_has_supportive_message():
    user_with_no_offers = get_user(user_id)
    profile_html = render_profile(user_with_no_offers)

    # Should have supportive message
    assert "that's okay" in profile_html.lower()
    assert "mutual aid" in profile_html.lower()
```

**Acceptance criteria**:
- All tests pass
- No pressure in code

## Verification Checklist

- [ ] No guilt-trip notifications
- [ ] Contribution stats opt-in only
- [ ] Rest mode exists and works
- [ ] Rest mode explanation clear
- [ ] Profile supports rest status
- [ ] Empty offers normalized
- [ ] "Needs only" validated
- [ ] Seasons of capacity explained
- [ ] All tests pass
- [ ] User feedback positive

## Estimated Total Time

- Phase 1: 3 hours (remove pressure)
- Phase 2: 4 hours (rest mode)
- Phase 3: 2 hours (normalize needs)
- Phase 4: 2 hours (testing)

**Total: 2-3 days (11 hours)**

## Dependencies

- User authentication
- Notification system
- Profile pages

## Philosophical Principles

- The right to laziness is sacred
- Rest is resistance
- Receiving without giving is valid
- No one owes productivity
- Trust over enforcement

## Success Metrics

- 0% users report feeling guilted
- 10%+ users use rest mode
- Users with only needs don't drop out
- Community supports all seasons
- No toxic productivity culture
