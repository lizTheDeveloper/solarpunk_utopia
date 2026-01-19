# Vision-Reality Delta: Implementation Gaps

This document lists specific gaps between the spec vision and current implementation, with actionable details for implementation.

**Last Updated**: December 19, 2025 16:45 UTC
**Session**: 3F - Inter-Community Sharing

**Agent Assignment Key**:
- 🔵 Claude Agent 1 (Main) - Working on this
- 🟢 Claude Agent 2 - Working on this
- ⚪ Unclaimed - Available

---

## 📊 Progress Summary

### Session 3F Completions (Agent 1)

✅ **Inter-Community Sharing**: Trust-Based Discovery → **COMPLETE**
- Full implementation of individual-choice visibility system
- 5 graduated visibility levels (my_cell → network_wide)
- Pull-based discovery API with trust filtering
- Frontend UI: VisibilitySelector + NetworkResourcesPage
- Backend: SharingPreference model, InterCommunityService, discovery endpoints
- Archived to: `openspec/archive/2025-12-19-inter-community-sharing/`

**Files Created**:
- Backend: `discovery.py`, `sharing_preference.py`, `sharing_preference_repo.py`, `inter_community_service.py`
- Frontend: `VisibilitySelector.tsx`, `NetworkResourcesPage.tsx`, `interCommunitySharing.ts`
- Migration: `003_add_is_private_to_listings.sql`

**Philosophy**: No gatekeepers - individuals control their own visibility. Pull not push.

### Session 3E Completions (Agent 1)

✅ **GAP-06**: API Routing Mismatch → **COMPLETE**
- Fixed Vite proxy to preserve `/vf` prefix
- Added GET endpoints for `/vf/matches` and `/vf/exchanges`
- Updated frontend API client to unwrap response format
- All API calls now returning 200 OK

✅ **E2E Test Suite**: Playwright Tests → **COMPLETE**
- Created comprehensive e2e tests for GAP-04, GAP-10, GAP-18
- 16/17 tests passing (1 intentionally skipped)
- Tests validate page loads, UI elements, and functionality

✅ **Seed Data**: Demo Database → **POPULATED**
- 20 offers, 10 needs, 15 resource specs, 10 members
- Full gift economy cycle ready for testing

### Session 3C Completions (Agent 1)

✅ **GAP-05**: Proposal Persistence → **COMPLETE**
- Full SQLite persistence with ProposalRepository
- 9/9 tests passing
- Zero data loss on restarts

✅ **GAP-06**: Agents API Routing → **PARTIAL** (Agents working, VF remains)
- Added `/api/agents/` nginx route
- Fixed frontend baseURL and all agent paths
- Frontend can now communicate with agents API

✅ **GAP-07**: Approval Payload Format → **COMPLETE**
- Fixed payload transformation in reviewProposal()
- Approvals now work correctly
- No more 422 errors

### Overall Status

| Category | Total | Complete | In Progress | Remaining |
|----------|-------|----------|-------------|-----------|
| **Priority 1 (Critical)** | 8 gaps | 5 | 0 | 3 |
| **Priority 2 (Core UX)** | 12 gaps | 2 | 0 | 10 |
| **Priority 3+ (Nice-to-Have)** | 30+ gaps | 0 | 0 | 30+ |

**Critical Path**: 5 / 8 complete (62.5%) → Frontend-Backend communication fully working! 🎉

### Files Modified This Session
- `app/database/db.py` - Added proposals table
- `app/database/proposal_repo.py` - NEW (215 lines)
- `app/agents/framework/approval.py` - Database integration
- `app/api/agents.py` - Fixed logger + async bugs
- `docker/nginx.conf` - Added agents route
- `frontend/src/api/agents.ts` - Fixed baseURL + paths
- `test_proposal_persistence.py` - NEW (186 lines, 9 tests)

**See**: `devlog/SESSION_3C_GAPS_567_COMPLETION.md` for complete details

---

## Priority 1: Critical Path (Demo Blockers)

### GAP-01: Agent Proposal Approval Does Nothing 🔵 CLAIMED

**Status**: 🔵 Claude Agent 1 working on this

**Vision**: When Alice and Bob both approve a match proposal, a VF Exchange is created and they're connected.

**Reality**: Approval is recorded in memory, but no VF objects are created. The proposal just sits there "approved."

**Location**: `app/api/agents.py:130-152` (approve_proposal endpoint)

**What to build**:
```python
# After both parties approve:
1. Create VF Match via POST /vf/matches/
2. Create VF Exchange via POST /vf/exchanges/
3. Update proposal status to "executed"
4. (Future: trigger notification)
```

**Files to modify**:
- `app/api/agents.py` - extend `approve_proposal`
- `app/agents/framework/approval.py` - add `execute_proposal()` method

**Estimated effort**: 2-3 hours

---

### GAP-02: No User Identity System

**Vision**: Alice logs in, sees her offers, approves proposals addressed to her.

**Reality**: No authentication. No "current user." Everyone sees everything with no ownership.

**What to build**:
- Simple auth (magic link email, or local-only user creation for MVP)
- User ID attached to offers/needs/approvals
- "My offers" vs "community offers" filtering

**Files to create**:
- `app/auth/` - new auth module
- `valueflows_node/app/api/vf/auth.py` - VF auth endpoints

**Files to modify**:
- `frontend/src/App.tsx` - add auth context
- `frontend/src/hooks/useAuth.ts` - new hook
- All API calls need user context

**Estimated effort**: 1-2 days

---

### GAP-03: No Community/Commune Entity

**Vision**: "Oak Street Collective" is a named community with members, settings, and shared data.

**Reality**: Single global namespace. No community boundaries.

**What to build**:
- Community model (name, created_at, settings, member list)
- Community membership (user + community + role)
- Scoping all queries to community

**Files to create**:
- `valueflows_node/app/models/community.py`
- `valueflows_node/app/repositories/community_repo.py`
- `valueflows_node/app/api/communities.py`

**Estimated effort**: 1 day

---

### GAP-04: Seed Data for Demo ✅ COMPLETE

**Status**: ✅ IMPLEMENTED

**Vision**: Workshop attendees see a living commune with realistic activity.

**Reality**: ~~Empty database. No demo content.~~

**Solution Implemented**:
```bash
python scripts/seed_demo_data.py
```

Creates:
- ✅ 15 resource specs (food, tools, skills, housing)
- ✅ 10 commune members (Alice, Bob, Carol, David, Eve, Frank, Grace, Henry, Iris, Jack)
- ✅ 20 realistic offers with descriptions
- ✅ 10 realistic needs with descriptions
- ✅ Runs mutual aid matchmaker to generate proposals

**Files Created**:
- `scripts/seed_demo_data.py` - Complete seeding script

**Tests**: `tests/e2e/test_seed_data.spec.ts`

**Estimated effort**: ~~3-4 hours~~ → ✅ Completed

---

### GAP-05: Proposals Lost on Server Restart (CRITICAL) ✅ COMPLETE

**Assigned**: Agent 1
**Status**: ✅ IMPLEMENTED

**Vision**: Proposals persist and survive restarts.

**Reality**: ~~`ApprovalTracker` stores proposals in-memory only: `self._proposals: Dict[str, Proposal] = {}`. Server restart = all proposals gone.~~

