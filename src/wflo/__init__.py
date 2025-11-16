"""
Wflo - The Secure Runtime for AI Agents

Two-line integration for production-ready AI agent safety:

    import wflo
    wflo.init()

Features:
- Budget enforcement (hard limits on spend)
- Cost prediction (know costs before execution)
- Auto-optimization (automatically save 50-90% on costs)
- Self-healing (auto-recovery from failures)
- Compliance gates (human approval for risky operations)
- Full observability (traces, metrics, audit logs)

Works with:
- LangGraph, CrewAI, AutoGen, LlamaIndex
- OpenAI SDK, Anthropic SDK, Google AI SDK
- Any custom agent framework

Example:
    >>> import wflo
    >>> wflo.init(budget_usd=10.0)
    🛡️  Wflo initialized (budget: $10.00)

    >>> # Your existing code - no changes needed
    >>> from langchain_openai import ChatOpenAI
    >>> llm = ChatOpenAI(model="gpt-4")
    >>> response = llm.invoke("Write a story")

    ⚠️  Predicted cost: $0.15
    💰 Auto-optimized: gpt-4 → gpt-3.5-turbo
    ✅ Complete (cost: $0.03, saved: $0.12)
"""

__version__ = "0.1.0"
__author__ = "Wflo Team"
__license__ = "Apache-2.0"

# Core autopilot API
from wflo.autopilot.runtime import init, protect, get_runtime, shutdown

# Configuration
from wflo.autopilot.config import configure

# Exceptions
from wflo.autopilot.exceptions import (
    WfloError,
    BudgetExceededError,
    ApprovalDeniedError,
    ComplianceViolationError,
)

__all__ = [
    # Main API
    "init",
    "protect",
    "get_runtime",
    "shutdown",
    "configure",
    # Exceptions
    "WfloError",
    "BudgetExceededError",
    "ApprovalDeniedError",
    "ComplianceViolationError",
    # Metadata
    "__version__",
]
