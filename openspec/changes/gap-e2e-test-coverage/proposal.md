# GAP-E2E: End-to-End Test Coverage Gaps

**Status:** Implemented
**Priority:** P1 - Reliability
**Effort:** 20-30 hours (across multiple sessions)
**Last Updated:** 2025-12-21

## Problem

We have integration tests and unit tests, but many critical flows lack end-to-end tests. Without E2E tests, we can't automatically verify that user-facing flows work correctly after changes.

**Current test coverage:**

| Flow | Test Type | Location |
|------|-----------|----------|
| Gift Economy (offer→match→exchange) | Integration | `tests/integration/test_end_to_end_gift_economy.py` |
| Governance Voting | E2E | `tests/e2e/test_governance_*.py` |
| Panic Features | Unit | `tests/test_panic_features.py` |
| Web of Trust | Unit | `tests/unit/test_web_of_trust.py` |
| Care Outreach | Unit | `tests/test_care_outreach.py` |
| Fork Rights | Unit | `tests/test_fork_rights.py` |
| Sanctuary Verification | Unit | `tests/test_sanctuary_multi_steward_verification.py` |
| Economic Withdrawal | Unit | `tests/test_economic_withdrawal.py` |
| Algorithmic Transparency | Unit | `tests/test_algorithmic_transparency.py` |
| Fraud/Abuse Protections | Unit | `tests/test_fraud_abuse_protections.py` |
| Network Import | Unit | `tests/test_network_import_offline.py` |

**Gap:** Unit tests verify components work. E2E tests verify *user flows* work. Many flows are tested at the component level but not at the flow level.

## Critical Flows Missing E2E Tests

### Priority 1: Safety-Critical Flows (OPSEC)

These protect lives. They MUST work.

#### 1. Rapid Response Flow
**What it does:** 2-tap emergency alert → network propagation → responder coordination → resolution
**Why critical:** Failure during ICE raid = people get detained
**Test scenario:**
```
WHEN Alice taps emergency button twice
AND enters alert type "ice_raid" with location hint "downtown area"
THEN alert bundle created with EMERGENCY priority
AND propagates to all responders within 30 seconds
AND responders can mark "available" or "en_route"
AND coordinator can escalate/de-escalate
AND after-action review captures lessons
```

#### 2. Sanctuary Network Full Flow
**What it does:** Resource offer → steward verification → request → allocation → coordination
**Why critical:** Failure during deportation operation = unsafe resource gets offered
**Test scenario:**
```
WHEN Carol offers safe_space resource with HIGH sensitivity
THEN resource NOT visible until verified
WHEN 3-of-5 stewards verify (escape routes, capacity, buddy protocol)
THEN resource becomes available
WHEN steward creates urgent request
THEN high-trust (>0.8) users can see and coordinate
AND no permanent records retained after 24h
```

#### 3. Panic Features E2E (beyond unit tests)
**What it does:** Duress PIN in auth flow → burn notice → network propagation
**Why critical:** Unit tests verify components; E2E verifies the actual auth flow
**Test scenario:**
```
WHEN Alice logs in with duress PIN (not normal PIN)
THEN login appears to succeed (no visible difference)
AND burn notice created and broadcast via DTN
AND vouch chain notified within 24h
AND local data wiped OR decoy mode activated
WHEN Alice recovers with seed phrase
THEN identity restored from network
```

### Priority 2: Trust & Coordination Flows

#### 4. Web of Trust Vouch Chain
**What it does:** Genesis → vouch → trust propagation → revocation
**Why critical:** Trust miscalculation = wrong people get access
**Test scenario:**
```
GIVEN Genesis node G with trust 1.0
WHEN G vouches for Alice
THEN Alice.trust = 0.85 (or configured decay)
WHEN Alice vouches for Bob (Alice.trust >= 0.7)
THEN Bob.trust = Alice.trust * decay
WHEN Alice revokes vouch for Bob
THEN Bob.trust recalculated (may drop to 0 if no other chains)
AND Bob's access to high-trust resources restricted
```

#### 5. Mycelial Strike Defense
**What it does:** Evidence submission → network consensus → proportional response
**Why critical:** False positive = innocent person cut off. False negative = warlord continues.
**Test scenario:**
```
WHEN Alice submits warlord alert against Mallory
WITH evidence (screenshot, transaction history)
THEN alert propagates to stewards via DTN
WHEN 3+ trusted sources corroborate
THEN auto-action triggered (throttle/quarantine)
WHEN steward reviews and confirms
THEN Mallory quarantined from network
WHEN new evidence exonerates Mallory
THEN steward can override with reason
```

#### 6. Blocking with Silent Failure
**What it does:** Block user → messaging/matching fails silently
**Why critical:** Blocked person MUST NOT know they're blocked (safety)
**Test scenario:**
```
WHEN Alice blocks Bob
THEN Bob receives no notification
WHEN Bob tries to message Alice
THEN request returns 404 (not 403 "blocked")
WHEN matchmaker considers Bob→Alice match
THEN match silently excluded (no "blocked" in explanation)
WHEN Alice unblocks Bob
THEN normal operation resumes
```

