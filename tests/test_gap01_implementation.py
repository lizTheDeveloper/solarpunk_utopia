"""
Integration test for GAP-01: Proposal Approval → VF Bridge

Tests that approving a proposal creates both Match and Exchange entities.
"""

import asyncio
import httpx
from datetime import datetime, timedelta


async def test_gap01_proposal_execution():
    """
    Test the full flow:
    1. Create offer and need
    2. Run mutual-aid-matchmaker agent to create proposal
    3. Approve proposal (simulating both parties)
    4. Verify Match was created
    5. Verify Exchange was created
    """

    base_url = "http://localhost:8001"
    agents_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== GAP-01 Integration Test ===\n")

        # Step 1: Create an offer
        print("1. Creating offer...")
        offer_response = await client.post(
            f"{base_url}/vf/listings",
            json={
                "agent_id": "agent:alice",
                "listing_type": "offer",
                "resource_spec_id": "spec:tomatoes",
                "quantity": 5.0,
                "unit": "kg",
                "title": "Fresh tomatoes",
                "description": "Garden tomatoes, ready now",
                "available_from": datetime.now().isoformat(),
                "available_until": (datetime.now() + timedelta(days=3)).isoformat(),
            }
        )
        if offer_response.status_code != 200:
            print(f"❌ Failed to create offer: {offer_response.status_code}")
            print(offer_response.text)
            return False

        offer_data = offer_response.json()
        offer_id = offer_data.get("listing", {}).get("id")
        print(f"✓ Created offer: {offer_id}")

        # Step 2: Create a need
        print("\n2. Creating need...")
        need_response = await client.post(
            f"{base_url}/vf/listings",
            json={
                "agent_id": "agent:bob",
                "listing_type": "need",
                "resource_spec_id": "spec:tomatoes",
                "quantity": 3.0,
                "unit": "kg",
                "title": "Need tomatoes for sauce",
                "description": "Making pasta sauce this weekend",
                "available_until": (datetime.now() + timedelta(days=2)).isoformat(),
            }
        )
        if need_response.status_code != 200:
            print(f"❌ Failed to create need: {need_response.status_code}")
            print(need_response.text)
            return False

        need_data = need_response.json()
        need_id = need_data.get("listing", {}).get("id")
        print(f"✓ Created need: {need_id}")

        # Step 3: Run mutual-aid-matchmaker agent
        print("\n3. Running mutual-aid-matchmaker agent...")
        agent_response = await client.post(f"{agents_url}/agents/mutual-aid-matchmaker/run")
        if agent_response.status_code != 200:
            print(f"❌ Failed to run agent: {agent_response.status_code}")
            print(agent_response.text)
            return False

        agent_data = agent_response.json()
        proposals = agent_data.get("proposals", [])
        if not proposals:
            print("❌ No proposals created by agent")
            return False

        proposal_id = proposals[0].get("proposal_id")
        print(f"✓ Created proposal: {proposal_id}")
        print(f"  Title: {proposals[0].get('title')}")

        # Step 4: Approve proposal as Alice
        print("\n4. Approving proposal as Alice...")
        approve1_response = await client.post(
            f"{agents_url}/agents/proposals/{proposal_id}/approve",
            json={
                "user_id": "agent:alice",
                "approved": True,
                "reason": "Looks good!"
            }
        )
        if approve1_response.status_code != 200:
            print(f"❌ Failed to approve as Alice: {approve1_response.status_code}")
            print(approve1_response.text)
            return False

        print("✓ Alice approved")

        # Step 5: Approve proposal as Bob (should trigger execution)
        print("\n5. Approving proposal as Bob (should trigger execution)...")
        approve2_response = await client.post(
            f"{agents_url}/agents/proposals/{proposal_id}/approve",
            json={
                "user_id": "agent:bob",
                "approved": True,
                "reason": "Perfect timing!"
            }
        )
        if approve2_response.status_code != 200:
            print(f"❌ Failed to approve as Bob: {approve2_response.status_code}")
            print(approve2_response.text)
            return False

        approval_data = approve2_response.json()
        print("✓ Bob approved")
        print(f"  Proposal status: {approval_data.get('status')}")

        # Step 6: Verify Match was created
        print("\n6. Verifying Match was created...")
        matches_response = await client.get(f"{base_url}/vf/matches")
        if matches_response.status_code != 200:
            print(f"❌ Failed to fetch matches: {matches_response.status_code}")
            return False

        matches_data = matches_response.json()
        matches = matches_data.get("matches", [])
        match = next((m for m in matches if m.get("offer_id") == offer_id), None)

        if not match:
            print(f"❌ No match found for offer {offer_id}")
            print(f"   Found {len(matches)} matches total")
            return False

        match_id = match.get("id")
        print(f"✓ Match created: {match_id}")
        print(f"  Offer: {match.get('offer_id')}")
        print(f"  Need: {match.get('need_id')}")

        # Step 7: Verify Exchange was created
        print("\n7. Verifying Exchange was created...")
        exchanges_response = await client.get(f"{base_url}/vf/exchanges")
        if exchanges_response.status_code != 200:
            print(f"❌ Failed to fetch exchanges: {exchanges_response.status_code}")
            return False

        exchanges_data = exchanges_response.json()
        exchanges = exchanges_data.get("exchanges", [])
        exchange = next((e for e in exchanges if e.get("match_id") == match_id), None)

        if not exchange:
            print(f"❌ No exchange found for match {match_id}")
            print(f"   Found {len(exchanges)} exchanges total")
            return False

        exchange_id = exchange.get("id")
        print(f"✓ Exchange created: {exchange_id}")
        print(f"  Match: {exchange.get('match_id')}")
        print(f"  Provider: {exchange.get('provider_id')}")
        print(f"  Receiver: {exchange.get('receiver_id')}")
        print(f"  Quantity: {exchange.get('quantity')} {exchange.get('unit')}")
        print(f"  Status: {exchange.get('status')}")

        print("\n=== ✅ GAP-01 Test PASSED ===")
        print("Proposal approval successfully created Match and Exchange!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_gap01_proposal_execution())
    exit(0 if success else 1)
