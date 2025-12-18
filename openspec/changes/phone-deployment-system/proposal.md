# Proposal: Phone Deployment System

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** Draft
**Priority:** TIER 0 (Foundation - Required for Workshop)
**Complexity:** 3 systems (software manifest, deployment presets, provisioning automation)

---

## Problem Statement

Before the workshop, we need to provision 20+ phones with the complete Solarpunk software stack. Each phone needs appropriate configuration based on its role (Citizen, Bridge, AP, Library). The provisioning process must be fast (<15 min/phone) and reliable. Participants need working phones ready to use immediately.

**Current state:** No deployment tooling
**Desired state:** Automated provisioning system with role-based presets

---

## Proposed Solution

Implement phone provisioning automation based on Section 11 "Software Manifest" and Section 12 "Deployment Presets" from spec. Create scripts to install base OS, F-Droid apps, custom apps, and configure based on role. Provide deployment presets (Citizen, Bridge, AP, Library) with appropriate cache budgets and behavior.

---

## Requirements

### Requirement: Software Manifest SHALL Be Installable

The complete Solarpunk software stack SHALL be installable via automation.

#### Scenario: Phone is provisioned with base software

- GIVEN a phone with LineageOS installed
- WHEN provisioning script runs
- THEN the following SHALL be installed:
  - **F-Droid** (app store)
  - **Briar** (secure messaging + forums)
  - **Manyverse** (SSB social feed)
  - **Syncthing** (file distribution)
  - **Kiwix** (offline knowledge, with permaculture content packs)
  - **Organic Maps** (offline maps, with local area cached)
  - **Termux** (terminal, for advanced users)
  - **DTN Bundle Service** (custom Android service)
  - **ValueFlows Node** (custom Android app)
- AND all apps SHALL be configured with reasonable defaults

### Requirement: Deployment Presets SHALL Define Role Behavior

Four deployment presets SHALL configure phones for specific roles.

#### Scenario: Phone is configured as Citizen (default)

- GIVEN a phone being provisioned
- WHEN "Citizen" preset is selected
- THEN the phone SHALL be configured:
  - Cache budget: 256-1024 MB (small, battery-first)
  - TTL enforcement: strict (delete expired immediately)
  - Forwarding: public/local + time-sensitive only
  - Speculative caching: disabled (save battery)
  - Battery profile: balanced
- AND SHALL be suitable for typical commune member

#### Scenario: Phone is configured as Bridge

- GIVEN a phone being provisioned
- WHEN "Bridge" preset is selected
- THEN the phone SHALL be configured:
  - Cache budget: 2-8 GB (medium, storage prioritized)
  - Forwarding: aggressive for perishables/emergency
  - Speculative caching: enabled (emergency + hot bundles)
  - Index response: enabled (answer queries)
  - Battery profile: balanced (expect regular charging)
- AND SHALL prioritize serving the commune's coordination needs

#### Scenario: Phone is configured as AP

- GIVEN a phone being provisioned
- WHEN "AP" preset is selected
- THEN the phone SHALL be configured:
  - Hotspot: enabled on schedule (or always-on if powered)
  - Cache budget: 2-8 GB
  - Index publishing: frequent (every 5 min)
  - Portal hosting: enabled (optional local services)
  - Battery profile: aggressive (expect continuous power)
- AND SHALL provide network infrastructure

#### Scenario: Phone is configured as Library

- GIVEN a phone being provisioned
- WHEN "Library" preset is selected
- THEN the phone SHALL be configured:
  - Cache budget: 10-50 GB (large, content prioritized)
  - File caching: aggressive (serve chunks for all knowledge)
  - Kiwix: host full content (permaculture, repair, education)
  - Index response: enabled
  - Battery profile: plugged-in (expect continuous power)
- AND SHALL serve as knowledge hub

### Requirement: Provisioning SHALL Be Fast and Reliable

Phone provisioning SHALL complete in <15 minutes per phone.

#### Scenario: Technical team provisions phones before workshop

- GIVEN 20 phones with LineageOS
- WHEN technical team runs provisioning
- THEN EACH phone SHALL complete in <15 minutes:
  - Software installation: <10 min
  - Configuration: <3 min
  - Testing: <2 min
- AND batch provisioning SHALL support parallel execution (5-10 phones simultaneously)
- AND failures SHALL be clearly reported for retry

### Requirement: Phones SHALL Be Workshop-Ready

Provisioned phones SHALL be immediately usable by participants.

#### Scenario: Participant receives phone at workshop

- GIVEN a provisioned phone
- WHEN participant receives it
- THEN the phone SHALL:
  - Boot to functional state (no setup wizard)
  - Have all apps installed and visible
  - Have test account created (or easy account creation flow)
  - Have battery >80%
  - Have quick-start guide visible (widget or PDF)
- AND participant SHALL be able to create first offer/need in <2 minutes

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Software manifest documentation
2. F-Droid + app installation automation (adb + scripts)
3. DTN Bundle Service APK
4. ValueFlows Node APK
5. Deployment preset configurations (4 JSON files)
6. Provisioning script (bash + adb)
7. Batch provisioning script (parallel execution)
8. Testing and validation scripts
9. Participant quick-start guide (1-page PDF)
10. Troubleshooting guide for facilitators

---

## Success Criteria

- [ ] Software manifest documented
- [ ] All base apps installable via automation
- [ ] DTN Bundle Service APK built and tested
- [ ] ValueFlows Node APK built and tested
- [ ] 4 deployment presets defined and tested
- [ ] Provisioning script works reliably
- [ ] Single phone provisions in <15 min
- [ ] Batch provisioning supports 5-10 phones in parallel
- [ ] 20+ phones provisioned and tested
- [ ] All phones charged >80%
- [ ] Quick-start guide created and printed
- [ ] Troubleshooting guide created
- [ ] Dry-run with test users successful

---

## Dependencies

- LineageOS installed on all phones
- DTN Bundle System APK built
- ValueFlows Node APK built
- Hardware: phones, USB cables, hub for parallel provisioning

---

## Constraints

- **Timeline:** Must complete before workshop (1 week prep recommended)
- **Hardware:** Phones must support LineageOS
- **Storage:** Library nodes need devices with large storage (32GB+)
- **Power:** AP and Library nodes need continuous power (wall or solar)

---

## Notes

This implements Section 11 "Software Manifest (Installable)" and Section 12 "Deployment Presets (Config)" from solarpunk_node_full_spec.md.

This is the culmination: turning the spec into working phones that participants can use. Everything else depends on this being executed correctly.
