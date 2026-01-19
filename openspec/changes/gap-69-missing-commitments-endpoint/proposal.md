# GAP-69: Missing Commitments Endpoint

**Status**: Draft
**Priority**: Critical
**Type**: Bug - Missing Backend Implementation
**Source**: VISION_REALITY_DELTA.md Gap #69

## Problem Statement

The frontend expects to fetch and manage ValueFlows commitments via `/api/vf/commitments`, but no backend endpoint exists. This breaks the commitment tracking feature essential for coordinating exchanges.

**Impact**:
- Cannot track commitments between community members
- Cannot manage multi-party agreements
- Frontend makes requests to non-existent endpoint (404 errors)
- Demo blocker - core ValueFlows coordination feature missing

**Evidence**:
```typescript
// Frontend: frontend/src/api/valueflows.ts:148-156
getCommitments: async (): Promise<Commitment[]> => {
  const response = await api.get<Commitment[]>('/commitments');
  return response.data;
},

createCommitment: async (data: CreateCommitmentInput): Promise<Commitment> => {
  const response = await api.post<Commitment>('/commitments', data);
  return response.data;
}
```

No corresponding backend file exists at `valueflows_node/app/api/vf/commitments.py`

## Requirements

### MUST (ValueFlows Spec Compliant)

- Commitments MUST link to Economic Agents (provider and receiver)
- Commitments MUST specify resource quantities and units
- Commitments MUST have lifecycle states (proposed, accepted, fulfilled, cancelled)
- Commitments MUST support due dates and time windows
- Commitments MUST be queryable by agent, resource, and status

### SHOULD

- Commitments SHOULD support partial fulfillment
- Commitments SHOULD link to related Intents (offers/needs)
- Commitments SHOULD support notes and metadata
- Commitment creation SHOULD verify agent permissions
- Commitment fulfillment SHOULD create EconomicEvents

### MAY

- Commitments MAY support recurring patterns
- Commitments MAY have dependencies on other commitments
- Commitments MAY include location and transport details

## ValueFlows Commitment Model

