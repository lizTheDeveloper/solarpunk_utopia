# Proposal: Mycelial Strike

**Submitted By:** Philosopher Council (Kropotkin + Health Monitor)
**Date:** 2025-12-19
**Status:** DRAFT
**Complexity:** 3 systems
**Timeline:** PHILOSOPHICAL

## Problem Statement

Mutual aid without mutual defense is incomplete. If we're building a solidarity network, it must be able to defend itself and its members.

Current approach:
- Individual nodes report abuse
- Stewards investigate
- Eventually, action is taken
- Meanwhile, the abuser continues extracting value

**How do we create automatic solidarity that doesn't wait for committee meetings?**

## Proposed Solution

The "Mycelial Strike" - automated solidarity strikes triggered by abuse detection.

### Mechanism

When the Counter-Power Agent detects a "Battery Warlord" (someone abusing the network for extraction), nearby nodes **automatically throttle** their interaction with the abuser.

- No committee meeting required
- No human intervention needed
- Instant, collective response
- Escalates based on severity

### As Kropotkin said: "Mutual Aid includes Mutual Defense."

## Requirements

### Requirement: Abuse Detection Integration

The system SHALL integrate with abuse detection systems.

#### Scenario: Warlord Detection
- GIVEN the Counter-Power Agent detects extractive behavior
- WHEN abuse threshold is crossed (e.g., 5 exchanges with nothing given)
- THEN a Warlord Alert is created
- AND propagated to nearby nodes via DTN

### Requirement: Automatic Throttling

The system SHALL automatically throttle interaction with abusers.

#### Scenario: Local Strike Activation
- GIVEN a Warlord Alert is received
- AND my node trusts the reporting node
- WHEN I process the alert
- THEN I automatically:
  - Deprioritize the warlord's offers in matching
  - Add latency to their message delivery
  - Reduce visibility of their proposals
  - Mark their profile with warning indicator
- AND this happens WITHOUT manual approval

### Requirement: Escalation Levels

The system SHALL escalate based on abuse severity.

#### Scenario: Severity-Based Response
- GIVEN abuse severity is calculated
- THEN throttling level is:
  - **Low (score 1-2):** Deprioritize in matching
  - **Medium (score 3-4):** Add message latency + matching penalty
  - **High (score 5-7):** Full throttle - minimal interaction
  - **Critical (score 8-10):** Automatic isolation pending steward review
- AND severity increases with repeated abuse

### Requirement: Solidarity Propagation

The system SHALL propagate strikes across the mesh.

#### Scenario: Strike Spreads
- GIVEN Node A throttles a warlord
- WHEN Node B syncs with Node A
- THEN Node B receives the Warlord Alert
- AND if Node B trusts Node A, Node B also throttles
- AND the strike spreads mycelially through trust networks

### Requirement: Evidence Collection

The system SHALL collect evidence automatically.

#### Scenario: Building a Case
- GIVEN a node is throttling someone
- THEN the system tracks:
  - Original abuse reports
  - How many nodes are throttling
  - Duration of throttling
  - User's response (did behavior change?)
- AND this evidence is available for steward review

### Requirement: De-escalation

The system SHALL automatically de-escalate when behavior improves.

#### Scenario: Redemption Path
- GIVEN a throttled user changes behavior
- WHEN they complete 3 successful exchanges (giving AND receiving)
- THEN throttling level decreases
- AND if sustained improvement, throttling is removed
- AND the network gives second chances

### Requirement: Human Override

The system SHALL allow stewards to override strikes.

#### Scenario: False Positive
- GIVEN a strike was triggered incorrectly
- WHEN a steward reviews the case
- THEN they can:
  - Cancel the strike
  - Adjust severity
  - Whitelist the user from future auto-strikes
- AND overrides are logged for accountability

### Requirement: Transparency

The system SHALL make strike reasons visible.

#### Scenario: Understanding Why
- GIVEN I'm being throttled
- WHEN I check my status
- THEN I see:
  - What behavior triggered the strike
  - Current throttle level
  - What I need to do to improve
  - How to appeal to stewards
- AND the system teaches, not just punishes

## Implementation Plan

