"""State management data models."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from wflo.models.workflow import ExecutionStatus


class WorkflowState(BaseModel):
    """State of a workflow execution."""

    workflow_id: str = Field(
        description="Workflow definition ID",
    )
    execution_id: str = Field(
        description="Execution instance ID",
    )
    status: ExecutionStatus = Field(
        description="Current execution status",
    )
    current_step: str | None = Field(
        default=None,
        description="Currently executing step",
    )
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow variables and context",
    )
    step_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from completed steps",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="State creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="State last updated timestamp",
    )


class StateSnapshot(BaseModel):
    """Point-in-time snapshot of workflow state for rollback."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique snapshot ID",
    )
    execution_id: str = Field(
        description="Execution instance ID",
    )
    step_id: str = Field(
        description="Step ID at time of snapshot",
    )
    state_data: dict[str, Any] = Field(
        description="Serialized state data",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Snapshot creation timestamp",
    )


class RollbackAction(BaseModel):
    """Compensating action for rollback."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique action ID",
    )
    execution_id: str = Field(
        description="Execution instance ID",
    )
    step_id: str = Field(
        description="Step that created this action",
    )
    action_type: str = Field(
        description="Type of compensating action",
    )
    action_data: dict[str, Any] = Field(
        description="Data needed to execute rollback",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Action creation timestamp",
    )
    executed_at: datetime | None = Field(
        default=None,
        description="When rollback was executed",
    )


class ApprovalRequest(BaseModel):
    """Request for human approval."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique approval request ID",
    )
    execution_id: str = Field(
        description="Execution instance ID",
    )
    step_id: str = Field(
        description="Step requiring approval",
    )
    reason: str = Field(
        description="Reason approval is required",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for decision",
    )
    status: str = Field(
        default="PENDING",
        description="Approval status (PENDING, APPROVED, REJECTED, TIMEOUT)",
    )
    timeout_seconds: int = Field(
        description="Timeout for approval decision",
    )
    approved_by: str | None = Field(
        default=None,
        description="User who approved/rejected",
    )
    decision_reason: str | None = Field(
        default=None,
        description="Reason for decision",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request creation timestamp",
    )
    decided_at: datetime | None = Field(
        default=None,
        description="When decision was made",
    )

    @property
    def is_pending(self) -> bool:
        """Check if approval is still pending."""
        return self.status == "PENDING"

    @property
    def is_approved(self) -> bool:
        """Check if approved."""
        return self.status == "APPROVED"

    @property
    def is_rejected(self) -> bool:
        """Check if rejected."""
        return self.status == "REJECTED"