**Solution Implemented**:
- ✅ Created `ProposalRepository` class (`app/database/proposal_repo.py`)
- ✅ Added proposals table to database schema (`app/database/db.py`)
- ✅ Updated `ApprovalTracker` to use database instead of in-memory dict
- ✅ All methods now persist: `store_proposal()`, `approve_proposal()`, `mark_executed()`, etc.
- ✅ Created comprehensive test suite (`test_proposal_persistence.py`)
- ✅ Fixed missing logger import in `app/api/agents.py`
- ✅ Added `await` to async `get_stats()` call

**Testing**: All 9 persistence tests passing
- Store/retrieve proposals
- Update approvals
- Filter by agent/status/user
- Count by status
- Delete proposals

**Files Modified**:
- `app/database/db.py` - Added proposals table schema
- `app/database/proposal_repo.py` - NEW: Repository for proposal CRUD
- `app/agents/framework/approval.py` - Replaced in-memory dict with DB calls
- `app/api/agents.py` - Fixed logger import, added await to get_stats()
- `test_proposal_persistence.py` - NEW: Comprehensive test suite

**Severity**: ~~CRITICAL~~ → ✅ RESOLVED

---

### GAP-06: Frontend/Backend API Route Mismatch (CRITICAL) ✅ COMPLETE

**Assigned**: Agent 1
**Status**: ✅ FULLY IMPLEMENTED

**Vision**: Frontend calls work.

**Reality**: ~~Multiple mismatches causing 404s and 422s~~

**Route Mismatches (ALL FIXED)**:
| Frontend calls | Backend has | Problem | Status |
|---------------|-------------|---------|--------|
| `/api/vf/ai-agents` | `/agents` on port 8000 | Agents on DTN, not VF! | ✅ FIXED |
| `/api/vf/listings` | `/vf/listings` | Proxy stripping /vf prefix | ✅ FIXED |
| `/api/vf/matches` | `/vf/matches` | Missing GET endpoint | ✅ FIXED |
| `/api/vf/exchanges` | `/vf/exchanges` | Missing GET endpoint | ✅ FIXED |
| `/api/vf/ai-agents/proposals/{id}/review` | `/agents/proposals/{id}/approve` | Wrong path + payload | ✅ FIXED (GAP-07) |

**Solution Implemented**:

**Phase 1 - Agents Routing (Session 3C)**:
- ✅ Added `/api/agents/` route in nginx:96-113 → dtn-bundle-system:8000
- ✅ Changed frontend `baseURL: '/api/agents'` in agents.ts:12
- ✅ Fixed all agent endpoint paths (removed `/ai-agents` prefix)
- ✅ Updated response parsing to match backend format

**Phase 2 - VF API Routing (Session 3E)**:
- ✅ Fixed Vite proxy: changed rewrite from `replace(/^\/api\/vf/, '')` to `replace(/^\/api/, '')` to preserve `/vf` prefix
- ✅ Added GET `/vf/matches` endpoint with proper `find_all()` usage
- ✅ Added GET `/vf/exchanges` endpoint with proper `find_all()` usage
- ✅ Fixed frontend API client to unwrap `{ matches: [], count: N }` and `{ exchanges: [], count: N }` responses
- ✅ Fixed repository method calls (removed invalid `status` parameter from `find_all()`)

**Files Modified**:
- `docker/nginx.conf` - Added agents proxy block
- `frontend/src/api/agents.ts` - Changed baseURL, fixed all paths
- `frontend/vite.config.ts` - Fixed proxy rewrite to preserve `/vf` prefix
- `frontend/src/api/valueflows.ts` - Updated getMatches/getExchanges to unwrap responses
- `valueflows_node/app/api/vf/matches.py` - Added GET endpoint, fixed find_all() call
- `valueflows_node/app/api/vf/exchanges.py` - Added GET endpoint, fixed find_all() call

**Testing**:
```bash
# All endpoints now returning 200 OK
GET /vf/listings?listing_type=offer  → 200 OK ✓
GET /vf/listings?listing_type=need   → 200 OK ✓
GET /vf/matches                      → 200 OK ✓
GET /vf/exchanges                    → 200 OK ✓
```

**E2E Tests**: 16/17 passing (1 skipped)

**Estimated effort**: ~~2-3 hours~~ → ✅ Completed (2.5 hours total)

**Severity**: ~~CRITICAL~~ → ✅ FULLY RESOLVED

---

### GAP-06B: No DELETE Endpoint for Listings

**Vision**: User can delete/cancel their offers.

**Reality**: Frontend calls `DELETE /api/vf/intents/{id}` but backend has no DELETE endpoint.

**Location**:
- Frontend: `frontend/src/api/valueflows.ts:89-91`
- Backend: `valueflows_node/app/api/vf/listings.py` - no DELETE route

**What to build**:
- Add `DELETE /vf/listings/{id}` endpoint
- Or: use PATCH to set `status: 'cancelled'`

**Estimated effort**: 30 minutes

---

### GAP-07: Frontend Approval Sends Wrong Payload ✅ COMPLETE

**Assigned**: Agent 1
**Status**: ✅ FIXED

**Vision**: User approves proposal.

**Reality**: ~~Frontend sends `{ action, note }` but backend expects `{ user_id, approved, reason }`~~

**Solution Implemented**:
- ✅ Changed endpoint from `/proposals/{id}/review` → `/proposals/{id}/approve`
- ✅ Transformed payload format in `reviewProposal()` function:
  - `user_id: 'demo-user'` (hardcoded until identity system exists)
  - `approved: action === 'approve'` (maps approve/reject to boolean)
  - `reason: note` (maps note to reason)

**Files Modified**:
- `frontend/src/api/agents.ts:73-83` - Fixed `reviewProposal()` method

**Before**:
```typescript
const response = await api.post(`/ai-agents/proposals/${id}/review`, {
  action,
  note,
});
```

**After**:
```typescript
const response = await api.post(`/proposals/${id}/approve`, {
  user_id: 'demo-user',
  approved: action === 'approve',
  reason: note,
});
```

**Estimated effort**: ~~30 minutes~~ → ✅ Completed

**Severity**: ~~HIGH~~ → ✅ RESOLVED - approvals now work correctly

---

### GAP-08: VF Bundle Publisher Doesn't Publish (Multi-node)

**Vision**: VF objects become DTN bundles for mesh sync.

**Reality**: Publisher just prints and returns False if no outbox configured.

**Location**: `valueflows_node/app/services/vf_bundle_publisher.py:133-134`

```python
if not self.dtn_outbox_path:
    print(f"Would publish...")
    return False  # Does nothing!
```

**For single-node demo**: Can defer
**For multi-node**: Must fix

**Estimated effort**: 2-3 hours

**Severity**: MEDIUM (single-node OK), CRITICAL (multi-node)

---

## Priority 2: Core Experience Gaps

### GAP-09: No Notification/Awareness System

**Vision**: Alice gets notified when there's a match proposal needing her approval.

**Reality**: Alice must manually navigate to /agents page and hope something's there.

**What to build (MVP)**:
- Polling-based check: "Do I have pending proposals?"
- Badge on navigation: "Agents (3)"
- Homepage card: "3 proposals need your review"

**Files to modify**:
- `frontend/src/components/Navigation.tsx` - add badge
- `frontend/src/hooks/useAgents.ts` - add pending count query
- `frontend/src/pages/HomePage.tsx` - already has pending section, just needs prominence

**What to build (Better)**:
- NATS → WebSocket → frontend real-time updates
- Push notifications (requires service worker)

