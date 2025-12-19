#!/usr/bin/env python3
"""
Seed Demo Data for Solarpunk Mesh Network

Creates realistic demo data:
- Commune members (agents)
- Resource types (specs)
- Offers and needs (listings)
- Runs matchmaker to generate initial proposals

Usage:
    python scripts/seed_demo_data.py
"""

import asyncio
import httpx
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URLs
VF_API = "http://localhost:8001"
AGENT_API = "http://localhost:8000"


# Demo data definitions
COMMUNE_MEMBERS = [
    {"name": "Alice", "agent_type": "person", "description": "Permaculture gardener, loves tomatoes"},
    {"name": "Bob", "agent_type": "person", "description": "Tool library coordinator, master carpenter"},
    {"name": "Carol", "agent_type": "person", "description": "Community chef, batch cooking expert"},
    {"name": "David", "agent_type": "person", "description": "Solar installer, renewable energy advocate"},
    {"name": "Eve", "agent_type": "person", "description": "Herbalist and medicine maker"},
    {"name": "Frank", "agent_type": "person", "description": "Bike mechanic, loves repairing things"},
    {"name": "Grace", "agent_type": "person", "description": "Teacher, runs skill shares"},
    {"name": "Henry", "agent_type": "person", "description": "Beekeeper and honey producer"},
    {"name": "Iris", "agent_type": "person", "description": "Artist and community organizer"},
    {"name": "Jack", "agent_type": "person", "description": "Compost coordinator, soil scientist"},
]

RESOURCE_SPECS = [
    # Food
    {"name": "Tomatoes", "unit": "kg", "category": "food"},
    {"name": "Fresh Herbs", "unit": "bunch", "category": "food"},
    {"name": "Honey", "unit": "jar", "category": "food"},
    {"name": "Sourdough Bread", "unit": "loaf", "category": "food"},
    {"name": "Garden Vegetables", "unit": "kg", "category": "food"},
    # Tools
    {"name": "Hand Tools", "unit": "set", "category": "tools"},
    {"name": "Power Drill", "unit": "item", "category": "tools"},
    {"name": "Bicycle Repair Kit", "unit": "set", "category": "tools"},
    {"name": "Gardening Tools", "unit": "set", "category": "tools"},
    # Skills
    {"name": "Carpentry Skills", "unit": "hour", "category": "skills"},
    {"name": "Cooking Class", "unit": "session", "category": "skills"},
    {"name": "Garden Consultation", "unit": "hour", "category": "skills"},
    {"name": "Bike Repair Help", "unit": "hour", "category": "skills"},
    # Space (using housing category)
    {"name": "Workshop Space", "unit": "hour", "category": "housing"},
    {"name": "Kitchen Access", "unit": "hour", "category": "housing"},
]


