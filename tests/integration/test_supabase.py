"""Integration tests for PostgreSQL database (Supabase or local).

These tests verify that wflo works correctly with PostgreSQL.
They can be run against Supabase, local PostgreSQL, or any PostgreSQL instance.

Requirements:
- PostgreSQL database (Supabase, local, or remote)
- DATABASE_URL or TEST_DATABASE_URL environment variable set in .env

Setup:
1. Configure your database URL in .env file:
   DATABASE_URL=postgresql+asyncpg://postgres:password@host:5432/dbname

   Examples:
   - Supabase: postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres
   - Local: postgresql+asyncpg://postgres:pass@localhost:5432/wflo
   - Remote: postgresql+asyncpg://user:pass@your-host:5432/dbname

2. Run tests:
   poetry run pytest tests/integration/test_supabase.py -v -m integration

Note:
- Tests use the database URL from .env file (DATABASE_URL or TEST_DATABASE_URL)
- These tests will create and delete data in your database
- Recommended to use a dedicated test database
"""

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from wflo.config import Settings
from wflo.db.engine import DatabaseEngine
from wflo.db.models import (
    StateSnapshotModel,
    WorkflowDefinitionModel,
    WorkflowExecutionModel,
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestSupabaseConnection:
    """Test basic Supabase connectivity."""

    async def test_can_connect_to_supabase(self, db_session: AsyncSession):
        """Test we can connect to Supabase."""
        result = await db_session.execute(select(1))
        assert result.scalar() == 1

    async def test_supabase_version(self, db_session: AsyncSession):
        """Test we can get PostgreSQL version from Supabase."""
        result = await db_session.execute(text("SELECT version()"))
        version = result.scalar()

        assert version is not None
        assert "PostgreSQL" in version
        print(f"\nSupabase PostgreSQL version: {version}")

    async def test_connection_pool_info(self, db_session: AsyncSession):
        """Test connection pool is working."""
        from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

        # Access the engine through the session
        engine = db_session.bind

        # Check pool exists and is configured
        pool = engine.pool
        assert pool is not None

        # Pool type and configuration depends on environment
        pool_type = type(pool).__name__
        print(f"\nConnection pool type: {pool_type}")

        # NullPool is used in testing, AsyncAdaptedQueuePool in production
        if isinstance(pool, AsyncAdaptedQueuePool):
            print(f"Pool size: {pool.size()}")
            print(f"Checked out connections: {pool.checkedout()}")
            print(f"Pool overflow: {pool.overflow()}")
        elif isinstance(pool, NullPool):
            print("NullPool: No connection pooling (test mode)")
        else:
            print(f"Unknown pool type: {pool_type}")

    async def test_tables_exist_in_supabase(self, db_session: AsyncSession):
        """Test all wflo tables exist in Supabase."""
        result = await db_session.execute(
            text(
                """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """
            )
        )
        tables = result.scalars().all()

        expected_tables = {
            "workflow_definitions",
            "workflow_executions",
            "step_executions",
            "state_snapshots",
            "approval_requests",
            "rollback_actions",
        }

        found_tables = set(tables)
        assert expected_tables.issubset(
            found_tables
        ), f"Missing tables: {expected_tables - found_tables}"

        print(f"\nFound {len(tables)} tables in Supabase")


@pytest.mark.asyncio
@pytest.mark.integration
class TestSupabaseWorkflowOperations:
    """Test workflow CRUD operations with Supabase."""

    async def test_create_and_query_workflow(self, db_session: AsyncSession):
        """Test creating and querying workflow in Supabase."""
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="supabase-test-workflow",
            description="Test workflow for Supabase integration",
            version=1,
            steps=[
                {"id": "step1", "type": "AGENT", "config": {}},
            ],
            policies={
                "max_cost_usd": 5.0,
                "timeout_seconds": 600,
            },
            is_active=True,
        )

        db_session.add(workflow)
        await db_session.commit()
        await db_session.refresh(workflow)

        # Verify creation
        assert workflow.id is not None
        assert workflow.name == "supabase-test-workflow"
        assert isinstance(workflow.created_at, datetime)

        # Query it back
        result = await db_session.execute(
            select(WorkflowDefinitionModel).where(
                WorkflowDefinitionModel.id == workflow.id
            )
        )
        found = result.scalar_one()

        assert found.id == workflow.id
        assert found.name == "supabase-test-workflow"
        assert found.is_active is True

    async def test_workflow_execution_with_cost_tracking(
        self, db_session: AsyncSession
    ):
        """Test execution with cost tracking in Supabase."""
        # Create workflow
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="cost-tracking-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow)
        await db_session.commit()

        # Create execution with cost data
        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow.id,
            status="COMPLETED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            trace_id=f"trace-{uuid4()}",
            correlation_id=f"corr-{uuid4()}",
            inputs={"test": "input"},
            outputs={"test": "output"},
            cost_total_usd=2.5,
            cost_prompt_tokens=1000,
            cost_completion_tokens=500,
        )

        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Verify cost tracking
        assert execution.cost_total_usd == 2.5
        assert execution.cost_prompt_tokens == 1000
        assert execution.cost_completion_tokens == 500
        assert execution.status == "COMPLETED"

        # Query by cost
        result = await db_session.execute(
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.cost_total_usd > 2.0)
            .where(WorkflowExecutionModel.workflow_id == workflow.id)
        )
        expensive_executions = result.scalars().all()

        assert len(expensive_executions) == 1
        assert expensive_executions[0].id == execution.id


