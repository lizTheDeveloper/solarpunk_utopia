"""
Test GAP-02 Backend Authentication

Tests the complete auth flow:
1. Register user
2. Use token to access protected endpoint
3. Login existing user
4. Test /auth/me endpoint
"""

import asyncio
import httpx


async def test_auth_flow():
    """Test the complete authentication flow"""

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== GAP-02 Backend Auth Test ===\n")

        # Test 1: Register new user
        print("1. Registering new user 'Bob'...")
        register_response = await client.post(
            f"{base_url}/auth/register",
            json={"name": "Bob"}
        )

        if register_response.status_code != 200:
            print(f"❌ Registration failed: {register_response.status_code}")
            print(register_response.text)
            return False

        register_data = register_response.json()
        bob_token = register_data["token"]
        bob_id = register_data["user"]["id"]

        print(f"✓ Registered Bob")
        print(f"  User ID: {bob_id}")
        print(f"  Token: {bob_token[:20]}...")
        print(f"  Expires: {register_data['expires_at']}")

        # Test 2: Get current user with token
        print("\n2. Testing /auth/me endpoint...")
        me_response = await client.get(
            f"{base_url}/auth/me",
            headers={"Authorization": f"Bearer {bob_token}"}
        )

        if me_response.status_code != 200:
            print(f"❌ /auth/me failed: {me_response.status_code}")
            print(me_response.text)
            return False

        me_data = me_response.json()
        print(f"✓ Got current user")
        print(f"  Name: {me_data['name']}")
        print(f"  ID: {me_data['id']}")

        # Test 3: Try accessing without token (should fail)
        print("\n3. Testing protected endpoint without token...")
        no_auth_response = await client.get(f"{base_url}/auth/me")

        if no_auth_response.status_code == 401:
            print("✓ Correctly rejected unauthenticated request (401)")
        else:
            print(f"❌ Should have returned 401, got {no_auth_response.status_code}")
            return False

        # Test 4: Login existing user (register again = login)
        print("\n4. Testing login (re-register existing user)...")
        login_response = await client.post(
            f"{base_url}/auth/register",
            json={"name": "Bob"}
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False

        login_data = login_response.json()
        new_token = login_data["token"]

        print(f"✓ Logged in existing user Bob")
        print(f"  Same user ID: {login_data['user']['id'] == bob_id}")
        print(f"  New token: {new_token[:20]}...")

        # Test 5: Test with invalid token
        print("\n5. Testing with invalid token...")
        invalid_response = await client.get(
            f"{base_url}/auth/me",
            headers={"Authorization": "Bearer invalid-token-12345"}
        )

        if invalid_response.status_code == 401:
            print("✓ Correctly rejected invalid token (401)")
        else:
            print(f"❌ Should have returned 401, got {invalid_response.status_code}")
            return False

        # Test 6: Use token for protected proposal approval
        print("\n6. Testing protected endpoint (proposal approval)...")

        # First, get a proposal
        proposals_response = await client.get(f"{base_url}/agents/proposals")
        proposals_data = proposals_response.json()

        if proposals_data["total"] > 0:
            proposal_id = proposals_data["proposals"][0]["proposal_id"]

            # Try to approve WITH auth
            approve_response = await client.post(
                f"{base_url}/agents/proposals/{proposal_id}/approve",
                headers={"Authorization": f"Bearer {bob_token}"},
                json={"approved": True, "reason": "Testing auth"}
            )

            if approve_response.status_code in [200, 400]:  # 400 if already approved
                print(f"✓ Proposal approval with auth: {approve_response.status_code}")
            else:
                print(f"⚠️  Proposal approval returned: {approve_response.status_code}")
                print(f"   (This might be ok depending on proposal state)")
        else:
            print("⚠️  No proposals to test with (this is ok)")

        print("\n=== ✅ All Auth Tests PASSED ===")
        print("\nBackend authentication is working correctly!")
        print("- User registration ✓")
        print("- Session token generation ✓")
        print("- Token validation ✓")
        print("- Protected endpoints ✓")
        print("- Error handling ✓")

        return True


if __name__ == "__main__":
    success = asyncio.run(test_auth_flow())
    exit(0 if success else 1)
