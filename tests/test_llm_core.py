"""
Focused LLM Integration Test - Core Functionality Only

Tests just the LLM layer without database dependencies.
"""

import asyncio
import logging
from app.llm import get_llm_client, LLMConfig, LLMClient
from app.agents.framework import BaseAgent, Proposal, ProposalType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgent(BaseAgent):
    """Simple test agent without database dependencies"""

    async def analyze(self) -> list[Proposal]:
        """Use LLM to analyze and create a proposal"""

        # Test using LLM
        response = await self.use_llm(
            prompt="In one sentence, what's a key benefit of gift economies?",
            context={"agent": self.agent_name}
        )

        logger.info(f"LLM said: {response}")

        # Create proposal based on LLM response
        proposal = Proposal(
            agent_name=self.agent_name,
            proposal_type=ProposalType.MATCH,
            title="Test LLM-generated proposal",
            explanation=f"Based on LLM insight: {response}",
            inputs_used=["llm_response"],
            constraints=["test_only"],
            data={"llm_response": response},
            requires_approval=["test-user"],
        )

        return [proposal]


async def test_llm_backends():
    """Test all LLM backend configurations"""

    results = {
        "mock": False,
        "ollama": False,
        "agent_integration": False,
        "caching": False,
    }

    # Test 1: MockBackend
    logger.info("=== Test 1: MockBackend ===")
    try:
        config = LLMConfig(backend="mock")
        client = get_llm_client(config, allow_mock=True)

        response = await client.generate("Hello, world!")
        assert response.content.startswith("Mock response")
        assert response.tokens_used > 0
        assert await client.health_check() == True

        results["mock"] = True
        logger.info("✅ MockBackend: PASS")
    except Exception as e:
        logger.error(f"❌ MockBackend: FAIL - {e}")

    # Test 2: Ollama (if available)
    logger.info("\n=== Test 2: OllamaBackend ===")
    try:
        config = LLMConfig(backend="ollama", model="qwen3:4b")
        client = get_llm_client(config)

        if await client.health_check():
            logger.info("Ollama is running, attempting generation...")
            try:
                response = await client.generate("Hello!")
                logger.info(f"Response: {response.content[:100]}")
                results["ollama"] = True
                logger.info("✅ OllamaBackend: PASS")
            except Exception as e:
                logger.warning(f"⚠️  OllamaBackend: Partial (health check passed, generation failed: {e})")
        else:
            logger.warning("⚠️  OllamaBackend: Skipped (Ollama not running)")
    except Exception as e:
        logger.error(f"❌ OllamaBackend: FAIL - {e}")

    # Test 3: Agent Integration
    logger.info("\n=== Test 3: Agent Integration ===")
    try:
        config = LLMConfig(backend="mock")
        llm_client = get_llm_client(config, allow_mock=True)

        agent = TestAgent(
            agent_name="test-agent",
            llm_client=llm_client
        )

        proposals = await agent.run()
        assert len(proposals) > 0
        assert "Mock response" in proposals[0].explanation

        results["agent_integration"] = True
        logger.info("✅ Agent Integration: PASS")
    except Exception as e:
        logger.error(f"❌ Agent Integration: FAIL - {e}")

    # Test 4: Caching
    logger.info("\n=== Test 4: Response Caching ===")
    try:
        config = LLMConfig(backend="mock", enable_caching=True)
        client = get_llm_client(config, allow_mock=True)

        # First call
        response1 = await client.generate("Test prompt", system_prompt="System")
        assert response1.cached == False

        # Second call (should be cached)
        response2 = await client.generate("Test prompt", system_prompt="System")
        assert response2.cached == True
        assert response1.content == response2.content

        results["caching"] = True
        logger.info("✅ Response Caching: PASS")
    except Exception as e:
        logger.error(f"❌ Response Caching: FAIL - {e}")

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*60)

    passed = sum(results.values())
    total = len(results)

    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test:20s} {status}")

    logger.info("="*60)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("="*60)

    if passed == total:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed")

    return results


if __name__ == "__main__":
    results = asyncio.run(test_llm_backends())

    # Exit with appropriate code
    if all(results.values()):
        exit(0)
    else:
        exit(1)
