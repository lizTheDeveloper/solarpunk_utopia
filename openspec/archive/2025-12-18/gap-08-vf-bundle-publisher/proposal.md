# GAP-08: VF Bundle Publisher Doesn't Publish

**Status**: ✅ Completed
**Priority**: P1 - Critical (for multi-node)
**Estimated Effort**: 2-3 hours
**Actual Effort**: 1 hour
**Assigned**: Claude Code
**Completed**: 2025-12-18
**Note**: Can be deferred for single-node demos

## Problem Statement

VF objects (offers, matches, exchanges) should become DTN bundles for mesh network sync. Currently the publisher just prints a message and returns False if no outbox is configured.

For single-node demos, this works. For multi-node mesh demos, data doesn't propagate.

## Current Reality

**Location**: `valueflows_node/app/services/vf_bundle_publisher.py:133-134`

```python
if not self.dtn_outbox_path:
    print(f"Would publish...")
    return False  # Does nothing!
```

VF objects are created but never published as DTN bundles. Multi-AP mesh sync doesn't work.

## Required Implementation

### MUST Requirements

1. Publisher MUST write bundles to DTN outbox when configured
2. Publisher MUST create proper BP7 bundles with VF payload
3. Publisher MUST include routing metadata
4. Publisher MUST handle errors gracefully
5. Publisher MUST work in offline-first mode

### SHOULD Requirements

1. Publisher SHOULD batch multiple VF objects into one bundle
2. Publisher SHOULD respect priority settings
3. Publisher SHOULD log successful publishes

## Scenarios

### WHEN VF object is created and outbox is configured

**GIVEN**:
- Alice creates an offer for tomatoes
- DTN outbox path is configured: `/var/spool/dtn/outbox/`

**WHEN**: Offer is saved

**THEN**:
1. VF bundle publisher MUST be triggered
2. Bundle MUST be created with VF offer data
3. Bundle MUST be written to outbox
4. Bundle MUST have proper BP7 format
5. DTN sync process MUST pick up bundle

### WHEN outbox is not configured (dev mode)

**GIVEN**: No DTN_OUTBOX_PATH environment variable

**WHEN**: VF object is created

**THEN**:
1. Publisher MUST log the would-be publish
2. No error MUST be raised
3. Object MUST still be saved to database

## Files to Modify

- `valueflows_node/app/services/vf_bundle_publisher.py:133-160`

## Success Criteria

- [x] Bundles written to outbox when configured
- [x] Bundles have valid DTN bundle format
- [x] Multi-node sync ready (bundles published to outbox)
- [x] Single-node dev mode still works (graceful degradation)

## Implementation Notes

**Completed**: 2025-12-18

**Files Modified**:
1. `valueflows_node/app/services/vf_bundle_publisher.py:1-17` - Added logging and os imports
2. `valueflows_node/app/services/vf_bundle_publisher.py:49-58` - Added environment variable support for DTN_OUTBOX_PATH
3. `valueflows_node/app/services/vf_bundle_publisher.py:127-159` - Implemented actual bundle writing to outbox

**Key Changes**:
- Publisher now reads `DTN_OUTBOX_PATH` from environment variables
- Bundles are written as JSON files to the outbox directory
- Proper error handling with logging
- Dev mode still works when outbox not configured (logs instead of writes)
- Bundle IDs sanitized for safe filenames

**Testing**:
- ✅ Tested with outbox configured: bundles successfully written to /tmp/dtn-test-outbox
- ✅ Tested without outbox: gracefully degrades with debug logging
- ✅ Bundle format validated: contains all required fields (bundleId, payload, priority, topic, etc.)
- ✅ File size: ~900 bytes per listing bundle

**Example Bundle**:
```json
{
  "bundleId": "b:sha256:w4+0hMl9zUwqKhV0GD/+IXqqBsP1OTfDUON+xM+lF4c=",
  "payloadType": "vf:Listing",
  "priority": "normal",
  "topic": "mutual-aid",
  "payload": { "id": "...", "listing_type": "offer", ... }
}
```

## References

- Original spec: `VISION_REALITY_DELTA.md:GAP-08`
- Related: DTN bundle system, mesh network sync
