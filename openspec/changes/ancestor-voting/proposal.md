# Proposal: Ancestor Voting

**Submitted By:** Philosopher Council (hooks + Bakunin)
**Date:** 2025-12-19
**Status:** DRAFT
**Complexity:** 2 systems
**Timeline:** PHILOSOPHICAL

## Problem Statement

Reputation systems create power hierarchies. The person with the most "contribution points" becomes the de facto leader. Long-term members accumulate influence, while newcomers and marginalized voices struggle to be heard.

Traditional solutions:
- Remove reputation entirely → No way to assess trustworthiness
- Cap reputation → Punishes genuine contribution
- Time decay → Dismisses wisdom gained through experience

**How do we use accumulated reputation to amplify marginalized voices instead of concentrating power?**

## Proposed Solution

The "Ghost in the Shell" protocol - when members leave or die, their reputation doesn't disappear. It becomes a **Memorial Fund** that can be spent by the community to boost proposals from marginalized members.

### Mechanism

When a user departs (voluntarily leaves, dies, or is removed):
1. Their public contributions (code, art, guides) remain in the **Common Heap**
2. Their reputation score is transferred to a **Memorial Fund**
3. This "Ghost Reputation" can be "spent" by stewards to boost specific proposals
4. Priority: Proposals from new members, marginalized voices, or controversial ideas
5. The ancestors vote for the voiceless

### As Bakunin said: "The only good authority is a dead one."

## Requirements

### Requirement: Memorial Fund Creation

The system SHALL create Memorial Funds from departed members.

#### Scenario: Member Departs
- GIVEN a member leaves the network (voluntary exit, death, or removal)
- WHEN their departure is confirmed
- THEN their reputation score is calculated
- AND a Memorial Fund is created with that reputation value
- AND their public contributions remain accessible
- AND their private data is purged per privacy policy

### Requirement: Ghost Reputation Allocation

The system SHALL allow stewards to allocate Ghost Reputation.

#### Scenario: Boosting a Marginalized Proposal
- GIVEN a proposal from a new/marginalized member
- AND the proposal is struggling to get visibility
- WHEN a steward allocates Ghost Reputation to it
- THEN the proposal receives a visibility boost
- AND the Memorial Fund is decremented
- AND the allocation is logged publicly

### Requirement: Prioritize Marginalized Voices

The system SHALL prioritize Ghost Reputation for specific use cases.

#### Scenario: Allocation Rules
- GIVEN Ghost Reputation is being allocated
- THEN priority goes to:
  - Proposals from members with <3 months tenure
  - Proposals from members with low existing reputation
  - Proposals flagged as "controversial but important"
  - Proposals from marginalized identity groups (if disclosed)
- AND allocations to already-popular proposals are rejected

### Requirement: Transparency

The system SHALL make all allocations transparent.

#### Scenario: Public Ledger
- GIVEN Ghost Reputation has been allocated
- WHEN anyone views the Memorial Fund
- THEN they see all allocations: who allocated, to which proposal, for what reason
- AND they see the current fund balance
- AND they see whose reputation contributed to the fund

### Requirement: Memorial Contribution Tracking

The system SHALL track which ancestors boosted which proposals.

#### Scenario: Ancestor Attribution
- GIVEN a proposal received Ghost Reputation
- WHEN it is approved and implemented
- THEN the ancestors whose reputation was used are credited
- AND their memorial page shows the impact of their legacy
- AND the community remembers who amplified this voice

### Requirement: Refund Mechanism

The system SHALL refund unused Ghost Reputation.

#### Scenario: Proposal Rejected
- GIVEN a proposal received Ghost Reputation boost
- AND the proposal was ultimately rejected
- WHEN the rejection is confirmed
- THEN the allocated Ghost Reputation returns to the Memorial Fund
- AND it can be reallocated to other proposals

### Requirement: Anti-Abuse Protections

The system SHALL prevent abuse of Ghost Reputation.

#### Scenario: Preventing Gaming
- GIVEN a steward is allocating Ghost Reputation
- THEN they cannot allocate to their own proposals
- AND they cannot allocate >20% of the fund to a single proposal
- AND they must provide a written justification
- AND other stewards can veto allocations within 24 hours

## Implementation Plan

### Phase 1: Memorial Fund Infrastructure
1. Schema for Memorial Funds, Ghost Reputation allocations
2. Departure detection and fund creation
3. Public contribution archiving

### Phase 2: Allocation System
1. Steward interface for allocating Ghost Reputation
2. Priority scoring for marginalized proposals
3. Allocation logging and transparency

### Phase 3: Attribution and Legacy
1. Memorial pages showing ancestor impact
2. Proposal attribution to ancestors
3. Community recognition of ancestor contributions

### Phase 4: Anti-Abuse
1. Allocation limits and justification requirements
2. Steward veto system
3. Audit trail and accountability

## Data Model

### Memorial Fund
```python
{
    "id": "memorial-fund-uuid",
    "created_from_user_id": "user-uuid",
    "departed_user_name": "Alice Chen",
    "initial_reputation": 450.0,
    "current_balance": 450.0,
    "created_at": "2025-12-19T...",
    "allocations": [...]
}
```

### Ghost Reputation Allocation
```python
{
    "id": "allocation-uuid",
    "fund_id": "memorial-fund-uuid",
    "proposal_id": "proposal-uuid",
    "amount": 50.0,
    "allocated_by": "steward-uuid",
    "reason": "New member with important accessibility proposal",
    "allocated_at": "2025-12-19T...",
    "refunded": false
}
```

## Privacy Considerations

- Departed members' private data is purged
- Only public contributions are retained
- Memorial pages honor privacy settings (e.g., anonymous contributions)
- Families can request removal of deceased member's memorial

## Risks

- **Steward Favoritism:** Stewards allocate to friends' proposals. Mitigation: Transparent logging, veto system, justification requirements.
- **Reputation Inflation:** Too much Ghost Reputation creates unfair advantages. Mitigation: Allocation caps, priority rules.
- **Grief Exploitation:** Using death for political gain. Mitigation: Waiting period after departure, community oversight.
- **Memorial Exhaustion:** Fund runs out too quickly. Mitigation: Replenishment from network fees/donations, careful allocation.

## Success Criteria

- [ ] Memorial Funds created automatically when members depart
- [ ] Stewards can allocate Ghost Reputation with justification
- [ ] Allocations prioritize marginalized voices
- [ ] All allocations are publicly logged
- [ ] Memorial pages show ancestor impact
- [ ] Refunds work for rejected proposals
- [ ] Anti-abuse protections prevent gaming

## Dependencies

- User departure system
- Proposal/governance system
- Reputation tracking system
- Steward permission system

## Philosophical Foundation

**bell hooks:** "Marginality [is] much more than a site of deprivation... it is also the site of radical possibility." Ghost Reputation makes marginality a site of power by channeling ancestral authority to the margins.

**Mikhail Bakunin:** "The only good authority is a dead one." Dead authority cannot accumulate power, demand loyalty, or create cults of personality. It can only serve.

**The Point:** In most systems, reputation dies with the person or concentrates in their heirs. Here, reputation returns to the commons and serves those who need it most. The dead protect the living by amplifying voices the powerful would rather silence.

This is not a gimmick. This is how we prevent meritocracy from becoming oligarchy.

## Notes

This proposal is philosophically ambitious. It asks:
- Can reputation serve liberation instead of hierarchy?
- Can death be a form of service?
- Can the ancestors vote?

If it makes you uncomfortable, good. That means it's touching something real.

Build accordingly.