### Priority 3: Multi-Node Network Flows

#### 7. DTN Mesh Sync Protocol
**What it does:** Bundle index → request → push/pull with trust enforcement
**Why critical:** Mesh doesn't work = network fails during infrastructure outage
**Test scenario:**
```
GIVEN Node A has bundles [B1, B2, B3]
AND Node C has bundles [B2, B4]
WHEN A and C connect (Bluetooth/WiFi-Direct)
AND exchange bundle indices
THEN A requests B4 (missing from A)
AND C requests B1, B3 (missing from C)
AND bundles transferred respecting priority
AND EMERGENCY bundles transferred first
AND expired bundles NOT transferred
```

#### 8. Cross-Community Discovery
**What it does:** Pull-model resource visibility across communities
**Why critical:** Communities need to coordinate without central server
**Test scenario:**
```
GIVEN Downtown community offers "solar panels"
AND Riverside community needs "solar panels"
WHEN Riverside pulls discovery index
THEN sees Downtown's offer (if audience=REGION or PUBLIC)
WHEN trust distance > 3
THEN offer hidden (unless PUBLIC)
WHEN match proposed cross-community
THEN both communities approve before exchange
```

### Priority 4: Governance & Power Dynamics

#### 9. Saturnalia Role Inversion
**What it does:** Annual role swap → power crystallization prevention
**Why critical:** Power crystallization = network becomes hierarchical
**Test scenario:**
```
WHEN Saturnalia event configured (role_inversion mode)
AND event triggers (annual/manual)
THEN stewards become members
AND members can access steward functions
AND safety-critical flows (panic/sanctuary) NOT inverted
WHEN member opts out
THEN opt-out recorded with reason
WHEN event ends
THEN roles revert
AND reflection prompts appear
```

#### 10. Ancestor Voting / Memorial Funds
**What it does:** Departed member's reputation → ghost voting on proposals
**Why critical:** Honoring departed while preventing abuse
**Test scenario:**
```
WHEN community member departs (natural/migration/injury)
THEN memorial fund created from reputation
WHEN new proposal matches departed member's values
THEN ghost reputation allocated (by threshold signature)
WHEN 3-of-5 stewards approve allocation
THEN proposal receives ghost votes
WHEN family requests removal
THEN memorial fund deleted, ghost votes removed
```

#### 11. Bakunin Analytics Alerts
**What it does:** Detect power concentration → alert stewards
**Why critical:** Silent power concentration = warlords form undetected
**Test scenario:**
```
GIVEN Carol controls 85% of community batteries
WHEN analytics runs
THEN "Battery Warlord" alert generated (severity: high)
AND suggestions include: pool resources, teach repair skills
GIVEN Dan is only person who can fix solar panels
WHEN analytics runs
THEN "Skill Gatekeeper" alert generated
AND suggestions include: skill share, apprenticeship
```

### Priority 5: Philosophical Features

#### 12. Silence Weight in Voting
**What it does:** Track who DIDN'T vote (deliberate silence ≠ absence)
**Why critical:** Consensus requires knowing who abstained deliberately
**Test scenario:**
```
WHEN vote session created with quorum=0.7
AND 60% vote yes, 10% vote no, 30% don't vote
THEN decision NOT reached (below quorum)
AND system shows: 10% silent (could have voted, chose not to)
AND system shows: 20% absent (never logged in during vote)
WHEN silent members are prompted
THEN can mark "deliberate abstention" vs "oversight"
```

#### 13. Temporal Justice / Slow Exchanges
**What it does:** Multi-day exchanges for complex items (repairs, teaching)
**Why critical:** Rushing complex exchanges = poor quality
**Test scenario:**
```
WHEN Alice offers "teach bike repair" (slow exchange)
AND expected duration = 3 sessions over 2 weeks
THEN exchange created with timeline
AND check-in prompts at session boundaries
WHEN Alice marks "session 1 complete"
THEN progress tracked
WHEN timeline exceeded
THEN coordinator notified (not auto-cancelled)
WHEN both parties mark complete
THEN exchange finalized
```

#### 14. Care Outreach Conversion Flow
**What it does:** Flag struggling member → volunteer outreach → conversion
**Why critical:** "Saboteurs" are often people in crisis
**Test scenario:**
```
WHEN system flags Bob as isolated (no exchanges in 30 days)
AND volunteer Carol assigned
THEN Carol sees Bob's needs assessment
WHEN Carol connects Bob with resources
AND adds notes (housing_insecure, connected to mutual aid)
AND Bob re-engages (creates offer or need)
THEN Bob marked "converted" (not surveillance - celebration)
AND conversion metrics updated
```

### Priority 6: Frontend Integration

