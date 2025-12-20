# GAP-44: Bare Except Clauses (ERROR HIDING)

**Status**: ✅ IMPLEMENTED
**Priority**: P6 - Production/Security
**Severity**: HIGH
**Estimated Effort**: 3-4 hours
**Assigned**: Autonomous Agent
**Created**: December 19, 2025

## Problem Statement

Code contains bare `except:` clauses and overly broad `except Exception:` handlers that silently swallow errors. This makes debugging impossible in production and hides critical failures.

## Current Reality

**Found 19 occurrences across 12 files:**

1. **app/database/db.py** - Bare except for schema migrations
2. **app/agents/work_party_scheduler.py** - Bare except for date parsing
3. **app/llm/backends.py** - Broad Exception for health checks (2 instances)
4. **app/services/attestation_service.py** - Exception handling
5. **app/services/mycelial_health_monitor_service.py** - Exception handling
6. **app/api/messages.py** - Exception handling
7. **app/api/steward_dashboard.py** - Exception handling
8. **app/clients/vf_client.py** - Exception handling (3 instances)

Example problems:
```python
# ❌ BAD: Silently swallows all errors
try:
    cursor.execute("ALTER TABLE proposals ADD COLUMN community_id TEXT")
except:
    pass  # Column already exists - OR DOES IT? Maybe syntax error?

# ❌ BAD: Too broad, loses error information
try:
    response = await self.client.get(f"{self.base_url}/api/tags")
    return response.status_code == 200
except Exception:
    return False  # Connection refused? Timeout? Auth failure? Who knows!
```

## Required Implementation

### MUST Requirements

1. System MUST catch specific exceptions only
2. System MUST log all caught exceptions with context
3. System MUST preserve stack traces for debugging
4. System MUST handle expected errors explicitly
5. System MUST re-raise unexpected errors after logging
6. System MUST NOT silently swallow errors

### SHOULD Requirements

1. System SHOULD use custom exception types for domain errors
2. System SHOULD provide helpful error messages to users
3. System SHOULD track error rates via metrics

## Scenarios

### WHEN database migration encounters existing column

**GIVEN**: Migration adds `community_id` column

**THEN**:
1. System MUST catch `sqlite3.OperationalError` specifically
2. System MUST verify error is "column already exists" (not other error)
3. System MUST log at INFO level: "Column community_id already exists, skipping"
4. System MUST re-raise if different OperationalError

### WHEN health check fails to connect to LLM backend

**GIVEN**: Ollama is not running

**THEN**:
1. System MUST catch `httpx.ConnectError` specifically
2. System MUST log at WARNING level with connection details
3. System MUST return False (expected failure case)
4. System MUST re-raise if unexpected HTTP error (500, auth failure, etc.)

### WHEN date parsing fails in scheduler

**GIVEN**: Malformed date in commitment data

**THEN**:
1. System MUST catch `ValueError` specifically
2. System MUST log at ERROR level with the bad date value
3. System MUST skip that commitment
4. System MUST continue processing other commitments

## Files to Modify

Priority order (most critical first):

### Critical (Production Blockers)
1. **app/database/db.py** - Schema migrations
2. **app/clients/vf_client.py** - API client error handling

### High Priority
3. **app/llm/backends.py** - LLM health checks
4. **app/api/messages.py** - Message API
5. **app/api/steward_dashboard.py** - Dashboard API

### Medium Priority
6. **app/agents/work_party_scheduler.py** - Scheduler
7. **app/services/attestation_service.py** - Attestation
8. **app/services/mycelial_health_monitor_service.py** - Health monitor

## Implementation Examples

### Migration with Proper Error Handling

```python
import sqlite3
import logging

logger = logging.getLogger(__name__)

try:
    await _db_connection.execute("""
        ALTER TABLE proposals ADD COLUMN community_id TEXT
    """)
    logger.info("Added community_id column to proposals table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        logger.info("Column community_id already exists, skipping migration")
    else:
        logger.error(f"Failed to add community_id column: {e}")
        raise  # Re-raise unexpected migration errors
```

### Health Check with Specific Exceptions

```python
import httpx
import logging

logger = logging.getLogger(__name__)

async def is_available(self) -> bool:
    """Check if Ollama backend is available."""
    try:
        response = await self.client.get(f"{self.base_url}/api/tags")
        return response.status_code == 200
    except httpx.ConnectError as e:
        logger.warning(f"Ollama not reachable at {self.base_url}: {e}")
        return False
    except httpx.TimeoutException as e:
        logger.warning(f"Ollama health check timed out: {e}")
        return False
    except Exception as e:
        # Unexpected errors should be logged and potentially alerted
        logger.error(f"Unexpected error checking Ollama availability: {e}", exc_info=True)
        raise  # Re-raise to surface unexpected issues
```

### Date Parsing with Context

```python
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    due_date = datetime.fromisoformat(commitment["due_date"])
    participants_map[agent_id]["availability"].append(due_date)
except (ValueError, KeyError) as e:
    logger.error(
        f"Failed to parse date for agent {agent_id}: {e}. "
        f"Commitment data: {commitment.get('due_date', 'MISSING')}"
    )
    # Continue processing other commitments
except Exception as e:
    logger.error(
        f"Unexpected error processing commitment for {agent_id}: {e}",
        exc_info=True
    )
    # Re-raise unexpected errors
    raise
```

## Success Criteria

- [ ] Zero bare `except:` clauses in codebase
- [ ] All `except Exception:` reviewed and replaced with specific exceptions OR proper logging
- [ ] All caught exceptions logged with context
- [ ] Error logs include enough information to debug production issues
- [ ] Health checks distinguish between expected and unexpected failures
- [ ] Tests added for error cases

## Testing Requirements

1. **Unit tests for error paths**:
   - Test migration with existing column
   - Test migration with actual error
   - Test health check when service down
   - Test health check when service errors
   - Test date parsing with malformed data

2. **Integration tests**:
   - Verify error logs contain expected context
   - Verify unexpected errors are re-raised
   - Verify application continues after expected errors

## Implementation Plan

### Phase 1: Critical Files (2 hours)
1. Fix app/database/db.py migrations
2. Fix app/clients/vf_client.py API calls
3. Add logging infrastructure if needed

### Phase 2: High Priority (1 hour)
4. Fix app/llm/backends.py health checks
5. Fix app/api/messages.py
6. Fix app/api/steward_dashboard.py

### Phase 3: Medium Priority (1 hour)
7. Fix app/agents/work_party_scheduler.py
8. Fix app/services/attestation_service.py
9. Fix app/services/mycelial_health_monitor_service.py

### Phase 4: Verification (30 minutes)
10. Search for remaining bare excepts
11. Review all Exception catches
12. Run tests

## References

- VISION_REALITY_DELTA.md:GAP-44
- Python Best Practices: https://docs.python.org/3/tutorial/errors.html
- Logging Best Practices: https://docs.python.org/3/howto/logging.html
