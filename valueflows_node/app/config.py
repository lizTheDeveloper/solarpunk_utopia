"""
Central Configuration for ValueFlows Node

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
    port: int = Field(default=8001, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    json_logs: bool = Field(default=False, description="Output JSON logs (production) vs colored logs (dev)")

    # Database configuration
    database_url: str = Field(
        default="sqlite:///valueflows.db",
        description="Database connection URL"
    )

    # CORS configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )

    # DTN Bundle service
    dtn_service_url: str = Field(
        default="http://localhost:8000",
        description="DTN Bundle service URL"
    )

    # Authentication
    jwt_secret: str = Field(
        default="change-me-in-production-use-random-string",
        description="JWT secret for token signing (MUST change in production)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_days: int = Field(default=7, description="JWT token expiration in days")

    # Magic link authentication
    auth_mode: str = Field(
        default="local",
        description="Authentication mode: 'local' for dev, 'magic_link' for production"
    )
    magic_link_ttl_minutes: int = Field(default=15, description="Magic link TTL in minutes")

    # Email (for magic links - optional in dev)
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: str = Field(
        default="noreply@solarpunk.local",
        description="From email address"
    )

    # LLM configuration (for matching/scheduling agents)
    llm_backend: str = Field(default="ollama", description="LLM backend")
    llm_model: str = Field(default="qwen2.5:1.5b", description="LLM model")
    llm_api_key: Optional[str] = Field(default=None, description="LLM API key")
    llm_timeout: int = Field(default=30, description="LLM timeout in seconds")

    # Gift economy configuration
    default_trust_threshold: float = Field(
        default=0.9,
        description="Default trust threshold for high-trust operations"
    )
    max_cell_size: int = Field(default=50, description="Maximum cell/molecule size")
    min_cell_size: int = Field(default=5, description="Minimum cell/molecule size")

    # Metrics and monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v):
        """Warn if using default JWT secret"""
        if v == "change-me-in-production-use-random-string" and not os.getenv("DEBUG", "").lower() == "true":
            import warnings
            warnings.warn(
                "Using default JWT secret! Set JWT_SECRET environment variable in production.",
                UserWarning
            )
        return v

    @field_validator("default_trust_threshold")
    @classmethod
    def validate_trust_threshold(cls, v):
        """Ensure trust threshold is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("default_trust_threshold must be between 0 and 1")
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


def get_dtn_service_url() -> str:
    """Get DTN service URL"""
    return settings.dtn_service_url


def get_allowed_origins() -> List[str]:
    """Get CORS allowed origins"""
    return settings.allowed_origins


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return settings.debug


def get_jwt_secret() -> str:
    """Get JWT secret"""
    return settings.jwt_secret


def get_default_trust_threshold() -> float:
    """Get default trust threshold"""
    return settings.default_trust_threshold
