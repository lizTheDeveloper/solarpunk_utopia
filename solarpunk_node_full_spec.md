# Solarpunk Node Full Spec (Optimum-Case)
**Multi-AP Phone Mesh · DTN Store-and-Forward · On-Phone ValueFlows Node (VF-Full v1.0) · Agent-Led Commune OS**

This is the **full, optimum-case** specification for building a Solarpunk commune network on repurposed phones—Android-first—where:
- Phones form **multiple AP “islands”**
- **Everyone carries at least one bridge node**
- Data moves via **DTN bundles** with TTL, cache budgets, and speculative caching
- Phones can (optimum-case) do **multi-hop routing** (not just syncing)
- Every node can run a **ValueFlows-compatible local node** for offers/needs/inventory/plans
- AI agents help with **matching, scheduling, permaculture planning, and education**, with explicit guardrails

---

## 1. System Goals

### 1.1 What we are building
A **commune-scale “network commons”**: local-first coordination for:
- food sharing, pantry/tool/seed libraries
- mutual aid requests and offers
- work parties and seasonal planning
- education that maps directly onto tasks

### 1.2 Non-goals
- “Everyone carries the whole internet”
- cryptocurrencies, tokens, global ledgers
- always-online SaaS dependencies

---

## 2. Node Roles

All roles use the same software family; configuration differs.

### 2.1 Citizen Node (default)
- low storage + battery-first
- can publish and receive offers/needs
- can bridge opportunistically, but not required

### 2.2 Bridge Node (everyone should carry at least one)
- larger cache
- prioritized forwarding for time-sensitive bundles
- aggressive index sync + query response

### 2.3 AP Node (a few)
- runs Wi‑Fi AP on schedule / high uptime
- publishes indexes frequently
- optionally hosts local portal + search

### 2.4 Library Node (optional, can be phone)
- stores large knowledge bundles and serves chunks
- best solar powered, high uptime

---

## 3. Network Architecture: Multi-AP + DTN + (Optimum) Multi-hop

### 3.1 AP “Islands”
- Several Wi‑Fi APs exist simultaneously:
  - Garden AP
  - Kitchen AP
  - Workshop AP
  - Library AP
- Phones join whichever AP is nearby.
- Local services (portal, search) are reachable inside the current island.

### 3.2 Bridging between islands
Bridging happens via **store-and-forward DTN bundles**:
- Bridge nodes walk/bike/drive between islands
- They carry pending bundles and forward them on contact

This yields “mesh behavior” even if IP routing is imperfect.

### 3.3 Optimum-case multi-hop routing
You requested **phones do routing**, not routers. This is included as an optimum-case mode (with fallback).

---

## 4. DTN Bundle Layer (Core Transport)

### 4.1 Bundle format
All payloads move as **bundles**:

```json
{
  "bundleId": "b:sha256:...",
  "createdAt": "2025-12-17T10:00:00Z",
  "expiresAt": "2025-12-20T00:00:00Z",
  "priority": "normal",
  "audience": "local",
  "topic": "mutual-aid",
  "tags": ["food","perishable"],
  "payloadType": "vf:Listing",
  "payload": { "...": "..." },
  "hopLimit": 20,
  "receiptPolicy": "none",
  "signature": "sig:..."
}
```

### 4.2 Queues (required)
- `inbox`: received, unprocessed
- `outbox`: created locally, not yet forwarded
- `pending`: awaiting forwarding (may include duplicates)
- `delivered`: acknowledged delivery (optional)
- `expired`: dropped due to TTL
- `quarantine`: invalid signatures / policy violations

### 4.3 TTL defaults (recommended)
- emergency: 6–24 hours
- perishable food offers: 24–72 hours
- time-sensitive needs: 24–72 hours
- tool lending: 7–30 days
- skill offers: 30–90 days
- plans/processes: until end + 30 days
- protocols/lessons: 180–365 days
- indexes: 1–7 days

### 4.4 Cache budgets (required)
Each node has budgets:
- storage budget (MB/GB)
- bandwidth budget (per hour/day)
- battery budget profile (aggressive / balanced)

Bundles are dropped when:
- expired
- over hopLimit
- over budget and low priority

### 4.5 Speculative caching (required)
Nodes may store bundles they are not subscribed to if:
- high utility (emergency, perishables)
- high request rate (“hot” bundles)
- steward/lib role

---

## 5. Routing & Replication Policy

### 5.1 Forwarding rules (baseline)
1. never forward expired
2. forward emergency first
3. forward perishables and time-sensitive coordination next
4. forward trusted/private only to eligible peers
5. use remaining bandwidth for:
   - public posts
   - indexes
   - knowledge chunks

### 5.2 Audience and trust
- `public`: anyone may carry
- `local`: only within a defined community boundary (keyrings / AP domain)
- `trusted`: only nodes meeting trust threshold
- `private`: encrypted direct delivery only

Trust methods (choose one baseline):
- manual trust lists
- web-of-trust scoring
- steward-issued membership tokens (non-monetary, revocable)

---

## 6. Discovery and Search (Index bundles)

Because not everyone stores everything, discovery relies on **rolling indexes**.

### 6.1 Index bundle types
- `InventoryIndex`: what ResourceSpecs and Listings exist locally
- `ServiceIndex`: what skills/education are available
- `KnowledgeIndex`: what files/protocols/lessons exist (hashes)

Indexes:
- are small
- have short TTL
- are aggressively replicated

### 6.2 Queries
Nodes can broadcast query bundles:
- “need childcare within 7 days”
- “offer tomatoes within 3 days”
- “protocol compost”
Peers respond with:
- matching references (bundleIds)
- optional small previews
- where to fetch chunks (library nodes)

---

