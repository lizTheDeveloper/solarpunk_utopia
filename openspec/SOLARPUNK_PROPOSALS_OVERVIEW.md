# Solarpunk Mesh Network - OpenSpec Proposals Overview

**Generated:** 2025-12-17
**Source:** solarpunk_node_full_spec.md
**Purpose:** Build complete gift economy mesh network system for Solar Punk communes before 6-hour workshop

---

## Total Complexity: 31 Systems

This is a full production system build, not a demo. All proposals are scoped for complete implementation by agents.

---

## Proposal Dependency Graph

```
TIER 0 (Foundation - Build First)
├─ DTN Bundle System (5 systems)
│  └─ Required by: ALL other proposals
│
├─ ValueFlows Node (6 systems)
│  └─ Required by: Agents, Discovery, Phone Deployment
│
└─ Phone Deployment System (3 systems)
   └─ Required for: Workshop delivery

TIER 1 (Core Functionality - Build Second)
├─ Discovery and Search (3 systems)
│  └─ Depends on: DTN, ValueFlows
│  └─ Required by: Agents
│
├─ File Chunking System (3 systems)
│  └─ Depends on: DTN
│  └─ Required by: Agents (Lessons/Protocols)
│
└─ Multi-AP Mesh Network (4 systems)
   └─ Depends on: DTN
   └─ Required for: Real-world deployment

TIER 2 (Intelligence Layer - Build Third)
└─ Agent System / Commune OS (7 systems)
   └─ Depends on: ValueFlows, Discovery, File Chunking
   └─ Makes the gift economy intelligent
```

---

## Proposal Summaries

### 1. DTN Bundle System (TIER 0)
**Complexity:** 5 systems
**Priority:** CRITICAL (foundation for everything)
**Status:** Draft

**What it does:**
- Core transport layer for all data
- Store-and-forward between AP islands
- TTL, priority queues, cache budgets, battery awareness
- Signing and trust management

**Key requirements:**
- Bundle format with metadata (TTL, priority, audience, signature)
- 6 queues (inbox, outbox, pending, delivered, expired, quarantine)
- TTL enforcement and cache budgets per node role
- Priority-based forwarding (emergency → perishable → normal → low)
- Speculative caching for high-utility bundles
- Ed25519 signing and verification

**Success criteria:**
- Emergency bundle reaches all nodes in <5 min via bridge walks
- System handles 1000+ bundles without degradation
- Invalid signatures go to quarantine
- Cache budgets enforced

---

### 2. ValueFlows Node (TIER 0)
**Complexity:** 6 systems
**Priority:** CRITICAL (economic coordination)
**Status:** Draft

**What it does:**
- Complete ValueFlows v1.0 implementation
- Offers, needs, matches, exchanges, events
- Processes, plans, protocols, lessons
- Gift economy coordination infrastructure

**Key requirements:**
- 13 VF object types (Agent, Location, ResourceSpec, ResourceInstance, Listing, Match, Exchange, Event, Process, Commitment, Plan, Protocol, Lesson)
- Simple offer/need UI (<1 min to create)
- Exchange workflow (match → approve → coordinate → record events)
- Process tracking (inputs → outputs with transformations)
- Plans with dependencies and scheduling
- Cryptographic signing for all objects
- Sync via DTN bundles

**Success criteria:**
- Offer created → bundle published → received on peer → saved to database in <10 min
- Exchanges coordinate handoffs with both parties signing events
- 100+ offers browsable without lag
- Queries work: "Show me available food in next 24h"

---

### 3. Phone Deployment System (TIER 0)
**Complexity:** 3 systems
**Priority:** CRITICAL (workshop delivery)
**Status:** Draft

**What it does:**
- Provision 20+ phones with complete software stack
- Role-based configuration (Citizen, Bridge, AP, Library)
- Fast, automated provisioning (<15 min/phone)

**Key requirements:**
- Software manifest: LineageOS + F-Droid + Briar + Manyverse + Syncthing + Kiwix + Organic Maps + DTN Service + VF Node
- 4 deployment presets with cache budgets and behavior
- Provisioning automation (single + batch)
- Content loading (Kiwix permaculture packs, local maps)
- Testing and validation scripts

**Success criteria:**
- 20+ phones provisioned in <15 min each
- Batch provisioning supports 5-10 phones in parallel
- All phones >80% battery
- Participant can create first offer in <2 min
- Dry-run successful

