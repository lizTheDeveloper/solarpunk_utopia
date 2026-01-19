"""
Tests for the 7 new philosophical agents.

Tests basic instantiation and proposal generation.
"""

import pytest
from app.agents import (
    GiftFlowAgent,
    GovernanceCircleAgent,
    ConquestOfBreadAgent,
    InsurrectionaryJoyAgent,
    RadicalInclusionAgent,
    ConscientizationAgent,
    CounterPowerAgent,
    AgentConfig,
    ProposalType,
)


@pytest.mark.asyncio
async def test_gift_flow_agent_instantiation():
    """Test Gift Flow Agent can be instantiated"""
    agent = GiftFlowAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "gift-flow"
    assert agent.enabled


@pytest.mark.asyncio
async def test_gift_flow_agent_burnout_detection():
    """Test Gift Flow Agent detects burnout"""
    agent = GiftFlowAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate at least one burnout care alert (mock data)
    assert len(proposals) >= 1
    assert proposals[0].proposal_type == ProposalType.BURNOUT_CARE_ALERT
    assert "care" in proposals[0].explanation.lower()


@pytest.mark.asyncio
async def test_governance_circle_agent_instantiation():
    """Test Governance Circle Agent can be instantiated"""
    agent = GovernanceCircleAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "governance-circle"
    assert agent.enabled


@pytest.mark.asyncio
async def test_governance_circle_agent_proposals():
    """Test Governance Circle Agent generates proposals"""
    agent = GovernanceCircleAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate mediation requests and governance proposals
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.MEDIATION_REQUEST in proposal_types or \
           ProposalType.GOVERNANCE_PROPOSAL in proposal_types


@pytest.mark.asyncio
async def test_conquest_of_bread_agent_instantiation():
    """Test Conquest of Bread Agent can be instantiated"""
    agent = ConquestOfBreadAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "conquest-of-bread"
    assert agent.enabled


@pytest.mark.asyncio
async def test_conquest_of_bread_agent_mode_toggles():
    """Test Conquest of Bread Agent proposes mode toggles"""
    agent = ConquestOfBreadAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate heap mode or rationing proposals
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.HEAP_MODE_TOGGLE in proposal_types or \
           ProposalType.RATIONING_MODE in proposal_types


@pytest.mark.asyncio
async def test_insurrectionary_joy_agent_instantiation():
    """Test Insurrectionary Joy Agent can be instantiated"""
    agent = InsurrectionaryJoyAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "insurrectionary-joy"
    assert agent.enabled


@pytest.mark.asyncio
async def test_insurrectionary_joy_agent_joy_strike():
    """Test Insurrectionary Joy Agent proposes joy strike"""
    agent = InsurrectionaryJoyAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate joy-related proposals
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.JOY_STRIKE in proposal_types or \
           ProposalType.DANCE_PARTY in proposal_types or \
           ProposalType.BUREAUCRACY_JAM in proposal_types


@pytest.mark.asyncio
async def test_radical_inclusion_agent_instantiation():
    """Test Radical Inclusion Agent can be instantiated"""
    agent = RadicalInclusionAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "radical-inclusion"
    assert agent.enabled


@pytest.mark.asyncio
async def test_radical_inclusion_agent_marginality_warnings():
    """Test Radical Inclusion Agent generates marginality warnings"""
    agent = RadicalInclusionAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate marginality warnings and care work recognition
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.MARGINALITY_WARNING in proposal_types or \
           ProposalType.CARE_WORK_RECOGNITION in proposal_types


@pytest.mark.asyncio
async def test_conscientization_agent_instantiation():
    """Test Conscientization Agent can be instantiated"""
    agent = ConscientizationAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "conscientization"
    assert agent.enabled


@pytest.mark.asyncio
async def test_conscientization_agent_learning_bridges():
    """Test Conscientization Agent bridges learning to action"""
    agent = ConscientizationAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate resource requests, mentor matches, or culture circles
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.RESOURCE_REQUEST in proposal_types or \
           ProposalType.MENTOR_MATCH in proposal_types or \
           ProposalType.CULTURE_CIRCLE in proposal_types


