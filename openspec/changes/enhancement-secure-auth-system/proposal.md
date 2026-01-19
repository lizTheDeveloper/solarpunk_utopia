# Enhancement: Secure Authentication System with Handle-Based Auth, Passwords, and 2FA

**Status**: Draft
**Priority**: High
**Type**: Enhancement - Security & UX Improvement
**Source**: User feedback + Security best practices

## Problem Statement

The current authentication system uses simple name-based auth without passwords, lacks 2FA, and doesn't properly namespace users to their nodes. This creates security vulnerabilities and poor UX for distributed mesh networks.

**Current Issues**:
1. **Name-based auth**: Anyone can claim to be "Alice" - no verification
2. **No passwords**: Authentication has no security layer
3. **No node namespacing**: Users aren't scoped to their mesh node
4. **No 2FA**: No second factor authentication for sensitive operations
5. **Weak identity**: Names are not unique globally

**Impact**:
- Users can be impersonated easily
- No protection against unauthorized access
- Identity collisions across nodes
- Cannot meet security requirements for sensitive use cases (medical, financial)
- Poor trust model for mesh network

## Requirements

### MUST

- Users MUST have globally unique handles (like @username@node-id)
- Passwords MUST be hashed using bcrypt or Argon2
- Users MUST be namespaced to their node ID
- Sensitive operations MUST support 2FA verification
- 2FA MUST support both TOTP (authenticator apps) and WebAuthn/passkeys
- Password reset MUST be possible via trusted recovery methods
- Session tokens MUST expire and be revocable

### SHOULD

- Handles SHOULD be portable (exportable with private key)
- 2FA SHOULD be optional but strongly encouraged
- WebAuthn/passkeys SHOULD be preferred over TOTP when available
- Password strength SHOULD be enforced (min length, complexity)
- Account recovery SHOULD support trusted contacts
- Login attempts SHOULD be rate-limited

### MAY

- Biometric auth MAY be supported on capable devices
- Decentralized identity (DID) MAY be integrated
- Social recovery MAY allow friend-based account recovery
- Hardware security keys MAY be supported for high-security accounts

## Proposed Architecture

### 1. Handle Format: @username@node-id

```
@alice@mesh-node-abc123
@bob@mesh-node-xyz789
@charlie@mesh-node-abc123  # Same node as Alice
```

**Benefits**:
- Globally unique across entire mesh network
- Clear node ownership
- Portable to other nodes if user moves
- Familiar format (like email or Mastodon)

### 2. User Model with Security Fields

```python
# app/models/user.py
from datetime import datetime
from typing import Optional, List
import bcrypt
import pyotp

class User(Base):
    __tablename__ = "users"

    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str  # @username@node-id (unique globally)
    username: str  # Just "alice" (for display)
    node_id: str  # Which mesh node they belong to
    display_name: Optional[str] = None

    # Authentication
    password_hash: str  # bcrypt hash
    password_changed_at: datetime

    # 2FA
    totp_secret: Optional[str] = None  # For authenticator apps
    totp_enabled: bool = False
    backup_codes: Optional[List[str]] = None  # One-time recovery codes

    # WebAuthn/Passkeys
    webauthn_credentials: List = []  # JSON list of registered credentials

    # Session management
    active_sessions: List = []  # JSON list of active session tokens
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    # Security
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None  # Account lockout
    requires_password_change: bool = False

    # Recovery
    recovery_email: Optional[str] = None  # For password reset
    trusted_contacts: List[str] = []  # User IDs who can help recover account

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Methods
    def set_password(self, password: str):
        """Hash and store password"""
        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters")
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.password_changed_at = datetime.utcnow()

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def enable_totp(self) -> str:
        """Generate TOTP secret and return QR code data"""
        self.totp_secret = pyotp.random_base32()
        self.totp_enabled = False  # User must verify first
        totp = pyotp.TOTP(self.totp_secret)
        return totp.provisioning_uri(
            name=self.handle,
            issuer_name="Solarpunk Mesh"
        )

    def verify_totp(self, code: str) -> bool:
        """Verify TOTP code"""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code, valid_window=1)

    def generate_backup_codes(self) -> List[str]:
        """Generate one-time backup codes for recovery"""
        codes = [pyotp.random_base32()[:8] for _ in range(10)]
        # Store hashed versions
        self.backup_codes = [bcrypt.hashpw(c.encode(), bcrypt.gensalt()).decode() for c in codes]
        return codes  # Return plain codes to show user once

    def use_backup_code(self, code: str) -> bool:
        """Use and invalidate a backup code"""
        if not self.backup_codes:
            return False
        for idx, hashed in enumerate(self.backup_codes):
            if bcrypt.checkpw(code.encode(), hashed.encode()):
                self.backup_codes.pop(idx)
                return True
        return False
```

