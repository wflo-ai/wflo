"""
Wflo Autopilot - Universal AI Agent Safety Layer

Provides zero-configuration safety for AI agents through:
- Universal LLM API interception
- Budget enforcement and prediction
- Auto-optimization for cost
- Self-healing on failures
- Compliance and approval gates
"""

from .runtime import init, protect, get_runtime, shutdown
from .exceptions import (
    WfloError,
    BudgetExceededError,
    ApprovalDeniedError,
    ComplianceViolationError,
)

__all__ = [
    "init",
    "protect",
    "get_runtime",
    "shutdown",
    "WfloError",
    "BudgetExceededError",
    "ApprovalDeniedError",
    "ComplianceViolationError",
]
