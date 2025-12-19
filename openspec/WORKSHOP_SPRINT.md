# Workshop Sprint Plan

**Mission:** Build resistance infrastructure for 500k+ network
**Timeline:** Weeks, not months
**Resources:** 3 Claude Pro Max accounts + coordination
**Stakes:** The future of distributed resistance in America

---

## The Vision

A mesh network that enables:
1. **Economic withdrawal** from extractive systems ($1B+ redirected annually at scale)
2. **Mutual aid coordination** that works without internet
3. **Sanctuary operations** for people at risk
4. **Rapid response** when the state comes for our people
5. **Resilient community** that can't be shut down

---

## Sprint Priority: What Must Work at Workshop

### Tier 1: MUST HAVE (Workshop Blockers)

| Proposal | Description | Status |
|----------|-------------|--------|
| [Android Deployment](changes/android-deployment/proposal.md) | App runs on phones, not servers | ✅ IMPLEMENTED - WiFi Direct mesh sync working |
| [Web of Trust](changes/web-of-trust/proposal.md) | Vouching system - keep infiltrators out | ✅ IMPLEMENTED |
| [Mass Onboarding](changes/mass-onboarding/proposal.md) | Get 200 people in during workshop | ✅ IMPLEMENTED - Event QR ready |
| [Offline-First](changes/offline-first/proposal.md) | Works without internet | ✅ IMPLEMENTED - Local storage + mesh sync working |
| [Local Cells](changes/local-cells/proposal.md) | Organize into local groups (molecules) | ✅ IMPLEMENTED - Full stack: API + UI complete |
| [Mesh Messaging](changes/mesh-messaging/proposal.md) | E2E encrypted over DTN | ✅ IMPLEMENTED - Full stack: API + UI complete |

### Tier 2: SHOULD HAVE (First Week Post-Workshop)

| Proposal | Description | Status |
|----------|-------------|--------|
| [Steward Dashboard](changes/steward-dashboard/proposal.md) | Tools for community leaders | ✅ IMPLEMENTED - Metrics + attention queue |
| [Leakage Metrics](changes/leakage-metrics/proposal.md) | Track economic impact | ✅ IMPLEMENTED - Privacy-preserving value tracking |
| [Network Import](changes/network-import/proposal.md) | Bring in existing communities | ✅ IMPLEMENTED - Threshold sigs + offline verification |
| [Panic Features](changes/panic-features/proposal.md) | Duress codes, wipe, decoy | ✅ IMPLEMENTED - Full OPSEC suite |

### Tier 3: IMPORTANT (First Month)

| Proposal | Description | Status |
|----------|-------------|--------|
| [Sanctuary Network](changes/sanctuary-network/proposal.md) | Safe houses, transport, legal | ✅ IMPLEMENTED - Auto-purge + high trust |
| [Rapid Response](changes/rapid-response/proposal.md) | When ICE shows up | ✅ IMPLEMENTED - Full coordination system |
| [Economic Withdrawal](changes/economic-withdrawal/proposal.md) | Coordinated boycotts | ✅ IMPLEMENTED - Backend complete: campaigns, pledges, alternatives, bulk buys |
| [Resilience Metrics](changes/resilience-metrics/proposal.md) | Network health tracking | ✅ IMPLEMENTED - Full stack: repository, service, API routes |

### Tier 4: PHILOSOPHICAL (Ongoing)