**Estimated effort**: MVP 2-3 hours, Better 1-2 days

---

### GAP-10: Exchange Completion Flow ✅ COMPLETE

**Status**: ✅ IMPLEMENTED

**Vision**: Alice and Bob meet, exchange tomatoes, both mark complete in app.

**Reality**: ~~Backend has `/vf/exchanges/{id}/complete` but no frontend UI.~~

**Solution Implemented**:
- ✅ Added `completeExchange()` API method to valueflows client
- ✅ Added `useCompleteExchange()` hook that creates event + marks complete
- ✅ Updated ExchangesPage with completion buttons for both parties
- ✅ Shows completion state for provider and receiver separately
- ✅ Celebration message when both parties confirm
- ✅ Buttons disabled after confirmation

**Files Modified**:
- `frontend/src/api/valueflows.ts` - added completeExchange method
- `frontend/src/hooks/useExchanges.ts` - added useCompleteExchange hook
- `frontend/src/pages/ExchangesPage.tsx` - added completion UI

**Tests**: `tests/e2e/test_exchange_completion.spec.ts`

**Estimated effort**: ~~3-4 hours~~ → ✅ Completed

---

### GAP-11: Agents Use Mock Data ✅ MOSTLY COMPLETE

**Status**: ✅ 71% Complete (5/7 agents using live VF database)
**Completed by**: Claude Agent 1 (Session 2)

**Vision**: Work Party Scheduler queries real VF Plans and participant availability.

**Reality**: ~~Returns hardcoded mock data.~~ **UPDATED**: Most agents now query VF database with fallback to mock data.

**✅ Completed Agents** (using VFClient):
- `app/agents/mutual_aid_matchmaker.py` - `_get_active_offers()`, `_get_active_needs()`
- `app/agents/perishables_dispatcher.py` - `_get_expiring_offers()`, `_find_matching_needs()`
- `app/agents/inventory_agent.py` - `_get_inventory()`, `_get_upcoming_resource_needs()`
- `app/agents/work_party_scheduler.py` - `_get_active_plans()`
- `app/agents/education_pathfinder.py` - `_find_lessons_for_skills()`, `_find_relevant_protocols()`

**⚪ Remaining Mock Data** (2 agents):
- `app/agents/work_party_scheduler.py:151-198` - `_get_available_participants()` (needs VF Commitments query)
- `app/agents/permaculture_planner.py` - `_get_active_goals()` (needs VF Goals), `_suggest_guilds()` (needs LLM)
- `app/agents/commons_router.py` - `_get_cache_state()` (needs cache database)

**What to build**:
- Query VF Plans via VFClient
- Query VF Commitments for availability
- Query VF Listings for matching needs

**Files to modify**:
- `app/clients/vf_client.py` - add `get_plans()`, `get_commitments()` methods
- Each agent file listed above

**Estimated effort**: 4-6 hours total

---

### GAP-12: Onboarding Flow

**Vision**: "Hello, let's get your Solarpunk commune going" → guided first-time experience.

**Reality**: App opens to empty homepage with no guidance.

**What to build**:
- First-run detection (localStorage or user flag)
- Welcome sequence (5-7 screens)
- First offer creation flow
- First need creation (optional)
- Invite flow

**Files to create**:
- `frontend/src/pages/OnboardingPage.tsx`
- `frontend/src/components/onboarding/` - step components

**Files to modify**:
- `frontend/src/App.tsx` - route to onboarding if first run

**See**: `ONBOARDING_EXPERIENCE.md` for full design

**Estimated effort**: 1-2 days

---

## Priority 3: Polish & Depth

### GAP-13: No Urgency Indicators

**Vision**: Expiring offers show red/yellow badges. Urgent proposals are prominent.

**Reality**: All offers look the same regardless of TTL.

**What to build**:
- Calculate hours until expiry for each offer
- Add urgency badge component
- Sort/filter by urgency

**Files to modify**:
- `frontend/src/components/OfferCard.tsx`
- `frontend/src/pages/OffersPage.tsx`

**Estimated effort**: 2-3 hours

---

### GAP-14: No Calendar Integration

**Vision**: "Add to Calendar" button exports work party as ICS file.

**Reality**: No calendar export.

**What to build**:
- ICS file generation for exchanges and work parties
- Download button on relevant cards

**Estimated effort**: 2-3 hours

---

### GAP-15: No Statistics/Impact Tracking

**Vision**: "Alice has shared 47 items this year. Your commune facilitated 230 gifts."

**Reality**: No aggregate tracking.

**What to build**:
- Event counting by agent
- Community totals
- Dashboard component

**Estimated effort**: 4-6 hours

---

### GAP-16: DTN Sync is Manual

**Vision**: Phone auto-syncs when joining new AP network.

**Reality**: Must manually call sync endpoints.

**What to build (for demo)**:
- "Sync Now" button in UI
- Sync status display
- Last sync timestamp

**What to build (for real)**:
- Network change detection
- Background sync service
- Requires native app or PWA with service worker

**Estimated effort**: Demo 2-3 hours, Real requires native work

---

## Priority 4: UX Polish Gaps

### GAP-17: No "My Stuff" View

**Vision**: Alice sees her offers, her needs, her pending exchanges in one place.

**Reality**: All offers/needs mixed together. No ownership filtering.

**What to build**:
- "My Offers" tab on Offers page
- "My Needs" tab on Needs page
- "My Exchanges" section on Exchanges page
- Profile page showing activity summary

**Estimated effort**: 3-4 hours

---

### GAP-18: Edit/Delete for Offers & Needs ✅ COMPLETE

**Status**: ✅ IMPLEMENTED

**Vision**: Fix typos, update quantities, cancel offers.

**Reality**: ~~Once posted, can't modify or remove.~~

**Solution Implemented**:
- ✅ Added Edit and Delete buttons to OfferCard and NeedCard components
- ✅ Buttons only visible to listing owner (isOwner check)
- ✅ Delete includes confirmation dialog
- ✅ Integrated useDeleteOffer and useDeleteNeed hooks
- ✅ Edit navigates to edit page (/offers/{id}/edit or /needs/{id}/edit)
- ✅ Icon buttons with hover states and proper styling

**Files Modified**:
- `frontend/src/components/OfferCard.tsx` - added edit/delete buttons
- `frontend/src/components/NeedCard.tsx` - added edit/delete buttons
- `frontend/src/pages/OffersPage.tsx` - wired up handlers
- `frontend/src/pages/NeedsPage.tsx` - wired up handlers

**Tests**: `tests/e2e/test_edit_delete.spec.ts`

**Estimated effort**: ~~2-3 hours~~ → ✅ Completed

---

### GAP-19: No Messaging Between Matched Parties

**Vision**: Alice and Bob coordinate handoff details after matching.

**Reality**: No communication channel. They'd have to... find each other somehow?

**What to build (MVP)**:
- Show contact info in match/exchange details
- Or: Simple message field on proposals

**What to build (Better)**:
- In-app messaging thread per exchange
- Or: NATS-based chat

**Estimated effort**: MVP 1 hour, Better 1-2 days

---

### GAP-20: No Photos on Offers

**Vision**: See what you're getting - picture of the tomatoes, the tool, etc.

**Reality**: Text only.

**What to build**:
- Image upload on offer creation
- Image display on cards
- Thumbnail + full view

**Note**: File chunking system exists, could use it

