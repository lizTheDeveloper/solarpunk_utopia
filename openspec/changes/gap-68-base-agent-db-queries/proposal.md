# GAP-68: Base Agent Database Queries Return Empty

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Core Functionality Missing
**Source**: VISION_REALITY_DELTA.md Gap #68

## Problem Statement

The `query_vf_data()` method in `BaseAgent` always returns an empty list, even when a database client is configured. This means agents cannot access ValueFlows data, making all agent reasoning non-functional. Agents are supposed to analyze offers, needs, and economic activity, but they have no data access.

**Impact**:
- All agents are effectively blind to economic data
- Matchmaker agent cannot find matches
- Inventory agent cannot track inventory
- All agent features are facades that appear to work but do nothing
- Demo blocker - core agent intelligence completely non-functional

**Evidence**:
```python
# app/agents/framework/base_agent.py:193-201
async def query_vf_data(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
    """Query ValueFlows data from database"""
    if not self.db_client:
        logger.warning(f"No database client configured for {self.agent_name}")
        return []  # Always empty without client!

    try:
        # TODO: Implement actual DB query once DB client is available
        # For now, return empty list
        return []  # Always empty even WITH db_client!
    except Exception as e:
        logger.error(f"Error querying VF data: {e}")
        return []
```

## Requirements

### MUST

- Agents MUST be able to query ValueFlows entities (Intents, Commitments, Events, Agents)
- Queries MUST support filtering by common fields (agent_id, resource_type, status, dates)
- Queries MUST return actual data from the database
- Query results MUST be properly typed and validated
- Errors MUST be logged but not silently swallowed

### SHOULD

- Query interface SHOULD be simple and agent-friendly
- Common queries SHOULD have helper methods (get_active_offers, get_needs_by_agent, etc.)
- Queries SHOULD support pagination for large result sets
- Query results SHOULD include relationships (offer with agent details, etc.)

### MAY

- Query interface MAY support raw SQL for advanced cases
- Queries MAY be cached for performance
- Query builder MAY provide a fluent API

## Architecture

The `VFClient` already exists in the codebase - we just need to use it:

```python
# app/valueflows/client.py already has:
class VFClient:
    def __init__(self, db: Session):
        self.db = db

    async def get_intents(self, filters: dict) -> List[Intent]:
        # Already implemented!

    async def get_agents(self, filters: dict) -> List[Agent]:
        # Already implemented!

    # etc.
```

The problem is `BaseAgent.query_vf_data()` doesn't actually call `VFClient` methods.

## Proposed Solution

### 1. Update BaseAgent to Use VFClient

```python
# app/agents/framework/base_agent.py
from app.valueflows.client import VFClient
from typing import List, Dict, Optional, Literal

class BaseAgent:
    def __init__(self, agent_name: str, db: Session):
        self.agent_name = agent_name
        self.db = db
        self.vf_client = VFClient(db)  # Initialize VF client
        self.settings = {}

    async def query_vf_data(
        self,
        entity_type: Literal["intent", "commitment", "event", "agent", "resource"],
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Query ValueFlows data from database

        Args:
            entity_type: Type of VF entity to query
            filters: Optional filters (e.g., {"status": "active", "agent_id": "123"})

        Returns:
            List of matching entities as dicts
        """
        if not self.vf_client:
            logger.error(f"No VF client configured for {self.agent_name}")
            return []

        try:
            filters = filters or {}

            if entity_type == "intent":
                results = await self.vf_client.get_intents(filters)
            elif entity_type == "commitment":
                results = await self.vf_client.get_commitments(filters)
            elif entity_type == "event":
                results = await self.vf_client.get_events(filters)
            elif entity_type == "agent":
                results = await self.vf_client.get_agents(filters)
            elif entity_type == "resource":
                results = await self.vf_client.get_resources(filters)
            else:
                logger.error(f"Unknown entity type: {entity_type}")
                return []

            # Convert to dicts for agent processing
            return [r.dict() if hasattr(r, 'dict') else r for r in results]

        except Exception as e:
            logger.error(f"Error querying VF data for {self.agent_name}: {e}", exc_info=True)
            raise  # Don't silently swallow errors!

    # Add convenient helper methods
    async def get_active_offers(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get active offers"""
        filters = filters or {}
        filters["listing_type"] = "offer"
        filters["status"] = "active"
        return await self.query_vf_data("intent", filters)

    async def get_active_needs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get active needs"""
        filters = filters or {}
        filters["listing_type"] = "need"
        filters["status"] = "active"
        return await self.query_vf_data("intent", filters)

    async def get_offers_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all offers from a specific agent"""
        return await self.get_active_offers({"agent_id": agent_id})

    async def get_needs_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all needs from a specific agent"""
        return await self.get_active_needs({"agent_id": agent_id})

    async def get_commitments_for_agent(self, agent_id: str) -> List[Dict]:
        """Get commitments involving this agent (as provider or receiver)"""
        # This requires OR logic - may need special VFClient method
        all_commitments = await self.query_vf_data("commitment", {})
        return [
            c for c in all_commitments
            if c.get("provider") == agent_id or c.get("receiver") == agent_id
        ]
```

