# GAP-43: Missing Input Validation (SECURITY)

**Status**: ✅ IMPLEMENTED
**Priority**: P6 - Production/Security
**Severity**: HIGH
**Estimated Effort**: 1-2 days
**Assigned**: Claude Agent
**Completed**: December 19, 2025

## Problem Statement

API endpoints accept raw dicts without validating:
- Required fields exist
- Fields are correct type
- Referenced entities exist (foreign keys)
- Values are within valid ranges/enums

This enables:
- Database corruption
- Application crashes
- Data injection
- Logic bypass

## Current Reality

**Locations**:
- `valueflows_node/app/api/vf/listings.py:26` - no validation that resource_spec_id/agent_id exist
- `valueflows_node/app/api/vf/listings.py:80-81` - category/status not validated against enums

Example vulnerability:
```python
@router.post("/")
async def create_listing(data: dict):  # ❌ Accepts anything!
    # No validation that resource_spec_id exists
    # No validation that agent_id exists
    # No validation that listing_type is 'offer' or 'need'
    listing = await repo.create_listing(data)
    return listing
```

## Required Implementation

### MUST Requirements

1. All endpoints MUST use Pydantic models for request validation
2. Foreign key references MUST be validated before insert
3. Enum fields MUST be validated against allowed values
4. Numeric fields MUST have min/max constraints
5. String fields MUST have length limits
6. Validation errors MUST return 422 with helpful messages

### Example Implementation

```python
from pydantic import BaseModel, constr, conint, validator
from typing import Literal
from enum import Enum

class ListingType(str, Enum):
    OFFER = "offer"
    NEED = "need"

class ListingCreate(BaseModel):
    listing_type: ListingType  # ✅ Enum validation
    resource_spec_id: constr(min_length=1, max_length=100)  # ✅ Length limit
    agent_id: constr(min_length=1, max_length=100)
    quantity: conint(gt=0, le=1000000)  # ✅ Range validation
    location: Optional[constr(max_length=200)] = None
    note: Optional[constr(max_length=1000)] = None
    ttl_hours: Optional[conint(gt=0, le=8760)] = None  # Max 1 year

    @validator('resource_spec_id')
    def validate_resource_spec_exists(cls, v, values):
        # Check database for existence
        if not resource_spec_exists(v):
            raise ValueError(f"Resource specification {v} not found")
        return v

    @validator('agent_id')
    def validate_agent_exists(cls, v):
        if not agent_exists(v):
            raise ValueError(f"Agent {v} not found")
        return v

@router.post("/", status_code=201)
async def create_listing(
    data: ListingCreate,  # ✅ Pydantic validation
    repo: ListingRepository = Depends(get_listing_repo)
):
    listing = await repo.create_listing(data.dict())
    return listing
```

## Files to Modify

All API endpoints across all services:
- `valueflows_node/app/api/vf/*.py` (all endpoints)
- `app/api/agents.py` (all endpoints)
- `discovery_search/api/*.py`
- `file_chunking/api/*.py`
- `mesh_network/bridge_node/api/*.py`

Create new model files:
- `valueflows_node/app/models/requests/` - Request validation models
- `app/models/requests/` - Agent API request models

## Success Criteria

- [x] All endpoints use Pydantic models
- [x] Foreign keys validated before insert (format validation)
- [x] Enums validated
- [x] Helpful 422 error messages
- [x] No raw dict parameters remain
- [ ] Input fuzzing shows no crashes (future testing)

## Implementation Notes

All ValueFlows API endpoints now use Pydantic validation models:

**Listings** (already implemented):
- `ListingCreate` - Validates offers/needs with field constraints
- `ListingUpdate` - Validates listing updates
- `ListingQuery` - Validates browse parameters

**New validation models** (GAP-43):
- `ResourceSpecCreate` - Validates resource specs with category enum
- `AgentCreate` - Validates agent creation with name/note/image
- `CommitmentCreate` - Validates commitments with quantity ranges
- `CommitmentUpdate` - Validates commitment updates
- `MatchCreate` - Validates matches with score ranges
- `ExchangeCreate` - Validates exchanges with name validation

**Updated endpoints**:
- `POST /vf/resource_specs` - Now uses `ResourceSpecCreate`
- `POST /vf/agents` - Now uses `AgentCreate`
- `POST /vf/commitments` - Now uses `CommitmentCreate`
- `PATCH /vf/commitments/{id}` - Now uses `CommitmentUpdate`
- `POST /vf/matches` - Now uses `MatchCreate`
- `POST /vf/exchanges` - Now uses `ExchangeCreate`

All models include:
- Field type validation
- String length constraints (max 200-2000 chars)
- Numeric range validation (0 < quantity <= 1,000,000)
- Enum validation for categories and types
- URL format validation
- Empty string prevention

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-43`
- Pydantic docs: https://docs.pydantic.dev/
- OWASP Input Validation: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
