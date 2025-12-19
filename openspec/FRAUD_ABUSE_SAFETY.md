# Fraud, Abuse & Safety Analysis

**Purpose:** Identify and mitigate vectors for fraud, abuse, and safety failures
**Perspective:** Bad actors within the community, not just external adversaries

---

## Part 1: Fraud Vectors

### FRAUD-01: Fake Offers (Never Intended to Deliver)

**Attack:** Post attractive offers, get matched, never show up. Waste people's time, erode trust.

**Current State:** No verification that offerer can deliver. No consequences for no-shows.

**Mitigations:**
1. **Completion tracking:** Track offer→match→complete rate per user
2. **No-show flag:** If matched party reports no-show, flag the offerer
3. **Pattern detection:** 3+ no-shows = trust score penalty + steward review
4. **Pre-match verification:** For high-value items, steward can verify before matching

**Implementation:**
```python
class OfferCompletionTracker:
    user_id: str
    offers_posted: int
    matches_made: int
    exchanges_completed: int
    no_shows_reported: int

    @property
    def completion_rate(self) -> float:
        if self.matches_made == 0:
            return 1.0
        return self.exchanges_completed / self.matches_made

    @property
    def is_suspicious(self) -> bool:
        return self.no_shows_reported >= 3 or self.completion_rate < 0.5
```

---

### FRAUD-02: Fake Needs (Resource Hoarding)

**Attack:** Post fake needs to accumulate resources without genuine necessity. Gift economy becomes one-way extraction.

**Current State:** Anyone can post unlimited needs. No verification of actual need.

**Mitigations:**
1. **Need limits:** Cap active needs per user (e.g., 5 at a time)
2. **Fulfillment tracking:** Must close old needs before posting new ones
3. **Pattern detection:** Always needing, never offering = flag for review
4. **Community visibility:** Cell can see aggregate give/receive ratios (not individual shame, but steward visibility)

**Implementation:**
```python
MAX_ACTIVE_NEEDS = 5

async def can_post_need(user_id: str) -> tuple[bool, str]:
    active_needs = await get_active_needs_count(user_id)
    if active_needs >= MAX_ACTIVE_NEEDS:
        return False, "Please close existing needs before posting new ones"
    return True, ""
```

---

### FRAUD-03: Fake Exchanges (Metric Inflation)

**Attack:** Two colluding users create fake exchanges to inflate leakage metrics. "We circulated $1M!" but it's fake.

**Current State:** Exchange completion is self-reported by participants. No verification.

**Mitigations:**
1. **Value caps:** Individual exchanges capped at reasonable amount (e.g., $500 estimated value)
2. **Velocity limits:** Max exchanges per day per user (e.g., 3)
3. **Pattern detection:** Same two users exchanging repeatedly = flag
4. **Random verification:** Stewards randomly verify 5% of exchanges

**Implementation:**
```python
MAX_EXCHANGE_VALUE = 500
MAX_DAILY_EXCHANGES = 3

async def validate_exchange(exchange: Exchange) -> tuple[bool, str]:
    if exchange.estimated_value > MAX_EXCHANGE_VALUE:
        return False, f"Value exceeds maximum ({MAX_EXCHANGE_VALUE})"

    today_count = await get_user_exchanges_today(exchange.provider_id)
    if today_count >= MAX_DAILY_EXCHANGES:
        return False, "Daily exchange limit reached"

    # Check for repeated exchanges with same person
    recent = await get_exchanges_between(
        exchange.provider_id,
        exchange.receiver_id,
        days=30
    )
    if len(recent) > 5:
        await flag_for_steward_review(exchange, "Repeated exchanges with same user")

    return True, ""
```

---

### FRAUD-04: Vouch Selling/Trading

**Attack:** High-trust member sells vouches for money or favors. Trust system becomes pay-to-play.

**Current State:** No monitoring of vouch patterns. No consequences for bad vouches.

**Mitigations:**
1. **Vouch accountability:** If vouchee is revoked, voucher's trust drops
2. **Vouch limits:** Max vouches per month (e.g., 5)
3. **Vouch cooling:** Can't vouch someone you just met (24-hour minimum)
4. **Pattern detection:** Sudden spike in vouching = flag for review

