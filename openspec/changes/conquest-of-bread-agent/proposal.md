# Proposal: Conquest of Bread Agent

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** FULLY IMPLEMENTED
**Complexity:** 2 systems
**Completed:** 2025-12-21
**Note:** Backend agent implementation complete with abundance/rationing logic. Now queries real ValueFlows database for resource inventory and calculates consumption rates. Falls back to mock data if db_client unavailable.

## Problem Statement

Accounting for every tomato is counter-revolutionary. As Kropotkin argued, "Well-Being for All" is the goal, not a balanced ledger. We need a system that defaults to abundance ("The Common Heap") and only triggers rationing/accounting when absolutely necessary.

## Proposed Solution

A **Conquest of Bread Agent** that dynamically toggles the "Economic Mode" of the commune.

1.  **The Common Heap**: If a resource is abundant (Supply > Demand * 1.5), the agent disables transaction logging for that resource. You just take it. No "Offer/Need" match required.
2.  **Needs-First Rationing**: If Supply drops below Demand, the agent switches to "Rationing Mode," prioritizing requests labeled "Survival Need" (food, medicine) over "Comfort Need."
3.  **Well-Being Index**: Tracks the satisfaction of basic needs across the whole population, not just individuals.

## Requirements

### Requirement: Abundance Trigger

The system SHALL disable accounting for resources exceeding the abundance threshold.

#### Scenario: Summer Tomato Harvest
- WHEN Tomato inventory > 500kg AND Weekly consumption < 100kg
- THEN Toggle Resource:Tomato to "Heap Mode" (No logging required for pickup)

### Requirement: Scarcity Rationing

The system SHALL enforce prioritization when scarcity is detected.

#### Scenario: Winter Scarcity
- WHEN Firewood inventory < 2 weeks supply
- THEN Reject all "Bonfire Party" requests
- AND Only auto-approve "Home Heating" requests

## Dependencies

- **ValueFlows Node**: To monitor inventory levels.
- **Mycelial Health Monitor**: To know if "Heap Mode" is causing waste/rot.

## Risks

- **Tragedy of the Commons**: People taking too much. Mitigation: "Heap Mode" reverts instantly if stock drops rapidly.

## Alternatives Considered

- **Always-On Accounting**: Too capitalist. Creates unnecessary friction.
