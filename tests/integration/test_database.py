"""Integration tests for database operations.

These tests require a PostgreSQL database to be running.
Set TEST_DATABASE_URL environment variable to specify the test database.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wflo.db.models import (
    ApprovalRequestModel,
    RollbackActionModel,
    StateSnapshotModel,
    StepExecutionModel,
    WorkflowDefinitionModel,
    WorkflowExecutionModel,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestDatabaseConnection:
    """Test basic database connectivity."""

    async def test_can_connect_to_database(self, db_session: AsyncSession):
        """Test we can connect to the database."""
        result = await db_session.execute(select(1))
        assert result.scalar() == 1

    async def test_tables_exist(self, db_session: AsyncSession):
        """Test all expected tables exist."""
        from sqlalchemy import inspect

        async with db_session.bind.connect() as conn:
            inspector = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

            expected_tables = {
                "workflow_definitions",
                "workflow_executions",
                "step_executions",
                "state_snapshots",
                "approval_requests",
                "rollback_actions",
            }

            assert expected_tables.issubset(set(inspector))


@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowDefinitionModel:
    """Test WorkflowDefinition CRUD operations."""

    async def test_create_workflow_definition(self, db_session: AsyncSession):
        """Test creating a workflow definition."""
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="test-workflow",
            description="A test workflow",
            version=1,
            steps=[
                {"id": "step1", "type": "AGENT", "config": {}},
                {"id": "step2", "type": "TOOL", "config": {}, "depends_on": ["step1"]},
            ],
            policies={
                "max_cost_usd": 10.0,
                "timeout_seconds": 300,
            },
            is_active=True,
        )

        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        assert workflow.id is not None
        assert workflow.name == "test-workflow"
        assert workflow.version == 1
        assert len(workflow.steps) == 2
        assert workflow.is_active is True
        assert isinstance(workflow.created_at, datetime)

    async def test_query_workflow_by_name(self, db_session: AsyncSession):
        """Test querying workflow by name."""
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="findable-workflow",
            version=1,
            steps=[],
            policies={},
        )

        db_session.add(workflow)
        await db_session.commit()

        # Query by name
        result = await db_session.execute(
            select(WorkflowDefinitionModel).where(
                WorkflowDefinitionModel.name == "findable-workflow"
            )
        )
        found = result.scalar_one()

        assert found.id == workflow.id
        assert found.name == "findable-workflow"

    async def test_unique_constraint_name_version(self, db_session: AsyncSession):
        """Test unique constraint on (name, version)."""
        workflow1 = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="unique-workflow",
            version=1,
            steps=[],
            policies={},
        )

        db_session.add(workflow1)
        await db_session.commit()

        # Same name and version should fail
        workflow2 = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="unique-workflow",
            version=1,
            steps=[],
            policies={},
        )

        db_session.add(workflow2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_workflow_versioning(self, db_session: AsyncSession):
        """Test multiple versions of same workflow."""
        workflow_v1 = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="versioned-workflow",
            version=1,
            steps=[],
            policies={},
        )

        workflow_v2 = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="versioned-workflow",
            version=2,
            steps=[],
            policies={},
        )

        db_session.add_all([workflow_v1, workflow_v2])
        await db_session.commit()

        # Query all versions
        result = await db_session.execute(
            select(WorkflowDefinitionModel)
            .where(WorkflowDefinitionModel.name == "versioned-workflow")
            .order_by(WorkflowDefinitionModel.version)
        )
        versions = result.scalars().all()

        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 2


@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowExecutionModel:
    """Test WorkflowExecution CRUD operations."""

    async def test_create_workflow_execution(self, db_session: AsyncSession):
        """Test creating a workflow execution."""
        # First create a workflow definition
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="exec-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create execution
        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            trace_id="trace-123",
            correlation_id="corr-456",
            inputs={"input_param": "value"},
            cost_total_usd=1.50,
            cost_prompt_tokens=100,
            cost_completion_tokens=50,
        )

        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        assert execution.id is not None
        assert execution.workflow_id == workflow_def.id
        assert execution.status == "RUNNING"
        assert execution.cost_total_usd == 1.50
        assert execution.inputs["input_param"] == "value"

    async def test_execution_relationship_to_workflow(self, db_session: AsyncSession):
        """Test relationship between execution and workflow definition."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="relationship-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="PENDING",
            trace_id="trace-rel",
            correlation_id="corr-rel",
        )
        db_session.add(execution)
        await db_session.commit()

        # Query with relationship
        result = await db_session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == execution.id
            )
        )
        found_exec = result.scalar_one()

        # Access relationship (requires eager loading in real app)
        await db_session.refresh(found_exec, ["workflow"])
        assert found_exec.workflow.id == workflow_def.id
        assert found_exec.workflow.name == "relationship-workflow"

    async def test_query_executions_by_status(self, db_session: AsyncSession):
        """Test querying executions by status."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="status-query-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create multiple executions with different statuses
        exec1 = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-1",
            correlation_id="corr-1",
        )
        exec2 = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-2",
            correlation_id="corr-2",
        )
        exec3 = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="COMPLETED",
            trace_id="trace-3",
            correlation_id="corr-3",
        )

        db_session.add_all([exec1, exec2, exec3])
        await db_session.commit()

        # Query running executions
        result = await db_session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.status == "RUNNING"
            )
        )
        running = result.scalars().all()

        assert len(running) == 2


@pytest.mark.asyncio
@pytest.mark.integration
class TestStepExecutionModel:
    """Test StepExecution CRUD operations."""

    async def test_create_step_execution(self, db_session: AsyncSession):
        """Test creating a step execution."""
        # Create workflow and execution first
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="step-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-step",
            correlation_id="corr-step",
        )
        db_session.add(execution)
        await db_session.commit()

        # Create step execution
        step = StepExecutionModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-1",
            status="COMPLETED",
            code="print('hello')",
            stdout="hello\n",
            exit_code=0,
            cost_usd=0.10,
            prompt_tokens=10,
            completion_tokens=5,
            inputs={"param": "value"},
            outputs={"result": "success"},
        )

        db_session.add(step)
        await db_session.commit()
        await db_session.refresh(step)

        assert step.id is not None
        assert step.execution_id == execution.id
        assert step.step_id == "step-1"
        assert step.status == "COMPLETED"
        assert step.stdout == "hello\n"
        assert step.exit_code == 0

    async def test_step_relationship_to_execution(self, db_session: AsyncSession):
        """Test relationship between step and execution."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="step-rel-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-step-rel",
            correlation_id="corr-step-rel",
        )
        db_session.add(execution)
        await db_session.commit()

        step = StepExecutionModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-1",
            status="RUNNING",
        )
        db_session.add(step)
        await db_session.commit()

        # Query step with relationship
        result = await db_session.execute(
            select(StepExecutionModel).where(StepExecutionModel.id == step.id)
        )
        found_step = result.scalar_one()

        await db_session.refresh(found_step, ["execution"])
        assert found_step.execution.id == execution.id


