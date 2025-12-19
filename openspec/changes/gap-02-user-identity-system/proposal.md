# GAP-02: User Identity System

**Status**: ✅ Complete (Backend + Frontend)
**Priority**: P1 - Critical (Demo Blocker)
**Estimated Effort**: 1-2 days → Actual: ~4 hours
**Assigned**: Claude Agent 1
**Completed**: December 19, 2025

## Problem Statement

The system has no concept of "who is logged in." Everyone sees everything. No one "owns" their offers. Approval happens with hardcoded user IDs. There's no way to implement "my offers" vs "community offers" or "proposals addressed to me."

This breaks fundamental UX:
- Alice can't see "her" offers
- Bob can't filter proposals that need his approval
- No accountability or ownership
- No privacy controls

## Current Reality

**Locations**:
- Frontend: No auth context, no login UI
- Backend: All endpoints accept user_id as a parameter (trusting client input!)
- Database: user_id fields exist but are populated with hardcoded values like "demo-user"

Examples of the problem:
- `frontend/src/api/agents.ts:76` - `user_id: 'demo-user'` (hardcoded)
- `app/api/agents.py` - No authentication middleware
- `valueflows_node/app/api/vf/listings.py` - No user ownership validation

## Required Implementation

The system SHALL implement a minimal but functional user identity system for MVP demos.

### MUST Requirements

1. The system MUST provide a user registration mechanism
2. The system MUST provide a user login mechanism
3. The system MUST maintain user session state
4. The system MUST attach user identity to all API requests
5. The system MUST scope offer/need creation to authenticated users
6. The system MUST scope approval actions to authenticated users
7. The system MUST provide a "current user" context in frontend

### SHOULD Requirements

1. The system SHOULD use magic link email authentication (passwordless) for MVP
2. The system SHOULD support local-only user creation (no email) for development
3. The system SHOULD provide user profile management
4. The system SHOULD implement "remember me" functionality

### MAY Requirements

1. The system MAY support OAuth providers (Google, GitHub) in future
2. The system MAY support multi-factor authentication in future

## Scenarios

### WHEN a new user visits the app

**GIVEN**: No existing session

**WHEN**: User opens the app

**THEN**:
1. App MUST redirect to login/registration page
2. User MUST see options: "Sign up" or "Log in"
3. UI MUST be mobile-friendly and accessible

### WHEN user registers with email (magic link)

**GIVEN**: User enters email "alice@commune.local"

**WHEN**: User clicks "Sign up with email"

**THEN**:
1. System MUST send magic link to email
2. System MUST show "Check your email" confirmation
3. Email link MUST contain single-use token
4. Clicking link MUST create user account if not exists
5. Clicking link MUST log user in
6. User MUST be redirected to app homepage

### WHEN user registers locally (dev mode)

**GIVEN**: `AUTH_MODE=local` environment variable

**WHEN**: User enters name "Alice"

**THEN**:
1. System MUST create user with ID derived from name
2. System MUST log user in immediately
3. No email verification required

### WHEN authenticated user creates an offer

**GIVEN**: Alice is logged in

**WHEN**: Alice creates an offer for tomatoes

**THEN**:
1. API request MUST include Alice's user_id from session
2. Offer MUST be stored with Alice as the owner (agent_id)
3. Offer MUST appear in "My Offers" view
4. Other users MUST see it in "Community Offers"

### WHEN user approves a proposal

**GIVEN**:
- Bob is logged in
- Proposal requires Bob's approval

**WHEN**: Bob clicks "Approve"

**THEN**:
1. API request MUST use Bob's user_id from session (not hardcoded)
2. System MUST verify Bob is in the required_approvals list
3. System MUST reject if Bob is not authorized
4. Approval MUST be recorded with Bob's identity

### WHEN unauthenticated user tries to access protected endpoint

**GIVEN**: No session token

**WHEN**: Request is made to `POST /vf/listings/`

**THEN**:
1. Request MUST be rejected with 401 Unauthorized
2. Response MUST include clear error message
3. Frontend MUST redirect to login page

