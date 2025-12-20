# Proposal: Mourning Protocol

**Submitted By:** Philosopher Council (bell hooks)
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-20
**Gap Addressed:** GAP-67
**Priority:** P3 - Philosophical (Post-Workshop)

## Problem Statement

**bell hooks:** "The moment we choose to love we begin to move against domination, against oppression."

What happens when someone dies? When someone leaves? When the community experiences collective trauma?

The app has no grief protocol. Metrics keep counting. Notifications keep pinging. The system doesn't know how to hold space for loss.

## Proposed Solution

### Mourning Mode

When activated, the community enters a different mode:

```python
class MourningPeriod(BaseModel):
    cell_id: str
    trigger: Literal["death", "departure", "collective_trauma", "other"]
    honoring: Optional[str]           # Name of person being mourned (if applicable)
    started_at: datetime
    duration_days: int = 7            # Default 1 week, adjustable
    initiated_by: str                 # Steward who activated

    practices: MourningPractices

class MourningPractices(BaseModel):
    pause_metrics: bool = True        # Stop counting contributions
    silence_non_urgent: bool = True   # Quiet the noise
    create_memorial: bool = True      # Space for remembrance
    enable_support_offers: bool = True # Easy way to offer help
```

### What Changes During Mourning

1. **Metrics Pause**
   - No contribution tracking
   - No "you haven't posted in X days" nudges
   - No gamification or achievements

2. **Quiet Mode**
   - Only urgent notifications
   - No marketing, no "you might like..."
   - Just human-to-human messages

3. **Memorial Space**
   - Page for the person/event
   - Share memories
   - Photos, stories, reflections

4. **Support Flows**
   - Easy "I can help" offers
   - "I need help" is normalized
   - Specific prompts: "Need meals? Childcare? Just someone to talk to?"

## Requirements

### Requirement: Activate Mourning

The system SHALL allow stewards to activate mourning mode.

#### Scenario: Community Loss
- GIVEN a beloved member has passed away
- WHEN the steward activates Mourning Mode
- THEN all cell members see a mourning banner
- AND metrics tracking pauses
- AND non-urgent notifications stop
- AND memorial space is created

### Requirement: Pause Productivity

The system SHALL stop measuring productivity during mourning.

#### Scenario: No Pressure
- GIVEN mourning mode is active
- WHEN Maria doesn't post offers for 2 weeks
- THEN NO nudge is sent
- AND NO "inactive member" flag appears on steward dashboard
- AND Maria's standing is completely unaffected

### Requirement: Memorial Space

The system SHALL provide space for collective memory.

#### Scenario: Remember Together
- GIVEN mourning mode for Alex who passed
- WHEN members visit the memorial
- THEN they can:
  - Share a memory (text)
  - Add a photo
  - Record what Alex meant to them
  - See what others shared
- AND this space persists after mourning ends

### Requirement: Support Coordination

The system SHALL make support easy during mourning.

#### Scenario: Practical Help
- GIVEN mourning mode is active
- WHEN Maria wants to help the grieving family
- THEN she sees simple options:
  - "I can bring a meal"
  - "I can help with childcare"
  - "I can run errands"
  - "I'm just here to listen"
- AND offers are coordinated so family isn't overwhelmed

### Requirement: Flexible Duration

The system SHALL allow extending or ending mourning naturally.

#### Scenario: Grief Takes Time
- GIVEN default mourning period is 7 days
- WHEN the community needs more time
- THEN steward can extend
- AND when ready, community can transition out gently
- AND memorial remains accessible

## Data Model

```python
class MourningPeriod(BaseModel):
    id: str
    cell_id: str
    trigger: str
    honoring: Optional[str]
    description: Optional[str]         # What happened
    started_at: datetime
    ends_at: datetime
    extended_count: int = 0
    ended_early: bool = False
    created_by: str

class Memorial(BaseModel):
    id: str
    mourning_id: str
    person_name: Optional[str]
    event_name: Optional[str]          # For collective trauma
    entries: List[MemorialEntry]

class MemorialEntry(BaseModel):
    id: str
    author_id: str
    content: str                       # Memory, reflection
    media_url: Optional[str]           # Photo
    created_at: datetime

class GriefSupport(BaseModel):
    id: str
    mourning_id: str
    offered_by: str
    support_type: Literal["meals", "childcare", "errands", "presence", "other"]
    details: str
    claimed_by: Optional[str]          # If coordinated
```

## Privacy Guarantees

**What we track:**
- That mourning is active (so we can pause metrics)
- Memorial entries (public within cell)
- Support offers (for coordination)

**What we DON'T track:**
- Who visited the memorial
- How long anyone grieved
- "Participation" in mourning
- Who didn't offer support

Grief is private. We hold space without surveillance.

## Implementation

### Phase 1: Mourning Mode
- Steward can activate
- Banner appears for all members
- Metrics pause automatically

### Phase 2: Memorial Space
- Create memorial page
- Add entries (text, photos)
- Persists after mourning ends

### Phase 3: Support Coordination
- Simple offer types
- Coordination to avoid overwhelm
- Connect helpers with family

### Phase 4: Gentle Transitions
- End mourning when ready
- Gradual return to normal
- Memorial stays accessible

## Mourning Banner UI

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🕯️ Our community is in mourning                           │
│                                                             │
│  We are honoring the memory of Alex Chen.                   │
│                                                             │
│  During this time:                                          │
│  • Take the time you need                                   │
│  • No productivity tracking                                 │
│  • Support offers welcome                                   │
│                                                             │
│  "Grief is not something to get over,                       │
│   but something to move through." - bell hooks              │
│                                                             │
│  [Visit Memorial]  [Offer Support]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Philosophical Foundation

**bell hooks on love and loss:**
"Knowing how to be solitary is central to the art of loving. When we can be alone, we can be with others without using them as a means of escape."

Mourning is not weakness. It's love manifesting as loss. A community that can grieve together is a community that loves together.

**Rest as resistance:**
The capitalist demand for constant productivity doesn't pause for death. We reject that. When someone dies, the appropriate response is to **stop**. To feel. To remember. To hold each other.

The app will not ping you during grief. It will not count your contributions. It will hold space.

## Success Criteria

- [ ] Stewards can activate mourning mode
- [ ] Metrics pause during mourning
- [ ] Non-urgent notifications stop
- [ ] Memorial space created and usable
- [ ] Support offers easy to make and coordinate
- [ ] Mourning can extend or end naturally
- [ ] Memorial persists after mourning ends
- [ ] No surveillance of grief (who visited, how long, etc.)

## Dependencies

- Cell and steward system
- Notification system (to silence it)
- Metrics system (to pause it)

## Notes

This is about building a community that can hold sorrow, not just joy. bell hooks taught us that love is a practice. Part of that practice is mourning together.

When someone dies, the app should know how to be quiet.