**Implementation:**
```python
MAX_VOUCHES_PER_MONTH = 5
MIN_KNOWN_HOURS = 24

async def can_vouch(voucher_id: str, vouchee_id: str) -> tuple[bool, str]:
    # Check monthly limit
    monthly_vouches = await get_vouches_this_month(voucher_id)
    if len(monthly_vouches) >= MAX_VOUCHES_PER_MONTH:
        return False, "Monthly vouch limit reached"

    # Check if they've interacted before
    first_interaction = await get_first_interaction(voucher_id, vouchee_id)
    if first_interaction is None:
        return False, "You must interact with someone before vouching"

    hours_known = (now() - first_interaction).total_hours()
    if hours_known < MIN_KNOWN_HOURS:
        return False, f"Please wait {MIN_KNOWN_HOURS - hours_known:.0f} more hours"

    return True, ""
```

---

### FRAUD-05: Identity Cloning

**Attack:** Create account pretending to be someone else. Use their reputation, target their contacts.

**Current State:** No identity verification beyond vouching.

**Mitigations:**
1. **Unique identifiers:** Public key is identity - can't be duplicated
2. **Vouch chain verification:** Real person will have different vouch chain than clone
3. **Challenge protocol:** If suspected clone, real person can challenge
4. **In-person verification:** For high-trust, require steward to have met in person

**Implementation:**
```python
async def report_identity_clone(reporter_id: str, suspect_id: str, real_id: str):
    """Report that suspect_id is impersonating real_id"""

    # Notify both parties
    await send_alert(real_id, f"Someone may be impersonating you: {suspect_id}")
    await send_alert(suspect_id, f"Your identity has been challenged by {reporter_id}")

    # Steward review
    await create_steward_case(
        type="identity_challenge",
        suspect=suspect_id,
        claimed_real=real_id,
        reporter=reporter_id
    )

    # Suspend suspect's ability to vouch until resolved
    await suspend_vouch_ability(suspect_id, reason="Identity challenge pending")
```

---

## Part 2: Abuse Vectors

### ABUSE-01: Harassment via Matching

**Attack:** Deliberately match with someone to harass them. Use the exchange coordination to stalk or threaten.

**Current State:** Anyone can accept any offer. No blocking mechanism.

**Mitigations:**
1. **Block list:** Users can block others - no matching, no messaging
2. **Match approval:** Offerer can decline a match request
3. **Report mechanism:** Report harassment, steward reviews
4. **Pattern detection:** Multiple reports against same user = suspension

**Implementation:**
```python
class BlockList:
    user_id: str
    blocked_ids: List[str]

async def can_match(requester_id: str, offerer_id: str) -> bool:
    # Check if blocked
    offerer_blocks = await get_block_list(offerer_id)
    if requester_id in offerer_blocks.blocked_ids:
        return False  # Silently fail - don't reveal block

    requester_blocks = await get_block_list(requester_id)
    if offerer_id in requester_blocks.blocked_ids:
        return False

    return True
```

---

### ABUSE-02: Doxxing via Offers

**Attack:** Post offers with hidden location/identity data. When people accept, collect their info for doxxing.

**Current State:** Exchange coordination may reveal location, contact info.

**Mitigations:**
1. **Minimal info exchange:** Only share what's needed for the exchange
2. **Location fuzzing:** Show approximate location until match confirmed
3. **Proxy meeting points:** Suggest public meeting points, not home addresses
4. **Steward-mediated high-risk:** For new users, steward can mediate

**Implementation:**
```python
def get_visible_location(offer: Offer, viewer_trust: float) -> Location:
    if viewer_trust < 0.5:
        # Low trust: only show neighborhood
        return offer.location.fuzz(radius_km=2)
    elif viewer_trust < 0.7:
        # Medium trust: show block
        return offer.location.fuzz(radius_km=0.5)
    else:
        # High trust: show actual location
        return offer.location

SAFE_MEETING_POINTS = [
    "Community center",
    "Library",
    "Coffee shop",
    "Public park",
]

def suggest_meeting_point(offer: Offer) -> str:
    """Suggest public meeting point instead of private location"""
    return random.choice(SAFE_MEETING_POINTS)
```

---

### ABUSE-03: Coercive Vouching

**Attack:** Pressure vulnerable people to vouch for you. "Vouch for me or I'll hurt you."

