# Proposal: ValueFlows Node (VF-Full v1.0)

**Submitted By:** orchestrator
**Date:** 2025-12-17
**Status:** Draft
**Priority:** TIER 0 (Foundation)
**Complexity:** 6 systems (data model, storage, UX, signing, sync, API)

---

## Problem Statement

Solar Punk communes need to coordinate economic activity in a gift economy: sharing food, tools, seeds, labor, skills, and knowledge. The system must track offers and needs, match them intelligently, coordinate exchanges, track resource flows, plan seasonal work, and preserve audit trails for accountability. This must work offline-first, without central servers, using local data stores that sync via DTN bundles.

**Current state:** No economic coordination infrastructure
**Desired state:** Complete ValueFlows-compatible node implementing VF-Full v1.0 specification with all objects, local storage, and bundle-based synchronization

---

## Proposed Solution

Implement a full ValueFlows (VF) node on each phone with complete VF-Full v1.0 object model: Agents, Locations, ResourceSpecs, ResourceInstances, Listings (offers/needs), Matches, Exchanges, Events, Processes, Commitments, Plans, Protocols, and Lessons. Provide simple UX for creating offers/needs while storing rich backend data for agent reasoning. Sign all objects cryptographically for provenance. Sync via DTN bundles.

---

## Requirements

### Requirement: VF Data Model SHALL Be Fully Implemented

The system SHALL implement all ValueFlows v1.0 objects as defined in spec.

#### Scenario: System supports complete VF object model

- GIVEN the ValueFlows node is initialized
- WHEN querying supported object types
- THEN the system SHALL support:
  - **Agents**: People, groups, places (who participates)
  - **Locations**: Physical places with optional lat/lon
  - **ResourceSpec**: Categories/types (tomatoes, shovel, tutoring)
  - **ResourceInstance**: Trackable instances (a specific shovel, a batch of tomatoes)
  - **Listing**: Offers and needs (UX primitive)
  - **Match**: Suggested/accepted pairing of offer+need
  - **Exchange**: Negotiated arrangement with constraints and window
  - **Event**: Economic events (handoff, work, delivery, harvest, class)
  - **Process**: Transforms inputs→outputs (permaculture, cooking, repairs)
  - **Commitment**: Promises to do work/deliver/teach
  - **Plan**: Container of processes/commitments + dependencies
  - **Protocol**: Repeatable method (compost recipe)
  - **Lesson**: Microlearning tied to tasks

### Requirement: Offers and Needs SHALL Be Simple to Create

The UX SHALL provide simple offer/need creation while storing rich data.

#### Scenario: User creates food offer

- GIVEN a user has surplus tomatoes
- WHEN they create an offer via UI
- THEN they SHALL provide:
  - Category: "Food" → "Vegetables" → "Tomatoes"
  - Quantity: "5 lbs"
  - Location: "Community Garden"
  - Available: "Next 2 days"
  - Notes: "Heirloom variety, organic"
- AND the system SHALL create:
  - Agent (if first time)
  - Location (if not exists)
  - ResourceSpec (if not exists: "Tomatoes")
  - ResourceInstance (this specific batch)
  - Listing (type=offer)
- AND SHALL sign with user's key
- AND SHALL publish as DTN bundle with appropriate TTL (24-72h)

#### Scenario: User creates skill need

- GIVEN a user needs help with beekeeping
- WHEN they create a need via UI
- THEN they SHALL provide:
  - Category: "Skills" → "Agriculture" → "Beekeeping"
  - Duration: "2 hours"
  - Location: "My backyard"
  - Timeframe: "Next week, flexible"
  - Notes: "First-time beekeeper, need guidance on hive setup"
- AND the system SHALL create VF objects and publish bundle

### Requirement: Resource Tracking SHALL Support Inventory

The system SHALL track resource instances for inventory management.

#### Scenario: Tool library tracks shovels

