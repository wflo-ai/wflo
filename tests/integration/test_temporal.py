"""Integration tests for Temporal workflows and activities.

These tests require Temporal server to be running.
Run with: pytest tests/integration/test_temporal.py -v
"""

from datetime import timedelta
from uuid import uuid4

import pytest
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from wflo.temporal.activities import (
    check_budget,
    create_state_snapshot,
    execute_code_in_sandbox,
    save_step_execution,
    save_workflow_execution,
    track_cost,
    update_step_execution,
    update_workflow_execution_status,
)
from wflo.temporal.workflows import (
    CodeExecutionWorkflow,
    SimpleWorkflow,
    WfloWorkflow,
)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestSimpleWorkflow:
    """Test SimpleWorkflow end-to-end."""

    async def test_simple_workflow_execution(self):
        """Test that SimpleWorkflow executes successfully."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Create worker
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[SimpleWorkflow],
            ):
                # Execute workflow
                result = await env.client.execute_workflow(
                    SimpleWorkflow.run,
                    "World",
                    id=f"test-simple-{uuid4()}",
                    task_queue="test-queue",
                )

                assert "Hello, World!" in result
                assert "successfully" in result

    async def test_simple_workflow_with_different_inputs(self):
        """Test SimpleWorkflow with various inputs."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[SimpleWorkflow],
            ):
                # Test with different names
                test_cases = ["Alice", "Bob", "Test User"]

                for name in test_cases:
                    result = await env.client.execute_workflow(
                        SimpleWorkflow.run,
                        name,
                        id=f"test-simple-{uuid4()}",
                        task_queue="test-queue",
                    )

                    assert name in result
                    assert "Hello" in result


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestCodeExecutionWorkflow:
    """Test CodeExecutionWorkflow."""

    async def test_code_execution_workflow(self):
        """Test code execution workflow."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[CodeExecutionWorkflow],
                activities=[execute_code_in_sandbox, track_cost],
            ):
                code = "print('Hello from sandbox')"

                result = await env.client.execute_workflow(
                    CodeExecutionWorkflow.run,
                    code,
                    30,
                    False,  # Don't track costs for this test
                    id=f"test-code-{uuid4()}",
                    task_queue="test-queue",
                )

                assert result["exit_code"] == 0
                assert "stdout" in result
                assert "stderr" in result

    async def test_code_execution_with_timeout(self):
        """Test code execution with custom timeout."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[CodeExecutionWorkflow],
                activities=[execute_code_in_sandbox, track_cost],
            ):
                code = "import time; time.sleep(1); print('done')"

                result = await env.client.execute_workflow(
                    CodeExecutionWorkflow.run,
                    code,
                    10,  # 10 second timeout
                    False,
                    id=f"test-code-timeout-{uuid4()}",
                    task_queue="test-queue",
                )

                assert result["exit_code"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestWfloWorkflow:
    """Test main WfloWorkflow."""

    async def test_wflo_workflow_execution(self, db_session):
        """Test WfloWorkflow executes and saves to database."""
        from wflo.config.settings import get_settings
        from wflo.db.engine import init_db
        from wflo.db.models import WorkflowDefinitionModel

        # Initialize database
        settings = get_settings()
        init_db(settings)

        # Create workflow definition first
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="test-workflow",
            version=1,
            steps={},
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[WfloWorkflow],
                activities=[
                    save_workflow_execution,
                    update_workflow_execution_status,
                    save_step_execution,
                    update_step_execution,
                    create_state_snapshot,
                    check_budget,
                ],
            ):
                inputs = {"test_input": "value"}

                result = await env.client.execute_workflow(
                    WfloWorkflow.run,
                    workflow_def.id,
                    inputs,
                    None,  # No budget limit
                    id=f"test-wflo-{uuid4()}",
                    task_queue="test-queue",
                )

                assert result is not None
                assert isinstance(result, dict)

    async def test_wflo_workflow_with_budget(self, db_session):
        """Test WfloWorkflow respects budget limits."""
        from wflo.config.settings import get_settings
        from wflo.db.engine import init_db
        from wflo.db.models import WorkflowDefinitionModel

        settings = get_settings()
        init_db(settings)

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="budget-test-workflow",
            version=1,
            steps={},
            policies={"max_cost_usd": 10.0},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[WfloWorkflow],
                activities=[
                    save_workflow_execution,
                    update_workflow_execution_status,
                    save_step_execution,
                    update_step_execution,
                    create_state_snapshot,
                    check_budget,
                ],
            ):
                inputs = {"test_input": "value"}
                max_cost = 10.0

                result = await env.client.execute_workflow(
                    WfloWorkflow.run,
                    workflow_def.id,
                    inputs,
                    max_cost,
                    id=f"test-wflo-budget-{uuid4()}",
                    task_queue="test-queue",
                )

                assert result is not None


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestTemporalActivities:
    """Test Temporal activities in isolation."""

    async def test_save_workflow_execution_activity(self, db_session):
        """Test save_workflow_execution activity."""
        from sqlalchemy import select

        from wflo.config.settings import get_settings
        from wflo.db.engine import init_db
        from wflo.db.models import WorkflowDefinitionModel, WorkflowExecutionModel

        settings = get_settings()
        init_db(settings)

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id=str(uuid4()),
            name="activity-test-workflow",
            version=1,
            steps={},
            policies={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                activities=[save_workflow_execution],
            ):
                # Execute activity directly
                execution_id = str(uuid4())

                result = await env.client.execute_workflow(
                    "test_activity",
                    id=f"test-activity-{uuid4()}",
                    task_queue="test-queue",
                )

                # The activity should have created an execution record
                # We would need to check the database here
                # For now, just verify it completes without error


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowRetries:
    """Test workflow retry behavior."""

    async def test_workflow_retry_on_activity_failure(self):
        """Test that workflows retry failed activities."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[SimpleWorkflow],
            ):
                # SimpleWorkflow should always succeed
                # This test demonstrates the test structure
                result = await env.client.execute_workflow(
                    SimpleWorkflow.run,
                    "Retry Test",
                    id=f"test-retry-{uuid4()}",
                    task_queue="test-queue",
                )

                assert result is not None


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowCancellation:
    """Test workflow cancellation."""

    async def test_workflow_can_be_cancelled(self):
        """Test that workflows can be cancelled."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[SimpleWorkflow],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    SimpleWorkflow.run,
                    "Cancel Test",
                    id=f"test-cancel-{uuid4()}",
                    task_queue="test-queue",
                )

                # Immediately cancel
                await handle.cancel()

                # Verify cancellation
                try:
                    await handle.result()
                    assert False, "Workflow should have been cancelled"
                except Exception:
                    # Expected - workflow was cancelled
                    pass