async def seed_data():
    """Seed all demo data"""

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Step 1: Create resource specs
        logger.info("Creating resource specs...")
        specs = {}
        for spec_data in RESOURCE_SPECS:
            response = await client.post(
                f"{VF_API}/vf/resource_specs",
                json=spec_data
            )
            response.raise_for_status()
            spec = response.json()
            specs[spec_data["name"]] = spec["id"]
            logger.info(f"  ✓ {spec_data['name']}")

        # Step 2: Create commune members
        logger.info("\nCreating commune members...")
        members = {}
        for member_data in COMMUNE_MEMBERS:
            response = await client.post(
                f"{VF_API}/vf/agents",
                json=member_data
            )
            response.raise_for_status()
            member = response.json()
            members[member_data["name"]] = member["id"]
            logger.info(f"  ✓ {member_data['name']}")

        # Step 3: Create offers
        logger.info("\nCreating offers...")
        offers_data = [
            {"provider": "Alice", "resource": "Tomatoes", "quantity": 5.0, "description": "Fresh from the garden!"},
            {"provider": "Alice", "resource": "Fresh Herbs", "quantity": 10, "description": "Basil, cilantro, parsley"},
            {"provider": "Henry", "resource": "Honey", "quantity": 3, "description": "Raw local honey"},
            {"provider": "Carol", "resource": "Sourdough Bread", "quantity": 2, "description": "Baked this morning"},
            {"provider": "Bob", "resource": "Hand Tools", "quantity": 2, "description": "Hammer, screwdriver set"},
            {"provider": "Bob", "resource": "Carpentry Skills", "quantity": 10, "description": "Available for projects"},
            {"provider": "David", "resource": "Power Drill", "quantity": 1, "description": "Cordless, fully charged"},
            {"provider": "Frank", "resource": "Bike Repair Help", "quantity": 5, "description": "Fix flats, tune-ups"},
            {"provider": "Grace", "resource": "Cooking Class", "quantity": 2, "description": "Fermentation basics"},
            {"provider": "Eve", "resource": "Garden Consultation", "quantity": 8, "description": "Permaculture design"},
            {"provider": "Jack", "resource": "Garden Vegetables", "quantity": 15, "description": "Mixed seasonal veg"},
            {"provider": "Iris", "resource": "Workshop Space", "quantity": 20, "description": "Community art studio"},
            {"provider": "Carol", "resource": "Kitchen Access", "quantity": 10, "description": "Commercial kitchen time"},
            {"provider": "Bob", "resource": "Gardening Tools", "quantity": 1, "description": "Shovels, rakes, hoes"},
            {"provider": "Alice", "resource": "Garden Vegetables", "quantity": 8, "description": "Leafy greens mostly"},
            {"provider": "Henry", "resource": "Garden Consultation", "quantity": 5, "description": "Pollinator gardens"},
            {"provider": "Frank", "resource": "Bicycle Repair Kit", "quantity": 1, "description": "Complete kit with tools"},
            {"provider": "David", "resource": "Carpentry Skills", "quantity": 6, "description": "Solar panel mounting"},
            {"provider": "Eve", "resource": "Fresh Herbs", "quantity": 8, "description": "Medicinal herbs"},
            {"provider": "Grace", "resource": "Cooking Class", "quantity": 3, "description": "Batch cooking workshop"},
        ]

        for offer_data in offers_data:
            unit = next(s["unit"] for s in RESOURCE_SPECS if s["name"] == offer_data["resource"])
            response = await client.post(
                f"{VF_API}/vf/listings",
                json={
                    "resource_spec_id": specs[offer_data["resource"]],
                    "listing_type": "offer",
                    "quantity": offer_data["quantity"],
                    "unit": unit,
                    "agent_id": members[offer_data["provider"]],
                    "status": "active",
                    "description": offer_data.get("description", ""),
                }
            )
            response.raise_for_status()
            logger.info(f"  ✓ {offer_data['provider']} offers {offer_data['quantity']} {unit} {offer_data['resource']}")

        # Step 4: Create needs
        logger.info("\nCreating needs...")
        needs_data = [
            {"receiver": "Bob", "resource": "Tomatoes", "quantity": 2.0, "description": "For family dinner"},
            {"receiver": "Carol", "resource": "Garden Vegetables", "quantity": 10, "description": "For community meal prep"},
            {"receiver": "David", "resource": "Hand Tools", "quantity": 1, "description": "For solar installation"},
            {"receiver": "Eve", "resource": "Fresh Herbs", "quantity": 5, "description": "For medicine making"},
            {"receiver": "Frank", "resource": "Workshop Space", "quantity": 8, "description": "Bike repair session"},
            {"receiver": "Grace", "resource": "Kitchen Access", "quantity": 4, "description": "Cooking class"},
            {"receiver": "Henry", "resource": "Gardening Tools", "quantity": 1, "description": "Expanding apiary garden"},
            {"receiver": "Iris", "resource": "Carpentry Skills", "quantity": 5, "description": "Building art shelves"},
            {"receiver": "Jack", "resource": "Bike Repair Help", "quantity": 2, "description": "Flat tire needs fixing"},
            {"receiver": "Alice", "resource": "Honey", "quantity": 1, "description": "For sourdough baking"},
        ]

        for need_data in needs_data:
            unit = next(s["unit"] for s in RESOURCE_SPECS if s["name"] == need_data["resource"])
            response = await client.post(
                f"{VF_API}/vf/listings",
                json={
                    "resource_spec_id": specs[need_data["resource"]],
                    "listing_type": "need",
                    "quantity": need_data["quantity"],
                    "unit": unit,
                    "agent_id": members[need_data["receiver"]],
                    "status": "active",
                    "description": need_data.get("description", ""),
                }
            )
            response.raise_for_status()
            logger.info(f"  ✓ {need_data['receiver']} needs {need_data['quantity']} {unit} {need_data['resource']}")

        # Step 5: Run mutual aid matchmaker to generate proposals
        logger.info("\nRunning mutual aid matchmaker...")
        response = await client.post(f"{AGENT_API}/agents/mutual-aid-matchmaker/run")
        response.raise_for_status()
        result = response.json()
        proposals_count = result.get("proposals_created", 0)
        logger.info(f"  ✓ Created {proposals_count} match proposals")

        # Success summary
        logger.info("\n" + "="*60)
        logger.info("🌱 Demo data seeded successfully!")
        logger.info("="*60)
        logger.info(f"Resource Specs: {len(RESOURCE_SPECS)}")
        logger.info(f"Commune Members: {len(COMMUNE_MEMBERS)}")
        logger.info(f"Offers: {len(offers_data)}")
        logger.info(f"Needs: {len(needs_data)}")
        logger.info(f"Match Proposals: {proposals_count}")
        logger.info("\nNext steps:")
        logger.info("1. Visit http://localhost:3000/offers to see offers")
        logger.info("2. Visit http://localhost:3000/needs to see needs")
        logger.info("3. Visit http://localhost:3000/agents to approve proposals")
        logger.info("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(seed_data())
    except Exception as e:
        logger.error(f"Failed to seed data: {e}", exc_info=True)
        exit(1)
