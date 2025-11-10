"""SQLAlchemy ORM models for database persistence.

These models map domain objects to database tables with proper
indexing, constraints, and relationships.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class WorkflowDefinitionModel(Base):
    """Database model for workflow definitions.

    Stores the workflow DAG structure, policies, and metadata.
    """

    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Workflow structure (JSON)
    steps: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    policies: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    executions: Mapped[list["WorkflowExecutionModel"]] = relationship(
        "WorkflowExecutionModel",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_workflow_name_version"),
        Index("ix_workflow_created_at", "created_at"),
        Index("ix_workflow_is_active", "is_active"),
    )


class WorkflowExecutionModel(Base):
    """Database model for workflow execution instances.

    Tracks the runtime execution of a workflow including status,
    cost, and timing information.
    """

    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )

    # Status tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Cost tracking
    cost_total_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_completion_tokens: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Tracing and correlation
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    parent_execution_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )

    # Additional data
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    workflow: Mapped["WorkflowDefinitionModel"] = relationship(
        "WorkflowDefinitionModel",
        foreign_keys=[workflow_id],
        back_populates="executions",
    )
    steps: Mapped[list["StepExecutionModel"]] = relationship(
        "StepExecutionModel",
        back_populates="execution",
        cascade="all, delete-orphan",
    )
    state_snapshots: Mapped[list["StateSnapshotModel"]] = relationship(
        "StateSnapshotModel",
        back_populates="execution",
        cascade="all, delete-orphan",
    )
    approval_requests: Mapped[list["ApprovalRequestModel"]] = relationship(
        "ApprovalRequestModel",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_execution_status_created", "status", "created_at"),
        Index("ix_execution_workflow_status", "workflow_id", "status"),
    )


class StepExecutionModel(Base):
    """Database model for individual step executions within a workflow.

    Tracks the execution details of each step including timing,
    results, and cost.
    """

    __tablename__ = "step_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    step_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Status tracking
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Execution details
    sandbox_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Cost tracking
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Results
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    execution: Mapped["WorkflowExecutionModel"] = relationship(
        "WorkflowExecutionModel",
        foreign_keys=[execution_id],
        back_populates="steps",
    )

    __table_args__ = (
        Index("ix_step_execution_step", "execution_id", "step_id"),
        Index("ix_step_status_created", "status", "created_at"),
    )


class StateSnapshotModel(Base):
    """Database model for workflow state snapshots.

    Captures point-in-time state of workflow execution for
    rollback and debugging purposes.
    """

    __tablename__ = "state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    step_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Snapshot data
    variables: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    execution: Mapped["WorkflowExecutionModel"] = relationship(
        "WorkflowExecutionModel",
        foreign_keys=[execution_id],
        back_populates="state_snapshots",
    )

    __table_args__ = (
        Index("ix_snapshot_execution_version", "execution_id", "version"),
        Index("ix_snapshot_execution_step", "execution_id", "step_id"),
    )


class ApprovalRequestModel(Base):
    """Database model for human approval requests.

    Tracks approval gates in workflows requiring human intervention.
    """

    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    step_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Approval details
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timeout
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    execution: Mapped["WorkflowExecutionModel"] = relationship(
        "WorkflowExecutionModel",
        foreign_keys=[execution_id],
        back_populates="approval_requests",
    )

    __table_args__ = (
        Index("ix_approval_status_expires", "status", "expires_at"),
        Index("ix_approval_execution_step", "execution_id", "step_id"),
    )


class RollbackActionModel(Base):
    """Database model for rollback actions.

    Records rollback attempts and their results for auditing.
    """

    __tablename__ = "rollback_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Rollback details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    initiated_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Additional data
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("ix_rollback_execution_status", "execution_id", "status"),
        Index("ix_rollback_started_at", "started_at"),
    )