@pytest.mark.asyncio
@pytest.mark.integration
class TestSupabaseCheckpointing:
    """Test checkpoint and rollback with Supabase."""

    async def test_create_checkpoints_in_supabase(self, db_session: AsyncSession):
        """Test creating multiple checkpoints in Supabase."""
        # Create workflow and execution
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="checkpoint-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow.id,
            status="RUNNING",
            trace_id=f"trace-{uuid4()}",
            correlation_id=f"corr-{uuid4()}",
        )
        db_session.add(execution)
        await db_session.commit()

        # Create multiple checkpoints
        checkpoints = []
        for i in range(3):
            checkpoint = StateSnapshotModel(
                id=str(uuid4()),
                execution_id=execution.id,
                step_id=f"step-{i+1}",
                version=i + 1,
                variables={
                    "step": i + 1,
                    "data": f"checkpoint-{i+1}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            checkpoints.append(checkpoint)
            db_session.add(checkpoint)

        await db_session.commit()

        # Query all checkpoints
        result = await db_session.execute(
            select(StateSnapshotModel)
            .where(StateSnapshotModel.execution_id == execution.id)
            .order_by(StateSnapshotModel.version)
        )
        found_checkpoints = result.scalars().all()

        assert len(found_checkpoints) == 3
        assert found_checkpoints[0].version == 1
        assert found_checkpoints[1].version == 2
        assert found_checkpoints[2].version == 3

        # Verify checkpoint data integrity
        for i, checkpoint in enumerate(found_checkpoints):
            assert checkpoint.variables["step"] == i + 1
            assert checkpoint.variables["data"] == f"checkpoint-{i+1}"
            assert "timestamp" in checkpoint.variables

    async def test_rollback_to_checkpoint(self, db_session: AsyncSession):
        """Test rollback to specific checkpoint in Supabase."""
        # Create workflow and execution
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="rollback-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow.id,
            status="RUNNING",
            trace_id=f"trace-{uuid4()}",
            correlation_id=f"corr-{uuid4()}",
        )
        db_session.add(execution)
        await db_session.commit()

        # Create checkpoint to rollback to
        target_checkpoint = StateSnapshotModel(
            id=str(uuid4()),
            execution_id=execution.id,
            step_id="important-step",
            version=2,
            variables={
                "state": "important",
                "can_rollback": True,
            },
        )
        db_session.add(target_checkpoint)
        await db_session.commit()

        # Simulate rollback by querying the checkpoint
        result = await db_session.execute(
            select(StateSnapshotModel)
            .where(StateSnapshotModel.execution_id == execution.id)
            .where(StateSnapshotModel.step_id == "important-step")
        )
        restored_checkpoint = result.scalar_one()

        # Verify we can restore the state
        assert restored_checkpoint.id == target_checkpoint.id
        assert restored_checkpoint.variables["state"] == "important"
        assert restored_checkpoint.variables["can_rollback"] is True


@pytest.mark.asyncio
@pytest.mark.integration
class TestSupabasePerformance:
    """Test performance characteristics with Supabase."""

    async def test_bulk_insert_performance(self, db_session: AsyncSession):
        """Test bulk inserting workflows into Supabase."""
        import time

        start_time = time.time()

        # Create 10 workflows in bulk
        workflows = []
        for i in range(10):
            workflow = WorkflowDefinitionModel(
                id=str(uuid4()),
                name=f"bulk-test-workflow-{i}",
                version=1,
                steps=[],
                policies={},
            )
            workflows.append(workflow)

        db_session.add_all(workflows)
        await db_session.commit()

        elapsed = time.time() - start_time

        # Verify all were created
        result = await db_session.execute(
            select(WorkflowDefinitionModel).where(
                WorkflowDefinitionModel.name.like("bulk-test-workflow-%")
            )
        )
        found = result.scalars().all()

        assert len(found) == 10
        print(f"\nBulk insert of 10 workflows took {elapsed:.3f} seconds")

        # Supabase should handle this quickly (under 2 seconds)
        assert elapsed < 2.0, f"Bulk insert took too long: {elapsed:.3f}s"

    async def test_concurrent_executions(self, db_session: AsyncSession):
        """Test handling multiple concurrent executions."""
        # Create workflow
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="concurrent-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow)
        await db_session.commit()

        # Create 5 concurrent executions
        executions = []
        for i in range(5):
            execution = WorkflowExecutionModel(
                id=str(uuid4()),
                workflow_id=workflow.id,
                status="RUNNING",
                trace_id=f"trace-{uuid4()}",
                correlation_id=f"corr-{i}",
            )
            executions.append(execution)

        db_session.add_all(executions)
        await db_session.commit()

        # Query concurrent executions
        result = await db_session.execute(
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_id == workflow.id)
            .where(WorkflowExecutionModel.status == "RUNNING")
        )
        running = result.scalars().all()

        assert len(running) == 5
        print(f"\nSuccessfully handled {len(running)} concurrent executions")


