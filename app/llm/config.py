"""
LLM Configuration

Environment-based configuration for LLM backends.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM backend"""

    # Backend selection
    backend: str = "ollama"  # ollama, mlx, remote, mock

    # Model selection
    model: str = "qwen2.5:1.5b"  # Default to small model for testing

    # API settings (for remote backend)
    api_key: Optional[str] = None
    api_base: Optional[str] = None

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9

    # Timeout settings
    timeout_seconds: int = 30

    # Caching
    enable_caching: bool = True
    cache_dir: str = ".llm_cache"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables"""
        return cls(
            backend=os.getenv("LLM_BACKEND", "ollama"),
            model=os.getenv("LLM_MODEL", "qwen2.5:1.5b"),
            api_key=os.getenv("LLM_API_KEY"),
            api_base=os.getenv("LLM_API_BASE"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
            top_p=float(os.getenv("LLM_TOP_P", "0.9")),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT", "30")),
            enable_caching=os.getenv("LLM_ENABLE_CACHE", "true").lower() == "true",
            cache_dir=os.getenv("LLM_CACHE_DIR", ".llm_cache"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "backend": self.backend,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "timeout_seconds": self.timeout_seconds,
            "enable_caching": self.enable_caching,
        }
