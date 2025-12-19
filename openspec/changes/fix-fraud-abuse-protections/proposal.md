# Proposal: Implement Fraud/Abuse Protections

**Submitted By:** Gap Analysis Agent
**Date:** 2025-12-19
**Status:** ✅ IMPLEMENTED
**Gaps Addressed:** GAP-103, GAP-104, GAP-105, GAP-107, GAP-108, GAP-109
**Priority:** P1 - First Week (P0 for Block List and Sanctuary Verification)
**Implemented:** 2025-12-19

## Problem Statement

FRAUD_ABUSE_SAFETY.md specifies critical protections that aren't implemented:

1. **GAP-103**: No monthly vouch limit (spec: MAX=5)
2. **GAP-104**: No vouch cooling period (spec: 24h minimum)
3. **GAP-105**: No vouch revocation cooloff (spec: 48h grace)
4. **GAP-107**: No block list for harassment prevention
5. **GAP-108**: No auto-lock on inactivity
6. **GAP-109**: No sanctuary verification protocol

## Proposed Solutions

### 1. Monthly Vouch Limit (GAP-103)

```python
# app/models/vouch.py
MAX_VOUCHES_PER_MONTH = 5

# app/services/web_of_trust_service.py
def get_vouch_eligibility(self, voucher_id: str, vouchee_id: str) -> Dict:
    # ... existing checks ...

    # Check monthly limit
    monthly_vouches = self.vouch_repo.get_vouches_since(
        voucher_id,
        since=datetime.utcnow() - timedelta(days=30)
    )
    if len(monthly_vouches) >= MAX_VOUCHES_PER_MONTH:
        return {
            "can_vouch": False,
            "reason": f"Monthly vouch limit reached ({MAX_VOUCHES_PER_MONTH}). Resets in {days_until_reset} days.",
        }
```

### 2. Vouch Cooling Period (GAP-104)

```python
# app/models/vouch.py
MIN_KNOWN_HOURS = 24

# app/services/web_of_trust_service.py
def get_vouch_eligibility(self, voucher_id: str, vouchee_id: str) -> Dict:
    # Check if they've interacted before
    first_interaction = self.vouch_repo.get_first_interaction(voucher_id, vouchee_id)

    if first_interaction is None:
        return {
            "can_vouch": False,
            "reason": "You must interact with this person before vouching",
        }

    hours_known = (datetime.utcnow() - first_interaction).total_seconds() / 3600
    if hours_known < MIN_KNOWN_HOURS:
        remaining = MIN_KNOWN_HOURS - hours_known
        return {
            "can_vouch": False,
            "reason": f"Please wait {remaining:.0f} more hours before vouching",
        }
```

### 3. Vouch Revocation Cooloff (GAP-105)

```python
# app/models/vouch.py
VOUCH_COOLOFF_HOURS = 48

# app/api/vouch.py
@router.post("/revoke")
async def revoke_vouch(request: RevocationRequest, ...):
    vouch = repo.get_vouch(request.vouch_id)

    hours_since = (datetime.utcnow() - vouch.created_at).total_seconds() / 3600

    if hours_since <= VOUCH_COOLOFF_HOURS:
        # Within cooloff - revoke without consequence, no reason required
        await repo.delete_vouch(vouch.id)
        return {"status": "revoked", "consequence": "none", "reason": "Within cooloff period"}

    # After cooloff - requires reason
    if not request.reason:
        raise HTTPException(400, "Reason required after cooloff period")

    result = trust_service.revoke_vouch_with_cascade(request.vouch_id, request.reason)
    return result
```

### 4. Block List (GAP-107) - P0 PRIORITY

