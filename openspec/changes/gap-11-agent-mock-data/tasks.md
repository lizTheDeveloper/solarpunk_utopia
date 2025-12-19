# Tasks: GAP-11 Replace Agent Mock Data

## Phase 1: VFClient Commitments (2 hours)

### Task 1.1: Add get_commitments method
**File**: `app/clients/vf_client.py`
**Estimated**: 1 hour

```python
async def get_commitments(
    self,
    agent_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict]:
    """Query VF commitments for availability checking"""
    params = {}
    if agent_id:
        params['agent_id'] = agent_id
    if start_date:
        params['start_date'] = start_date.isoformat()
    # ...
    response = await self.client.get('/vf/commitments', params=params)
    return response.json()
```

### Task 1.2: Update Work Party Scheduler
**File**: `app/agents/work_party_scheduler.py`
**Estimated**: 1 hour

Replace `_get_available_participants()` mock with:
```python
async def _get_available_participants(
    self,
    date: datetime,
    participant_ids: List[str]
) -> List[Dict]:
    """Check actual availability via VF commitments"""
    available = []
    for participant_id in participant_ids:
        commitments = await self.vf_client.get_commitments(
            agent_id=participant_id,
            start_date=date,
            end_date=date + timedelta(days=1)
        )
        # If no conflicting commitments, they're available
        if not commitments:
            available.append({"id": participant_id, "available": True})
    return available
```

## Phase 2: Permaculture Planner (2-4 hours)

### Task 2.1: Add get_goals to VFClient
**File**: `app/clients/vf_client.py`
**Estimated**: 30 minutes

```python
async def get_goals(self, agent_id: Optional[str] = None) -> List[Dict]:
    params = {"agent_id": agent_id} if agent_id else {}
    response = await self.client.get('/vf/goals', params=params)
    return response.json()
```

### Task 2.2: Update Permaculture Planner goals
**File**: `app/agents/permaculture_planner.py`
**Estimated**: 1 hour

Replace mock with VF query.

### Task 2.3: Integrate LLM for guild suggestions
**File**: `app/agents/permaculture_planner.py`
**Estimated**: 2 hours

```python
async def _suggest_guilds(self, crop: str, context: Dict) -> List[str]:
    """Use LLM to suggest companion planting"""
    llm = get_llm_backend()
    prompt = f"Suggest 3 companion plants for {crop} in permaculture guild"
    suggestions = await llm.generate(prompt)
    return suggestions
```

**Total: 4-6 hours**
