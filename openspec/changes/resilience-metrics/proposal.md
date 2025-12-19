# Proposal: Resilience Metrics

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** HIGH PRIORITY
**Complexity:** 2 systems
**Timeline:** POST-WORKSHOP

## Problem Statement

How do we know if the network is working? Not just "are there users" but:
- Are cells healthy or dying?
- Are resources actually flowing?
- Are we building real resilience or just LARPing?
- Where are the weak points an adversary could exploit?

We need metrics that measure what matters: the network's ability to sustain itself and its members under pressure.

## Proposed Solution

A resilience dashboard that measures network health across multiple dimensions.

### Resilience Dimensions

| Dimension | What It Measures | Healthy Threshold |
|-----------|------------------|-------------------|
| **Density** | Connections per person | >3 trusted connections |
| **Flow** | Resources actually moving | >1 exchange per member per month |
| **Redundancy** | Multiple paths exist | No single point of failure |
| **Velocity** | Speed of resource matching | <24 hours offer→match |
| **Recovery** | Bounce back from disruption | Cells reform within 1 week |
| **Coverage** | Needs being met | >80% needs matched |
| **Decentralization** | No power concentration | No node >10% of activity |

### Views

1. **Network Health:** Overall resilience score and trends
2. **Cell Health:** Per-cell breakdown (for stewards)
3. **Regional Gaps:** Geographic weak spots
4. **Threat Surface:** Potential vulnerabilities

## Requirements

### Requirement: Network Health Dashboard

The system SHALL provide network-wide health visibility.

#### Scenario: Daily Check
- GIVEN a steward opens the resilience dashboard
- THEN they see overall network score (0-100)
- AND breakdown by dimension
- AND trend over last 30 days
- AND alerts for any dimension below threshold

### Requirement: Cell Health Indicators

The system SHALL show cell-level health.

#### Scenario: Cell Diagnosis
- GIVEN a cell steward wants to assess their cell
- WHEN they view cell health
- THEN they see: active members, resource flow rate, match velocity
- AND comparison to network averages
- AND specific suggestions ("Your cell needs more tool offers")

### Requirement: Redundancy Analysis

The system SHALL identify single points of failure.

#### Scenario: Vulnerability Scan
- GIVEN the network has grown organically
- WHEN an admin runs vulnerability scan
- THEN they see nodes that are "too important" (>10% of vouches, resources, or activity)
- AND edges that if removed would isolate cells
- AND suggestions for adding redundancy

### Requirement: Flow Analysis

The system SHALL track actual resource movement.

#### Scenario: Flow Map
- GIVEN the admin wants to see resource flows
- WHEN they view the flow dashboard
- THEN they see aggregate flows between cells (not individual transactions)
- AND identify cells that are "takers" vs "givers"
- AND spot imbalances before they become problems

### Requirement: Threat Modeling

The system SHALL model resilience under attack.

#### Scenario: "What If" Analysis
- GIVEN a steward wants to test resilience
- WHEN they run a scenario ("What if Alice is compromised?")
- THEN they see the impact on trust graph
- AND which members would be affected
- AND how quickly the network could recover

### Requirement: Geographic Coverage

The system SHALL identify coverage gaps.

#### Scenario: Coverage Map
- GIVEN the network spans a region
- WHEN viewing the coverage map
- THEN they see areas with active cells
- AND "cold spots" with no coverage
- AND suggested expansion priorities

## Metrics Definitions

### Density Score
```
density = avg(trusted_connections per member)
healthy = density >= 3
```

### Flow Score
```
flow_rate = exchanges_completed / active_members / days
healthy = flow_rate >= 1/30 (1 per month per member)
```

### Redundancy Score
```
redundancy = 1 - (max_node_centrality / total_nodes)
healthy = no single node > 10% of graph centrality
```

### Velocity Score
```
velocity = median(match_time - offer_time)
healthy = velocity <= 24 hours
```

### Coverage Score
```
coverage = needs_matched / needs_posted
healthy = coverage >= 0.8
```

## Tasks

1. [ ] Design resilience scoring algorithm
2. [ ] Build data collection for all metrics
3. [ ] Create network health dashboard UI
4. [ ] Build cell health view for stewards
5. [ ] Implement redundancy analysis (graph algorithms)
6. [ ] Create flow visualization (sankey diagram or similar)
7. [ ] Build threat modeling scenario runner
8. [ ] Create geographic coverage map
9. [ ] Implement alerts for unhealthy dimensions
10. [ ] Build trend tracking over time
11. [ ] Create "network diagnosis" report generator

## Dependencies

- Local Cells (cell data)
- Leakage Metrics (flow data)
- Web of Trust (trust graph data)
- Exchange system (completion data)

## Privacy Considerations

- All metrics are AGGREGATES - no individual visibility
- Cell-level data visible only to cell stewards
- Network-level data visible to all members
- Threat modeling does not expose individual connections

## Risks

- **Gaming:** People inflate metrics for status. Mitigation: Metrics measure flow, not volume. Quality over quantity.
- **Surveillance:** Metrics reveal network structure. Mitigation: Aggregates only, no individual data, local computation.
- **Anxiety:** Metrics stress people out. Mitigation: Frame as health check, not judgment.

## Success Criteria

- [ ] Network health score computable in real-time
- [ ] Cell stewards can see their cell's health
- [ ] Single points of failure are identified
- [ ] Geographic gaps are visible
- [ ] Trends show network trajectory
- [ ] All metrics preserve privacy (aggregates only)