```python
# app/models/block.py
class BlockEntry(BaseModel):
    id: str
    blocker_id: str
    blocked_id: str
    created_at: datetime
    reason: Optional[str] = None  # Private, not shared with blocked user

# app/database/block_repository.py
class BlockRepository:
    def block_user(self, blocker_id: str, blocked_id: str, reason: str = None) -> BlockEntry:
        ...

    def unblock_user(self, blocker_id: str, blocked_id: str) -> bool:
        ...

    def is_blocked(self, user_a: str, user_b: str) -> bool:
        """Check if either user has blocked the other"""
        ...

    def get_blocked_by(self, user_id: str) -> List[str]:
        """Get list of users who blocked this user"""
        ...

# app/api/matches.py
async def can_match(requester_id: str, offerer_id: str) -> bool:
    """Check if match is allowed (not blocked)"""
    if block_repo.is_blocked(requester_id, offerer_id):
        return False  # Silently fail - don't reveal block
    return True

# app/api/block.py
@router.post("/block/{user_id}")
async def block_user(user_id: str, reason: str = None, current_user=Depends(get_current_user)):
    """Block a user - they won't be able to match or message you"""
    block_repo.block_user(current_user.id, user_id, reason)
    return {"status": "blocked"}

@router.delete("/block/{user_id}")
async def unblock_user(user_id: str, current_user=Depends(get_current_user)):
    """Unblock a user"""
    block_repo.unblock_user(current_user.id, user_id)
    return {"status": "unblocked"}
```

### 5. Auto-Lock on Inactivity (GAP-108)

```python
# frontend/src/services/security_manager.ts
const INACTIVITY_TIMEOUT_MS = 120_000;  // 2 minutes
const SENSITIVE_ACTIONS = [
    "send_message",
    "create_offer",
    "view_sanctuary",
    "vouch_for",
];

class SecurityManager {
    private lastActivity: number = Date.now();
    private locked: boolean = false;
    private lockTimeout: NodeJS.Timeout | null = null;

    constructor() {
        this.startInactivityTimer();
        this.setupEventListeners();
    }

    private startInactivityTimer() {
        this.lockTimeout = setInterval(() => {
            if (Date.now() - this.lastActivity > INACTIVITY_TIMEOUT_MS) {
                this.lock();
            }
        }, 10_000);
    }

    private setupEventListeners() {
        ['click', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => this.recordActivity());
        });
    }

    recordActivity() {
        this.lastActivity = Date.now();
    }

    async lock() {
        this.locked = true;
        // Navigate to lock screen
        window.location.href = '/lock';
    }

    async checkSensitiveAction(action: string): Promise<boolean> {
        if (SENSITIVE_ACTIONS.includes(action)) {
            return await this.verifyPIN();
        }
        return true;
    }

    private async verifyPIN(): Promise<boolean> {
        // Show PIN dialog
        const pin = await showPINDialog();
        return await verifyPINWithServer(pin);
    }
}
```

### 6. Sanctuary Verification Protocol (GAP-109) - P0 PRIORITY