**Current State:** No way to report coerced vouches. No mechanism to revoke under duress.

**Mitigations:**
1. **Anonymous vouch reporting:** Report a vouch you made under duress
2. **Vouch cooling-off:** Can revoke own vouch within 48 hours, no questions
3. **Duress detection:** Sudden vouch followed by immediate revoke = flag
4. **Steward outreach:** Steward can reach out if patterns detected

**Implementation:**
```python
VOUCH_COOLOFF_HOURS = 48

async def revoke_own_vouch(voucher_id: str, vouchee_id: str, reason: str = None):
    vouch = await get_vouch(voucher_id, vouchee_id)

    hours_since = (now() - vouch.created_at).total_hours()

    if hours_since <= VOUCH_COOLOFF_HOURS:
        # Within cooloff - revoke without consequence
        await delete_vouch(vouch.id)
        await recalculate_trust(vouchee_id)
    else:
        # After cooloff - requires reason and affects both parties slightly
        if not reason:
            return False, "Reason required after cooloff period"
        await delete_vouch(vouch.id)
        await recalculate_trust(vouchee_id)
        await flag_for_review(voucher_id, vouchee_id, reason)

    return True, ""

async def report_coerced_vouch(voucher_id: str, vouchee_id: str):
    """Anonymously report that a vouch was coerced"""
    await delete_vouch_immediately(voucher_id, vouchee_id)
    await create_steward_case(
        type="coerced_vouch",
        suspect=vouchee_id,
        # Don't store reporter to protect them
    )
    await suspend_vouch_ability(vouchee_id, reason="Under investigation")
```

---

### ABUSE-04: Cell Capture for Abuse

**Attack:** Become steward of a cell, use steward powers to abuse members. Approve harassers, block victims, control information.

**Current State:** Steward has significant power. Limited accountability.

**Mitigations:**
1. **Multi-steward requirement:** Sensitive actions require 2+ stewards
2. **Term limits:** Stewards rotate, preventing entrenchment
3. **Steward accountability log:** All steward actions logged, visible to cell
4. **Override mechanism:** Super-majority of cell can remove steward
5. **Cross-cell visibility:** Regional stewards can see patterns across cells

**Implementation:**
```python
SENSITIVE_ACTIONS = [
    "approve_join",
    "revoke_member",
    "change_settings",
    "view_member_list",
]

async def require_multi_steward(action: str, cell_id: str, actor_id: str):
    if action in SENSITIVE_ACTIONS:
        stewards = await get_cell_stewards(cell_id)
        if len(stewards) < 2:
            # Small cell - log for transparency
            await log_steward_action(action, cell_id, actor_id, multi=False)
        else:
            # Require second steward approval
            await create_pending_action(action, cell_id, actor_id)
            await notify_other_stewards(cell_id, actor_id, action)
            return "pending_approval"

    await log_steward_action(action, cell_id, actor_id)
    return "approved"

async def remove_steward_by_vote(cell_id: str, steward_id: str):
    """Cell members can vote to remove a steward"""
    members = await get_cell_members(cell_id)
    votes = await get_removal_votes(cell_id, steward_id)

    # 2/3 majority required
    if len(votes) >= len(members) * 0.67:
        await remove_steward(cell_id, steward_id)
        await notify_all(cell_id, f"Steward {steward_id} removed by member vote")
```

---

### ABUSE-05: Information Weaponization

**Attack:** Use information from the network (who needs help, who has resources, patterns) for targeting/blackmail.

**Current State:** Data is distributed but still exists. Stewards can see sensitive info.

**Mitigations:**
1. **Minimal data:** Don't store what you don't need
2. **Data expiration:** Old data auto-deletes
3. **Access logging:** All data access logged
4. **Compartmentalization:** No single view of everything
5. **Steward data limits:** Even stewards can't export or bulk-view

