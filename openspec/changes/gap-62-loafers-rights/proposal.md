# GAP-62: No "Loafer's Rights" - System Pressures Contribution (Goldman + Kropotkin)

**Status**: Draft
**Priority**: P7 - Philosophical/Political
**Philosophers**: Emma Goldman + Peter Kropotkin
**Concept**: Right to Laziness, Contribution Without Coercion
**Estimated Effort**: 2-3 days
**Assigned**: Unclaimed

## Theoretical Foundation

**Emma Goldman**: "The right to be lazy" - true freedom includes the right NOT to produce.

**Peter Kropotkin**: Mutual aid should be voluntary and joyful, not enforced. "From each according to ability" means *according to YOUR assessment of your ability*, not society's demands.

**Paul Lafargue** ("The Right to be Lazy"): The capitalist fetish for productivity must be rejected. Leisure is not the enemy of solidarity.

## Problem Statement

The app subtly pressures contribution through:
- "You haven't posted an offer in 2 weeks!" notifications
- Statistics that make non-givers feel guilty
- Implicit expectation that everyone must participate equally
- Matching "needs" with "offers" assumes everyone has something to offer

**This replicates capitalist work ethic**: Everyone must be productive. Receiving without giving is shameful.

**Goldman would say**: "Some days I garden. Some days I nap. Both are valid. Your app shouldn't judge."

## Current Reality

