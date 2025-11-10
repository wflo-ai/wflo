"""Event schemas for Kafka-based event streaming.

All events follow a common base structure with specific fields
for different event types (workflow, cost, sandbox, audit).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event schema with common fields for all events.

    All events in the system extend this base class and inherit
    common fields for traceability and debugging.

    Attributes:
        event_id: Unique identifier for this event
        event_type: Type of event (e.g., "workflow.started")
        timestamp: When the event occurred (UTC)
        service: Service that generated the event
        version: Event schema version for compatibility
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique event identifier",
    )
    event_type: str = Field(
        description="Event type (e.g., workflow.started, cost.alert)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp (UTC)",
    )
    service: str = Field(
        default="wflo",
        description="Service name",
    )
    version: str = Field(
        default="1.0.0",
        description="Event schema version",
    )

    model_config = {"json_schema_extra": {"example": {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "workflow.started",
        "timestamp": "2025-01-15T10:30:00Z",
        "service": "wflo",
        "version": "1.0.0",
    }}}


class WorkflowEvent(BaseEvent):
    """Workflow lifecycle event.

    Published when workflows change state (started, completed, failed, etc.).
    Consumers can use these events for monitoring, alerting, and analytics.

    Example:
        >>> event = WorkflowEvent(
        ...     event_type="workflow.started",
        ...     workflow_id="data-pipeline",
        ...     execution_id="exec-123",
        ...     status="running",
        ... )
    """

    workflow_id: str = Field(description="Workflow definition ID")
    execution_id: str = Field(description="Workflow execution ID")
    status: str = Field(
        description="Workflow status: running, completed, failed, cancelled",
    )
    duration_seconds: float | None = Field(
        default=None,
        description="Workflow execution duration (seconds)",
    )
    error: str | None = Field(
        default=None,
        description="Error message if workflow failed",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional workflow metadata",
    )

    model_config = {"json_schema_extra": {"example": {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "workflow.completed",
        "timestamp": "2025-01-15T10:35:00Z",
        "service": "wflo",
        "version": "1.0.0",
        "workflow_id": "data-pipeline",
        "execution_id": "exec-123",
        "status": "completed",
        "duration_seconds": 300.5,
        "error": None,
        "metadata": {"steps_completed": 5},
    }}}


class CostEvent(BaseEvent):
    """Cost tracking and budget alert event.

    Published when costs are tracked or budget thresholds are reached.
    Enables real-time cost monitoring and automated budget management.

    Example:
        >>> event = CostEvent(
        ...     event_type="cost.tracked",
        ...     execution_id="exec-123",
        ...     model="gpt-4-turbo",
        ...     cost_usd=0.05,
        ...     total_cost_usd=2.50,
        ...     budget_limit_usd=10.00,
        ...     budget_percentage=25.0,
        ... )
    """

    execution_id: str = Field(description="Workflow execution ID")
    model: str = Field(description="LLM model used")
    cost_usd: float = Field(description="Cost of this API call (USD)")
    prompt_tokens: int = Field(description="Number of input tokens")
    completion_tokens: int = Field(description="Number of output tokens")
    total_cost_usd: float = Field(
        description="Total accumulated cost for execution (USD)",
    )
    budget_limit_usd: float | None = Field(
        default=None,
        description="Budget limit if set (USD)",
    )
    budget_percentage: float | None = Field(
        default=None,
        description="Percentage of budget used (0-100)",
    )
    alert_type: str | None = Field(
        default=None,
        description="Alert type: warning_50, warning_75, warning_90, exceeded",
    )

    model_config = {"json_schema_extra": {"example": {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "cost.alert",
        "timestamp": "2025-01-15T10:32:00Z",
        "service": "wflo",
        "version": "1.0.0",
        "execution_id": "exec-123",
        "model": "gpt-4-turbo",
        "cost_usd": 0.05,
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_cost_usd": 7.50,
        "budget_limit_usd": 10.00,
        "budget_percentage": 75.0,
        "alert_type": "warning_75",
    }}}


class SandboxEvent(BaseEvent):
    """Sandbox code execution event.

    Published when code is executed in a sandboxed environment.
    Useful for monitoring execution patterns and detecting anomalies.

    Example:
        >>> event = SandboxEvent(
        ...     event_type="sandbox.executed",
        ...     execution_id="exec-123",
        ...     language="python",
        ...     exit_code=0,
        ...     duration_seconds=2.5,
        ...     status="success",
        ... )
    """

    execution_id: str = Field(description="Workflow execution ID")
    step_id: str | None = Field(
        default=None,
        description="Workflow step ID if applicable",
    )
    language: str = Field(description="Programming language (python, javascript, etc.)")
    exit_code: int = Field(description="Exit code (0 = success)")
    duration_seconds: float = Field(description="Execution duration (seconds)")
    status: str = Field(
        description="Execution status: success, error, timeout",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed",
    )
    memory_used_mb: float | None = Field(
        default=None,
        description="Memory used (MB)",
    )
    cpu_percent: float | None = Field(
        default=None,
        description="CPU usage percentage",
    )

    model_config = {"json_schema_extra": {"example": {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "sandbox.executed",
        "timestamp": "2025-01-15T10:31:00Z",
        "service": "wflo",
        "version": "1.0.0",
        "execution_id": "exec-123",
        "step_id": "step-1",
        "language": "python",
        "exit_code": 0,
        "duration_seconds": 2.5,
        "status": "success",
        "error": None,
        "memory_used_mb": 128.5,
        "cpu_percent": 45.2,
    }}}


class AuditEvent(BaseEvent):
    """Audit trail event for compliance and security.

    Published for all significant operations that modify system state.
    Provides an immutable audit trail for compliance requirements.

    Example:
        >>> event = AuditEvent(
        ...     event_type="audit.workflow.created",
        ...     actor="user@example.com",
        ...     action="create",
        ...     resource_type="workflow",
        ...     resource_id="data-pipeline",
        ...     details={"name": "Daily ETL", "schedule": "0 2 * * *"},
        ... )
    """

    actor: str = Field(description="User or service that performed the action")
    action: str = Field(description="Action performed: create, update, delete, execute")
    resource_type: str = Field(
        description="Resource type: workflow, execution, approval",
    )
    resource_id: str = Field(description="Resource identifier")
    ip_address: str | None = Field(
        default=None,
        description="IP address of the actor",
    )
    user_agent: str | None = Field(
        default=None,
        description="User agent string",
    )
    details: dict[str, Any] = Field(
        description="Additional details about the action",
    )
    success: bool = Field(
        default=True,
        description="Whether the action was successful",
    )

    model_config = {"json_schema_extra": {"example": {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "event_type": "audit.workflow.executed",
        "timestamp": "2025-01-15T10:30:00Z",
        "service": "wflo",
        "version": "1.0.0",
        "actor": "user@example.com",
        "action": "execute",
        "resource_type": "workflow",
        "resource_id": "data-pipeline",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "details": {"execution_id": "exec-123", "trigger": "manual"},
        "success": True,
    }}}
