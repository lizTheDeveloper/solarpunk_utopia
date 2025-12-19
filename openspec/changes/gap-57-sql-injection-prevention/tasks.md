# Tasks: GAP-57 SQL Injection Prevention (SECURITY)

## Phase 1: Audit Current Code (2-3 hours)

### Task 1.1: Search for SQL injection vectors
**File**: `scripts/audit_sql_injection.sh` (new file)
**Estimated**: 30 minutes

```bash
#!/bin/bash

echo "=== SQL Injection Audit ==="
echo ""

echo "1. Searching for f-string SQL queries..."
grep -r "f\".*SELECT" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" || echo "None found"
grep -r "f\".*INSERT" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" || echo "None found"
grep -r "f\".*UPDATE" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" || echo "None found"
grep -r "f\".*DELETE" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" || echo "None found"
echo ""

echo "2. Searching for .format() SQL queries..."
grep -r "\.format(" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" | grep -i "select\|insert\|update\|delete" || echo "None found"
echo ""

echo "3. Searching for % string formatting in SQL..."
grep -r "% " app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" | grep -i "select\|insert\|update\|delete" || echo "None found"
echo ""

echo "4. Searching for string concatenation in SQL..."
grep -r "+.*SELECT\|SELECT.*+" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" || echo "None found"
echo ""

echo "5. Listing all .execute() calls for manual review..."
grep -r "\.execute(" app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ --include="*.py" -A 2 -B 2
echo ""

echo "Audit complete. Review findings above."
```

**Acceptance criteria**:
- Script searches all services
- Finds f-strings in SQL
- Finds .format() in SQL
- Finds % formatting in SQL
- Lists all execute() calls
- Output saved to file

### Task 1.2: Manual review of database queries
**File**: Audit findings documented in `docs/SQL_INJECTION_AUDIT.md`
**Estimated**: 1.5 hours

For each finding from Task 1.1:
1. Review the query
2. Determine if user input involved
3. Check if parameterized
4. Mark as SAFE or VULNERABLE
5. Prioritize fixes

Document in table format:
```markdown
| File | Line | Query Type | User Input | Parameterized | Status | Priority |
|------|------|------------|------------|---------------|--------|----------|
| app/repo.py | 45 | SELECT | Yes | No | VULNERABLE | HIGH |
| vf/repo.py | 120 | INSERT | No | N/A | SAFE | N/A |
```

**Acceptance criteria**:
- All database queries reviewed
- User input sources identified
- Parameterization status documented
- Vulnerabilities prioritized
- Safe queries confirmed

### Task 1.3: Identify ORM usage vs raw SQL
**Estimated**: 30 minutes

Determine:
- Which services use ORM (SQLAlchemy, Tortoise, etc.)
- Which use raw SQL (execute())
- Consistency across codebase
- Recommend standardization

**Acceptance criteria**:
- ORM usage documented
- Raw SQL usage documented
- Recommendations for standardization

## Phase 2: Fix Vulnerable Queries (2-4 hours)

### Task 2.1: Fix repository layer queries
**Files**: `app/repositories/*.py`, `valueflows_node/app/repositories/*.py`
**Estimated**: 2-3 hours (depends on findings)

For each vulnerable query, convert to parameterized:

**Example 1: Simple SELECT**
```python
# ❌ BEFORE (vulnerable)
async def get_listing(self, listing_id: str):
    query = f"SELECT * FROM listings WHERE id = '{listing_id}'"
    result = await self.db.execute(query)
    return result.fetchone()

# ✅ AFTER (safe)
async def get_listing(self, listing_id: str):
    query = "SELECT * FROM listings WHERE id = ?"
    result = await self.db.execute(query, (listing_id,))
    return result.fetchone()
```

**Example 2: Dynamic WHERE clauses**
```python
# ❌ BEFORE (vulnerable)
async def search_listings(self, filters: dict):
    where_clauses = []
    for key, value in filters.items():
        where_clauses.append(f"{key} = '{value}'")
    where = " AND ".join(where_clauses)
    query = f"SELECT * FROM listings WHERE {where}"
    result = await self.db.execute(query)
    return result.fetchall()

# ✅ AFTER (safe)
async def search_listings(self, filters: dict):
    # Whitelist allowed filter keys
    ALLOWED_FILTERS = {'listing_type', 'status', 'category', 'agent_id'}

    conditions = []
    params = []
    for key, value in filters.items():
        if key not in ALLOWED_FILTERS:
            continue  # Skip unknown filters
        conditions.append(f"{key} = ?")
        params.append(value)

    where = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM listings WHERE {where}"
    result = await self.db.execute(query, params)
    return result.fetchall()
```