### Phase 1: Detection Integration
1. Hook into Counter-Power Agent abuse scoring
2. Define warlord thresholds
3. Create Warlord Alert bundle type

### Phase 2: Throttling Engine
1. Matching deprioritization logic
2. Message latency injection
3. UI warning indicators
4. Severity-based escalation

### Phase 3: Propagation
1. DTN bundle sync for Warlord Alerts
2. Trust-based filtering (only propagate from trusted nodes)
3. Mycelial spread tracking

### Phase 4: Redemption & Oversight
1. Behavior tracking for de-escalation
2. Steward override interface
3. Appeal system
4. Audit trail

## Data Model

### Warlord Alert
```python
{
    "id": "warlord-alert-uuid",
    "target_user_id": "user-uuid",
    "severity": 6,  # 1-10
    "abuse_type": "battery_warlord",  # extraction without contribution
    "evidence": [
        {"type": "exchange", "details": "Took 5 items, gave 0"},
        {"type": "pattern", "details": "20 requests, 0 offers in 30 days"}
    ],
    "reporting_node": "node-fingerprint",
    "created_at": "2025-12-19T...",
    "expires_at": "2025-12-26T..."  # 7 day alert window
}
```

### Local Strike
```python
{
    "id": "strike-uuid",
    "alert_id": "warlord-alert-uuid",
    "target_user_id": "user-uuid",
    "throttle_level": "medium",
    "activated_at": "2025-12-19T...",
    "deactivated_at": null,
    "behavior_score_at_start": 2.5,
    "current_behavior_score": 4.1,  # improving
    "automatic": true
}
```

## Safety Considerations

### Preventing Abuse of the Strike System

- **False Reports:** Only propagate from trusted nodes (Web of Trust)
- **Vendetta Strikes:** Require evidence, not just accusations
- **Echo Chamber:** Stewards can review and override
- **Transparency:** User knows why they're being throttled and how to fix it

### Preventing Centralized Blacklists

- **No Central Authority:** Each node decides independently based on trust
- **Expiration:** Alerts expire after 7 days if not renewed
- **Redemption:** Behavior change leads to automatic de-escalation
- **No Permanent Bans:** Even critical-level strikes can be overcome

## Risks

- **False Positives:** Someone gets throttled who doesn't deserve it. Mitigation: Steward override, transparent criteria, redemption path.
- **Gaming:** Bad actors report enemies as warlords. Mitigation: Trust-based filtering, evidence requirements, steward review.
- **Overreach:** System becomes punitive instead of protective. Mitigation: Emphasis on redemption, education over punishment.
- **Technical Failure:** Throttling doesn't work, warlords continue. Mitigation: Multiple throttling mechanisms, manual backup.

## Success Criteria

- [ ] Warlord Alerts integrate with Counter-Power Agent
- [ ] Automatic throttling activates based on severity
- [ ] Strikes propagate through trust networks
- [ ] De-escalation works when behavior improves
- [ ] Stewards can review and override
- [ ] Users understand why they're throttled and how to fix it
- [ ] False positive rate <5%

## Dependencies

- Counter-Power Agent (abuse detection)
- Web of Trust (trust-based propagation)
- DTN Bundle System (alert propagation)
- Steward permission system (override capability)

## Philosophical Foundation

**Peter Kropotkin:** In "Mutual Aid," Kropotkin showed that cooperation is an evolutionary advantage. But cooperation without defense is naive. The mycelium doesn't just share nutrients - it also fights infections.

**Networked Solidarity:** Strike doesn't mean destroy. It means: "We will not facilitate your extraction." The network collectively withdraws participation until behavior changes.

**Decentralized Defense:** No central authority decides who to ban. Each node decides based on evidence and trust. The network defends itself without becoming authoritarian.

## Notes

This is the most technically aggressive proposal in Tier 4. It's saying: "The network has immune system."

Some will call this censorship. But refusing to serve an abuser is not censorship - it's boundaries. The difference:
- Censorship: "You cannot speak"
- Mycelial Strike: "We will not amplify your extraction"

The abuser can still use the network. They're just deprioritized until they demonstrate reciprocity.

This is mutual aid AND mutual defense. You cannot have one without the other.

Build accordingly.
