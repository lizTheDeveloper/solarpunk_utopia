#!/usr/bin/env python3
"""
Mock test for Agent API endpoints using FastAPI TestClient.

Tests the API endpoints without starting an actual server.
"""

import sys
from fastapi.testclient import TestClient
from app.main import app


def test_list_agents():
    """Test GET /agents endpoint"""
    print("\n=== Test 1: GET /agents ===")
    client = TestClient(app)

    response = client.get("/agents")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "agents" in data, "Response should contain 'agents' field"
    assert "mutual-aid-matchmaker" in data["agents"], "Should include mutual-aid-matchmaker"

    print(f"✓ Found {len(data['agents'])} agents")
    print(f"✓ Agents: {', '.join(data['agents'])}")
    return True


def test_run_agent():
    """Test POST /agents/{agent_name}/run endpoint"""
    print("\n=== Test 2: POST /agents/mutual-aid-matchmaker/run ===")
    client = TestClient(app)

    response = client.post("/agents/mutual-aid-matchmaker/run", json={})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "agent_name" in data, "Response should contain 'agent_name'"
    assert "proposals" in data, "Response should contain 'proposals'"
    assert data["agent_name"] == "mutual-aid-matchmaker"

    print(f"✓ Agent executed: {data['agent_name']}")
    print(f"✓ Generated {len(data['proposals'])} proposals")

    # Verify proposal structure
    if len(data["proposals"]) > 0:
        proposal = data["proposals"][0]
        required_fields = [
            "id", "agent_name", "proposal_type", "title", "explanation",
            "inputs_used", "constraints", "data", "requires_approval",
            "approvals", "approval_reasons", "status", "created_at"
        ]

        for field in required_fields:
            assert field in proposal, f"Proposal should contain '{field}' field"

        print(f"✓ First proposal: {proposal['title']}")
        print(f"✓ Explanation: {proposal['explanation']}")
        print(f"✓ Requires approval from: {proposal['requires_approval']}")
        print(f"✓ Status: {proposal['status']}")

    return True


def test_list_proposals():
    """Test GET /agents/proposals endpoint"""
    print("\n=== Test 3: GET /agents/proposals ===")
    client = TestClient(app)

    # First run an agent to generate proposals
    client.post("/agents/mutual-aid-matchmaker/run", json={})

    # Now list proposals
    response = client.get("/agents/proposals")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "proposals" in data, "Response should contain 'proposals'"
    assert "total" in data, "Response should contain 'total'"

    print(f"✓ Listed {data['total']} proposals")
    return True


def test_get_agent_settings():
    """Test GET /agents/settings/{agent_name} endpoint"""
    print("\n=== Test 4: GET /agents/settings/mutual-aid-matchmaker ===")
    client = TestClient(app)

    response = client.get("/agents/settings/mutual-aid-matchmaker")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "agent_name" in data, "Response should contain 'agent_name'"
    assert "config" in data, "Response should contain 'config'"

    print(f"✓ Agent: {data['agent_name']}")
    print(f"✓ Config: {data['config']}")
    return True


def test_approve_proposal():
    """Test POST /agents/proposals/{proposal_id}/approve endpoint"""
    print("\n=== Test 5: POST /agents/proposals/{proposal_id}/approve ===")
    client = TestClient(app)

    # Run agent to generate proposals
    run_response = client.post("/agents/mutual-aid-matchmaker/run", json={})
    proposals = run_response.json()["proposals"]

    if len(proposals) == 0:
        print("⚠ No proposals to approve (skipping test)")
        return True

    proposal = proposals[0]
    proposal_id = proposal["id"]
    user_id = proposal["requires_approval"][0] if proposal["requires_approval"] else "test_user"

    # Approve the proposal
    response = client.post(
        f"/agents/proposals/{proposal_id}/approve",
        json={"user_id": user_id, "approved": True, "reason": "Test approval"}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"✓ Approved proposal: {proposal_id}")
    print(f"✓ Status: {data['status']}")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Agent API Mock Tests (using TestClient)")
    print("=" * 60)

    tests = [
        ("List Agents", test_list_agents),
        ("Run Agent", test_run_agent),
        ("List Proposals", test_list_proposals),
        ("Get Agent Settings", test_get_agent_settings),
        ("Approve Proposal", test_approve_proposal),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ Test failed: {test_name}")
        except Exception as e:
            failed += 1
            print(f"❌ Test failed: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