**Estimated effort**: 4-6 hours

---

### GAP-21: No Filter/Sort on Offers & Needs Pages

**Vision**: "Show me only food offers near me"

**Reality**: Flat list, no filtering.

**What to build**:
- Category filter dropdown
- Location filter
- Sort by: newest, expiring soon, nearest
- Search within offers/needs

**Estimated effort**: 3-4 hours

---

### GAP-22: Locations Are Hardcoded

**Vision**: Communities define their own locations.

**Reality**: `COMMON_LOCATIONS` array in code: "North Garden", "Tool Shed", etc.

**Location**: `frontend/src/utils/categories.ts:240-251`

**What to build**:
- Locations table in VF database
- Admin UI to manage locations
- Or: "Other (specify)" option with free text

**Estimated effort**: 2-3 hours (quick fix), 1 day (proper)

---

### GAP-23: No Custom Items Beyond Predefined List

**Vision**: Offer something unique not in the category list.

**Reality**: Must pick from fixed items list.

**What to build**:
- "Other" option with free text input
- Save custom items to resource_specs table
- Show recently used items

**Estimated effort**: 2-3 hours

---

### GAP-24: No Recurring Offers

**Vision**: "I have eggs every week" - not a one-time thing.

**Reality**: Each offer is a single instance.

**What to build**:
- "This is recurring" toggle
- Frequency selector (weekly, monthly)
- Auto-renew offers

**Estimated effort**: 4-6 hours

---

### GAP-25: "Accept Offer" Button Does Nothing Useful

**Vision**: Click "Accept Offer" → express interest → coordinate exchange.

**Reality**: Button exists (`OfferCard.tsx:66`) but `onAccept` handler likely doesn't create the right flow.

**What to build**:
- Click Accept → Create a "match request" or "expression of interest"
- Notify the offerer
- Start coordination flow

**Currently**: Probably just navigates somewhere or does nothing

**Estimated effort**: 3-4 hours

---

### GAP-26: Navigation Badge Not Displayed

**Vision**: "AI Agents (3)" shows pending proposals count.

**Reality**: Code fetches `pendingCount` but never displays it!

**Location**: `frontend/src/components/Navigation.tsx:32-43` - fetches but doesn't use

**What to build**:
- Actually show the badge on the nav item
- Style it (red dot, number badge)

**Estimated effort**: 30 minutes

---

### GAP-27: No Offline/Sync Status Indicator

**Vision**: "Last synced 5 minutes ago" - know if data is stale.

**Reality**: No indication of network state or data freshness.

**What to build**:
- "Offline" banner when no network
- "Last synced: X ago" in header or footer
- "Syncing..." indicator during sync

**Estimated effort**: 2-3 hours

---

### GAP-28: No Success/Error Feedback (Toasts)

**Vision**: "Offer created!" confirmation, "Failed to save" error.

**Reality**: Silent success, generic error messages.

**What to build**:
- Toast notification component
- Success toasts on create/update/delete
- Error toasts with helpful messages

**Estimated effort**: 2-3 hours

---

### GAP-29: No Mobile Bottom Navigation

**Vision**: Thumb-friendly navigation on phones.

**Reality**: Horizontal scrolling nav works but isn't ideal for mobile.

**What to build**:
- Fixed bottom nav bar for mobile
- 4-5 key icons (Home, Offers, Needs, Agents, More)
- Hide top nav on mobile or make it minimal

**Estimated effort**: 2-3 hours

---

### GAP-30: No Proximity/Distance Display

**Vision**: "Alice (0.3 miles away)" - know who's nearby.

**Reality**: Location shown but no distance calculation.

**What to build**:
- Store user location (opt-in)
- Calculate distances between locations
- Show "nearby" badges

**Note**: Requires location data model, privacy considerations

**Estimated effort**: 4-6 hours

---

## Priority 5: Agent & Backend Gaps

### GAP-31: Agent Settings Not Persisted

**Vision**: Disable an agent, restart server, it stays disabled.

**Reality**: Settings returned from memory, changes lost on restart.

**Location**: `app/api/agents.py:220,251,286`

**What to build**:
- Agent settings table in database
- Load settings on startup
- Save on update

**Estimated effort**: 2-3 hours

---

### GAP-32: Agent Stats Return Mock Data

**Vision**: See how many proposals each agent has created, approval rates.

**Reality**: Returns hardcoded mock stats.

**Location**: `app/api/agents.py:326-327,365-366`

**What to build**:
- Track agent runs in database
- Count proposals by agent
- Calculate approval rates

**Estimated effort**: 3-4 hours

---

### GAP-33: Commons Router Uses Mock Cache State

**Vision**: Agent decides caching strategy based on actual node cache.

**Reality**: Returns mock data instead of querying real cache.

**Location**: `app/agents/commons_router.py:83-84`

**What to build**:
- Query `QueueManager.get_total_cache_size()`
- Query actual bundle priorities in cache
- Make real forwarding decisions

**Estimated effort**: 2-3 hours

---

### GAP-34: Work Party Scheduler Uses Mock Availability

**Vision**: Schedule work parties when participants are actually free.

**Reality**: Returns mock participant availability.

**Location**: `app/agents/work_party_scheduler.py:161-162`

**What to build**:
- Query VF Commitments for each participant
- Check for scheduling conflicts
- Find actual free time slots

**Estimated effort**: 3-4 hours

---

### GAP-35: Education Pathfinder Uses Mock Skills/Commitments

**Vision**: Recommend learning based on what user knows and is committed to.

**Reality**: Returns mock skill data and commitments.

**Location**: `app/agents/education_pathfinder.py:88-89,120-121`

**What to build**:
- Query VF Commitments by user
- Track user skills (new table or VF extension)
- Match skills to learning paths

**Estimated effort**: 4-6 hours

---

### GAP-36: Permaculture Planner Missing LLM Integration

**Vision**: AI-powered seasonal planning suggestions.

**Reality**: LLM call not implemented.

**Location**: `app/agents/permaculture_planner.py:74-75,152`

**What to build**:
- Connect to LLM backend (exists in `app/llm/`)
- Generate seasonal recommendations
- Query actual VF Plans and goals

**Estimated effort**: 4-6 hours

---

### GAP-37: Weather API Not Integrated

**Vision**: Work parties scheduled around weather.

**Reality**: Returns "Mock favorable weather for demo".

**Location**: `app/agents/work_party_scheduler.py:385-389`

**What to build**:
- Integrate weather API (OpenWeatherMap, etc.)
- Cache weather forecasts
- Factor into scheduling decisions

**Estimated effort**: 2-3 hours (requires API key)

---

### GAP-38: Proposal Executor Incomplete

**Vision**: Approved proposals trigger cache updates and forwarding.

**Reality**: TODOs for service integration.

**Location**: `app/services/proposal_executor.py:353,367,382`

**What to build**:
- Connect to CacheService for budget updates
- Connect to ForwardingService for routing changes
- Execute CommonsRouter proposals properly

**Estimated effort**: 3-4 hours

---

### GAP-39: Files API Routing May Be Missing

**Vision**: KnowledgePage uploads/downloads files.

**Reality**: Frontend calls `/api/files/*` - nginx routing needs verification.

**What to verify**:
- Does nginx have `/api/files` → file_chunking:8004 route?
- Are all file endpoints implemented?

**Location**:
- `frontend/src/api/files.ts` - expects `/api/files/*`
- `file_chunking/api/` - backend endpoints
- `docker/nginx.conf` - routing