---

### 4. Discovery and Search System (TIER 1)
**Complexity:** 3 systems
**Priority:** High (enables decentralized discovery)
**Status:** Draft

**What it does:**
- Index bundles advertise local data
- Query/response protocol for distributed search
- Speculative index caching for disconnected discovery

**Key requirements:**
- 3 index types: InventoryIndex, ServiceIndex, KnowledgeIndex
- Periodic index publishing (every 5-60 min)
- Query bundles propagate and get responses
- Bridge nodes cache indexes to answer for disconnected nodes

**Success criteria:**
- Indexes published periodically
- Query "who has tomatoes?" returns results in <2 min (nearby) or <10 min (across islands)
- Cached indexes enable discovery when source offline

---

### 5. File Chunking System (TIER 1)
**Complexity:** 3 systems
**Priority:** High (enables offline knowledge)
**Status:** Draft

**What it does:**
- Content-addressed file distribution
- Chunking large files (256KB-1MB chunks)
- Opportunistic retrieval and reassembly

**Key requirements:**
- sha256 content addressing
- Chunking engine with manifest generation
- Chunks distributed as DTN bundles
- Reassembly with verification
- Library nodes cache and serve popular files

**Success criteria:**
- 10MB file retrieved in <30 min via library node
- Partial downloads resume correctly
- Final hash verified after reassembly

---

### 6. Multi-AP Mesh Network (TIER 1)
**Complexity:** 4 systems
**Priority:** High (real-world infrastructure)
**Status:** Draft

**What it does:**
- Multiple AP islands (Garden, Kitchen, Workshop, Library)
- Bridge nodes provide store-and-forward
- Mode C (DTN-only) always works
- Mode A (BATMAN-adv) optimizes when available

**Key requirements:**
- 3+ independent APs with separate subnets
- Bridge node configuration and behavior
- Mode C (DTN-only) foundation - mandatory
- Mode A (BATMAN-adv) for rooted phones - optional
- Graceful degradation Mode A → Mode C

**Success criteria:**
- 3+ APs operating independently
- Bundles propagate between islands in <10 min via bridge walks
- Mode C works reliably (all apps functional)
- Mode A provides speedup on supported devices
- Network handles 20+ concurrent users

---

### 7. Agent System / Commune OS (TIER 2)
**Complexity:** 7 systems
**Priority:** Medium (intelligence layer)
**Status:** Draft

**What it does:**
- 7 specialized agents provide intelligent coordination
- Proposal-based suggestions (human approval required)
- Make gift economy easy and efficient

**Key agents:**
1. **Commons Router Agent** - cache and forwarding optimization
2. **Mutual Aid Matchmaker** - offer/need matching
3. **Perishables Dispatcher** - time-sensitive food coordination
4. **Scheduler / Work Party Agent** - session and commitment planning
5. **Permaculture Seasonal Planner** - goals → seasonal → weekly planning
6. **Education Pathfinder** - just-in-time learning recommendations
7. **Inventory/Pantry Agent** - replenishment and shortage prediction (opt-in)

**Key requirements:**
- All agents emit proposals, NOT allocations
- Proposals include explanation, inputs used, constraints
- Human approval required (default)
- Agents are opt-in, no surveillance required
- Proposal approval UI

**Success criteria:**
- Matchmaker creates viable offer/need matches
- Perishables Dispatcher prioritizes expiring food
- Scheduler proposes work parties with optimal timing
- Permaculture Planner generates realistic seasonal plans
- Education Pathfinder recommends relevant lessons
- All proposals require human approval
- Agents work without surveillance

---

## Implementation Order (Recommended)

### Phase 1: Foundation (TIER 0)
**Build these in parallel, they're mostly independent:**

1. **DTN Bundle System** (5 systems) - START FIRST, required by everything
2. **ValueFlows Node** (6 systems) - START SECOND, can begin once DTN bundle format is defined
3. **Phone Deployment System** (3 systems) - START THIRD, builds APKs from #1 and #2

**Phase 1 Total:** 14 systems
**Agent allocation:** 2-3 feature-implementer agents in parallel

---

### Phase 2: Core Functionality (TIER 1)
**Build these after Phase 1 completes:**

4. **Discovery and Search** (3 systems) - Depends on DTN + ValueFlows
5. **File Chunking** (3 systems) - Depends on DTN
6. **Multi-AP Mesh Network** (4 systems) - Depends on DTN, can build in parallel with #4/#5