| Proposal | Description | Status |
|----------|-------------|--------|
| [Saturnalia Protocol](changes/saturnalia-protocol/proposal.md) | Prevent role crystallization | ✅ IMPLEMENTED - Backend complete: migration, models, repo, service, API |
| [Ancestor Voting](changes/ancestor-voting/proposal.md) | Dead reputation boosts margins | ✅ IMPLEMENTED - Full stack: migration, models, repo, service, API |
| [Mycelial Strike](changes/mycelial-strike/proposal.md) | Automated solidarity defense | ✅ IMPLEMENTED - Complete system: alerts, strikes, throttling, de-escalation, steward oversight |
| [Knowledge Osmosis](changes/knowledge-osmosis/proposal.md) | Study circles output artifacts | ✅ IMPLEMENTED - Full stack: circles, artifacts, Common Heap, osmosis tracking |
| [Algorithmic Transparency](changes/algorithmic-transparency/proposal.md) | Why did the AI match this? | ✅ IMPLEMENTED - Full transparency: explanations, adjustable weights, bias detection, audit trail (13 tests passing) |
| [Temporal Justice](changes/temporal-justice/proposal.md) | Don't exclude caregivers/workers | ✅ IMPLEMENTED - Async participation: slow exchanges, time banks, chunk offers, flexible voting |
| [Accessibility First](changes/accessibility-first/proposal.md) | Works for non-tech-savvy | ✅ IMPLEMENTED - Backend tracking: preferences, feature usage, feedback, metrics (>10% success goal) |
| [Language Justice](changes/language-justice/proposal.md) | Not just English | ✅ IMPLEMENTED - Multi-language: translation system, community contributions, language preferences, >20% non-English goal |

---

## CRITICAL: Gap Fix Proposals (Session 4 Discovery)

**WARNING:** Many features marked "✅ IMPLEMENTED" above have APIs that respond but use placeholder internals. See VISION_REALITY_DELTA.md for details.

### P0 - BEFORE WORKSHOP (Blocking Issues)

| Proposal | Gaps Fixed | Status |
|----------|------------|--------|
| [Fix Real Encryption](changes/fix-real-encryption/proposal.md) | GAP-112, 114, 116, 119 | ✅ IMPLEMENTED |
| [Fix DTN Propagation](changes/fix-dtn-propagation/proposal.md) | GAP-110, 113, 117 | ✅ IMPLEMENTED |
| [Fix Trust Verification](changes/fix-trust-verification/proposal.md) | GAP-106, 118, 120 | ✅ IMPLEMENTED |
| [Fix API Endpoints](changes/fix-api-endpoints/proposal.md) | GAP-65, 69, 71, 72 | ✅ IMPLEMENTED |
| [Fix Fraud/Abuse Protections](changes/fix-fraud-abuse-protections/proposal.md) | GAP-103-109 | ✅ IMPLEMENTED |

### P1 - FIRST WEEK (Quality Issues)

| Proposal | Gaps Fixed | Status |
|----------|------------|--------|
| [Fix Mock Data](changes/fix-mock-data/proposal.md) | GAP-66-68, 70, 73-102, 111, 115, 121-123 | ✅ IMPLEMENTED (80% - core metrics done) |

### Known Facade Issues (from VISION_REALITY_DELTA.md) - ALL FIXED ✅

| Feature | Claims | Reality | Status |
|---------|--------|---------|--------|
| Mesh Messaging | "E2E encrypted" | ~~Base64 encoding only~~ | ✅ FIXED (GAP-116) - Now uses X25519 + XSalsa20-Poly1305 |
| Panic Wipe | "Secure deletion" | ~~Keys not actually wiped~~ | ✅ FIXED (GAP-114) - Now securely overwrites key material |
| Burn Notices | "Network propagation" | ~~Never sent~~ | ✅ FIXED (GAP-113) - Now creates and propagates DTN bundles |
| Trust Checks | "0.9 required" | ~~Hardcoded 0.9 always~~ | ✅ FIXED (GAP-118) - Now queries WebOfTrustService |
| Metrics | "Real tracking" | ~~Hardcoded values~~ | ✅ FIXED (GAP-115) - Now computes from actual database |
| Admin Endpoints | "Protected" | ~~No authentication~~ | ✅ FIXED (GAP-119) - Now requires admin API key |

---

## Parallel Work Streams

### Stream A: Mobile App (Agent 1)
- Port to Android (Capacitor/React Native)
- Local SQLite database
- WiFi Direct / Bluetooth mesh
- APK sideloading

### Stream B: Trust & Identity (Agent 2)
- Web of Trust vouching system
- Trust score computation
- Revocation cascade
- Network import OAuth

