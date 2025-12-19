"""
Test script to verify proposal persistence to SQLite database.

This script tests that proposals can be:
1. Stored to database
2. Retrieved from database
3. Updated in database
4. Listed with filters
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.framework import Proposal, ProposalType, ProposalStatus, ProposalFilter
from app.database.db import init_db, close_db
from app.database.proposal_repo import ProposalRepository


async def test_proposal_persistence():
    """Test proposal persistence functionality"""
    print("🧪 Testing Proposal Persistence\n")
    print("=" * 60)

    # Initialize database
    print("\n1️⃣  Initializing database...")
    await init_db()
    print("   ✓ Database initialized")

    # Create a test proposal
    print("\n2️⃣  Creating test proposal...")
    proposal = Proposal(
        agent_name="mutual-aid-matchmaker",
        proposal_type=ProposalType.MATCH,
        title="Test Match: Alice's tomatoes → Bob's need",
        explanation="This is a test proposal for persistence verification",
        inputs_used=[
            "bundle:offer_123",
            "bundle:need_456",
        ],
        constraints=[
            "max_distance_km: 5",
            "perishable: true",
        ],
        data={
            "offer": {"id": "offer_123", "agent": "Alice", "resource": "Tomatoes", "quantity": 10},
            "need": {"id": "need_456", "agent": "Bob", "resource": "Tomatoes", "quantity": 8},
        },
        requires_approval=["alice", "bob"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    print(f"   ✓ Created proposal: {proposal.proposal_id}")
    print(f"     - Type: {proposal.proposal_type.value}")
    print(f"     - Status: {proposal.status.value}")
    print(f"     - Requires approval: {proposal.requires_approval}")

    # Save to database
    print("\n3️⃣  Saving to database...")
    await ProposalRepository.save(proposal)
    print("   ✓ Saved successfully")

    # Retrieve from database
    print("\n4️⃣  Retrieving from database...")
    retrieved = await ProposalRepository.get_by_id(proposal.proposal_id)
    if not retrieved:
        print("   ✗ FAILED: Proposal not found!")
        return False

    print(f"   ✓ Retrieved proposal: {retrieved.proposal_id}")
    print(f"     - Title: {retrieved.title}")
    print(f"     - Status: {retrieved.status.value}")

    # Verify all fields match
    print("\n5️⃣  Verifying fields match...")
    errors = []

    if retrieved.agent_name != proposal.agent_name:
        errors.append(f"agent_name mismatch: {retrieved.agent_name} != {proposal.agent_name}")
    if retrieved.proposal_type != proposal.proposal_type:
        errors.append(f"proposal_type mismatch: {retrieved.proposal_type} != {proposal.proposal_type}")
    if retrieved.title != proposal.title:
        errors.append(f"title mismatch: {retrieved.title} != {proposal.title}")
    if retrieved.explanation != proposal.explanation:
        errors.append(f"explanation mismatch")
    if retrieved.inputs_used != proposal.inputs_used:
        errors.append(f"inputs_used mismatch")
    if retrieved.constraints != proposal.constraints:
        errors.append(f"constraints mismatch")
    if retrieved.data != proposal.data:
        errors.append(f"data mismatch")
    if retrieved.requires_approval != proposal.requires_approval:
        errors.append(f"requires_approval mismatch: {retrieved.requires_approval} != {proposal.requires_approval}")
    if retrieved.status != proposal.status:
        errors.append(f"status mismatch: {retrieved.status} != {proposal.status}")

    if errors:
        print("   ✗ FAILED: Field mismatches:")
        for error in errors:
            print(f"     - {error}")
        return False

    print("   ✓ All fields match!")

    # Test updating (add approval)
    print("\n6️⃣  Testing update (adding approval)...")
    retrieved.add_approval("alice", True, "Looks good!")
    await ProposalRepository.save(retrieved)
    print("   ✓ Added approval and saved")

    # Retrieve again and verify approval persisted
    print("\n7️⃣  Verifying approval persisted...")
    updated = await ProposalRepository.get_by_id(proposal.proposal_id)
    if "alice" not in updated.approvals:
        print("   ✗ FAILED: Approval not persisted!")
        return False
    if updated.approvals["alice"] != True:
        print("   ✗ FAILED: Approval value incorrect!")
        return False
    print(f"   ✓ Approval persisted: alice={updated.approvals['alice']}")
    print(f"     - Status: {updated.status.value}")

    # Test listing with filters
    print("\n8️⃣  Testing filtered listing...")

    # Filter by agent name
    filter_agent = ProposalFilter(agent_name="mutual-aid-matchmaker")
    results = await ProposalRepository.list_all(filter_agent)
    if len(results) == 0:
        print("   ✗ FAILED: No proposals found with agent filter!")
        return False
    print(f"   ✓ Found {len(results)} proposal(s) by agent 'mutual-aid-matchmaker'")

    # Filter by status
    filter_status = ProposalFilter(status=ProposalStatus.PENDING)
    results = await ProposalRepository.list_all(filter_status)
    if proposal.proposal_id not in [p.proposal_id for p in results]:
        print("   ✗ FAILED: Proposal not found with status filter!")
        return False
    print(f"   ✓ Found {len(results)} pending proposal(s)")

    # Filter by user (requires approval)
    filter_user = ProposalFilter(user_id="bob")
    results = await ProposalRepository.list_all(filter_user)
    if proposal.proposal_id not in [p.proposal_id for p in results]:
        print("   ✗ FAILED: Proposal not found with user filter!")
        return False
    print(f"   ✓ Found {len(results)} proposal(s) requiring approval from 'bob'")

    # Count by status
    print("\n9️⃣  Testing count by status...")
    count = await ProposalRepository.count_by_status(ProposalStatus.PENDING)
    if count == 0:
        print("   ✗ FAILED: Count returned 0!")
        return False
    print(f"   ✓ Count of pending proposals: {count}")

    # Cleanup
    print("\n🧹 Cleaning up...")
    deleted = await ProposalRepository.delete(proposal.proposal_id)
    if not deleted:
        print("   ✗ FAILED: Deletion failed!")
        return False
    print("   ✓ Test proposal deleted")

    await close_db()
    print("   ✓ Database closed")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!\n")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_proposal_persistence())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
