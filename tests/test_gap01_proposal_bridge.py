"""
Test GAP-01: Proposal → VF Bridge

Verifies that when a proposal is approved, it creates actual VF entities.
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_proposal_to_vf_bridge():
    """
    Test the complete flow:
    1. Create offer and need
    2. Run mutual aid matchmaker
    3. Approve the proposal
    4. Verify VF Match was created
    """

    base_url = "http://localhost:8000"
    vf_url = "http://localhost:8001"

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Step 1: Create resource spec
        logger.info("Step 1: Creating resource spec (tomatoes)")
        spec_response = await client.post(
            f"{vf_url}/vf/resource_specs",
            json={
                "name": "Tomatoes",
                "unit": "kg",
                "category": "food",
            }
        )
        spec_response.raise_for_status()
        spec = spec_response.json()
        spec_id = spec["id"]
        logger.info(f"✓ Created resource spec: {spec_id}")

        # Step 2: Create test agents
        logger.info("Step 2: Creating test agents (alice, bob)")
        alice_response = await client.post(
            f"{vf_url}/vf/agents",
            json={"name": "Alice", "agent_type": "person"}
        )
        alice_response.raise_for_status()
        alice = alice_response.json()
        alice_id = alice["id"]

        bob_response = await client.post(
            f"{vf_url}/vf/agents",
            json={"name": "Bob", "agent_type": "person"}
        )
        bob_response.raise_for_status()
        bob = bob_response.json()
        bob_id = bob["id"]
        logger.info(f"✓ Created agents: alice={alice_id}, bob={bob_id}")

        # Step 3: Create offer (Alice has tomatoes)
        logger.info("Step 3: Creating offer (Alice offers 5kg tomatoes)")
        offer_response = await client.post(
            f"{vf_url}/vf/listings",
            json={
                "resource_spec_id": spec_id,
                "listing_type": "offer",
                "quantity": 5.0,
                "unit": "kg",
                "provider_id": alice_id,
                "status": "active",
            }
        )
        offer_response.raise_for_status()
        offer = offer_response.json()
        offer_id = offer["id"]
        logger.info(f"✓ Created offer: {offer_id}")

        # Step 4: Create need (Bob needs tomatoes)
        logger.info("Step 4: Creating need (Bob needs 3kg tomatoes)")
        need_response = await client.post(
            f"{vf_url}/vf/listings",
            json={
                "resource_spec_id": spec_id,
                "listing_type": "need",
                "quantity": 3.0,
                "unit": "kg",
                "receiver_id": bob_id,
                "status": "active",
            }
        )
        need_response.raise_for_status()
        need = need_response.json()
        need_id = need["id"]
        logger.info(f"✓ Created need: {need_id}")

        # Step 5: Run mutual aid matchmaker
        logger.info("Step 5: Running mutual aid matchmaker agent")
        run_response = await client.post(
            f"{base_url}/agents/mutual-aid-matchmaker/run"
        )
        run_response.raise_for_status()
        run_result = run_response.json()
        proposals = run_result.get("proposals", [])

        if not proposals:
            logger.error("❌ No proposals created by matchmaker")
            return False

        proposal_id = proposals[0]["proposal_id"]
        logger.info(f"✓ Matchmaker created proposal: {proposal_id}")

        # Step 6: Approve proposal (Alice approves)
        logger.info("Step 6: Alice approves the proposal")
        alice_approve = await client.post(
            f"{base_url}/agents/proposals/{proposal_id}/approve",
            json={
                "user_id": alice_id,
                "approved": True,
                "reason": "Happy to share!",
            }
        )
        alice_approve.raise_for_status()
        logger.info("✓ Alice approved")

        # Step 7: Approve proposal (Bob approves)
        logger.info("Step 7: Bob approves the proposal")
        bob_approve = await client.post(
            f"{base_url}/agents/proposals/{proposal_id}/approve",
            json={
                "user_id": bob_id,
                "approved": True,
                "reason": "Thank you!",
            }
        )
        bob_approve.raise_for_status()
        proposal = bob_approve.json()
        logger.info(f"✓ Bob approved - Proposal status: {proposal['status']}")

        # Step 8: Verify VF Match was created
        logger.info("Step 8: Verifying VF Match was created")
        matches_response = await client.get(f"{vf_url}/vf/matches")
        matches_response.raise_for_status()
        matches = matches_response.json()

        if not matches:
            logger.error("❌ No VF Match was created!")
            logger.error("This means GAP-01 is NOT fixed")
            return False

        match = matches[-1]  # Get most recent match
        logger.info(f"✓ VF Match created: {match['id']}")
        logger.info(f"  Offer: {match['offer_id']}")
        logger.info(f"  Need: {match['need_id']}")
        logger.info(f"  Quantity: {match['matched_quantity']} {match['unit']}")

        # Success!
        logger.info("\n" + "="*60)
        logger.info("🎉 GAP-01 TEST PASSED!")
        logger.info("Proposal → VF Bridge is working!")
        logger.info("="*60)

        return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_proposal_to_vf_bridge())
        exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
        exit(1)
