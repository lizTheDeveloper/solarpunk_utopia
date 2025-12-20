# GAP-56: No CSRF Protection (SECURITY)

**Status**: ✅ IMPLEMENTED
**Priority**: P6 - Production/Security
**Severity**: CRITICAL
**Estimated Effort**: 2-3 hours
**Assigned**: Unclaimed
**Implemented**: 2025-12-19

## Problem Statement

APIs have no CSRF token validation. Combined with `allow_credentials=True` in CORS, this enables Cross-Site Request Forgery attacks where malicious sites can make authenticated requests on behalf of users.

## Attack Scenario

```html
<!-- evil.com -->
<form id="evil" action="https://commune.local/vf/listings/" method="POST">
  <input name="listing_type" value="offer">
  <input name="agent_id" value="victim_user">
  <input name="resource_spec_id" value="stolen_goods">
  <input name="quantity" value="1000">
</form>
<script>document.getElementById('evil').submit();</script>
```

If victim is logged in to commune.local, this auto-submits and creates a fake listing!

## Required Implementation

### MUST Requirements

1. System MUST generate CSRF tokens for authenticated sessions
2. System MUST validate CSRF token on state-changing requests (POST, PUT, PATCH, DELETE)
3. System MUST reject requests with missing/invalid CSRF tokens
4. Tokens MUST be cryptographically random
5. Tokens MUST be tied to user session
6. GET requests MUST NOT require CSRF tokens (idempotent)

### Implementation Options

**Option 1: Double Submit Cookie** (simpler)
```python
from fastapi import Request, HTTPException
import secrets

@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    # Skip for safe methods
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return await call_next(request)

    # Get CSRF token from header
    csrf_token = request.headers.get("X-CSRF-Token")

    # Get CSRF cookie
    csrf_cookie = request.cookies.get("csrf_token")

    if not csrf_token or not csrf_cookie or csrf_token != csrf_cookie:
        raise HTTPException(403, "CSRF token missing or invalid")

    return await call_next(request)

# On login, set CSRF cookie
response.set_cookie(
    "csrf_token",
    value=secrets.token_urlsafe(32),
    httponly=False,  # JavaScript needs to read it
    secure=True,
    samesite="strict"
)
```

**Option 2: Synchronizer Token Pattern** (more secure)
- Store CSRF token in session
- Include token in forms/headers
- Validate server-side

## Files to Modify

- `app/middleware/csrf.py` (new) - CSRF middleware
- `valueflows_node/middleware/csrf.py` (new)
- All service main.py files - add middleware
- `frontend/src/api/client.ts` - add CSRF header

## Frontend Changes

```typescript
// Get CSRF token from cookie
const getCsrfToken = () => {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrf_token='))
    ?.split('=')[1];
};

// Add to all requests
api.interceptors.request.use(config => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = getCsrfToken();
  }
  return config;
});
```

## Success Criteria

- [ ] CSRF tokens generated on login
- [ ] CSRF validation on state-changing requests
- [ ] Invalid tokens rejected with 403
- [ ] Frontend sends tokens correctly
- [ ] Attack scenario fails

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-56`
- OWASP CSRF: https://owasp.org/www-community/attacks/csrf
- FastAPI CSRF: https://fastapi-csrf-protect.readthedocs.io/
