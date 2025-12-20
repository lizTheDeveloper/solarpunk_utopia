# Proposal: Group Formation Protocol

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** ✅ IMPLEMENTED - Fractal group formation: physical key exchange (NFC/QR+OTP), nested groups, fission/fusion (12 tests passing)
**Complexity:** 2 systems

## Problem Statement

To have decentralized governance, we need a fluid way to define *who* is governing. Rigorous identity systems are too heavy; informal distinctness is too vague. We need a "Molecular" approach where groups can form, merge, and split instantly based on physical presence and trust.

## Proposed Solution

A **Fractal Group Formation Protocol** that allows groups to exist at *any scale* (from "Garden Task Force" to "Global Federation") using identical cryptographic primitives.

1.  **Fractal Grouping**: A "Group" is just a shared key + a scope. Groups can contain other Groups (Nesting).
    *   *Example*: `Commune_A` contains `Garden_Squad` and `Child_Care_Squad`.
2.  **Molecular Formation**: The primary way to form a *new* base-layer group is still physical proximity (NFC/QR), creating a "Molecule".
3.  **Group Stewardship ("The Holon")**: Every group, regardless of size, gets a "Holon Context" which acts as a bucket for **Stewardship**:
    *   **Resource Stewardship**: A Shared Inventory ("Heap") that the group manages.
    *   **Governance Stewardship**: A decision-making scope.
    *   **Communication Stewardship**: A shared chat channel.
4.  **Fission/Fusion**: Protocols for merging two Groups (Federating) or splitting them (Seceding).

## Requirements

### Requirement: Physical Key Exchange

The system SHALL require physical presence (or trusted bridge) to establish the initial Group Key.

#### Scenario: The Campfire Formation
- WHEN 3 users tap phones via NFC
- THEN Generate `GroupKey_Campfire`
- AND Distribute to all 3 devices
- *Rationale*: A minimum of 3 defines a "Commune" vs a "Couple". The system is designed for collective stewardship, not dyadic relationships.

### Requirement: Nested Scopes (Fractal Governance)

The system SHALL allow groups to nesting within other groups, inheriting permissions or resources if defined.

#### Scenario: The Sub-Committee
- WHEN "Garden Squad" is formed *inside* "Commune Alpha" context
- THEN "Garden Squad" inherits "Commune Alpha" public keys as trusted roots
- BUT "Commune Alpha" does NOT automatically get access to "Garden Squad" private chat (Subsidiarity)

### Requirement: Shared Context (The Holon)

The system SHALL auto-provision shared resources for the new group.

#### Scenario: Instant Commons
- WHEN `Molecule_Campfire` is formed
- THEN Create `Inventory_Campfire` (Shared Heap)
- AND Create `Chat_Campfire` (Encrypted Channel)

## Dependencies

- **Identity System**: For device keys.
- **DTN Bundle System**: To sync group state.

## Risks

- **Sybil Attacks**: One person creating many groups. Mitigation: Physical presence requirement makes this harder/expensive.

## Alternatives Considered

- **Admin-created Groups**: "Admin creates group, invites users." Rejected as too centralized.
