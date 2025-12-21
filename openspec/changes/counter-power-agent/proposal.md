# Proposal: Counter-Power Agent

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** FULLY IMPLEMENTED
**Completed:** 2025-12-21
**Note:** Backend agent implementation complete. Now queries real ValueFlows database: detects resource warlords from offer patterns, identifies silent members from listing activity, tracks contribution patterns. All with graceful fallback to mock data.
**Complexity:** 2 systems

## Problem Statement

Hierarchy is a weed that grows whenever vigilance sleeps. Even in a "flat" structure, power tends to accumulate in the hands of the administrative class (system admins, facilitators). Consistent with Bakunin's anti-statism, we need an automated immune system against centralized authority.

## Proposed Solution

A **Counter-Power Agent** that continuously audits the network for power asymmetry.

1.  **Authority Audit (The Guild Filter)**: Analyzes power regarding hardware/resources.
    *   **Distinction**: Recognizes "Productive Condensation" (e.g., a Battery Guild).
    *   **Logic**: High Stock + High Outflow = **"Critical Infrastructure"** (Good). High Stock + No Outflow = **"Warlord"** (Bad).
    *   **"Process Sabotage" vs "Silence"**: It distinguishes between *Active Obstruction* (Repeated Blocking) and *Passive Silence*.
        *   **Silence** -> Triggers **Pruning Prompt** (Private: "Do you want to leave?").
        *   **Blocking** -> Triggers **Saboteur Sensor** (Public: "You are blocking without code.").
2.  **Leveling Protocols**: If hierarchy OR bureaucracy is detected, agent proposes remedies.
3.  **Safe Eject**: In any Justice Circle, the individual has an "Eject Button" to immediately Secede (Fork) if they feel coerced, preventing "Struggle Sessions".

## Requirements

### Requirement: Centralization Detection

The system SHALL detect when specific agents dominate governance or resource flows.

#### Scenario: The Admin Problem
- WHEN User "AdminDave" performs 80% of node approvals
- THEN Agent broadcasts "Centralization Warning: AdminDave is becoming a Single Point of Need."

### Requirement: Voluntary Association

The system SHALL make leaving easy.

#### Scenario: Forking the Commune
- WHEN a Group clicks "Secede"
- THEN Bundle all their data + keys
- AND Cleanly sever ties with the parent mesh (removing mutual keys)

## Dependencies

- **Governance Circle**: To audit proposal authorship.
- **Identity System**: For key management during secession.

## Risks

- **False Positives**: Someone might just be helpful. Mitigation: Tone is "Warning" not "Punishment." The community decides.

## Alternatives Considered

- **Term Limits**: Good, but static. We want dynamic detection of power accumulation.
