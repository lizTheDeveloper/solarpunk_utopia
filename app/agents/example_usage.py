"""
Example usage of the Commune OS Agent System.

This demonstrates how to:
1. Create and configure agents
2. Run agents to generate proposals
3. Review and approve proposals
4. Track approval status
"""

import asyncio
from datetime import datetime

from app.agents import (
    MutualAidMatchmaker,
    PerishablesDispatcher,
    WorkPartyScheduler,
    PermaculturePlanner,
    EducationPathfinder,
    InventoryAgent,
    CommonsRouterAgent,
    AgentConfig,
    approval_tracker,
)


async def demo_mutual_aid_matchmaker():
    """Demonstrate the Mutual Aid Matchmaker"""
    print("\n=== Mutual Aid Matchmaker Demo ===\n")

    # Create agent
    matchmaker = MutualAidMatchmaker(
        config=AgentConfig(enabled=True, check_interval_seconds=300)
    )

    # Run analysis (uses mock data)
    proposals = await matchmaker.run()

    print(f"Generated {len(proposals)} match proposals:\n")

    for proposal in proposals:
        print(f"Proposal ID: {proposal.proposal_id}")
        print(f"Title: {proposal.title}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Requires approval from: {', '.join(proposal.requires_approval)}")
        print(f"Match score: {proposal.data.get('match_score', 'N/A')}")
        print()

        # Store proposal
        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_perishables_dispatcher():
    """Demonstrate the Perishables Dispatcher"""
    print("\n=== Perishables Dispatcher Demo ===\n")

    dispatcher = PerishablesDispatcher(
        config=AgentConfig(enabled=True)
    )

    proposals = await dispatcher.run()

    print(f"Generated {len(proposals)} perishables proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Urgency: {proposal.data.get('urgency', 'unknown')}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Hours until expiry: {proposal.data.get('hours_until_expiry', 'N/A'):.1f}")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_work_party_scheduler():
    """Demonstrate the Work Party Scheduler"""
    print("\n=== Work Party Scheduler Demo ===\n")

    scheduler = WorkPartyScheduler(
        config=AgentConfig(enabled=True)
    )

    proposals = await scheduler.run()

    print(f"Generated {len(proposals)} work party proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Participants: {len(proposal.data.get('participants', []))}")
        print(f"Date/Time: {proposal.data.get('date_time', 'N/A')}")
        print(f"Location: {proposal.data.get('location', 'N/A')}")
        print(f"Skill coverage: {proposal.data.get('skill_coverage', {}).get('coverage_pct', 0)}%")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_permaculture_planner():
    """Demonstrate the Permaculture Planner"""
    print("\n=== Permaculture Seasonal Planner Demo ===\n")

    planner = PermaculturePlanner(
        config=AgentConfig(enabled=True),
        climate_zone="9b"
    )

    proposals = await planner.run()

    print(f"Generated {len(proposals)} seasonal plan proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Processes: {len(proposal.data.get('processes', []))}")
        print(f"Duration: {proposal.data.get('duration_weeks', 0)} weeks")
        print(f"Principles: {', '.join(proposal.data.get('principles', [])[:3])}")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_education_pathfinder():
    """Demonstrate the Education Pathfinder"""
    print("\n=== Education Pathfinder Demo ===\n")

    pathfinder = EducationPathfinder(
        config=AgentConfig(enabled=True)
    )

    proposals = await pathfinder.run()

    print(f"Generated {len(proposals)} learning path proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Skill gaps: {', '.join(proposal.data.get('skill_gaps', []))}")
        print(f"Lessons: {len(proposal.data.get('lessons', []))}")
        print(f"Days until commitment: {proposal.data.get('days_until_commitment', 'N/A')}")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_inventory_agent():
    """Demonstrate the Inventory Agent (opt-in)"""
    print("\n=== Inventory/Pantry Agent Demo ===\n")

    # Note: Inventory agent is disabled by default (opt-in)
    # User must explicitly enable it
    inventory_agent = InventoryAgent(
        config=AgentConfig(enabled=True)  # Opt-in
    )

    proposals = await inventory_agent.run()

    print(f"Generated {len(proposals)} inventory proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Explanation: {proposal.explanation}")
        print(f"Gap: {proposal.data.get('gap_quantity', 'N/A')} {proposal.data.get('gap_unit', '')}")
        print(f"Alternatives: {len(proposal.data.get('alternatives', []))}")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_commons_router():
    """Demonstrate the Commons Router Agent"""
    print("\n=== Commons Router Agent Demo ===\n")

    router = CommonsRouterAgent(
        config=AgentConfig(enabled=True),
        node_role="bridge",
        cache_budget_mb=1024,
    )

    proposals = await router.run()

    print(f"Generated {len(proposals)} cache optimization proposals:\n")

    for proposal in proposals:
        print(f"Title: {proposal.title}")
        print(f"Type: {proposal.proposal_type.value}")
        print(f"Explanation: {proposal.explanation}")
        print()

        await approval_tracker.store_proposal(proposal)

    return proposals


async def demo_approval_workflow():
    """Demonstrate the approval workflow"""
    print("\n=== Approval Workflow Demo ===\n")

    # Run matchmaker to generate proposals
    matchmaker = MutualAidMatchmaker()
    proposals = await matchmaker.run()

    if not proposals:
        print("No proposals generated")
        return

    # Store proposals
    for proposal in proposals:
        await approval_tracker.store_proposal(proposal)

    # Get first proposal
    proposal = proposals[0]
    print(f"Proposal: {proposal.title}")
    print(f"Requires approval from: {', '.join(proposal.requires_approval)}")
    print()

    # Get pending approvals for first user
    user_id = proposal.requires_approval[0]
    pending = await approval_tracker.get_pending_approvals(user_id)
    print(f"{user_id} has {len(pending)} pending approvals")
    print()

    # User approves
    print(f"{user_id} approves the proposal")
    await approval_tracker.approve_proposal(
        proposal_id=proposal.proposal_id,
        user_id=user_id,
        approved=True,
        reason="Looks good to me!"
    )

    # Check if there's a second user
    if len(proposal.requires_approval) > 1:
        user_id_2 = proposal.requires_approval[1]
        print(f"{user_id_2} also approves")
        await approval_tracker.approve_proposal(
            proposal_id=proposal.proposal_id,
            user_id=user_id_2,
            approved=True,
            reason="Works for me"
        )

    # Check approval status
    updated_proposal = await approval_tracker.get_proposal(proposal.proposal_id)
    print(f"\nProposal status: {updated_proposal.status.value}")
    print(f"Fully approved: {updated_proposal.is_fully_approved()}")
    print(f"Approvals: {updated_proposal.approvals}")
    print()


async def demo_stats():
    """Show approval tracker statistics"""
    print("\n=== Approval Tracker Statistics ===\n")

    stats = approval_tracker.get_stats()
    print(f"Total proposals: {stats['total']}")
    print(f"Pending: {stats['pending']}")
    print(f"Approved: {stats['approved']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Expired: {stats['expired']}")
    print(f"Executed: {stats['executed']}")
    print()


async def main():
    """Run all demos"""
    print("=" * 60)
    print("Commune OS Agent System - Demo")
    print("=" * 60)

    # Run each agent demo
    await demo_mutual_aid_matchmaker()
    await demo_perishables_dispatcher()
    await demo_work_party_scheduler()
    await demo_permaculture_planner()
    await demo_education_pathfinder()
    await demo_inventory_agent()
    await demo_commons_router()

    # Demonstrate approval workflow
    await demo_approval_workflow()

    # Show statistics
    await demo_stats()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
