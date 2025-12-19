# Tasks: GAP-02 User Identity System

## Phase 1: Database Schema (2 hours)

### Task 1.1: Create users table
**File**: `app/database/migrations/001_add_users.sql` (new)
**Estimated**: 30 minutes

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    settings JSON DEFAULT '{}'
);

CREATE INDEX idx_users_email ON users(email);
```

### Task 1.2: Create sessions table
**File**: Same migration file
**Estimated**: 30 minutes

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

### Task 1.3: Create magic_links table (optional for MVP)
**File**: Same migration file
**Estimated**: 30 minutes

```sql
CREATE TABLE magic_links (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_magic_links_token ON magic_links(token);
```

### Task 1.4: Run migrations
**File**: `app/database/db.py`
**Estimated**: 30 minutes

- Add migration runner if not exists
- Update `init_db()` to run migrations
- Test migration on clean database

## Phase 2: Auth Service Backend (4 hours)

### Task 2.1: Create User model
**File**: `app/auth/models.py` (new)
**Estimated**: 30 minutes

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    settings: dict = {}

class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    name: str

class Session(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: datetime
```

### Task 2.2: Create UserRepository
**File**: `app/auth/repository.py` (new)
**Estimated**: 1 hour

Methods:
- `create_user(user_data: UserCreate) -> User`
- `get_user_by_id(user_id: str) -> Optional[User]`
- `get_user_by_email(email: str) -> Optional[User]`
- `update_last_login(user_id: str)`
- `create_session(user_id: str, ttl_days: int = 7) -> Session`
- `get_session_by_token(token: str) -> Optional[Session]`
- `delete_session(token: str)`

### Task 2.3: Create AuthService
**File**: `app/auth/auth_service.py` (new)
**Estimated**: 1.5 hours

```python
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.jwt_secret = os.getenv("JWT_SECRET")

    async def register_local(self, name: str) -> Dict[str, Any]:
        """Create user account (dev mode)"""
        user_id = self._generate_user_id(name)
        user = await self.user_repo.create_user(
            UserCreate(name=name)
        )
        session = await self.user_repo.create_session(user.id)
        return {
            "user": user,
            "token": session.token
        }

    async def login_with_magic_link(self, email: str) -> bool:
        """Send magic link email (MVP: log to console)"""
        # TODO: Implement email sending
        # For MVP, just log the link
        token = secrets.token_urlsafe(32)
        link = f"http://localhost/auth/verify?token={token}"
        print(f"Magic link for {email}: {link}")
        return True

    async def verify_magic_link(self, token: str) -> Dict[str, Any]:
        """Verify magic link and create session"""
        # Verify token, get/create user, create session
        pass

    def create_jwt(self, user_id: str) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt(self, token: str) -> Optional[str]:
        """Verify JWT and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
```

### Task 2.4: Create auth middleware
**File**: `app/auth/middleware.py` (new)
**Estimated**: 1 hour

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if request.url.path in ["/auth/login", "/auth/register", "/health"]:
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = auth_header.split(" ")[1]

        # Verify token and get user
        auth_service = request.app.state.auth_service
        user_id = auth_service.verify_jwt(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await auth_service.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Attach user to request
        request.state.user = user

        return await call_next(request)
```

## Phase 3: Auth API Endpoints (2 hours)

### Task 3.1: Create auth endpoints
**File**: `valueflows_node/app/api/auth.py` (new) OR `app/api/auth.py`
**Estimated**: 2 hours

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register/local")
async def register_local(
    data: dict,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register user without email (dev mode)"""
    result = await auth_service.register_local(data["name"])
    return result

@router.post("/login/magic-link")
async def send_magic_link(
    data: dict,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Send magic link to email"""
    await auth_service.login_with_magic_link(data["email"])
    return {"message": "Check your email"}

@router.get("/verify")
async def verify_magic_link(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify magic link and return session token"""
    result = await auth_service.verify_magic_link(token)
    return result

@router.get("/me")
async def get_current_user(request: Request):
    """Get currently authenticated user"""
    return request.state.user

@router.post("/logout")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout (invalidate session)"""
    token = request.headers.get("Authorization").split(" ")[1]
    await auth_service.user_repo.delete_session(token)
    return {"message": "Logged out"}
```

## Phase 4: Update Existing Endpoints (2 hours)

### Task 4.1: Update agents API
**File**: `app/api/agents.py`
**Estimated**: 1 hour

Changes:
- Remove hardcoded user_ids
- Use `request.state.user.id` instead
- Add authentication dependency

Example:
```python
@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: str,
    approval_data: ApprovalData,
    request: Request,
    tracker: ApprovalTracker = Depends(get_approval_tracker)
):
    # OLD: user_id from request body (untrusted!)
    # NEW: user_id from authenticated session
    user_id = request.state.user.id

    approval_data.user_id = user_id  # Override with authenticated user
    result = await tracker.approve_proposal(proposal_id, approval_data)
    return result
```

### Task 4.2: Update VF listings API
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 1 hour

Changes:
- Add ownership validation (user can only edit/delete own listings)
- Auto-populate agent_id from request.state.user.id
- Return 403 for unauthorized operations

## Phase 5: Frontend Auth (4 hours)

### Task 5.1: Create AuthContext
**File**: `frontend/src/contexts/AuthContext.tsx` (new)
**Estimated**: 1 hour

```typescript
interface User {
  id: string;
  email?: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string) => Promise<void>;
  loginLocal: (name: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export const AuthProvider: React.FC = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('auth_token')
  );

  // Auto-load user on mount if token exists
  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  // ... implementation
};
```

### Task 5.2: Create useAuth hook
**File**: `frontend/src/hooks/useAuth.ts` (new)
**Estimated**: 30 minutes

```typescript
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Task 5.3: Create LoginPage
**File**: `frontend/src/pages/LoginPage.tsx` (new)
**Estimated**: 1.5 hours

UI elements:
- Local login form (name input + submit)
- Magic link form (email input + submit)
- Toggle between modes
- Loading states
- Error messages

### Task 5.4: Create ProtectedRoute component
**File**: `frontend/src/components/ProtectedRoute.tsx` (new)
**Estimated**: 30 minutes

```typescript
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
};
```

### Task 5.5: Update App.tsx
**File**: `frontend/src/App.tsx`
**Estimated**: 30 minutes

- Wrap app with AuthProvider
- Add /login route
- Wrap existing routes with ProtectedRoute

### Task 5.6: Update API clients
**File**: `frontend/src/api/agents.ts`, `frontend/src/api/valueflows.ts`
**Estimated**: 1 hour

- Add Authorization header to all requests
- Remove hardcoded user_id values
- Handle 401 errors (redirect to login)

## Phase 6: Testing (3 hours)

### Task 6.1: Backend unit tests
**Estimated**: 1 hour

- Test JWT creation/verification
- Test user repository operations
- Test session creation/validation

### Task 6.2: API integration tests
**Estimated**: 1 hour

- Test full registration flow
- Test login flow
- Test protected endpoints reject unauthorized requests
- Test token expiration

### Task 6.3: Frontend tests
**Estimated**: 1 hour

- Test AuthContext state management
- Test login form submission
- Test ProtectedRoute redirects
- Test logout clears state

## Phase 7: Configuration & Deployment (1 hour)

### Task 7.1: Update environment config
**File**: `.env.example`
**Estimated**: 15 minutes

Add:
```
AUTH_MODE=local  # or 'magic_link'
JWT_SECRET=generate-random-secret-here
SESSION_TTL_DAYS=7

# For magic link mode:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=noreply@commune.local
```

### Task 7.2: Update docker-compose
**File**: `docker-compose.yml`
**Estimated**: 15 minutes

- Pass auth environment variables to services
- Generate JWT_SECRET if not set

### Task 7.3: Documentation
**File**: `docs/AUTHENTICATION.md` (new)
**Estimated**: 30 minutes

Document:
- How to set up auth (local vs magic link)
- Environment variables
- API endpoints
- Frontend integration

## Verification Checklist

- [ ] Users table created and accessible
- [ ] User can register locally (dev mode)
- [ ] User can log in with magic link (production mode)
- [ ] JWT tokens are generated and verified correctly
- [ ] All API requests include user context
- [ ] Offers are created with correct user ownership
- [ ] User can only edit/delete own offers
- [ ] Proposals show correct "addressed to me" filtering
- [ ] Logout clears session
- [ ] Page reload preserves auth state
- [ ] All tests pass
- [ ] Documentation complete

## Estimated Total Time

- Phase 1 (Database): 2 hours
- Phase 2 (Auth Service): 4 hours
- Phase 3 (API Endpoints): 2 hours
- Phase 4 (Update Existing): 2 hours
- Phase 5 (Frontend): 4 hours
- Phase 6 (Testing): 3 hours
- Phase 7 (Config/Docs): 1 hour

**Total: 18 hours (~2-3 days for one developer)**

## Dependencies

- PyJWT library (`pip install pyjwt`)
- Email service or console logging for magic links
- React Router for frontend routing
- localStorage for token persistence
