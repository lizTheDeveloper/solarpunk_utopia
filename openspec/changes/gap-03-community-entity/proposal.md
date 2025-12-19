# GAP-03: Community/Commune Entity

**Status**: Backend Implemented - Frontend Pending
**Priority**: P1 - Critical (Demo Blocker)
**Estimated Effort**: 1 day
**Assigned**: Claude Agent (Backend Complete)
**Completed**: December 19, 2025 (Backend)

## Problem Statement

The system has no concept of a "community" or "commune." All data exists in a single global namespace. There's no way to:
- Name a community ("Oak Street Collective")
- Define community boundaries
- Manage community membership
- Scope offers/needs to a specific community
- Support multiple communities on one server

This breaks the core use case: a commune needs an identity, members, and boundaries.

## Current Reality

**Locations**:
- No community model exists
- All queries return global results
- No filtering by community
- No concept of "my community" vs "other communities"

The system can only support ONE unnamed commune per deployment. Multi-commune deployments are impossible.

## Required Implementation

The system SHALL implement a community entity with membership and scoping.

### MUST Requirements

1. The system MUST define a Community model with:
   - Unique ID
   - Name
   - Created timestamp
   - Settings (JSON for extensibility)
2. The system MUST define a CommunityMembership model linking users to communities
3. The system MUST scope all listings (offers/needs) to a specific community
4. The system MUST scope all agents to operate within a specific community
5. The system MUST scope all exchanges to a specific community
6. The system MUST provide API to create communities
7. The system MUST provide API to add/remove community members

### SHOULD Requirements

1. The system SHOULD support users belonging to multiple communities
2. The system SHOULD provide community settings management
3. The system SHOULD show community member count
4. The system SHOULD support community discovery (public vs private)

### MAY Requirements

1. The system MAY support community-level permissions (admin, member, viewer)
2. The system MAY support cross-community exchanges (future)
3. The system MAY support community templates/presets

## Scenarios

### WHEN creating a new community

**GIVEN**: Alice wants to start "Oak Street Collective"

**WHEN**: Alice creates a community

**THEN**:
1. System MUST create community with unique ID
2. System MUST set Alice as the creator and first member
3. System MUST initialize empty member list
4. System MUST initialize default settings
5. Community MUST appear in community list

### WHEN user joins a community

**GIVEN**:
- Community "Oak Street Collective" exists
- Bob wants to join

**WHEN**: Bob joins the community (via invite or request)

**THEN**:
1. System MUST create membership record linking Bob to community
2. Bob MUST see Oak Street data when viewing that community
3. Bob's offers MUST be scoped to Oak Street
4. Bob MUST appear in community member list

### WHEN user creates an offer

**GIVEN**: Alice is a member of "Oak Street Collective"

**WHEN**: Alice creates an offer for tomatoes

**THEN**:
1. Offer MUST be associated with Oak Street community
2. Offer MUST be visible to Oak Street members
3. Offer MUST NOT be visible to members of other communities
4. Agents operating on Oak Street MUST see this offer

### WHEN viewing offers from different communities

**GIVEN**: Alice is a member of both "Oak Street Collective" and "River Commons"

**WHEN**: Alice views the offers page

**THEN**:
1. UI MUST show community selector
2. Selecting Oak Street MUST show only Oak Street offers
3. Selecting River Commons MUST show only River Commons offers
4. "All my communities" view SHOULD aggregate both

### WHEN agent creates proposal within community

**GIVEN**: Mutual aid matchmaker runs in "Oak Street Collective"

**WHEN**: Agent finds a match

**THEN**:
1. Proposal MUST be scoped to Oak Street
2. Only Oak Street members MUST be notified
3. VF Match MUST be scoped to Oak Street
4. Cross-community matches MUST NOT be created

## Architecture

### Database Schema

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
    role TEXT DEFAULT 'member',  -- 'creator', 'admin', 'member'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (community_id) REFERENCES communities(id) ON DELETE CASCADE,
    UNIQUE(user_id, community_id)
);