### 3. Registration Flow

```python
# app/api/auth.py
from pydantic import BaseModel, validator
import re

class RegistrationRequest(BaseModel):
    username: str  # "alice" (will become @alice@node-id)
    password: str
    password_confirm: str
    display_name: Optional[str] = None
    recovery_email: Optional[str] = None

    @validator('username')
    def username_valid(cls, v):
        if not re.match(r'^[a-z0-9_-]{3,20}$', v):
            raise ValueError(
                "Username must be 3-20 characters, lowercase letters, numbers, hyphens, underscores only"
            )
        return v

    @validator('password')
    def password_strong(cls, v):
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError("Passwords do not match")
        return v


@router.post("/register", response_model=User)
async def register(
    data: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""

    # Get current node ID
    node_config = await get_node_config()
    node_id = node_config.node_id

    # Create handle: @username@node-id
    handle = f"@{data.username}@{node_id}"

    # Check if handle already exists
    existing = db.query(User).filter(User.handle == handle).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{data.username}' already taken on this node"
        )

    # Create user
    user = User(
        username=data.username,
        handle=handle,
        node_id=node_id,
        display_name=data.display_name or data.username,
        recovery_email=data.recovery_email
    )

    user.set_password(data.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"New user registered: {handle}")

    return user
```

### 4. Login Flow with 2FA

```python
class LoginRequest(BaseModel):
    handle: str  # Full handle: @alice@node-id
    password: str
    totp_code: Optional[str] = None  # If 2FA enabled


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: User
    requires_2fa: bool = False  # If password correct but 2FA needed


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with password and optional 2FA"""

    # Find user by handle
    user = db.query(User).filter(User.handle == data.handle).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"Account locked until {user.locked_until.isoformat()}"
        )

    # Verify password
    if not user.verify_password(data.password):
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            db.commit()
            raise HTTPException(
                status_code=403,
                detail="Account locked due to too many failed login attempts. Try again in 15 minutes."
            )

        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Reset failed attempts on successful password
    user.failed_login_attempts = 0

    # Check if 2FA is enabled
    if user.totp_enabled or user.webauthn_credentials:
        # Require 2FA code
        if not data.totp_code:
            db.commit()
            return LoginResponse(
                access_token="",
                refresh_token="",
                user=user,
                requires_2fa=True  # Signal frontend to prompt for 2FA
            )

        # Verify 2FA code
        if not user.verify_totp(data.totp_code):
            # Try backup code as fallback
            if not user.use_backup_code(data.totp_code):
                raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # Create session tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Update last login
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.client.host

    # Add session to active sessions
    session = {
        "token_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "ip": request.client.host,
        "user_agent": request.headers.get("User-Agent")
    }
    user.active_sessions.append(session)

    db.commit()

    logger.info(f"User logged in: {user.handle} from {request.client.host}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user,
        requires_2fa=False
    )
```

### 5. TOTP Setup Endpoint

```python
@router.post("/2fa/totp/setup", response_model=dict)
async def setup_totp(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Setup TOTP 2FA"""

    # Generate secret and QR code
    qr_uri = current_user.enable_totp()
    db.commit()

    return {
        "qr_uri": qr_uri,
        "secret": current_user.totp_secret,  # Show once for manual entry
        "message": "Scan QR code with your authenticator app, then verify"
    }


@router.post("/2fa/totp/verify", response_model=dict)
async def verify_totp_setup(
    code: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Verify TOTP setup and enable it"""

    if not current_user.verify_totp(code):
        raise HTTPException(status_code=400, detail="Invalid code")

    # Enable TOTP
    current_user.totp_enabled = True

    # Generate backup codes
    backup_codes = current_user.generate_backup_codes()

    db.commit()

    return {
        "enabled": True,
        "backup_codes": backup_codes,  # Show once! User must save these
        "message": "2FA enabled successfully. Save your backup codes in a secure location."
    }
```

### 6. WebAuthn/Passkey Support

