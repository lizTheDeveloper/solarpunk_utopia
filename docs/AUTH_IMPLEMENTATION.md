# Authentication Implementation (GAP-02)

**Status**: Backend ✅ Complete | Frontend 🚧 In Progress
**Date**: December 19, 2025
**Type**: Simple session-based auth (no crypto/blockchain)

## Overview

Simple name-based authentication perfect for workshops and demos. No passwords, no magic links, no JWT complexity - just straightforward session tokens.

## Backend Architecture

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,              -- user:uuid format
    name TEXT NOT NULL,               -- Display name (unique login)
    email TEXT UNIQUE,                -- Optional email
    created_at TEXT NOT NULL,
    last_login TEXT,
    settings TEXT DEFAULT '{}'        -- JSON blob for user preferences
);

-- Sessions table
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,              -- session:uuid format
    user_id TEXT NOT NULL,            -- FK to users.id
    token TEXT UNIQUE NOT NULL,       -- 32-byte urlsafe token
    expires_at TEXT NOT NULL,         -- ISO timestamp (7 days)
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### API Endpoints

#### POST /auth/register
Register new user or login if exists.

**Request:**
```json
{
  "name": "Alice",
  "email": "alice@commune.local"  // optional
}
```

**Response:**
```json
{
  "user": {
    "id": "user:eb7376c8-8632-40da-804d-7de33c7f5b65",
    "name": "Alice",
    "email": null,
    "created_at": "2025-12-19T08:30:20.554239+00:00",
    "last_login": "2025-12-19T08:30:20.554239+00:00",
    "settings": {}
  },
  "token": "LHWzewP8-Bn8L7FopOjY1THfVIagVvLHAovFFrkfAMY",
  "expires_at": "2025-12-26T08:30:20.554825Z"
}
```

#### POST /auth/login
Login existing user (same as register - idempotent).

**Request:**
```json
{
  "name": "Alice"
}
```

**Response:** Same as register

#### GET /auth/me
Get current user info (requires auth).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user:eb7376c8-8632-40da-804d-7de33c7f5b65",
  "name": "Alice",
  "email": null,
  "created_at": "2025-12-19T08:30:20.554239+00:00",
  "last_login": "2025-12-19T08:30:20.554239+00:00",
  "settings": {}
}
```

### Protected Endpoints

All protected endpoints now require:
```
Authorization: Bearer <token>
```

Examples:
- `POST /agents/proposals/{id}/approve` - User ID extracted from token
- `POST /vf/listings` - (Future) Owner set from authenticated user
- `PATCH /vf/listings/{id}` - (Future) Only owner can edit

### Middleware

**`get_current_user()`** - Optional auth dependency
- Returns `User` if valid token provided
- Returns `None` if no token (allows public endpoints)
- Raises `401` if invalid/expired token

**`require_auth()`** - Required auth dependency
- Returns `User` if valid token
- Raises `401` if no token or invalid token
- Use for protected endpoints

## Usage Examples

### From CLI

```bash
# 1. Register/Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}' | jq -r '.token')

# 2. Access protected endpoint
curl -X POST http://localhost:8000/agents/proposals/proposal-123/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "reason": "Looks good!"}'

# 3. Check current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### From Frontend (Future)

```typescript
// 1. Login
const { user, token } = await api.post('/auth/register', { name: 'Alice' });
localStorage.setItem('auth_token', token);

// 2. All subsequent requests include token
api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// 3. Access protected endpoints
await api.post(`/agents/proposals/${id}/approve`, {
  approved: true,
  reason: "Looks good!"
});
```

## Security Considerations

### ✅ What We Have

- Session tokens are cryptographically random (32 bytes)
- Tokens expire after 7 days
- Sessions are deleted on logout
- Expired sessions are automatically rejected
- Protected endpoints verify token on every request
- User ID cannot be spoofed (extracted from session)

### ⚠️ Production TODOs

For production deployment, add:

1. **HTTPS Only** - Tokens must only be sent over HTTPS
2. **Rate Limiting** - Prevent brute force token guessing
3. **CORS Configuration** - Lock down to specific frontend origins
4. **Session Rotation** - Rotate tokens periodically
5. **Account Security** - Add password/email verification for production

## Testing

Run backend tests:
```bash
python test_auth_backend.py
```

Tests cover:
- User registration ✓
- Session token generation ✓
- Token validation ✓
- Protected endpoint access ✓
- Invalid token rejection ✓
- Unauthenticated request rejection ✓

## Files

### Created
- `app/auth/__init__.py`
- `app/auth/models.py` - User, Session, LoginRequest/Response models
- `app/auth/service.py` - AuthService with register/login/token validation
- `app/auth/middleware.py` - get_current_user, require_auth dependencies
- `app/api/auth.py` - Auth API endpoints

### Modified
- `app/database/db.py` - Added users & sessions tables
- `app/main.py` - Added auth router
- `app/api/agents.py` - approve_proposal now uses require_auth()

## Next Steps

### Frontend Implementation (In Progress)

1. **Auth Context** (`frontend/src/contexts/AuthContext.tsx`)
   - Track current user
   - Store token in localStorage
   - Provide login/logout functions

2. **Login Page** (`frontend/src/pages/LoginPage.tsx`)
   - Simple name input
   - Register/login button
   - Auto-redirect after login

3. **API Client Updates** (`frontend/src/api/*.ts`)
   - Include Authorization header
   - Handle 401 responses
   - Redirect to login on auth failure

4. **Protected Routes** (`frontend/src/App.tsx`)
   - Wrap routes that need auth
   - Redirect to login if not authenticated

5. **User-Specific Views**
   - "My Offers" filter
   - "My Needs" filter
   - "Proposals for Me" filter

## Philosophy: No Crypto

This implementation deliberately avoids:
- ❌ Blockchain/cryptocurrency
- ❌ Complex JWT with public/private keys
- ❌ OAuth provider dependencies
- ❌ Magic link email infrastructure

Instead, we have:
- ✅ Simple session tokens
- ✅ Name-based registration (perfect for workshops)
- ✅ Works offline (no email verification needed)
- ✅ Easy to understand and debug
- ✅ Sufficient security for demos and MVPs

For production, this can be upgraded to password auth or magic links without changing the core architecture.
