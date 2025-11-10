"""Observability with structured logging, metrics, and tracing.

This package provides a complete observability stack for Wflo:
- Structured logging with structlog (JSON + colored output)
- Distributed tracing with OpenTelemetry
- Metrics collection with Prometheus
"""

from wflo.observability.logging import configure_logging, get_logger
from wflo.observability.metrics import (
    init_service_info,
    llm_cost_total_usd,
    llm_tokens_total,
    sandbox_executions_total,
    workflow_duration_seconds,
    workflow_executions_active,
    workflow_executions_total,
)
from wflo.observability.tracing import configure_tracing, get_tracer

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    # Tracing
    "configure_tracing",
    "get_tracer",
    # Metrics
    "init_service_info",
    "workflow_executions_total",
    "workflow_duration_seconds",
    "workflow_executions_active",
    "llm_cost_total_usd",
    "llm_tokens_total",
    "sandbox_executions_total",
]
