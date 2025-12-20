"""
LLM Backend Implementations

Concrete implementations for different LLM providers:
- OllamaBackend: Local inference via Ollama (Raspberry Pi, Linux, Mac)
- MLXBackend: Apple Silicon optimized via MLX
- RemoteBackend: OpenAI/Anthropic/other APIs
- MockBackend: Testing without real LLM
"""

import asyncio
import httpx
import logging
from typing import List, Optional

from .client import LLMClient, LLMMessage, LLMResponse
from .config import LLMConfig

logger = logging.getLogger(__name__)


class OllamaBackend(LLMClient):
    """
    Ollama backend for local inference.

    Best for: Raspberry Pi, Linux servers, cross-platform deployment
    Models: qwen2.5:1.5b, llama3.2:1b, phi3:mini
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.api_base or "http://localhost:11434"
        self.client = httpx.AsyncClient(timeout=config.timeout_seconds)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate text using Ollama API"""
        # Check cache
        cache_key = self._get_cache_key(prompt, system_prompt)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            # Build full prompt (Ollama /api/generate uses single prompt, not messages)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Call Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens,
                        "top_p": self.config.top_p,
                    },
                },
            )

            response.raise_for_status()
            data = response.json()

            # Parse response
            content = data["response"]
            result = LLMResponse(
                content=content,
                model=self.config.model,
                finish_reason=data.get("done_reason", "stop"),
                tokens_used=data.get("eval_count", 0),
                cached=False,
            )

            # Cache result
            self._store_cache(cache_key, result)

            logger.info(
                f"Ollama generated {result.tokens_used} tokens "
                f"(model: {self.config.model})"
            )
            return result

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Multi-turn chat with Ollama (converts to single prompt)"""
        try:
            # Convert messages to single prompt
            prompt_parts = []
            for msg in messages:
                if msg.role == "system":
                    prompt_parts.append(f"System: {msg.content}")
                elif msg.role == "user":
                    prompt_parts.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    prompt_parts.append(f"Assistant: {msg.content}")

            full_prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature or self.config.temperature,
                        "num_predict": max_tokens or self.config.max_tokens,
                    },
                },
            )

            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["response"],
                model=self.config.model,
                tokens_used=data.get("eval_count", 0),
            )

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.ConnectError as e:
            logger.debug(f"Ollama not reachable at {self.base_url}: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.warning(f"Ollama health check timed out: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama returned error status: {e}")
            return False
        except Exception as e:
            # Unexpected errors should be logged for investigation
            logger.error(f"Unexpected error checking Ollama health: {e}", exc_info=True)
            return False


class MLXBackend(LLMClient):
    """
    MLX backend for Apple Silicon.

    Best for: Mac development, Apple Silicon optimization
    Requires: mlx-lm package
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None

    async def _load_model(self):
        """Lazy load MLX model"""
        if self._model is not None:
            return

        try:
            import mlx.core as mx
            from mlx_lm import load, generate

            logger.info(f"Loading MLX model: {self.config.model}")
            self._model, self._tokenizer = load(self.config.model)
            logger.info(f"MLX model loaded successfully")

        except ImportError:
            raise ImportError(
                "MLX backend requires 'mlx' and 'mlx-lm' packages. "
                "Install with: pip install mlx mlx-lm"
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate text using MLX"""
        # Check cache
        cache_key = self._get_cache_key(prompt, system_prompt)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        await self._load_model()

        try:
            from mlx_lm import generate

            # Format prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"

            # Generate
            response_text = generate(
                self._model,
                self._tokenizer,
                prompt=full_prompt,
                temp=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )

            result = LLMResponse(
                content=response_text,
                model=self.config.model,
                tokens_used=len(self._tokenizer.encode(response_text)),
            )

            self._store_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"MLX generation failed: {e}")
            raise

    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Chat not yet implemented for MLX"""
        # For now, convert to single prompt
        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        return await self.generate(prompt, temperature=temperature, max_tokens=max_tokens)

    async def health_check(self) -> bool:
        """Check if MLX is available"""
        try:
            import mlx.core as mx
            return True
        except ImportError:
            return False


class RemoteBackend(LLMClient):
    """
    Remote API backend (OpenAI, Anthropic, etc.).

    Best for: Development, fallback when local inference unavailable
    Requires: API key
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(timeout=config.timeout_seconds)

        # Detect provider from model name
        if "gpt" in config.model.lower():
            self.provider = "openai"
            self.base_url = config.api_base or "https://api.openai.com/v1"
        elif "claude" in config.model.lower():
            self.provider = "anthropic"
            self.base_url = config.api_base or "https://api.anthropic.com/v1"
        else:
            self.provider = "openai"  # Default to OpenAI-compatible
            self.base_url = config.api_base or "https://api.openai.com/v1"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate via remote API"""
        cache_key = self._get_cache_key(prompt, system_prompt)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature or self.config.temperature,
                    "max_tokens": max_tokens or self.config.max_tokens,
                },
            )

            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            result = LLMResponse(
                content=content,
                model=self.config.model,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
            )

            self._store_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Remote API call failed: {e}")
            raise

    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Multi-turn chat via API"""
        # Similar to generate but with all messages
        api_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.config.model,
                "messages": api_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            },
        )

        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=self.config.model,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
        )

    async def health_check(self) -> bool:
        """Check if API is reachable"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            return response.status_code == 200
        except httpx.ConnectError as e:
            logger.debug(f"Remote API not reachable at {self.base_url}: {e}")
            return False
        except httpx.TimeoutException as e:
            logger.warning(f"Remote API health check timed out: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Remote API returned error status: {e}")
            return False
        except Exception as e:
            # Unexpected errors should be logged for investigation
            logger.error(f"Unexpected error checking Remote API health: {e}", exc_info=True)
            return False


class MockBackend(LLMClient):
    """
    Mock backend for testing.

    Returns canned responses without calling any LLM.
    Useful for integration tests.
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Return mock response"""
        # Check cache
        cache_key = self._get_cache_key(prompt, system_prompt)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        # Generate mock response
        result = LLMResponse(
            content=f"Mock response to: {prompt[:50]}...",
            model="mock",
            tokens_used=10,
        )

        # Store in cache
        self._store_cache(cache_key, result)

        return result

    async def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Return mock chat response"""
        last_message = messages[-1].content if messages else ""
        return LLMResponse(
            content=f"Mock response to: {last_message[:50]}...",
            model="mock",
            tokens_used=10,
        )

    async def health_check(self) -> bool:
        """Mock backend is always healthy"""
        return True


def get_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """
    Factory function to get appropriate LLM client based on config.

    Args:
        config: LLMConfig object (defaults to environment-based config)

    Returns:
        Appropriate LLMClient implementation

    Example:
        >>> client = get_llm_client()  # Uses env vars
        >>> response = await client.generate("Hello world")
    """
    if config is None:
        config = LLMConfig.from_env()

    backend = config.backend.lower()

    if backend == "ollama":
        return OllamaBackend(config)
    elif backend == "mlx":
        return MLXBackend(config)
    elif backend == "remote":
        return RemoteBackend(config)
    elif backend == "mock":
        return MockBackend(config)
    else:
        logger.warning(
            f"Unknown backend '{backend}', falling back to mock. "
            f"Valid options: ollama, mlx, remote, mock"
        )
        return MockBackend(config)