- GIVEN a tool library has 3 shovels
- WHEN they are added to inventory
- THEN the system SHALL create:
  - ResourceSpec: "Shovel"
  - ResourceInstance: "Shovel-001" (serial/label)
  - ResourceInstance: "Shovel-002"
  - ResourceInstance: "Shovel-003"
- AND SHALL track state: available, checked-out, in-repair
- AND SHALL track location: which shed/member has it
- AND SHALL emit Events when state changes

#### Scenario: Pantry tracks perishable food

- GIVEN a community pantry receives a batch of tomatoes
- WHEN they are logged
- THEN the system SHALL create:
  - ResourceSpec: "Tomatoes"
  - ResourceInstance: "Batch-20251217-tomatoes" with expiry
  - Location: "Community Pantry, Shelf 2"
  - Event: "Receive" (quantity: 10 lbs, from: Garden)
- AND SHALL trigger Perishables Dispatcher agent when expiry approaches

### Requirement: Exchanges SHALL Coordinate Handoffs

The system SHALL support negotiated exchanges between offers and needs.

#### Scenario: Match leads to exchange

- GIVEN Alice offers "5 lbs tomatoes"
- AND Bob needs "tomatoes for sauce"
- WHEN Mutual Aid Matchmaker creates a Match
- AND Alice and Bob both accept
- THEN the system SHALL create Exchange:
  - Parties: Alice (provider), Bob (receiver)
  - Resource: 3 lbs tomatoes (negotiated)
  - Location: Community Kitchen
  - Time window: Tomorrow 2-4pm
  - Constraints: Bob brings container
- AND SHALL create Commitments for both parties
- AND SHALL notify both via bundle

#### Scenario: Exchange completes with Events

- GIVEN an Exchange is arranged
- WHEN handoff occurs
- THEN both parties SHALL record Events:
  - Alice: Event type=transfer-out, resource=3lbs tomatoes, to=Bob
  - Bob: Event type=receive, resource=3lbs tomatoes, from=Alice
- AND Events SHALL be signed by both parties
- AND SHALL update ResourceInstance state and location

### Requirement: Processes SHALL Track Transformations

The system SHALL support production processes with inputs and outputs.

#### Scenario: Community kitchen tracks sauce production

- GIVEN a cooking session is planned
- WHEN creating a Process
- THEN the Process SHALL specify:
  - Name: "Tomato Sauce Batch 12"
  - Protocol: "Community Tomato Sauce Recipe"
  - Inputs: 10 lbs tomatoes, 2 onions, 1 cup olive oil, spices
  - Outputs: 8 jars tomato sauce
  - Duration: ~3 hours
  - Location: Community Kitchen
  - Participants: Alice, Bob, Carol (commitments)
- AND the Process SHALL emit Events:
  - Consume events for inputs
  - Produce events for outputs
  - Work events for participant labor

#### Scenario: Garden tracks planting process

- GIVEN spring planting is planned
- WHEN creating a seasonal Process
- THEN inputs SHALL include: seeds, compost, water, labor
- AND outputs SHALL include: seedlings, transplants, harvest (future)
- AND Process SHALL be part of seasonal Plan

### Requirement: Plans SHALL Organize Work

The system SHALL support plans with dependencies and schedules.

#### Scenario: Seasonal permaculture plan

- GIVEN a permaculture garden needs seasonal planning
- WHEN creating a Plan for "Spring 2025"
- THEN the Plan SHALL contain:
  - Processes: soil preparation → planting → transplanting → maintenance → harvest
  - Dependencies: planting depends on soil preparation completion
  - Commitments: who does what, when
  - Resources: seeds, tools, labor hours
  - Schedule: weekly work parties
- AND Permaculture Seasonal Planner agent SHALL generate from goals
- AND Scheduler agent SHALL coordinate work parties

### Requirement: Protocols and Lessons SHALL Enable Learning

The system SHALL tie education directly to practice.

#### Scenario: Protocol is reusable recipe