**Estimated effort**: 1-2 hours to verify and fix

---

### GAP-40: LLM Backend Requires Local Setup

**Vision**: Agents use AI for intelligent proposals.

**Reality**: LLM defaults to Ollama which requires local installation.

**Location**: `app/llm/config.py:42`

**Options**:
- Demo: Use `LLM_BACKEND=mock`
- Local: Install Ollama + model
- Remote: Set `LLM_BACKEND=remote` with API key

**Environment variables**: `LLM_BACKEND`, `LLM_MODEL`, `LLM_API_KEY`

**Estimated effort**: Configuration only

---

## Priority 6: Production-Readiness (CRITICAL for Real Deployment)

### GAP-41: CORS Allows All Origins (SECURITY)

**Severity**: CRITICAL

**Reality**: All 5 services have `allow_origins=["*"]` - anyone can make requests.

**Locations**:
- `app/main.py:115`
- `valueflows_node/app/main.py:40`
- `discovery_search/main.py:155`
- `file_chunking/main.py:66`
- `mesh_network/bridge_node/main.py:61`

**What to build**:
- Environment variable for allowed origins
- Default to localhost in dev, explicit origins in prod

**Estimated effort**: 1-2 hours

---

### GAP-42: No Authentication System (SECURITY)

**Severity**: CRITICAL

**Reality**: APIs accept `user_id` as a query parameter - trivially spoofable.

**Locations**:
- `app/api/agents.py:79` - user_id from query, no verification
- `valueflows_node/app/api/vf/listings.py:26` - no auth check
- `frontend/src/api/agents.ts:79` - hardcoded 'demo-user'

**What to build**:
- JWT or session-based auth
- Middleware to verify identity on all protected routes
- User registration/login flow

**Estimated effort**: 2-3 days

---

### GAP-43: Missing Input Validation (SECURITY)

**Severity**: HIGH

**Reality**: API endpoints accept raw dicts without validating required fields exist, are correct type, or reference existing entities.

**Locations**:
- `valueflows_node/app/api/vf/listings.py:26` - no validation that resource_spec_id/agent_id exist
- `valueflows_node/app/api/vf/listings.py:80-81` - category/status not validated against enums

**What to build**:
- Pydantic request models for all endpoints
- Foreign key existence checks before insert
- Enum validation with helpful error messages

**Estimated effort**: 1-2 days

---

### GAP-44: Bare Except Clauses (ERROR HIDING)

**Severity**: HIGH

**Reality**: Several `except:` or `except Exception:` clauses that swallow errors silently.

**Locations**:
- `app/clients/vf_client.py:217,228,239` - bare `except:`
- `app/llm/backends.py:147` - swallows errors

**What to build**:
- Specific exception handling
- Proper error logging
- Re-raise or return structured errors

**Estimated effort**: 2-3 hours

---

### GAP-45: No Foreign Key Enforcement (DATA INTEGRITY)

**Severity**: HIGH

**Reality**: Foreign keys defined in schema but not enforced. Can create listings for non-existent agents/resources.

**Locations**:
- `app/database/db.py:22` - no `PRAGMA foreign_keys = ON`
- `valueflows_node/app/database/vf_schema.sql` - FKs defined but deletions don't cascade

**What to build**:
- Enable FK enforcement in all DB connections
- Add ON DELETE CASCADE or RESTRICT as appropriate
- Validation before insert

**Estimated effort**: 3-4 hours

---

### GAP-46: Race Conditions in Queue/Cache (DATA INTEGRITY)

**Severity**: HIGH

**Reality**: Non-atomic operations allow concurrent access to corrupt state.

**Locations**:
- `app/database/queues.py:67-83` - INSERT OR REPLACE without lock
- `app/services/cache_service.py:70-85` - check-then-delete not atomic

**What to build**:
- Database transactions for multi-step operations
- Proper locking for concurrent access
- Atomic size checking and eviction

**Estimated effort**: 4-6 hours

---

### GAP-47: INSERT OR REPLACE Overwrites Bundles (DATA INTEGRITY)

**Severity**: HIGH

**Reality**: `app/database/queues.py:72-82` uses INSERT OR REPLACE which silently overwrites existing bundles.

**What to build**:
- Check for existence first
- Return error if duplicate
- Or use INSERT OR IGNORE with explicit update logic

**Estimated effort**: 1-2 hours

---

### GAP-48: No Database Migrations (OPERATIONS)

**Severity**: HIGH

**Reality**: Schema created inline, no way to update schema after deployment.

**Locations**:
- `app/database/db.py:26-111` - schema in code
- No alembic or similar migration tool

**What to build**:
- Migration system (alembic for SQLAlchemy or custom for raw SQLite)
- Schema versioning
- Up/down migrations

**Estimated effort**: 1 day

---

### GAP-49: Hardcoded URLs (CONFIGURATION)

**Severity**: HIGH

**Reality**: Localhost URLs hardcoded, won't work in production.

**Locations**:
- `app/services/proposal_executor.py:26` - `"http://localhost:8001"`
- `mesh_network/bridge_node/services/sync_orchestrator.py:75` - `"http://localhost:8000"`
- `app/llm/backends.py:32` - `"http://localhost:11434"`

**What to build**:
- All URLs from environment variables
- Service discovery or config file

**Estimated effort**: 2-3 hours

---

### GAP-50: No Logging for Debugging (OPERATIONS)

**Severity**: MEDIUM

**Reality**: Most operations have no logging - impossible to debug in production.

**Locations**:
- `app/api/bundles.py:21-35` - no logging
- `app/services/cache_service.py:70-85` - no eviction logging
- `valueflows_node/app/api/vf/listings.py` - no logging

**What to build**:
- Structured logging throughout
- Request ID correlation
- Log levels (DEBUG, INFO, WARN, ERROR)

**Estimated effort**: 1 day

---

### GAP-51: Health Checks Don't Verify Dependencies (OPERATIONS)

**Severity**: MEDIUM

**Reality**: Health endpoints return 200 without checking if DB or dependent services are reachable.

**Locations**:
- `app/main.py:144-163` - doesn't check DB
- `docker-compose.yml` - basic HTTP checks only

**What to build**:
- Deep health checks (DB connectivity, service dependencies)
- Readiness vs liveness probes
- Dependency status in health response

**Estimated effort**: 2-3 hours

---

### GAP-52: No Graceful Shutdown (OPERATIONS)

**Severity**: MEDIUM

**Reality**: Services shut down abruptly, potentially losing in-flight operations.

**Locations**:
- `app/main.py` - TTL service just canceled
- No cleanup of pending operations

**What to build**:
- Signal handlers for SIGTERM
- Drain in-flight requests
- Cleanup background tasks properly

**Estimated effort**: 2-3 hours

---

### GAP-53: No Request Tracing (OPERATIONS)

**Severity**: MEDIUM

**Reality**: No correlation IDs - can't trace a request across services.

**What to build**:
- Generate request ID on ingress
- Pass through all service calls
- Include in all logs

**Estimated effort**: 3-4 hours

---

### GAP-54: No Metrics Collection (OPERATIONS)

**Severity**: MEDIUM

**Reality**: No counters, gauges, or histograms for monitoring.

**What to build**:
- Prometheus metrics endpoint
- Request count, latency, error rate
- System metrics (cache size, queue depth, DB connections)

