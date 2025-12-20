# Proposal: Steward Dashboard

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED - Dashboard with metrics, attention items, activity, celebrations
**Complexity:** 1 system
**Timeline:** WORKSHOP REQUIRED
**Implemented:** 2025-12-19

## Problem Statement

At the workshop, you'll have community leaders (stewards) who need to see what's happening in their cells. They need tools to:
- Onboard new members
- See pending proposals
- Track cell health
- Identify issues before they become problems
- Celebrate wins

Without this, stewards are flying blind.

## Proposed Solution

A dedicated dashboard for cell stewards that provides visibility and control.

### Dashboard Sections

```
┌─────────────────────────────────────────────────────┐
│  🏠 Downtown Collective                    [Settings]│
├─────────────────────────────────────────────────────┤
│                                                      │
│  📊 THIS WEEK                                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 12      │ │ 8       │ │ 5       │ │ 7       │   │
│  │ Members │ │ Offers  │ │ Matches │ │ Exchanges│   │
│  │ (+2)    │ │ Active  │ │ Made    │ │ Complete │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                      │
│  ⚡ NEEDS ATTENTION                                  │
│  ┌─────────────────────────────────────────────────┐│
│  │ 🔴 3 join requests pending                      ││
│  │ 🟡 2 proposals awaiting approval                ││
│  │ 🟡 1 member hasn't participated in 2 weeks      ││
│  │ 🟢 All clear on trust/safety                    ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  📬 RECENT ACTIVITY                                  │
│  • Alice offered "Garden tools" (2 hours ago)       │
│  • Bob and Carol completed exchange (yesterday)     │
│  • New member: Dave (vouched by Alice)              │
│                                                      │
│  🎉 GOOD VIBES                                       │
│  • 3 new members joined this week                   │
│  • First exchange between Downtown and Riverside!   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Requirements

### Requirement: At-a-Glance Health

The system SHALL show cell health at a glance.

#### Scenario: Morning Check-in
- GIVEN Maria is a steward of Downtown Collective
- WHEN Maria opens the steward dashboard
- THEN she immediately sees key metrics (members, active offers, recent matches)
- AND she sees any items needing attention (pending requests, stale proposals)
- AND she can drill into any section for details

### Requirement: Join Request Management

The system SHALL let stewards process join requests.

#### Scenario: New Member Request
- GIVEN someone requests to join the cell
- WHEN the steward opens "Pending Requests"
- THEN they see who is requesting
- AND who vouched for them
- AND their trust score
- AND their stated reason for joining
- AND they can approve, reject, or request more info

### Requirement: Proposal Queue

The system SHALL surface proposals needing steward attention.

#### Scenario: Pending Proposals
- GIVEN agents have created proposals affecting the cell
- WHEN the steward opens the proposal queue
- THEN they see proposals sorted by urgency
- AND they can approve, reject, or discuss each one
- AND they see who else needs to approve

### Requirement: Member Participation Visibility

The system SHALL help stewards notice members who haven't participated recently.

#### Scenario: Check-in Prompt
- GIVEN Dave hasn't posted offers, needs, or completed exchanges in 14 days
- WHEN the steward views the dashboard
- THEN they see a gentle flag: "Dave hasn't participated recently"
- AND they can send a check-in message
- AND this is framed as care, not surveillance

**What we track (functional data):**
- Offers posted
- Needs posted
- Exchanges completed

**What we DON'T track:**
- Login times
- Pages viewed
- Time spent in app
- "Last active" timestamps

### Requirement: Good Vibes Display

The system SHALL highlight community moments (not individual achievements).

#### Scenario: Community Moments
- GIVEN something good happened (new member, cross-cell connection)
- WHEN stewards view the dashboard
- THEN they see the moment noted
- AND focus is on community, not individual "scores"
- NOTE: No gamification of exchanges. Carol got her reward from the exchange itself.

### Requirement: Cross-Cell Visibility

The system SHALL show stewards what's happening in adjacent cells.

#### Scenario: Regional View
- GIVEN Downtown Collective is near Riverside Collective
- WHEN the steward toggles "Regional View"
- THEN they see aggregate activity in nearby cells
- AND they see cross-cell match opportunities
- AND they can reach out to other cell stewards

## Tasks

1. [ ] Design dashboard layout and components
2. [ ] Build metrics summary cards
3. [ ] Implement "Needs Attention" queue
4. [ ] Create join request management flow
5. [ ] Build proposal queue for stewards
6. [ ] Add member participation tracking (offers/needs/exchanges only - no login tracking)
7. [ ] Create good vibes display (community moments, NOT individual gamification)
8. [ ] Build regional/cross-cell view
9. [ ] Add cell settings management
10. [ ] Implement steward messaging tools

## Dependencies

- Local Cells proposal (cell data model)
- Web of Trust (for join request evaluation)
- Leakage Metrics (for value tracking)
- Agent proposals (for proposal queue)

## Risks

- **Surveillance creep:** Dashboard becomes Big Brother. Mitigation: Only track functional data (offers, needs, exchanges). Never track login times, browsing, or "activity". No individual contribution tracking.
- **Steward burnout:** Too many notifications. Mitigation: Configurable quiet hours, delegation.

## Success Criteria

- [ ] Steward can see cell health in <5 seconds
- [ ] Join requests are processed through dashboard
- [ ] Proposals are visible and actionable
- [ ] Community moments are visible (no individual gamification)
- [ ] Cross-cell opportunities are visible
