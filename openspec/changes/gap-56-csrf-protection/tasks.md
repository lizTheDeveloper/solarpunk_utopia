# Tasks: GAP-56 CSRF Protection (SECURITY)

## Phase 1: Implement CSRF Middleware (1-1.5 hours)

### Task 1.1: Create CSRF token generator
**File**: `app/middleware/csrf.py` (new file)
**Estimated**: 20 minutes

```python
import secrets
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

def generate_csrf_token() -> str:
    """Generate cryptographically secure CSRF token"""
    return secrets.token_urlsafe(32)

def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Extract CSRF token from request header"""
    return request.headers.get("X-CSRF-Token") or request.headers.get("X-Csrf-Token")

def get_csrf_token_from_cookie(request: Request) -> Optional[str]:
    """Extract CSRF token from cookie"""
    return request.cookies.get("csrf_token")
```

**Acceptance criteria**:
- Generates 32-byte URL-safe tokens
- Case-insensitive header lookup
- Cookie extraction works
- No hardcoded secrets

### Task 1.2: Create CSRF validation middleware
**File**: `app/middleware/csrf.py`
**Estimated**: 40 minutes

```python
class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double Submit Cookie CSRF protection.

    Safe methods (GET, HEAD, OPTIONS) bypass validation.
    State-changing methods (POST, PUT, PATCH, DELETE) require matching token.
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app, exempt_paths: set[str] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or set()

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF for exempt paths (e.g., webhooks)
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Get tokens from header and cookie
        csrf_header = get_csrf_token_from_request(request)
        csrf_cookie = get_csrf_token_from_cookie(request)

        # Validate tokens match
        if not csrf_header:
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing from request headers"
            )

        if not csrf_cookie:
            raise HTTPException(
                status_code=403,
                detail="CSRF token missing from cookies"
            )

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(csrf_header, csrf_cookie):
            raise HTTPException(
                status_code=403,
                detail="CSRF token mismatch"
            )

        # Token valid, proceed with request
        return await call_next(request)
```

**Acceptance criteria**:
- Safe methods bypass validation
- Unsafe methods require token
- Tokens compared in constant time
- Helpful error messages
- Exempt paths configurable

### Task 1.3: Create token refresh endpoint
**File**: `app/api/auth.py` (new or existing)
**Estimated**: 30 minutes

```python
from fastapi import APIRouter, Response
from app.middleware.csrf import generate_csrf_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/csrf-token")
async def get_csrf_token(response: Response):
    """
    Generate and set CSRF token cookie.

    Called on:
    - Initial page load
    - Login
    - Token expiration
    """
    token = generate_csrf_token()

    # Set cookie (client will read and include in requests)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # JavaScript needs to read it
        secure=True,  # HTTPS only in production
        samesite="strict",  # Prevent cross-site sending
        max_age=3600 * 24,  # 24 hours
    )

    return {"csrf_token": token}
```

**Acceptance criteria**:
- Generates new token on request
- Sets secure cookie
- Returns token in response body
- Cookie attributes correct

## Phase 2: Integrate Middleware into Services (30-45 minutes)

### Task 2.1: Add middleware to main app
**File**: `app/main.py`
**Estimated**: 15 minutes

```python
from app.middleware.csrf import CSRFMiddleware

app = FastAPI()

# Add CSRF protection
app.add_middleware(
    CSRFMiddleware,
    exempt_paths={
        "/docs",  # Swagger UI
        "/openapi.json",  # OpenAPI spec
        "/health",  # Health check
        # Add webhook endpoints if needed
    }
)
```

**Acceptance criteria**:
- Middleware registered
- Exempt paths configured
- Health checks still work
- Swagger UI accessible

### Task 2.2: Add middleware to ValueFlows node
**File**: `valueflows_node/app/main.py`
**Estimated**: 15 minutes

```python
from valueflows_node.middleware.csrf import CSRFMiddleware

app = FastAPI()

app.add_middleware(
    CSRFMiddleware,
    exempt_paths={
        "/docs",
        "/openapi.json",
        "/health",
    }
)
```

**Acceptance criteria**:
- Same as Task 2.1
- VF API protected

### Task 2.3: Copy middleware to other services
**Files**: All service `main.py` files
**Estimated**: 15 minutes

Copy CSRF middleware to:
- `discovery_search/middleware/csrf.py`
- `file_chunking/middleware/csrf.py`
- `mesh_network/bridge_node/middleware/csrf.py`

Add to each service's `main.py`.

**Acceptance criteria**:
- All services protected
- Consistent configuration
- No duplicate code issues

## Phase 3: Frontend Integration (1 hour)

### Task 3.1: Create CSRF token utility
**File**: `frontend/src/utils/csrf.ts` (new file)
**Estimated**: 20 minutes

