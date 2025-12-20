# Proposal: Eject Button (Fork Rights)

**Submitted By:** Philosopher Council (Bakunin)
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED
**Implemented:** 2025-12-20
**Gap Addressed:** GAP-65
**Priority:** P3 - Philosophical (Post-Workshop)

## Problem Statement

**Bakunin:** "Freedom without socialism is privilege, injustice; socialism without freedom is slavery and brutality."

What if commune governance goes bad? What if majority tyrannizes minority? Currently, users have no "eject button" - they're stuck in a community or must leave entirely and lose everything.

Freedom includes the right to exit **with your data and relationships**.

## Proposed Solution

### Fork Rights

Any member can leave a community and take:
- Their own data
- Their relationship connections (with consent of the other person)
- Their history (for personal record)

### Data Portability

One-click export of everything that's yours:

```python
class DataExport(BaseModel):
    user_id: str
    exported_at: datetime

    # YOUR data (you own it)
    my_profile: UserProfile
    my_offers: List[Offer]
    my_needs: List[Need]
    my_exchanges: List[Exchange]      # History of your exchanges
    my_vouches_given: List[Vouch]     # Who you vouched for
    my_vouches_received: List[Vouch]  # Who vouched for you (with their consent)

    # Portable connections (with consent)
    my_connections: List[Connection]  # People who agreed to stay connected

    # NOT included (community data, not yours)
    # - Other people's offers
    # - Community governance decisions
    # - Cell membership lists
```

### Fork a Community

If you believe the community is going wrong, you can fork:

```python
class CommunityFork(BaseModel):
    original_cell_id: str
    new_cell_name: str
    forked_by: str
    fork_reason: Optional[str]       # Optional public statement
    members_invited: List[str]       # Who you're inviting to join
    forked_at: datetime

    # Fork creates new cell with you as initial steward
    # Others can join if they want
    # Original cell continues unchanged
```

## Requirements

### Requirement: Data Export

The system SHALL allow complete export of personal data.

#### Scenario: Export My Data
- GIVEN Maria wants to leave the community
- WHEN she clicks "Export My Data"
- THEN she receives a SQLite file containing:
  - Her profile
  - Her offers/needs history
  - Her exchange history
  - Her vouches (given and received)
- AND the export completes in under 1 minute
- AND she can use this data in another community or just keep it

### Requirement: Portable Connections

The system SHALL allow exporting connections with consent.

#### Scenario: Take My Relationships
- GIVEN Maria is leaving and wants to stay connected to Bob
- WHEN Maria requests to export the connection
- THEN Bob receives notification: "Maria is leaving and wants to stay connected. Allow?"
- AND if Bob agrees, the connection is included in Maria's export
- AND if Bob declines or doesn't respond, Maria gets just her side of the relationship

### Requirement: Fork Community

The system SHALL allow anyone to fork a community.

#### Scenario: Start Fresh
- GIVEN Carlos disagrees with how the community is governed
- WHEN Carlos clicks "Fork Community"
- THEN he creates a new cell with himself as steward
- AND he can invite anyone from the original cell
- AND invitees can join the fork, stay in original, or do both
- AND the original cell is completely unaffected

### Requirement: No Exit Penalty

The system SHALL NOT penalize leaving.

#### Scenario: Return Welcome
- GIVEN Maria left the community 3 months ago
- WHEN Maria wants to rejoin
- THEN she can rejoin (subject to normal vouch requirements)
- AND her previous history is NOT held against her
- AND no "left before" flag exists

## Data Model

```python
class ExitRequest(BaseModel):
    user_id: str
    requested_at: datetime
    export_type: Literal["data_only", "with_connections", "fork"]
    status: Literal["pending", "processing", "complete"]

class ConnectionExportConsent(BaseModel):
    requester_id: str
    connection_id: str
    asked_at: datetime
    response: Optional[Literal["allow", "deny"]]
    responded_at: Optional[datetime]

class ForkInvitation(BaseModel):
    fork_id: str
    inviter_id: str
    invitee_id: str
    status: Literal["pending", "accepted", "declined"]
    # Declined invitations are deleted after 30 days
```

## Privacy Guarantees

**Your data belongs to you:**
- Profile, offers, needs, exchanges, vouches
- Always exportable
- No permission needed from community

**Connections require consent:**
- You can't export someone else's contact info without asking
- Declined = you get your side only

**No exit surveillance:**
- No "exit interview" required
- No record of why you left (unless you want to make a statement)
- No "left_community_count" tracking

## Implementation

### Phase 1: Data Export
- Export button in settings
- Generate SQLite bundle
- Include all personal data

### Phase 2: Connection Portability
- Request consent workflow
- Export with consented connections
- Clear messaging: "Bob agreed to stay connected"

### Phase 3: Community Fork
- "Fork Community" button
- Create new cell
- Invite workflow

### Phase 4: Import
- Import data to new community
- Restore connections where both parties consent
- Resume history

## Exit Flow UI

```
┌─────────────────────────────────────────────┐
│  Leaving [Community Name]?                  │
├─────────────────────────────────────────────┤
│                                             │
│  We're sorry to see you go. Your choices:  │
│                                             │
│  📦 Export My Data                          │
│     Download everything that's yours        │
│     (profile, offers, exchanges, vouches)   │
│                                             │
│  🔗 Export With Connections                 │
│     Take your data + ask connections        │
│     if they want to stay linked             │
│                                             │
│  🍴 Fork Community                          │
│     Start a new community, invite who       │
│     you want, take your data with you       │
│                                             │
│  ❓ Just Leave                              │
│     Your data stays here (you can           │
│     export later if you change your mind)   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Note: You can always come back.     │   │
│  │ Leaving doesn't burn bridges.       │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

## Philosophical Foundation

**Bakunin on liberty:**
"The liberty of man consists solely in this, that he obeys the laws of nature because he has himself recognized them as such."

If you're in a community and the rules no longer feel like natural law to you, you have the right to leave. You have the right to take what's yours. You have the right to try again elsewhere.

**No lock-in:**
Capitalist platforms trap users with network effects. You stay because your friends are there, your data is there. We reject that. Your data is yours. Your relationships are yours (with consent). Freedom includes freedom to exit.

## Success Criteria

- [ ] Data export works in under 1 minute
- [ ] Exported SQLite is usable standalone
- [ ] Connection consent flow works
- [ ] Fork creates functional new cell
- [ ] No exit penalties exist
- [ ] Return path is smooth

## Dependencies

- Data model for offers, needs, exchanges, vouches
- Notification system (for consent requests)
- Cell creation (for fork)

## Notes

This is the anarchist escape hatch. If the commune becomes oppressive, you can leave. If you want to try a different approach, you can fork. Your freedom isn't held hostage by your data or your relationships.

Bakunin would approve.
