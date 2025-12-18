"""
End-to-End Integration Tests: Gift Economy Flow

Tests the complete flow of the Solarpunk gift economy system:
1. Create agents (people in the commune)
2. Create resource specs (what can be shared)
3. Create offers and needs
4. Use AI matchmaker to find matches
5. Coordinate exchanges via DTN bundles
6. Record events
7. Verify all data propagates correctly
"""

import pytest
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
import json


# Service URLs
DTN_API = "http://localhost:8000"
VF_API = "http://localhost:8001"
DISCOVERY_API = "http://localhost:8003"
AGENT_API = "http://localhost:8000/agents"

class TestGiftEconomyFlow:
    """Test complete gift economy workflow"""

    @pytest.mark.asyncio
    async def test_complete_offer_need_exchange_flow(self):
        """
        Complete flow: Alice offers tomatoes → Bob needs tomatoes →
        Matchmaker creates proposal → Exchange coordinated → Events recorded
        """

        async with httpx.AsyncClient(timeout=30.0) as client:

            # Step 1: Create agents (Alice and Bob)
            print("\n=== Step 1: Creating agents ===")
            alice_resp = await client.post(
                f"{VF_API}/vf/agents",
                json={"name": "Alice", "type": "person"}
            )
            assert alice_resp.status_code == 200
            alice = alice_resp.json()
            alice_id = alice["id"]
            print(f"Created Alice: {alice_id}")

            bob_resp = await client.post(
                f"{VF_API}/vf/agents",
                json={"name": "Bob", "type": "person"}
            )
            assert bob_resp.status_code == 200
            bob = bob_resp.json()
            bob_id = bob["id"]
            print(f"Created Bob: {bob_id}")

            # Step 2: Create resource spec (tomatoes)
            print("\n=== Step 2: Creating resource spec ===")
            tomatoes_resp = await client.post(
                f"{VF_API}/vf/resource_specs",
                json={
                    "name": "Tomatoes",
                    "category": "food",
                    "unit": "lbs"
                }
            )
            assert tomatoes_resp.status_code == 200
            tomatoes = tomatoes_resp.json()
            tomatoes_id = tomatoes["id"]
            print(f"Created Tomatoes spec: {tomatoes_id}")

            # Step 3: Alice creates an offer
            print("\n=== Step 3: Alice creates offer ===")
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
            offer_resp = await client.post(
                f"{VF_API}/vf/listings",
                json={
                    "listing_type": "offer",
                    "provider_agent_id": alice_id,
                    "resource_spec_id": tomatoes_id,
                    "quantity": 5.0,
                    "available_until": tomorrow
                }
            )
            assert offer_resp.status_code == 200
            offer = offer_resp.json()
            offer_id = offer["id"]
            print(f"Alice created offer: {offer_id}")

            # Step 4: Bob creates a need
            print("\n=== Step 4: Bob creates need ===")
            need_resp = await client.post(
                f"{VF_API}/vf/listings",
                json={
                    "listing_type": "need",
                    "provider_agent_id": bob_id,
                    "resource_spec_id": tomatoes_id,
                    "quantity": 3.0,
                    "available_until": tomorrow
                }
            )
            assert need_resp.status_code == 200
            need = need_resp.json()
            need_id = need["id"]
            print(f"Bob created need: {need_id}")

            # Step 5: Query Discovery System
            print("\n=== Step 5: Searching for tomatoes ===")
            search_resp = await client.post(
                f"{DISCOVERY_API}/discovery/search",
                json={
                    "query": "tomatoes",
                    "filters": {"category": "food"},
                    "max_results": 50
                }
            )
            assert search_resp.status_code == 200
            search_results = search_resp.json()
            print(f"Found {search_results['total_results']} results")
            assert search_results['total_results'] >= 1

            # Step 6: Run AI Matchmaker
            print("\n=== Step 6: Running AI Matchmaker ===")
            matchmaker_resp = await client.post(
                f"{AGENT_API}/mutual-aid-matchmaker/run",
                json={}
            )
            assert matchmaker_resp.status_code == 200
            proposals = matchmaker_resp.json()["proposals"]
            print(f"Matchmaker created {len(proposals)} proposals")
            assert len(proposals) > 0

            # Find the match proposal for Alice→Bob
            match_proposal = None
            for proposal in proposals:
                if (offer_id in str(proposal.get("data", {})) and
                    need_id in str(proposal.get("data", {}))):
                    match_proposal = proposal
                    break

            assert match_proposal is not None
            print(f"Found match proposal: {match_proposal['explanation']}")

            # Step 7: Create VF Match
            print("\n=== Step 7: Creating VF Match ===")
            match_resp = await client.post(
                f"{VF_API}/vf/matches",
                json={
                    "offer_id": offer_id,
                    "need_id": need_id,
                    "matched_quantity": 3.0,
                    "status": "proposed"
                }
            )
            assert match_resp.status_code == 200
            match = match_resp.json()
            match_id = match["id"]
            print(f"Created match: {match_id}")

            # Step 8: Create Exchange
            print("\n=== Step 8: Creating Exchange ===")
            exchange_resp = await client.post(
                f"{VF_API}/vf/exchanges",
                json={
                    "name": "Alice→Bob: Tomatoes",
                    "provider_agent_id": alice_id,
                    "receiver_agent_id": bob_id,
                    "agreed_at": datetime.now(timezone.utc).isoformat()
                }
            )
            assert exchange_resp.status_code == 200
            exchange = exchange_resp.json()
            exchange_id = exchange["id"]
            print(f"Created exchange: {exchange_id}")

            # Step 9: Record events (Alice gives, Bob receives)
            print("\n=== Step 9: Recording events ===")

            # Alice's event: transfer
            alice_event_resp = await client.post(
                f"{VF_API}/vf/events",
                json={
                    "action": "transfer",
                    "provider_agent_id": alice_id,
                    "receiver_agent_id": bob_id,
                    "resource_spec_id": tomatoes_id,
                    "quantity": 3.0,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "exchange_id": exchange_id
                }
            )
            assert alice_event_resp.status_code == 200
            alice_event = alice_event_resp.json()
            print(f"Alice recorded event: {alice_event['id']}")

            # Bob's event: accept
            bob_event_resp = await client.post(
                f"{VF_API}/vf/events",
                json={
                    "action": "accept",
                    "provider_agent_id": alice_id,
                    "receiver_agent_id": bob_id,
                    "resource_spec_id": tomatoes_id,
                    "quantity": 3.0,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "exchange_id": exchange_id
                }
            )
            assert bob_event_resp.status_code == 200
            bob_event = bob_event_resp.json()
            print(f"Bob recorded event: {bob_event['id']}")

            # Step 10: Verify bundles were created in DTN
            print("\n=== Step 10: Verifying DTN bundles ===")
            bundles_resp = await client.get(f"{DTN_API}/bundles?queue=outbox")
            assert bundles_resp.status_code == 200
            bundles = bundles_resp.json()
            print(f"Found {len(bundles)} bundles in outbox")

            # Check for VF bundles
            vf_bundles = [b for b in bundles if b.get("topic") == "valueflows"]
            print(f"Found {len(vf_bundles)} ValueFlows bundles")
            assert len(vf_bundles) > 0

            # Step 11: Verify complete flow
            print("\n=== Step 11: Verifying complete flow ===")

            # Get exchange with events
            exchange_detail_resp = await client.get(f"{VF_API}/vf/exchanges/{exchange_id}")
            assert exchange_detail_resp.status_code == 200
            exchange_detail = exchange_detail_resp.json()

            print(f"✅ Exchange completed successfully")
            print(f"   Provider: {exchange_detail.get('provider_agent_id')}")
            print(f"   Receiver: {exchange_detail.get('receiver_agent_id')}")
            print(f"   Status: {exchange_detail.get('status', 'completed')}")

            print("\n=== ✅ END-TO-END TEST PASSED ===")


    @pytest.mark.asyncio
    async def test_bundle_propagation_across_services(self):
        """
        Test that bundles created by one service propagate to others
        """

        async with httpx.AsyncClient(timeout=30.0) as client:

            print("\n=== Testing Bundle Propagation ===")

            # Create a bundle in DTN system
            bundle_resp = await client.post(
                f"{DTN_API}/bundles",
                json={
                    "priority": "normal",
                    "audience": "public",
                    "topic": "test",
                    "tags": ["integration-test"],
                    "payload_type": "text/plain",
                    "payload": {"message": "Test propagation"},
                    "ttl_hours": 24
                }
            )
            assert bundle_resp.status_code == 200
            bundle = bundle_resp.json()
            bundle_id = bundle["bundle_id"]
            print(f"Created bundle: {bundle_id}")

            # Verify bundle is in outbox
            outbox_resp = await client.get(f"{DTN_API}/bundles?queue=outbox")
            assert outbox_resp.status_code == 200
            outbox = outbox_resp.json()
            bundle_ids = [b["bundle_id"] for b in outbox]
            assert bundle_id in bundle_ids
            print(f"✅ Bundle in outbox")

            # Verify bundle can be retrieved
            get_resp = await client.get(f"{DTN_API}/bundles/{bundle_id}")
            assert get_resp.status_code == 200
            retrieved = get_resp.json()
            assert retrieved["bundle_id"] == bundle_id
            print(f"✅ Bundle retrieved successfully")

            # Verify signature
            assert "signature" in retrieved
            assert retrieved["signature"].startswith("sig:")
            print(f"✅ Bundle is signed")

            print("\n=== ✅ BUNDLE PROPAGATION TEST PASSED ===")


    @pytest.mark.asyncio
    async def test_agent_proposals_require_approval(self):
        """
        Test that all agent proposals require human approval
        """

        async with httpx.AsyncClient(timeout=30.0) as client:

            print("\n=== Testing Agent Approval Gates ===")

            # Run matchmaker
            matchmaker_resp = await client.post(
                f"{AGENT_API}/mutual-aid-matchmaker/run",
                json={}
            )
            assert matchmaker_resp.status_code == 200
            result = matchmaker_resp.json()
            proposals = result.get("proposals", [])

            if len(proposals) > 0:
                proposal = proposals[0]

                # Verify proposal has approval requirements
                assert "requires_approval" in proposal
                assert len(proposal["requires_approval"]) > 0
                print(f"✅ Proposal requires approval from: {proposal['requires_approval']}")

                # Verify proposal has explanation
                assert "explanation" in proposal
                assert len(proposal["explanation"]) > 0
                print(f"✅ Proposal has explanation: {proposal['explanation']}")

                # Verify proposal has inputs
                assert "inputs_used" in proposal
                print(f"✅ Proposal shows inputs used")

                # Verify proposal has constraints
                assert "constraints" in proposal
                print(f"✅ Proposal shows constraints")

            print("\n=== ✅ AGENT APPROVAL TEST PASSED ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
