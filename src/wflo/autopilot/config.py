"""
Wflo Configuration
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WfloConfig:
    """Configuration for Wflo autopilot."""

    # Budget settings
    budget_usd: float = 100.0
    budget_reset_interval: Optional[str] = None  # "daily", "weekly", "monthly", None

    # Feature flags
    auto_optimize: bool = True
    self_healing: bool = True
    cost_prediction: bool = True
    approval_gates: bool = False

    # Compliance
    compliance_mode: Optional[str] = None  # "hipaa", "pci", "sox", None
    require_approval_for: List[str] = field(default_factory=list)

    # Optimization settings
    optimization_aggressive: bool = False  # More aggressive cost cutting
    optimization_quality_threshold: float = 0.8  # Min quality score (0-1)

    # Self-healing settings
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    retry_initial_delay_seconds: float = 1.0

    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"
    silent: bool = False  # Suppress output

    # Advanced
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600


# Global config instance
_config: Optional[WfloConfig] = None


def configure(**kwargs) -> WfloConfig:
    """
    Configure global Wflo settings.

    Args:
        **kwargs: Configuration options (see WfloConfig for available options)

    Returns:
        Updated configuration

    Example:
        >>> import wflo
        >>> wflo.configure(
        ...     budget_usd=50.0,
        ...     auto_optimize=True,
        ...     compliance_mode="hipaa"
        ... )
    """
    global _config

    if _config is None:
        _config = WfloConfig(**kwargs)
    else:
        # Update existing config
        for key, value in kwargs.items():
            if hasattr(_config, key):
                setattr(_config, key, value)
            else:
                raise ValueError(f"Unknown configuration option: {key}")

    return _config


def get_config() -> WfloConfig:
    """Get current configuration (create default if not exists)."""
    global _config
    if _config is None:
        _config = WfloConfig()
    return _config


def reset_config():
    """Reset configuration to defaults."""
    global _config
    _config = WfloConfig()
