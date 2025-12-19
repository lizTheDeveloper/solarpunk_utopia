# Proposal: Mass Onboarding System

**Submitted By:** Liz / Antigravity
**Date:** 2025-12-18
**Status:** CRITICAL PATH
**Complexity:** 2 systems
**Timeline:** WORKSHOP BLOCKER

## Problem Statement

You have 500,000 people ready to join. The workshop will have hundreds wanting to onboard simultaneously. The current system has no concept of bulk onboarding, event-based registration, or importing from existing trusted networks.

If onboarding is slow, people bounce. If it's insecure, infiltrators get in. We need to thread this needle.

## Proposed Solution

Multiple onboarding paths optimized for different contexts:

### Path 1: Event Onboarding (Workshop)
- Steward generates event QR code
- Attendees scan → instant vouch from steward
- Immediate access to event cell
- Upgrade to full membership after event

### Path 2: Network Import (Hipcamp, Bootcamp Alumni)
- OAuth or verified email from existing platform
- Automatic trust score based on existing reputation
- Maps to appropriate geographic cell

### Path 3: Personal Vouch (Standard)
- Friend sends invite link
- New user creates account
- Friend confirms vouch
- Trust computed from vouch chain

### Path 4: Open Application
- For people without connections
- Apply → explain your interest
- Stewards review → interview → vouch
- Slower but maintains integrity

## Requirements

### Requirement: Event QR Onboarding

The system SHALL enable rapid onboarding at events.

#### Scenario: Workshop Registration
- GIVEN Liz is hosting a workshop with 200 attendees
- WHEN Liz generates an "Event QR" for the workshop
- THEN attendees scan and are instantly added to the workshop cell
- AND they receive temporary trust (enough for participation)
- AND they can post offers/needs within the event
- AND after the event, they're prompted to get full vouches or leave

### Requirement: Trusted Network Import

The system SHALL bootstrap trust from existing networks.

#### Scenario: Hipcamp User Import
- GIVEN Maria has been a Hipcamp host since 2017 with 50+ reviews
- WHEN Maria chooses "Connect Hipcamp"
- THEN she authenticates with Hipcamp OAuth
- AND the system imports her verification status
- AND she receives genesis-adjacent trust (0.85)
- AND she can immediately participate without needing vouches

### Requirement: Bulk Invite Links

The system SHALL support steward-generated invite links.

#### Scenario: Community Leader Onboarding
- GIVEN Carlos is a trusted community leader
- WHEN Carlos generates a "batch invite" (limit: 20 people)
- THEN he gets a unique link/QR code
- AND each person who uses it receives Carlos's vouch
- AND Carlos sees who used his links
- AND his vouch capacity refreshes over time

### Requirement: Onboarding Queue Management

The system SHALL prevent onboarding bottlenecks.

#### Scenario: Event Surge
- GIVEN 500 people try to onboard in 5 minutes
- WHEN the system receives the surge
- THEN it processes requests in parallel
- AND shows users their queue position if delayed
- AND nobody is rejected due to capacity

### Requirement: Trust Ladder

The system SHALL have graduated access levels.

#### Scenario: New Member Progression
- WHEN a new member joins via event QR
- THEN they start with "Event" trust (can participate in event only)
- WHEN they get vouched by a full member
- THEN they upgrade to "Member" trust (cell access)
- WHEN they complete 3 successful exchanges
- THEN they upgrade to "Established" trust (can vouch others)

## Onboarding Flows

### Event Flow
```
Scan QR → Create Account → Set Location → Tutorial → Event Cell → Active
     (30 seconds total)
```

### Import Flow
```
Choose Platform → OAuth → Confirm Identity → Set Location → Find Cell → Active
     (60 seconds total)
```

### Vouch Flow
```
Receive Invite → Create Account → Voucher Confirms → Set Location → Find Cell → Active
     (varies - depends on voucher)
```

### Open Application Flow
```
Apply → Explain Interest → Wait for Review → Interview → Vouch → Active
     (1-7 days)
```

## Tasks

1. [ ] Build event QR generation for stewards
2. [ ] Implement event-scoped temporary trust
3. [ ] Create OAuth integration for Hipcamp
4. [ ] Create OAuth integration for other platforms (GitHub, etc.)
5. [ ] Build batch invite link system
6. [ ] Implement trust ladder progression
7. [ ] Create queue management for surge protection
8. [ ] Build application review flow for stewards
9. [ ] Implement post-event upgrade prompts
10. [ ] Create onboarding analytics for stewards
11. [ ] Build "invite your network" sharing tools

## Dependencies

- Web of Trust (trust scoring)
- Local Cells (cell assignment)
- Identity system (account creation)

## Risks

- **Event trust abuse:** People use event access for bad purposes. Mitigation: Event trust is limited, expires after event.
- **Import trust gaming:** Fake accounts on source platforms. Mitigation: Require minimum account age/activity.
- **Surge failures:** System crashes during big events. Mitigation: Load testing, queue management.

## Success Criteria

- [ ] 200 people can onboard in 15 minutes at an event
- [ ] Hipcamp users can join in under 60 seconds
- [ ] Batch invite links work and track usage
- [ ] Trust ladder progression is clear and achievable
- [ ] No bottlenecks during workshop
