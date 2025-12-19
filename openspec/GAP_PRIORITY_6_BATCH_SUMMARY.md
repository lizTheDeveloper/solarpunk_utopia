# Priority 6 Remaining Gaps - Batch Summary

**Created comprehensive proposals for**: GAP-41, 42, 43, 56, 57 (most critical security)

**Remaining gaps**: 13 (data integrity + operations)

---

## Data Integrity Gaps (HIGH Priority)

### GAP-44: Bare Except Clauses (Error Hiding)
**Severity**: HIGH | **Effort**: 2-3 hours

**Problem**: `except:` and `except Exception:` swallow errors silently

**Locations**:
- `app/clients/vf_client.py:217,228,239` - bare `except:`
- `app/llm/backends.py:147` - swallows errors

**Fix**:
```python
# ❌ BAD
try:
    result = await vf_client.get_listings()
except:  # Hides ALL errors!
    return []

# ✅ GOOD
try:
    result = await vf_client.get_listings()
except HTTPError as e:
    logger.error(f"VF API error: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error in get_listings")
    raise
```

**Tasks**:
1. Find all `except:` and `except Exception:` (2 hours)
2. Replace with specific exceptions + logging
3. Re-raise or return structured errors

---

###GAP-45: No Foreign Key Enforcement (Data Integrity)
**Severity**: HIGH | **Effort**: 3-4 hours

**Problem**: Foreign keys defined but not enforced - can create orphaned records

**Locations**:
- `app/database/db.py:22` - no `PRAGMA foreign_keys = ON`
- Schema files - missing CASCADE rules

**Fix**:
```python
# Enable FK enforcement
async def init_db():
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")  # ✅ Enable!
        await db.commit()
```

**Schema updates**:
```sql
-- Add CASCADE rules
ALTER TABLE listings
  ADD CONSTRAINT fk_agent
  FOREIGN KEY (agent_id)
  REFERENCES vf_agents(id)
  ON DELETE CASCADE;  -- ✅ Delete listings when agent deleted
```

---

### GAP-46: Race Conditions in Queue/Cache (Data Integrity)
**Severity**: HIGH | **Effort**: 4-6 hours

**Problem**: Non-atomic check-then-act allows concurrent corruption

**Locations**:
- `app/database/queues.py:67-83` - INSERT OR REPLACE without lock
- `app/services/cache_service.py:70-85` - check-then-delete not atomic

**Fix**:
```python
# ❌ VULNERABLE
cache_size = await get_cache_size()
if cache_size > MAX_SIZE:
    await delete_oldest()  # Race! Another thread might delete different item

# ✅ SAFE
async with cache_lock:
    cache_size = await get_cache_size()
    if cache_size > MAX_SIZE:
        await delete_oldest()

# Or use database transaction
async with db.transaction():
    cache_size = await db.execute("SELECT SUM(size) FROM cache")
    if cache_size > MAX_SIZE:
        await db.execute("DELETE FROM cache WHERE ...")
```

---

### GAP-47: INSERT OR REPLACE Overwrites Bundles (Data Integrity)
**Severity**: HIGH | **Effort**: 2-3 hours

**Problem**: `INSERT OR REPLACE` silently overwrites existing bundles

**Location**: `app/database/queues.py:72-82`

**Fix**:
```python
# ❌ DANGEROUS
await db.execute(
    "INSERT OR REPLACE INTO bundles (id, data) VALUES (?, ?)",
    (bundle_id, data)
)  # Silently overwrites!

# ✅ SAFE
try:
    await db.execute(
        "INSERT INTO bundles (id, data) VALUES (?, ?)",
        (bundle_id, data)
    )
except IntegrityError:
    logger.warning(f"Bundle {bundle_id} already exists, skipping")
    # Or: raise error, or UPDATE if appropriate
```

---

## Operations Gaps (MEDIUM-HIGH Priority)

### GAP-48: No Database Migrations
**Effort**: 4-6 hours

Use Alembic or similar:
```python
# alembic/versions/001_initial.py
def upgrade():
    op.create_table('users', ...)
    op.add_column('listings', sa.Column('community_id', ...))

def downgrade():
    op.drop_column('listings', 'community_id')
    op.drop_table('users')
```

---

### GAP-49: Hardcoded URLs
**Effort**: 2-3 hours

Move to environment variables:
```python
# ❌ Hardcoded
VF_URL = "http://localhost:8001"

# ✅ Configurable
VF_URL = os.getenv("VF_SERVICE_URL", "http://localhost:8001")
```

---

### GAP-50: No Logging for Debugging
**Effort**: 3-4 hours

Add structured logging:
```python
import structlog

logger = structlog.get_logger()

logger.info("proposal_approved",
    proposal_id=proposal_id,
    user_id=user_id,
    agent_type=agent.type
)
```

---

### GAP-51: Health Checks Don't Verify Dependencies
**Effort**: 2-3 hours

Check database, services:
```python
@router.get("/health")
async def health_check():
    checks = {
        "database": await check_db(),
        "vf_service": await check_vf_api(),
        "cache": await check_cache()
    }
    all_healthy = all(checks.values())
    status = 200 if all_healthy else 503
    return JSONResponse(checks, status_code=status)
```

---

### GAP-52: No Graceful Shutdown
**Effort**: 2-3 hours

Handle SIGTERM:
```python
import signal

async def shutdown():
    logger.info("Shutting down...")
    # Close database connections
    await db.close()
    # Finish processing queues
    await queue.drain()
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()

signal.signal(signal.SIGTERM, shutdown)
```

---

### GAP-53: No Request Tracing
**Effort**: 4-6 hours

Add correlation IDs:
```python
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

---

### GAP-54: No Metrics Collection
**Effort**: 4-6 hours

Use Prometheus:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response
```

---

### GAP-55: Frontend Returns Empty Agent List
**Effort**: 1-2 hours

Debug why agents list empty - likely API route or data issue.

---

### GAP-58: No Backup/Recovery
**Effort**: 3-4 hours

Automated backups:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 app.db ".backup /backups/app_${DATE}.db"
# Upload to S3/backup service
aws s3 cp /backups/app_${DATE}.db s3://commune-backups/
# Retention: delete backups older than 30 days
find /backups -name "app_*.db" -mtime +30 -delete
```

---

## Implementation Priority (Priority 6)

**Week 1: Critical Security**
1. ✅ GAP-41: CORS (1-2 hours)
2. ✅ GAP-42: Auth (see GAP-02)
3. ✅ GAP-43: Input validation (1-2 days)
4. ✅ GAP-56: CSRF (2-3 hours)
5. ✅ GAP-57: SQL injection (3-4 hours)

**Week 2: Data Integrity**
6. GAP-45: Foreign keys (3-4 hours)
7. GAP-46: Race conditions (4-6 hours)
8. GAP-47: INSERT OR REPLACE (2-3 hours)
9. GAP-44: Error handling (2-3 hours)

**Week 3: Operations**
10. GAP-48: Migrations (4-6 hours)
11. GAP-50: Logging (3-4 hours)
12. GAP-51: Health checks (2-3 hours)
13. GAP-52: Graceful shutdown (2-3 hours)

**Later**:
14. GAP-53: Request tracing
15. GAP-54: Metrics
16. GAP-58: Backups
17. GAP-49: Config cleanup
18. GAP-55: Debug agents list

---

## Total Effort Estimate (Priority 6)

- **Critical Security** (created proposals): 2-4 days
- **Data Integrity**: 2-3 days
- **Operations**: 3-4 days

**Total: ~7-11 days for full Priority 6 completion**

**Status**: 5 comprehensive proposals created, 13 summarized above
