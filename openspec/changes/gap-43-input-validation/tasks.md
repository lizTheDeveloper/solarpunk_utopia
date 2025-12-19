# Tasks: GAP-43 Input Validation (SECURITY)

## Phase 1: Create Validation Models (4-6 hours)

### Task 1.1: Create VF Listing validation models
**File**: `valueflows_node/app/models/requests/listings.py` (new file)
**Estimated**: 2 hours

```python
from pydantic import BaseModel, constr, conint, validator, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime

class ListingType(str, Enum):
    OFFER = "offer"
    NEED = "need"

class ListingCategory(str, Enum):
    FOOD = "food"
    SHELTER = "shelter"
    TRANSPORT = "transport"
    SKILLS = "skills"
    GOODS = "goods"
    # Add all valid categories

class ListingStatus(str, Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    COMPLETED = "completed"
    EXPIRED = "expired"

class ListingCreate(BaseModel):
    listing_type: ListingType
    resource_spec_id: constr(min_length=1, max_length=100)
    agent_id: constr(min_length=1, max_length=100)
    quantity: conint(gt=0, le=1000000)
    location: Optional[constr(max_length=200)] = None
    category: Optional[ListingCategory] = None
    status: Optional[ListingStatus] = Field(default=ListingStatus.ACTIVE)
    note: Optional[constr(max_length=1000)] = None
    ttl_hours: Optional[conint(gt=0, le=8760)] = None  # Max 1 year
    urgency: Optional[conint(ge=1, le=5)] = None

    @validator('resource_spec_id')
    def validate_resource_spec_exists(cls, v):
        # TODO: Check database for existence
        # For now, just validate format
        if not v or len(v.strip()) == 0:
            raise ValueError("Resource specification ID cannot be empty")
        return v

    @validator('agent_id')
    def validate_agent_exists(cls, v):
        # TODO: Check database for existence
        if not v or len(v.strip()) == 0:
            raise ValueError("Agent ID cannot be empty")
        return v

class ListingUpdate(BaseModel):
    quantity: Optional[conint(gt=0, le=1000000)] = None
    location: Optional[constr(max_length=200)] = None
    category: Optional[ListingCategory] = None
    status: Optional[ListingStatus] = None
    note: Optional[constr(max_length=1000)] = None
    ttl_hours: Optional[conint(gt=0, le=8760)] = None
    urgency: Optional[conint(ge=1, le=5)] = None
```

**Acceptance criteria**:
- All fields have type validation
- String fields have length limits
- Numeric fields have range constraints
- Enums validated against allowed values
- Validators check non-empty strings
- Helpful error messages on validation failure

### Task 1.2: Create Agent API validation models
**File**: `app/models/requests/agents.py` (new file)
**Estimated**: 1 hour

```python
from pydantic import BaseModel, constr, validator
from typing import Dict, Any, Optional, List
from enum import Enum

class AgentType(str, Enum):
    MUTUAL_AID_MATCHMAKER = "mutual-aid-matchmaker"
    COMMONS_ROUTER = "commons-router"
    WORK_PARTY_SCHEDULER = "work-party-scheduler"
    EDUCATION_PATHFINDER = "education-pathfinder"
    PERMACULTURE_PLANNER = "permaculture-planner"
    PROPOSAL_EXECUTOR = "proposal-executor"

class AgentInvokeRequest(BaseModel):
    agent_type: AgentType
    context: Dict[str, Any]
    user_id: Optional[constr(min_length=1, max_length=100)] = None

    @validator('context')
    def validate_context_size(cls, v):
        # Prevent DOS via huge context objects
        import json
        size = len(json.dumps(v))
        if size > 100000:  # 100KB max
            raise ValueError("Context object too large")
        return v

class ProposalApproval(BaseModel):
    approved: bool
    user_id: constr(min_length=1, max_length=100)
    comment: Optional[constr(max_length=500)] = None
```

**Acceptance criteria**:
- Agent types validated against enum
- Context size limited
- User IDs validated
- Comments have length limits

### Task 1.3: Create Discovery/Search validation models
**File**: `discovery_search/models/requests.py` (new file)
**Estimated**: 1 hour

```python
from pydantic import BaseModel, constr, conint, validator
from typing import Optional, List

class SearchQuery(BaseModel):
    query: constr(min_length=1, max_length=200)
    limit: Optional[conint(ge=1, le=100)] = 20
    offset: Optional[conint(ge=0)] = 0

    @validator('query')
    def validate_query_format(cls, v):
        # Prevent injection attacks
        forbidden = ['<script', 'javascript:', 'onerror=']
        if any(f in v.lower() for f in forbidden):
            raise ValueError("Invalid characters in query")
        return v

class ServiceAnnouncement(BaseModel):
    service_name: constr(min_length=1, max_length=100)
    endpoint: constr(min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = None

    @validator('endpoint')
    def validate_endpoint_format(cls, v):
        # Basic URL validation
        if not v.startswith(('http://', 'https://', 'ws://', 'wss://')):
            raise ValueError("Invalid endpoint URL")
        return v
```