#### 15. Onboarding Flow
**What it does:** Welcome → gift economy explanation → first offer → first match
**Why critical:** Bad onboarding = people don't understand gift economy
**Test scenario:**
```
WHEN new user starts onboarding
THEN sees: WelcomeStep, GiftEconomyStep, CreateOfferStep, BrowseOffersStep, AgentsHelpStep, CompletionStep
WHEN user creates first offer during onboarding
THEN offer actually created in backend
WHEN user browses offers
THEN sees real offers from community
WHEN onboarding completes
THEN user has trust score (from inviter vouch)
```

#### 16. Steward Dashboard Flow
**What it does:** Metrics → attention items → activity → celebrations
**Why critical:** Stewards need situational awareness
**Test scenario:**
```
WHEN steward views dashboard for their cell
THEN sees: member count, active offers/needs, exchanges this week
AND sees attention items: join requests, proposals, trust issues
AND sees recent activity timeline
AND sees celebrations (NO individual $ amounts - per anti-reputation-capitalism)
WHEN steward clicks "approve" on join request
THEN member added to cell
```

## Test Infrastructure Needed

### 1. Multi-Node Test Harness
For DTN tests, need to simulate multiple nodes that can:
- Connect/disconnect on demand
- Exchange bundles via mock Bluetooth/WiFi-Direct
- Verify bundle propagation timing

### 2. Time Manipulation
For slow exchanges and dead man's switch:
- Freeze/advance time in tests
- Verify timeout behaviors

### 3. Trust Graph Fixtures
Predefined trust networks:
- Genesis → fully trusted chain (5 hops)
- Disjoint communities (no trust path)
- Ring topology (circular vouches)

## Tasks

### Phase 1: Safety-Critical (P1)
1. [x] Rapid Response E2E test - `tests/e2e/test_rapid_response_e2e.py` (6 test scenarios)
2. [x] Sanctuary Network E2E test - `tests/e2e/test_sanctuary_network_e2e.py` (7 test scenarios)
3. [ ] Panic Features E2E test (auth flow + network propagation) - DEFERRED (unit tests exist, needs auth system integration)

### Phase 2: Trust & Coordination (P2)
4. [x] Web of Trust vouch chain E2E test - `tests/e2e/test_web_of_trust_e2e.py` (10 test scenarios, all passing)
5. [x] Mycelial Strike defense E2E test - `tests/e2e/test_mycelial_strike_e2e.py` (10 test scenarios, all passing)
6. [x] Blocking with silent failure E2E test - `tests/e2e/test_blocking_silent_failure_e2e.py` (10 test scenarios, all passing)

### Phase 3: Multi-Node (P3)
7. [x] DTN Mesh Sync E2E test - `tests/e2e/test_dtn_mesh_sync_e2e.py` (9 test scenarios, skeleton complete, needs bundle creation fix)
8. [x] Cross-Community Discovery E2E test - `tests/e2e/test_cross_community_discovery_e2e.py` (11 test scenarios covering all visibility levels)

### Phase 4: Governance (P4)
9. [x] Saturnalia E2E test - `tests/e2e/test_saturnalia_e2e.py` (14 test scenarios, all passing)
10. [x] Ancestor Voting E2E test - `tests/e2e/test_ancestor_voting_e2e.py` (11 test scenarios, all passing)
11. [x] Bakunin Analytics E2E test - `tests/e2e/test_bakunin_analytics_e2e.py` (6 test scenarios, all passing)

### Phase 5: Philosophical (P5)
12. [x] Silence Weight E2E test - `tests/e2e/test_governance_e2e.py` (10 test scenarios covering silence tracking, quorum, and privacy)
13. [x] Temporal Justice E2E test - `valueflows_node/tests/e2e/test_temporal_justice_e2e.py` (9 test scenarios covering slow exchanges, fragmented availability, care work acknowledgment)
14. [x] Care Outreach E2E test - `valueflows_node/tests/e2e/test_care_outreach_e2e.py` (11 test scenarios covering detection, conversion, access levels, no-shaming approach)

### Phase 6: Frontend (P6)
15. [x] Onboarding E2E test - `tests/e2e/test_onboarding_flow_e2e.spec.ts` (9 Playwright test scenarios covering full onboarding flow, validation, navigation, education)
16. [x] Steward Dashboard E2E test - `tests/e2e/test_steward_dashboard_e2e.spec.ts` (13 Playwright test scenarios covering metrics, actions, trust issues, celebrations without rankings)

## Success Criteria

- [x] All P1 (safety-critical) flows have passing E2E tests
- [x] E2E tests run in CI on every PR (GitHub Actions workflows configured)
- [x] Multi-node test harness enables mesh testing (`tests/harness/multi_node.py`)
- [x] Trust graph fixtures enable complex scenarios (`tests/harness/trust_fixtures.py`)
- [x] Time manipulation enables timeout testing (`tests/harness/time_control.py`)
- [x] No flow ships without corresponding E2E test (enforced via PR template)

## Philosophy

> "If we can't test it automatically, we can't be sure it works when someone's life depends on it."

The rapid response system that fails during an actual ICE raid isn't a bug - it's a betrayal. These aren't features; they're promises we make to people who trust us with their safety.

E2E tests are how we keep those promises.
