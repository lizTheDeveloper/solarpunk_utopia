#!/usr/bin/env python3
"""
Test script for Agent API endpoints.

Verifies that the agent execution endpoints work correctly.
"""

import asyncio
import sys
from app.agents import MutualAidMatchmaker, approval_tracker


async def test_agent_execution():
    """Test that the mutual aid matchmaker agent can run and generate proposals"""
    print("\n=== Testing Agent Execution ===")

    # Create agent instance
    agent = MutualAidMatchmaker()
    print(f"✓ Created agent: {agent.agent_name}")

    # Run agent
    proposals = await agent.run()
    print(f"✓ Agent ran successfully")
    print(f"✓ Generated {len(proposals)} proposals")

    if len(proposals) > 0:
        proposal = proposals[0]
        print(f"\nFirst Proposal:")
        print(f"  ID: {proposal.proposal_id}")
        print(f"  Type: {proposal.proposal_type}")
        print(f"  Title: {proposal.title}")
        print(f"  Explanation: {proposal.explanation}")
        print(f"  Requires Approval: {proposal.requires_approval}")
        print(f"  Status: {proposal.status}")

        # Test serialization to dict format expected by API
        proposal_dict = {
            "id": proposal.proposal_id,
            "agent_name": proposal.agent_name,
            "proposal_type": proposal.proposal_type,
            "title": proposal.title,
            "explanation": proposal.explanation,
            "inputs_used": proposal.inputs_used,
            "constraints": proposal.constraints,
            "data": proposal.data,
            "requires_approval": proposal.requires_approval,
            "approvals": proposal.approvals,
            "approval_reasons": proposal.approval_reasons,
            "status": proposal.status,
            "created_at": proposal.created_at.isoformat(),
            "expires_at": proposal.expires_at.isoformat() if proposal.expires_at else None,
            "bundle_id": proposal.bundle_id,
        }
        print(f"\n✓ Proposal can be serialized to API format")
    else:
        print("\n⚠ No proposals generated (this is OK if no matches found)")

    return True


async def test_approval_tracker():
    """Test approval tracker integration"""
    print("\n=== Testing Approval Tracker ===")

    # Create a test agent and run it
    agent = MutualAidMatchmaker()
    proposals = await agent.run()

    # Store proposals in approval tracker
    for proposal in proposals:
        await approval_tracker.store_proposal(proposal)

    print(f"✓ Stored {len(proposals)} proposals in approval tracker")

    # Test retrieval
    if len(proposals) > 0:
        proposal_id = proposals[0].proposal_id
        retrieved = await approval_tracker.get_proposal(proposal_id)
        if retrieved:
            print(f"✓ Successfully retrieved proposal: {proposal_id}")
        else:
            print(f"✗ Failed to retrieve proposal: {proposal_id}")
            return False

    # Get stats
    stats = approval_tracker.get_stats()
    print(f"✓ Approval tracker stats: {stats}")

    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent API Integration Test")
    print("=" * 60)

    try:
        success = True

        # Test 1: Agent execution
        if not await test_agent_execution():
            success = False

        # Test 2: Approval tracker
        if not await test_approval_tracker():
            success = False

        print("\n" + "=" * 60)
        if success:
            print("✅ All tests passed!")
            print("=" * 60)
            return 0
        else:
            print("❌ Some tests failed")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