Pressure points in current design:
1. **Navigation badge**: "You have 3 proposals!" (but none for "take a break")
2. **Stats page**: "Alice shared 47 items!" (implicit: why haven't you?)
3. **Empty profile shame**: If you have no offers, your profile looks "lazy"
4. **No "I need rest" option**: All interactions are transactional

Missing:
- Celebration of non-participation
- Recognition that needs are valid without offers
- Space for rest, grief, burnout
- Protection from "productivity theater"

## Required Implementation

### MUST Requirements

1. System MUST allow users to receive without giving (no reciprocity pressure)
2. System MUST NOT send "you haven't contributed" guilt-trips
3. System MUST NOT display "contribution scores" that shame non-participants
4. System MUST celebrate rest and recovery as valid states
5. System MUST allow "I'm taking a break" status

### SHOULD Requirements

1. System SHOULD explain the political right to laziness
2. System SHOULD normalize asking for help without offering help
3. System SHOULD have a "needs only" mode (no obligation to offer)
4. System SHOULD track burnout and suggest rest

### MAY Requirements

1. System MAY have "sabbatical mode" - pause all expectations
2. System MAY surface quotes from Goldman/Kropotkin about rest
3. System MAY create "rest is resistance" messaging

## Scenarios

### WHEN user hasn't posted offer in a while

**Current (implicit pressure)**:
```
[Notification] You haven't shared anything recently! Post an offer?
```

**Goldman-compatible**:
```
NO NOTIFICATION

Or, if the system must say something:
"Taking a break? That's valid. The commune is here when you're ready."
```

### WHEN user only has needs, no offers

**Current**: Profile looks empty, feels shameful

**Goldman-compatible**:
```
Bob's Profile
Needs: Help with childcare (3 hours/week)
Offers: None right now, and that's okay

"Everyone goes through seasons of capacity and need.
Right now, Bob needs support. That's what mutual aid is for."
```

### WHEN user wants to set boundaries

**New Feature: Rest Mode**:
```
☑ I'm in rest mode

What this means:
- No notifications about matches or proposals
- Profile shows "Taking time to rest"
- You can still receive gifts if needed
- No judgment, no timeline to return

Why? Sometimes life is hard. Rest is resistance to productivity culture.
```

## Implementation

### User Status Field

```sql
ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active';
-- Values: 'active', 'resting', 'sabbatical'

ALTER TABLE users ADD COLUMN status_note TEXT;
-- User can explain: "Recovering from injury", "Caring for family", etc.
```

### Profile Display

```tsx
{user.status === 'resting' && (
  <Banner variant="info">
    🌙 {user.name} is taking time to rest.
    {user.status_note && <p>{user.status_note}</p>}
    <p>"The right to be lazy is sacred." - Emma Goldman</p>
  </Banner>
)}

{user.offers.length === 0 && user.needs.length > 0 && (
  <Message>
    Right now, {user.name} is in a season of needing support.
    Mutual aid means we support each other through all seasons.
  </Message>
)}
```

### Settings: Disable Guilt-Trips

```tsx
<SettingsPage>
  <Section title="Notifications">
    <Toggle
      label="Suggest posting offers when I haven't in a while"
      defaultValue={false}
      description="Some people find this helpful. Others find it guilt-trippy. You decide."
    />

    <Toggle
      label="Show my contribution statistics"
      defaultValue={false}
      description="If numbers make you feel bad, hide them. You know your own capacity."
    />
  </Section>

  <Section title="Rest Mode">
    <Toggle
      label="Enable rest mode"
      description="Pause all notifications. Signal to community you're taking a break."
    />
    {restMode && (
      <TextArea
        label="Optional note (visible to community)"
        placeholder="e.g., 'Recovering from burnout', 'Caring for sick parent', or just 'Need rest'"
      />
    )}
  </Section>
</SettingsPage>
```

### Statistics Page Redesign

**Current (problematic)**:
```
🌟 Top Contributors This Month:
1. Alice - 47 gifts
2. Carol - 32 gifts
3. Bob - 28 gifts

[You: 3 gifts - Come on, you can do better!]
```

**Goldman-compatible**:
```
Community Abundance This Month:
- 347 gifts shared
- 89 needs met
- 23 people in rest mode (we're holding you)

Individual stats hidden by default.
[Show my personal stats] ← optional, not default
```

## Philosophical Considerations

### The Right to Receive

**Kropotkin**: "In a well-organized society, all will have a right to live and to enjoy life."

Not *earn* the right. Not *work for* the right. Just *have* the right.

### Productivity as Violence

**Goldman**: The capitalist demand for constant productivity is a form of violence. Anarchism means you can nap.

### Trust vs. Enforcement

**Kropotkin**: Real mutual aid is based on trust, not enforcement. If you're worried about "freeloaders," you're thinking like a capitalist.

## Success Criteria

- [ ] Users can receive without giving (no pressure)
- [ ] "Rest mode" exists and is celebrated
- [ ] No guilt-trip notifications
- [ ] Profiles with only needs are normalized
- [ ] Statistics don't create hierarchy
- [ ] Users report feeling safe to rest

## Risks & Mitigations

**Risk**: "Everyone will go into rest mode and nothing will get done!"

**Response**:
1. That's a capitalist fear (scarcity thinking)
2. Empirical question - try it!
3. If everyone's in rest mode, maybe that's the collective need right now
4. Most people WANT to contribute when they have capacity

**Risk**: Some users exploit this - take without ever giving

**Response**:
1. That's their right (Goldman's point!)
2. If it becomes a pattern that hurts the commune, community can address it socially (not programmatically)
3. A few "freeloaders" are less harmful than coercing everyone

## Related Gaps

- GAP-61: Anonymous gifts (freedom from surveillance)
- GAP-59: Conscientization (critical reflection on why we give)
- GAP-67: Mourning protocol (rest during grief)

## References

- Goldman, Emma. "The Right to Be Lazy"
- Kropotkin, Peter. *Mutual Aid: A Factor of Evolution* (1902)
- Lafargue, Paul. *The Right to Be Lazy* (1883)
- Original spec: `VISION_REALITY_DELTA.md:GAP-62`

## Philosopher Quote

> "Somebody has said that dust is matter in the wrong place. The same can be said about persons who are supposed to be wrong people in the right place." - Emma Goldman

Applied: There's no "wrong" amount to contribute. Rest is not laziness. Needing help is not failure. The app should reflect this.
