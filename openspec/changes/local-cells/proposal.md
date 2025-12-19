# Proposal: Local Cells (Molecules)

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED - Full stack complete: backend API + frontend UI
**Complexity:** 2 systems
**Timeline:** WORKSHOP REQUIRED
**Implemented:** 2025-12-19

## Problem Statement

500,000 people cannot coordinate as a single group. The network must be organized into local cells ("molecules") of 5-50 people who can actually meet in person, share resources physically, and build real trust.

The platform's job is to help people find and form these local cells, then help cells federate into larger networks.

## Proposed Solution

A hierarchical but non-authoritarian structure:

```
Network (millions)
    └── Region (thousands)
            └── Cell/Molecule (5-50 people who can meet IRL)
                    └── Individual
```

### Cell Characteristics

- **Geographic proximity:** Members can physically reach each other
- **Human scale:** Small enough that everyone knows everyone (Dunbar's number: ~50 max)
- **Self-governing:** Each cell sets its own norms within network principles
- **Federated:** Cells connect to share resources across boundaries
- **Resilient:** If a cell is compromised, others continue

### Cell Formation Paths

1. **Organic:** Friends vouch friends until a cluster forms
2. **Geographic:** "Find people near me" → auto-suggest cell formation
3. **Existing:** Import an existing group (neighborhood, co-op, etc.)
4. **Event-based:** People at same event/workshop form a cell

## Requirements

### Requirement: Cell Discovery

The system SHALL help users find or form local cells.

#### Scenario: Find My People
- GIVEN Alice is a trusted member without a cell
- WHEN Alice opens "Find Local Cell"
- THEN she sees cells within her geographic area accepting new members
- AND she sees trusted members near her who aren't in a cell yet
- AND she can request to join an existing cell or propose forming a new one

### Requirement: Cell Formation

The system SHALL support creating new cells.

#### Scenario: Starting a Molecule
- GIVEN Alice, Bob, and Carol are trusted members in the same area
- WHEN Alice proposes forming "Downtown Collective"
- THEN Bob and Carol receive invitations
- AND when all three accept, the cell is formed
- AND they become the founding members with steward capabilities

### Requirement: Cell Boundaries

The system SHALL scope activities to cells by default.

#### Scenario: Local First
- GIVEN Alice is in "Downtown Collective"
- WHEN Alice posts an offer
- THEN the offer is visible to her cell first
- AND after 24 hours (or immediately if she chooses), it's visible to adjacent cells
- AND network-wide visibility is opt-in

### Requirement: Inter-Cell Sharing

The system SHALL enable resource sharing between cells.

#### Scenario: Cross-Cell Match
- GIVEN Downtown Collective has excess tomatoes
- AND Riverside Collective needs tomatoes
- WHEN the agents detect this match
- THEN a cross-cell proposal is created
- AND stewards from both cells can approve
- AND the exchange is facilitated

### Requirement: Cell Autonomy

The system SHALL allow cells to set their own rules.

#### Scenario: Cell Configuration
- GIVEN Downtown Collective's stewards
- WHEN they access cell settings
- THEN they can configure:
  - Minimum trust score to join (default 0.5)
  - Vouch requirements for membership
  - Default offer visibility scope
  - Meeting frequency reminders
  - Cell-specific resource categories

### Requirement: Steward Roles

The system SHALL support distributed cell leadership.

#### Scenario: Steward Rotation
- GIVEN a cell has been active for 3 months
- WHEN the rotation period arrives
- THEN steward role is offered to active members
- AND no single person can be permanent steward (term limits)
- AND the Counter-Power agent monitors for steward concentration

## Data Model

```python
class Cell:
    id: str
    name: str
    description: str
    location: GeoPoint          # Approximate center
    radius_km: float            # Coverage area
    created_at: datetime
    member_count: int
    settings: CellSettings
    steward_ids: List[str]      # Current stewards

class CellMembership:
    cell_id: str
    user_id: str
    joined_at: datetime
    role: str                   # "member", "steward"
    vouched_by: str             # Who vouched them into this cell

class CellSettings:
    min_trust_to_join: float
    offer_default_scope: str    # "cell", "region", "network"
    vouch_requirement: str      # "any_member", "steward_only", "consensus"
    max_members: int
    steward_term_days: int
```

## Tasks

1. [ ] Design Cell data model and storage
2. [ ] Implement cell creation flow
3. [ ] Build cell discovery by location
4. [ ] Create cell membership management
5. [ ] Implement steward role and permissions
6. [ ] Build cell settings UI
7. [ ] Create inter-cell offer visibility logic
8. [ ] Implement cross-cell matching
9. [ ] Build cell dashboard for stewards
10. [ ] Add term limits and rotation for stewards
11. [ ] Integrate with Counter-Power agent for hierarchy detection

## Dependencies

- Web of Trust (vouching determines who can join)
- Community entity (GAP-03) - cells ARE communities
- Location services (for geographic discovery)

## Risks

- **Cell isolation:** Cells become islands. Mitigation: Active cross-cell matching, regional gatherings.
- **Cliques:** Cells reject outsiders unfairly. Mitigation: Minimum acceptance requirements, appeals process.
- **Steward capture:** One person dominates. Mitigation: Term limits, Counter-Power monitoring.

## Success Criteria

- [ ] Users can discover cells near them
- [ ] Users can form new cells with trusted contacts
- [ ] Offers default to cell scope, expand on demand
- [ ] Cross-cell matching works
- [ ] Steward rotation is enforced
- [ ] Cells can set their own rules within bounds
