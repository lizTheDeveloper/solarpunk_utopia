# Proposal: Sanctuary Network

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** ✅ IMPLEMENTED
**Complexity:** 2 systems
**Timeline:** URGENT
**Implemented:** 2025-12-19

## Problem Statement
## Problem Statement

People are being kidnapped. Journalists detained. Congresspeople threatened. ICE with a $58 billion budget and bounty hunters operating nationwide.

The network needs to coordinate sanctuary: safe houses, transport, legal resources, supplies. This isn't abstract mutual aid. This is underground railroad infrastructure.

## Proposed Solution

A specialized resource category and matching system for sanctuary operations.

### Resource Types

| Type | Examples | Sensitivity |
|------|----------|-------------|
| Safe Space | Spare room, basement, rural property | HIGH |
| Transport | Car, bike, knowledge of routes | HIGH |
| Legal | Immigration lawyer, bail fund, know-your-rights | MEDIUM |
| Supplies | Food, clothes, cash, burner phones | MEDIUM |
| Skills | Translation, medical, de-escalation | MEDIUM |
| Intel | ICE activity alerts, checkpoint locations | HIGH |

### Sensitivity Levels

- **HIGH:** Only visible to high-trust members (>0.8), never broadcast widely, extra verification
- **MEDIUM:** Visible to established members (>0.6), cell-scoped by default
- **LOW:** Standard visibility rules

### Operational Security

1. **No permanent records** of sanctuary matches (auto-purge after completion)
2. **High trust required** to see or offer sanctuary resources
3. **Code words** for sensitive resources (configurable by cell)
4. **Verified need** - sanctuary requests require steward verification
5. **Cell-to-cell only** - no network-wide sanctuary broadcasts

## Requirements

### Requirement: Sanctuary Resource Category

The system SHALL have a protected category for sanctuary resources.

#### Scenario: Safe Space Offer
- GIVEN Maria has a spare room she can offer for emergency housing
- WHEN Maria creates a "Safe Space" offer
- THEN it is tagged as HIGH sensitivity
- AND only visible to members with trust >0.8
- AND never appears in network-wide searches
- AND can only be matched by steward-verified requests

### Requirement: Sanctuary Requests

The system SHALL handle urgent sanctuary needs.

#### Scenario: Emergency Request
- GIVEN someone needs immediate safe housing
- WHEN a steward creates a verified sanctuary request
- THEN it is matched against available safe spaces in the cell
- AND if no local match, adjacent cells' stewards are quietly notified
- AND the match is made with minimal information exposure

### Requirement: Auto-Purge

The system SHALL not retain sensitive match records.

#### Scenario: Completed Sanctuary
- GIVEN a sanctuary match was completed (person is safe)
- WHEN the match is marked complete
- THEN all details are purged within 24 hours
- AND only aggregate stats remain ("1 sanctuary completed this month")
- AND no record of who helped whom exists

### Requirement: Rapid Alert

The system SHALL support rapid "need help now" alerts.

#### Scenario: ICE Raid Alert
- GIVEN a community member witnesses an ICE operation
- WHEN they trigger a "Rapid Alert"
- THEN nearby high-trust members receive immediate notification
- AND the alert includes location and basic situation
- AND members can respond with availability

### Requirement: Resource Verification

The system SHALL verify sanctuary resources.

#### Scenario: Safe Space Verification
- GIVEN Maria offers a safe space
- WHEN the offer is created
- THEN a steward must verify (visit or video call)
- AND the verification is recorded
- AND unverified spaces are not matched to critical needs

## Flow: Sanctuary Request

```
1. Person in danger contacts trusted cell member
2. Cell member (or steward) creates verified sanctuary request
3. System matches to available resources (safe space, transport, etc.)
4. Steward coordinates logistics (never through the app - in person or signal)
5. Resources deployed
6. Once safe, match marked complete
7. Records purged after 24 hours
```

## Tasks

1. [ ] Add sanctuary resource categories to data model
2. [ ] Implement sensitivity levels for resources
3. [ ] Create trust-gated visibility for HIGH sensitivity
4. [ ] Build steward verification flow for sanctuary offers
5. [ ] Implement sanctuary request creation (steward-only)
6. [ ] Build matching logic for sanctuary (priority, proximity, verification)
7. [ ] Create Rapid Alert broadcast system
8. [ ] Implement auto-purge for completed sanctuary matches
9. [ ] Build sanctuary dashboard for stewards (minimal info, just status)
10. [ ] Create OPSEC guide for sanctuary operations

## Dependencies

- Web of Trust (high trust requirements)
- Local Cells (cell-scoped operations)
- Mesh Messaging (secure coordination)
- Panic Features (protection if compromised)

## Risks

- **Infiltration:** Agent offers fake safe space. Mitigation: Steward verification, high trust requirements, in-person vetting.
- **Record seizure:** Logs reveal sanctuary network. Mitigation: Auto-purge, no permanent records, minimal logging.
- **Misuse:** Fake requests waste resources. Mitigation: Steward verification for all requests.

## OPSEC Notes

This document describes the system capabilities. Operational security practices should be documented separately and distributed only to trained stewards:
- How to verify sanctuary offers
- How to coordinate without leaving trails
- What to do if a sanctuary is compromised
- Legal considerations by jurisdiction

## Success Criteria

- [ ] Sanctuary resources only visible to high-trust members
- [ ] Steward verification required for sanctuary offers
- [ ] Sanctuary matches purge after 24 hours
- [ ] Rapid alerts reach relevant members in <5 minutes
- [ ] No persistent record of who helped whom
