"""Prometheus metrics for Wflo monitoring and alerting."""

from prometheus_client import Counter, Gauge, Histogram, Info

# Service information
service_info = Info(
    "wflo_service",
    "Wflo service information",
)

# Workflow metrics
workflow_executions_total = Counter(
    "wflo_workflow_executions_total",
    "Total number of workflow executions",
    ["workflow_id", "status"],
)

workflow_duration_seconds = Histogram(
    "wflo_workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float("inf")),
)

workflow_executions_active = Gauge(
    "wflo_workflow_executions_active",
    "Number of currently active workflow executions",
)

# LLM Cost metrics
llm_cost_total_usd = Counter(
    "wflo_llm_cost_total_usd",
    "Total LLM API cost in USD",
    ["model"],
)

llm_tokens_total = Counter(
    "wflo_llm_tokens_total",
    "Total LLM tokens used",
    ["model", "token_type"],  # token_type: input or output
)

llm_api_calls_total = Counter(
    "wflo_llm_api_calls_total",
    "Total LLM API calls",
    ["model", "status"],  # status: success or error
)

# LLM Cache metrics
llm_cache_hits_total = Counter(
    "wflo_llm_cache_hits_total",
    "Total LLM cache hits",
    ["model"],
)

llm_cache_misses_total = Counter(
    "wflo_llm_cache_misses_total",
    "Total LLM cache misses",
    ["model"],
)

# Sandbox execution metrics
sandbox_executions_total = Counter(
    "wflo_sandbox_executions_total",
    "Total sandbox code executions",
    ["language", "status"],  # status: success or error
)

sandbox_duration_seconds = Histogram(
    "wflo_sandbox_duration_seconds",
    "Sandbox execution duration in seconds",
    ["language"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

sandbox_exit_codes = Counter(
    "wflo_sandbox_exit_codes_total",
    "Sandbox exit code distribution",
    ["exit_code"],
)

# Database metrics
database_operations_total = Counter(
    "wflo_database_operations_total",
    "Total database operations",
    ["operation", "table"],  # operation: select, insert, update, delete
)

database_connection_pool_size = Gauge(
    "wflo_database_connection_pool_size",
    "Current database connection pool size",
)

database_connection_pool_active = Gauge(
    "wflo_database_connection_pool_active",
    "Number of active database connections",
)

# Temporal worker metrics
temporal_activities_executed_total = Counter(
    "wflo_temporal_activities_executed_total",
    "Total Temporal activities executed",
    ["activity_name", "status"],
)

temporal_activity_duration_seconds = Histogram(
    "wflo_temporal_activity_duration_seconds",
    "Temporal activity execution duration",
    ["activity_name"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")),
)

# Budget and cost governance metrics
workflow_budget_exceeded_total = Counter(
    "wflo_workflow_budget_exceeded_total",
    "Number of workflows that exceeded budget",
    ["workflow_id"],
)

workflow_cost_by_model = Counter(
    "wflo_workflow_cost_by_model_usd",
    "Workflow cost breakdown by model",
    ["workflow_id", "model"],
)

# Error metrics
errors_total = Counter(
    "wflo_errors_total",
    "Total errors",
    ["error_type", "component"],
)


def init_service_info(version: str, environment: str) -> None:
    """Initialize service information metric.

    Args:
        version: Service version
        environment: Deployment environment (development, staging, production)
    """
    service_info.info(
        {
            "version": version,
            "environment": environment,
        }
    )