**Acceptance criteria**:
- Query strings sanitized
- Pagination limits enforced
- URLs validated
- XSS prevention in queries

### Task 1.4: Create File Chunking validation models
**File**: `file_chunking/models/requests.py` (new file)
**Estimated**: 1 hour

```python
from pydantic import BaseModel, constr, conint, validator
from typing import Optional

class ChunkRequest(BaseModel):
    file_id: constr(min_length=1, max_length=100)
    chunk_size: Optional[conint(ge=512, le=1048576)] = 65536  # 512B to 1MB
    offset: Optional[conint(ge=0)] = 0

    @validator('file_id')
    def validate_file_id_format(cls, v):
        # Prevent path traversal
        if '../' in v or '..\\' in v:
            raise ValueError("Invalid file ID format")
        return v

class FileMetadata(BaseModel):
    filename: constr(min_length=1, max_length=255)
    size: conint(ge=0, le=10737418240)  # Max 10GB
    mime_type: Optional[constr(max_length=100)] = None

    @validator('filename')
    def validate_filename(cls, v):
        # Prevent path traversal
        if '../' in v or '..\\' in v or v.startswith('/'):
            raise ValueError("Invalid filename")
        return v
```

**Acceptance criteria**:
- File IDs validated against path traversal
- Chunk sizes within reasonable bounds
- Filenames sanitized
- File sizes limited

## Phase 2: Update API Endpoints (6-8 hours)

### Task 2.1: Update VF listings endpoints
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 2 hours

Replace all `data: dict` parameters with Pydantic models:

```python
from valueflows_node.app.models.requests.listings import (
    ListingCreate, ListingUpdate
)

@router.post("/", status_code=201)
async def create_listing(
    data: ListingCreate,  # ✅ Changed from dict
    repo: ListingRepository = Depends(get_listing_repo)
):
    listing = await repo.create_listing(data.dict())
    return listing

@router.patch("/{listing_id}")
async def update_listing(
    listing_id: str,
    data: ListingUpdate,  # ✅ Changed from dict
    repo: ListingRepository = Depends(get_listing_repo)
):
    listing = await repo.update_listing(listing_id, data.dict(exclude_unset=True))
    return listing
```

**Acceptance criteria**:
- All endpoints use Pydantic models
- No raw dict parameters remain
- Validation errors return 422 with details
- Existing tests updated

### Task 2.2: Update Agent API endpoints
**File**: `app/api/agents.py`
**Estimated**: 2 hours

```python
from app.models.requests.agents import AgentInvokeRequest, ProposalApproval

@router.post("/invoke")
async def invoke_agent(
    request: AgentInvokeRequest,  # ✅ Changed from dict
    agent_factory: AgentFactory = Depends(get_agent_factory)
):
    agent = agent_factory.create(request.agent_type)
    result = await agent.run(request.context)
    return result

@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    approval: ProposalApproval,  # ✅ Changed from dict
    tracker: ApprovalTracker = Depends(get_approval_tracker)
):
    result = await tracker.approve_proposal(proposal_id, approval.dict())
    return result
```

**Acceptance criteria**:
- All endpoints validated
- Agent types checked
- Context size limited
- Error messages helpful

### Task 2.3: Update Discovery/Search endpoints
**File**: `discovery_search/api/routes.py`
**Estimated**: 1.5 hours

```python
from discovery_search.models.requests import SearchQuery, ServiceAnnouncement

@router.get("/search")
async def search(
    query: SearchQuery = Depends(),  # ✅ Query params validated
    repo = Depends(get_search_repo)
):
    results = await repo.search(query.query, query.limit, query.offset)
    return results

@router.post("/announce")
async def announce_service(
    announcement: ServiceAnnouncement,  # ✅ Validated
    registry = Depends(get_registry)
):
    await registry.register(announcement.dict())
    return {"status": "registered"}
```

**Acceptance criteria**:
- Query params validated
- Service announcements validated
- URLs checked
- XSS prevented

### Task 2.4: Update File Chunking endpoints
**File**: `file_chunking/api/routes.py`
**Estimated**: 1.5 hours

```python
from file_chunking.models.requests import ChunkRequest, FileMetadata

@router.get("/chunks/{file_id}")
async def get_chunk(
    request: ChunkRequest = Depends(),
    storage = Depends(get_storage)
):
    chunk = await storage.get_chunk(
        request.file_id,
        request.chunk_size,
        request.offset
    )
    return chunk

@router.post("/files")
async def upload_file(
    metadata: FileMetadata,
    storage = Depends(get_storage)
):
    file_id = await storage.store_metadata(metadata.dict())
    return {"file_id": file_id}
```