**Estimated effort**: 1 day

---

### GAP-55: Frontend Returns Empty Agent List

**Severity**: MEDIUM

**Reality**: `frontend/src/api/agents.ts:17-21` - `getAgents()` returns empty array instead of calling backend.

**What to build**:
- Actually call `/api/agents/` endpoint
- Handle response properly

**Estimated effort**: 30 minutes

---

### GAP-56: No CSRF Protection (SECURITY)

**Severity**: MEDIUM

**Reality**: No CSRF tokens on state-changing operations.

**What to build**:
- CSRF token generation and validation
- SameSite cookie configuration

**Estimated effort**: 2-3 hours

---

### GAP-57: SQL Injection Risk (SECURITY)

**Severity**: MEDIUM

**Reality**: String interpolation in SQL queries.

**Location**: `valueflows_node/app/repositories/vf/listing_repo.py:135` - `f" LIMIT {limit}"`

**What to build**:
- Use parameterized queries everywhere
- Audit all SQL for interpolation

**Estimated effort**: 2-3 hours

---

### GAP-58: No Backup/Recovery (OPERATIONS)

**Severity**: MEDIUM

**Reality**: SQLite databases in Docker volumes with no backup mechanism.

**What to build**:
- Automated backup script
- Export/import functionality
- Recovery procedures documented

**Estimated effort**: 4-6 hours

---

## Updated Gap Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P1 - Critical | 8 | Demo won't work without these |
| P2 - Core Experience | 4 | Core flows feel incomplete |
| P3 - Polish | 4 | Depth and refinement |
| P4 - UX Polish | 14 | User experience improvements |
| P5 - Agent/Backend | 10 | Mock data and incomplete integrations |
| P6 - Production Ready | 18 | Security, data integrity, operations |
| P7 - Philosophical | 11 | Values alignment, systemic issues |
| **Total** | **69** | |

---

## Implementation Order Recommendation

### Immediate (Before ANY Demo)
1. **GAP-06**: Frontend/Backend route mismatch (1 hour) - nothing works without this
2. **GAP-07**: Frontend approval payload fix (30 min) - approvals will 422 without this
3. **GAP-05**: Proposal persistence (2-3 hours) - or lose everything on restart

