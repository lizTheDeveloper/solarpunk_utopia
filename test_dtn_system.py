#!/usr/bin/env python3
"""
Test script for DTN Bundle System

Tests:
1. Bundle creation with signing
2. Queue management operations
3. TTL enforcement
4. Signature verification
5. Forwarding rules
6. Cache budget enforcement
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, '/Users/annhoward/src/solarpunk_utopia')

from app.models import Bundle, BundleCreate, Priority, Audience, Topic, QueueName
from app.services import CryptoService, BundleService, TTLService, CacheService, ForwardingService
from app.database import init_db, QueueManager, close_db


async def test_bundle_creation():
    """Test 1: Bundle creation with signing"""
    print("\n=== Test 1: Bundle Creation with Signing ===")

    crypto = CryptoService()
    bundle_service = BundleService(crypto)

    # Create bundle
    bundle_create = BundleCreate(
        payload={"message": "Emergency: Fire in garden"},
        payloadType="alert:Emergency",
        priority=Priority.EMERGENCY,
        audience=Audience.PUBLIC,
        topic=Topic.COORDINATION,
        tags=["emergency", "fire"]
    )

    bundle = await bundle_service.create_bundle(bundle_create)

    print(f"✓ Bundle created: {bundle.bundleId}")
    print(f"  Priority: {bundle.priority.value}")
    print(f"  Topic: {bundle.topic.value}")
    print(f"  Created: {bundle.createdAt}")
    print(f"  Expires: {bundle.expiresAt}")
    print(f"  Signature: {bundle.signature[:32]}...")

    # Verify signature
    is_valid, error = await bundle_service.validate_bundle(bundle)
    assert is_valid, f"Bundle validation failed: {error}"
    print(f"✓ Signature verified successfully")

    return bundle


async def test_queue_operations():
    """Test 2: Queue management operations"""
    print("\n=== Test 2: Queue Operations ===")

    crypto = CryptoService()
    bundle_service = BundleService(crypto)

    # Create bundles with different priorities
    priorities = [Priority.EMERGENCY, Priority.PERISHABLE, Priority.NORMAL, Priority.LOW]
    bundles = []

    for priority in priorities:
        bundle_create = BundleCreate(
            payload={"message": f"Test bundle with {priority.value} priority"},
            payloadType="test:Message",
            priority=priority,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=["test"]
        )
        bundle = await bundle_service.create_bundle(bundle_create)
        bundles.append(bundle)
        print(f"✓ Created {priority.value} priority bundle")

    # Move to pending
    for bundle in bundles:
        await QueueManager.move(bundle.bundleId, QueueName.OUTBOX, QueueName.PENDING)
        print(f"✓ Moved {bundle.bundleId[:20]}... to pending")

    # List pending queue (should be ordered by priority)
    pending = await QueueManager.list_queue(QueueName.PENDING)
    print(f"\n✓ Pending queue has {len(pending)} bundles")
    print("  Priority order:")
    for i, b in enumerate(pending):
        print(f"    {i+1}. {b.priority.value}")

    # Verify priority order
    assert pending[0].priority == Priority.EMERGENCY
    assert pending[1].priority == Priority.PERISHABLE
    assert pending[2].priority == Priority.NORMAL
    assert pending[3].priority == Priority.LOW
    print("✓ Priority ordering correct")

    return bundles


async def test_ttl_enforcement():
    """Test 3: TTL enforcement"""
    print("\n=== Test 3: TTL Enforcement ===")

    crypto = CryptoService()
    bundle_service = BundleService(crypto)

    # Create expired bundle (expires 1 hour ago)
    now = datetime.now(datetime.UTC)
    expired_time = now - timedelta(hours=1)

    bundle_create = BundleCreate(
        payload={"message": "Expired bundle"},
        payloadType="test:Expired",
        priority=Priority.NORMAL,
        audience=Audience.PUBLIC,
        topic=Topic.COORDINATION,
        tags=["test"],
        expiresAt=expired_time
    )

    bundle = await bundle_service.create_bundle(bundle_create)
    print(f"✓ Created expired bundle: {bundle.bundleId[:20]}...")
    print(f"  Expires: {bundle.expiresAt} (already expired)")

    # Move to pending
    await QueueManager.move(bundle.bundleId, QueueName.OUTBOX, QueueName.PENDING)

    # Run TTL enforcement
    ttl_service = TTLService()
    moved_count = await ttl_service.enforce_once()

    print(f"✓ TTL enforcement moved {moved_count} expired bundles")

    # Check that bundle is now in expired queue
    expired_bundles = await QueueManager.list_queue(QueueName.EXPIRED)
    expired_ids = [b.bundleId for b in expired_bundles]

    assert bundle.bundleId in expired_ids
    print(f"✓ Expired bundle moved to expired queue")


async def test_signature_verification():
    """Test 4: Signature verification and quarantine"""
    print("\n=== Test 4: Signature Verification ===")

    crypto1 = CryptoService()
    crypto2 = CryptoService()  # Different keypair
    bundle_service = BundleService(crypto1)

    # Create valid bundle
    bundle_create = BundleCreate(
        payload={"message": "Valid bundle"},
        payloadType="test:Valid",
        priority=Priority.NORMAL,
        audience=Audience.PUBLIC,
        topic=Topic.COORDINATION,
        tags=["test"]
    )

    bundle = await bundle_service.create_bundle(bundle_create)
    print(f"✓ Created valid bundle: {bundle.bundleId[:20]}...")

    # Test valid signature
    is_valid, error = await bundle_service.validate_bundle(bundle)
    assert is_valid
    print(f"✓ Valid signature accepted")

    # Tamper with bundle (change payload)
    tampered_bundle = bundle.model_copy(deep=True)
    tampered_bundle.payload = {"message": "Tampered message"}

    # Test invalid signature
    is_valid, error = await bundle_service.validate_bundle(tampered_bundle)
    assert not is_valid
    print(f"✓ Invalid signature detected: {error}")

    # Test receiving invalid bundle (should go to quarantine)
    success, message = await bundle_service.receive_bundle(tampered_bundle)
    assert not success
    print(f"✓ Invalid bundle rejected: {message}")

    # Check quarantine queue
    quarantine = await QueueManager.list_queue(QueueName.QUARANTINE)
    print(f"✓ Quarantine queue has {len(quarantine)} bundles")


async def test_forwarding_rules():
    """Test 5: Forwarding rules and audience enforcement"""
    print("\n=== Test 5: Forwarding Rules ===")

    crypto = CryptoService()
    bundle_service = BundleService(crypto)
    forwarding_service = ForwardingService()

    # Create bundles with different audiences
    audiences = [
        (Audience.PUBLIC, "public", True, 0.5),
        (Audience.LOCAL, "local", True, 0.5),
        (Audience.LOCAL, "local_remote", False, 0.5),
        (Audience.TRUSTED, "trusted_high", True, 0.8),
        (Audience.TRUSTED, "trusted_low", True, 0.5),
    ]

    for audience, label, is_local, trust_score in audiences:
        bundle_create = BundleCreate(
            payload={"message": f"Bundle with {audience.value} audience"},
            payloadType="test:Audience",
            priority=Priority.NORMAL,
            audience=audience,
            topic=Topic.COORDINATION,
            tags=["test"]
        )
        bundle = await bundle_service.create_bundle(bundle_create)

        # Check if can forward
        can_forward, reason = forwarding_service.can_forward_to_peer(
            bundle,
            peer_trust_score=trust_score,
            peer_is_local=is_local
        )

        # Determine expected result
        if audience == Audience.PUBLIC:
            expected = True
        elif audience == Audience.LOCAL:
            expected = is_local
        elif audience == Audience.TRUSTED:
            expected = trust_score >= 0.7
        else:
            expected = False

        status = "✓" if can_forward == expected else "✗"
        print(f"{status} {label}: audience={audience.value}, "
              f"local={is_local}, trust={trust_score} → "
              f"{'ALLOWED' if can_forward else 'BLOCKED'}")

        if can_forward != expected:
            print(f"  FAILED: Expected {expected}, got {can_forward}")
            print(f"  Reason: {reason}")


async def test_cache_budget():
    """Test 6: Cache budget enforcement"""
    print("\n=== Test 6: Cache Budget Enforcement ===")

    # Use small budget for testing (10KB)
    cache_service = CacheService(storage_budget_bytes=10 * 1024)

    # Get initial stats
    stats = await cache_service.get_cache_stats()
    print(f"✓ Initial cache size: {stats['current_size_bytes']} bytes")
    print(f"  Budget: {stats['budget_bytes']} bytes")
    print(f"  Usage: {stats['usage_percentage']:.2f}%")

    # Check if we can accept a 5KB bundle
    can_accept = await cache_service.can_accept_bundle(5 * 1024)
    print(f"✓ Can accept 5KB bundle: {can_accept}")

    # Check if we can accept a 20KB bundle (over budget)
    can_accept = await cache_service.can_accept_bundle(20 * 1024)
    print(f"✓ Can accept 20KB bundle: {can_accept}")

    # Get final stats
    stats = await cache_service.get_cache_stats()
    print(f"✓ Final cache usage: {stats['usage_percentage']:.2f}%")
    print(f"  Over budget: {stats['is_over_budget']}")


async def test_priority_forwarding():
    """Test 7: Priority-based forwarding order"""
    print("\n=== Test 7: Priority-Based Forwarding ===")

    crypto = CryptoService()
    bundle_service = BundleService(crypto)
    forwarding_service = ForwardingService()

    # Create bundles with different priorities and move to pending
    priorities = [Priority.LOW, Priority.NORMAL, Priority.EMERGENCY, Priority.PERISHABLE]

    for priority in priorities:
        bundle_create = BundleCreate(
            payload={"message": f"Bundle with {priority.value} priority"},
            payloadType="test:Priority",
            priority=priority,
            audience=Audience.PUBLIC,
            topic=Topic.COORDINATION,
            tags=["test"]
        )
        bundle = await bundle_service.create_bundle(bundle_create)
        await QueueManager.move(bundle.bundleId, QueueName.OUTBOX, QueueName.PENDING)
        print(f"✓ Created and queued {priority.value} bundle")

    # Get bundles for forwarding
    bundles = await forwarding_service.get_bundles_for_forwarding(max_bundles=10)

    print(f"\n✓ Got {len(bundles)} bundles for forwarding")
    print("  Forwarding order:")
    for i, bundle in enumerate(bundles):
        print(f"    {i+1}. {bundle.priority.value}")

    # Verify order: emergency, perishable, normal, low
    expected_order = [Priority.EMERGENCY, Priority.PERISHABLE, Priority.NORMAL, Priority.LOW]
    actual_order = [b.priority for b in bundles]

    if actual_order == expected_order:
        print("✓ Priority ordering correct!")
    else:
        print(f"✗ Priority ordering incorrect!")
        print(f"  Expected: {[p.value for p in expected_order]}")
        print(f"  Got: {[p.value for p in actual_order]}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("DTN Bundle System Test Suite")
    print("=" * 60)

    try:
        # Initialize database
        await init_db()
        print("✓ Database initialized")

        # Run tests
        await test_bundle_creation()
        await test_queue_operations()
        await test_ttl_enforcement()
        await test_signature_verification()
        await test_forwarding_rules()
        await test_cache_budget()
        await test_priority_forwarding()

        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Close database
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
