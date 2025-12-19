# Tasks: GAP-04 Seed Demo Data

## Implementation (3-4 hours)

### Task 1: Create seed script structure
**File**: `scripts/seed_demo_data.py` (new)
**Estimated**: 30 minutes

```python
#!/usr/bin/env python3
"""
Seed demo data for Solarpunk commune demo.
Creates realistic data: community, agents, offers, needs, proposals.
"""
import asyncio
import httpx
from datetime import datetime, timedelta

VF_BASE = "http://localhost:8001"
AGENTS_BASE = "http://localhost:8000"

async def clear_demo_data():
    """Delete existing demo data"""
    # TODO: Implement
    pass

async def create_community():
    """Create Sunrise Collective community"""
    # TODO: Implement
    pass

async def create_demo_agents():
    """Create 10 demo agents (people)"""
    # TODO: Implement
    pass

async def create_locations():
    """Create 5 commune locations"""
    # TODO: Implement
    pass

async def create_resource_specs():
    """Create 15 resource specifications"""
    # TODO: Implement
    pass

async def create_offers():
    """Create 20 demo offers"""
    # TODO: Implement
    pass

async def create_needs():
    """Create 10 demo needs"""
    # TODO: Implement
    pass

async def create_proposals():
    """Create 3 pending agent proposals"""
    # TODO: Implement
    pass

async def main():
    print("🌱 Seeding demo data...")
    await clear_demo_data()
    await create_community()
    await create_demo_agents()
    await create_locations()
    await create_resource_specs()
    await create_offers()
    await create_needs()
    await create_proposals()
    print("✅ Demo data created!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Task 2: Implement community creation
**Estimated**: 15 minutes

```python
async def create_community():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VF_BASE}/communities/",
            json={
                "name": "Sunrise Collective",
                "description": "A resilient gift economy community",
                "is_public": True
            }
        )
        community = response.json()
        print(f"✓ Created community: {community['name']}")
        return community['id']
```

### Task 3: Implement demo agents creation
**Estimated**: 30 minutes

```python
DEMO_AGENTS = [
    {"name": "Alice", "skills": "Experienced gardener"},
    {"name": "Bob", "skills": "Carpenter and builder"},
    {"name": "Carol", "skills": "Preserving and canning expert"},
    {"name": "Dave", "skills": "Permaculture designer"},
    {"name": "Eve", "skills": "Herbalist and healer"},
    {"name": "Frank", "skills": "Mechanic and tool repair"},
    {"name": "Grace", "skills": "Community organizer"},
    {"name": "Hank", "skills": "Forager and wildcrafting"},
    {"name": "Iris", "skills": "Textile arts and mending"},
    {"name": "Jack", "skills": "Renewable energy tech"}
]

async def create_demo_agents(community_id: str):
    async with httpx.AsyncClient() as client:
        agents = []
        for agent_data in DEMO_AGENTS:
            response = await client.post(
                f"{VF_BASE}/vf/agents/",
                json={
                    "name": agent_data["name"],
                    "note": agent_data["skills"],
                    "community_id": community_id
                }
            )
            agent = response.json()
            agents.append(agent)
            print(f"✓ Created agent: {agent['name']}")
        return agents
```

### Task 4: Implement locations creation
**Estimated**: 15 minutes

```python
LOCATIONS = [
    "North Garden",
    "South Garden",
    "Tool Shed",
    "Community Kitchen",
    "Workshop"
]

async def create_locations(community_id: str):
    # Store in database or use predefined list
    print(f"✓ Created {len(LOCATIONS)} locations")
    return LOCATIONS
```

### Task 5: Implement resource specs creation
**Estimated**: 30 minutes

```python
RESOURCE_SPECS = [
    {"name": "Tomatoes", "unit": "kg", "category": "food"},
    {"name": "Eggs", "unit": "dozen", "category": "food"},
    {"name": "Hand Tools", "unit": "item", "category": "tools"},
    {"name": "Carpentry Skills", "unit": "hours", "category": "skills"},
    {"name": "Preserve Jars", "unit": "units", "category": "supplies"},
    {"name": "Herbal Remedies", "unit": "units", "category": "health"},
    {"name": "Workshop Space", "unit": "hours", "category": "space"},
    {"name": "Bicycle Repair", "unit": "service", "category": "skills"},
    {"name": "Sewing/Mending", "unit": "hours", "category": "skills"},
    {"name": "Solar Panel Maintenance", "unit": "service", "category": "skills"},
    {"name": "Wild Mushrooms", "unit": "kg", "category": "food"},
    {"name": "Chamomile Tea", "unit": "g", "category": "food"},
    {"name": "Facilitation Tools", "unit": "set", "category": "supplies"},
    {"name": "Permaculture Consultation", "unit": "hours", "category": "skills"},
    {"name": "Clothing Mending", "unit": "hours", "category": "skills"}
]

async def create_resource_specs(community_id: str):
    async with httpx.AsyncClient() as client:
        specs = []
        for spec_data in RESOURCE_SPECS:
            response = await client.post(
                f"{VF_BASE}/vf/resource-specifications/",
                json={
                    "name": spec_data["name"],
                    "default_unit_of_effort": spec_data["unit"],
                    "note": spec_data["category"],
                    "community_id": community_id
                }
            )
            spec = response.json()
            specs.append(spec)
        print(f"✓ Created {len(specs)} resource specifications")
        return specs
