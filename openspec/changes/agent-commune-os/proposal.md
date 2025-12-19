# Proposal: Agent System (Commune OS)

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** ✅ IMPLEMENTED - All 7 agents complete: Commons Router, Matchmaker, Perishables, Scheduler, Planner, Pathfinder, Inventory
**Priority:** TIER 2 (Intelligence Layer)
**Complexity:** 7 systems (7 specialized agents with guardrails)

---

## Problem Statement

The gift economy needs intelligent coordination: matching offers with needs, prioritizing perishable food, planning seasonal work, scheduling work parties, suggesting learning paths, and optimizing inventory. Humans shouldn't have to manually scan all offers or plan complex dependencies. AI agents should provide proposals that humans ratify.

**Current state:** Manual coordination only
**Desired state:** 7 specialized agents providing proposal-based assistance with human approval gates

---

## Proposed Solution

Implement 7 specialized agents as defined in Section 10 of the spec:
1. Commons Router Agent - cache and forwarding decisions
2. Mutual Aid Matchmaker - offer/need matching
3. Perishables Dispatcher - time-sensitive food coordination
4. Scheduler / Work Party Agent - session and commitment planning
5. Permaculture Seasonal Planner - goals → seasonal → weekly planning
6. Education Pathfinder - lesson recommendations tied to work
7. Inventory/Pantry Agent - replenishment and shortage prediction

All agents emit **proposals** that require human ratification. All proposals include explanation, inputs used, and constraints.

---

## Requirements

### Requirement: All Agents SHALL Emit Proposals, Not Allocations

Agents SHALL NOT make unilateral allocations. All suggestions SHALL be proposals requiring human approval.

#### Scenario: Matchmaker proposes match

- GIVEN Alice offers tomatoes, Bob needs tomatoes
- WHEN Mutual Aid Matchmaker analyzes
- THEN it SHALL create proposal:
  - Type: Match
  - Explanation: "Alice has 5 lbs tomatoes available for 2 days. Bob needs tomatoes for sauce. Both are near Community Kitchen."
  - InputsUsed: [AliceOfferBundleId, BobNeedBundleId, location data]
  - Constraints: "Alice prefers morning handoff. Bob provides container."
  - RequiresApproval: [Alice, Bob]
- AND SHALL publish proposal bundle
- AND SHALL NOT create Exchange until both approve

### Requirement: Commons Router Agent SHALL Manage Cache Decisions

The Commons Router Agent SHALL decide what to cache and forward based on role and budgets.

#### Scenario: Router optimizes cache for bridge node

- GIVEN a bridge node has 2GB cache budget
- WHEN the Router Agent analyzes cache usage
- THEN it SHALL propose:
  - Keep: All emergency bundles (always)
  - Keep: Perishables with <48h TTL (high priority)
  - Keep: Popular knowledge indexes (high access frequency)
  - Evict: Old low-priority bundles
  - Explanation: "Prioritizing emergency + perishables supports commune coordination. Knowledge indexes enable disconnected discovery."

### Requirement: Perishables Dispatcher SHALL Prioritize Time-Sensitive Food

The Perishables Dispatcher SHALL identify expiring food and propose urgent redistribution.

#### Scenario: Dispatcher detects expiring tomatoes

- GIVEN InventoryIndex shows 10 lbs tomatoes expiring in 36 hours
- WHEN Dispatcher analyzes
- THEN it SHALL:
  - Query for tomato needs (recent or latent)
  - Identify nearby receivers
  - Propose urgentExchange with explanation
  - Set high priority for coordination bundles
  - Suggest: "Batch cooking event if no individual needs found"

### Requirement: Scheduler SHALL Coordinate Work Parties

The Scheduler SHALL propose work party sessions based on Plans and Commitments.

#### Scenario: Scheduler plans spring planting work party

- GIVEN seasonal Plan includes "Planting Process" requiring 5 people × 4 hours
- WHEN Scheduler analyzes
- THEN it SHALL propose:
  - Date/time: Next Saturday 9am-1pm (based on participant availability)
  - Location: Community Garden
  - Participants: [5 people with availability + gardening skill]
  - Resources needed: Seeds (from pantry), tools (from shed), water
  - Explanation: "Saturday has most participant availability. Weather forecast shows good planting conditions."
  - Constraint: "Need 3+ experienced gardeners for guidance"

### Requirement: Permaculture Planner SHALL Generate Seasonal Plans

The Permaculture Seasonal Planner SHALL transform goals into actionable Plans with Processes and dependencies.

#### Scenario: Planner creates spring 2025 plan

