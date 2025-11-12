"""Unit tests for Settings configuration."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from wflo.config.settings import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test that default settings load correctly."""
        settings = Settings()

        assert settings.app_env == "development"
        assert settings.log_level == "INFO"
        assert settings.debug is False
        assert settings.database_pool_size == 20
        assert settings.redis_max_connections == 50
        assert settings.temporal_task_queue == "wflo-tasks"
        assert settings.sandbox_cpu_limit == 0.5
        assert settings.sandbox_memory_limit == "512m"
        assert settings.default_budget_limit_usd == 100.00

    def test_settings_validation(self):
        """Test settings validation."""
        # Valid settings
        settings = Settings(
            database_pool_size=10,
            sandbox_cpu_limit=1.0,
            default_budget_limit_usd=50.0,
        )
        assert settings.database_pool_size == 10
        assert settings.sandbox_cpu_limit == 1.0

        # Invalid pool size (too large)
        with pytest.raises(ValidationError):
            Settings(database_pool_size=200)

        # Invalid CPU limit (too low)
        with pytest.raises(ValidationError):
            Settings(sandbox_cpu_limit=0.05)

        # Invalid budget (negative)
        with pytest.raises(ValidationError):
            Settings(default_budget_limit_usd=-10.0)

    def test_database_url_normalization(self):
        """Test that database URL is normalized to use asyncpg."""
        # Without asyncpg
        settings = Settings(database_url="postgresql://user:pass@localhost/db")
        assert str(settings.database_url).startswith("postgresql+asyncpg://")

        # Already has asyncpg
        settings = Settings(database_url="postgresql+asyncpg://user:pass@localhost/db")
        assert str(settings.database_url).startswith("postgresql+asyncpg://")

    def test_environment_properties(self):
        """Test environment detection properties."""
        # Development
        settings = Settings(app_env="development")
        assert settings.is_development is True
        assert settings.is_production is False

        # Production
        settings = Settings(app_env="production")
        assert settings.is_development is False
        assert settings.is_production is True

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance (cached)
        assert settings1 is settings2

    def test_settings_from_env_file(self, tmp_path, monkeypatch):
        """Test loading settings from .env file."""
        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
APP_ENV=production
LOG_LEVEL=WARNING
DEBUG=true
DATABASE_POOL_SIZE=30
SANDBOX_CPU_LIMIT=2.0
DEFAULT_BUDGET_LIMIT_USD=200.0
"""
        )

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Load settings (will read .env)
        settings = Settings(_env_file=str(env_file))

        assert settings.app_env == "production"
        assert settings.log_level == "WARNING"
        assert settings.debug is True
        assert settings.database_pool_size == 30
        assert settings.sandbox_cpu_limit == 2.0
        assert settings.default_budget_limit_usd == 200.0

    def test_nested_config_delimiter(self):
        """Test nested configuration with __ delimiter."""
        settings = Settings()

        # Test that we can set nested config (simulated)
        # In practice this would come from env vars like DATABASE__POOL_SIZE
        assert hasattr(settings, "database_pool_size")
        assert hasattr(settings, "database_max_overflow")

    def test_approval_timeout_policy(self):
        """Test approval timeout policy validation."""
        # Valid policies
        settings = Settings(approval_timeout_policy="reject")
        assert settings.approval_timeout_policy == "reject"

        settings = Settings(approval_timeout_policy="approve")
        assert settings.approval_timeout_policy == "approve"

        # Invalid policy should fail
        with pytest.raises(ValidationError):
            Settings(approval_timeout_policy="invalid")

    def test_port_validation(self):
        """Test port number validation."""
        # Valid ports
        settings = Settings(
            jaeger_agent_port=6831,
            prometheus_port=9090,
        )
        assert settings.jaeger_agent_port == 6831

        # Invalid port (too large)
        with pytest.raises(ValidationError):
            Settings(jaeger_agent_port=70000)

        # Invalid port (too small for prometheus)
        with pytest.raises(ValidationError):
            Settings(prometheus_port=100)
