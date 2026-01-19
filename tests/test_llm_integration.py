"""
Test LLM Integration

Tests the LLM client abstraction with different backends.
"""

import asyncio
import logging
from app.llm import get_llm_client, LLMConfig
from app.agents import MutualAidMatchmaker
from app.services import AgentScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mock_backend():
    """Test with MockBackend (no external dependencies)"""
    logger.info("=== Testing MockBackend ===")

    config = LLMConfig(backend="mock", model="mock")
    client = get_llm_client(config, allow_mock=True)

    # Test basic generation
    response = await client.generate(
        prompt="What are the benefits of gift economies?",
        system_prompt="You are a solarpunk AI assistant.",
    )

    logger.info(f"Response: {response.content}")
    logger.info(f"Tokens used: {response.tokens_used}")
    logger.info(f"Cached: {response.cached}")

    # Test health check
    healthy = await client.health_check()
    logger.info(f"Health check: {healthy}")

    # Test stats
    stats = client.get_stats()
    logger.info(f"Stats: {stats}")


async def test_ollama_backend():
    """Test with Ollama backend (requires Ollama running)"""
    logger.info("\n=== Testing OllamaBackend ===")

    config = LLMConfig(
        backend="ollama",
        model="qwen2.5:1.5b",
        temperature=0.7,
        max_tokens=256,
    )
    client = get_llm_client(config)

    # Check if Ollama is running
    healthy = await client.health_check()
    if not healthy:
        logger.warning("Ollama not running. Start with: ollama serve")
        logger.warning("Then pull model with: ollama pull qwen2.5:1.5b")
        return

    logger.info("Ollama is running!")

    try:
        # Test basic generation
        response = await client.generate(
            prompt="In 2-3 sentences, explain what makes gift economies sustainable.",
            system_prompt="You are a solarpunk AI assistant for a commune.",
        )

        logger.info(f"Response: {response.content}")
        logger.info(f"Tokens used: {response.tokens_used}")

        # Test caching
        response2 = await client.generate(
            prompt="In 2-3 sentences, explain what makes gift economies sustainable.",
            system_prompt="You are a solarpunk AI assistant for a commune.",
        )

        logger.info(f"Cached: {response2.cached}")

    except Exception as e:
        logger.warning(f"Ollama test failed (may need model or API update): {e}")


async def test_agent_with_llm():
    """Test agent using LLM client"""
    logger.info("\n=== Testing Agent with LLM ===")

    # Create LLM client
    config = LLMConfig(backend="mock", model="mock")
    llm_client = get_llm_client(config, allow_mock=True)

    # Create agent with LLM
    agent = MutualAidMatchmaker(llm_client=llm_client)

    # Test use_llm method
    response = await agent.use_llm(
        prompt="Should we match an offer of 10kg tomatoes with a need for fresh vegetables?",
        context={"offer": "10kg tomatoes", "need": "fresh vegetables"},
    )

    logger.info(f"Agent LLM response: {response}")

    # Run agent to generate proposals
    proposals = await agent.run()
    logger.info(f"Agent created {len(proposals)} proposals")


async def test_scheduler():
    """Test agent scheduler"""
    logger.info("\n=== Testing Agent Scheduler ===")

    # Create scheduler with mock LLM
    config = LLMConfig(backend="mock", model="mock")
    scheduler = AgentScheduler(llm_config=config)

    # Get stats
    stats = scheduler.get_stats()
    logger.info(f"Scheduler stats: {stats}")

    # Run all agents once
    await scheduler.run_once()

    # Get updated stats
    stats = scheduler.get_stats()
    logger.info(f"Updated stats: {stats}")


async def main():
    """Run all tests"""
    await test_mock_backend()
    await test_ollama_backend()
    await test_agent_with_llm()
    await test_scheduler()

    logger.info("\n=== All Tests Complete ===")
    logger.info("To use Ollama:")
    logger.info("1. Install: curl -fsSL https://ollama.com/install.sh | sh")
    logger.info("2. Start: ollama serve")
    logger.info("3. Pull model: ollama pull qwen2.5:1.5b")
    logger.info("4. Set env: export LLM_BACKEND=ollama")
    logger.info("\nTo use MLX (Mac only):")
    logger.info("1. Install: pip install mlx mlx-lm")
    logger.info("2. Set env: export LLM_BACKEND=mlx")
    logger.info("\nTo use Remote API:")
    logger.info("1. Set env: export LLM_BACKEND=remote")
    logger.info("2. Set key: export LLM_API_KEY=your-key")
    logger.info("3. Set model: export LLM_MODEL=gpt-4 (or claude-3-opus)")


if __name__ == "__main__":
    asyncio.run(main())