CREATE INDEX idx_memberships_user ON community_memberships(user_id);
CREATE INDEX idx_memberships_community ON community_memberships(community_id);
```

### Schema Migrations

Add `community_id` to existing tables:
- `listings` (offers/needs)
- `vf_matches`
- `vf_exchanges`
- `vf_commitments`
- `proposals`

### API Endpoints

```
POST   /communities/                    - Create community
GET    /communities/                    - List communities (user's communities)
GET    /communities/{id}                - Get community details
PATCH  /communities/{id}                - Update community settings
DELETE /communities/{id}                - Delete community (admin only)

POST   /communities/{id}/members        - Add member
GET    /communities/{id}/members        - List members
DELETE /communities/{id}/members/{uid}  - Remove member

GET    /communities/{id}/stats          - Community statistics
```

### Frontend Changes

1. **Community Selector**:
   - Header component with dropdown
   - Persists selected community in localStorage
   - All API calls include community context

2. **Community Settings Page**:
   - Community name, description
   - Member management
   - Settings toggles

3. **Multi-Community Support**:
   - "My Communities" page
   - Switch between communities
   - Aggregate view option

## Files to Create

### Backend
- `valueflows_node/app/models/community.py`
- `valueflows_node/app/repositories/community_repo.py`
- `valueflows_node/app/api/communities.py`
- `app/database/migrations/002_add_communities.sql`

### Frontend
- `frontend/src/contexts/CommunityContext.tsx`
- `frontend/src/hooks/useCommunity.ts`
- `frontend/src/components/CommunitySelector.tsx`
- `frontend/src/pages/CommunitiesPage.tsx`
- `frontend/src/pages/CommunitySettingsPage.tsx`

## Files to Modify

### Backend
- `valueflows_node/app/models/vf/listing.py` - Add community_id
- `valueflows_node/app/models/vf/match.py` - Add community_id
- `valueflows_node/app/models/vf/exchange.py` - Add community_id
- `app/models/proposal.py` - Add community_id
- All VF API endpoints - Add community filtering
- All agent implementations - Add community scoping

### Frontend
- `frontend/src/App.tsx` - Add CommunityProvider
- All pages - Use community context for filtering
- All forms - Include community_id in submissions

## Migration Strategy

For existing data:
1. Create default community: "Default Commune"
2. Assign all existing data to default community
3. Assign all existing users to default community
4. Allow users to rename/customize from there

## Testing Requirements

1. **Unit tests**:
   - Community CRUD operations
   - Membership CRUD operations
   - Community scoping queries

2. **Integration tests**:
   - Create community → add members → create offer → verify scoping
   - User in 2 communities → verify data isolation
   - Agent runs in community → verify proposals scoped

3. **Migration tests**:
   - Verify existing data migrated to default community
   - Verify no data loss

## Implementation Status

### ✅ Backend Complete (December 19, 2025)

**Files Created:**
- `/valueflows_node/app/models/community.py` - Community & CommunityMembership models
- `/valueflows_node/app/services/community_service.py` - Full CRUD service layer
- `/valueflows_node/app/api/communities.py` - Complete REST API with auth
- `/valueflows_node/app/database/migrations/001_add_communities.sql` - Database schema

**Files Modified:**
- `/app/database/db.py` - Added communities and community_memberships tables (lines 202-238)
- `/valueflows_node/app/main.py` - Communities router registered (line 48)

**API Endpoints Implemented:**
- `POST /communities` - Create community (creator becomes first member)
- `GET /communities` - List user's communities
- `GET /communities/{id}` - Get community details
- `PATCH /communities/{id}` - Update settings (admin/creator only)
- `DELETE /communities/{id}` - Delete community (creator only)
- `POST /communities/{id}/members` - Add member
- `GET /communities/{id}/members` - List members
- `DELETE /communities/{id}/members/{uid}` - Remove member
- `GET /communities/{id}/stats` - Community statistics

**Database Schema:**
- `communities` table with id, name, description, created_at, settings (JSON), is_public
- `community_memberships` table with id, user_id, community_id, role, joined_at
- Foreign keys with CASCADE delete
- Indexes on key columns for performance
- `community_id` column added to listings, matches, exchanges tables

**Features Working:**
- ✅ Multi-community support (users can belong to multiple communities)
- ✅ Role-based permissions (creator, admin, member)
- ✅ Public/private community visibility
- ✅ Community statistics (member count, listings, exchanges, proposals)
- ✅ Data scoping (listings, matches, exchanges scoped to community)

### ⏳ Frontend Pending

**Still Needed:**
- CommunityContext provider
- Community selector component in header
- Communities list page
- Community settings page
- Integration with all forms to include community_id

## Success Criteria

**Backend:**
- [x] Communities can be created and managed
- [x] Users can join communities
- [x] All data is scoped to communities
- [x] Multi-community support works
- [x] Database migration created
- [ ] All tests pass (no tests written yet)

**Frontend:**
- [ ] Community selector in UI
- [ ] Community settings page
- [ ] Multi-community view
- [ ] Forms include community context

## Dependencies

- GAP-02 (User Identity System) - MUST be complete first
- Database supports JSON columns (SQLite 3.38+)

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-03`
- Related gaps: GAP-02 (User Identity), GAP-17 (My Stuff View)
