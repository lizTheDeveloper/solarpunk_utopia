# Architecture Constraints: Non-Negotiables

**These constraints are absolute. Any proposal that violates them is rejected.**

---

## Constraint 1: Old Phones

**The system MUST work on old Android phones.**

- Minimum: Android 8.0 (2017)
- RAM: 2GB
- Storage: 16GB total, app uses <500MB
- CPU: Whatever $30 gets you in 2018

**Why:** The people who most need this network have the least resources. If it only works on iPhone 14, it's not solarpunk, it's techno-feudalism.

**Implications:**
- No heavy frameworks
- Minimal dependencies
- Efficient storage
- Battery-conscious design
- Works on cracked screens
- Works with spotty touch

---

## Constraint 2: Fully Distributed

**There is NO central server. NO admin. NO single point of control.**

- No AWS/GCP/Azure
- No "the server"
- No "admin panel" that controls the network
- No single signing key that matters

**Why:** Anything centralized can be:
- Seized
- Subpoenaed
- Pressured
- Compromised
- Shut down

**Implications:**
- All data lives on user devices
- Sync is peer-to-peer (mesh)
- "Admin" functions are distributed (steward consensus, not single admin)
- Signing keys for attestations: multiple required, threshold signatures
- No phone-home, no telemetry, no analytics

---

## Constraint 3: Works Without Internet

**The system MUST work with zero internet connectivity.**

- Phone-to-phone over WiFi Direct
- Phone-to-phone over Bluetooth
- Store-and-forward when no direct connection
- Days of operation without any internet

**Why:**
- Rural areas have no signal
- Festivals/gatherings are often off-grid
- Internet can be shut down
- Cell networks can be surveilled
- The mesh IS the infrastructure

**Implications:**
- Local-first database
- DTN bundle sync
- No "checking the server"
- No email verification that requires live internet
- No dependencies on internet services

---

## Constraint 4: No Big Tech Dependencies

**The system MUST NOT depend on any corporation.**

- No Google Play (sideload only)
- No Apple App Store (maybe PWA, but not required)
- No OAuth to any platform
- No cloud storage
- No CDN
- No analytics platforms
- No email services (or self-hosted only)
- No SMS gateways (or mesh-based verification)

**Why:**
- Any platform can cut us off
- Any platform can be pressured to share data
- Any platform can be acquired by adversaries
- Independence means no dependencies

**Implications:**
- APK distribution via mesh, QR, file share
- Verification via mesh-based challenge-response
- Email is optional enhancement, not requirement
- All core functions work on mesh alone

---

## Constraint 5: Seizure Resistant

**Seizing any device should not compromise the network.**

- No device has "all the data"
- No device has "the keys to the kingdom"
- Compromising one node doesn't reveal others
- Losing a device doesn't lose access (recovery possible)

**Why:**
- Devices will be seized
- People will be detained
- Phones will be demanded at borders
- We assume hostile environment

**Implications:**
- Compartmentalization by design
- Minimal data on each device
- Data expires and auto-deletes
- Recovery via seed phrase + trusted contacts
- Network continues if any node disappears

---

## Constraint 6: Understandable

**A non-technical person must be able to use this.**

- No command lines
- No config files
- No "edit the JSON"
- No technical jargon in UI

**Why:**
- Most people are not developers
- The community includes elders, children, non-English speakers
- If only hackers can use it, we've failed

**Implications:**
- Simple, clear UI
- Onboarding that actually onboards
- Errors that explain what to do
- Accessibility (screen readers, large text, etc.)

---

## Constraint 7: No Surveillance Capitalism Patterns

**The system MUST NOT implement patterns that enable surveillance capitalism.**

- No tracking individual contributions publicly
- No "reputation scores" that become currency
- No gamification that creates compulsion
- No dark patterns
- No attention hijacking

**Why:**
- We're building an alternative to capitalism, not a new flavor of it
- Reputation scores become class markers
- Gamification is manipulation
- This is about liberation, not engagement metrics

**Implications:**
- Aggregate stats only (community level, not individual)
- No leaderboards
- No streaks or badges
- No notifications designed to addict
- Users control all notification settings

---

## Constraint 8: Harm Reduction

**The system MUST minimize harm when things go wrong.**

- Failed sanctuary shouldn't expose the sanctuary network
- Compromised member shouldn't reveal all their contacts
- Crashed app shouldn't corrupt data
- Mistake by one person shouldn't break the network

**Why:**
- Things will go wrong
- People will make mistakes
- Adversaries will succeed sometimes
- The question is: how bad is the damage?

**Implications:**
- Compartmentalization
- Graceful degradation
- Auto-recovery
- Limited blast radius for any failure

---

## How to Evaluate Proposals

For every proposal, ask:

1. **Old phone test:** Will this work on a 2017 Android with 2GB RAM?
2. **Island test:** Will this work with no internet for a week?
3. **Seizure test:** If police take this phone, what do they learn?
4. **Platform test:** If [platform] cuts us off, does this still work?
5. **Grandma test:** Can my non-technical relative use this?
6. **Goldman test:** Does this create reputation capitalism?
7. **Failure test:** When this breaks, how bad is it?

If any answer is bad, redesign.

---

## Anti-Patterns to Reject

| Pattern | Why It's Bad | What To Do Instead |
|---------|--------------|-------------------|
| "The server stores X" | Central point of failure/seizure | User devices store, mesh syncs |
| "Admin approves X" | Centralized authority | Steward consensus, threshold |
| "OAuth with X" | Platform dependency | Mesh-based verification |
| "API call to X" | Requires internet | Local-first with optional sync |
| "User with most Y" | Reputation capitalism | Aggregate only |
| "Send email to verify" | Requires internet + email service | In-person or mesh challenge |
| "Push notification via FCM" | Google dependency | Local notification + mesh alert |
| "Check the blockchain" | Requires internet + crypto infrastructure | Local signatures, mesh consensus |

---

## This Is Non-Negotiable

These constraints exist because they're load-bearing for the mission.

If a feature can't be built within these constraints, the feature doesn't get built.

If a shortcut requires violating these constraints, we don't take the shortcut.

The goal is not "an app." The goal is infrastructure for a new economy that can survive hostile conditions.

Build accordingly.
