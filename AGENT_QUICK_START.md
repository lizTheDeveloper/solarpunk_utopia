# Agent System Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Run the Demo

```bash
python -m app.agents.example_usage
```

This will run all 7 agents and show:
- Proposal generation for each agent
- Approval workflow example
- Statistics

### 2. Use Individual Agents

```python
import asyncio
from app.agents import MutualAidMatchmaker, approval_tracker

async def main():
    # Create agent
    matchmaker = MutualAidMatchmaker()

    # Run analysis (generates proposals)
    proposals = await matchmaker.run()

    # Store proposals
    for proposal in proposals:
        await approval_tracker.store_proposal(proposal)

    # View proposals
    print(f"Generated {len(proposals)} proposals")
    for p in proposals:
        print(f"- {p.title}")

asyncio.run(main())
```

### 3. Approve Proposals

```python
# Get pending approvals for a user
pending = await approval_tracker.get_pending_approvals("alice")

# Approve a proposal
await approval_tracker.approve_proposal(
    proposal_id=pending[0].proposal_id,
    user_id="alice",
    approved=True,
    reason="Looks good!"
)
```

### 4. Use the API

Start the FastAPI server (once integrated):

```bash
uvicorn app.main:app --reload
```

Then use the API:

```bash
# List all proposals
curl http://localhost:8000/agents/proposals

# Get pending approvals for user
curl http://localhost:8000/agents/proposals/pending/alice

# Approve a proposal
curl -X POST http://localhost:8000/agents/proposals/PROPOSAL_ID/approve \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "approved": true,
    "reason": "Great match!"
  }'

# Update agent settings
curl -X PUT http://localhost:8000/agents/settings/mutual-aid-matchmaker \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "check_interval_seconds": 300
  }'
```

## The 7 Agents

### 1. Commons Router Agent
Optimizes cache and forwarding for your node role.

```python
from app.agents import CommonsRouterAgent

router = CommonsRouterAgent(
    node_role="bridge",  # citizen, bridge, ap, library
    cache_budget_mb=2048
)
proposals = await router.run()
```

### 2. Mutual Aid Matchmaker
Matches offers with needs using intelligent scoring.

```python
from app.agents import MutualAidMatchmaker

matchmaker = MutualAidMatchmaker()
proposals = await matchmaker.run()
# Creates proposals requiring approval from both parties
```

### 3. Perishables Dispatcher
Monitors expiring food and proposes urgent action.

```python
from app.agents import PerishablesDispatcher

dispatcher = PerishablesDispatcher()
proposals = await dispatcher.run()
# Urgency escalates as expiry approaches
```

### 4. Work Party Scheduler
Proposes work parties based on availability and skills.

```python
from app.agents import WorkPartyScheduler

scheduler = WorkPartyScheduler()
proposals = await scheduler.run()
# Finds optimal times and ensures skill coverage
```

### 5. Permaculture Seasonal Planner
Transforms goals into detailed seasonal plans.

```python
from app.agents import PermaculturePlanner

planner = PermaculturePlanner(climate_zone="9b")
proposals = await planner.run()
# Creates process sequences with dependencies
```

### 6. Education Pathfinder
Recommends just-in-time learning for upcoming tasks.

```python
from app.agents import EducationPathfinder

pathfinder = EducationPathfinder()
proposals = await pathfinder.run()
# Orders lessons by prerequisites
```

### 7. Inventory/Pantry Agent (OPT-IN)
Predicts shortages and proposes replenishment.

```python
from app.agents import InventoryAgent, AgentConfig

# Must explicitly opt-in (disabled by default)
inventory = InventoryAgent(
    config=AgentConfig(enabled=True)
)
proposals = await inventory.run()
```

## Configuration

Configure agents via AgentConfig:

```python
from app.agents import AgentConfig, MutualAidMatchmaker

config = AgentConfig(
    enabled=True,
    check_interval_seconds=300,  # 5 minutes
    proposal_ttl_hours=72,  # 3 days
    auto_approve=False  # Require human approval
)

agent = MutualAidMatchmaker(config=config)
```

## Proposal Structure

Every proposal includes:

```python
{
    "proposal_id": "prop:uuid",
    "agent_name": "mutual-aid-matchmaker",
    "proposal_type": "match",
    "title": "Match: tomatoes (Alice → Bob)",

    # Transparency (required)
    "explanation": "Alice has 5 lbs tomatoes...",
    "inputs_used": ["bundle:offer-alice", "bundle:need-bob"],
    "constraints": ["morning handoff", "container provided"],

    # Proposal-specific data
    "data": {
        "match_score": 0.85,
        "quantity": 5.0,
        "unit": "lbs"
    },

    # Approval tracking
    "requires_approval": ["alice", "bob"],
    "approvals": {},
    "status": "pending"
}
```

## Privacy & Ethics

- **Inventory Agent is OPT-IN:** Disabled by default
- **No surveillance:** System works without tracking
- **Transparent:** All inputs and reasoning visible
- **Human control:** All proposals require approval

## Next Steps

1. **Integrate with VF Database**
   - Connect agents to real data
   - Query actual offers, needs, plans

2. **Enable DTN Publishing**
   - Publish proposals as bundles
   - Sync across nodes

3. **Add Frontend UI**
   - Proposal approval interface
   - Agent settings dashboard

4. **Optional: Add LLM**
   - Set ANTHROPIC_API_KEY
   - Enable complex reasoning

## Troubleshooting

**Agent not generating proposals?**
- Check if agent is enabled: `agent.enabled`
- Verify data is available (currently uses mock data)

**Proposals not being approved?**
- Check required approvers: `proposal.requires_approval`
- Verify approval status: `proposal.status`

**Want to auto-approve for testing?**
```python
config = AgentConfig(auto_approve=True)
agent = MutualAidMatchmaker(config=config)
```

## Documentation

- Full documentation: `app/agents/README.md`
- Implementation summary: `AGENT_SYSTEM_SUMMARY.md`
- Example code: `app/agents/example_usage.py`
- API docs: FastAPI auto-generated at `/docs`

## Support

All agents follow these guardrails:
1. Proposals, not allocations (no unilateral decisions)
2. Human approval required (configurable)
3. Transparent reasoning (all inputs visible)
4. Privacy-respecting (opt-in only)
5. Configurable (can be disabled)

The agent system makes the gift economy smart while keeping humans in control.
