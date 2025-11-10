"""Application settings using pydantic-settings for type-safe configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.
    Nested configuration uses '__' delimiter (e.g., DATABASE__URL).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Database (PostgreSQL)
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://wflo_user:wflo_password@localhost:5432/wflo",
        description="PostgreSQL connection URL",
    )
    database_pool_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Database connection pool size",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=50,
        description="Maximum overflow connections",
    )

    # Redis
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_max_connections: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum Redis connections",
    )

    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    kafka_client_id: str = Field(
        default="wflo-producer",
        description="Kafka client ID",
    )
    kafka_group_id: str = Field(
        default="wflo-consumer-group",
        description="Kafka consumer group ID",
    )

    # Temporal
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server host",
    )
    temporal_namespace: str = Field(
        default="default",
        description="Temporal namespace",
    )
    temporal_task_queue: str = Field(
        default="wflo-tasks",
        description="Temporal task queue name",
    )

    # Sandbox
    sandbox_image: str = Field(
        default="wflo/runtime:python3.11",
        description="Docker image for sandbox",
    )
    sandbox_cpu_limit: float = Field(
        default=0.5,
        ge=0.1,
        le=8.0,
        description="CPU limit per sandbox (cores)",
    )
    sandbox_memory_limit: str = Field(
        default="512m",
        description="Memory limit per sandbox",
    )
    sandbox_timeout_seconds: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Sandbox execution timeout",
    )
    sandbox_network_access: bool = Field(
        default=False,
        description="Allow sandbox network access by default",
    )

    # Cost Tracking
    default_budget_limit_usd: float = Field(
        default=100.00,
        ge=0.0,
        description="Default budget limit per workflow (USD)",
    )
    budget_warning_threshold_50: bool = Field(
        default=True,
        description="Alert at 50% budget",
    )
    budget_warning_threshold_75: bool = Field(
        default=True,
        description="Alert at 75% budget",
    )
    budget_warning_threshold_90: bool = Field(
        default=True,
        description="Alert at 90% budget",
    )

    # Observability
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OpenTelemetry OTLP endpoint",
    )
    otel_service_name: str = Field(
        default="wflo",
        description="Service name for traces",
    )
    jaeger_agent_host: str = Field(
        default="localhost",
        description="Jaeger agent host",
    )
    jaeger_agent_port: int = Field(
        default=6831,
        ge=1,
        le=65535,
        description="Jaeger agent port",
    )
    prometheus_port: int = Field(
        default=9090,
        ge=1024,
        le=65535,
        description="Prometheus metrics port",
    )

    # Approval Gates
    approval_timeout_default: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default approval timeout (seconds)",
    )
    approval_timeout_policy: Literal["reject", "approve"] = Field(
        default="reject",
        description="Action on approval timeout",
    )
    slack_webhook_url: str | None = Field(
        default=None,
        description="Slack webhook URL for notifications",
    )

    # Security
    secret_key: str = Field(
        default="change-this-to-a-random-secret-key",
        min_length=32,
        description="Secret key for encryption",
    )
    api_key_salt: str = Field(
        default="change-this-to-random-salt",
        min_length=16,
        description="Salt for API key hashing",
    )

    # External APIs (optional)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def temporal_address(self) -> str:
        """Get Temporal server address (alias for temporal_host)."""
        return self.temporal_host


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Settings are loaded once and cached for the application lifetime.
    Use this function to access settings throughout the application.

    Returns:
        Settings: Application settings instance

    Example:
        >>> from wflo.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.database_url)
    """
    return Settings()
