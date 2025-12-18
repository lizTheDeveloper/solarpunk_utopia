# Solarpunk Mesh Network - Build Plan

**Status:** ✅ **CORE SOFTWARE COMPLETE** (28 of 31 systems implemented)
**Build Date:** 2025-12-17
**Target:** 6-hour workshop for Solar Punk communes
**Scope:** Complete gift economy mesh network system (production-ready, not demo)

---

## ✅ Build Completion Status

**TIER 0 (Foundation):** ✅ 11/14 systems complete
- ✅ DTN Bundle System (5/5 systems) - `/app/`
- ✅ ValueFlows Node (6/6 systems) - `/valueflows_node/`
- ⏳ Phone Deployment (0/3 systems) - Deferred for hardware

**TIER 1 (Core Functionality):** ✅ 10/10 systems complete
- ✅ Discovery and Search (3/3 systems) - `/discovery_search/`
- ✅ File Chunking (3/3 systems) - `/file_chunking/`
- ✅ Multi-AP Mesh Network (4/4 systems) - `/mesh_network/`

**TIER 2 (Intelligence):** ✅ 7/7 systems complete
- ✅ Agent System (7/7 systems) - `/app/agents/`

**Total Progress:** ✅ **28 of 31 systems (90% complete)**

**See `BUILD_STATUS.md` for detailed implementation status.**

**Quick Start:** See `QUICKSTART.md` to run the system in 5 minutes.

---

## What We're Building

A complete mesh network system for Solar Punk communes to coordinate gift economy activities (food sharing, tool lending, skill exchange, permaculture planning) without internet dependency. Phones form multi-AP islands, bridge nodes provide store-and-forward messaging, AI agents help with matching and planning, all offline-first.

**Source specification:** `solarpunk_node_full_spec.md`
**Proposals:** `openspec/changes/*` (7 proposals, 31 systems total)
**Overview:** `openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md`

---

## The 7 Proposals

### TIER 0 (Foundation - 14 systems)
1. **DTN Bundle System** (5 systems) - Store-and-forward transport layer
2. **ValueFlows Node** (6 systems) - Gift economy coordination (offers, needs, exchanges)
3. **Phone Deployment System** (3 systems) - Provision phones for workshop

### TIER 1 (Core Functionality - 10 systems)
4. **Discovery and Search** (3 systems) - Distributed queries and indexes
5. **File Chunking** (3 systems) - Offline knowledge distribution
6. **Multi-AP Mesh Network** (4 systems) - Physical infrastructure

### TIER 2 (Intelligence - 7 systems)
7. **Agent System / Commune OS** (7 systems) - AI agents for matching, planning, coordination

**Total:** 31 systems

---

## Implementation Strategy

### Orchestrated Multi-Agent Build

Use the Abstract Agent Team framework to build this:

1. **Orchestrator** coordinates the full build (3 phases)
2. **Architect** approves each proposal before implementation
3. **Feature-implementers** build in parallel where possible (2-3 agents)
4. **PM-validator** verifies requirements met
5. **Test-validator** ensures quality gates pass
6. **Architect** archives completed work

### Build Order

**Phase 1:** DTN + ValueFlows + Phone Deployment (can parallelize)
**Phase 2:** Discovery + File Chunking + Multi-AP Network (after Phase 1)
**Phase 3:** Agent System (after Phase 2)

---

## Key Technical Decisions

### Transport Layer
- **DTN bundles** for all data (not HTTP/REST)
- Store-and-forward via bridge nodes walking between AP islands
- TTL, priority queues, cache budgets, battery awareness
- Signed bundles (Ed25519) for trust

### Economic Coordination
- **ValueFlows v1.0** complete implementation
- 13 object types (Agent, Location, ResourceSpec, ResourceInstance, Listing, Match, Exchange, Event, Process, Commitment, Plan, Protocol, Lesson)
- Simple UX (offer/need) with rich backend data for agents