## 7. Files: Content Addressing + Chunking

### 7.1 Content addressing
- every file has `contentHash`
- metadata bundles reference hashes

### 7.2 Chunking
- split into 256KB–1MB chunks
- chunks are bundles with TTL and priority

### 7.3 Retrieval
Nodes fetch chunks:
- from nearby library nodes
- from speculative caches
- opportunistically via bridge nodes

---

## 8. Phones as Routers (Optimum-Case Multi-Hop)

You want multi-hop routing done by phones. This is difficult but spec’d.

### 8.1 Mode A (Optimum): Rooted Android + BATMAN-adv
**Requirements**
- LineageOS (rooted)
- kernel with batman-adv support (built-in or module)
- ability to create mesh interface (bat0)

**Behavior**
- nodes participate in a batman mesh
- assign addresses from `10.44.0.0/16`
- route traffic multi-hop over bat0

**Reality constraint**
Most phones struggle with AP + mesh simultaneously on one Wi‑Fi interface.
Optimum-case assumes one of:
- dual radio (USB Wi‑Fi via OTG)
- device supports concurrent AP + P2P in driver
- accept reduced reliability

### 8.2 Mode B: Wi‑Fi Direct multi-group bridging (Meshrabiya-style)
- no kernel modules
- device-dependent
- gives near-mesh behavior; may approximate multi-hop at app/virtual layer

### 8.3 Mode C (fallback): DTN-only
- no routed IP mesh across islands
- still full functionality via DTN bundles and indexes

**Hard requirement:** all core apps must work in Mode C.

---

## 9. ValueFlows Node Spec (VF-Full v1.0)

### 9.1 Objects (full)
**Agents**
- people, groups, places

**Locations**
- physical places with optional lat/lon

**ResourceSpec**
- categories/types (tomatoes, shovel, tutoring)

**ResourceInstance**
- trackable instances/batches (a specific shovel; a batch of tomatoes)

**Listing**
- offers and needs (UX primitive)

**Match**
- suggested/accepted pairing of offer+need

**Exchange**
- negotiated arrangement with constraints and window

**Event**
- handoff/work/delivery/harvest/class etc

**Process**
- transforms inputs→outputs (permaculture, cooking, repairs)

**Commitment**
- promises to do work/deliver/teach etc

**Plan**
- container of processes/commitments + dependencies (weekly/seasonal)

**Protocol**
- repeatable method (compost recipe)

**Lesson**
- microlearning tied to tasks

### 9.2 UX vs model
- UX stays simple: Offer/Need + category + quantity + where/when
- Backend stores the richer objects so agents can plan and audit

### 9.3 Signing and provenance
- Each object is signed by its authoring Agent.
- DTN bundles carry signatures; invalid signatures go to quarantine.

---

## 10. Agent Layer (Commune OS)

Agents emit **proposals**, not unilateral allocations (initially).

### 10.1 Required agents
1. **Commons Router Agent**
   - decides what this node caches/forwards given its role and budgets
2. **Mutual Aid Matchmaker**
   - proposes Matches/Exchanges
3. **Perishables Dispatcher**
   - prioritizes short-TTL food redistribution
4. **Scheduler / Work Party Agent**
   - proposes sessions and commitments
5. **Permaculture Seasonal Planner**
   - goals → seasonal plan → weekly processes
6. **Education Pathfinder**
   - recommends lessons/protocols tied to next work
7. **Inventory/Pantry Agent**
   - suggests replenishment, predicts shortages (opt-in)

### 10.2 Guardrails (non-negotiable)
- human ratification for allocations/commitments (configurable later)
- every proposal bundle includes:
  - explanation (short)
  - inputsUsed (bundleIds)
  - constraints (dietary/access/privacy)
- no surveillance requirement to participate

---

## 11. Software Manifest (Installable)

### 11.1 Base
- LineageOS (Android) + root (optimum-case)
- F-Droid
- Termux

### 11.2 Core apps
- Briar (secure messaging + forums)
- Manyverse (SSB) (social feed / bulletin)
- Syncthing (file distribution)
- Kiwix (offline knowledge)
- Organic Maps (offline maps)

### 11.3 Your components (to build)
- DTN bundle daemon (Android service)
- ValueFlows node (local store + API + UI)
- Index publisher and query responder
- Agent modules (proposal-only)

---

## 12. Deployment Presets (Config)

### 12.1 Citizen
- small cache (e.g., 256–1024MB)
- TTL enforcement strict
- forwards only public/local + time-sensitive

### 12.2 Bridge
- medium cache (e.g., 2–8GB)
- forwards perishables/emergency aggressively
- stores indexes and responds to queries

### 12.3 AP
- hotspot schedule
- high uptime settings
- publishes indexes frequently
- optional portal hosting

### 12.4 Library
- large cache (tens of GB if available)
- serves file chunks
- hosts kiwix + knowledge portal

---

## 13. Implementation Order (Full build, reality-first)
1. Patchwork mesh (multi-AP + bridge nodes)
2. DTN bundle daemon (TTL + caches + forwarding policies)
3. VF node storage + listing UI
4. Rolling indexes + queries
5. Files: chunking + retrieval
6. Agents: matchmaker + scheduler (proposal-only)
7. Permaculture: plans/processes/protocols/lessons
8. Optimum-case phone routing Mode A/B experiments

---

## 14. “Finished” Success Criteria (Optimum Case)
- Multi-AP islands operate independently
- Bridge nodes propagate time-sensitive bundles within hours
- Users can discover offers/needs via indexes without full replication
- VF node supports end-to-end flows: offers→match→exchange→event→audit
- Agents generate useful weekly plans + education modules
- Multi-hop routing works for at least a subset of devices; DTN fallback always works