**Example 3: Dynamic ORDER BY**
```python
# ❌ BEFORE (vulnerable)
async def get_listings_sorted(self, sort_by: str):
    query = f"SELECT * FROM listings ORDER BY {sort_by}"
    result = await self.db.execute(query)
    return result.fetchall()

# ✅ AFTER (safe)
ALLOWED_SORT_COLUMNS = {
    'created_at', 'updated_at', 'quantity', 'listing_type', 'status'
}

async def get_listings_sorted(self, sort_by: str = 'created_at'):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Invalid sort column: {sort_by}")

    # Safe to use in query - whitelisted
    query = f"SELECT * FROM listings ORDER BY {sort_by}"
    result = await self.db.execute(query)
    return result.fetchall()
```

**Acceptance criteria**:
- All vulnerable queries fixed
- Parameterized queries used
- Column/table names whitelisted
- Dynamic SQL minimized
- Code reviewed

### Task 2.2: Add query builder helper functions
**File**: `app/database/query_builder.py` (new file)
**Estimated**: 1 hour

```python
from typing import Dict, List, Tuple, Any

def build_where_clause(
    filters: Dict[str, Any],
    allowed_columns: set[str]
) -> Tuple[str, List[Any]]:
    """
    Build safe WHERE clause with parameterized values.

    Args:
        filters: Dictionary of column -> value
        allowed_columns: Whitelist of allowed column names

    Returns:
        Tuple of (where_clause, params)
    """
    conditions = []
    params = []

    for column, value in filters.items():
        if column not in allowed_columns:
            raise ValueError(f"Invalid filter column: {column}")

        conditions.append(f"{column} = ?")
        params.append(value)

    where = " AND ".join(conditions) if conditions else "1=1"
    return where, params


def build_update_clause(
    updates: Dict[str, Any],
    allowed_columns: set[str]
) -> Tuple[str, List[Any]]:
    """
    Build safe UPDATE SET clause with parameterized values.

    Args:
        updates: Dictionary of column -> new_value
        allowed_columns: Whitelist of allowed column names

    Returns:
        Tuple of (set_clause, params)
    """
    set_clauses = []
    params = []

    for column, value in updates.items():
        if column not in allowed_columns:
            raise ValueError(f"Invalid update column: {column}")

        set_clauses.append(f"{column} = ?")
        params.append(value)

    set_clause = ", ".join(set_clauses)
    return set_clause, params


def validate_sort_column(
    column: str,
    allowed_columns: set[str],
    default: str = 'id'
) -> str:
    """
    Validate sort column against whitelist.

    Args:
        column: Requested sort column
        allowed_columns: Whitelist of allowed columns
        default: Default column if validation fails

    Returns:
        Safe column name
    """
    if column not in allowed_columns:
        return default
    return column
```

**Acceptance criteria**:
- Helper functions created
- Column names validated
- Parameterized queries generated
- Well documented
- Unit tested

## Phase 3: Add Security Tests (2-3 hours)

### Task 3.1: SQL injection attack tests
**File**: `tests/security/test_sql_injection.py` (new)
**Estimated**: 1.5 hours

```python
import pytest
from httpx import AsyncClient
from app.database import get_db

# Common SQL injection payloads
SQL_INJECTION_PAYLOADS = [
    # Classic injection
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",

    # Union attacks
    "' UNION SELECT * FROM users --",
    "1' UNION SELECT NULL, NULL, NULL --",

    # Stacked queries
    "'; DROP TABLE listings; --",
    "'; DELETE FROM users; --",

    # Comment injection
    "admin'--",
    "admin'/*",

    # Boolean-based blind
    "' AND 1=1 --",
    "' AND 1=2 --",

    # Time-based blind
    "' AND SLEEP(5) --",
    "' WAITFOR DELAY '00:00:05' --",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
async def test_listing_id_sql_injection(client: AsyncClient, payload):
    """Test that SQL injection in listing ID is blocked"""
    # Try to inject via GET parameter
    response = await client.get(f"/vf/listings/{payload}")

    # Should either 404 (not found) or 422 (validation error)
    # Should NOT return all listings or execute malicious SQL
    assert response.status_code in [404, 422, 400]

    # Verify no data leakage
    if response.status_code == 200:
        data = response.json()
        # If 200, should return single item, not all items
        assert not isinstance(data, list) or len(data) <= 1


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
async def test_search_sql_injection(client: AsyncClient, payload):
    """Test that SQL injection in search is blocked"""
    response = await client.get("/vf/listings/search", params={
        "query": payload
    })

    # Should handle safely
    assert response.status_code in [200, 400, 422]

    # If 200, verify no mass data dump
    if response.status_code == 200:
        data = response.json()
        assert len(data) < 1000  # Reasonable limit


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
async def test_filter_sql_injection(client: AsyncClient, payload):
    """Test that SQL injection in filters is blocked"""
    response = await client.get("/vf/listings/", params={
        "status": payload,
        "category": payload
    })

    # Should validate or return empty
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_drop_table_attack_fails():
    """Verify DROP TABLE attack does not work"""
    db = await get_db()

    # Verify table exists before attack
    result = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='listings'")
    assert result.fetchone() is not None

    # Attempt injection
    malicious_id = "'; DROP TABLE listings; --"

    # Try various endpoints
    client = AsyncClient(app=app, base_url="http://test")
    await client.get(f"/vf/listings/{malicious_id}")

    # Verify table still exists
    result = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='listings'")
    assert result.fetchone() is not None, "Table was dropped! SQL injection successful!"


@pytest.mark.asyncio
async def test_union_attack_no_data_leakage():
    """Verify UNION attack doesn't leak data from other tables"""
    client = AsyncClient(app=app, base_url="http://test")

    # Attempt to leak user data via union
    malicious_query = "' UNION SELECT id, password FROM users --"

    response = await client.get("/vf/listings/search", params={
        "query": malicious_query
    })

    # Should not succeed
    if response.status_code == 200:
        data = response.json()
        # Verify response doesn't contain user passwords
        response_text = str(data).lower()
        assert 'password' not in response_text
        assert 'hash' not in response_text
```

