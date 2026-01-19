# Day in the Life: Solarpunk Gift Economy Mesh Network

This document describes the intended user experience for commune members using the Solarpunk mesh network, maps each moment to implementation status, and identifies gaps.

---

## Cast of Characters

- **Alice** - Has a garden, often has surplus produce
- **Bob** - New to the commune, needs food while getting established
- **Carol** - Runs the community kitchen, coordinates batch cooking
- **Dave** - Permaculture expert, leads work parties
- **Eve** - Bridge node carrier, walks between Garden AP and Kitchen AP daily

---

## Morning: 7:00 AM - Alice Checks Her Garden

### The Experience

Alice wakes up and checks her phone. The Solarpunk app shows:

> **3 Notifications**
> - Your tomatoes (5 lbs) expire in 36 hours - tap to see suggestions
> - Work Party tomorrow: Spring Planting needs 2 more people
> - Match found: Bob needs vegetables, you have tomatoes nearby

She taps the tomato notification. The Perishables Dispatcher has already analyzed her inventory and shows:

> **Urgent: Tomatoes expiring soon**
>
> The AI suggests:
> 1. **Match with Bob** - He posted need for vegetables yesterday (0.3 miles away)
> 2. **Batch cooking** - Carol is hosting sauce-making at Community Kitchen (2pm today)
>
> [Approve Match] [Join Batch Cooking] [Dismiss]

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Listing expiration tracking | ✅ Implemented | `valueflows_node/app/models/vf/listing.py` - `available_until` field |
| Perishables Dispatcher agent | ✅ Implemented | `app/agents/perishables_dispatcher.py` |
| Urgency tiers (critical/high/medium) | ✅ Implemented | `perishables_dispatcher.py:64-75` |
| Agent scheduler (automatic runs) | 🔄 In Progress | Being built now |
| Notification system | ❌ Missing | No push notifications, no in-app alerts |
| "Suggestions" UI for expiring items | ❌ Missing | Frontend shows offers but not urgency suggestions |
| Match-from-perishables flow | ⚠️ Partial | Agent creates proposal, but no notification to Alice |

### Gap Analysis

The agent logic exists and is sophisticated (`_propose_critical_action`, `_propose_urgent_exchange`), but:
1. Alice never sees the proposal unless she manually visits `/agents` page
2. No urgency indicators in the offers list
3. No "approve from notification" flow

---

## Morning: 8:00 AM - Bob Posts a Need

### The Experience

Bob is new and needs food. He opens the app and taps "Express a Need":

> **What do you need?**
> Category: [Food > Vegetables]
> Description: "Fresh vegetables for the week"
> Quantity: ~5 lbs
> Needed by: [This week]
> Location: [My place - Cottage 7]
>
> [Post Need]

After posting, Bob sees:

> **Need posted!**
>
> The network is searching for matches. We'll notify you when something's found.
>
> **Tip:** 3 people nearby have offered vegetables this week.

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Need creation UI | ✅ Implemented | `frontend/src/pages/CreateNeedPage.tsx` |
| Need storage in VF | ✅ Implemented | `valueflows_node/app/api/vf/listings.py` |
| Need published as DTN bundle | ✅ Implemented | `valueflows_node/app/services/vf_bundle_publisher.py` |
| "Nearby offers" suggestion | ❌ Missing | No query on need creation |
| Automatic match notification | ❌ Missing | Matchmaker runs, but Bob isn't notified |

### Gap Analysis

Bob can post a need successfully. The data flows correctly through VF → DTN bundle. But:
1. No immediate feedback about potential matches
2. No notification when Matchmaker finds Alice's tomatoes
3. Bob would have to manually check the Agents page or hope Alice checks hers

---

## Morning: 9:00 AM - Matchmaker Agent Runs

### The Experience (What Should Happen)

The Matchmaker runs automatically and analyzes:
- Alice's tomatoes (offer, expires in 36h, location: Garden plot)
- Bob's need for vegetables (need, this week, location: Cottage 7)

It calculates:
- Category match: 100% (vegetables)
- Location proximity: 0.3 miles = 0.8 score
- Time overlap: Alice's window includes Bob's deadline = 1.0 score
- Quantity fit: 5 lbs offered, ~5 lbs needed = 1.0 score
- **Total score: 0.94**