**Acceptance criteria**:
- File IDs validated
- Path traversal prevented
- Chunk sizes limited
- Filenames sanitized

### Task 2.5: Update Mesh Network Bridge endpoints
**File**: `mesh_network/bridge_node/api/routes.py`
**Estimated**: 1 hour

Similar validation for mesh network endpoints:
- Bundle submissions
- Node announcements
- Routing tables

## Phase 3: Add Database Validators (3-4 hours)

### Task 3.1: Create validation helper functions
**File**: `valueflows_node/app/validators.py` (new file)
**Estimated**: 2 hours

```python
from valueflows_node.app.database import get_db

async def resource_spec_exists(resource_spec_id: str) -> bool:
    """Check if resource specification exists in database"""
    db = await get_db()
    result = await db.execute(
        "SELECT id FROM resource_specifications WHERE id = ?",
        (resource_spec_id,)
    )
    return result.fetchone() is not None

async def agent_exists(agent_id: str) -> bool:
    """Check if agent exists in database"""
    db = await get_db()
    result = await db.execute(
        "SELECT id FROM agents WHERE id = ?",
        (agent_id,)
    )
    return result.fetchone() is not None

async def listing_exists(listing_id: str) -> bool:
    """Check if listing exists"""
    db = await get_db()
    result = await db.execute(
        "SELECT id FROM listings WHERE id = ?",
        (listing_id,)
    )
    return result.fetchone() is not None
```

**Acceptance criteria**:
- Efficient database queries
- Async-compatible
- Cached for performance
- Clear error messages

### Task 3.2: Wire validators into Pydantic models
**File**: `valueflows_node/app/models/requests/listings.py`
**Estimated**: 1-2 hours

```python
from valueflows_node.app.validators import (
    resource_spec_exists,
    agent_exists
)

class ListingCreate(BaseModel):
    # ... existing fields ...

    @validator('resource_spec_id')
    async def validate_resource_spec_exists(cls, v):
        if not await resource_spec_exists(v):
            raise ValueError(f"Resource specification {v} not found")
        return v

    @validator('agent_id')
    async def validate_agent_exists(cls, v):
        if not await agent_exists(v):
            raise ValueError(f"Agent {v} not found")
        return v

    class Config:
        # Enable async validators
        validate_assignment = True
```

**Note**: Pydantic v2 handles async validators differently. May need to use dependency injection instead.

**Acceptance criteria**:
- Foreign keys validated
- Database checked before insert
- Efficient queries
- Clear error messages

## Phase 4: Testing (4-6 hours)

### Task 4.1: Unit tests for validation models
**File**: `tests/unit/test_validation_models.py` (new)
**Estimated**: 2 hours

```python
import pytest
from pydantic import ValidationError
from valueflows_node.app.models.requests.listings import (
    ListingCreate, ListingType, ListingCategory
)

def test_listing_create_valid():
    """Valid listing creation"""
    data = {
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5
    }
    listing = ListingCreate(**data)
    assert listing.listing_type == ListingType.OFFER
    assert listing.quantity == 5

def test_listing_create_invalid_type():
    """Invalid listing type rejected"""
    data = {
        "listing_type": "invalid",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5
    }
    with pytest.raises(ValidationError) as exc:
        ListingCreate(**data)
    assert "listing_type" in str(exc.value)

def test_listing_create_invalid_quantity():
    """Negative quantity rejected"""
    data = {
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": -5
    }
    with pytest.raises(ValidationError):
        ListingCreate(**data)

def test_listing_create_too_large_quantity():
    """Excessive quantity rejected"""
    data = {
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 10000001  # > 1 million
    }
    with pytest.raises(ValidationError):
        ListingCreate(**data)

def test_listing_note_too_long():
    """Note length limit enforced"""
    data = {
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5,
        "note": "x" * 1001  # > 1000 chars
    }
    with pytest.raises(ValidationError):
        ListingCreate(**data)
```

**Acceptance criteria**:
- All validation rules tested
- Boundary conditions tested
- Error messages verified
- 100% coverage on models

### Task 4.2: Integration tests for API endpoints
**File**: `tests/integration/test_validated_endpoints.py` (new)
**Estimated**: 2 hours

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_listing_with_invalid_data(client: AsyncClient):
    """API rejects invalid listing data"""
    response = await client.post("/vf/listings/", json={
        "listing_type": "invalid_type",
        "quantity": -5
    })
    assert response.status_code == 422
    data = response.json()
    assert "listing_type" in str(data)
    assert "quantity" in str(data)

