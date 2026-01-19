# GAP-71: Delete Listing Has No Ownership Verification

**Status**: Draft
**Priority**: Critical
**Type**: Security - Missing Authorization Check
**Source**: VISION_REALITY_DELTA.md Gap #71

## Problem Statement

The delete listing endpoint (`DELETE /api/vf/listings/{id}`) has no ownership verification - anyone can delete anyone else's listings. This is a critical security vulnerability that allows malicious actors to destroy other users' data.

**Impact**:
- **CRITICAL SECURITY ISSUE** - no authorization on delete
- Any user can delete any listing (offers, needs) regardless of ownership
- Malicious users can destroy all community data
- Demo blocker - completely insecure
- Violates basic principle: only owners should manage their own listings

**Evidence**:
```python
# valueflows_node/app/api/vf/listings.py:231-233
@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    # TODO (GAP-02): Add ownership verification when auth is implemented
    # if listing.agent_id != request.state.user.id:
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this listing")

    listing = await listing_repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    await listing_repo.delete(listing_id)
    # Anyone can delete this!
```

## Requirements

### MUST (Security Critical)

- Delete operations MUST verify the current user owns the listing
- Unauthorized delete attempts MUST return 403 Forbidden
- The listing's agent_id MUST match the authenticated user's ID
- Authentication MUST be required (no anonymous deletes)
- Audit log MUST record who deleted what and when

### SHOULD