@pytest.mark.asyncio
async def test_counter_power_agent_instantiation():
    """Test Counter-Power Agent can be instantiated"""
    agent = CounterPowerAgent(config=AgentConfig(enabled=True))
    assert agent.agent_name == "counter-power"
    assert agent.enabled


@pytest.mark.asyncio
async def test_counter_power_agent_centralization_detection():
    """Test Counter-Power Agent detects centralization"""
    agent = CounterPowerAgent(config=AgentConfig(enabled=True))
    proposals = await agent.analyze()

    # Should generate centralization warnings or warlord alerts
    assert len(proposals) >= 1
    proposal_types = [p.proposal_type for p in proposals]
    assert ProposalType.CENTRALIZATION_WARNING in proposal_types or \
           ProposalType.WARLORD_ALERT in proposal_types or \
           ProposalType.PRUNING_PROMPT in proposal_types


@pytest.mark.asyncio
async def test_all_agents_have_transparency():
    """Test all agents include transparency fields in proposals"""
    agents = [
        GiftFlowAgent(),
        GovernanceCircleAgent(),
        ConquestOfBreadAgent(),
        InsurrectionaryJoyAgent(),
        RadicalInclusionAgent(),
        ConscientizationAgent(),
        CounterPowerAgent(),
    ]

    for agent in agents:
        proposals = await agent.analyze()
        assert len(proposals) > 0, f"{agent.agent_name} generated no proposals"

        for proposal in proposals:
            # Check required transparency fields
            assert proposal.explanation, f"{agent.agent_name} missing explanation"
            assert proposal.inputs_used, f"{agent.agent_name} missing inputs_used"
            assert isinstance(proposal.constraints, list), f"{agent.agent_name} constraints not a list"


@pytest.mark.asyncio
async def test_proposal_types_are_unique():
    """Test that each agent uses appropriate proposal types"""
    gift_flow = GiftFlowAgent()
    governance = GovernanceCircleAgent()
    bread = ConquestOfBreadAgent()
    joy = InsurrectionaryJoyAgent()
    inclusion = RadicalInclusionAgent()
    conscient = ConscientizationAgent()
    counter = CounterPowerAgent()

    # Run all agents
    gift_proposals = await gift_flow.analyze()
    gov_proposals = await governance.analyze()
    bread_proposals = await bread.analyze()
    joy_proposals = await joy.analyze()
    inclusion_proposals = await inclusion.analyze()
    conscient_proposals = await conscient.analyze()
    counter_proposals = await counter.analyze()

    # Check proposal types are appropriate
    gift_types = {p.proposal_type for p in gift_proposals}
    assert ProposalType.BURNOUT_CARE_ALERT in gift_types

    gov_types = {p.proposal_type for p in gov_proposals}
    assert ProposalType.MEDIATION_REQUEST in gov_types or \
           ProposalType.GOVERNANCE_PROPOSAL in gov_types

    bread_types = {p.proposal_type for p in bread_proposals}
    assert ProposalType.HEAP_MODE_TOGGLE in bread_types or \
           ProposalType.RATIONING_MODE in bread_types

    joy_types = {p.proposal_type for p in joy_proposals}
    assert ProposalType.JOY_STRIKE in joy_types or \
           ProposalType.DANCE_PARTY in joy_types or \
           ProposalType.BUREAUCRACY_JAM in joy_types

    inclusion_types = {p.proposal_type for p in inclusion_proposals}
    assert ProposalType.MARGINALITY_WARNING in inclusion_types or \
           ProposalType.CARE_WORK_RECOGNITION in inclusion_types

    conscient_types = {p.proposal_type for p in conscient_proposals}
    assert ProposalType.RESOURCE_REQUEST in conscient_types or \
           ProposalType.MENTOR_MATCH in conscient_types or \
           ProposalType.CULTURE_CIRCLE in conscient_types

    counter_types = {p.proposal_type for p in counter_proposals}
    assert ProposalType.CENTRALIZATION_WARNING in counter_types or \
           ProposalType.WARLORD_ALERT in counter_types or \
           ProposalType.PRUNING_PROMPT in counter_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