### Week 1: Make the Demo Work
4. GAP-04: Seed data (so there's something to see)
5. GAP-01: Proposal→VF bridge (so approvals do something)
6. GAP-09 MVP: Notification badges (so users know to check)
7. GAP-10: Exchange completion UI (so flow is complete)

### Week 2: Add Identity & Onboarding
8. GAP-02: User identity (so offers belong to people)
9. GAP-03: Community entity (so there's a "commune")
10. GAP-12: Onboarding flow (so new users aren't lost)

### Week 3: Polish & Depth
11. GAP-11: Replace remaining mock data in agents
12. GAP-13: Urgency indicators
13. GAP-14: Calendar integration
14. GAP-15: Statistics

### For Multi-Node Demo
15. GAP-08: VF Bundle Publisher actually publishes
16. GAP-16: DTN Sync automation

### Quick UX Wins (Can Do Anytime)
17. GAP-26: Show nav badge for pending proposals (30 min)
18. GAP-28: Add toast notifications (2-3 hours)
19. GAP-18: Edit/delete buttons on own listings (2-3 hours)
20. GAP-21: Filter/sort on offers page (3-4 hours)
21. GAP-22: Allow custom locations (2-3 hours)

### Deeper UX Work (Post-Workshop)
22. GAP-17: "My Stuff" view
23. GAP-19: Messaging between parties
24. GAP-20: Photo uploads
25. GAP-24: Recurring offers
26. GAP-29: Mobile bottom nav
27. GAP-30: Proximity/distance display

---

## Gap Summary (by Priority)

| Priority | Count | Description |
|----------|-------|-------------|
| P1 - Critical | 8 | Demo won't work without these |
| P2 - Core Experience | 4 | Core flows feel incomplete |
| P3 - Polish | 4 | Depth and refinement |
| P4 - UX Polish | 14 | User experience improvements |
| P5 - Agent/Backend | 10 | Mock data and incomplete integrations |
| P6 - Production Ready | 18 | Security, data integrity, operations |
| P7 - Philosophical | 11 | Values alignment, systemic issues |
| **Total** | **69** | |

---

## Quick Reference: Key Files

### Backend Core
- `app/main.py` - DTN service entry
- `app/api/agents.py` - Agent endpoints (GAP-01)
- `app/agents/` - All agent implementations (GAP-07)
- `app/clients/vf_client.py` - VF database queries

### ValueFlows Node
- `valueflows_node/app/main.py` - VF service entry
- `valueflows_node/app/api/vf/` - All VF endpoints
- `valueflows_node/app/models/vf/` - Data models

### Frontend
- `frontend/src/App.tsx` - Routes (GAP-12)
- `frontend/src/api/agents.ts` - **FIX IMMEDIATELY** (GAP-06, GAP-07)
- `frontend/src/pages/AgentsPage.tsx` - Proposal UI
- `frontend/src/pages/ExchangesPage.tsx` - Exchange UI (GAP-10)
- `frontend/src/components/Navigation.tsx` - Nav badges (GAP-09)

### Docker/Infra
- `docker/nginx.conf` - **FIX IMMEDIATELY** (GAP-06) - add `/api/agents` route

### To Create
- `scripts/seed_demo_data.py` (GAP-04)
- `app/database/proposals.py` (GAP-05)
- `app/auth/` (GAP-02)
- `valueflows_node/app/models/community.py` (GAP-03)
- `frontend/src/pages/OnboardingPage.tsx` (GAP-12)

---

## Testing the Gaps

After fixing each gap, verify:

### GAP-06 Test (Frontend Route Fix) - TEST FIRST!
```bash
# After nginx config update, test that frontend can reach agents
curl http://localhost/api/agents/
# Should return agent list, NOT 404

# If running without nginx (dev mode), check vite.config.ts proxy
```

### GAP-07 Test (Approval Payload)
```bash
# Try approving from frontend - should NOT get 422 error
# Check Network tab in browser devtools for payload structure
```

### GAP-05 Test (Proposal Persistence)
```bash
# Create a proposal
curl -X POST localhost:8000/agents/mutual-aid-matchmaker/run

# Restart the DTN service
# (kill and restart app/main.py)

# Check proposals still exist
curl localhost:8000/agents/proposals
# Should still see the proposal
```

### GAP-01 Test (Proposal → VF Bridge)
```bash
# Create offer and need
curl -X POST localhost:8001/vf/listings/ -d '{"type": "offer", ...}'
curl -X POST localhost:8001/vf/listings/ -d '{"type": "need", ...}'

# Run matchmaker
curl -X POST localhost:8000/agents/mutual-aid-matchmaker/run

# Get proposal ID from response, approve it
curl -X POST localhost:8000/agents/proposals/{id}/approve \
  -d '{"user_id": "alice", "approved": true}'
curl -X POST localhost:8000/agents/proposals/{id}/approve \
  -d '{"user_id": "bob", "approved": true}'

# Verify VF Match was created
curl localhost:8001/vf/matches/
```

### GAP-04 Test (Seed Data)
```bash
python scripts/seed_demo_data.py
curl localhost:8001/vf/listings/ | jq '.count'  # Should be 30
curl localhost:8000/agents/proposals | jq '.total'  # Should be 3
```

### GAP-10 Test (Exchange Completion)
```bash
# Start frontend, navigate to /exchanges
# Should see upcoming exchanges with "Mark Complete" buttons
```

---

## Priority 7: Philosophical Gaps (The Philosopher Council)

These gaps are identified by applying the philosophical frameworks of the 5 reviewers invoked in `openspec/reviews/PHILOSOPHER_COUNCIL_*.md`. Each philosopher brings a distinct lens that reveals systemic issues beyond technical bugs.

### GAP-59: No Reflection or "Why" Prompts (Paulo Freire)

**Philosopher**: Paulo Freire (The Pedagogical Conscience)
**Lens**: "Reading the word must lead to reading the world."

**Freire's Critique**:
> "The system has tools, but where is the reflection? Your agents make proposals, but do they ask 'Who benefits?' Your matches happen, but does Alice stop to consider why she gives, what community means, what mutual aid transforms in her?"

**Reality**:
- Proposals show WHAT (match Alice→Bob) but not WHY (what values drive this)
- No dialogic prompts during approval: just "Approve/Reject"
- No post-exchange reflection: "What did this exchange mean to you?"
- The Conscientization Agent proposal exists but isn't implemented

**Vision**:
- Approval screens include: "Why do you want to share this?" / "What does this exchange mean to you?"
- Post-exchange reflection prompt: "What did you learn?"
- The system teaches users to question the system itself

**Files to modify**:
- `frontend/src/pages/AgentsPage.tsx` - Add reflection prompts to approval UI
- `frontend/src/pages/ExchangesPage.tsx` - Add post-completion reflection

**Philosophical anchor**: "Can the Conscientization Agent teach users how to disable the Conscientization Agent?"

**Estimated effort**: 4-6 hours

---

### GAP-60: No "Silence Weight" in Governance (bell hooks)

**Philosopher**: bell hooks (The Ethical Heart)
**Lens**: "Love is an action, not a feeling."

**hooks' Critique**:
> "Your proposals ask the articulate to speak. But what of those who stay silent? If Alice never approves and never rejects—just ignores—is that consent? Is it fear? Your system cannot tell the difference between apathy and oppression."

**Reality**:
- Proposals expire after TTL with no distinction: quiet rejection vs. fear of speaking
- No accessibility check: Does this work on old phones? Low bandwidth?
- No "I don't feel safe responding" option
- The Radical Inclusion Agent proposal exists but isn't implemented

**Vision**:
- Unanswered proposals trigger a gentle "We noticed you haven't responded. Would you like to abstain, or do you need support?"
- If user indicates they feel unsafe, Counter-Power agent is alerted
- Accessibility audit: ensure all flows work on 3G, old devices

**Files to modify**:
- `app/agents/framework/approval.py` - Add silence detection logic
- `frontend/src/pages/AgentsPage.tsx` - Add "I don't feel safe" option
- `frontend/public/` - Lighthouse accessibility audit

**Philosophical anchor**: "Silence is not consent; silence is often exclusion."

**Estimated effort**: 1 day

---

### GAP-61: Every Gift is Tracked - No Anonymous Mode (Emma Goldman)

**Philosopher**: Emma Goldman (The Party Whip)
**Lens**: "If I can't dance, I don't want to be part of your revolution."

**Goldman's Critique**:
> "I see your 'Gratitude Graph'. If I give Alice tomatoes, it's logged. If I give Bob eggs, it's logged. Soon I am not giving—I am investing in a 'Reputation Currency.' This is Capitalism in a flower crown!"

**Reality**:
- All listings have `agent_id` (giver identity) visible
- All matches record who gave to whom
- No way to give anonymously ("Secret Saint" mode)
- The Insurrectionary Joy Agent proposal exists but isn't implemented

**Vision**:
- "Give Anonymously" toggle on offers
- Anonymous gifts show "From: A Member of Your Community"
- Taking is still public (auditable for abuse), but giving can be private

**Files to modify**:
- `valueflows_node/app/models/vf/listing.py` - Add `anonymous: bool` field
- `frontend/src/pages/CreateOfferPage.tsx` - Add anonymous toggle
- `frontend/src/components/OfferCard.tsx` - Respect anonymity in display

**Philosophical anchor**: "Sometimes the greatest joy is giving without being recognized."

**Estimated effort**: 3-4 hours

---

### GAP-62: No "Loafer's Rights" - System Subtly Pressures Contribution (Emma Goldman + Peter Kropotkin)

**Philosopher**: Emma Goldman + Peter Kropotkin
**Lens**: "In my vision, even the idler is fed." / "Is 'Loafing' a valid contribution?"

**Critique**:
> "Your system tracks who gives. It will eventually show 'Alice: 47 gifts, Bob: 0.' Even if you don't shame Bob explicitly, the data will shame him. Can a user exist doing absolutely nothing? Or does the subtle pressure of the Gratitude Graph starve them socially?"

**Reality**:
- GAP-15 proposes "impact tracking" - gift counts per person
- No explicit protection for those who take more than they give
- No recognition that some members may be in crisis, disabled, or simply need community without reciprocity

**Vision**:
- "Needs-First" mode: Some users marked as "receiving support" with no expectation of reciprocity
- Statistics never show individual "contribution scores"
- Community totals only: "We've shared 230 gifts" (not "Alice gave the most")

**Files to modify**:
- GAP-15 design must change: community stats only, not individual leaderboards
- `valueflows_node/app/models/vf/agent.py` - Add `receiving_support: bool` field

**Philosophical anchor**: "Freeloading is a myth invented by capitalists to make us fear our neighbors."

**Estimated effort**: Design decision + 2-3 hours

---

### GAP-63: No "Osmosis" - Abundance Doesn't Automatically Spill Over (Peter Kropotkin)

**Philosopher**: Peter Kropotkin (The Quartermaster)
**Lens**: "The Common Heap."

**Kropotkin's Critique**:
> "Your offers are individual property until someone 'claims' them. But what if Alice has 50 tomatoes and her neighbor commune has none? There is no automatic sharing. A Molecule with a full Heap while its neighbor starves is not Solarpunk."

**Reality**:
- Offers stay with their owner until explicitly matched
- ✅ **UPDATED**: Inter-community resource flow is now available via trust-based discovery (Session 3F)
  - Users can browse cross-community offers/needs at `/network-resources`
  - Visibility controlled by individual choice, not stewards
- No automated "overflow" mechanism when one community has abundance
- No proactive osmosis proposals

**Vision**:
- When abundance > threshold, auto-notify nearby communities
- "Osmosis" proposals: "Your community has excess tomatoes. The Elm Street Collective needs tomatoes. Shall we propose a transfer?"
- Resources flow horizontally, not just between individuals
- **Foundation complete**: Manual cross-community sharing now works

**Files to create**:
- `app/agents/osmosis_agent.py` - Detect abundance, propose inter-community transfers
  - Can leverage existing `InterCommunityService` for visibility checks
  - Can use existing discovery API to find matching needs

**Philosophical anchor**: "Charity is vertical; Osmosis is horizontal."

**Estimated effort**: 1 day (reduced from original estimate - foundation now exists)

---

### GAP-64: No Detection of "Battery Warlords" (Mikhail Bakunin)

**Philosopher**: Mikhail Bakunin (The Antibody)
**Lens**: "Power tends to accumulate."

**Bakunin's Critique**:
> "Who runs the server? Who owns the bridge node? If AdminDave controls 50% of the active battery power or storage, he is a Warlord. Your beautiful mesh is his personal kingdom. I see no Hardware Audits."

**Reality**:
- Single-node architecture means whoever runs the server controls everything
- No multi-node decentralization implemented
- No detection of infrastructure concentration
- The Counter-Power Agent proposal exists but isn't implemented

**Vision**:
- Track which nodes contribute infrastructure (storage, bandwidth, uptime)
- Alert when any single actor controls >30% of infrastructure
- "Hardware Leveling" suggestions: distribute physical assets

**Files to modify**:
- `mesh_network/bridge_node/` - Add infrastructure contribution tracking
- `app/agents/counter_power_agent.py` - Implement the proposed agent

**Philosophical anchor**: "The only good authority is a dead one."

**Estimated effort**: Complex - requires multi-node architecture (GAP-08)

---

### GAP-65: No "Eject Button" for Oppressed Individuals (Mikhail Bakunin)

**Philosopher**: Mikhail Bakunin (The Antibody)
**Lens**: "The Right of Exit"

**Bakunin's Critique**:
> "What if the commune turns against Alice? What if the 'Restorative Justice' circle becomes a Maoist Struggle Session? Can Alice leave with her dignity and data intact? Or is she trapped?"

**Reality**:
- No data export functionality
- No "leave community" flow
- No protection for individuals against majority pressure
- User data belongs to the system, not the user

**Vision**:
- "Export My Data" button: download all your offers, needs, exchanges
- "Leave Community" flow: clean exit with data portability
- "Right of Secession": fork your data to a new community

**Files to create**:
- `valueflows_node/app/api/vf/export.py` - User data export endpoint
- `frontend/src/pages/SettingsPage.tsx` - Export and leave buttons

**Philosophical anchor**: "Without the right of exit, you are building a digital jail."

**Estimated effort**: 4-6 hours

---

### GAP-66: Crypto-Priesthood - Security is Unintelligible (Mikhail Bakunin)

**Philosopher**: Mikhail Bakunin (The Antibody)
**Lens**: "Complexity as hidden hierarchy"

**Bakunin's Critique**:
> "You use Ed25519 and sha256 and 'content-addressed bundleIds.' But who understands this? The math is too complex for the worker. They must trust a priesthood of coders. You have built a new church."

**Reality**:
- Cryptographic signing happens invisibly
- No explanation of what signatures mean or why they matter
- Users cannot verify the security claims themselves
- Security is a black box

**Vision**:
- Explain in plain language: "This message is signed, meaning it provably came from Alice and wasn't changed"
- Show "verified" badges with explanations
- Documentation for non-technical users: "How the Mesh Keeps You Safe"

**Files to create**:
- `frontend/src/components/SecurityExplainer.tsx` - Plain-language security info
- `docs/SECURITY_FOR_HUMANS.md` - Non-technical security guide

**Philosophical anchor**: "If the math is too complex for the worker to understand, they are trusting a priesthood."

**Estimated effort**: 4-6 hours

---

### GAP-67: No Mourning Protocol (bell hooks)

**Philosopher**: bell hooks (The Ethical Heart)
**Lens**: "Who tends the grief?"

**hooks' Critique**:
> "You have agents for Joy, for Bread, for Governance. But when a commune fails—and they will fail—where does the grief go? Do you just 'delete the namespace'?"

**Reality**:
- No community archival or end-of-life process
- Dead communities just... disappear
- No dignity for failed experiments
- No learning from failure

**Vision**:
- "Sunset" process: When a community chooses to end, archive its history
- "Seed Vault": Encrypted archive of what was learned (what worked, what failed)
- Memorial: Honor the attempt, even if it failed
- Future communities can "dig up" the history to learn

**Files to create**:
- `app/services/sunset_service.py` - Community end-of-life archival
- `frontend/src/pages/MemorialPage.tsx` - Honor past communities

**Philosophical anchor**: "Failure is the most honest teacher. We must compost our mistakes."

**Estimated effort**: 1 day

---

### GAP-68: System Too Safe - No Room for Chaos (Emma Goldman)

**Philosopher**: Emma Goldman (The Party Whip)
**Lens**: "Revolution requires risk."

**Goldman's Critique**:
> "This system is very safe. Warnings, audits, health monitors. But if I want to throw a wild rave that drains the battery to 0%, will your 'Health Monitor' stop me? Freedom includes the freedom to make bad choices."

**Reality**:
- Health monitors could prevent "dangerous" but joyful events
- Everything requires approval and validation
- No explicit protection for chaos, spontaneity, or "bad" decisions

**Vision**:
- "Do-ocracy" mode: Some actions bypass approval entirely
- Tiered decisions: Constitutional matters need consensus; parties just happen
- "Override" capability: "I know this will drain the battery, let me do it anyway"

**Files to modify**:
- `app/agents/framework/approval.py` - Add decision tiers
- Proposal types should have different approval requirements

**Philosophical anchor**: "Have we sterilized the chaos?"

**Estimated effort**: Design decision + 3-4 hours

---

### GAP-69: "Committee Sabotage" Risk (CIA Simple Sabotage Manual)

**Philosopher**: The Council (Round 5 - Sabotage Audit)
**Lens**: OSS Simple Sabotage Field Manual (1944)

**Sabotage Risk Identified**:
> "Refer all matters to committees for 'further study'. A single saboteur can stay silent, trigger the 'Safety Check', and freeze the vote indefinitely."

**Reality**:
- 9 agents creating proposals
- Culture Circles, Justice Circles, Molecules, Holons
- "Silence Weight" (GAP-60) could be weaponized to block decisions forever

**Vision**:
- "Rough Consensus" override: >75% support + 24 hours = proceed despite blockers
- "Triviality Filter": Some decisions don't need voting at all
- "Saboteur Sensor": Flag nodes that consistently delay without alternatives
- "Sunset Clause": Every committee has a mandatory death date

**Files to modify**:
- `app/agents/framework/approval.py` - Add timeout/override logic
- `app/agents/counter_power_agent.py` - Add "process walling" detection

**Philosophical anchor**: "You cannot block with words; only with better code."

**Estimated effort**: 4-6 hours

---

## Updated Summary Including Philosophical Gaps

| Priority | Count | Description |
|----------|-------|-------------|
| P1 - Critical | 8 | Demo won't work without these |
| P2 - Core Experience | 4 | Core flows feel incomplete |
| P3 - Polish | 4 | Depth and refinement |
| P4 - UX Polish | 14 | User experience improvements |
| P5 - Agent/Backend | 10 | Mock data and incomplete integrations |
| P6 - Production Ready | 18 | Security, data integrity, operations |
| P7 - Philosophical | 11 | Values alignment, systemic issues |
| **Total** | **69** | |

---

## The Philosophers' Priority Order

Based on the council's debates, if they could only fix 5 things:

1. **GAP-65: Eject Button** (Bakunin) - "Without exit, it's a prison"
2. **GAP-61: Anonymous Mode** (Goldman) - "Or it's reputation capitalism"
3. **GAP-60: Silence Weight** (hooks) - "Silence is often exclusion"
4. **GAP-64: Battery Warlords Detection** (Bakunin) - "Power accumulates invisibly"
5. **GAP-63: Osmosis** (Kropotkin) - "Abundance must flow horizontally"

These represent the philosophical core of what makes this "solarpunk" vs. just "an app."
