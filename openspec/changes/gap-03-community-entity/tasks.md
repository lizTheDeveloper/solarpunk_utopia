# Tasks: GAP-03 Community/Commune Entity

## Phase 1: Database Schema (2 hours)

### Task 1.1: Create communities and memberships tables
**File**: `app/database/migrations/002_add_communities.sql` (new)
**Estimated**: 1 hour

```sql
CREATE TABLE communities (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSON DEFAULT '{}',
    is_public BOOLEAN DEFAULT TRUE
);

CREATE TABLE community_memberships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    community_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    UNIQUE(user_id, community_id)
);

CREATE INDEX idx_memberships_user ON community_memberships(user_id);
CREATE INDEX idx_memberships_community ON community_memberships(community_id);
```

### Task 1.2: Add community_id to existing tables
**File**: Same migration file
**Estimated**: 1 hour

```sql
-- Add community_id to listings
ALTER TABLE listings ADD COLUMN community_id TEXT REFERENCES communities(id);
CREATE INDEX idx_listings_community ON listings(community_id);

-- Add community_id to proposals
ALTER TABLE proposals ADD COLUMN community_id TEXT REFERENCES communities(id);
CREATE INDEX idx_proposals_community ON proposals(community_id);

-- Add community_id to vf_matches (if table exists)
ALTER TABLE vf_matches ADD COLUMN community_id TEXT REFERENCES communities(id);
CREATE INDEX idx_matches_community ON vf_matches(community_id);

-- Add community_id to vf_exchanges (if table exists)
ALTER TABLE vf_exchanges ADD COLUMN community_id TEXT REFERENCES communities(id);
CREATE INDEX idx_exchanges_community ON vf_exchanges(community_id);

-- Create default community and migrate existing data
INSERT INTO communities (id, name, description, is_public)
VALUES ('default', 'Default Commune', 'Default community for existing data', TRUE);

-- Assign existing data to default community
UPDATE listings SET community_id = 'default' WHERE community_id IS NULL;
UPDATE proposals SET community_id = 'default' WHERE community_id IS NULL;

-- Assign existing users to default community
INSERT INTO community_memberships (id, user_id, community_id, role)
SELECT
    'mem_' || user_id || '_default' as id,
    user_id,
    'default' as community_id,
    'member' as role
FROM users;
```

## Phase 2: Models and Repositories (3 hours)

### Task 2.1: Create Community models
**File**: `valueflows_node/app/models/community.py` (new)
**Estimated**: 45 minutes

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class Community(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    settings: Dict = {}
    is_public: bool = True

class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True

class CommunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict] = None
    is_public: Optional[bool] = None

class CommunityMembership(BaseModel):
    id: str
    user_id: str
    community_id: str
    role: str = "member"
    joined_at: datetime

class MembershipCreate(BaseModel):
    user_id: str
    community_id: str
    role: str = "member"
```

### Task 2.2: Create CommunityRepository
**File**: `valueflows_node/app/repositories/community_repo.py` (new)
**Estimated**: 1.5 hours

Methods:
- `create_community(data: CommunityCreate, creator_id: str) -> Community`
- `get_community_by_id(community_id: str) -> Optional[Community]`
- `get_community_by_name(name: str) -> Optional[Community]`
- `list_communities(user_id: Optional[str] = None) -> List[Community]`
- `update_community(community_id: str, data: CommunityUpdate) -> Community`
- `delete_community(community_id: str) -> bool`
- `add_member(data: MembershipCreate) -> CommunityMembership`
- `remove_member(user_id: str, community_id: str) -> bool`
- `get_members(community_id: str) -> List[CommunityMembership]`
- `get_user_communities(user_id: str) -> List[Community]`
- `is_member(user_id: str, community_id: str) -> bool`
- `get_member_count(community_id: str) -> int`

### Task 2.3: Add community_id to existing models
**File**: Multiple model files
**Estimated**: 45 minutes

Update these models to include `community_id`:
- `valueflows_node/app/models/vf/listing.py`
- `valueflows_node/app/models/vf/match.py`
- `valueflows_node/app/models/vf/exchange.py`
- `app/models/proposal.py`

Make `community_id` required in Create schemas, optional in main schemas (for backward compatibility).

## Phase 3: API Endpoints (3 hours)

### Task 3.1: Create communities API
**File**: `valueflows_node/app/api/communities.py` (new)
**Estimated**: 2 hours

```python
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter(prefix="/communities", tags=["communities"])