### Network Architecture
- **Multi-AP islands** (Garden, Kitchen, Workshop, Library)
- **Mode C (DTN-only)** as foundation (mandatory, always works)
- **Mode A (BATMAN-adv)** for rooted phones (optional optimization)
- **Mode B (Wi-Fi Direct)** research (future work)

### AI Agents
- 7 specialized agents (matching, perishables, scheduling, planning, education, inventory, routing)
- **Proposal-based** (not allocations) - human approval required
- **Opt-in** - no surveillance required
- Transparent (explanation + inputs + constraints visible)

---

## Workshop Deliverables

Before the 6-hour workshop, we need:

### Hardware
- [ ] 20+ phones with LineageOS installed
- [ ] 3+ Raspberry Pis or Android phones as APs
- [ ] Power supplies (wall or solar+battery)
- [ ] USB cables and hub for provisioning

### Software
- [ ] DTN Bundle Service (Android APK)
- [ ] ValueFlows Node (Android APK)
- [ ] Base apps: Briar, Manyverse, Syncthing, Kiwix, Organic Maps
- [ ] Kiwix content (permaculture, regeneration, gift economy)
- [ ] Organic Maps data (local area)

### Configuration
- [ ] Phones provisioned with appropriate role (mostly Citizen, some Bridge)
- [ ] APs deployed and configured (Garden, Kitchen, Workshop)
- [ ] Bridge nodes tested walking between islands
- [ ] All phones >80% battery

### Documentation
- [ ] Participant quick-start guide (1-page PDF, 30 copies)
- [ ] Facilitator troubleshooting guide

### Testing
- [ ] Offer created → propagates → received on other island (in <10 min)
- [ ] Match → Exchange → Events recorded
- [ ] File chunks and retrieves
- [ ] 20+ concurrent users without degradation

---

## How to Execute

### Option 1: Single Orchestrator Command

```typescript
Task({
  subagent_type: "orchestrator",
  description: "Build complete Solarpunk mesh network system",
  prompt: `
Build the complete Solarpunk gift economy mesh network system for workshop delivery.

