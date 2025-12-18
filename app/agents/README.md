# Commune OS Agent System

7 specialized AI agents that provide intelligent coordination for the gift economy.

## Overview

All agents emit **proposals** (not allocations) that require human approval. This ensures human oversight while benefiting from AI-powered coordination and planning.

## The 7 Agents

### 1. Commons Router Agent
**Purpose:** Optimizes cache and forwarding decisions based on node role.

**Creates proposals for:**
- Cache evictions when budget exceeded
- Priority adjustments for cached bundles
- Forwarding policies for bridge nodes

**Key features:**
- Prioritizes emergency bundles (always cached)
- Keeps perishables with <48h TTL
- Optimizes for node role (citizen, bridge, AP, library)

### 2. Mutual Aid Matchmaker
**Purpose:** Matches offers with needs based on multiple criteria.

**Creates proposals for:**
- Offer/need matches with both parties' approval

**Scoring criteria:**
- Category match (40%)
- Location proximity (30%)
- Time overlap (20%)
- Quantity fit (10%)

**Key features:**
- Requires approval from both parties
- Explains reasoning with scores
- Suggests handoff time and location

### 3. Perishables Dispatcher
**Purpose:** Monitors expiring food and proposes urgent redistribution.

**Creates proposals for:**
- Urgent exchanges (12-48h until expiry)
- Batch cooking events (if no individual needs)
- Critical actions (<12h until expiry)

**Key features:**
- Monitors ResourceInstance.expiry_date
- Escalates urgency as expiry approaches
- Suggests preservation methods

### 4. Scheduler / Work Party Agent
**Purpose:** Proposes work party sessions based on availability and skills.

**Creates proposals for:**
- Work party sessions (time, location, participants, resources)

**Analyzes:**
- Participant availability
- Required skills and skill coverage
- Resource availability
- Weather conditions (for outdoor work)

**Key features:**
- Finds optimal time slots
- Ensures skill coverage
- Checks resource availability

### 5. Permaculture Seasonal Planner
**Purpose:** Transforms goals into seasonal plans with processes and dependencies.

**Creates proposals for:**
- Seasonal plans with process sequences
- Timeline based on climate and season

**Uses permaculture knowledge:**
- Guild plantings (companion species)
- Seasonal timing
- Process dependencies
- Resource requirements

**Key features:**
- LLM-powered reasoning (if available)
- Rule-based fallback for common patterns
- Detailed process sequences with dependencies

### 6. Education Pathfinder
**Purpose:** Recommends just-in-time learning for upcoming commitments.

**Creates proposals for:**
- Learning paths with prerequisites ordered
- Lesson recommendations tied to upcoming work

**Analyzes:**
- Upcoming Commitments
- User's existing skills
- Available Lessons and Protocols
- Prerequisite relationships

**Key features:**
- Just-in-time recommendations (days before task)
- Orders prerequisites first
- Creates learning schedules

### 7. Inventory/Pantry Agent (Opt-In)
**Purpose:** Predicts inventory shortages and proposes replenishment.

**Creates proposals for:**
- Replenishment needs
- Shortage warnings

**Analyzes:**
- Current inventory levels
- Historical usage rates
- Upcoming Plans requiring resources

**Key features:**
- **OPT-IN ONLY** (disabled by default)
- Privacy-preserving
- Suggests alternatives before external sourcing

## Guardrails (Non-Negotiable)

All agents follow these principles:

1. **Proposals, not allocations:** Agents NEVER make unilateral decisions
2. **Human approval required:** All proposals need ratification (configurable)
3. **Transparency:** Every proposal includes:
   - `explanation`: Human-readable rationale
   - `inputs_used`: Data sources that informed decision
   - `constraints`: Relevant limitations
4. **Privacy-respecting:** No surveillance required to participate
5. **Opt-in:** All agents can be disabled per user preference

## API Endpoints

### List Proposals
```
GET /agents/proposals
  ?agent_name=mutual-aid-matchmaker
  &status=pending
  &user_id=alice
```

### Get Pending Approvals for User
```
GET /agents/proposals/pending/{user_id}
```

### Get Proposal Details
```
GET /agents/proposals/{proposal_id}
```

### Approve Proposal
```
POST /agents/proposals/{proposal_id}/approve
{
  "user_id": "alice",
  "approved": true,
  "reason": "Good match, I can do morning handoff"
}
```

### Reject Proposal
```
POST /agents/proposals/{proposal_id}/reject
{
  "user_id": "alice",
  "approved": false,
  "reason": "Cannot make that time"
}
```

### Get Agent Settings
```
GET /agents/settings
GET /agents/settings/{agent_name}
```