```python
# app/models/sanctuary.py
class SanctuaryVerification(BaseModel):
    space_id: str
    verified_by: List[str]  # At least 2 steward IDs
    verified_at: datetime
    last_check: datetime
    escape_routes: List[str]
    has_buddy_protocol: bool
    successful_uses: int = 0

    @property
    def is_valid(self) -> bool:
        if len(self.verified_by) < 2:
            return False
        if (datetime.utcnow() - self.verified_at).days > 90:
            return False
        return True

# app/services/sanctuary_service.py
class SanctuaryService:
    async def verify_space(
        self,
        space_id: str,
        verifier_id: str,
        escape_routes: List[str],
    ) -> SanctuaryVerification:
        """Add steward verification to a sanctuary space"""
        space = await self.repo.get_space(space_id)

        # Verify the verifier is a steward
        if not await self.is_steward(verifier_id):
            raise HTTPException(403, "Only stewards can verify sanctuary spaces")

        verification = await self.repo.get_verification(space_id)
        if not verification:
            verification = SanctuaryVerification(
                space_id=space_id,
                verified_by=[verifier_id],
                verified_at=datetime.utcnow(),
                escape_routes=escape_routes,
                has_buddy_protocol=True,
            )
        else:
            if verifier_id not in verification.verified_by:
                verification.verified_by.append(verifier_id)
                verification.verified_at = datetime.utcnow()

        await self.repo.save_verification(verification)
        return verification

    async def assign_sanctuary(
        self,
        person_id: str,
        need_severity: str
    ) -> Optional[str]:
        """Assign verified sanctuary to person in need"""
        available = await self.repo.get_verified_sanctuaries()

        # Filter to valid verifications only
        available = [s for s in available if s.verification.is_valid]

        if need_severity == "critical":
            # Only use sanctuaries with 3+ successful prior uses
            available = [s for s in available if s.verification.successful_uses >= 3]

        if not available:
            # Escalate - no safe options
            await self.escalate_sanctuary_need(person_id, need_severity)
            return None

        sanctuary = self.select_best_match(available, person_id)

        # Set up mandatory buddy system
        buddy = await self.assign_buddy(person_id)
        await self.create_checkin_requirement(
            person_id,
            sanctuary.id,
            buddy.id,
            checkin_hours=4,
        )

        return sanctuary.id
```

## Requirements

### SHALL Requirements
- SHALL limit vouches to 5 per month per user
- SHALL require 24h interaction history before vouching
- SHALL allow no-consequence revocation within 48h
- SHALL provide block list preventing matches/messages
- SHALL auto-lock app after 2 minutes inactivity
- SHALL require 2+ steward verification for sanctuaries
- SHALL require buddy system for sanctuary assignments

### MUST Requirements
- MUST silently fail matches with blocked users (don't reveal block)
- MUST NEVER assign unverified sanctuary to critical needs

## Testing

```python
def test_vouch_monthly_limit():
    user = create_user()
    for i in range(5):
        vouch_for(user, create_user())

    # 6th vouch should fail
    result = get_vouch_eligibility(user.id, new_user.id)
    assert result["can_vouch"] == False
    assert "Monthly" in result["reason"]

def test_block_prevents_match():
    alice = create_user()
    bob = create_user()

    block_user(alice.id, bob.id)

    # Bob tries to match Alice's offer
    result = can_match(bob.id, alice.id)
    assert result == False

def test_sanctuary_requires_verification():
    space = create_sanctuary_space()

    # Unverified - should not be assignable
    result = assign_sanctuary(person_id, "critical")
    assert result is None

    # One steward verifies - still not enough
    verify_space(space.id, steward_1.id, escape_routes)
    result = assign_sanctuary(person_id, "critical")
    assert result is None

    # Second steward verifies - now valid
    verify_space(space.id, steward_2.id, escape_routes)
    result = assign_sanctuary(person_id, "low")
    assert result == space.id
```

## Files to Modify/Create

1. `app/models/vouch.py` - Add constants
2. `app/services/web_of_trust_service.py` - Add limit checks
3. `app/api/vouch.py` - Add cooloff logic
4. New: `app/models/block.py`
5. New: `app/database/block_repository.py`
6. New: `app/api/block.py`
7. `frontend/src/services/security_manager.ts` - New
8. `app/models/sanctuary.py` - Add verification model
9. `app/services/sanctuary_service.py` - Add verification logic

## Effort Estimate

- Block list: 2 hours
- Vouch limits: 1 hour
- Auto-lock: 2 hours
- Sanctuary verification: 3 hours
- Testing: 2 hours
- Total: ~10 hours

## Success Criteria

- [ ] Monthly vouch limit enforced
- [ ] 24h cooling period enforced
- [ ] 48h revocation cooloff implemented
- [ ] Block list functional
- [ ] Auto-lock triggers after 2 min inactivity
- [ ] Sanctuary requires 2+ steward verifications
- [ ] Buddy system mandatory for sanctuary assignments
