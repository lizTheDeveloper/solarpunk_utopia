# Implementation Tasks: Agent System (Commune OS)

**Proposal:** agent-commune-os
**Complexity:** 7 systems (one per agent)

---

## Task Breakdown

### System 1: Commons Router Agent (0.8 systems)

**Task 1.1: Implement cache decision logic**
- Analyze current cache usage
- Prioritize based on: emergency, perishables, access frequency
- Propose evictions when budget exceeded
- **Complexity:** 0.5 systems

**Task 1.2: Implement forwarding optimization**
- Decide which bundles to forward given bandwidth budget
- Prioritize based on node role (bridge vs citizen)
- **Complexity:** 0.3 systems

---

### System 2: Mutual Aid Matchmaker (1.2 systems)

**Task 2.1: Implement matching algorithm**
- Query offers and needs
- Score matches based on: category match, location proximity, time overlap, quantity fit
- **Complexity:** 0.6 systems

**Task 2.2: Implement proposal generation**
- Create Match proposal with explanation
- Include constraints from both parties
- Publish proposal bundle
- **Complexity:** 0.4 systems

**Task 2.3: Implement approval tracking**
- Track which parties have approved
- Create Exchange when both approve
- **Complexity:** 0.2 systems

---

### System 3: Perishables Dispatcher (1.0 systems)

**Task 3.1: Implement expiry detection**
- Monitor InventoryIndex for soon-expiring food
- Calculate urgency (hours until expiry)
- **Complexity:** 0.4 systems

**Task 3.2: Implement urgent matching**
- Find needs or propose batch cooking event
- Prioritize bundles with high priority
- Generate urgent proposals
- **Complexity:** 0.4 systems

**Task 3.3: Implement notification escalation**
- Notify progressively more people as expiry approaches
- Suggest preservation methods if no takers
- **Complexity:** 0.2 systems

---

### System 4: Scheduler / Work Party Agent (1.2 systems)

**Task 4.1: Implement availability analysis**
- Query participant availability (from Commitments or calendar)
- Find optimal time slots
- **Complexity:** 0.4 systems

**Task 4.2: Implement work party proposal**
- Generate session with participants, location, resources
- Explain rationale (weather, availability, skill mix)
- **Complexity:** 0.5 systems

**Task 4.3: Implement resource coordination**
- Verify resources available (tools, seeds, etc.)
- Propose acquiring missing resources
- **Complexity:** 0.3 systems

---

### System 5: Permaculture Seasonal Planner (1.5 systems)

**Task 5.1: Implement goal → Plan transformation**
- Parse high-level goal
- Generate Process sequence with dependencies
- **Complexity:** 0.6 systems

**Task 5.2: Implement permaculture knowledge integration**
- Use protocols (guilds, companion planting, seasonal cycles)
- Calculate timing based on climate/location
- **Complexity:** 0.5 systems

**Task 5.3: Implement Plan proposal generation**
- Create complete Plan with Processes, Commitments, Resources
- Explain dependencies and timing
- **Complexity:** 0.4 systems

---

### System 6: Education Pathfinder (1.0 systems)

**Task 6.1: Implement task → Lesson mapping**
- Analyze upcoming Commitment or Process
- Find relevant Lessons (by tags, skills)
- **Complexity:** 0.4 systems

**Task 6.2: Implement learning path generation**
- Order Lessons (prerequisites first)
- Recommend just-in-time (days before task)
- **Complexity:** 0.4 systems

**Task 6.3: Implement recommendation UI**
- Display recommended Lessons
- Track completion (optional)
- **Complexity:** 0.2 systems

---

### System 7: Inventory/Pantry Agent (1.0 systems)

**Task 7.1: Implement usage tracking (opt-in)**
- Analyze Events (consume, produce)
- Calculate usage rates
- **Complexity:** 0.4 systems

**Task 7.2: Implement shortage prediction**
- Compare current inventory to upcoming Plans
- Identify gaps
- **Complexity:** 0.4 systems

**Task 7.3: Implement replenishment proposals**
- Propose creating Needs
- Suggest alternatives (internal sourcing, substitutes)
- **Complexity:** 0.2 systems

---

## Framework Tasks (included in each agent)

**Task F1: Agent proposal framework**
- Proposal schema (explanation, inputsUsed, constraints)
- Proposal publishing (as DTN bundle)
- Approval tracking
- **Complexity:** included in each agent

**Task F2: Agent settings UI**
- Enable/disable per agent
- Configure behavior (e.g., urgency thresholds)
- **Complexity:** 0.3 systems (shared across agents)

**Task F3: Proposal approval UI**
- View proposals
- Approve/reject with reason
- Track approval status
- **Complexity:** 0.4 systems (shared across agents)

---

## Validation Checklist

- [ ] Agent framework supports proposals
- [ ] Commons Router proposes cache optimizations
- [ ] Matchmaker creates offer/need matches
- [ ] Perishables Dispatcher identifies expiring food
- [ ] Scheduler proposes work parties
- [ ] Permaculture Planner generates seasonal Plans
- [ ] Education Pathfinder recommends Lessons
- [ ] Inventory Agent predicts shortages
- [ ] All proposals include explanation, inputs, constraints
- [ ] Approval required before execution
- [ ] Agent settings UI allows opt-in/out
- [ ] Proposal approval UI functional
- [ ] Agents work without surveillance (opt-in)

---

## Total Complexity: 7 Systems

- Commons Router: 0.8 systems
- Mutual Aid Matchmaker: 1.2 systems
- Perishables Dispatcher: 1.0 systems
- Scheduler / Work Party: 1.2 systems
- Permaculture Seasonal Planner: 1.5 systems
- Education Pathfinder: 1.0 systems
- Inventory/Pantry: 1.0 systems
- Shared framework (settings, approval UI): 0.7 systems