### Update Agent Settings
```
PUT /agents/settings/{agent_name}
{
  "enabled": true,
  "check_interval_seconds": 300,
  "proposal_ttl_hours": 72,
  "auto_approve": false
}
```

### Get Agent Statistics
```
GET /agents/stats
GET /agents/stats/{agent_name}
```

### Manually Run Agent
```
POST /agents/run/{agent_name}
```

## Usage Examples

### Running Agents

```python
from app.agents import MutualAidMatchmaker, approval_tracker

# Create agent
matchmaker = MutualAidMatchmaker(
    config={"enabled": True, "check_interval_seconds": 300},
    db_client=db,
    bundle_publisher=publisher,
)

# Run analysis
proposals = await matchmaker.run()

# Store proposals
for proposal in proposals:
    await approval_tracker.store_proposal(proposal)
```

### Approving Proposals

```python
from app.agents import approval_tracker

# Get pending approvals for user
pending = await approval_tracker.get_pending_approvals("alice")

# Approve a proposal
proposal = await approval_tracker.approve_proposal(
    proposal_id="prop:123",
    user_id="alice",
    approved=True,
    reason="Looks good!"
)

# Check if fully approved
if proposal.is_fully_approved():
    # Execute the approved action
    # (Implementation specific to proposal type)
    pass
```

### Configuring Agents

```python
from app.agents import AgentConfig, InventoryAgent

# Enable inventory agent (opt-in)
config = AgentConfig(
    enabled=True,
    check_interval_seconds=3600,  # Check hourly
    proposal_ttl_hours=168,  # 1 week
)

agent = InventoryAgent(config=config)
```

## Integration with ValueFlows

Agents query VF data structures:

- **Offers/Needs:** Mutual Aid Matchmaker
- **ResourceInstance.expiry_date:** Perishables Dispatcher
- **Plans/Processes:** Work Party Scheduler, Permaculture Planner
- **Commitments:** Education Pathfinder
- **Events (consume/produce):** Inventory Agent

## Integration with DTN Bundles

All proposals are published as DTN bundles:

```python
bundle_payload = proposal.to_bundle_payload()
# {
#   "type": "agent-proposal",
#   "proposal": { ... }
# }

bundle_id = await bundle_publisher.publish(
    payload=bundle_payload,
    topic="mutual-aid",
    priority="normal",
    tags=["agent-proposal", "match"],
)
```

## LLM Integration (Optional)

Agents can use Claude API for complex reasoning:

```python
from anthropic import Anthropic

llm_client = Anthropic(api_key="...")

agent = PermaculturePlanner(llm_client=llm_client)
```

Agents gracefully degrade to rule-based logic if LLM unavailable.

## Privacy & Ethics

- **Inventory Agent is OPT-IN:** Disabled by default
- **No surveillance required:** System works without inventory tracking
- **Transparent reasoning:** All inputs and logic visible
- **User control:** Agents can be disabled individually

## Development

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Implement `analyze()` method
3. Return list of `Proposal` objects
4. Add to API router
5. Update documentation

### Testing Agents

```python
# Mock data approach (current)
agent = MutualAidMatchmaker()
proposals = await agent.analyze()

# Once DB integrated
agent = MutualAidMatchmaker(db_client=db)
proposals = await agent.analyze()
```

## Future Enhancements

- [ ] Database persistence for proposals
- [ ] Scheduled agent runs (cron-like)
- [ ] LLM integration for complex reasoning
- [ ] Weather API integration (Work Party Scheduler)
- [ ] Machine learning for match scoring
- [ ] Frontend UI for proposal approval
- [ ] Notification system for pending approvals
- [ ] Execution engine for approved proposals

## Architecture

```
app/agents/
├── framework/
│   ├── proposal.py       # Proposal data model
│   ├── base_agent.py     # Base agent class
│   ├── approval.py       # Approval tracking
│   └── __init__.py
├── commons_router.py     # Cache/forwarding optimization
├── mutual_aid_matchmaker.py  # Offer/need matching
├── perishables_dispatcher.py  # Expiring food coordination
├── work_party_scheduler.py   # Session planning
├── permaculture_planner.py   # Seasonal planning
├── education_pathfinder.py   # Learning recommendations
├── inventory_agent.py    # Shortage prediction (opt-in)
└── __init__.py

app/api/
└── agents.py            # API endpoints
```

## Success Criteria

- [x] All 7 agents implemented
- [x] Agents emit proposals, not allocations
- [x] Proposals include explanation, inputs, constraints
- [x] Human approval required (configurable)
- [x] Agents are opt-in (can be disabled)
- [x] API endpoints functional
- [ ] Proposal approval UI (frontend)
- [ ] Integration with VF database
- [ ] Integration with DTN bundle system
- [ ] LLM client integration (optional)

## License

This is part of the Solarpunk Commune OS project.
