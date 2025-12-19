# Tasks: GAP-06B DELETE Endpoint

## Implementation (30 minutes)

### Task 1: Add DELETE endpoint
**File**: `valueflows_node/app/api/vf/listings.py`
**Estimated**: 30 minutes

```python
@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: str,
    request: Request,
    repo: ListingRepository = Depends(get_listing_repo)
):
    """Delete a listing (owner only)"""
    user = request.state.user

    # Get listing
    listing = await repo.get_listing_by_id(listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")

    # Verify ownership
    if listing.agent_id != user.id:
        raise HTTPException(403, "Not authorized to delete this listing")

    # Delete
    await repo.delete_listing(listing_id)

    return Response(status_code=204)
```

### Task 2: Add delete_listing to repository
**File**: `valueflows_node/app/repositories/listing_repo.py`
**Estimated**: Included above

```python
async def delete_listing(self, listing_id: str) -> bool:
    """Delete a listing by ID"""
    async with self.db.cursor() as cur:
        await cur.execute(
            "DELETE FROM listings WHERE id = ?",
            (listing_id,)
        )
        await self.db.commit()
        return cur.rowcount > 0
```

## Testing (10 minutes)

```bash
# Test delete own listing
curl -X DELETE http://localhost:8001/vf/listings/{id} \
  -H "Authorization: Bearer {alice_token}"
# Should return 204

# Test delete someone else's listing
curl -X DELETE http://localhost:8001/vf/listings/{alice_listing_id} \
  -H "Authorization: Bearer {bob_token}"
# Should return 403
```

## Verification

- [ ] DELETE endpoint added
- [ ] Ownership check implemented
- [ ] Returns 204 on success
- [ ] Returns 403 for unauthorized
- [ ] Returns 404 for not found
- [ ] Frontend delete button works

**Total: 30-40 minutes**