```typescript
/**
 * Get CSRF token from cookie
 */
export const getCsrfToken = (): string | null => {
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
};

/**
 * Fetch fresh CSRF token from server
 */
export const refreshCsrfToken = async (): Promise<string> => {
  const response = await fetch('/auth/csrf-token', {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch CSRF token');
  }

  const data = await response.json();
  return data.csrf_token;
};

/**
 * Ensure CSRF token is available
 */
export const ensureCsrfToken = async (): Promise<string> => {
  let token = getCsrfToken();

  if (!token) {
    token = await refreshCsrfToken();
  }

  return token;
};
```

**Acceptance criteria**:
- Extracts token from cookie
- Fetches new token if missing
- Handles errors gracefully
- TypeScript types correct

### Task 3.2: Add CSRF header to API client
**File**: `frontend/src/api/client.ts`
**Estimated**: 20 minutes

```typescript
import axios from 'axios';
import { getCsrfToken, ensureCsrfToken } from '@/utils/csrf';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,  // Send cookies
});

// Add CSRF token to state-changing requests
api.interceptors.request.use(async (config) => {
  const method = config.method?.toLowerCase();

  // Add CSRF token for unsafe methods
  if (['post', 'put', 'patch', 'delete'].includes(method || '')) {
    const token = getCsrfToken();

    if (token) {
      config.headers['X-CSRF-Token'] = token;
    } else {
      // Token missing - fetch it
      const newToken = await ensureCsrfToken();
      config.headers['X-CSRF-Token'] = newToken;
    }
  }

  return config;
});

// Handle CSRF errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 403 && error.response?.data?.detail?.includes('CSRF')) {
      // CSRF token invalid - refresh and retry
      await ensureCsrfToken();

      // Retry original request
      return api.request(error.config);
    }

    return Promise.reject(error);
  }
);

export default api;
```

**Acceptance criteria**:
- CSRF header added automatically
- Safe methods don't get header
- Missing token triggers refresh
- 403 CSRF errors trigger retry
- Max one retry per request

### Task 3.3: Initialize CSRF on app load
**File**: `frontend/src/App.tsx` or `main.tsx`
**Estimated**: 20 minutes

```typescript
import { useEffect } from 'react';
import { ensureCsrfToken } from '@/utils/csrf';

function App() {
  useEffect(() => {
    // Fetch CSRF token on app initialization
    ensureCsrfToken().catch((error) => {
      console.error('Failed to initialize CSRF token:', error);
    });
  }, []);

  return (
    // ... app content
  );
}
```

**Acceptance criteria**:
- Token fetched on app load
- Errors logged but don't crash app
- Token available before first API call

## Phase 4: Testing (1-1.5 hours)

### Task 4.1: Backend CSRF tests
**File**: `tests/security/test_csrf.py` (new)
**Estimated**: 45 minutes

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_request_works_without_csrf(client: AsyncClient):
    """GET requests don't require CSRF token"""
    response = await client.get("/vf/listings/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_post_request_requires_csrf(client: AsyncClient):
    """POST requests require CSRF token"""
    response = await client.post("/vf/listings/", json={
        "listing_type": "offer",
        "resource_spec_id": "food-123",
        "agent_id": "user-456",
        "quantity": 5
    })
    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]