### 2. Update VFClient to Support Common Filters

```python
# app/valueflows/client.py
class VFClient:
    def __init__(self, db: Session):
        self.db = db

    async def get_intents(self, filters: dict = None) -> List[Intent]:
        """Get intents with optional filters"""
        query = self.db.query(Intent)

        if filters:
            # Apply common filters
            if "listing_type" in filters:
                query = query.filter(Intent.listing_type == filters["listing_type"])
            if "status" in filters:
                query = query.filter(Intent.status == filters["status"])
            if "agent_id" in filters:
                query = query.filter(Intent.agent_id == filters["agent_id"])
            if "resource_spec_id" in filters:
                query = query.filter(Intent.resource_spec_id == filters["resource_spec_id"])
            if "location_id" in filters:
                query = query.filter(Intent.location_id == filters["location_id"])

            # Date range filters
            if "created_after" in filters:
                query = query.filter(Intent.created_at >= filters["created_after"])
            if "created_before" in filters:
                query = query.filter(Intent.created_at <= filters["created_before"])

        return query.all()

    async def get_commitments(self, filters: dict = None) -> List[Commitment]:
        """Get commitments with optional filters"""
        query = self.db.query(Commitment)

        if filters:
            if "provider" in filters:
                query = query.filter(Commitment.provider == filters["provider"])
            if "receiver" in filters:
                query = query.filter(Commitment.receiver == filters["receiver"])
            if "finished" in filters:
                query = query.filter(Commitment.finished == filters["finished"])
            if "due_before" in filters:
                query = query.filter(Commitment.due <= filters["due_before"])

        return query.all()

    # Similar for get_events, get_agents, get_resources
```

### 3. Update Example Agent to Use New Methods

```python
# app/agents/matchmaker_agent.py
class MatchmakerAgent(BaseAgent):
    async def _execute_internal(self, context: dict) -> dict:
        """Find matches between offers and needs"""

        # NOW THIS WORKS! Gets real data
        offers = await self.get_active_offers()
        needs = await self.get_active_needs()

        logger.info(f"Matchmaker found {len(offers)} offers and {len(needs)} needs")

        matches = []
        for offer in offers:
            for need in needs:
                if self._is_match(offer, need):
                    match = {
                        "offer_id": offer["id"],
                        "need_id": need["id"],
                        "score": self._calculate_match_score(offer, need)
                    }
                    matches.append(match)

        return {
            "status": "success",
            "matches_found": len(matches),
            "matches": matches
        }

    def _is_match(self, offer: dict, need: dict) -> bool:
        """Check if offer can fulfill need"""

        # Check resource type
        if offer.get("resource_spec_id") != need.get("resource_spec_id"):
            return False

        # Check quantity
        if offer.get("quantity", 0) < need.get("quantity", 0):
            return False

        # Check location if needed
        if self.settings.get("require_location_match"):
            if offer.get("location_id") != need.get("location_id"):
                return False

        return True

    def _calculate_match_score(self, offer: dict, need: dict) -> float:
        """Calculate match quality (0-1)"""
        score = 0.7  # Base score

        # Bonus for same location
        if offer.get("location_id") == need.get("location_id"):
            score += 0.2

        # Bonus for local priority
        if self.settings.get("priority_local") and offer.get("visibility") == "local":
            score += 0.1

        return min(score, 1.0)
```

