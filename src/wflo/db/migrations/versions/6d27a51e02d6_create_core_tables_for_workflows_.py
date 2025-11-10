"""Create core tables for workflows, executions, and state management

Revision ID: 6d27a51e02d6
Revises:
Create Date: 2025-11-10 08:39:22.237292

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6d27a51e02d6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create workflow_definitions table
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("steps", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("policies", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "extra_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_workflow_name_version"),
    )
    op.create_index("ix_workflow_name", "workflow_definitions", ["name"])
    op.create_index("ix_workflow_created_at", "workflow_definitions", ["created_at"])
    op.create_index("ix_workflow_is_active", "workflow_definitions", ["is_active"])

    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cost_total_usd", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "cost_prompt_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "cost_completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("parent_execution_id", sa.String(length=36), nullable=True),
        sa.Column(
            "inputs",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "outputs",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "extra_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"]
    )
    op.create_index(
        "ix_workflow_executions_status", "workflow_executions", ["status"]
    )
    op.create_index(
        "ix_workflow_executions_trace_id", "workflow_executions", ["trace_id"]
    )
    op.create_index(
        "ix_workflow_executions_correlation_id",
        "workflow_executions",
        ["correlation_id"],
    )
    op.create_index(
        "ix_workflow_executions_parent_execution_id",
        "workflow_executions",
        ["parent_execution_id"],
    )
    op.create_index(
        "ix_workflow_executions_created_at", "workflow_executions", ["created_at"]
    )
    op.create_index(
        "ix_execution_status_created",
        "workflow_executions",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_execution_workflow_status",
        "workflow_executions",
        ["workflow_id", "status"],
    )

    # Create step_executions table
    op.create_table(
        "step_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("execution_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sandbox_id", sa.String(length=64), nullable=True),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "prompt_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "completion_tokens", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "inputs",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "outputs",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "extra_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_step_executions_execution_id", "step_executions", ["execution_id"]
    )
    op.create_index("ix_step_executions_step_id", "step_executions", ["step_id"])
    op.create_index("ix_step_executions_status", "step_executions", ["status"])
    op.create_index(
        "ix_step_execution_step", "step_executions", ["execution_id", "step_id"]
    )
    op.create_index(
        "ix_step_status_created", "step_executions", ["status", "created_at"]
    )

    # Create state_snapshots table
    op.create_table(
        "state_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("execution_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=255), nullable=False),
        sa.Column("variables", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "extra_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_state_snapshots_execution_id", "state_snapshots", ["execution_id"]
    )
    op.create_index(
        "ix_state_snapshots_created_at", "state_snapshots", ["created_at"]
    )
    op.create_index(
        "ix_snapshot_execution_version",
        "state_snapshots",
        ["execution_id", "version"],
    )
    op.create_index(
        "ix_snapshot_execution_step", "state_snapshots", ["execution_id", "step_id"]
    )

    # Create approval_requests table
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("execution_id", sa.String(length=36), nullable=False),
        sa.Column("step_id", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "context",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="PENDING"
        ),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_requests_execution_id", "approval_requests", ["execution_id"]
    )
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])
    op.create_index(
        "ix_approval_requests_expires_at", "approval_requests", ["expires_at"]
    )
    op.create_index(
        "ix_approval_status_expires", "approval_requests", ["status", "expires_at"]
    )
    op.create_index(
        "ix_approval_execution_step",
        "approval_requests",
        ["execution_id", "step_id"],
    )

    # Create rollback_actions table
    op.create_table(
        "rollback_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("execution_id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("initiated_by", sa.String(length=255), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="PENDING"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "extra_metadata",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rollback_actions_execution_id", "rollback_actions", ["execution_id"]
    )
    op.create_index(
        "ix_rollback_execution_status",
        "rollback_actions",
        ["execution_id", "status"],
    )
    op.create_index(
        "ix_rollback_started_at", "rollback_actions", ["started_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("rollback_actions")
    op.drop_table("approval_requests")
    op.drop_table("state_snapshots")
    op.drop_table("step_executions")
    op.drop_table("workflow_executions")
    op.drop_table("workflow_definitions")