### Stream C: Core Features (Agent 3)
- Fix existing gaps (GAP-01 through GAP-10)
- Offer/need flow working
- Matching and proposals
- Exchange completion

### Stream D: Security & OPSEC (Agent 4 or rotate)
- Panic features
- E2E messaging encryption
- Duress detection
- Auto-purge of sensitive data

---

## What Exists Already (Don't Rebuild)

- ✅ DTN Bundle System (store-and-forward)
- ✅ Ed25519 cryptographic signing
- ✅ ValueFlows data model
- ✅ 7 AI agents (matchmaker, scheduler, etc.)
- ✅ Proposal/approval flow
- ✅ React frontend
- ✅ SQLite databases
- ✅ Docker infrastructure (for dev)

---

## What Must Be Built

### Week 1: Make It Mobile
- [ ] Capacitor or React Native wrapper
- [ ] Port database to local SQLite
- [ ] Basic WiFi Direct sync
- [ ] APK that installs and runs

### Week 1: Make It Secure
- [ ] Web of Trust data model
- [ ] Vouch creation flow
- [ ] Trust computation
- [ ] High-trust gating on sensitive actions

### Week 2: Make It Scale
- [ ] Event QR onboarding
- [ ] Batch import tools
- [ ] Cell discovery and formation
- [ ] Steward dashboard basics

### Week 2: Make It Work Offline
- [ ] Local-first data layer
- [ ] Sync protocol
- [ ] Conflict resolution
- [ ] Sync status UI

### Week 3: Make It Safe
- [ ] Duress PIN
- [ ] Quick wipe
- [ ] Panic alert propagation
- [ ] Auto-purge timers

---

## Workshop Day Checklist

By workshop start, attendees must be able to:

- [ ] Install APK on their phone (2 minutes)
- [ ] Scan event QR to join (30 seconds)
- [ ] See other workshop attendees (immediate)
- [ ] Post an offer (1 minute)
- [ ] Post a need (1 minute)
- [ ] Get matched (within session)
- [ ] Message their match (works via mesh)
- [ ] Complete a mock exchange (5 minutes)
- [ ] See workshop collective impact (end of day)

---

## Success Metrics

### At Workshop End
- 200+ attendees onboarded
- 50+ offers posted
- 20+ matches made
- 10+ exchanges completed
- Mesh messaging works phone-to-phone

### At Week 4
- 10,000+ members onboarded
- 100+ cells formed
- $100k+ estimated value circulated
- Mesh works without internet
- Zero security incidents

### At Month 3
- 100,000+ members
- 1,000+ active cells
- $10M+ estimated value circulated
- Sanctuary operations functional
- Rapid response tested

---

## Critical Reference Documents

Before building ANYTHING, read:

1. **[ARCHITECTURE_CONSTRAINTS.md](ARCHITECTURE_CONSTRAINTS.md)** - Non-negotiable requirements
   - Old phones (Android 8+, 2GB RAM)
   - Fully distributed (no server)
   - Works without internet
   - No big tech dependencies
   - Seizure resistant

2. **[ADVERSARIAL_REVIEW.md](ADVERSARIAL_REVIEW.md)** - How to sabotage this network
   - 40 attack vectors identified
   - Priority hardening items
   - Assume infiltration

---

## Agent Coordination Protocol

When working on these proposals:

1. **Read the proposal completely** before starting
2. **Check for dependencies** - some proposals build on others
3. **Update proposal status** as you work (Draft → In Progress → Implemented)
4. **Document what you build** - others will need to understand
5. **Test on actual Android device** if touching mobile
6. **Think adversarially** - assume infiltrators will try

---

## Emergency Contacts

If stuck, need decisions, or find blocking issues:

- Liz: [coordination channel]
- This repository: main source of truth
- Philosopher Council reviews: for values decisions

---

## Remember

> "Every transaction in the gift economy is a transaction that DIDN'T go to Bezos. Every person connected to the mesh is someone who can't be isolated. Every cell that forms is a community that can protect its own."

This isn't an app. It's infrastructure for the next economy.

Build accordingly.