**Implementation:**
```python
# Data retention policy
RETENTION_DAYS = {
    "offers": 30,           # Active offers
    "completed_offers": 90, # After completion
    "needs": 30,
    "completed_needs": 90,
    "exchanges": 180,       # Completed exchanges
    "messages": 30,         # Auto-delete messages
    "sanctuary": 1,         # 24 hours max!
    "alerts": 7,
}

async def purge_expired_data():
    """Run daily to purge old data"""
    for data_type, days in RETENTION_DAYS.items():
        cutoff = now() - timedelta(days=days)
        await delete_older_than(data_type, cutoff)

# Steward access limits
async def steward_view_members(steward_id: str, cell_id: str):
    """Steward can see member list but not export"""
    await log_access(steward_id, "member_list", cell_id)

    # Return limited view - no contact info
    members = await get_cell_members(cell_id)
    return [
        {"id": m.id, "name": m.display_name, "trust": m.trust_score}
        for m in members
    ]
    # NO: email, phone, address, full activity history
```

---

## Part 3: Safety Failures

### SAFETY-01: Sanctuary Trap (Physical Danger)

**Attack:** Offer fake safe house. Person in danger shows up. Attacker is waiting.

**THIS IS THE HIGHEST RISK SCENARIO.**

**Current State:** Web of trust + steward verification proposed, but not enough.

**Mitigations:**
1. **Never use unverified sanctuary:** No exceptions
2. **Multi-steward verification:** 2+ stewards must verify in person
3. **Verification expiration:** Re-verify every 90 days
4. **Buddy system:** Someone always knows where person is going
5. **Check-in protocol:** Must check in within X hours or alert triggered
6. **Escape routes:** Safe houses must have documented escape routes
7. **No first-time for critical:** Never send critical need to first-time sanctuary

**Implementation:**
```python
class SanctuaryVerification:
    space_id: str
    verified_by: List[str]  # At least 2 steward IDs
    verified_at: datetime
    last_check: datetime
    escape_routes: List[str]
    buddy_protocol: bool

    @property
    def is_valid(self) -> bool:
        if len(self.verified_by) < 2:
            return False
        if (now() - self.verified_at).days > 90:
            return False
        return True

async def assign_sanctuary(person_id: str, need_severity: str) -> Optional[str]:
    available = await get_verified_sanctuaries()

    if need_severity == "critical":
        # Only use sanctuaries with 3+ successful prior uses
        available = [s for s in available if s.successful_uses >= 3]

    if not available:
        # No safe options - escalate to regional stewards
        await escalate_sanctuary_need(person_id, need_severity)
        return None

    sanctuary = select_best_match(available, person_id)

    # Set up buddy system
    buddy = await assign_buddy(person_id)
    await create_checkin_requirement(
        person_id,
        sanctuary.id,
        buddy.id,
        checkin_hours=4,  # Must check in every 4 hours
    )

    return sanctuary.id
```

---

### SAFETY-02: Rapid Response as Trap

**Attack:** Trigger false rapid response to identify activists. Photograph/detain everyone who shows up.

**Current State:** Alerts propagate to all nearby high-trust members.

**Mitigations:**
1. **Tiered response:** Not everyone needs to physically show up
2. **Role separation:** Legal observers ≠ direct responders
3. **Remote support:** Many roles can be done remotely
4. **Alert verification:** CRITICAL requires confirmation within 5 min
5. **Response training:** Only trained members physically respond
6. **Counter-surveillance:** Assume you're being watched

**Implementation:**
```python
class RapidResponseRoles:
    REMOTE_SUPPORT = "remote"      # Coordinate, document, legal calls
    LEGAL_OBSERVER = "observer"    # Document from distance, don't engage
    DIRECT_RESPONDER = "direct"    # Physically intervene if trained
    MEDIA_LIAISON = "media"        # Interface with press

async def assign_response_roles(alert_id: str, responders: List[str]):
    """Assign roles based on training and proximity"""
    for responder_id in responders:
        training = await get_training(responder_id)
        proximity = await get_proximity_to_alert(responder_id, alert_id)

        if "direct_action" in training and proximity < 5:  # Within 5 min
            role = RapidResponseRoles.DIRECT_RESPONDER
        elif "legal_observer" in training:
            role = RapidResponseRoles.LEGAL_OBSERVER
        else:
            role = RapidResponseRoles.REMOTE_SUPPORT

        await assign_role(alert_id, responder_id, role)
        await send_role_instructions(responder_id, role)
```

---

### SAFETY-03: Panic Feature Failure

**Attack:** Panic wipe fails, leaving sensitive data. Or: panic triggers accidentally, wiping legitimate data.

