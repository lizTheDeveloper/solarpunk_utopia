# Fix Steward Verification (GAP-134)

**Status**: Implemented
**Priority**: P0 - CRITICAL (Before Workshop)
**Gaps Fixed**: GAP-134, partial GAP-120
**Created**: 2025-12-20
**Author**: Autonomous Gap Analysis Agent

---

## Problem Statement

15+ API endpoints claim to be "steward-only" but have **zero verification**. Every endpoint has a `# TODO: Check if user is a steward` comment but the verification code is missing.

### Security Impact

Without steward verification, ANY authenticated user can:
- Create memorial funds for living users (ancestor voting abuse)
- Override mycelial strikes (disable abuse protection)
- Whitelist malicious users from abuse detection
- Trigger Saturnalia events (disrupt governance)
- Manage economic withdrawal campaigns
- Approve sanctuary requests (safety risk)
- Access cell-level resilience metrics

This is a **systemic authorization bypass** affecting core security features.

---

## Requirements

### SHALL Requirements

1. **SHALL** create a reusable `require_steward` dependency that checks trust >= 0.9
2. **SHALL** apply `require_steward` to all 15+ affected endpoints
3. **SHALL** return HTTP 403 with clear message when verification fails
4. **SHALL** log all steward verification attempts for audit trail
5. **SHALL** work with existing WebOfTrustService

### MUST NOT Requirements

1. **MUST NOT** hardcode steward trust threshold (use config)
2. **MUST NOT** break existing authenticated endpoints
3. **MUST NOT** require database migrations

---

## Affected Endpoints

| File | Lines | Endpoint | Action |
|------|-------|----------|--------|
| `app/api/mycelial_strike.py` | 284, 314 | POST /strike/override, POST /user/whitelist | Override abuse detection |
| `app/api/saturnalia.py` | 146, 184, 282, 306 | POST /events, PUT /events/{id}/*, POST /configs | Saturnalia management |
| `app/api/ancestor_voting.py` | 149, 282, 328, 390 | POST /memorial-fund, PUT /memorial-fund/*, POST /weight-allocation | Memorial fund management |
| `app/api/economic_withdrawal.py` | 240, 387, 473 | PUT /campaigns/*, POST /bulk-buys, POST /alternatives | Campaign management |
| `app/api/sanctuary.py` | 167 | POST /safe-houses | Sanctuary verification |
| `app/api/resilience_metrics.py` | 334 | GET /cell/{cell_id}/trends | Cell-level trends |

---

## Technical Design

### 1. Create Steward Dependency

```python
# app/api/dependencies/steward.py

from fastapi import Depends, HTTPException
from app.services.web_of_trust_service import WebOfTrustService
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_trust_service

STEWARD_TRUST_THRESHOLD = 0.9  # From FRAUD_ABUSE_SAFETY.md

async def require_steward(
    current_user: dict = Depends(get_current_user),
    trust_service: WebOfTrustService = Depends(get_trust_service)
) -> dict:
    """Verify user has steward-level trust (>= 0.9).

    Raises:
        HTTPException(403): If user trust < 0.9

    Returns:
        Current user dict if verification passes
    """
    user_id = current_user["id"]
    trust_score = trust_service.compute_trust_score(user_id)

    if trust_score.computed_trust < STEWARD_TRUST_THRESHOLD:
        # Log failed attempt for security audit
        logger.warning(
            f"Steward access denied for user {user_id}: "
            f"trust {trust_score.computed_trust:.2f} < {STEWARD_TRUST_THRESHOLD}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Steward access required (trust >= {STEWARD_TRUST_THRESHOLD})"
        )

    # Log successful verification
    logger.info(f"Steward access granted for user {user_id}")
    return current_user
```

### 2. Apply to Endpoints

Replace all instances of:
```python
# TODO: Check if user is a steward
```

With:
```python
current_user: dict = Depends(require_steward),
```

### 3. Example Migration

Before:
```python
@router.post("/memorial-fund")
async def create_memorial_fund(
    request: CreateMemorialFundRequest,
    current_user: dict = Depends(get_current_user),  # Anyone authenticated
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    # TODO: Check if user is a steward or admin
    ...
```

After:
```python
@router.post("/memorial-fund")
async def create_memorial_fund(
    request: CreateMemorialFundRequest,
    current_user: dict = Depends(require_steward),  # Steward-only
    service: AncestorVotingService = Depends(get_ancestor_voting_service)
):
    # Steward verification handled by dependency
    ...
```

---

## Test Scenarios

### WHEN user with trust < 0.9 calls steward endpoint
THEN system SHALL return 403 Forbidden
AND response SHALL include message about steward requirement

### WHEN user with trust >= 0.9 calls steward endpoint
THEN system SHALL allow the request
AND log successful steward verification

### WHEN genesis node calls steward endpoint
THEN system SHALL allow the request (trust = 1.0)

### WHEN unauthenticated user calls steward endpoint
THEN system SHALL return 401 Unauthorized (from auth dependency)

---

## Validation

```bash
# Test steward verification
pytest tests/test_steward_verification.py -v

# Integration test for each affected endpoint
pytest tests/integration/test_steward_endpoints.py -v

# Verify no regression in non-steward endpoints
pytest tests/test_api_endpoints.py -v
```

---

## Rollout Plan

1. Create `require_steward` dependency
2. Add comprehensive tests
3. Apply to all 15+ endpoints
4. Verify existing tests still pass
5. Test with real trust scores in staging

---

## Notes

- This is a **security-critical** fix
- Must be completed before workshop to prevent abuse
- Consider adding `require_genesis` for even higher-privilege operations
