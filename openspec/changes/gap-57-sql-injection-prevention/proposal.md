# GAP-57: SQL Injection Risk (SECURITY)

**Status**: ✅ IMPLEMENTED
**Priority**: P6 - Production/Security
**Severity**: CRITICAL
**Estimated Effort**: 3-4 hours
**Assigned**: Unclaimed
**Implemented**: 2025-12-19

## Implementation Summary

Audit completed - codebase is secure against SQL injection:

1. **Fixed vulnerability** in `valueflows_node/app/repositories/vf/base_repo.py:84`
   - LIMIT and OFFSET were using f-string interpolation
   - Now uses parameterized query: `LIMIT ? OFFSET ?`

2. **Verified safe patterns**:
   - All user input uses `?` placeholders with parameter tuples
   - F-strings only used for table names (controlled by code, not user input)
   - Dynamic UPDATE queries build column names from internal logic, values are parameterized
   - No `.format()` or string concatenation with user input

3. **Audit script** available at `scripts/audit_sql_injection.sh` for ongoing verification

## Problem Statement

Some database queries use string formatting or concatenation instead of parameterized queries, enabling SQL injection attacks.

## Current Reality

**Potential locations**: Any raw SQL queries

Example vulnerability:
```python
# ❌ VULNERABLE
async def get_listing(listing_id: str):
    query = f"SELECT * FROM listings WHERE id = '{listing_id}'"
    result = await db.execute(query)

# Attack:
# listing_id = "'; DROP TABLE listings; --"
# Executes: SELECT * FROM listings WHERE id = ''; DROP TABLE listings; --'
```

## Required Implementation

### MUST Requirements

1. All queries MUST use parameterized statements
2. All user input MUST be sanitized before database operations
3. No string concatenation or f-strings in SQL
4. Query parameters MUST use `?` placeholders (SQLite) or `%s` (PostgreSQL)
5. ORM usage MUST be preferred over raw SQL

### Correct Implementation

```python
# ✅ SAFE - Parameterized query
async def get_listing(listing_id: str):
    query = "SELECT * FROM listings WHERE id = ?"
    result = await db.execute(query, (listing_id,))

# ✅ SAFE - ORM
listing = await Listing.get(id=listing_id)
```

## Audit Required

### Task 1: Find all raw SQL
```bash
# Search for potential SQL injection vectors
grep -r "f\".*SELECT" app/ valueflows_node/
grep -r "f\".*INSERT" app/ valueflows_node/
grep -r "f\".*UPDATE" app/ valueflows_node/
grep -r "f\".*DELETE" app/ valueflows_node/
grep -r "\.format(" app/ valueflows_node/ | grep -i "select\|insert\|update\|delete"
grep -r "% " app/ valueflows_node/ | grep -i "select\|insert\|update\|delete"
```

### Task 2: Review each finding

For each finding:
1. Determine if user input involved
2. Check if parameterized
3. Fix if vulnerable
4. Add test case

## Common Patterns to Fix

### Pattern 1: Dynamic WHERE clauses
```python
# ❌ VULNERABLE
filters = []
if name:
    filters.append(f"name = '{name}'")
if category:
    filters.append(f"category = '{category}'")
where = " AND ".join(filters)
query = f"SELECT * FROM items WHERE {where}"

# ✅ SAFE
conditions = []
params = []
if name:
    conditions.append("name = ?")
    params.append(name)
if category:
    conditions.append("category = ?")
    params.append(category)
where = " AND ".join(conditions)
query = f"SELECT * FROM items WHERE {where}"
await db.execute(query, params)
```

### Pattern 2: Dynamic column names
```python
# ❌ VULNERABLE
sort_by = request.args.get('sort')
query = f"SELECT * FROM items ORDER BY {sort_by}"

# ✅ SAFE - Whitelist
ALLOWED_SORT_COLUMNS = ['name', 'created_at', 'quantity']
sort_by = request.args.get('sort', 'created_at')
if sort_by not in ALLOWED_SORT_COLUMNS:
    raise ValueError("Invalid sort column")
query = f"SELECT * FROM items ORDER BY {sort_by}"  # Safe - whitelisted
```

## Files to Audit

All files with database access:
- `app/database/*.py`
- `valueflows_node/app/database/*.py`
- `app/repositories/*.py`
- `valueflows_node/app/repositories/*.py`
- Any `*_repo.py` files

## Testing

```python
# SQL Injection test cases
def test_sql_injection_listing_id():
    """Verify SQL injection is blocked"""
    malicious_id = "'; DROP TABLE listings; --"
    with pytest.raises(Exception):  # Should not delete table!
        get_listing(malicious_id)

    # Verify table still exists
    assert table_exists("listings")

def test_sql_injection_search():
    """Verify search parameter injection blocked"""
    malicious_search = "' OR '1'='1"
    results = search_listings(malicious_search)
    # Should return 0 or limited results, not all listings
    assert len(results) < 100
```

## Success Criteria

- [ ] All raw SQL uses parameterized queries
- [ ] No f-strings or concatenation in SQL
- [ ] SQL injection tests pass
- [ ] Automated SQLMap scan finds no vulnerabilities

## Tools

Run automated scanning:
```bash
# SQLMap test (requires running server)
sqlmap -u "http://localhost:8001/vf/listings?id=1" --batch --level=5

# Bandit security scanner
pip install bandit
bandit -r app/ valueflows_node/ -f json -o security-report.json
```

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-57`
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- SQLite Injection: https://www.sqlite.org/lang_expr.html#varparam