**Current State:** Panic features proposed but not implemented.

**Mitigations:**
1. **Test regularly:** Users should test panic features monthly
2. **Secure deletion:** Overwrite, don't just delete
3. **Confirmation gesture:** Prevent accidental triggers
4. **Recovery path:** Seed phrase recovery after legitimate wipe
5. **Backup elsewhere:** Critical data can be recovered from network

**Implementation:**
```python
async def panic_wipe(confirmation_gesture: str) -> bool:
    """Execute panic wipe with secure deletion"""

    # Verify confirmation gesture (e.g., specific pattern)
    if not verify_gesture(confirmation_gesture):
        return False

    # Order matters - most sensitive first
    wipe_order = [
        "private_keys",      # Identity - most sensitive
        "messages",          # Communications
        "sanctuary_data",    # Location of vulnerable people
        "vouch_data",        # Trust relationships
        "offers_needs",      # Activity history
    ]

    for data_type in wipe_order:
        # Secure delete: overwrite with random data, then delete
        await secure_delete(data_type)

    # Reset app to fresh install state
    await reset_to_fresh()

    # Queue burn notice to network (will send when reconnected)
    await queue_burn_notice(get_public_key())

    return True

async def secure_delete(data_type: str):
    """Overwrite data before deletion"""
    data = await get_all(data_type)

    # Overwrite with random bytes
    for record in data:
        random_data = os.urandom(len(serialize(record)))
        await overwrite(record.id, random_data)

    # Then delete
    await delete_all(data_type)

    # Force filesystem sync
    await force_sync()
```

---

### SAFETY-04: Mesh Message Interception

**Attack:** Compromise relay nodes, collect metadata (who talks to whom, when, patterns).

**Current State:** E2E encryption proposed, but metadata still visible.

**Mitigations:**
1. **Onion routing:** Message bounces through multiple nodes
2. **Cover traffic:** Fake messages to obscure real patterns
3. **Timing randomization:** Random delays prevent timing analysis
4. **Recipient anonymization:** Encrypt recipient ID too

**Implementation:**
```python
async def send_message_secure(sender_id: str, recipient_id: str, content: str):
    """Send message with metadata protection"""

    # 1. Encrypt content with recipient's key
    encrypted_content = encrypt(content, recipient_pubkey)

    # 2. Choose onion route (3 hops)
    route = select_random_route(hops=3)

    # 3. Wrap in onion layers
    for hop in reversed(route):
        encrypted_content = wrap_onion_layer(encrypted_content, hop.pubkey)

    # 4. Random delay before sending (1-30 seconds)
    await asyncio.sleep(random.uniform(1, 30))

    # 5. Send to first hop (recipient unknown to first hop)
    await send_to_hop(route[0], encrypted_content)

    # 6. Generate cover traffic
    await generate_cover_traffic()
```

---

### SAFETY-05: Device Theft While Logged In

**Attack:** Phone snatched while unlocked. Attacker has full access.

**Current State:** No auto-lock, no session timeout.

**Mitigations:**
1. **Auto-lock:** Lock app after 2 minutes inactive
2. **Sensitive action re-auth:** PIN required for sensitive actions
3. **Quick-lock gesture:** Specific gesture to lock immediately
4. **Motion detection:** Detect "snatched" motion, auto-lock

**Implementation:**
```python
INACTIVITY_TIMEOUT = 120  # 2 minutes
SENSITIVE_ACTIONS = [
    "send_message",
    "create_offer",
    "view_sanctuary",
    "vouch_for",
]

class SecurityManager:
    last_activity: datetime
    locked: bool = False

    async def check_lock(self):
        if (now() - self.last_activity).seconds > INACTIVITY_TIMEOUT:
            await self.lock()

    async def on_action(self, action: str):
        self.last_activity = now()

        if action in SENSITIVE_ACTIONS:
            if not await self.verify_pin():
                raise SecurityError("PIN required")

    async def detect_snatch(self, accelerometer_data):
        """Detect sudden acceleration (phone snatched)"""
        if detect_snatch_pattern(accelerometer_data):
            await self.lock()
            await self.alert_contacts("Phone may have been taken")
```

---

## Part 4: Sabotage Loose Ends

