# Implementation Tasks: ValueFlows Node (VF-Full v1.0)

**Proposal:** valueflows-node-full
**Complexity:** 6 systems

---

## Task Breakdown

### System 1: Data Model and Storage (1.5 systems)

**Task 1.1: Design SQLite schema for all VF objects**
- Tables for: Agent, Location, ResourceSpec, ResourceInstance, Listing, Match, Exchange, Event, Process, Commitment, Plan, Protocol, Lesson
- Indexes for efficient queries
- Foreign key constraints
- **Complexity:** 0.5 systems

**Task 1.2: Implement CRUD operations for all object types**
- Create, Read, Update, Delete for each VF object type
- Validation logic per object
- **Complexity:** 0.6 systems

**Task 1.3: Implement query layer**
- `findOffers(filters)`
- `findNeeds(filters)`
- `findMatches(agentId)`
- `getInventory(location)`
- `getUpcomingExchanges(agentId)`
- **Complexity:** 0.4 systems

### System 2: Offer/Need UX (1.0 systems)

**Task 2.1: Design simple offer/need form UI**
- Category picker (Food, Tools, Skills, Housing, etc.)
- Quantity/duration input
- Location selector
- Time availability picker
- Notes field
- **Complexity:** 0.3 systems

**Task 2.2: Implement offer creation flow**
- Form validation
- Create VF objects (Agent, Location, ResourceSpec, ResourceInstance, Listing)
- Sign with user's key
- Publish as DTN bundle
- **Complexity:** 0.4 systems

**Task 2.3: Implement browse/search UI**
- List offers and needs
- Filter by category, location, timeframe
- Detail view for each listing
- **Complexity:** 0.3 systems

### System 3: Matching and Exchanges (1.2 systems)

**Task 3.1: Implement match creation**
- Agent API for creating matches
- User approval flow (accept/reject)
- Notification via bundles
- **Complexity:** 0.3 systems

**Task 3.2: Implement exchange workflow**
- Create Exchange from accepted Match
- Specify location, time, constraints
- Create Commitments for both parties
- **Complexity:** 0.4 systems

**Task 3.3: Implement event recording**
- UI for recording handoff events
- Sign events by both parties
- Update ResourceInstance state
- **Complexity:** 0.5 systems

### System 4: Processes and Plans (1.0 systems)

**Task 4.1: Implement Process creation and tracking**
- Process definition (name, protocol, inputs, outputs, participants)
- Emit Events (consume, produce, work)
- Link to Protocol if reusable
- **Complexity:** 0.4 systems

**Task 4.2: Implement Plan management**
- Create plans with processes and commitments
- Define dependencies between processes
- Schedule work parties
- **Complexity:** 0.4 systems

**Task 4.3: Implement Protocol and Lesson storage**
- Store Protocol definitions (reusable recipes)
- Link Lessons to Protocols and tasks
- Reference files via content hash (file chunking system)
- **Complexity:** 0.2 systems

### System 5: Signing and Verification (0.8 systems)

**Task 5.1: Implement object signing**
- Sign all VF objects on creation
- Use Ed25519 from DTN bundle system
- Include author (Agent ID = public key) and createdAt
- **Complexity:** 0.3 systems

**Task 5.2: Implement signature verification**
- Verify signatures on objects received via bundles
- Reject objects with invalid signatures
- Track verification failures
- **Complexity:** 0.3 systems

**Task 5.3: Implement provenance tracking**
- Display author and signature status in UI
- Show chain of events for resource instances
- Audit trail for exchanges
- **Complexity:** 0.2 systems

### System 6: DTN Bundle Integration (1.5 systems)

**Task 6.1: Implement VF object → bundle conversion**
- Serialize VF objects to bundle payload
- Set payloadType (vf:Listing, vf:Event, vf:Process, etc.)
- Set appropriate TTL and priority
- Publish to DTN outbox
- **Complexity:** 0.4 systems

**Task 6.2: Implement bundle → VF object conversion**
- Subscribe to VF bundle types
- Deserialize bundle payloads
- Verify signatures
- Save to local VF database
- Handle conflicts (same object from multiple sources)
- **Complexity:** 0.5 systems

**Task 6.3: Implement sync strategy**
- Publish new/updated objects immediately
- Request objects referenced but not yet received
- Handle deletions/revocations
- **Complexity:** 0.4 systems

**Task 6.4: Implement index publishing**
- Periodically publish InventoryIndex bundle (what offers/needs exist locally)
- Periodically publish ServiceIndex bundle (skills available)
- Respond to queries with matching object references
- **Complexity:** 0.2 systems

---

## Testing Tasks (included in complexity)

**Task T1: Unit tests**
- CRUD operations for all VF objects
- Signing and verification
- Bundle conversion
- **Complexity:** included

**Task T2: Integration tests**
- Create offer → publish bundle → received on peer → saved to peer database
- Match → Exchange → Events recorded by both parties
- Process with inputs/outputs → Events emitted
- **Complexity:** included

**Task T3: Field tests**
- Real offers/needs created by 10+ users
- Matches and exchanges coordinated
- Inventory tracked over time
- **Complexity:** included

---

## Validation Checklist

- [ ] SQLite schema implemented for all 13 VF object types
- [ ] CRUD operations work for all objects
- [ ] Simple offer/need UI (<1 min to create)
- [ ] Browse/search UI shows offers and needs
- [ ] Filtering works (category, location, timeframe)
- [ ] Match creation and approval flow works
- [ ] Exchange workflow coordinates handoffs
- [ ] Events recorded and signed by both parties
- [ ] ResourceInstance state updates correctly
- [ ] Processes track input→output transformations
- [ ] Plans organize processes with dependencies
- [ ] Protocols provide reusable recipes
- [ ] Lessons link to protocols and tasks
- [ ] All objects signed on creation (Ed25519)
- [ ] Signatures verified on receipt
- [ ] Invalid signatures rejected
- [ ] VF objects serialize to DTN bundles
- [ ] Bundles deserialize to VF objects
- [ ] New offers propagate across mesh in <10 min
- [ ] Index bundles published periodically
- [ ] Queries return correct results
- [ ] 100+ offers browsable without lag
- [ ] Provenance visible in UI

---

## Total Complexity: 6 Systems

- Data model and storage: 1.5 systems
- Offer/need UX: 1.0 systems
- Matching and exchanges: 1.2 systems
- Processes and plans: 1.0 systems
- Signing and verification: 0.8 systems
- DTN bundle integration: 1.5 systems
