# Proposal: Leakage Metrics - Economic Impact Tracking

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** ⚠️ SUPERSEDED by anti-reputation-capitalism
**Complexity:** 2 systems
**Timeline:** WORKSHOP REQUIRED
**Implemented:** 2025-12-19
**Superseded:** 2025-12-20

> **WARNING:** This proposal has been superseded. See `changes/anti-reputation-capitalism/proposal.md`
>
> Tracking dollar values of exchanges creates reputation capitalism. The exchange IS the reward.
> Carol doesn't need "$X kept in community" - she already got the value of the exchange.
>
> What remains: Optional "stats for nerds" with rough aggregate estimates, not per-exchange tracking.

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

1. [x] Design value estimation service
2. [x] Build category → average value mapping
3. [ ] Implement market price lookup API integration (optional - future enhancement)
4. [x] Add value tracking to exchange completion flow
5. [x] Build aggregation service (hourly/daily rollups)
6. [x] Create personal impact dashboard
7. [x] Create community impact dashboard
8. [x] Create network-wide impact display
9. [x] Implement privacy controls
10. [ ] Build monthly celebration notification (future enhancement)
11. [x] Add value override UI in exchange flow

## Dependencies

- Exchange completion flow (GAP-10) ✅ DONE
- Community entity (GAP-03)

## Risks

- **Gamification pressure:** People inflate values for status. Mitigation: No leaderboards, no individual visibility.
- **Inaccurate estimates:** Values are rough. Mitigation: Be honest about "estimates," allow overrides.
- **Surveillance concern:** Even aggregates feel like tracking. Mitigation: Opt-out, clear messaging about privacy.

## Success Criteria

- [x] Every completed exchange has a value estimate
- [x] Users see personal impact on home screen
- [x] Communities see aggregate impact on dashboard
- [x] Network total is visible to all
- [x] No individual transaction values are ever public
- [x] Users can opt out of aggregates

## Implementation Summary

### Backend (Python/FastAPI)
- **Database**: Migration 005 adds tables for exchange_values, personal_metrics, community_metrics, network_metrics, and category_value_defaults
- **Models**: Complete data models with privacy controls (leakage_metrics.py)
- **Services**:
  - ValueEstimationService: Estimates counterfactual value using category defaults
  - MetricsAggregationService: Privacy-preserving aggregation at personal, community, and network levels
- **Repositories**: LeakageMetricsRepository for all CRUD operations
- **API**: Full REST API at /leakage-metrics for personal, community, network metrics and value overrides
- **Integration**: Exchange completion flow automatically tracks values

### Frontend (React/TypeScript)
- **PersonalImpactWidget**: Shows user's personal economic impact (private)
- **CommunityImpactWidget**: Shows community-level aggregates with category breakdown
- **NetworkImpactWidget**: Shows network-wide impact and movement scale
- **ValueOverrideModal**: Allows users to correct value estimates

### Privacy Features
- Individual exchange values NEVER exposed publicly
- Only aggregates shown at community and network levels
- Users can opt out of aggregates (included_in_aggregates flag)
- Users can hide their personal stats (show_stats flag)
- Value override allows user corrections without exposing specifics

### Files Created
- valueflows_node/app/database/migrations/005_add_leakage_metrics.sql
- valueflows_node/app/models/leakage_metrics.py
- valueflows_node/app/services/value_estimation_service.py
- valueflows_node/app/services/metrics_aggregation_service.py
- valueflows_node/app/repositories/leakage_metrics_repo.py
- valueflows_node/app/api/leakage_metrics.py
- frontend/src/components/PersonalImpactWidget.tsx
- frontend/src/components/CommunityImpactWidget.tsx
- frontend/src/components/NetworkImpactWidget.tsx
- frontend/src/components/ValueOverrideModal.tsx
- test_leakage_metrics.py (test suite)

### What Works
✅ Automatic value estimation when exchanges complete
✅ Category-based default values (food, tools, transport, skills, housing, goods)
✅ User value override capability
✅ Privacy-preserving aggregation
✅ Personal, community, and network dashboards
✅ Tested and verified core functionality