**Phase 2 Total:** 10 systems
**Agent allocation:** 2-3 feature-implementer agents in parallel

---

### Phase 3: Intelligence Layer (TIER 2)
**Build this after Phase 2 completes:**

7. **Agent System / Commune OS** (7 systems) - Depends on ValueFlows + Discovery + File Chunking

**Phase 3 Total:** 7 systems
**Agent allocation:** 1-2 feature-implementer agents (agents can be built sequentially)

---

## Orchestration Strategy

### Recommended Approach

Use the orchestrator agent to coordinate:

```typescript
Task({
  subagent_type: "orchestrator",
  description: "Build complete Solarpunk mesh network system",
  prompt: `
Build the complete Solarpunk gift economy mesh network system as specified in solarpunk_node_full_spec.md.

All proposals are in openspec/changes/:
- dtn-bundle-system (5 systems) - PRIORITY 1
- valueflows-node-full (6 systems) - PRIORITY 1
- phone-deployment-system (3 systems) - PRIORITY 1
- discovery-search-system (3 systems) - PRIORITY 2
- file-chunking-system (3 systems) - PRIORITY 2
- multi-ap-mesh-network (4 systems) - PRIORITY 2
- agent-commune-os (7 systems) - PRIORITY 3

Build in 3 phases:
Phase 1: Complete DTN, ValueFlows, Phone Deployment (can work in parallel where independent)
Phase 2: Complete Discovery, File Chunking, Multi-AP Network (after Phase 1)
Phase 3: Complete Agent System (after Phase 2)

For each proposal:
1. Have architect review and approve
2. Assign to feature-implementer agents (can run multiple in parallel)
3. Validate with pm-validator and test-validator
4. Archive when complete

This is a full production system, not a demo. Build everything specified in the proposals.
Must be ready for workshop where participants will actually use the system.
  `
})
```

---

## Quality Gates

Each proposal MUST pass:

1. **Architect approval** - Before implementation starts
2. **PM validation** - Requirements met, scenarios pass
3. **Test validation** - Tests exist and pass, no placeholders
4. **Field testing** - Tested on actual phones/network when applicable

---

## Workshop Readiness Checklist

Before the 6-hour workshop:

- [ ] All Phase 1 proposals completed and validated (DTN, ValueFlows, Phone Deployment)
- [ ] All Phase 2 proposals completed and validated (Discovery, File Chunking, Multi-AP Network)
- [ ] Phase 3 (Agents) completed if time permits, otherwise can be added post-workshop
- [ ] 20+ phones provisioned with complete software stack
- [ ] 3+ APs deployed and tested (Garden, Kitchen, Workshop)
- [ ] Bridge nodes configured and tested
- [ ] Offers/needs can be created and propagated between islands
- [ ] Matches and exchanges can be coordinated
- [ ] Files can be chunked and retrieved
- [ ] All phones charged >80%
- [ ] Quick-start guides printed
- [ ] Facilitators trained on troubleshooting

---

## Success Criteria for Workshop

Participants should be able to:

1. **Create offers and needs** (<2 min per item)
2. **Browse and search** offers/needs from others
3. **Accept matches** and coordinate exchanges
4. **Record events** when handoffs occur
5. **Move between AP islands** and see messages propagate
6. **Access offline knowledge** (protocols, lessons via Kiwix)
7. **Experience the gift economy** in action

---

## Post-Workshop Evolution

After workshop, system can evolve:

- Add more agents (Red Team security testing, Blue Team monitoring)
- Optimize Mode A (BATMAN-adv) for more devices
- Research Mode B (Wi-Fi Direct) viability
- Expand knowledge base (more Kiwix content)
- Integrate with external systems (Matrix, NATS for cross-commune coordination)
- Scale to multiple communes

---

## Documentation

Each proposal has:
- `proposal.md` - Requirements with SHALL/MUST, WHEN/THEN scenarios
- `tasks.md` - Implementation breakdown with complexity estimation

All proposals follow OpenSpec workflow:
- Draft → Architect Review → Approved → In Progress → Validation → Completed → Archived

---

## Contact

For questions about this build:
- Review: solarpunk_node_full_spec.md (source specification)
- Proposals: openspec/changes/* (detailed requirements)
- Workflow: openspec/AGENTS.md (agent coordination)

**Let's build the infrastructure for regenerative gift economy communities! 🌱**