Creates proposal:
> **Match Proposal**
>
> Alice has 5 lbs tomatoes available for 2 days.
> Bob needs vegetables for this week.
> Both are near Garden Plot and Cottage 7.
>
> Suggested handoff: Tomorrow morning (9-10am)
> Suggested location: Garden Plot
>
> Requires approval from: Alice, Bob

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Matchmaker analysis logic | ✅ Implemented | `app/agents/mutual_aid_matchmaker.py` |
| Multi-criteria scoring | ✅ Implemented | `mutual_aid_matchmaker.py:137-177` |
| Category matching (exact + parent) | ✅ Implemented | `mutual_aid_matchmaker.py:179-203` |
| Location proximity scoring | ✅ Implemented | `mutual_aid_matchmaker.py:205-227` |
| Time overlap scoring | ✅ Implemented | `mutual_aid_matchmaker.py:229-249` |
| Quantity fit scoring | ✅ Implemented | `mutual_aid_matchmaker.py:251-273` |
| Proposal creation | ✅ Implemented | `mutual_aid_matchmaker.py:275-327` |
| Query VF for active offers | ✅ Implemented | `app/clients/vf_client.py:72-139` |
| Query VF for active needs | ✅ Implemented | `app/clients/vf_client.py:141-207` |
| Scheduler triggers agent | 🔄 In Progress | Being built now |
| Notify Alice of proposal | ❌ Missing | No notification system |
| Notify Bob of proposal | ❌ Missing | No notification system |

### Gap Analysis

The Matchmaker is actually quite sophisticated. The scoring algorithm is real and functional. But:
1. Currently only runs on manual API call (`POST /agents/mutual-aid-matchmaker/run`)
2. Scheduler being added will fix automatic runs
3. **Critical gap**: No notification to Alice or Bob that a match was found

---

## Mid-Morning: 10:00 AM - Alice Reviews Proposal

### The Experience (What Should Happen)

Alice gets a notification (or checks the app) and sees:

> **New Match Proposal**
>
> The Mutual Aid Matchmaker found a match for your tomatoes!
>
> **Bob** needs vegetables (0.3 miles from you)
>
> Suggested: Meet at Garden Plot tomorrow 9-10am
>
> [View Details] [Approve] [Suggest Different Time]

Alice approves. The system shows:

> **Waiting for Bob's approval**
>
> We'll notify you when Bob confirms. You can also message Bob directly.

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Proposal storage | ✅ Implemented | `app/agents/framework/approval.py` |
| Proposal listing API | ✅ Implemented | `app/api/agents.py:73-97` |
| Proposal detail API | ✅ Implemented | `app/api/agents.py:115-127` |
| Approval API | ✅ Implemented | `app/api/agents.py:130-152` |
| Multi-party approval tracking | ✅ Implemented | `app/agents/framework/approval.py` |
| Frontend proposal display | ✅ Implemented | `frontend/src/pages/AgentsPage.tsx` |
| Frontend approval buttons | ✅ Implemented | `frontend/src/components/ProposalCard.tsx` |
| Pending proposals on homepage | ✅ Implemented | `frontend/src/pages/HomePage.tsx:127-147` |
| Notification that proposal exists | ❌ Missing | Alice must manually check |
| "Waiting for other party" status | ⚠️ Partial | Status exists but no active notification |
| Direct messaging | ❌ Missing | No chat/messaging system |

### Gap Analysis

The approval infrastructure is solid. Alice CAN approve if she knows to look. Missing:
1. Push/notification to tell her there's something to approve
2. In-app messaging to coordinate details
3. "Suggest different time" alternative flow

---

## Late Morning: 11:00 AM - Bob Approves

### The Experience (What Should Happen)

Bob sees the same proposal and approves. The system:

1. Creates a VF **Match** object (both parties approved)
2. Creates a VF **Exchange** object with the agreed terms
3. Notifies both parties:

> **Match Confirmed!**
>
> You and Alice agreed to exchange:
> - Alice provides: 5 lbs tomatoes
> - Meeting: Tomorrow, 9-10am at Garden Plot
>
> [Add to Calendar] [Message Alice] [Get Directions]

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Agent proposal approval | ✅ Implemented | `app/api/agents.py:130-152` |
| VF Match creation | ✅ Implemented | `valueflows_node/app/api/vf/matches.py:15-41` |
| VF Match approval (provider/receiver) | ✅ Implemented | `valueflows_node/app/api/vf/matches.py:44-85` |
| VF Exchange creation | ✅ Implemented | `valueflows_node/app/api/vf/exchanges.py:15-41` |
| **Connect agent approval → VF Match** | ❌ Missing | Approving agent proposal doesn't create VF objects |
| Calendar export (ICS) | ❌ Missing | No calendar integration |
| Directions/map | ❌ Missing | No location services integration |
| Message other party | ❌ Missing | No messaging |
| Confirmation notification | ❌ Missing | No notification system |

### Gap Analysis

**This is the critical missing link.** The agent creates proposals, users can approve them, but:
- Approving an agent proposal doesn't automatically create the VF Match
- No bridge between "agent proposal approved" → "VF Exchange created"
- The approval is essentially just a vote that goes nowhere

**What needs to happen:**
```
Agent Proposal Approved (both parties)
         ↓
Create VF Match (status: accepted)
         ↓
Create VF Exchange (status: scheduled)
         ↓
Notify both parties
         ↓
Add to their upcoming exchanges
```

---

## Afternoon: 2:00 PM - Carol's Batch Cooking

### The Experience (What Should Happen)

Carol runs the Community Kitchen. The Perishables Dispatcher noticed several people have expiring produce and proposed a batch cooking event:

> **Batch Cooking Proposal**
>
> 3 community members have produce expiring in the next 48 hours:
> - Alice: 5 lbs tomatoes
> - Frank: 3 lbs peppers
> - Grace: 2 lbs onions
>
> Suggesting: Sauce-making session at Community Kitchen
> Time: Today 2:00 PM
> Output: ~8 jars tomato sauce (shared among contributors)
>
> [Approve as Host] [Suggest Different Time]

Carol approves as host. Alice, Frank, and Grace get notifications to bring their produce.

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Batch cooking proposal type | ✅ Implemented | `app/agents/framework/proposal.py` - `ProposalType.BATCH_COOKING` |
| Perishables → batch cooking logic | ✅ Implemented | `perishables_dispatcher.py:107-163` |
| `_is_cookable()` check | ✅ Implemented | `perishables_dispatcher.py:303-310` |
| Multiple-contributor aggregation | ❌ Missing | Agent only looks at single items, not aggregating across people |
| Host role / venue coordination | ❌ Missing | No concept of "Carol hosts at Kitchen" |
| Output tracking (jars produced) | ❌ Missing | No VF Process → output flow |
| Notification to contributors | ❌ Missing | No notification system |

### Gap Analysis

The agent has the concept of batch cooking but it's per-item, not community-aggregated. Missing:
1. Aggregate expiring items across multiple people
2. Suggest venue + host
3. Track the Process (inputs → cooking → outputs)
4. Distribute outputs fairly

---

## Afternoon: 4:00 PM - Work Party Planning

### The Experience (What Should Happen)

Dave is planning the spring planting. The Work Party Scheduler has analyzed:
- The Plan: "Spring Planting 2025" with processes needing work
- Participant availability (from their calendars/commitments)
- Skills needed vs. skills available

It proposes:

> **Work Party: Spring Planting**
>
> Date: Saturday, December 21 at 9:00 AM
> Location: Community Garden - South Plot
> Duration: ~4 hours
>
> **5 participants available:**
> - Alice (gardening, permaculture)
> - Bob (gardening, digging)
> - Carol (gardening)
> - Dave (permaculture, landscaping)
> - Eve (gardening, digging)
>
> **Skill coverage: 100%** - All required skills covered
>
> **Resources needed:**
> - Trees (confirmed available)
> - Compost (confirmed available)
> - Tools (need to reserve)
> - Water (on-site)
>
> Weather: Mild temps, no rain expected
>
> [Approve] [Suggest Different Date] [I Can't Make It]

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Work Party proposal type | ✅ Implemented | `app/agents/framework/proposal.py` - `ProposalType.WORK_PARTY` |
| Work Party Scheduler agent | ✅ Implemented | `app/agents/work_party_scheduler.py` |
| Find best time slot | ✅ Implemented | `work_party_scheduler.py:294-319` |
| Skill coverage analysis | ✅ Implemented | `work_party_scheduler.py:321-362` |
| Weather note (placeholder) | ⚠️ Stub | `work_party_scheduler.py:364-382` - returns mock data |
| Query actual VF Plans | ❌ Missing | `work_party_scheduler.py:75-131` returns mock data |
| Query actual participant availability | ❌ Missing | `work_party_scheduler.py:141-198` returns mock data |
| Resource availability check | ❌ Missing | Just lists resources, doesn't check inventory |
| Multi-participant approval | ⚠️ Partial | `requires_approval` set but flow not tested |
| Calendar integration | ❌ Missing | No ICS export, no calendar sync |
| "I can't make it" response | ❌ Missing | No decline/reschedule flow |

### Gap Analysis

The scheduling algorithm is well-designed but operates on mock data:
1. `_get_active_plans()` returns hardcoded plans, not VF queries
2. `_get_available_participants()` returns hardcoded availability
3. No actual VF Plan/Commitment objects being created or queried
4. Weather integration is a stub

---

## Evening: 6:00 PM - Eve Bridges the Network

### The Experience (What Should Happen)

Eve walks from the Garden AP area to the Kitchen AP area. Her phone:

1. **At Garden AP**: Syncs all new bundles (Alice's tomato offer, Bob's need, the Match proposal)
2. **Walking**: Carries bundles in local cache
3. **At Kitchen AP**: Pushes bundles, receives Kitchen area bundles

The DTN system handles this automatically. Eve might see:

> **Bridge Sync Complete**
>
> ↑ Uploaded: 12 bundles (offers, needs, indexes)
> ↓ Downloaded: 8 bundles (Kitchen area updates)
>
> Network health: Good (last sync 2 hours ago)

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| DTN Bundle format | ✅ Implemented | `app/models/bundle.py` |
| Bundle queues (inbox/outbox/pending) | ✅ Implemented | `app/models/queue.py` |
| Sync index endpoint | ✅ Implemented | `app/api/sync.py` |
| Push bundles endpoint | ✅ Implemented | `app/api/sync.py` |
| Pull bundles endpoint | ✅ Implemented | `app/api/sync.py` |
| TTL enforcement | ✅ Implemented | `app/services/ttl_service.py` |
| Priority-based forwarding | ✅ Implemented | `app/services/forwarding_service.py` |
| Cache budget management | ✅ Implemented | `app/services/cache_service.py` |
| Bridge node service | ✅ Implemented | `mesh_network/bridge_node/` |
| Sync orchestrator | ✅ Implemented | `mesh_network/bridge_node/services/sync_orchestrator.py` |
| Automatic sync on network change | ❌ Missing | Must manually trigger sync |
| Bridge UI showing sync status | ⚠️ Partial | `NetworkPage.tsx` exists but limited |
| "Walk route" optimization | ❌ Missing | No suggestion of which areas need syncing |

### Gap Analysis

The DTN infrastructure is solid and well-implemented. Missing pieces for UX:
1. Auto-detect network change and sync
2. Background service on phone (would need Android app)
3. Visual indication of what data is being carried
4. "You're carrying urgent bundles" alerts

---

## Next Morning: The Exchange Happens

### The Experience (What Should Happen)

Alice and Bob meet at the Garden Plot at 9 AM. Alice hands over the tomatoes. Both open their phones:

> **Complete Exchange?**
>
> Exchange: Tomatoes (Alice → Bob)
>
> [I Gave the Items] (Alice)
> [I Received the Items] (Bob)

Both confirm. The system:
1. Creates VF **Event** objects (transfer-give, transfer-receive)
2. Updates Alice's inventory (tomatoes removed)
3. Updates the Exchange status to "completed"
4. Thanks both parties

> **Exchange Complete!**
>
> Thank you for participating in the gift economy.
>
> Alice has shared 47 items this year.
> Bob has received 3 items as a new member.
>
> [Share Feedback] [Back to Home]

### Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Exchange completion endpoint | ✅ Implemented | `valueflows_node/app/api/vf/exchanges.py:62-103` |
| Dual-party completion tracking | ✅ Implemented | `exchange.provider_completed`, `exchange.receiver_completed` |
| VF Event creation | ✅ Implemented | `valueflows_node/app/api/vf/events.py` |
| Bundle publishing on completion | ✅ Implemented | `exchanges.py:91` |
| Inventory update on exchange | ❌ Missing | No automatic resource instance update |
| User statistics tracking | ❌ Missing | No "Alice has shared X items" |
| Feedback/rating system | ❌ Missing | No reputation or feedback |
| Completion UI | ❌ Missing | Frontend doesn't have exchange completion flow |

### Gap Analysis

The backend has exchange completion, but:
1. No frontend UI to complete exchanges
2. Inventory not automatically adjusted
3. No statistics or community impact tracking

---

## Summary: Implementation Completeness by Flow

| Flow | Backend | Frontend | Notifications | End-to-End |
|------|---------|----------|---------------|------------|
| Post Offer | ✅ | ✅ | N/A | ✅ Works |
| Post Need | ✅ | ✅ | N/A | ✅ Works |
| Agent Analysis | ✅ | N/A | N/A | ⚠️ Needs scheduler |
| Proposal Creation | ✅ | ✅ View | ❌ | ⚠️ Manual discovery |
| Proposal Approval | ✅ | ✅ | ❌ | ⚠️ Doesn't create VF objects |
| Match → Exchange | ✅ Separate | ❌ | ❌ | ❌ Not connected |
| Exchange Completion | ✅ | ❌ | ❌ | ❌ No UI |
| DTN Sync | ✅ | ⚠️ Basic | N/A | ⚠️ Manual trigger |
| Work Party Scheduling | ⚠️ Mock data | ✅ View | ❌ | ❌ No real data |
| Batch Cooking | ⚠️ Single-item | ❌ | ❌ | ❌ Limited |

---

## Critical Path to "Working Demo"

### Must Have (Demo won't work without these)

1. **Agent Scheduler** (🔄 in progress)
   - Run agents on configurable interval
   - Location: New service in `app/`

2. **Proposal Approval → VF Objects Bridge**
   - When agent proposal approved → create VF Match + Exchange
   - Location: `app/api/agents.py` - extend `approve_proposal`
   - ~50-100 lines of code

3. **Seed Data Script**
   - Create realistic commune: 10 people, 30 offers/needs, 5 locations
   - Location: `scripts/seed_demo_data.py`
   - Essential for workshop

### Should Have (Makes demo compelling)

4. **Simple Notification System**
   - Even just polling-based "you have N pending proposals"
   - Frontend badge on Agents nav item
   - ~2-3 hours work

5. **Exchange Completion UI**
   - Page showing upcoming exchanges
   - "Mark as complete" buttons
   - Location: `frontend/src/pages/ExchangesPage.tsx`

6. **Replace Mock Data in Agents**
   - `work_party_scheduler.py` - query real VF Plans
   - `perishables_dispatcher.py:288-301` - query real needs
   - ~2-4 hours per agent

### Nice to Have (Polish)

7. **Urgency indicators in UI**
   - Red/yellow badges on expiring offers
   - "Urgent" tag on perishables proposals

8. **Calendar export (ICS)**
   - Download work party as calendar event

9. **Statistics dashboard**
   - Community impact metrics
   - "X items shared this week"

---

## File Reference Quick Guide

### Where Things Live

**Agents:**
- Framework: `app/agents/framework/`
- Implementations: `app/agents/*.py`
- API: `app/api/agents.py`

**ValueFlows:**
- Models: `valueflows_node/app/models/vf/`
- Repositories: `valueflows_node/app/repositories/vf/`
- API: `valueflows_node/app/api/vf/`

**DTN:**
- Models: `app/models/`
- Services: `app/services/`
- API: `app/api/bundles.py`, `app/api/sync.py`

**Frontend:**
- Pages: `frontend/src/pages/`
- Components: `frontend/src/components/`
- API hooks: `frontend/src/hooks/`

---

## Questions to Resolve

1. **Notification strategy**: Push (needs infrastructure) vs. polling (simpler) vs. NATS websocket (middle ground)?

2. **Identity**: How do Alice and Bob authenticate? Currently no user auth system.

3. **Multi-node demo**: Do we show mesh/DTN aspects or focus on single-node coordination?

4. **Phone deployment**: Termux? PWA? Native app? What's realistic for workshop?