```

### Task 6: Implement offers creation
**Estimated**: 45 minutes

```python
async def create_offers(community_id: str, agents: List[Dict], specs: List[Dict]):
    async with httpx.AsyncClient() as client:
        offers_data = [
            {
                "agent_id": find_agent(agents, "Alice")["id"],
                "resource_spec_id": find_spec(specs, "Tomatoes")["id"],
                "quantity": 5,
                "location": "North Garden",
                "ttl_hours": 72,
                "note": "Fresh heirloom tomatoes"
            },
            {
                "agent_id": find_agent(agents, "Bob")["id"],
                "resource_spec_id": find_spec(specs, "Carpentry Skills")["id"],
                "quantity": 4,
                "location": "Workshop",
                "ttl_hours": 168,
                "note": "Available next week"
            },
            # ... more offers
        ]

        offers = []
        for offer_data in offers_data:
            response = await client.post(
                f"{VF_BASE}/vf/listings/",
                json={
                    **offer_data,
                    "listing_type": "offer",
                    "community_id": community_id
                }
            )
            offer = response.json()
            offers.append(offer)

        print(f"✓ Created {len(offers)} offers")
        return offers

def find_agent(agents: List[Dict], name: str) -> Dict:
    return next(a for a in agents if a["name"] == name)

def find_spec(specs: List[Dict], name: str) -> Dict:
    return next(s for s in specs if s["name"] == name)
```

### Task 7: Implement needs creation
**Estimated**: 30 minutes

```python
async def create_needs(community_id: str, agents: List[Dict], specs: List[Dict]):
    async with httpx.AsyncClient() as client:
        needs_data = [
            {
                "agent_id": find_agent(agents, "Bob")["id"],
                "resource_spec_id": find_spec(specs, "Tomatoes")["id"],
                "quantity": 2,
                "location": "Community Kitchen",
                "note": "For family dinner tonight"
            },
            {
                "agent_id": find_agent(agents, "Alice")["id"],
                "resource_spec_id": find_spec(specs, "Carpentry Skills")["id"],
                "quantity": 2,
                "note": "Help building raised bed"
            },
            # ... more needs
        ]

        needs = []
        for need_data in needs_data:
            response = await client.post(
                f"{VF_BASE}/vf/listings/",
                json={
                    **need_data,
                    "listing_type": "need",
                    "community_id": community_id
                }
            )
            need = response.json()
            needs.append(need)

        print(f"✓ Created {len(needs)} needs")
        return needs
```

### Task 8: Implement proposals creation
**Estimated**: 30 minutes

```python
async def create_proposals(community_id: str, agents: List[Dict]):
    """Create 3 pending agent proposals"""
    async with httpx.AsyncClient() as client:
        # Trigger agents to create proposals
        # This is tricky - may need to directly insert proposals or run agents

        # Option 1: Run mutual-aid-matchmaker
        response = await client.post(
            f"{AGENTS_BASE}/agents/mutual-aid-matchmaker/run",
            json={"community_id": community_id}
        )

        # Option 2: Directly create proposals (if API supports it)
        # ...

        print("✓ Created 3 pending proposals")
```

### Task 9: Add clear_demo_data function
**Estimated**: 30 minutes

```python
async def clear_demo_data():
    """Delete existing demo data (idempotency)"""
    async with httpx.AsyncClient() as client:
        # Delete community "Sunrise Collective" if exists
        # This will cascade delete all related data
        try:
            # Get community by name
            response = await client.get(f"{VF_BASE}/communities/")
            communities = response.json()
            sunrise = next((c for c in communities if c["name"] == "Sunrise Collective"), None)

            if sunrise:
                await client.delete(f"{VF_BASE}/communities/{sunrise['id']}")
                print("✓ Cleared existing demo data")
        except Exception as e:
            print(f"Note: {e}")
```

## Testing (30 minutes)

### Task 10: Test script execution
**Estimated**: 30 minutes

```bash
# Test on empty database
python scripts/seed_demo_data.py

# Verify data created
curl http://localhost:8001/vf/listings/ | jq '.count'  # Should be 30
curl http://localhost:8000/agents/proposals | jq '.total'  # Should be 3

# Test idempotency - run again
python scripts/seed_demo_data.py

# Verify no duplicates
curl http://localhost:8001/vf/listings/ | jq '.count'  # Still 30

# Check frontend
open http://localhost
# Navigate to Offers, Needs, Agents pages
```

## Documentation (15 minutes)

### Task 11: Add README instructions
**File**: `scripts/README.md` or main README
**Estimated**: 15 minutes

```markdown
## Seed Demo Data

To populate the database with demo data:

```bash
python scripts/seed_demo_data.py
```

This creates:
- 1 community: "Sunrise Collective"
- 10 demo agents (people)
- 5 locations
- 15 resource types
- 20 offers
- 10 needs
- 3 pending proposals

The script is idempotent - safe to run multiple times.
```

## Verification Checklist

- [ ] Script runs without errors
- [ ] Community "Sunrise Collective" created
- [ ] 10 agents created
- [ ] 20 offers created
- [ ] 10 needs created
- [ ] 3 proposals created
- [ ] Frontend shows populated data
- [ ] Running script twice doesn't create duplicates
- [ ] Proposals are actionable (can be approved)

## Estimated Total Time

- Task 1-2: 45 minutes (structure + community)
- Task 3-4: 45 minutes (agents + locations)
- Task 5: 30 minutes (resource specs)
- Task 6: 45 minutes (offers)
- Task 7: 30 minutes (needs)
- Task 8: 30 minutes (proposals)
- Task 9: 30 minutes (clear function)
- Task 10: 30 minutes (testing)
- Task 11: 15 minutes (docs)

**Total: ~4 hours**
