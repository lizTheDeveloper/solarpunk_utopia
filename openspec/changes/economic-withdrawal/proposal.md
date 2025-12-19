# Proposal: Economic Withdrawal - Coordinated Wealth Deconcentration

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** STRATEGIC
**Complexity:** 3 systems
**Timeline:** POST-WORKSHOP (but design now)

## Problem Statement

Individual gift economy transactions are nice. But we're not here to be nice. We're here to put a dent in the extractive economy.

The goal isn't just "share more" - it's coordinated withdrawal of economic activity from corporations and redirecting it to community. This is economic strike as praxis.

## Proposed Solution

A system for coordinating economic withdrawal campaigns - collective action to redirect spending from extractive to regenerative systems.

### Campaign Types

| Campaign | Target | Mechanism |
|----------|--------|-----------|
| **Amazon Exit** | Amazon.com | Collective commitment to buy nothing from Amazon for X days |
| **Local Food Shift** | Grocery chains | 50% grocery spending redirected to local/community sources |
| **Tool Library** | Hardware stores | Shared tools eliminate individual purchases |
| **Skill Share** | Credentialing industry | Free skill exchange replaces paid training |
| **Housing Mutual Aid** | Landlords/Hotels | Room shares, land access, housing co-ops |
| **Transport Commons** | Uber/Auto industry | Ride shares, bike collectives, car co-ops |

### Coordination Mechanics

1. **Campaign Creation:** Steward proposes campaign with target, goal, duration
2. **Commitment Gathering:** Members pledge participation
3. **Threshold Activation:** Campaign activates when threshold met (e.g., 1000 participants)
4. **Execution Support:** Platform helps members fulfill commitments (matches for alternatives)
5. **Impact Tracking:** Measure actual economic shift
6. **Celebration:** Campaign success celebrated, metrics shared

## Requirements

### Requirement: Campaign Framework

The system SHALL support creating and coordinating economic campaigns.

#### Scenario: Amazon Exit Campaign
- GIVEN Downtown Collective wants to coordinate an Amazon boycott
- WHEN a steward creates the "No Amazon November" campaign
- THEN members can view the campaign and pledge participation
- AND they see how many others have pledged
- AND the campaign activates when 100 members commit
- AND the platform surfaces local alternatives for common Amazon purchases

### Requirement: Commitment Tracking

The system SHALL track campaign commitments.

#### Scenario: Pledge Tracking
- GIVEN Maria pledges to participate in No Amazon November
- WHEN November arrives
- THEN she receives gentle reminders
- AND can log her "almost bought on Amazon but didn't" moments
- AND sees her personal impact estimate
- AND sees collective campaign impact

### Requirement: Alternative Matching

The system SHALL help participants find alternatives.

#### Scenario: Need Something?
- GIVEN Carlos needs batteries during No Amazon November
- WHEN he opens the app
- THEN he sees: "Need something? Check if someone has it before buying"
- AND can post a need for batteries
- AND is matched with someone who has batteries to share
- OR sees local stores as alternatives

### Requirement: Economic Impact Calculation

The system SHALL estimate economic impact.

#### Scenario: Campaign Results
- GIVEN No Amazon November has concluded
- WHEN viewing campaign results
- THEN members see:
  - Total pledged participants: 2,340
  - Estimated spending redirected: $127,000
  - Local transactions facilitated: 890
  - Network value circulated: $34,000
- AND this is celebrated as a collective victory

### Requirement: Corporate Replacement Mapping

The system SHALL map extractive services to community alternatives.

#### Scenario: Replacement Guide
- GIVEN a new member wants to reduce Amazon dependence
- WHEN they view the "Extraction Exit" guide
- THEN they see categories of spending
- AND for each: network alternatives (tool library, food shares, etc.)
- AND local alternatives (local stores, co-ops)
- AND they can track their personal "exit progress"

### Requirement: Collective Bargaining

The system SHALL support group purchasing.

#### Scenario: Bulk Buy Coordination
- GIVEN 50 members all need bulk rice
- WHEN a steward creates a bulk buy campaign
- THEN members commit to quantities
- AND the collective order gets wholesale pricing
- AND distribution is coordinated through the network
- AND per-unit cost is lower than retail

## Economic Targets

### Phase 1: Easy Exits
- Amazon → Local shops + network sharing
- DoorDash → Community meals + food sharing
- Uber → Ride sharing + transport co-ops

### Phase 2: Infrastructure Shifts
- Grocery chains → CSAs + community gardens + food co-ops
- Hardware stores → Tool libraries + skill shares
- Big Box retail → Goods circulation + repair cafes

### Phase 3: Structural Changes
- Rent → Housing co-ops + land trusts
- Health insurance → Mutual aid health funds
- Banking → Credit unions + time banks

## Tasks

1. [ ] Design campaign data model
2. [ ] Build campaign creation flow for stewards
3. [ ] Implement pledge/commitment system
4. [ ] Create campaign activation thresholds
5. [ ] Build alternative matching during campaigns
6. [ ] Implement economic impact estimation
7. [ ] Create extraction exit guide content
8. [ ] Build bulk buy coordination feature
9. [ ] Design campaign celebration moments
10. [ ] Create "personal exit progress" tracker
11. [ ] Build campaign analytics dashboard

## Dependencies

- Local Cells (campaign scope)
- Leakage Metrics (impact tracking)
- Matching system (alternative finding)

## Risks

- **Commitment decay:** People pledge but don't follow through. Mitigation: Gentle reminders, buddy system, celebration of participation not perfection.
- **Alternative gaps:** Network can't meet all needs. Mitigation: Be honest about gaps, map local alternatives, prioritize building capacity.
- **Retaliation:** Corporations notice and respond. Mitigation: Decentralized coordination, no public claims until impact is clear.

## Success Metrics

- Campaigns reaching activation threshold
- Pledges fulfilled rate (>70%)
- Estimated spending redirected per campaign
- Member "exit progress" over time
- Trend in network value circulation

## Philosophical Anchor

> "Every transaction in the gift economy is a transaction that DIDN'T go to Bezos."

This isn't about purity. It's about direction. Every dollar that stays in community is a dollar drained from the machine.

## Success Criteria

- [ ] Stewards can create economic campaigns
- [ ] Members can pledge participation
- [ ] Campaigns activate at threshold
- [ ] Alternative matching works during campaigns
- [ ] Economic impact is estimated and displayed
- [ ] Campaigns feel like collective action, not individual guilt