@router.post("/")
async def create_community(
    data: CommunityCreate,
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """Create a new community"""
    user = request.state.user
    community = await repo.create_community(data, creator_id=user.id)
    return community

@router.get("/")
async def list_communities(
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """List communities user is a member of"""
    user = request.state.user
    communities = await repo.get_user_communities(user.id)
    return communities

@router.get("/{community_id}")
async def get_community(
    community_id: str,
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """Get community details"""
    user = request.state.user
    if not await repo.is_member(user.id, community_id):
        raise HTTPException(403, "Not a member of this community")
    community = await repo.get_community_by_id(community_id)
    if not community:
        raise HTTPException(404, "Community not found")
    return community

@router.patch("/{community_id}")
async def update_community(
    community_id: str,
    data: CommunityUpdate,
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """Update community settings (admin only)"""
    # TODO: Check if user is admin
    community = await repo.update_community(community_id, data)
    return community

@router.post("/{community_id}/members")
async def add_member(
    community_id: str,
    data: dict,  # {user_id, role}
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """Add member to community (admin only)"""
    # TODO: Check if requester is admin
    membership = await repo.add_member(
        MembershipCreate(
            user_id=data["user_id"],
            community_id=community_id,
            role=data.get("role", "member")
        )
    )
    return membership

@router.get("/{community_id}/members")
async def list_members(
    community_id: str,
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """List community members"""
    user = request.state.user
    if not await repo.is_member(user.id, community_id):
        raise HTTPException(403, "Not a member of this community")
    members = await repo.get_members(community_id)
    return members

@router.get("/{community_id}/stats")
async def get_stats(
    community_id: str,
    request: Request,
    repo: CommunityRepository = Depends(get_community_repo)
):
    """Get community statistics"""
    member_count = await repo.get_member_count(community_id)
    # TODO: Add more stats (offer count, exchange count, etc.)
    return {"member_count": member_count}
```

### Task 3.2: Add community filtering to existing endpoints
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 1 hour

Update these endpoints to:
1. Accept optional `community_id` query parameter
2. Default to user's current community if not specified
3. Filter results by community
4. Verify user is member of community before returning data

Example:
```python
@router.get("/")
async def list_listings(
    community_id: Optional[str] = None,
    request: Request,
    repo: ListingRepository = Depends(get_listing_repo),
    community_repo: CommunityRepository = Depends(get_community_repo)
):
    user = request.state.user

    # Default to user's first community if not specified
    if not community_id:
        communities = await community_repo.get_user_communities(user.id)
        if not communities:
            raise HTTPException(400, "User not in any community")
        community_id = communities[0].id

    # Verify membership
    if not await community_repo.is_member(user.id, community_id):
        raise HTTPException(403, "Not a member of this community")

    # Filter by community
    listings = await repo.list_listings(community_id=community_id)
    return listings
```

## Phase 4: Frontend Implementation (4 hours)

### Task 4.1: Create CommunityContext
**File**: `frontend/src/contexts/CommunityContext.tsx` (new)
**Estimated**: 1 hour

```typescript
interface Community {
  id: string;
  name: string;
  description?: string;
}

interface CommunityContextType {
  communities: Community[];
  currentCommunity: Community | null;
  switchCommunity: (communityId: string) => void;
  refreshCommunities: () => Promise<void>;
}

export const CommunityProvider: React.FC = ({ children }) => {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [currentCommunity, setCurrentCommunity] = useState<Community | null>(null);

  useEffect(() => {
    loadCommunities();
  }, []);

  // Load from localStorage or default to first community
  useEffect(() => {
    const savedId = localStorage.getItem('current_community_id');
    if (savedId && communities.length) {
      const community = communities.find(c => c.id === savedId);
      setCurrentCommunity(community || communities[0]);
    } else if (communities.length) {
      setCurrentCommunity(communities[0]);
    }
  }, [communities]);

  // ...
};
```

### Task 4.2: Create CommunitySelector component
**File**: `frontend/src/components/CommunitySelector.tsx` (new)
**Estimated**: 1 hour

Dropdown in header showing:
- Current community name
- List of user's communities
- "Switch to..." option
- Link to "My Communities" page

### Task 4.3: Create CommunitiesPage
**File**: `frontend/src/pages/CommunitiesPage.tsx` (new)
**Estimated**: 1.5 hours

Shows:
- List of user's communities
- "Create New Community" button
- Community cards with:
  - Name, description
  - Member count
  - "View" button
  - "Settings" button (if admin)

### Task 4.4: Update API calls to include community
**File**: `frontend/src/api/valueflows.ts`, `frontend/src/api/agents.ts`
**Estimated**: 30 minutes

Add `community_id` parameter to all list/create requests:
```typescript
export const getListings = async (communityId: string) => {
  const response = await api.get('/vf/listings/', {
    params: { community_id: communityId }
  });
  return response.data;
};
```

## Phase 5: Agent Updates (2 hours)

### Task 5.1: Add community scoping to agents
**File**: All agent files in `app/agents/`
**Estimated**: 2 hours

Update each agent's `_get_*` methods to:
1. Accept `community_id` parameter
2. Pass to VFClient queries
3. Filter results by community

Example:
```python
async def _get_active_offers(self, community_id: str) -> List[Dict]:
    """Get active offers within specified community"""
    offers = await self.vf_client.get_listings(
        listing_type="offer",
        community_id=community_id
    )
    return offers
```

Update `run()` method to accept community_id from request.

## Phase 6: Testing (2 hours)

### Task 6.1: Backend tests
**Estimated**: 1 hour

- Test community CRUD operations
- Test membership management
- Test community scoping queries
- Test unauthorized access

### Task 6.2: Integration tests
**Estimated**: 1 hour

- Test full flow: create community → add members → create offers → verify scoping
- Test user in multiple communities sees correct data
- Test data isolation between communities

## Phase 7: Documentation (1 hour)

### Task 7.1: Update API docs
**Estimated**: 30 minutes

Document:
- Community endpoints
- Community filtering on existing endpoints
- community_id parameter usage

### Task 7.2: Update user guide
**File**: `docs/USER_GUIDE.md`
**Estimated**: 30 minutes

Document:
- How to create a community
- How to switch between communities
- How to invite members

## Verification Checklist

- [ ] Communities table created
- [ ] Memberships table created
- [ ] Existing data migrated to default community
- [ ] Community API endpoints work
- [ ] Users can create communities
- [ ] Users can join communities
- [ ] All data correctly scoped by community
- [ ] Frontend community selector works
- [ ] Agents operate within community scope
- [ ] All tests pass

## Estimated Total Time

- Phase 1 (Database): 2 hours
- Phase 2 (Models/Repos): 3 hours
- Phase 3 (API): 3 hours
- Phase 4 (Frontend): 4 hours
- Phase 5 (Agents): 2 hours
- Phase 6 (Testing): 2 hours
- Phase 7 (Docs): 1 hour

**Total: 17 hours (~1 day for experienced developer, 2 days for learning curve)**

## Dependencies

- GAP-02 (User Identity) must be complete
- Database migrations infrastructure
- VFClient updates to support community filtering