Based on [ValueFlows spec v1.0](https://valueflo.ws/introduction/commitment.html):

```python
# app/models/commitment.py
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

class Commitment(Base):
    __tablename__ = "vf_commitments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Core VF fields
    action: str  # VF action (transfer, produce, consume, etc.)
    provider: str  # Agent ID providing the resource
    receiver: str  # Agent ID receiving the resource

    # Resource specification
    resource_classified_as: Optional[str] = None  # Resource category
    resource_conforms_to: Optional[str] = None  # Resource spec ID
    resource_quantity_has_numerical_value: float  # Amount
    resource_quantity_has_unit: str  # Unit (kg, hours, etc.)

    # Timing
    has_beginning: Optional[datetime] = None
    has_end: Optional[datetime] = None
    has_point_in_time: Optional[datetime] = None
    due: Optional[datetime] = None

    # State
    finished: bool = False
    fulfilled_by: Optional[str] = None  # Fulfillment tracking

    # Relationships
    input_of: Optional[str] = None  # Process ID
    output_of: Optional[str] = None  # Process ID
    in_scope_of: Optional[str] = None  # Agent scope

    # Metadata
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relations
    provider_agent = relationship("Agent", foreign_keys=[provider])
    receiver_agent = relationship("Agent", foreign_keys=[receiver])
```

## Proposed Implementation

### 1. Create Commitments API

```python
# valueflows_node/app/api/vf/commitments.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.commitment import Commitment, CreateCommitmentInput
from app.repositories.commitment_repo import CommitmentRepository
from app.auth import require_auth, User

router = APIRouter(prefix="/commitments", tags=["commitments"])

@router.get("/", response_model=List[Commitment])
async def get_commitments(
    provider: Optional[str] = Query(None),
    receiver: Optional[str] = Query(None),
    finished: Optional[bool] = Query(None),
    current_user: User = Depends(require_auth),
    repo: CommitmentRepository = Depends()
):
    """Get commitments with optional filters"""

    filters = {}
    if provider:
        filters["provider"] = provider
    if receiver:
        filters["receiver"] = receiver
    if finished is not None:
        filters["finished"] = finished

    commitments = await repo.find_all(filters)
    return commitments

@router.get("/{commitment_id}", response_model=Commitment)
async def get_commitment(
    commitment_id: str,
    current_user: User = Depends(require_auth),
    repo: CommitmentRepository = Depends()
):
    """Get a specific commitment"""
    commitment = await repo.find_by_id(commitment_id)
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    return commitment

@router.post("/", response_model=Commitment, status_code=201)
async def create_commitment(
    data: CreateCommitmentInput,
    current_user: User = Depends(require_auth),
    repo: CommitmentRepository = Depends()
):
    """Create a new commitment"""

    # Verify user has permission to commit as provider
    if data.provider != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Can only create commitments as yourself"
        )

    commitment = Commitment(
        **data.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    created = await repo.create(commitment)
    return created

@router.patch("/{commitment_id}", response_model=Commitment)
async def update_commitment(
    commitment_id: str,
    updates: dict,
    current_user: User = Depends(require_auth),
    repo: CommitmentRepository = Depends()
):
    """Update a commitment"""

    commitment = await repo.find_by_id(commitment_id)
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    # Verify user is provider or receiver
    if current_user.id not in [commitment.provider, commitment.receiver]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this commitment"
        )

    updated = await repo.update(commitment_id, updates)
    return updated

@router.delete("/{commitment_id}", status_code=204)
async def delete_commitment(
    commitment_id: str,
    current_user: User = Depends(require_auth),
    repo: CommitmentRepository = Depends()
):
    """Delete/cancel a commitment"""

    commitment = await repo.find_by_id(commitment_id)
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")

    # Only provider can cancel
    if current_user.id != commitment.provider:
        raise HTTPException(
            status_code=403,
            detail="Only provider can cancel commitment"
        )

    await repo.delete(commitment_id)
```

### 2. Create Repository

```python
# app/repositories/commitment_repo.py
class CommitmentRepository:
    def __init__(self, db: Session):
        self.db = db

    async def find_all(self, filters: dict) -> List[Commitment]:
        query = self.db.query(Commitment)
        for key, value in filters.items():
            query = query.filter(getattr(Commitment, key) == value)
        return query.all()

    async def find_by_id(self, commitment_id: str) -> Optional[Commitment]:
        return self.db.query(Commitment).filter(Commitment.id == commitment_id).first()

    async def create(self, commitment: Commitment) -> Commitment:
        self.db.add(commitment)
        self.db.commit()
        self.db.refresh(commitment)
        return commitment

    async def update(self, commitment_id: str, updates: dict) -> Commitment:
        commitment = await self.find_by_id(commitment_id)
        for key, value in updates.items():
            setattr(commitment, key, value)
        commitment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(commitment)
        return commitment

    async def delete(self, commitment_id: str):
        commitment = await self.find_by_id(commitment_id)
        self.db.delete(commitment)
        self.db.commit()
```

## Implementation Steps

1. Create `Commitment` model following ValueFlows spec
2. Create database migration for `vf_commitments` table
3. Create `CommitmentRepository` for database operations
4. Create `commitments.py` API router
5. Register router in main FastAPI app
6. Add comprehensive tests (CRUD, permissions, filtering)
7. Update frontend types if needed

## Test Scenarios

### WHEN a user creates a commitment as provider
THEN the commitment MUST be created successfully
AND the provider MUST be set to the current user
AND the receiver MUST be validated as an existing agent

### WHEN a user tries to create a commitment as someone else
THEN the request MUST return 403 Forbidden
AND no commitment MUST be created

### WHEN a user queries commitments they're involved in
THEN they MUST see commitments where they are provider OR receiver
AND they MUST NOT see commitments they're not involved in (privacy)

### WHEN a commitment is fulfilled
THEN an EconomicEvent SHOULD be created linking to the commitment
AND the commitment.fulfilled_by SHOULD reference the event
AND the commitment.finished SHOULD be set to True

### WHEN a provider cancels a commitment
THEN the commitment MUST be deleted
AND both provider and receiver SHOULD be notified

## Database Schema

```sql
CREATE TABLE vf_commitments (
    id VARCHAR(36) PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    provider VARCHAR(36) NOT NULL,
    receiver VARCHAR(36) NOT NULL,
    resource_classified_as VARCHAR(255),
    resource_conforms_to VARCHAR(36),
    resource_quantity_has_numerical_value DECIMAL(10,2) NOT NULL,
    resource_quantity_has_unit VARCHAR(50) NOT NULL,
    has_beginning TIMESTAMP,
    has_end TIMESTAMP,
    has_point_in_time TIMESTAMP,
    due TIMESTAMP,
    finished BOOLEAN DEFAULT FALSE,
    fulfilled_by VARCHAR(36),
    input_of VARCHAR(36),
    output_of VARCHAR(36),
    in_scope_of VARCHAR(36),
    note TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (provider) REFERENCES agents(id),
    FOREIGN KEY (receiver) REFERENCES agents(id),
    INDEX idx_provider (provider),
    INDEX idx_receiver (receiver),
    INDEX idx_finished (finished)
);
```

## Files to Create/Modify

- `valueflows_node/app/models/commitment.py` - New model
- `valueflows_node/app/api/vf/commitments.py` - New API router
- `valueflows_node/app/repositories/commitment_repo.py` - New repository
- `valueflows_node/app/database/migrations/` - Add migration
- `valueflows_node/app/main.py` - Register commitments router
- `valueflows_node/tests/test_commitments.py` - Comprehensive tests
- `frontend/src/types/valueflows.ts` - Verify Commitment type matches

## ValueFlows Spec Compliance

This implementation follows:
- [ValueFlows Commitment spec](https://valueflo.ws/introduction/commitment.html)
- REA (Resources, Events, Agents) pattern
- VF Actions vocabulary
- Proper economic event linkage

## Related Gaps

- GAP-75: Work Party Scheduler needs commitment queries (will use this endpoint)
- GAP-76: Education Pathfinder needs commitment queries (will use this endpoint)
- VF Events implementation (needed for fulfillment tracking)