**Acceptance criteria**:
- All attack vectors tested
- DROP TABLE blocked
- UNION attacks blocked
- Boolean-based blind blocked
- No data leakage
- Tables remain intact

### Task 3.2: Automated SQLMap scanning
**File**: `scripts/sqlmap_scan.sh` (new)
**Estimated**: 1 hour

```bash
#!/bin/bash

echo "=== SQLMap Automated SQL Injection Scan ==="
echo ""

# Ensure services are running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "Error: Services not running. Start with 'docker-compose up' or similar."
    exit 1
fi

# Install sqlmap if not present
if ! command -v sqlmap &> /dev/null; then
    echo "Installing sqlmap..."
    pip install sqlmap
fi

echo "Scanning ValueFlows API endpoints..."

# Test GET parameter injection
sqlmap -u "http://localhost:8000/vf/listings?status=active" \
    --batch \
    --level=5 \
    --risk=3 \
    --threads=10 \
    --output-dir=./sqlmap-results

# Test POST parameter injection
sqlmap -u "http://localhost:8000/vf/listings/" \
    --method=POST \
    --data='{"listing_type": "offer", "quantity": "5"}' \
    --headers="Content-Type: application/json" \
    --batch \
    --level=5 \
    --risk=3 \
    --output-dir=./sqlmap-results

# Test search endpoint
sqlmap -u "http://localhost:8000/vf/listings/search?query=food" \
    --batch \
    --level=5 \
    --risk=3 \
    --threads=10 \
    --output-dir=./sqlmap-results

echo ""
echo "Scan complete. Review results in ./sqlmap-results/"
echo ""
echo "Expected result: No vulnerabilities found"
```

**Acceptance criteria**:
- SQLMap runs successfully
- All endpoints scanned
- No SQL injection vulnerabilities found
- Results documented

### Task 3.3: Bandit security scanner
**File**: Add to CI/CD pipeline
**Estimated**: 30 minutes

```bash
#!/bin/bash

echo "Running Bandit security scanner..."

pip install bandit

bandit -r app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ \
    -f json \
    -o bandit-report.json \
    -ll  # Medium and high severity only

bandit -r app/ valueflows_node/ discovery_search/ file_chunking/ mesh_network/ \
    -f html \
    -o bandit-report.html \
    -ll

echo "Bandit scan complete. Review:"
echo "  - bandit-report.json"
echo "  - bandit-report.html"
```

**Acceptance criteria**:
- Bandit runs on all code
- No SQL injection issues found
- Report generated
- Added to CI/CD

## Phase 4: Code Review & Refactoring (1-2 hours)

### Task 4.1: Standardize on ORM where possible
**Estimated**: 1-1.5 hours

Recommendation: Use SQLAlchemy ORM for complex queries

```python
# Instead of raw SQL:
query = "SELECT * FROM listings WHERE agent_id = ? AND status = ?"
result = await db.execute(query, (agent_id, status))

# Use ORM:
from sqlalchemy import select
from app.models import Listing

stmt = select(Listing).where(
    Listing.agent_id == agent_id,
    Listing.status == status
)
result = await session.execute(stmt)
listings = result.scalars().all()
```