@pytest.mark.asyncio
async def test_post_with_valid_csrf_succeeds(client: AsyncClient):
    """POST with valid CSRF token succeeds"""
    # Get CSRF token
    token_response = await client.post("/auth/csrf-token")
    token = token_response.json()["csrf_token"]

    # Make request with token
    response = await client.post(
        "/vf/listings/",
        json={
            "listing_type": "offer",
            "resource_spec_id": "food-123",
            "agent_id": "user-456",
            "quantity": 5
        },
        headers={"X-CSRF-Token": token},
        cookies={"csrf_token": token}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_post_with_mismatched_csrf_fails(client: AsyncClient):
    """POST with mismatched CSRF tokens fails"""
    response = await client.post(
        "/vf/listings/",
        json={"listing_type": "offer", "quantity": 5},
        headers={"X-CSRF-Token": "token1"},
        cookies={"csrf_token": "token2"}  # Mismatch!
    )
    assert response.status_code == 403
    assert "mismatch" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_csrf_exempt_paths(client: AsyncClient):
    """Exempt paths don't require CSRF"""
    response = await client.get("/health")
    assert response.status_code == 200

    response = await client.get("/docs")
    assert response.status_code == 200
```

**Acceptance criteria**:
- All test cases pass
- Safe methods work without token
- Unsafe methods require token
- Token mismatch rejected
- Exempt paths work

### Task 4.2: Frontend CSRF tests
**File**: `frontend/src/utils/csrf.test.ts` (new)
**Estimated**: 30 minutes

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getCsrfToken, refreshCsrfToken, ensureCsrfToken } from './csrf';

describe('CSRF utilities', () => {
  beforeEach(() => {
    // Clear cookies
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC';
  });

  it('getCsrfToken returns null when no cookie', () => {
    expect(getCsrfToken()).toBeNull();
  });

  it('getCsrfToken extracts token from cookie', () => {
    document.cookie = 'csrf_token=test-token-123';
    expect(getCsrfToken()).toBe('test-token-123');
  });

  it('refreshCsrfToken fetches new token', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'new-token' }),
      } as Response)
    );

    const token = await refreshCsrfToken();
    expect(token).toBe('new-token');
  });

  it('ensureCsrfToken uses existing token', async () => {
    document.cookie = 'csrf_token=existing-token';
    const token = await ensureCsrfToken();
    expect(token).toBe('existing-token');
  });

  it('ensureCsrfToken fetches when missing', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ csrf_token: 'fetched-token' }),
      } as Response)
    );

    const token = await ensureCsrfToken();
    expect(token).toBe('fetched-token');
  });
});
```

**Acceptance criteria**:
- All tests pass
- Cookie parsing works
- Token fetching works
- Fallback logic correct

### Task 4.3: E2E attack simulation
**File**: `tests/e2e/test_csrf_attack.py` (new)
**Estimated**: 15 minutes

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_csrf_attack_blocked():
    """Simulate cross-site request forgery attack"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # User logs in to legitimate site
        await page.goto("http://localhost:5173")
        await page.fill("#username", "testuser")
        await page.click("#login")

        # Attacker tries to make request from evil.com
        # (Simulate by making request without CSRF token)
        response = await page.evaluate("""
            fetch('http://localhost:8000/vf/listings/', {
                method: 'POST',
                credentials: 'include',  // Send auth cookies
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    listing_type: 'offer',
                    resource_spec_id: 'stolen',
                    agent_id: 'victim',
                    quantity: 1000
                })
            }).then(r => r.status)
        """)

        # Should be blocked with 403
        assert response == 403

        await browser.close()
```

**Acceptance criteria**:
- Attack is blocked
- User credentials don't bypass CSRF
- Only requests with valid token succeed

## Phase 5: Documentation & Monitoring (30 minutes)

### Task 5.1: Update security documentation
**File**: `docs/SECURITY.md`
**Estimated**: 15 minutes

Add section:
```markdown
## CSRF Protection

All state-changing API requests (POST, PUT, PATCH, DELETE) require CSRF tokens.

### How it works
1. Client fetches CSRF token via `/auth/csrf-token`
2. Server sets token in cookie
3. Client includes token in `X-CSRF-Token` header
4. Server validates header matches cookie

### For frontend developers
The API client automatically handles CSRF tokens. No manual intervention needed.

### For backend developers
Exempt paths can be configured in middleware initialization:
- Webhooks
- Public APIs
- Health checks

### Attack mitigation
- Prevents cross-site request forgery
- Uses double-submit cookie pattern
- Constant-time comparison prevents timing attacks
```

**Acceptance criteria**:
- Clear explanation
- Usage instructions
- Security guarantees documented

### Task 5.2: Add monitoring/logging
**File**: `app/middleware/csrf.py`
**Estimated**: 15 minutes

```python
import logging

logger = logging.getLogger(__name__)

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # ... existing code ...

        # Log CSRF failures
        if not csrf_header:
            logger.warning(
                f"CSRF token missing from {request.method} {request.url.path}",
                extra={
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                }
            )
            raise HTTPException(403, "CSRF token missing from request headers")

        if not secrets.compare_digest(csrf_header, csrf_cookie):
            logger.warning(
                f"CSRF token mismatch for {request.method} {request.url.path}",
                extra={
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                }
            )
            raise HTTPException(403, "CSRF token mismatch")

        return await call_next(request)
```

**Acceptance criteria**:
- CSRF failures logged
- IP and user agent captured
- Log level appropriate (WARNING)
- No sensitive data logged

## Verification Checklist

Before marking this as complete:

- [ ] CSRF middleware implemented
- [ ] Token generation cryptographically secure
- [ ] Safe methods (GET/HEAD/OPTIONS) bypass validation
- [ ] Unsafe methods require valid token
- [ ] Constant-time comparison used
- [ ] Frontend automatically includes token
- [ ] Token refresh on 403 CSRF error
- [ ] All tests pass
- [ ] E2E attack simulation blocked
- [ ] Exempt paths configured
- [ ] Documentation updated
- [ ] Monitoring/logging added
- [ ] No false positives in production
- [ ] Performance acceptable (< 1ms overhead)

## Estimated Total Time

- Phase 1: 1.5 hours (middleware)
- Phase 2: 45 minutes (integration)
- Phase 3: 1 hour (frontend)
- Phase 4: 1.5 hours (testing)
- Phase 5: 30 minutes (docs)

**Total: 2-3 hours**

## Dependencies

- FastAPI/Starlette middleware support
- Frontend can read cookies
- Frontend can set headers
- Sessions/cookies enabled

## Security Considerations

- Tokens must be cryptographically random
- SameSite=Strict prevents cross-site cookie sending
- Secure=True for HTTPS-only in production
- HttpOnly=False allows JavaScript to read token
- Constant-time comparison prevents timing attacks
- Token rotation on login/logout recommended

## Production Rollout

1. Deploy to staging
2. Test with real traffic (1 week)
3. Monitor for false positives
4. Adjust exempt paths as needed
5. Deploy to production
6. Monitor CSRF failure rates
7. Set up alerts for unusual patterns
