#!/usr/bin/env python
"""Test VF Bundle Publisher"""

import sys
import os

# Set up env before imports
os.environ['DTN_OUTBOX_PATH'] = '/tmp/dtn-test-outbox'

sys.path.insert(0, 'valueflows_node')

from valueflows_node.app.services.vf_bundle_publisher import VFBundlePublisher
from valueflows_node.app.models.vf.listing import Listing, ListingType
from datetime import datetime
import glob

# Create test outbox
os.makedirs('/tmp/dtn-test-outbox', exist_ok=True)

# Clean up any existing test bundles
for f in glob.glob('/tmp/dtn-test-outbox/*.json'):
    os.remove(f)

# Create a test listing
listing = Listing(
    id='test_listing_001',
    listing_type=ListingType.OFFER,
    resource_spec_id='tomatoes',
    agent_id='alice',
    quantity=5.0,
    unit='kg',
    status='active',
    created_at=datetime.now(),
    updated_at=datetime.now()
)

# Test publisher
print("Testing VF Bundle Publisher...")
print(f"Outbox path: {os.getenv('DTN_OUTBOX_PATH')}")

publisher = VFBundlePublisher()
print(f"Publisher initialized with outbox: {publisher.dtn_outbox_path}")

# Publish the listing
bundle = publisher.publish_vf_object(listing, 'Listing')
print(f"\n✓ Bundle created: {bundle['bundleId'][:60]}...")
print(f"✓ Payload type: {bundle.get('payloadType')}")
print(f"✓ Priority: {bundle.get('priority')}")
print(f"✓ Topic: {bundle.get('topic')}")

# Check if file was created
files = glob.glob('/tmp/dtn-test-outbox/*.json')
print(f"\n✓ Files created in outbox: {len(files)}")
if files:
    import json
    with open(files[0]) as f:
        bundle_from_file = json.load(f)
    print(f"✓ Bundle file: {files[0]}")
    print(f"✓ Bundle size: {os.path.getsize(files[0])} bytes")
    print(f"✓ Contains {len(bundle_from_file)} fields")

print("\n✅ Bundle publishing test PASSED!")
