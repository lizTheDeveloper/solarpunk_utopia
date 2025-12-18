# Proposal: Governance Circle Agent

**Submitted By:** Antigravity
**Date:** 2025-12-17
**Status:** Draft
**Complexity:** 2 systems

## Problem Statement

Decentralized communities often struggle with decision-making and conflict resolution. We need a way to formalize "proposals" that require consensus or consent, and a structured way to handle interpersonal conflicts without resorting to "admin banning".

## Proposed Solution

A **Governance Circle Agent** that facilitates Human-AI collaboration:
1. **Loomio-lite Proposal Flow**: Humans AND AI Agents can submit proposals. AIs submit based on data (e.g., "Predicted shortfall"), Humans ratify.
2. **Restorative Justice Circles**: A specific protocol for conflict resolution where the agent facilitates the scheduling and structure of a resolution circle.
3. **Consensus Health Monitoring**: Tracking engagement in governance to prevent "stagnocracy" (where only a few people vote).

## Requirements

### Requirement: Proposal Lifecycle

The system SHALL support the creation, discussion, and voting of governance proposals.

#### Scenario: Submitting a Proposal
- WHEN a user submits a "New Garden Budget" proposal
- THEN a discussion thread is created
- AND a voting deadline is set

### Requirement: Restorative Justice Circles

The system SHALL provide a "Request Mediation" action that triggers a structured conflict resolution workflow.

#### Scenario: Requesting Mediation
- WHEN User A blocks User B
- THEN the agent prompts User A: "Would you like to initiate a restorative circle?"
- IF yes, THEN the agent invites pre-selected mediators

## Dependencies

- **Identity System**: To authenticate voters.
- **Briar/Manyverse**: For the discussion threads.

## Risks

- **Bureaucracy**: Too much governance can stifle action. Mitigation: "Lazy Consensus" (silence = assent) defaults for minor issues.
- **Tyranny of Structurelessness**: If we don't define this, hidden power structures emerge.

## Alternatives Considered

- **DAO / Token Voting**: Rejected. One-coin-one-vote is anti-solarpunk. We use one-person-one-voice.
