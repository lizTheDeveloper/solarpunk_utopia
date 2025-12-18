# Proposal: Insurrectionary Joy Agent

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** Draft
**Complexity:** 2 systems

## Problem Statement

Utopian projects often fail due to "audit culture" and bureaucratic burnout. If the revolution is boring, no one will come. Following Emma Goldman ("If I can't dance, I don't want to be part of your revolution"), we need systemic safeguards against joylessness. We need to prioritize pleasure, spontaneity, and celebration as critical infrastructure.

## Proposed Solution

A **Insurrectionary Joy Agent** that acts as a "party whip" but for fun.

1.  **Joy Metric**: Tracks the ratio of "Work Events" to "Social/Play Events".
2.  **Frictionless Input ("Vibe Check")**:
    *   **Dance Protocol**: If 3+ phones are syncing music, it counts as Play.
    *   **The Dinner Bell**: Intelligent "Meal Invite" that pings neighbors until food is claimed.
    *   **Local Social Proprioception**: Devices privately count Bluetooth proximity density. If a user is "high density" (social) or "low density" (hermit mode), this state is stored *locally*.
3.  **Opt-in Intervention**: The Agent can query the local state *with permission*. If Local State = "Low Density" (Sad/Isolated), it prompts: "Hey, want a dance party?"
4.  **Bureaucracy Jammer**: If a meeting goes over 90 minutes, the agent intervenes.

## Requirements

### Requirement: Joy Metric Limits

The system SHALL enforce a maximum limit on consecutive work without play.

#### Scenario: Joy Strike
- WHEN the community has logged 500 hours of work without a "Party" event
- THEN the Matchmaker Agent stops accepting new "Work" proposals
- UNTIL a "Party" proposal is ratified and executed.

### Requirement: Spontaneous Synchronization

The system SHALL support multi-device audio syncing for instant parties.

#### Scenario: The Drop
- WHEN a user initiates "Protocol: Dance"
- THEN all nearby consenting phones download the same track
- AND play it in perfect sync (using NTP/DTN ticks)

## Dependencies

- **ValueFlows Node**: To count Work vs Play events.
- **Audio Subsystem**: For the dance party sync.

## Risks

- **Disruption**: Important work might be interrupted. Mitigation: "Critical Path" override for emergencies (e.g. food harvest, medical).

## Alternatives Considered

- **Scheduled Fun**: "Mandatory Fun Day". Rejected. Joy must be insurrectionary and spontaneous, not just scheduled.