@pytest.mark.asyncio
@pytest.mark.integration
class TestSupabaseDataTypes:
    """Test Supabase handles all wflo data types correctly."""

    async def test_jsonb_fields(self, db_session: AsyncSession):
        """Test JSONB fields work correctly in Supabase."""
        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="jsonb-test-workflow",
            version=1,
            steps=[
                {
                    "id": "step1",
                    "type": "AGENT",
                    "config": {
                        "nested": {"deep": {"value": 123}},
                        "array": [1, 2, 3, 4, 5],
                        "boolean": True,
                        "null_value": None,
                    },
                }
            ],
            policies={
                "complex": {
                    "retry": {"max_attempts": 3, "backoff": "exponential"},
                    "timeout": 300,
                },
            },
        )

        db_session.add(workflow)
        await db_session.commit()

        # Query and verify JSONB integrity
        result = await db_session.execute(
            select(WorkflowDefinitionModel).where(
                WorkflowDefinitionModel.id == workflow.id
            )
        )
        found = result.scalar_one()

        # Verify nested JSON structure
        assert found.steps[0]["config"]["nested"]["deep"]["value"] == 123
        assert found.steps[0]["config"]["array"] == [1, 2, 3, 4, 5]
        assert found.steps[0]["config"]["boolean"] is True
        assert found.steps[0]["config"]["null_value"] is None

        # Verify complex policies
        assert found.policies["complex"]["retry"]["max_attempts"] == 3
        assert found.policies["complex"]["retry"]["backoff"] == "exponential"

    async def test_timestamp_fields(self, db_session: AsyncSession):
        """Test timestamp fields with timezone."""
        now = datetime.now(timezone.utc)

        workflow = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="timestamp-test-workflow",
            version=1,
            steps=[],
            policies={},
        )
        db_session.add(workflow)
        await db_session.commit()

        execution = WorkflowExecutionModel(
            id=str(uuid4()),
            workflow_id=workflow.id,
            status="COMPLETED",
            started_at=now,
            completed_at=now,
            trace_id=f"trace-{uuid4()}",
            correlation_id=f"corr-{uuid4()}",
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)

        # Verify timestamps are preserved with timezone
        assert execution.started_at.tzinfo is not None
        assert execution.completed_at.tzinfo is not None
        assert execution.created_at.tzinfo is not None

        # Timestamps should be close to our input
        time_diff = abs((execution.started_at - now).total_seconds())
        assert time_diff < 1.0, "Timestamp differs by more than 1 second"
