# Tasks: GAP-41 CORS Security

## Implementation (1-2 hours)

### Task 1: Update all 5 services
**Estimated**: 1 hour

Update each service's main.py:

```python
# Add at top of file
import os
from typing import List

def get_allowed_origins() -> List[str]:
    """Get CORS allowed origins from environment"""
    origins_str = os.getenv("ALLOWED_ORIGINS", "")

    if not origins_str:
        # Check if production
        if os.getenv("ENV") == "production":
            raise ValueError(
                "ALLOWED_ORIGINS environment variable must be set in production. "
                "Example: ALLOWED_ORIGINS=https://app.commune.local"
            )
        # Development defaults
        return ["http://localhost:3000", "http://localhost:5173"]

    # Parse comma-separated list
    origins = [o.strip() for o in origins_str.split(",") if o.strip()]

    # Validate format
    for origin in origins:
        if not (origin.startswith("http://") or origin.startswith("https://")):
            raise ValueError(f"Invalid origin format: {origin}")

    return origins

# In FastAPI app setup
allowed_origins = get_allowed_origins()
logger.info(f"CORS configured for origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

Files to update:
1. `app/main.py:115`
2. `valueflows_node/app/main.py:40`
3. `discovery_search/main.py:155`
4. `file_chunking/main.py:66`
5. `mesh_network/bridge_node/main.py:61`

### Task 2: Update configuration files
**Estimated**: 30 minutes

`.env.example`:
```bash
# CORS Configuration
# Comma-separated list of allowed origins
# Development (default): http://localhost:3000,http://localhost:5173
# Production: MUST be set explicitly
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Environment (development or production)
ENV=development
```

`docker-compose.yml`:
```yaml
services:
  dtn-bundle-system:
    environment:
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:5173}
      - ENV=${ENV:-development}

  valueflows-node:
    environment:
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:5173}
      - ENV=${ENV:-development}

  # ... repeat for all services
```

### Task 3: Testing
**Estimated**: 30 minutes

```bash
# Test 1: Development (no ALLOWED_ORIGINS set)
unset ALLOWED_ORIGINS
docker-compose up
# Should start with localhost defaults

# Test 2: Production without ALLOWED_ORIGINS
ENV=production docker-compose up
# Should FAIL with error message

# Test 3: Production with valid ALLOWED_ORIGINS
ENV=production ALLOWED_ORIGINS=https://app.commune.local docker-compose up
# Should start successfully

# Test 4: Browser CORS check
# Try making request from https://evil.com
# Should be blocked

# Test 5: Valid origin
# Make request from configured origin
# Should succeed
```

### Task 4: Documentation
**Estimated**: 15 minutes

Update deployment docs with CORS configuration requirements.

## Verification

- [ ] All 5 services updated
- [ ] No `allow_origins=["*"]` remains
- [ ] Dev mode works without config
- [ ] Production fails without config
- [ ] CORS blocks unauthorized origins
- [ ] Configured origins work correctly

**Total: 2 hours**