```python
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)

@router.post("/2fa/passkey/register-options", response_model=dict)
async def get_passkey_registration_options(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get WebAuthn registration options for adding a passkey"""

    options = generate_registration_options(
        rp_id="mesh.local",  # Relying party ID (your domain)
        rp_name="Solarpunk Mesh Network",
        user_id=current_user.id,
        user_name=current_user.handle,
        user_display_name=current_user.display_name
    )

    # Store challenge temporarily
    current_user.pending_webauthn_challenge = options.challenge
    db.commit()

    return options


@router.post("/2fa/passkey/register", response_model=dict)
async def register_passkey(
    credential: dict,
    credential_name: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Register a new passkey"""

    # Verify registration response
    verified_credential = verify_registration_response(
        credential=credential,
        expected_challenge=current_user.pending_webauthn_challenge,
        expected_origin="https://mesh.local",
        expected_rp_id="mesh.local"
    )

    # Store credential
    credential_data = {
        "id": verified_credential.credential_id,
        "public_key": verified_credential.public_key,
        "name": credential_name,
        "created_at": datetime.utcnow().isoformat(),
        "last_used": None
    }

    current_user.webauthn_credentials.append(credential_data)
    current_user.pending_webauthn_challenge = None

    db.commit()

    return {
        "registered": True,
        "message": f"Passkey '{credential_name}' registered successfully"
    }
```

## Implementation Steps

1. **Phase 1: Handle-Based Auth**
   - Add handle, username, node_id fields to User model
   - Update registration to create @username@node-id handles
   - Update login to accept full handles
   - Migration script to convert existing users

2. **Phase 2: Password Security**
   - Add password_hash field
   - Implement bcrypt hashing
   - Add password strength validation
   - Add password reset flow

3. **Phase 3: TOTP 2FA**
   - Add totp_secret, totp_enabled fields
   - Implement TOTP setup endpoints
   - Update login flow to check for 2FA
   - Generate backup codes

4. **Phase 4: WebAuthn/Passkeys**
   - Add webauthn_credentials field
   - Implement passkey registration
   - Implement passkey authentication
   - Test on multiple devices

5. **Phase 5: Session Management**
   - Implement JWT tokens
   - Add session revocation
   - Add "active sessions" page
   - Add logout from all devices

## Test Scenarios

### WHEN a user registers
THEN they MUST provide a unique username
AND a strong password
AND their handle MUST be @username@node-id format

### WHEN a user logs in with password only
THEN if they have 2FA enabled, they MUST NOT get a token
AND they MUST be prompted for 2FA code

### WHEN a user enables TOTP
THEN they MUST scan QR code with authenticator
AND they MUST verify with a code before it's enabled
AND they MUST receive backup codes

### WHEN a user logs in with passkey
THEN browser MUST prompt for biometric/PIN
AND login MUST succeed without password

### WHEN login fails 5 times
THEN account MUST be locked for 15 minutes
AND error MUST explain when they can try again

## Database Migration

```sql
ALTER TABLE users
ADD COLUMN handle VARCHAR(255) UNIQUE,
ADD COLUMN username VARCHAR(50),
ADD COLUMN node_id VARCHAR(255),
ADD COLUMN password_hash VARCHAR(255),
ADD COLUMN password_changed_at TIMESTAMP,
ADD COLUMN totp_secret VARCHAR(255),
ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN backup_codes JSON,
ADD COLUMN webauthn_credentials JSON,
ADD COLUMN failed_login_attempts INT DEFAULT 0,
ADD COLUMN locked_until TIMESTAMP,
ADD COLUMN recovery_email VARCHAR(255);

CREATE INDEX idx_handle ON users(handle);
CREATE INDEX idx_node_id ON users(node_id);
```

## Files to Create/Modify

- `app/models/user.py` - Add auth fields and methods
- `app/api/auth.py` - Registration, login, 2FA endpoints
- `app/auth/tokens.py` - JWT token generation
- `app/auth/webauthn.py` - WebAuthn helpers
- `frontend/src/pages/Register.tsx` - Registration form
- `frontend/src/pages/Login.tsx` - Login with 2FA
- `frontend/src/pages/Security Settings.tsx` - Manage 2FA
- `app/database/migrations/` - Database migration
- `tests/test_auth_security.py` - Comprehensive tests

## Security Considerations

1. **Password Storage**: Never store plain passwords, always bcrypt
2. **Rate Limiting**: Implement on all auth endpoints
3. **HTTPS Only**: Require TLS for all auth operations
4. **Token Expiry**: Access tokens expire in 15 min, refresh in 30 days
5. **CSRF Protection**: Use CSRF tokens for state-changing operations

## Related Gaps

- GAP-71: Delete listing auth (uses new auth system)
- GAP-72: Proposal reject (uses new auth system)
- All endpoints with `require_auth` dependency

## Documentation

Create docs explaining:
- How to choose a strong password
- How to set up authenticator app (TOTP)
- How to register a passkey
- What to do if locked out
- How to use backup codes