@pytest.mark.asyncio
@pytest.mark.integration
class TestStateSnapshotModel:
    """Test StateSnapshot CRUD operations."""

    async def test_create_state_snapshot(self, db_session: AsyncSession):
        """Test creating a state snapshot."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="snapshot-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-snapshot",
            correlation_id="corr-snapshot",
        )
        db_session.add(execution)
        await db_session.commit()

        snapshot = StateSnapshotModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-1",
            version=1,
            variables={"var1": "value1", "var2": 42},
        )

        db_session.add(snapshot)
        await db_session.commit()
        await db_session.refresh(snapshot)

        assert snapshot.id is not None
        assert snapshot.execution_id == execution.id
        assert snapshot.version == 1
        assert snapshot.variables["var1"] == "value1"
        assert snapshot.variables["var2"] == 42

    async def test_multiple_snapshots_for_execution(self, db_session: AsyncSession):
        """Test creating multiple snapshots for same execution."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="multi-snapshot-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="RUNNING",
            trace_id="trace-multi-snap",
            correlation_id="corr-multi-snap",
        )
        db_session.add(execution)
        await db_session.commit()

        # Create multiple snapshots
        snapshot1 = StateSnapshotModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-1",
            version=1,
            variables={"state": "initial"},
        )
        snapshot2 = StateSnapshotModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-2",
            version=2,
            variables={"state": "updated"},
        )

        db_session.add_all([snapshot1, snapshot2])
        await db_session.commit()

        # Query all snapshots for execution
        result = await db_session.execute(
            select(StateSnapshotModel)
            .where(StateSnapshotModel.execution_id == execution.id)
            .order_by(StateSnapshotModel.version)
        )
        snapshots = result.scalars().all()

        assert len(snapshots) == 2
        assert snapshots[0].version == 1
        assert snapshots[1].version == 2


@pytest.mark.asyncio
@pytest.mark.integration
class TestApprovalRequestModel:
    """Test ApprovalRequest CRUD operations."""

    async def test_create_approval_request(self, db_session: AsyncSession):
        """Test creating an approval request."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="approval-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="WAITING_APPROVAL",
            trace_id="trace-approval",
            correlation_id="corr-approval",
        )
        db_session.add(execution)
        await db_session.commit()

        approval = ApprovalRequestModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="approval-step",
            message="Please approve this action",
            context={"action": "deploy", "environment": "production"},
            status="PENDING",
            timeout_seconds=3600,
            expires_at=datetime.now(timezone.utc),
        )

        db_session.add(approval)
        await db_session.commit()
        await db_session.refresh(approval)

        assert approval.id is not None
        assert approval.execution_id == execution.id
        assert approval.status == "PENDING"
        assert approval.message == "Please approve this action"
        assert approval.context["action"] == "deploy"


@pytest.mark.asyncio
@pytest.mark.integration
class TestRollbackActionModel:
    """Test RollbackAction CRUD operations."""

    async def test_create_rollback_action(self, db_session: AsyncSession):
        """Test creating a rollback action."""
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="rollback-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow_def.id,
            status="FAILED",
            trace_id="trace-rollback",
            correlation_id="corr-rollback",
        )
        db_session.add(execution)
        await db_session.commit()

        snapshot = StateSnapshotModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="step-1",
            version=1,
            variables={},
        )
        db_session.add(snapshot)
        await db_session.commit()

        rollback = RollbackActionModel(
            id=str(uuid4()),
            execution_id=execution.id,
            snapshot_id=snapshot.id,
            reason="Step failed, rolling back",
            initiated_by="system",
            status="PENDING",
        )

        db_session.add(rollback)
        await db_session.commit()
        await db_session.refresh(rollback)

        assert rollback.id is not None
        assert rollback.execution_id == execution.id
        assert rollback.snapshot_id == snapshot.id
        assert rollback.reason == "Step failed, rolling back"
        assert rollback.initiated_by == "system"
