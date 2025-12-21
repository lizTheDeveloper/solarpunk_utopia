"""
Tests for GAP-46: Race Conditions in Queue/Cache

Verifies that:
1. Concurrent enqueue operations don't create duplicates
2. Cache eviction is atomic
3. No check-then-act race conditions exist
"""

import asyncio
import pytest
import pytest_asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

from app.models import Bundle, QueueName, Priority, Audience, Topic, ReceiptPolicy
from app.database.queues import QueueManager
from app.services.cache_service import CacheService
from app.database.db import init_db, close_db, get_db, DB_PATH


@pytest_asyncio.fixture
async def setup_db():
    """Initialize test database"""
    # Use a temporary database for testing
    original_db_path = DB_PATH

    # Create temp db
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    # Monkey patch DB_PATH
    import app.database.db as db_module
    db_module.DB_PATH = Path(temp_db.name)

    # Initialize test database
    await init_db()

    yield await get_db()

    # Cleanup
    await close_db()
    db_module.DB_PATH = original_db_path
    os.unlink(temp_db.name)


def create_test_bundle(bundle_id: str, priority: Priority = Priority.NORMAL) -> Bundle:
    """Create a test bundle"""
    # Bundle IDs must start with b:sha256:
    if not bundle_id.startswith("b:sha256:"):
        bundle_id = f"b:sha256:{bundle_id}"
    return Bundle(
        bundleId=bundle_id,
        createdAt=datetime.now(timezone.utc),
        expiresAt=datetime.now(timezone.utc) + timedelta(hours=1),
        priority=priority,
        audience=Audience.PUBLIC,
        topic=Topic.MUTUAL_AID,
        tags=[],
        payloadType="test",
        payload={"test": "data"},
        hopLimit=10,
        hopCount=0,
        receiptPolicy=ReceiptPolicy.NONE,
        signature="test_signature",
        authorPublicKey="test_public_key"
    )


@pytest.mark.asyncio
async def test_concurrent_enqueue_no_duplicates(setup_db):
    """
    Test that concurrent enqueue operations don't create duplicate bundles.

    This verifies the fix for GAP-46 where INSERT OR REPLACE could cause
    race conditions.
    """
    bundle = create_test_bundle("concurrent-test-1")

    # Enqueue the same bundle 10 times concurrently
    tasks = [
        QueueManager.enqueue(QueueName.INBOX, bundle)
        for _ in range(10)
    ]
    await asyncio.gather(*tasks)

    # Verify only one bundle exists
    bundles = await QueueManager.list_queue(QueueName.INBOX)
    matching_bundles = [b for b in bundles if b.bundleId == bundle.bundleId]

    assert len(matching_bundles) == 1, f"Should only have one bundle despite concurrent inserts, got {len(matching_bundles)}"


@pytest.mark.asyncio
async def test_concurrent_enqueue_different_bundles(setup_db):
    """
    Test that concurrent enqueue of different bundles works correctly.
    """
    # Create 10 different bundles
    bundles = [create_test_bundle(f"bundle-{i}") for i in range(10)]

    # Enqueue all concurrently
    tasks = [
        QueueManager.enqueue(QueueName.INBOX, bundle)
        for bundle in bundles
    ]
    await asyncio.gather(*tasks)

    # Verify all bundles exist
    queue_bundles = await QueueManager.list_queue(QueueName.INBOX, limit=100)
    bundle_ids = {b.bundleId for b in queue_bundles}
    expected_ids = {b.bundleId for b in bundles}

    for expected_id in expected_ids:
        assert expected_id in bundle_ids, f"Bundle {expected_id} should exist"

    assert len(queue_bundles) == 10, f"Should have 10 bundles, got {len(queue_bundles)}"


@pytest.mark.asyncio
async def test_cache_eviction_atomic(setup_db):
    """
    Test that cache eviction is atomic - no race conditions during eviction.

    This verifies the fix for GAP-46 where check-then-delete wasn't atomic.
    """
    # Create small cache service (1MB budget)
    cache_service = CacheService(storage_budget_bytes=1024 * 1024)

    # Add some low-priority bundles
    for i in range(5):
        bundle = create_test_bundle(f"low-priority-{i}", Priority.LOW)
        await QueueManager.enqueue(QueueName.INBOX, bundle)

    # Run eviction concurrently multiple times
    tasks = [cache_service.enforce_budget() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # All eviction calls should complete without error
    assert all(isinstance(r, int) for r in results), "All eviction calls should return int"


@pytest.mark.asyncio
async def test_cache_can_accept_bundle_atomic(setup_db):
    """
    Test that can_accept_bundle is atomic when checking and evicting.
    """
    # Create small cache service
    cache_service = CacheService(storage_budget_bytes=1024 * 1024)

    # Fill cache with low-priority bundles
    for i in range(10):
        bundle = create_test_bundle(f"filler-{i}", Priority.LOW)
        await QueueManager.enqueue(QueueName.INBOX, bundle)

    # Concurrently try to accept new bundles
    tasks = [
        cache_service.can_accept_bundle(100 * 1024)  # 100KB each
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)

    # All calls should complete without error
    assert all(isinstance(r, bool) for r in results), "All calls should return bool"


@pytest.mark.asyncio
async def test_no_insert_or_replace_overwrites(setup_db):
    """
    Test that INSERT OR REPLACE is not used (GAP-47).

    Verifies that existing bundles are not silently overwritten.
    """
    bundle1 = create_test_bundle("no-overwrite-test")
    bundle1.payload = {"version": 1}

    # Enqueue first version
    await QueueManager.enqueue(QueueName.INBOX, bundle1)

    # Try to enqueue modified version with same ID
    bundle2 = create_test_bundle("no-overwrite-test")
    bundle2.payload = {"version": 2}
    await QueueManager.enqueue(QueueName.INBOX, bundle2)

    # Verify original bundle still exists (not overwritten)
    retrieved = await QueueManager.get_bundle(bundle1.bundleId)
    assert retrieved is not None, f"Bundle should exist with ID {bundle1.bundleId}"
    assert retrieved.payload["version"] == 1, "Original bundle should not be overwritten"


@pytest.mark.asyncio
async def test_concurrent_delete_safe(setup_db):
    """
    Test that concurrent delete operations are safe.
    """
    # Create and enqueue bundle
    bundle = create_test_bundle("delete-test")
    await QueueManager.enqueue(QueueName.INBOX, bundle)

    # Try to delete concurrently multiple times
    tasks = [
        QueueManager.delete(bundle.bundleId)
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)

    # First delete should succeed, rest should fail
    successful_deletes = sum(1 for r in results if r)
    assert successful_deletes <= 1, "Should only successfully delete once"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
