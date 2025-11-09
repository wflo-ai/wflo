"""Execution-related data models."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from wflo.models.workflow import ExecutionStatus


class CostSummary(BaseModel):
    """Summary of costs for a workflow execution."""

    total_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost in USD",
    )
    llm_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="LLM API cost in USD",
    )
    compute_cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Compute/sandbox cost in USD",
    )
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Cost breakdown by provider/model",
    )


class ExecutionResult(BaseModel):
    """Result of a step or workflow execution."""

    success: bool = Field(
        description="Whether execution succeeded",
    )
    output: Any = Field(
        default=None,
        description="Output data from execution",
    )
    error: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    error_type: str | None = Field(
        default=None,
        description="Type of error",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration",
    )
    cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost of this execution",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class WorkflowExecution(BaseModel):
    """Running instance of a workflow."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique execution ID",
    )
    workflow_id: str = Field(
        description="ID of workflow definition",
    )
    workflow_name: str = Field(
        description="Name of workflow",
    )
    workflow_version: str = Field(
        description="Version of workflow",
    )
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Current execution status",
    )
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Input data for workflow",
    )
    outputs: dict[str, Any] | None = Field(
        default=None,
        description="Output data from workflow",
    )
    current_step: str | None = Field(
        default=None,
        description="Currently executing step ID",
    )
    completed_steps: list[str] = Field(
        default_factory=list,
        description="List of completed step IDs",
    )
    failed_step: str | None = Field(
        default=None,
        description="Step ID that caused failure",
    )
    cost: CostSummary = Field(
        default_factory=CostSummary,
        description="Cost summary",
    )
    budget_limit_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Budget limit for this execution",
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Distributed tracing ID",
    )
    correlation_id: str = Field(
        default_factory=lambda: f"req-{uuid4().hex[:16]}",
        description="Correlation ID for logging",
    )
    user_id: str | None = Field(
        default=None,
        description="User who initiated execution",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status in (ExecutionStatus.RUNNING, ExecutionStatus.WAITING_APPROVAL)

    @property
    def is_terminal(self) -> bool:
        """Check if execution is in terminal state."""
        return self.status in (
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.ROLLED_BACK,
        )


class StepExecution(BaseModel):
    """Execution details for a single step."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique step execution ID",
    )
    execution_id: str = Field(
        description="Parent workflow execution ID",
    )
    step_id: str = Field(
        description="Step definition ID",
    )
    step_name: str = Field(
        description="Step name",
    )
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING,
        description="Step execution status",
    )
    result: ExecutionResult | None = Field(
        default=None,
        description="Step execution result",
    )
    attempt_number: int = Field(
        default=1,
        ge=1,
        description="Current attempt number (for retries)",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )
    sandbox_container_id: str | None = Field(
        default=None,
        description="Docker container ID if using sandbox",
    )

    @property
    def duration_seconds(self) -> float | None:
        """Calculate step duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
