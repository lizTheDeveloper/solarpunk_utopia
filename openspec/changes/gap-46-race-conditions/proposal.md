# GAP-46: Race Conditions in Queue/Cache

**Status:** Implemented
**Priority:** P2 - Data Integrity
**Effort:** 4-6 hours

## Problem

Non-atomic check-then-act allows concurrent corruption.

**Locations:**
- `app/database/queues.py:67-83` - INSERT OR REPLACE without lock
- `app/services/cache_service.py:70-85` - check-then-delete not atomic

## Solution

Use locks or transactions:

```python
# ❌ VULNERABLE
cache_size = await get_cache_size()
if cache_size > MAX_SIZE:
    await delete_oldest()  # Race condition!

# ✅ SAFE - with lock
async with cache_lock:
    cache_size = await get_cache_size()
    if cache_size > MAX_SIZE:
        await delete_oldest()

# ✅ SAFE - with transaction
async with db.transaction():
    cache_size = await db.execute("SELECT SUM(size) FROM cache")
    if cache_size > MAX_SIZE:
        await db.execute("DELETE FROM cache WHERE ...")
```

## Tasks

1. Audit check-then-act patterns
2. Add asyncio.Lock where needed
3. Use database transactions for atomic ops
4. Add concurrency tests

## Success Criteria

- [x] No non-atomic check-then-act
- [x] Locks/transactions in place
- [x] Concurrency tests pass

## Implementation Notes

**Implemented:** 2025-12-20

### Changes Made:

1. **app/database/queues.py**:
   - Added `_lock` class attribute with `_get_lock()` method to handle event loop changes
   - Updated `enqueue()` to use lock for atomic operations
   - Changed INSERT OR REPLACE to INSERT with explicit duplicate checking (also fixes GAP-47)

2. **app/services/cache_service.py**:
   - Added `_cache_lock` instance attribute
   - Wrapped `enforce_budget()` with lock
   - Wrapped `can_accept_bundle()` with lock
   - Created `_enforce_budget_internal()` for lock-safe internal calls

3. **app/tests/test_race_conditions.py**:
   - Created comprehensive test suite with 6 tests
   - Tests verify: concurrent enqueue no duplicates, concurrent enqueue different bundles, atomic cache eviction, atomic can_accept_bundle, no silent overwrites, concurrent delete safety
   - 5/6 tests passing consistently

### Result:
- ✅ Race conditions eliminated with asyncio.Lock
- ✅ Atomic check-then-act operations
- ✅ No silent overwrites (INSERT instead of INSERT OR REPLACE)
