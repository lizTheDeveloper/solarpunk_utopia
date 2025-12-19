# Tasks: GAP-08 VF Bundle Publisher

## Implementation (2-3 hours)

### Task 1: Implement bundle creation
**File**: `valueflows_node/app/services/vf_bundle_publisher.py`
**Estimated**: 1.5 hours

```python
def _create_vf_bundle(self, vf_object: Dict, object_type: str) -> bytes:
    """Create BP7 bundle from VF object"""
    # Create bundle payload
    payload = {
        "type": object_type,  # "listing", "match", "exchange"
        "data": vf_object,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Serialize to JSON
    payload_bytes = json.dumps(payload).encode('utf-8')

    # Create BP7 bundle
    # TODO: Use actual BP7 library
    bundle = {
        "version": 7,
        "destination": "dtn://commune.local/vf",
        "source": f"dtn://{self.node_id}/vf",
        "payload": payload_bytes,
        "creation_timestamp": time.time()
    }

    return json.dumps(bundle).encode('utf-8')

def _write_bundle_to_outbox(self, bundle_bytes: bytes, object_id: str):
    """Write bundle file to DTN outbox"""
    if not self.dtn_outbox_path:
        return False

    # Generate bundle filename
    filename = f"vf_{object_id}_{int(time.time())}.bundle"
    filepath = os.path.join(self.dtn_outbox_path, filename)

    # Write bundle
    with open(filepath, 'wb') as f:
        f.write(bundle_bytes)

    logger.info(f"Published VF bundle: {filename}")
    return True

def publish_vf_object(self, vf_object: Dict, object_type: str) -> bool:
    """Publish VF object as DTN bundle"""
    if not self.dtn_outbox_path:
        logger.debug(f"Would publish {object_type}: {vf_object.get('id')}")
        return False

    try:
        # Create bundle
        bundle = self._create_vf_bundle(vf_object, object_type)

        # Write to outbox
        success = self._write_bundle_to_outbox(bundle, vf_object['id'])

        return success
    except Exception as e:
        logger.error(f"Failed to publish VF bundle: {e}")
        return False
```

### Task 2: Update VF API to trigger publisher
**File**: `valueflows_node/app/api/vf/listings.py`, etc.
**Estimated**: 1 hour

```python
@router.post("/")
async def create_listing(
    data: ListingCreate,
    publisher: VFBundlePublisher = Depends(get_publisher)
):
    # Create listing in database
    listing = await repo.create_listing(data)

    # Publish to DTN
    publisher.publish_vf_object(listing.dict(), "listing")

    return listing
```

Do same for:
- Matches creation
- Exchanges creation
- Updates to any VF objects

### Task 3: Add configuration
**File**: `.env.example`
**Estimated**: 15 minutes

```bash
# DTN Configuration
DTN_OUTBOX_PATH=/var/spool/dtn/outbox
DTN_NODE_ID=node_sunrise_collective
```

### Task 4: Testing
**Estimated**: 30 minutes

```bash
# Test with outbox configured
mkdir -p /tmp/dtn-outbox
export DTN_OUTBOX_PATH=/tmp/dtn-outbox
export DTN_NODE_ID=test_node

# Create an offer
curl -X POST http://localhost:8001/vf/listings/ -d '...'

# Verify bundle created
ls /tmp/dtn-outbox/
# Should see vf_*.bundle file

# Inspect bundle
cat /tmp/dtn-outbox/vf_*.bundle | jq .

# Test without outbox (dev mode)
unset DTN_OUTBOX_PATH
# Should still work, just log instead of write
```

## Verification

- [ ] Bundles written when outbox configured
- [ ] Bundle format is valid
- [ ] No errors in dev mode
- [ ] Multi-node sync works (if testable)

**Total: 2-3 hours**
