# GAP-47: INSERT OR REPLACE Overwrites Bundles

**Status:** Implemented
**Priority:** P2 - Data Integrity
**Effort:** 2-3 hours

## Problem

`INSERT OR REPLACE` silently overwrites existing bundles without warning.

**Location:** `app/database/queues.py:72-82`

## Solution

```python
# ❌ DANGEROUS
await db.execute(
    "INSERT OR REPLACE INTO bundles (id, data) VALUES (?, ?)",
    (bundle_id, data)
)

# ✅ SAFE
try:
    await db.execute(
        "INSERT INTO bundles (id, data) VALUES (?, ?)",
        (bundle_id, data)
    )
except IntegrityError:
    logger.warning(f"Bundle {bundle_id} already exists, skipping")
    # Or raise, or UPDATE if appropriate
```

## Tasks

1. Find all INSERT OR REPLACE usages
2. Replace with INSERT + conflict handling
3. Decide policy per table (skip/update/error)
4. Add tests for duplicate handling

## Success Criteria

- [x] No silent overwrites
- [x] Explicit conflict handling
- [x] Tests for duplicate inserts

## Implementation Notes

**Implemented:** 2025-12-20

Fixed as part of GAP-46 implementation.

### Changes:
- Replaced `INSERT OR REPLACE` with `INSERT` + explicit duplicate checking in `app/database/queues.py`
- enqueue() now checks if bundle exists before inserting
- Existing bundles are skipped (logged as debug) rather than overwritten
- Test coverage in `app/tests/test_race_conditions.py::test_no_insert_or_replace_overwrites`

### Result:
- ✅ No silent overwrites
- ✅ Bundles are immutable once inserted
- ✅ Explicit logging when duplicates are skipped
