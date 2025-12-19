# Proposal: Leakage Metrics - Economic Impact Tracking

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** CRITICAL PATH
**Complexity:** 2 systems
**Timeline:** WORKSHOP REQUIRED

## Problem Statement

The gift economy isn't just about warm feelings. It's economic warfare. Every transaction that happens in the mesh is a transaction that DIDN'T go to Amazon, Walmart, Uber, or landlords.

We need to measure this. Not for vanity metrics, but to prove the model works and to motivate participation. When someone sees "Your community kept $47,000 local this month," they understand they're part of something real.

## Proposed Solution

Track the **counterfactual economic value** of gift economy transactions.

### What We Measure

| Transaction Type | Counterfactual | How We Estimate |
|-----------------|----------------|-----------------|
| Tool share | Would have bought/rented | Market price lookup or user input |
| Food share | Would have bought groceries | Average grocery prices by category |
| Ride share | Would have paid Uber/Lyft | Distance × avg rideshare rate |
| Skill share | Would have hired someone | Hourly rate by skill category |
| Space share | Would have paid rent/hotel | Local housing rates |
| Goods share | Would have bought new | Retail price or user estimate |

### Aggregation Levels

1. **Personal:** "You've kept $340 in community this month"
2. **Cell/Molecule:** "Oak Street Collective circulated $12,400 this month"
3. **Network:** "The mesh kept $2.3M out of extractive systems this month"

### Privacy Preservation

- Individual transaction values are NEVER public
- Only aggregates shown at cell level and above
- User can hide their personal stats
- No leaderboards (Goldman's critique)

## Requirements

### Requirement: Value Estimation

The system SHALL estimate economic value of transactions.

#### Scenario: Tool Share Valuation
- GIVEN Alice shares her power drill with Bob
- WHEN the exchange is completed
- THEN the system estimates value ($50 purchase price or $15 rental)
- AND records this as "leakage prevented"
- AND adds to both personal and community aggregates

### Requirement: Privacy-Preserving Aggregates

The system SHALL protect individual transaction privacy while showing community impact.

#### Scenario: Community Dashboard
- GIVEN Oak Street Collective has 47 members
- WHEN a steward views the community dashboard
- THEN they see total value circulated this month
- AND they see breakdown by category (food, tools, rides, etc.)
- BUT they cannot see individual member contributions
- AND they cannot see specific transaction values

### Requirement: User Control

The system SHALL let users control their visibility.

#### Scenario: Privacy Settings
- GIVEN Alice is a member
- WHEN she visits settings
- THEN she can toggle "Show my impact stats" on/off
- AND she can toggle "Include my transactions in aggregates" on/off

### Requirement: Counterfactual Calibration

The system SHALL allow users to correct valuations.

#### Scenario: User Override
- GIVEN Bob received a "vintage synthesizer" marked as $50
- WHEN Bob knows it's actually worth $800
- THEN Bob can adjust the recorded value
- AND the system learns better valuations over time

### Requirement: Inspiring Display

The system SHALL present impact in motivating ways.

#### Scenario: Monthly Celebration
- GIVEN it's the first of the month
- WHEN users open the app
- THEN they see a celebration: "Last month, you kept $X local!"
- AND they see their community's impact
- AND they see the network-wide impact
- AND this feels like a victory, not surveillance

## Data Model

```python
class ExchangeValue:
    exchange_id: str
    category: str           # food, tools, transport, skills, housing, goods
    estimated_value: float  # In local currency
    estimation_method: str  # "market_lookup", "user_input", "category_average"
    user_override: Optional[float]
    final_value: float
    included_in_aggregates: bool  # User privacy choice

class CommunityMetrics:
    community_id: str
    period: str            # "2025-01", "2025-W03", "2025-12-18"
    total_value: float
    transaction_count: int
    by_category: Dict[str, float]
    member_count: int      # For per-capita calculations
```

## Tasks

1. [ ] Design value estimation service
2. [ ] Build category → average value mapping
3. [ ] Implement market price lookup API integration (optional)
4. [ ] Add value tracking to exchange completion flow
5. [ ] Build aggregation service (hourly/daily rollups)
6. [ ] Create personal impact dashboard
7. [ ] Create community impact dashboard
8. [ ] Create network-wide impact display
9. [ ] Implement privacy controls
10. [ ] Build monthly celebration notification
11. [ ] Add value override UI in exchange flow

## Dependencies

- Exchange completion flow (GAP-10) ✅ DONE
- Community entity (GAP-03)

## Risks

- **Gamification pressure:** People inflate values for status. Mitigation: No leaderboards, no individual visibility.
- **Inaccurate estimates:** Values are rough. Mitigation: Be honest about "estimates," allow overrides.
- **Surveillance concern:** Even aggregates feel like tracking. Mitigation: Opt-out, clear messaging about privacy.

## Success Criteria

- [ ] Every completed exchange has a value estimate
- [ ] Users see personal impact on home screen
- [ ] Communities see aggregate impact on dashboard
- [ ] Network total is visible to all
- [ ] No individual transaction values are ever public
- [ ] Users can opt out of aggregates