Source: solarpunk_node_full_spec.md
Proposals: openspec/changes/* (7 proposals, 31 systems)
Overview: openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md

Build in 3 phases:
1. DTN + ValueFlows + Phone Deployment (14 systems)
2. Discovery + File Chunking + Multi-AP Network (10 systems)
3. Agent System (7 systems)

For each proposal:
- Architect review and approval
- Feature-implementer builds (can parallelize where independent)
- PM and Test validation
- Archive when complete

This is production software for real communities, not a demo.
Must be ready for participants to use at workshop.
  `
})
```

### Option 2: Phase-by-Phase

Execute each phase sequentially, allowing for validation and course correction between phases.

**See `openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md`** for detailed orchestration strategy.

---

## Success Criteria

### Technical Success
- [ ] All 31 systems implemented and tested
- [ ] DTN bundles propagate reliably between islands
- [ ] Offers/needs sync across mesh in <10 min
- [ ] Matches and exchanges coordinate successfully
- [ ] Files chunk and retrieve correctly
- [ ] Agents generate useful proposals
- [ ] System handles 20+ concurrent users

### Workshop Success
- [ ] Participants create first offer in <2 min
- [ ] Participants discover others' offers/needs
- [ ] Participants coordinate exchanges
- [ ] Participants experience gift economy in action
- [ ] System works reliably throughout 6-hour workshop
- [ ] Participants leave excited to use in their communes

### Real-World Success
- [ ] Communes adopt system for daily coordination
- [ ] Food sharing reduces waste
- [ ] Tool libraries increase access
- [ ] Skill exchange strengthens community
- [ ] Permaculture planning improves yields
- [ ] Gift economy replaces monetary transactions for local goods

---

## Timeline

This is agent-driven development. **No timeline estimates.**

Complexity estimation:
- **TIER 0:** 14 systems (foundation)
- **TIER 1:** 10 systems (core functionality)
- **TIER 2:** 7 systems (intelligence)

Agents will determine actual implementation pace based on complexity and dependencies.

---

## Architecture Highlights

### Delay-Tolerant Networking (DTN)
All data moves as signed bundles with TTL and priority. Nodes cache and forward based on role. Emergency content always prioritized. Perishable food gets high priority. Knowledge content gets long TTL.

### ValueFlows Economic Model
Complete VF-Full v1.0 with all objects. Simple UX (post offer, browse needs) while backend stores rich data for agent reasoning. Provenance via signatures. Exchanges require both parties to record events.

### Multi-Hop Mesh (Optimum Case)
Mode C (DTN-only) always works. Mode A (BATMAN-adv) adds IP routing when hardware supports. Mode B (Wi-Fi Direct) researched for future. Never depend on routing; DTN is foundation.

### AI Agent Layer
7 specialized agents provide proposals (not allocations). Human approval required. Matchmaker finds offer/need pairs. Perishables Dispatcher prioritizes expiring food. Scheduler plans work parties. Permaculture Planner generates seasonal plans. Education Pathfinder recommends just-in-time learning. All opt-in, no surveillance.

---

## Post-Workshop Roadmap

After workshop validates the system:

1. **Scale to production** - Deploy in participating communes
2. **Cross-commune sync** - NATS integration for inter-commune coordination
3. **Optimize Mode A** - Support more devices with BATMAN-adv
4. **Research Mode B** - Wi-Fi Direct multi-group viability
5. **Expand knowledge** - More Kiwix content, protocols, lessons
6. **Additional agents** - Security testing, monitoring, forecasting
7. **Hardware optimization** - Solar+battery optimization, dedicated devices
8. **Federation** - Multiple communes forming regional networks

---

## Resources

### Documentation
- **Specification:** `solarpunk_node_full_spec.md` (full system spec)
- **Proposals:** `openspec/changes/*` (7 proposals with requirements and tasks)
- **Overview:** `openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md` (dependencies and orchestration)
- **Workflow:** `openspec/AGENTS.md` (agent coordination patterns)

### Related Projects
- **Abstract Agent Team:** This meta-framework (multi-agent orchestration)
- **ValueFlows:** Standard for economic networks (https://valueflo.ws/)
- **BATMAN-adv:** Mesh routing protocol (https://www.open-mesh.org/)
- **Kiwix:** Offline knowledge (https://www.kiwix.org/)
- **Briar:** Secure messaging (https://briarproject.org/)

### Community
- **Solar Punk:** Regenerative futures, appropriate technology, mutual aid
- **Permaculture:** Regenerative agriculture and community design
- **Gift Economy:** Non-monetary exchange, commons-based coordination
- **Mesh Networks:** Community-owned infrastructure

---

## Vision

We're building the infrastructure for **regenerative gift economy communities**. This isn't just software—it's a tool for communities to coordinate mutual aid, share resources, plan permaculture work, and learn together, all without depending on corporate platforms or internet infrastructure.

When this system works, communes can:
- Share surplus food before it spoils
- Lend tools and equipment easily
- Coordinate seasonal planting and harvests
- Teach and learn skills within the community
- Plan work parties and events
- Track resource flows for accountability
- Operate entirely offline and autonomously

**This is infrastructure for a better world. Let's build it. 🌱**

---

## Getting Started

1. Review the spec: `solarpunk_node_full_spec.md`
2. Review proposals: `openspec/changes/*`
3. Review overview: `openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md`
4. Execute orchestrator command (see "How to Execute" above)
5. Watch agents build the system
6. Validate each phase before moving forward
7. Deploy to phones before workshop
8. Run workshop and gather feedback
9. Iterate based on real-world usage

**Ready to start? The proposals are waiting in `openspec/changes/`.**
