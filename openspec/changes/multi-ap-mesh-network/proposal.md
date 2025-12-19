# Proposal: Multi-AP Mesh Network

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** ✅ IMPLEMENTED - AP configs, bridge services, Mode A/C support, network monitoring
**Priority:** TIER 1 (Core Infrastructure)
**Complexity:** 4 systems (AP setup, bridge nodes, Mode C fallback, Mode A/B research)

---

## Problem Statement

Communes need network coverage across multiple physical areas (garden, kitchen, workshop, library) without relying on internet infrastructure. Single AP coverage is insufficient. Phones need to participate in mesh routing, not just connect to routers. The system must work reliably even when multi-hop routing fails (Mode C fallback).

**Current state:** No mesh network infrastructure
**Desired state:** Multiple AP "islands" with bridge nodes providing store-and-forward, plus opportunistic multi-hop routing when hardware supports it

---

## Proposed Solution

Implement multi-AP island architecture (Section 3 of spec):
- **Mode C (DTN-only)**: Foundation mode, always works, no IP routing between islands
- **Mode A (BATMAN-adv)**: Optimum-case for rooted phones with kernel support
- **Mode B (Wi-Fi Direct)**: Alternative for non-rooted phones with capable drivers

All core apps MUST work in Mode C. Mode A/B are optimizations.

---

## Requirements

### Requirement: Multiple AP Islands SHALL Operate Independently

The system SHALL support multiple simultaneously-operating APs.

#### Scenario: Commune has 4 AP islands

- GIVEN a commune with physical areas
- WHEN network infrastructure is deployed
- THEN there SHALL be independent APs:
  - Garden AP (outdoor area, SSID: "SolarpunkGarden")
  - Kitchen AP (food prep/sharing, SSID: "SolarpunkKitchen")
  - Workshop AP (tool/skill sharing, SSID: "SolarpunkWorkshop")
  - Library AP (knowledge hub, SSID: "SolarpunkLibrary")
- AND each AP SHALL assign addresses from separate subnet:
  - Garden: 10.44.1.0/24
  - Kitchen: 10.44.2.0/24
  - Workshop: 10.44.3.0/24
  - Library: 10.44.4.0/24
- AND local services (DTN sync, VF node API) SHALL be reachable within each island

### Requirement: Bridge Nodes SHALL Provide Store-and-Forward

Bridge nodes SHALL carry bundles between islands.

#### Scenario: Bridge node walks between garden and kitchen

- GIVEN Alice's phone is configured as bridge node
- WHEN Alice visits Garden AP
- THEN her phone SHALL:
  - Connect to Garden AP
  - Sync bundles (receive pending, publish local)
  - Cache bundles for forwarding
- WHEN Alice walks to Kitchen AP
- THEN her phone SHALL:
  - Disconnect from Garden AP
  - Connect to Kitchen AP
  - Sync bundles (forward cached bundles from Garden)
  - Receive new bundles from Kitchen
- AND bundles SHALL propagate between islands via Alice's carries

### Requirement: Mode C (DTN-Only) SHALL Always Work

All core functionality SHALL work without IP routing between islands.

#### Scenario: System operates in Mode C

- GIVEN phones cannot route between islands (no mesh)
- WHEN using the system
- THEN all features SHALL work:
  - Offers/needs published as bundles
  - Bundles propagate via bridge nodes
  - Queries and responses work
  - Files chunk and retrieve
  - Agents propose matches
- AND propagation SHALL occur when bridge nodes move
- AND system SHALL function correctly despite delays

### Requirement: Mode A (BATMAN-adv) SHALL Be Supported When Available

Phones with rooted Android + batman-adv kernel support SHALL participate in multi-hop mesh.

#### Scenario: Rooted phone with batman-adv joins mesh

- GIVEN a phone has LineageOS with batman-adv kernel module
- WHEN phone is configured for Mode A
- THEN phone SHALL:
  - Load batman-adv kernel module
  - Create mesh interface (bat0)
  - Assign address from 10.44.0.0/16
  - Participate in BATMAN mesh routing
- AND phone SHALL route traffic multi-hop over bat0
- AND DTN bundles SHALL sync faster via direct routing

#### Scenario: Mode A degrades to Mode C

- GIVEN Mode A mesh has routing issues
- WHEN DTN cannot reach peer via IP
- THEN system SHALL fallback to Mode C (store-and-forward)
- AND SHALL continue functioning correctly

### Requirement: Mode B (Wi-Fi Direct) SHALL Be Researched

Wi-Fi Direct multi-group bridging SHALL be investigated as non-rooted alternative.

#### Scenario: Wi-Fi Direct mode is evaluated

- GIVEN most phones don't have root access
- WHEN evaluating Mode B
- THEN research SHALL determine:
  - Which Android devices support concurrent Wi-Fi groups
  - Whether Meshrabiya-style bridging works on target hardware
  - Performance and reliability compared to Mode C
  - Battery impact
- AND IF Mode B proves viable
- THEN it SHALL be implemented as alternative to Mode A

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. AP configuration guide (hostapd for RPi, AP mode for Android)
2. Bridge node configuration (DTN sync behavior)
3. Mode C: DTN-only fallback (foundation, always works)
4. Mode A: BATMAN-adv setup scripts and documentation
5. Mode B: Wi-Fi Direct research and prototype (if viable)
6. Network testing and validation across 3+ islands

---

## Success Criteria

- [ ] 3+ AP islands operating independently
- [ ] Bridge nodes configured and tested
- [ ] Mode C (DTN-only) works reliably
- [ ] Bundles propagate between islands in <10 min (via bridge walks)
- [ ] Mode A (BATMAN-adv) works on supported devices
- [ ] Mode A gracefully degrades to Mode C when needed
- [ ] Mode B viability determined (research complete)
- [ ] All core apps work in Mode C (mandatory)
- [ ] Multi-hop routing provides speedup when available (Mode A/B)
- [ ] Network handles 20+ concurrent users without degradation

---

## Dependencies

- DTN Bundle System (Mode C foundation)
- Android service for network management
- Hardware: Devices for AP nodes (RPi or Android phones)

---

## Constraints

- **Mode C is mandatory**: All apps must work without IP routing
- **Battery**: Multi-hop routing consumes more power
- **Hardware**: Not all phones support Mode A/B
- **Reliability**: Mesh routing can be unpredictable; DTN fallback required

---

## Notes

This implements Section 3 "Network Architecture: Multi-AP + DTN + (Optimum) Multi-hop" and Section 8 "Phones as Routers (Optimum-Case Multi-Hop)" from solarpunk_node_full_spec.md.

**Critical:** Mode C (DTN-only) is the foundation. Mode A/B are optimizations that may or may not work on specific hardware. Never depend on Mode A/B for core functionality.