### Reviewing ADVERSARIAL_REVIEW.md - What's Not Yet Addressed?

| Attack | Status | Needs Work |
|--------|--------|------------|
| Long-term infiltration | Proposed | Need behavioral analysis implementation |
| Genesis node compromise | Proposed | Need 7+ genesis, diverse profiles |
| Weaponized revocation | Proposed | Need supermajority requirement |
| Trust score gaming | **NOT ADDRESSED** | Need quality metrics, not just quantity |
| Event flood | Proposed | Need per-event limits |
| QR code theft | Proposed | Need expiration, location binding |
| Steward impersonation | **NOT ADDRESSED** | Need steward verification protocol |
| Honeypot cell | Proposed | Need cell age/provenance visibility |
| Steward capture | Proposed | Need term limits, logging |
| Cell isolation | **NOT ADDRESSED** | Need connectivity metrics |
| Traffic analysis | Proposed | Need onion routing implementation |
| Mesh flooding | **NOT ADDRESSED** | Need rate limiting |
| Malicious APK | Proposed | Need signing, verification |
| Relay node compromise | Proposed | Need untrusted relay design |
| False panic | Proposed | Need reversible wipe |
| Duress detection | Proposed | Need indistinguishable decoy |
| Seed phrase interception | **NOT ADDRESSED** | Need secure generation UX |
| Fake safe house | Enhanced above | See SAFETY-01 |
| Reverse sting | Enhanced above | Need compartmentalization |
| Pattern analysis | Proposed | Need anonymization |
| False alarm exhaustion | Proposed | Need trust impact |
| Response gathering trap | Enhanced above | See SAFETY-02 |
| Coordinator compromise | Proposed | Need coordinator rotation |
| Data poisoning | Proposed | Need anomaly detection |
| Sync conflict exploitation | **NOT ADDRESSED** | Need clear resolution |
| Version fragmentation | **NOT ADDRESSED** | Need protocol versioning |
| Pledge then defect | Proposed | Need private pledges |
| Fake impact numbers | Proposed | Need conservative estimates |
| Platform retaliation | Addressed | No platform dependencies |
| Metric manipulation | Proposed | Need aggregates only |
| OAuth compromise | Addressed | No OAuth |
| Fake source community | Proposed | Need verification |
| Steward account takeover | Proposed | Need 2FA, dual-steward |
| Dashboard as intel | Proposed | Need data minimization |
| Legal pressure | Proposed | Need distributed architecture |
| App store removal | Addressed | Sideload only |
| ISP blocking | Proposed | Need traffic obfuscation |
| Physical seizure | Proposed | Need dead man's switch |
| Social engineering | **NOT ADDRESSED** | Need verification culture |
| Co-optation | **NOT ADDRESSED** | Need independence policy |

---

## Implementation Priority

### P0 - Before Workshop
1. Block list (ABUSE-01)
2. Fake offer detection (FRAUD-01)
3. Auto-lock (SAFETY-05)
4. Sanctuary verification (SAFETY-01) - critical

### P1 - First Week
5. Multi-steward for sensitive actions (ABUSE-04)
6. Vouch limits and cooling (FRAUD-04)
7. Panic wipe implementation (SAFETY-03)
8. Coerced vouch reporting (ABUSE-03)

### P2 - First Month
9. Onion routing (SAFETY-04)
10. Data retention/expiration (ABUSE-05)
11. Exchange velocity limits (FRAUD-03)
12. Mesh flood protection

### P3 - Ongoing
13. Behavioral analysis for infiltration
14. Traffic analysis protection
15. Counter-surveillance training
16. Independence policy (no co-optation)

---

## Cultural Mitigations

Technical controls are not enough. The community needs:

1. **Verification culture:** "Did you meet them in person?" should be normal
2. **Healthy skepticism:** Question unusual patterns, don't assume good faith
3. **Reporting normalization:** Make reporting issues easy and non-shameful
4. **Steward accountability:** Stewards are servants, not rulers
5. **Rotation expectations:** No permanent roles, everyone rotates
6. **Security training:** Regular training on OPSEC, not just technical
7. **Failure acceptance:** When things go wrong, learn and adapt, don't blame

---

*"Security is a process, not a product."* — Bruce Schneier

Build the technical controls. But also build the culture.
