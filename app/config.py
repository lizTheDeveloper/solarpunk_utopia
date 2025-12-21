"""
Central Configuration for DTN Bundle System

Environment-based configuration using pydantic_settings for type safety and validation.
All hardcoded values should be moved here.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Main application settings"""

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    json_logs: bool = Field(default=False, description="Output JSON logs (production) vs colored logs (dev)")

    # Database configuration
    database_url: str = Field(
        default="sqlite:///dtn_bundles.db",
        description="Database connection URL"
    )

    # DTN Bundle configuration
    max_bundle_size_mb: int = Field(default=10, description="Maximum bundle size in MB")
    default_ttl_hours: int = Field(default=168, description="Default TTL in hours (7 days)")
    cache_budget_mb: int = Field(default=100, description="Cache budget in MB")
    ttl_check_interval_seconds: int = Field(default=60, description="TTL check interval")

    # Crypto configuration
    keypair_path: str = Field(
        default="./dtn_keypair.json",
        description="Path to Ed25519 keypair"
    )

    # CORS configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )

    # ValueFlows service
    vf_service_url: str = Field(
        default="http://localhost:8001",
        description="ValueFlows service URL"
    )

    # NATS configuration (for multi-agent coordination)
    nats_url: Optional[str] = Field(default=None, description="NATS server URL")
    nats_user: Optional[str] = Field(default=None, description="NATS username")
    nats_password: Optional[str] = Field(default=None, description="NATS password")
    nats_namespace: str = Field(default="solarpunk_utopia", description="NATS namespace")

    # Security
    csrf_secret: str = Field(
        default="change-me-in-production",
        description="CSRF token secret (MUST change in production)"
    )
    admin_api_key: Optional[str] = Field(
        default=None,
        description="Admin API key for protected endpoints"
    )

    # LLM configuration (for agents)
    llm_backend: str = Field(default="ollama", description="LLM backend")
    llm_model: str = Field(default="qwen2.5:1.5b", description="LLM model")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    llm_timeout: int = Field(default=30, description="LLM timeout in seconds")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("csrf_secret")
    @classmethod
    def validate_csrf_secret(cls, v):
        """Warn if using default CSRF secret"""
        if v == "change-me-in-production" and not os.getenv("DEBUG", "").lower() == "true":
            import warnings
            warnings.warn(
                "Using default CSRF secret! Set CSRF_SECRET environment variable in production.",
                UserWarning
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow environment variables to override
        case_sensitive = False


# Singleton settings instance
settings = Settings()


# Convenience functions for common config access
def get_database_url() -> str:
    """Get database URL"""
    return settings.database_url


def get_vf_service_url() -> str:
    """Get ValueFlows service URL"""
    return settings.vf_service_url


def get_allowed_origins() -> List[str]:
    """Get CORS allowed origins"""
    return settings.allowed_origins


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return settings.debug


def require_admin_api_key() -> str:
    """Get admin API key, raising error if not set"""
    if not settings.admin_api_key:
        raise ValueError("ADMIN_API_KEY environment variable is required for this operation")
    return settings.admin_api_key