## Implementation Steps

1. Update `BaseAgent.__init__()` to initialize `VFClient`
2. Implement `query_vf_data()` to actually call VFClient methods
3. Add helper methods (`get_active_offers`, etc.) to BaseAgent
4. Update `VFClient` methods to support filtering
5. Update all agent implementations to use new query methods
6. Add comprehensive tests with real database data
7. Remove all TODO comments about DB queries
8. Add logging for query performance monitoring

## Test Scenarios

### WHEN an agent queries for active offers
THEN it MUST receive all offers with status="active" and listing_type="offer"
AND each offer MUST include all required fields
AND related entities (agent, resource_spec) SHOULD be included

### WHEN an agent queries with filters
THEN only matching records MUST be returned
AND invalid filters MUST raise clear errors
AND empty filters MUST return all records

### WHEN an agent queries but database connection fails
THEN an exception MUST be raised (not silently caught)
AND the error MUST be logged with full details
AND the agent execution MUST fail gracefully

### WHEN matchmaker agent executes
THEN it MUST find real matches between actual offers and needs
AND matches MUST be based on resource compatibility
AND match scores MUST be calculated correctly

### WHEN inventory agent checks stock levels
THEN it MUST query actual VF Events to track consumption
AND it MUST calculate remaining quantities correctly
AND it MUST identify items below reorder threshold

## Example Agent Implementations Using Queries

### Matchmaker Agent
```python
offers = await self.get_active_offers()
needs = await self.get_active_needs()
matches = find_matches(offers, needs)
```

### Inventory Agent
```python
resources = await self.query_vf_data("resource", {})
for resource in resources:
    events = await self.query_vf_data("event", {
        "resource_id": resource["id"],
        "action": "consume"
    })
    consumed = sum(e["quantity"] for e in events)
    if consumed > resource["quantity"] * 0.8:
        await self.create_reorder_proposal(resource)
```

### Work Party Scheduler
```python
commitments = await self.query_vf_data("commitment", {
    "action": "work",
    "finished": False,
    "due_before": next_week
})
schedule = optimize_work_parties(commitments)
```

## Files to Modify

- `app/agents/framework/base_agent.py` - Implement query methods
- `app/valueflows/client.py` - Add/improve filter support
- `app/agents/matchmaker_agent.py` - Use new query methods
- `app/agents/inventory_agent.py` - Use new query methods
- `app/agents/*.py` - Update all agents to use real queries
- `tests/test_base_agent_queries.py` - Comprehensive tests
- `tests/test_matchmaker_agent.py` - Test with real data

## Performance Considerations

1. **Add database indices** on commonly filtered fields:
   - `intents(status, listing_type, agent_id)`
   - `commitments(provider, receiver, finished)`
   - `events(resource_id, action)`

2. **Implement query result caching** for expensive queries

3. **Add pagination** for large result sets:
   ```python
   async def get_active_offers(self, limit=100, offset=0):
       filters = {"status": "active", "limit": limit, "offset": offset}
       return await self.query_vf_data("intent", filters)
   ```

## Related Gaps

- GAP-73: Inventory agent queries return empty (fixed by this)
- GAP-74: Commons router cache state (fixed by this)
- GAP-75: Work party scheduler availability (fixed by this)
- GAP-76: Education pathfinder skills (fixed by this)
- GAP-66: Agent stats (agents need to run successfully to generate stats)

## Migration Path

1. Implement changes in BaseAgent
2. Update one agent at a time (start with matchmaker)
3. Test each agent with real data
4. Verify agent execution logs show real results
5. Update all remaining agents
6. Remove all query-related TODO comments