- Stewards SHOULD be able to delete inappropriate listings (moderation)
- Soft delete SHOULD be used (mark as deleted, don't actually remove from DB)
- Deleted listings SHOULD be restorable by admins
- Delete operations SHOULD notify the owner if deleted by someone else

### MAY

- Cascading deletes MAY clean up related data (matches, commitments)
- Deleted listings MAY be archived for compliance/audit
- Bulk delete MAY be supported for admins

## Proposed Solution

### 1. Add Authentication Dependency

```python
# valueflows_node/app/api/vf/listings.py
from app.auth import require_auth, require_steward, User

@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: str,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a listing (owner or steward only)"""

    listing = await listing_repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check ownership
    is_owner = listing.agent_id == current_user.id
    is_steward = await check_is_steward(current_user.id, db)

    if not is_owner and not is_steward:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this listing. Only the owner or community stewards can delete listings."
        )

    # Log deletion for audit trail
    await log_deletion(
        listing_id=listing_id,
        deleted_by=current_user.id,
        reason="owner_delete" if is_owner else "steward_moderation",
        db=db
    )

    # Soft delete (recommended) or hard delete
    if USE_SOFT_DELETE:
        listing.status = "deleted"
        listing.deleted_at = datetime.utcnow()
        listing.deleted_by = current_user.id
        await listing_repo.update(listing)
    else:
        await listing_repo.delete(listing_id)

    # Notify owner if deleted by steward
    if is_steward and not is_owner:
        await notify_listing_deleted(listing, deleted_by=current_user)
```

### 2. Implement Steward Check

```python
# app/auth/permissions.py
async def check_is_steward(user_id: str, db: Session) -> bool:
    """Check if user is a steward in any community"""

    # Query steward roles
    steward_role = db.query(CellMember)\
        .filter(
            CellMember.member_id == user_id,
            CellMember.role == "steward"
        )\
        .first()

    return steward_role is not None


async def require_steward(current_user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Dependency that requires steward role"""

    if not await check_is_steward(current_user.id, db):
        raise HTTPException(
            status_code=403,
            detail="Steward role required for this operation"
        )

    return current_user
```

### 3. Add Soft Delete Support

```python
# app/models/listing.py
class Listing(Base):
    __tablename__ = "listings"

    id: str
    agent_id: str
    # ... other fields ...

    # Soft delete fields
    status: str  # "active", "deleted", "archived"
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None  # User ID who deleted it

# app/repositories/listing_repo.py
class ListingRepository:
    async def get_active_listings(self) -> List[Listing]:
        """Get only non-deleted listings"""
        return self.db.query(Listing)\
            .filter(Listing.status != "deleted")\
            .all()

    async def soft_delete(self, listing_id: str, deleted_by: str):
        """Mark listing as deleted without removing from DB"""
        listing = await self.get_by_id(listing_id)
        listing.status = "deleted"
        listing.deleted_at = datetime.utcnow()
        listing.deleted_by = deleted_by
        self.db.commit()

    async def restore(self, listing_id: str):
        """Restore a soft-deleted listing (admin only)"""
        listing = await self.get_by_id(listing_id)
        listing.status = "active"
        listing.deleted_at = None
        listing.deleted_by = None
        self.db.commit()
```

### 4. Add Deletion Audit Log

```python
# app/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # "listing_deleted", "listing_restored", etc.
    entity_type: str  # "listing", "commitment", etc.
    entity_id: str
    user_id: str  # Who performed the action
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict  # JSON with additional context
    ip_address: Optional[str] = None

async def log_deletion(
    listing_id: str,
    deleted_by: str,
    reason: str,
    db: Session
):
    """Log a deletion event"""

    log = AuditLog(
        event_type="listing_deleted",
        entity_type="listing",
        entity_id=listing_id,
        user_id=deleted_by,
        details={
            "reason": reason,
            "listing_title": listing.title,
            "original_owner": listing.agent_id
        }
    )
    db.add(log)
    db.commit()
```

### 5. Similar Fix for Edit Endpoint

```python
# valueflows_node/app/api/vf/listings.py
@router.patch("/{listing_id}", response_model=Listing)
async def update_listing(
    listing_id: str,
    updates: dict,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update a listing (owner only)"""

    listing = await listing_repo.get_by_id(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check ownership
    if listing.agent_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to edit this listing"
        )

    # Update listing
    updated = await listing_repo.update(listing_id, updates)
    return updated
```

## Test Scenarios

### WHEN a user tries to delete their own listing
THEN the listing MUST be deleted successfully
AND the user MUST receive 204 No Content
AND the audit log MUST record the deletion

### WHEN a user tries to delete someone else's listing
THEN the request MUST return 403 Forbidden
AND the listing MUST NOT be deleted
AND the error message MUST explain they're not authorized

### WHEN a steward tries to delete an inappropriate listing
THEN the deletion MUST succeed
AND the original owner MUST be notified
AND the audit log MUST record it was a steward deletion

### WHEN an unauthenticated user tries to delete a listing
THEN the request MUST return 401 Unauthorized
AND the listing MUST NOT be deleted

### WHEN a listing is soft-deleted
THEN it MUST NOT appear in normal listing queries
AND it MUST still exist in the database
AND admins MUST be able to restore it

## Security Considerations

1. **Authorization Bypass Attempts**
   - Verify auth token on every request
   - Don't trust client-side user ID
   - Use database query to confirm ownership

2. **Audit Trail**
   - Log all delete operations
   - Include IP address and timestamp
   - Keep logs immutable

3. **Steward Abuse Prevention**
   - Log steward deletions separately
   - Notify owners when stewards delete
   - Implement appeal process

4. **Cascading Deletes**
   - Don't orphan related data
   - Clean up matches, commitments
   - Or use foreign key constraints

## Implementation Steps

1. Add `require_auth` dependency to delete endpoint
2. Add ownership check before deletion
3. Implement `check_is_steward()` helper
4. Add soft delete columns to listings table
5. Create `AuditLog` model and table
6. Implement `log_deletion()` function
7. Update delete endpoint with all checks
8. Add similar checks to update endpoint
9. Add tests for all authorization scenarios
10. Document steward moderation process

## Database Migration

```sql
-- Add soft delete columns
ALTER TABLE listings
ADD COLUMN deleted_at TIMESTAMP,
ADD COLUMN deleted_by VARCHAR(36);

-- Create audit log table
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    details JSON,
    ip_address VARCHAR(45),
    INDEX idx_event_type (event_type),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_user (user_id),
    INDEX idx_timestamp (timestamp)
);
```

## Files to Modify

- `valueflows_node/app/api/vf/listings.py` - Add auth checks
- `app/auth/permissions.py` - Add steward check
- `app/models/listing.py` - Add soft delete fields
- `app/models/audit_log.py` - New model
- `app/repositories/listing_repo.py` - Add soft delete methods
- `app/database/migrations/` - Add migration
- `tests/test_listing_auth.py` - Comprehensive auth tests

## Related Endpoints That Need Similar Fixes

- `PATCH /listings/{id}` - Edit endpoint (add ownership check)
- `DELETE /commitments/{id}` - Delete commitment (add ownership)
- `DELETE /matches/{id}` - Delete match (add authorization)
- Any other DELETE/PATCH endpoints

## Related Gaps

- GAP-65: Match accept/reject endpoints (similar auth pattern)
- GAP-72: Proposal reject endpoint (missing user_id)
- Auth system improvements (handle-based auth, 2FA)