- GIVEN goal: "Establish food forest with 20 fruit trees + guild plantings"
- WHEN Planner generates Plan
- THEN it SHALL propose:
  - Processes: Site analysis → Soil preparation → Tree selection → Planting → Guild establishment → Mulching → Maintenance
  - Dependencies: Soil prep MUST complete before planting; tree planting MUST complete before guild planting
  - Timeline: Weekly work parties over 8 weeks
  - Resources: Trees (sourced), compost (from pantry), mulch (from yard waste), labor (from commitments)
  - Inputs: Permaculture principles, climate data, soil analysis
  - Explanation: "Guild plantings (nitrogen fixers, pest deterrents) establish after trees to avoid competition during establishment."

### Requirement: Education Pathfinder SHALL Recommend Just-In-Time Learning

The Education Pathfinder SHALL suggest Lessons tied to upcoming tasks.

#### Scenario: Pathfinder recommends learning for first-time beekeeper

- GIVEN Bob accepted Commitment to help with hive inspection next week
- AND Bob has no beekeeping experience
- WHEN Pathfinder analyzes
- THEN it SHALL recommend Lessons:
  - "Beekeeping Safety Basics" (5 min video, prerequisite)
  - "Hive Inspection Checklist" (1-page PDF, reference)
  - "Reading Bee Behavior" (10 min interactive)
  - Protocol: "Community Hive Inspection Process"
- AND SHALL explain: "These lessons prepare you for safe, effective participation. Safety Basics is prerequisite."

### Requirement: Inventory Agent SHALL Predict Shortages

The Inventory/Pantry Agent SHALL analyze usage and propose replenishment.

#### Scenario: Inventory agent detects seed shortage

- GIVEN seed inventory for tomatoes: 5 packets
- AND seasonal Plan requires: 20 packets for spring planting
- WHEN Inventory Agent analyzes (opt-in)
- THEN it SHALL propose:
  - Action: Create Need for 15 tomato seed packets
  - Explanation: "Spring planting in 4 weeks requires 20 packets. Current inventory: 5. Gap: 15."
  - Alternatives: "Check with members for saved seeds before external sourcing."
  - Constraint: "Heirloom varieties preferred for seed saving."

### Requirement: All Proposals SHALL Include Guardrails

Every proposal SHALL include explanation, inputs, and constraints.

#### Scenario: Proposal is published

- GIVEN any agent creates a proposal
- WHEN the proposal is published as bundle
- THEN it SHALL include:
  - `explanation`: Human-readable rationale (1-3 sentences)
  - `inputsUsed`: Array of bundleIds that informed the decision
  - `constraints`: Relevant limitations (dietary, access, privacy, timing)
- AND SHALL require human ratification (configurable per proposal type)
- AND SHALL NOT execute automatically

### Requirement: Surveillance SHALL NOT Be Required

No agent SHALL require surveillance to provide value. All are opt-in.

#### Scenario: User opts out of Inventory Agent

- GIVEN a user values privacy
- WHEN they configure agent settings
- THEN Inventory Agent SHALL be disabled by default
- AND user SHALL manually manage their inventory if desired
- AND system SHALL function fully without Inventory Agent

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Agent framework (proposal generation, publishing, approval tracking)
2. Commons Router Agent implementation
3. Mutual Aid Matchmaker implementation
4. Perishables Dispatcher implementation
5. Scheduler / Work Party Agent implementation
6. Permaculture Seasonal Planner implementation
7. Education Pathfinder implementation
8. Inventory/Pantry Agent implementation
9. Proposal approval UI
10. Agent settings UI (opt-in/out, configure behavior)

---

## Success Criteria

- [ ] Agent framework supports proposal generation and publishing
- [ ] All 7 agents implemented
- [ ] Agents emit proposals, not allocations
- [ ] Proposals include explanation, inputs, constraints
- [ ] Human approval required (configurable)
- [ ] Commons Router optimizes cache for node role
- [ ] Matchmaker creates offer/need matches
- [ ] Perishables Dispatcher prioritizes expiring food
- [ ] Scheduler proposes work parties with participants and resources
- [ ] Permaculture Planner generates seasonal Plans from goals
- [ ] Education Pathfinder recommends just-in-time Lessons
- [ ] Inventory Agent predicts shortages (opt-in)
- [ ] Agents are opt-in, surveillance not required
- [ ] Proposal approval UI functional
- [ ] Agent settings configurable per user

---

## Dependencies

- ValueFlows Node (agents reason about VF objects)
- DTN Bundle System (proposals published as bundles)
- Discovery/Search (agents query for matching data)

---

## Constraints

- **Human oversight:** Proposals require approval (default)
- **Privacy:** No mandatory surveillance
- **Transparency:** All inputs and reasoning visible
- **Opt-in:** Agents can be disabled per user preference

---

## Notes

This implements Section 10 "Agent Layer (Commune OS)" from solarpunk_node_full_spec.md. Agents provide intelligence but humans retain control through mandatory approval gates.