@pytest.mark.asyncio
async def test_create_listing_with_valid_data(client: AsyncClient):
    """API accepts valid listing data"""
    response = await client.post("/vf/listings/", json={
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5,
        "location": "Community Center"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 5

@pytest.mark.asyncio
async def test_agent_invoke_with_huge_context(client: AsyncClient):
    """API rejects oversized context objects"""
    huge_context = {"data": "x" * 200000}  # > 100KB
    response = await client.post("/agents/invoke", json={
        "agent_type": "mutual-aid-matchmaker",
        "context": huge_context
    })
    assert response.status_code == 422
```

**Acceptance criteria**:
- All endpoints tested
- Valid data accepted
- Invalid data rejected with 422
- Error messages helpful
- Performance not degraded

### Task 4.3: Security fuzzing tests
**File**: `tests/security/test_input_fuzzing.py` (new)
**Estimated**: 2 hours

```python
import pytest
from httpx import AsyncClient

# SQL injection attempts
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE listings; --",
    "' OR '1'='1",
    "1' UNION SELECT * FROM users--",
]

# XSS attempts
XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "javascript:alert('xss')",
    "<img src=x onerror=alert('xss')>",
]

# Path traversal attempts
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32",
    "....//....//....//etc/passwd",
]

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
async def test_sql_injection_blocked(client: AsyncClient, payload):
    """SQL injection attempts are blocked"""
    response = await client.post("/vf/listings/", json={
        "listing_type": "offer",
        "resource_spec_id": payload,
        "agent_id": "user-456",
        "quantity": 5
    })
    # Should either reject (422) or safely handle
    assert response.status_code in [422, 404]

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", XSS_PAYLOADS)
async def test_xss_blocked(client: AsyncClient, payload):
    """XSS attempts are sanitized or blocked"""
    response = await client.post("/vf/listings/", json={
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5,
        "note": payload
    })
    if response.status_code == 201:
        # If accepted, verify it's escaped in response
        data = response.json()
        assert "<script>" not in data.get("note", "")

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
async def test_path_traversal_blocked(client: AsyncClient, payload):
    """Path traversal attempts are blocked"""
    response = await client.get(f"/files/chunks/{payload}")
    # Should reject invalid file IDs
    assert response.status_code in [400, 422, 404]
```

**Acceptance criteria**:
- SQL injection blocked
- XSS sanitized/blocked
- Path traversal blocked
- No crashes on malicious input
- Helpful error messages

## Phase 5: Documentation (1-2 hours)

### Task 5.1: Update API documentation
**File**: `docs/API.md` or OpenAPI specs
**Estimated**: 1 hour

Document for each endpoint:
- Request schema with all fields
- Field constraints (min/max, allowed values)
- Validation error responses (422)
- Example requests (valid and invalid)

### Task 5.2: Add validation error handling guide
**File**: `docs/ERROR_HANDLING.md` (new)
**Estimated**: 30 minutes

Document:
- How to interpret 422 validation errors
- Common validation failures and fixes
- Client-side pre-validation recommendations

### Task 5.3: Security audit report
**File**: `docs/SECURITY_AUDIT.md`
**Estimated**: 30 minutes

Document:
- What was validated
- What attack vectors were tested
- Remaining risks
- Recommendations for monitoring

## Verification Checklist

Before marking this as complete:

- [ ] All API endpoints use Pydantic models
- [ ] No raw dict parameters remain in any endpoint
- [ ] All validation tests pass
- [ ] Security fuzzing tests pass
- [ ] Foreign key validation implemented
- [ ] Enum validation works correctly
- [ ] String length limits enforced
- [ ] Numeric range limits enforced
- [ ] Helpful 422 error messages returned
- [ ] Error messages don't leak sensitive info
- [ ] Performance benchmarks show < 5% overhead
- [ ] Documentation updated
- [ ] Code review completed

## Estimated Total Time

- Phase 1: 5 hours (model creation)
- Phase 2: 8 hours (endpoint updates)
- Phase 3: 4 hours (database validators)
- Phase 4: 6 hours (testing)
- Phase 5: 2 hours (documentation)

**Total: 1-2 days (25 hours)**

## Dependencies

- Pydantic v2 installed
- Database access for foreign key validation
- Test database setup
- Security testing tools (optional: OWASP ZAP, Burp Suite)

## Performance Considerations

- Validation adds ~1-5ms per request
- Database validators may add latency - consider caching
- Large context objects may need streaming validation
- Monitor P95/P99 latency after deployment

## Rollout Strategy

1. **Phase 1**: Deploy validation to staging environment
2. **Phase 2**: Monitor logs for validation errors (1 week)
3. **Phase 3**: Fix client code generating invalid requests
4. **Phase 4**: Deploy to production
5. **Phase 5**: Monitor error rates and performance
