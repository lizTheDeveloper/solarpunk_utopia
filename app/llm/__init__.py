"""
LLM Integration Layer

Pluggable backend system for running AI agents with different LLM providers.
Supports local inference (MLX, Ollama) and remote APIs.
"""

from .client import LLMClient
from .backends import (
    MLXBackend,
    OllamaBackend,
    RemoteBackend,
    get_llm_client,
)
from .config import LLMConfig

__all__ = [
    "LLMClient",
    "MLXBackend",
    "OllamaBackend",
    "RemoteBackend",
    "LLMConfig",
    "get_llm_client",
]