- GIVEN a community has successful compost method
- WHEN creating a Protocol
- THEN the Protocol SHALL specify:
  - Name: "Hot Composting Method"
  - Category: Waste Management
  - Inputs: food scraps, yard waste, water
  - Process: layer, turn, monitor temperature
  - Duration: 4-6 weeks
  - Outputs: finished compost
  - Lessons: attached microlearning modules
- AND Protocol SHALL be reusable for future Processes

#### Scenario: Lesson provides just-in-time learning

- GIVEN a user is about to start beekeeping
- WHEN Education Pathfinder agent recommends next steps
- THEN it SHALL provide Lessons:
  - "Beekeeping Safety Basics" (5 min video)
  - "Hive Inspection Checklist" (1-page PDF)
  - "Seasonal Beekeeping Calendar" (reference)
- AND Lessons SHALL be tagged with skills/tasks
- AND SHALL be available offline via file chunking system

### Requirement: All Objects SHALL Be Signed

Every VF object SHALL have cryptographic signature for provenance.

#### Scenario: Object is signed on creation

- GIVEN a user creates an offer
- WHEN the VF node saves the object
- THEN the object SHALL include:
  - `author`: Agent ID (public key)
  - `createdAt`: ISO 8601 timestamp
  - `signature`: Ed25519 signature of canonical JSON
- AND signature SHALL be verified on receipt
- AND objects with invalid signatures SHALL be rejected

### Requirement: Objects SHALL Sync via DTN Bundles

VF objects SHALL propagate across the mesh via bundles.

#### Scenario: New offer is published

- GIVEN a user creates an offer
- WHEN the VF node saves it locally
- THEN the system SHALL:
  - Save to local SQLite database
  - Create DTN bundle with payloadType="vf:Listing"
  - Set appropriate TTL (24-72h for perishables)
  - Set priority (perishable for food, normal for tools)
  - Publish to DTN outbox
- AND bundle SHALL propagate to other nodes
- AND other nodes SHALL save to their local VF database

---

## Implementation Tasks

See `tasks.md` for detailed breakdown.

**Key deliverables:**
1. Complete VF data model (SQLite schema)
2. CRUD operations for all VF object types
3. Simple offer/need UI (Android app)
4. Matching algorithm (agent integration point)
5. Exchange coordination workflow
6. Process tracking with events
7. Plan management with dependencies
8. Protocol and lesson storage
9. Cryptographic signing for all objects
10. DTN bundle sync integration

---

## Success Criteria

- [ ] All VF-Full v1.0 objects implemented in SQLite
- [ ] Simple UI for creating offers and needs (<1 minute to post)
- [ ] ResourceInstance tracking works (inventory, location, state)
- [ ] Exchanges coordinate handoffs with commitments
- [ ] Processes track input→output transformations
- [ ] Plans organize seasonal work with dependencies
- [ ] Protocols provide reusable recipes
- [ ] Lessons tie learning to tasks
- [ ] All objects are signed on creation
- [ ] Signatures are verified on receipt
- [ ] Invalid signatures are rejected
- [ ] VF objects sync via DTN bundles
- [ ] Offers propagate across 3+ AP islands in <10 min
- [ ] 100+ offers/needs can be browsed without lag
- [ ] Queries work: "Show me available food in next 24h"

---

## Dependencies

- DTN Bundle System (must be implemented first)
- SQLite for local storage
- Ed25519 signing (from DTN bundle system)
- Android UI framework
- File chunking system (for Protocol/Lesson content)

---

## Constraints

- **Offline-first:** All operations must work without internet
- **Storage:** VF database should fit in 50-200MB for typical usage
- **Privacy:** Private exchanges must not be publicly visible
- **Trust:** Users must be able to verify provenance of all objects

---

## Notes

This implements Section 9 "ValueFlows Node Spec (VF-Full v1.0)" from solarpunk_node_full_spec.md. The UX stays simple (offer/need) but the backend stores rich VF objects so agents can reason about planning, matching, and optimization.

The system provides the economic coordination layer for the gift economy.
