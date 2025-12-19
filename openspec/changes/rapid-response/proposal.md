# Proposal: Rapid Response Coordination

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** IMPLEMENTED
**Complexity:** 2 systems
**Timeline:** URGENT
**Implemented:** 2025-12-19

## Problem Statement

When ICE shows up at a workplace, when a journalist is detained, when a community member is threatened - there's no time for normal matching flows. The network needs to mobilize in minutes, not hours.

We need a rapid response system that can:
1. Alert relevant people immediately
2. Coordinate who's responding
3. Track situation status
4. Document for legal/media purposes
5. Stand down cleanly when resolved

## Proposed Solution

A rapid response mode that overrides normal flows for emergencies.

### Alert Levels

| Level | Trigger | Response |
|-------|---------|----------|
| 🔴 CRITICAL | Active raid, detention, immediate danger | All nearby high-trust members alerted, stewards mobilized |
| 🟠 URGENT | Developing situation, heightened risk | Cell stewards alerted, resources staged |
| 🟡 WATCH | Reported activity, monitor situation | Logged, stewards informed |

### Response Roles

- **Witness/Reporter:** Person who triggers alert
- **Coordinator:** Steward who manages response (one per incident)
- **Responders:** People who can physically respond
- **Legal:** Know-your-rights, lawyer contacts
- **Media:** Documenters, journalists
- **Support:** Supplies, transport, childcare

## Requirements

### Requirement: Rapid Alert

The system SHALL enable emergency alerts with minimal friction.

#### Scenario: Workplace Raid
- GIVEN Maria witnesses ICE entering a workplace
- WHEN Maria triggers a CRITICAL alert
- THEN she can do so in 2 taps (big red button + confirm)
- AND her location is attached (unless she disables)
- AND the alert propagates to all nearby high-trust members within 30 seconds

### Requirement: Alert Propagation

The system SHALL propagate alerts through mesh even without internet.

#### Scenario: Mesh Alert
- GIVEN an alert is triggered
- WHEN it is broadcast as a high-priority DTN bundle
- THEN nearby mesh nodes relay immediately
- AND priority preempts normal bundle traffic
- AND the alert reaches maximum range fastest

### Requirement: Response Coordination

The system SHALL coordinate responders.

#### Scenario: Response Marshaling
- GIVEN a CRITICAL alert is active
- WHEN responders receive it
- THEN they can indicate: "Responding," "Available but far," or "Can't respond"
- AND the coordinator sees who's coming
- AND responders see each other's status
- AND the system suggests roles based on skills/resources

### Requirement: Situation Updates

The system SHALL support real-time status updates.

#### Scenario: Evolving Situation
- GIVEN an active CRITICAL response
- WHEN the situation changes
- THEN the coordinator posts updates
- AND all responders receive updates immediately
- AND status can be escalated/de-escalated
- AND the timeline is preserved for documentation

### Requirement: Documentation

The system SHALL support secure documentation.

#### Scenario: Evidence Gathering
- GIVEN responders are on scene
- WHEN they capture photos/video
- THEN media is encrypted immediately
- AND uploaded to distributed storage (not central server)
- AND tagged with time/location metadata
- AND can be shared with legal/media contacts later

### Requirement: Stand Down

The system SHALL cleanly resolve incidents.

#### Scenario: All Clear
- GIVEN a situation is resolved
- WHEN the coordinator issues "All Clear"
- THEN responders are notified
- AND the incident is closed
- AND an after-action prompt is generated
- AND sensitive location data is purged after 24 hours

## Flow: Critical Response

```
1. ALERT: Maria hits red button (2 taps)
2. PROPAGATE: Alert reaches nearby members (<30 sec)
3. COORDINATE: First steward online becomes coordinator
4. MARSHAL: Responders indicate availability
5. DEPLOY: Coordinator assigns roles, responders move
6. UPDATE: Coordinator posts status updates
7. DOCUMENT: Responders capture evidence (encrypted)
8. RESOLVE: Situation resolved, coordinator calls "All Clear"
9. DEBRIEF: After-action review (optional)
10. PURGE: Sensitive data purged after 24 hours
```

## Tasks

1. [ ] Design rapid alert UI (2-tap trigger)
2. [ ] Implement high-priority DTN bundle type for alerts
3. [ ] Build alert propagation with mesh priority
4. [ ] Create responder status UI (responding/available/unavailable)
5. [ ] Build coordinator dashboard (who's responding, status)
6. [ ] Implement situation update broadcasting
7. [ ] Create encrypted media capture and upload
8. [ ] Build distributed storage for documentation
9. [ ] Implement stand-down flow
10. [ ] Create after-action review template
11. [ ] Build purge timer for sensitive data
12. [ ] Test alert propagation under various network conditions

## Dependencies

- Mesh Messaging (alert propagation)
- Web of Trust (high-trust requirements for alerts)
- Local Cells (geographic targeting)
- Panic Features (if responder is compromised)

## Risks

- **False alarms:** Wasted mobilization, alert fatigue. Mitigation: CRITICAL requires 1 confirmation within 5 min or auto-downgrades to WATCH.
- **Weaponized alerts:** Bad actor triggers to identify network members. Mitigation: High trust required to trigger, pattern detection for abuse.
- **Responder safety:** Running toward danger. Mitigation: Clear roles, legal observers stay back, OPSEC training.

## Success Criteria

- [ ] Alert triggers in 2 taps
- [ ] Alert reaches nearby members in <30 seconds (mesh)
- [ ] Coordinator can see who's responding
- [ ] Status updates propagate in real-time
- [ ] Documentation is encrypted and distributed
- [ ] Stand-down clears active state cleanly
- [ ] Sensitive data purges after 24 hours
