#!/usr/bin/env python3
"""
Verify that the Agent API implementation matches integration test expectations.

This script simulates the exact calls made by test_end_to_end_gift_economy.py
"""

import sys
from fastapi.testclient import TestClient
from app.main import app


def test_integration_compatibility():
    """
    Simulate the exact integration test scenario from:
    tests/integration/test_end_to_end_gift_economy.py
    """
    print("=" * 70)
    print("Verifying Integration Test Compatibility")
    print("=" * 70)
    print()

    client = TestClient(app)
    AGENT_API = "/agents"

    # Simulate Step 6 from integration test (lines 124-133)
    print("=== Step 6: Running AI Matchmaker ===")
    print(f"POST {AGENT_API}/mutual-aid-matchmaker/run")
    print()

    matchmaker_resp = client.post(
        f"{AGENT_API}/mutual-aid-matchmaker/run",
        json={}
    )

    # Check status code
    assert matchmaker_resp.status_code == 200, \
        f"Expected status 200, got {matchmaker_resp.status_code}"
    print(f"✓ Status code: {matchmaker_resp.status_code}")

    # Get proposals
    result = matchmaker_resp.json()
    proposals = result.get("proposals", [])

    print(f"✓ Matchmaker created {len(proposals)} proposals")
    assert len(proposals) > 0, "Expected at least one proposal"
    print()

    # Simulate test_agent_proposals_require_approval (lines 295-334)
    print("=== Testing Agent Approval Gates ===")
    print()

    if len(proposals) > 0:
        proposal = proposals[0]

        # Test 1: Verify proposal has approval requirements
        print("Test 1: Checking 'requires_approval' field")
        assert "requires_approval" in proposal, \
            "Proposal must have 'requires_approval' field"
        assert len(proposal["requires_approval"]) > 0, \
            "Proposal must require approval from at least one party"
        print(f"✓ Proposal requires approval from: {proposal['requires_approval']}")
        print()

        # Test 2: Verify proposal has explanation
        print("Test 2: Checking 'explanation' field")
        assert "explanation" in proposal, \
            "Proposal must have 'explanation' field"
        assert len(proposal["explanation"]) > 0, \
            "Explanation must not be empty"
        print(f"✓ Proposal has explanation: {proposal['explanation']}")
        print()

        # Test 3: Verify proposal has inputs
        print("Test 3: Checking 'inputs_used' field")
        assert "inputs_used" in proposal, \
            "Proposal must have 'inputs_used' field"
        print(f"✓ Proposal shows inputs used: {proposal['inputs_used']}")
        print()

        # Test 4: Verify proposal has constraints
        print("Test 4: Checking 'constraints' field")
        assert "constraints" in proposal, \
            "Proposal must have 'constraints' field"
        print(f"✓ Proposal shows constraints: {proposal['constraints']}")
        print()

        # Additional checks for completeness
        print("=== Additional Completeness Checks ===")
        print()

        expected_fields = [
            "id", "agent_name", "proposal_type", "title",
            "explanation", "inputs_used", "constraints", "data",
            "requires_approval", "approvals", "approval_reasons",
            "status", "created_at"
        ]

        missing_fields = [f for f in expected_fields if f not in proposal]
        if missing_fields:
            print(f"⚠ Warning: Missing optional fields: {missing_fields}")
        else:
            print(f"✓ All expected fields present")
        print()

        # Verify field types
        print("Verifying field types:")
        assert isinstance(proposal["id"], str), "id must be string"
        print("✓ id is string")

        assert isinstance(proposal["agent_name"], str), "agent_name must be string"
        print("✓ agent_name is string")

        assert isinstance(proposal["requires_approval"], list), \
            "requires_approval must be list"
        print("✓ requires_approval is list")

        assert isinstance(proposal["constraints"], list), \
            "constraints must be list"
        print("✓ constraints is list")

        assert isinstance(proposal["inputs_used"], list), \
            "inputs_used must be list"
        print("✓ inputs_used is list")

        assert isinstance(proposal["data"], dict), "data must be dict"
        print("✓ data is dict")
        print()

        # Print full proposal structure for verification
        print("=== Full Proposal Structure ===")
        print(f"ID: {proposal['id']}")
        print(f"Agent: {proposal['agent_name']}")
        print(f"Type: {proposal['proposal_type']}")
        print(f"Title: {proposal['title']}")
        print(f"Explanation: {proposal['explanation']}")
        print(f"Status: {proposal['status']}")
        print(f"Requires Approval: {proposal['requires_approval']}")
        print(f"Inputs Used: {len(proposal['inputs_used'])} items")
        print(f"Constraints: {len(proposal['constraints'])} items")
        print(f"Data Keys: {list(proposal['data'].keys())}")
        print()

    print("=" * 70)
    print("✅ ALL INTEGRATION TEST COMPATIBILITY CHECKS PASSED")
    print("=" * 70)
    print()
    print("The API implementation is fully compatible with:")
    print("  tests/integration/test_end_to_end_gift_economy.py")
    print()
    print("Expected test behavior:")
    print("  ✓ POST /agents/mutual-aid-matchmaker/run returns 200")
    print("  ✓ Response contains 'proposals' array")
    print("  ✓ Each proposal has required fields:")
    print("    - requires_approval (non-empty list)")
    print("    - explanation (non-empty string)")
    print("    - inputs_used (list)")
    print("    - constraints (list)")
    print()

    return True


if __name__ == "__main__":
    try:
        test_integration_compatibility()
        sys.exit(0)
    except AssertionError as e:
        print()
        print("=" * 70)
        print("❌ COMPATIBILITY CHECK FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ UNEXPECTED ERROR")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
