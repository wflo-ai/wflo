"""add missing foreign keys

Revision ID: 500165e12345
Revises: 6d27a51e02d6
Create Date: 2025-11-10 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "500165e12345"
down_revision: Union[str, Sequence[str], None] = "6d27a51e02d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add foreign key constraints to database tables."""
    # Add foreign key from workflow_executions.workflow_id to workflow_definitions.id
    op.create_foreign_key(
        "fk_workflow_executions_workflow_id",
        "workflow_executions",
        "workflow_definitions",
        ["workflow_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add foreign key from step_executions.execution_id to workflow_executions.id
    op.create_foreign_key(
        "fk_step_executions_execution_id",
        "step_executions",
        "workflow_executions",
        ["execution_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add foreign key from state_snapshots.execution_id to workflow_executions.id
    op.create_foreign_key(
        "fk_state_snapshots_execution_id",
        "state_snapshots",
        "workflow_executions",
        ["execution_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add foreign key from approval_requests.execution_id to workflow_executions.id
    op.create_foreign_key(
        "fk_approval_requests_execution_id",
        "approval_requests",
        "workflow_executions",
        ["execution_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add foreign key from rollback_actions.execution_id to workflow_executions.id
    op.create_foreign_key(
        "fk_rollback_actions_execution_id",
        "rollback_actions",
        "workflow_executions",
        ["execution_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Remove foreign key constraints."""
    op.drop_constraint("fk_rollback_actions_execution_id", "rollback_actions", type_="foreignkey")
    op.drop_constraint("fk_approval_requests_execution_id", "approval_requests", type_="foreignkey")
    op.drop_constraint("fk_state_snapshots_execution_id", "state_snapshots", type_="foreignkey")
    op.drop_constraint("fk_step_executions_execution_id", "step_executions", type_="foreignkey")
    op.drop_constraint("fk_workflow_executions_workflow_id", "workflow_executions", type_="foreignkey")
