# Proposal: Abundance Osmosis

**Submitted By:** Philosopher Council (Kropotkin)
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-20
**Gap Addressed:** GAP-63
**Priority:** P3 - Philosophical (Post-Workshop)

## Problem Statement

**Kropotkin** observed in "Mutual Aid": In nature, abundance spreads. When one garden thrives, seeds spread to neighbors. Knowledge flows. Skills transfer. **Without explicit transactions.**

Current app requires:
- Explicit offer posting
- Explicit matching
- Explicit exchange completion
- No "osmosis" - unintentional spreading of abundance

The app models scarcity (everything must be tracked, matched, recorded) not abundance (overflow spills naturally).

## Proposed Solution

### Abundance Flows Naturally

Features that let surplus spread without explicit transactions:

### 1. Overflow Offers

When someone has persistent surplus, gently suggest sharing:

```python
class OverflowDetection:
    """Detect when offers have been available for a while"""

    def check_for_overflow(self, user_id: str) -> Optional[OverflowPrompt]:
        # Find offers that have been available for 3+ days
        old_offers = get_offers_older_than(user_id, days=3)

        if not old_offers:
            return None

        return OverflowPrompt(
            message="You've had tomatoes available for 3 days. Let them flow?",
            options=[
                "Leave on community shelf (anyone can take)",
                "Keep offer as-is (wait for match)",
                "I'm actually keeping these (close offer)"
            ]
        )
```

### 2. Community Shelves

Physical or virtual "take what you need" spaces:

```python
class CommunityShelf(BaseModel):
    id: str
    location: str              # "Downtown library foyer" or virtual
    items: List[ShelfItem]

class ShelfItem(BaseModel):
    description: str           # "3 jars homemade jam"
    added_at: datetime
    # NO: added_by - can be anonymous (see GAP-61)
    # NO: taken_by - not tracked
    # NO: quantity_taken - not tracked
```

When someone takes from a shelf, **no record is kept of who took what**. The abundance just flows.

### 3. Knowledge Ripples

When someone learns something, suggest they teach:

```python
# When exchange is completed
if exchange.category == "learning" and exchange.receiver_id == user_id:
    # User just learned something
    weeks_later(2)  # Don't prompt immediately

    prompt = KnowledgeRipplePrompt(
        message=f"You learned {exchange.description} 2 weeks ago. Feeling solid? Maybe teach someone else?",
        options=[
            "Offer to teach (create learning offer)",
            "Still learning (not ready)",
            "Not my thing to teach"
        ]
    )
```

### 4. Seed Libraries

Shared resources that circulate without ownership:

```python
class CirculatingResource(BaseModel):
    id: str
    description: str           # "Dewalt drill"
    category: str              # "tools"
    current_location: str      # "Alice's garage" - just location, not ownership
    notes: str                 # "Needs new battery"

    # Resources move around - we track WHERE not WHO OWNS
    # Anyone can update location when they pass it on
```

## Requirements

### Requirement: Overflow Detection

The system SHALL detect persistent surplus and prompt sharing.

#### Scenario: Tomato Overflow
- GIVEN Maria has had "10kg tomatoes" offered for 4 days
- AND no one has matched
- WHEN Maria opens the app
- THEN she sees a gentle prompt: "Your tomatoes haven't found a match. Let them flow to the community shelf?"
- AND she can accept, decline, or snooze
- AND declining doesn't affect her in any way

### Requirement: Anonymous Community Shelves

The system SHALL support community shelves where giving and taking are anonymous.

#### Scenario: Drop Off
- GIVEN a community shelf exists at "Main St library"
- WHEN Maria adds items
- THEN she can choose to be anonymous or not
- AND the app just records "3 jars jam added to Main St shelf"
- AND NO tracking of who added what (if anonymous)

#### Scenario: Pick Up
- GIVEN items are on the community shelf
- WHEN someone takes items
- THEN NO record is kept of who took what
- AND the item is just marked "no longer on shelf" (or removed)
- AND shelf creator can see aggregate counts ("12 items taken this week")

### Requirement: Knowledge Ripple Suggestions

The system SHALL gently suggest knowledge sharing.

#### Scenario: Teach What You Learned
- GIVEN Bob completed an exchange to learn "bicycle repair"
- WHEN 2 weeks have passed
- THEN Bob gets a gentle prompt: "Feeling confident? Maybe teach someone else?"
- AND this is a suggestion only, not a requirement
- AND Bob can dismiss permanently ("stop suggesting")

### Requirement: Circulating Resources

The system SHALL track shared resources by location, not ownership.

#### Scenario: Drill Circulation
- GIVEN a drill is registered as a circulating resource
- WHEN Alice has it and passes it to Bob
- THEN Alice updates: "Drill is now at Bob's place"
- AND NO transaction is recorded
- AND no one "owns" the drill - it belongs to the community

## Data Model

```python
class CommunityShelf(BaseModel):
    id: str
    name: str
    location: str
    created_by: str             # Steward who set it up
    cell_id: str
    is_virtual: bool = False    # Virtual shelves for digital goods

class ShelfItem(BaseModel):
    id: str
    shelf_id: str
    description: str
    category: str
    added_at: datetime
    added_by: Optional[str]     # None if anonymous
    still_available: bool = True
    # NOTE: No taken_by, no quantity_tracking

class CirculatingResource(BaseModel):
    id: str
    description: str
    category: str
    current_location: str       # Physical location or "unknown"
    current_holder_notes: str   # "Works great" / "Needs repair"
    last_updated: datetime
    # NOTE: No ownership, no checkout history
```

## Privacy Guarantees

**What we track:**
- That items exist on shelves (public info)
- Where circulating resources currently are (public info)
- Aggregate stats: "12 items given from shelf this week"

**What we DON'T track:**
- Who took what from shelves
- Pattern of who uses circulating resources
- "Contribution scores" for shelf giving
- Any surveillance of generosity

Abundance flows anonymously. We don't count gifts.

## Implementation

### Phase 1: Community Shelves
- Create shelf in cell
- Add items (anonymous or attributed)
- Take items (always anonymous)
- Aggregate stats for stewards

### Phase 2: Overflow Prompts
- Detect old offers (3+ days)
- Gentle "let it flow?" prompt
- One-click move to shelf

### Phase 3: Circulating Resources
- Register shared resources
- Update location
- Notes/condition tracking

### Phase 4: Knowledge Ripples
- Track learning exchanges
- 2-week delayed prompt
- "Teach what you learned?"

## Philosophical Foundation

**Kropotkin on mutual aid:**
"The mutual-aid tendency in man has so remote an origin... that we may consider it as the natural continuation of the development of life."

This isn't charity. It's abundance finding its natural flow. The tomatoes don't need to be "matched" - they can just flow to whoever needs them. The drill doesn't need an "owner" - it belongs to the community and moves where it's needed.

**Gift economy vs exchange economy:**
Traditional gift economies didn't track every transaction. Abundance flowed. Trust grew. Community deepened. We're recreating that.

## Success Criteria

- [ ] Community shelves can be created by cells
- [ ] Items can be added anonymously
- [ ] Taking items leaves no record of who took
- [ ] Overflow prompts appear for old offers
- [ ] Circulating resources track location not ownership
- [ ] No contribution scoring or gift surveillance

## Dependencies

- Local Cells (shelf belongs to cell)
- GAP-61 Anonymous Gifts (overlapping concept)
- Notification system

## Notes

The goal is to model abundance, not scarcity. Current app: "You have tomatoes, someone needs tomatoes, let's match!" Osmosis: "You have tomatoes, here's a shelf, whoever needs them will take them."

Less tracking. More trust. More flow.