**Acceptance criteria**:
- Complex queries use ORM
- Simple queries can use parameterized SQL
- Consistent pattern across services
- Migration path documented

### Task 4.2: Add linting rules
**File**: `.pylintrc` or `pyproject.toml`
**Estimated**: 30 minutes

Add custom linting rules to detect SQL injection risks:

```toml
[tool.pylint.messages_control]
disable = []
enable = [
    "f-string-without-interpolation",
    "logging-format-interpolation",
]

[tool.pylint.custom]
# Detect f-strings in SQL
sql-keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE"]
```

Consider: https://github.com/sqlfluff/sqlfluff

**Acceptance criteria**:
- Linter detects f-strings in SQL
- Linter detects .format() in SQL
- CI fails on violations
- Existing code passes

## Phase 5: Documentation (1 hour)

### Task 5.1: Create SQL security guidelines
**File**: `docs/DATABASE_SECURITY.md` (new)
**Estimated**: 45 minutes

```markdown
# Database Security Guidelines

## SQL Injection Prevention

### MUST Requirements

1. **ALWAYS use parameterized queries**
   ```python
   # ✅ GOOD
   query = "SELECT * FROM listings WHERE id = ?"
   await db.execute(query, (listing_id,))

   # ❌ BAD
   query = f"SELECT * FROM listings WHERE id = '{listing_id}'"
   await db.execute(query)
   ```

2. **NEVER use f-strings or .format() in SQL**
   ```python
   # ❌ NEVER DO THIS
   query = f"SELECT * FROM {table_name} WHERE id = {user_id}"
   query = "SELECT * FROM {} WHERE id = {}".format(table, id)
   ```

3. **Whitelist column and table names**
   ```python
   ALLOWED_SORT_COLUMNS = {'created_at', 'quantity', 'status'}

   if sort_by not in ALLOWED_SORT_COLUMNS:
       raise ValueError("Invalid sort column")

   query = f"SELECT * FROM listings ORDER BY {sort_by}"  # Safe
   ```

4. **Prefer ORM over raw SQL**
   ```python
   # ✅ BETTER - ORM handles escaping
   listings = await session.query(Listing).filter_by(status=status).all()
   ```

### Code Review Checklist

Before approving PR:
- [ ] No f-strings in SQL queries
- [ ] No .format() in SQL queries
- [ ] All queries parameterized
- [ ] Column/table names whitelisted
- [ ] SQL injection tests added

### Testing

Run security tests before commit:
```bash
pytest tests/security/test_sql_injection.py -v
./scripts/sqlmap_scan.sh
bandit -r app/ -ll
```
```

**Acceptance criteria**:
- Guidelines clear and actionable
- Examples provided (good and bad)
- Review checklist included
- Testing instructions provided

### Task 5.2: Update SECURITY.md
**File**: `docs/SECURITY.md`
**Estimated**: 15 minutes

Add section on SQL injection prevention:
- What was audited
- What was fixed
- Current security posture
- How to maintain security

**Acceptance criteria**:
- Security posture documented
- Mitigation strategies listed
- Monitoring recommendations included

## Verification Checklist

Before marking this as complete:

- [ ] All database code audited
- [ ] Vulnerable queries identified and fixed
- [ ] All queries use parameterized statements
- [ ] No f-strings or .format() in SQL
- [ ] Column/table names whitelisted
- [ ] SQL injection tests pass
- [ ] SQLMap scan finds no vulnerabilities
- [ ] Bandit scan finds no SQL issues
- [ ] DROP TABLE attack blocked
- [ ] UNION attack blocked
- [ ] Boolean-based blind blocked
- [ ] Database tables intact after tests
- [ ] Documentation complete
- [ ] Linting rules added
- [ ] Code review completed

## Estimated Total Time

- Phase 1: 2.5 hours (audit)
- Phase 2: 3 hours (fixes)
- Phase 3: 3 hours (testing)
- Phase 4: 1.5 hours (refactoring)
- Phase 5: 1 hour (documentation)

**Total: 3-4 hours (11 hours for thorough implementation)**

## Dependencies

- Database access for testing
- SQLMap installed
- Bandit installed
- Test database with sample data
- CI/CD pipeline access

## Risk Assessment

**Before**: CRITICAL - Full database compromise possible

**After**: LOW - Parameterized queries prevent injection

**Residual Risks**:
- Second-order SQL injection (user data stored then used in query)
- ORM vulnerabilities (keep dependencies updated)
- Insider threats (DB credentials)

## Monitoring

Post-deployment monitoring:
- Log all database errors
- Alert on unusual query patterns
- Monitor query performance (parameterization overhead)
- Regular security scans (weekly)
- Dependency updates (CVE monitoring)