## Architecture

### Components to Create

1. **Authentication Service** (`app/auth/`)
   - `auth_service.py` - Core auth logic
   - `models.py` - User model
   - `repository.py` - User database operations
   - `middleware.py` - FastAPI auth middleware
   - `magic_link.py` - Magic link generation/verification

2. **Frontend Auth** (`frontend/src/auth/`)
   - `AuthContext.tsx` - React context for current user
   - `useAuth.ts` - Hook for auth state
   - `LoginPage.tsx` - Login/registration UI
   - `ProtectedRoute.tsx` - Route guard component

3. **Database**
   - Users table (id, email, name, created_at, last_login)
   - Sessions table (id, user_id, token, expires_at)
   - Magic links table (id, email, token, expires_at, used)

### API Changes

All protected endpoints MUST accept:
- Header: `Authorization: Bearer <token>`
- Extract user_id from token via middleware
- Populate `request.state.user` with current user

Endpoints to protect:
- `POST /vf/listings/` (create offer/need)
- `PATCH /vf/listings/{id}` (edit own listings)
- `DELETE /vf/listings/{id}` (delete own listings)
- `POST /agents/proposals/{id}/approve` (approve proposals)
- All exchange-related endpoints

## Files to Create

### Backend
- `app/auth/auth_service.py`
- `app/auth/models.py`
- `app/auth/repository.py`
- `app/auth/middleware.py`
- `app/auth/magic_link.py`
- `app/database/migrations/add_users_tables.sql`
- `valueflows_node/app/api/auth.py` - Auth endpoints

### Frontend
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/components/ProtectedRoute.tsx`

### Configuration
- `.env` - Add `AUTH_MODE`, `JWT_SECRET`, `SMTP_*` variables

## Files to Modify

### Backend
- `app/main.py` - Add auth middleware
- `app/api/agents.py` - Remove hardcoded user_id, use `request.state.user.id`
- `valueflows_node/app/api/vf/listings.py` - Add auth checks
- `valueflows_node/app/api/vf/exchanges.py` - Add auth checks

### Frontend
- `frontend/src/App.tsx` - Wrap with AuthProvider, add login route
- `frontend/src/api/agents.ts` - Remove hardcoded user_id, use auth context
- `frontend/src/api/valueflows.ts` - Add auth headers
- `frontend/src/pages/OffersPage.tsx` - Add "My Offers" filter
- `frontend/src/pages/AgentsPage.tsx` - Filter proposals by current user

## Testing Requirements

1. **Unit tests**:
   - Magic link generation/validation
   - JWT token creation/verification
   - User repository CRUD operations

2. **Integration tests**:
   - Full registration flow
   - Full login flow
   - Token refresh
   - Logout

3. **E2E tests**:
   - User registers → creates offer → sees it in "My Offers"
   - User logs out → can't access protected pages → logs in → sees own data
   - User tries to edit someone else's offer → receives 403

## Success Criteria

- [ ] Users can register and log in
- [ ] User identity persists across page reloads
- [ ] All API calls include user context
- [ ] Offers are scoped to owners
- [ ] Proposals are filtered by user
- [ ] Unauthorized access is blocked
- [ ] All tests pass

## Dependencies

- Email service for magic links (can mock for MVP)
- JWT library for token generation
- Secure secret management for JWT_SECRET

## Alternatives Considered

1. **No auth (current state)** - Rejected: Breaks all ownership UX
2. **Basic password auth** - Considered: Less secure, worse UX than magic link
3. **OAuth only** - Rejected: Requires network, doesn't work offline
4. **Magic link (chosen)** - Best balance of security and UX

## Security Considerations

1. JWT secrets MUST be cryptographically random
2. Magic link tokens MUST be single-use
3. Magic links MUST expire (15-minute TTL recommended)
4. Passwords MUST be hashed with bcrypt if password auth is added later
5. Sessions MUST have reasonable TTL (7 days recommended)
6. HTTPS MUST be enforced in production

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-02`
- Related gaps: GAP-03 (Community Entity), GAP-17 (My Stuff View)
