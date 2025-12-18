"""
LLM Client Abstract Base Class

Defines the interface all LLM backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """A message in a conversation"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    model: str
    finish_reason: str = "stop"
    tokens_used: int = 0
    cached: bool = False


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All backends (MLX, Ollama, Remote) must implement this interface.
    """

    def __init__(self, config: Any):
        """
        Initialize LLM client.

        Args:
            config: LLMConfig object with backend settings
        """
        self.config = config
        self._cache: Dict[str, LLMResponse] = {}

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)

        Returns:
            LLMResponse with generated text
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Multi-turn chat conversation.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            LLMResponse with assistant's reply
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM backend is available and responding.

        Returns:
            True if healthy, False otherwise
        """
        pass

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Generate cache key for a prompt"""
        key = f"{prompt}::{system_prompt or 'none'}"
        return key

    def _check_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Check if response is cached"""
        if not self.config.enable_caching:
            return None

        if cache_key in self._cache:
            response = self._cache[cache_key]
            response.cached = True
            logger.debug(f"Cache hit for prompt (key: {cache_key[:50]}...)")
            return response

        return None

    def _store_cache(self, cache_key: str, response: LLMResponse):
        """Store response in cache"""
        if self.config.enable_caching:
            self._cache[cache_key] = response
            logger.debug(f"Cached response (key: {cache_key[:50]}...)")

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "backend": self.config.backend,
            "model": self.config.model,
            "cache_size": len(self._cache),
            "cache_enabled": self.config.enable_caching,
        }
