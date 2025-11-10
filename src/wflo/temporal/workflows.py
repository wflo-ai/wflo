"""Temporal workflows for durable workflow orchestration.

Workflows are the orchestration logic that coordinates activities.
They are durable and can survive crashes, restarts, and long delays.
"""

from datetime import timedelta
from typing import Any
from uuid import uuid4

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
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


@workflow.defn
class WfloWorkflow:
    """Main Wflo workflow for executing agent workflows.

    This workflow orchestrates the execution of a workflow definition,
    managing state, cost tracking, and error handling.
    """

    def __init__(self) -> None:
        """Initialize workflow."""
        self.execution_id: str = ""
        self.workflow_id: str = ""
        self.current_state: dict[str, Any] = {}
        self.snapshot_version: int = 0

    @workflow.run
    async def run(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        max_cost_usd: float | None = None,
    ) -> dict[str, Any]:
        """Execute the workflow.

        Args:
            workflow_id: Workflow definition ID
            inputs: Workflow inputs
            max_cost_usd: Maximum cost budget in USD

        Returns:
            dict: Workflow execution results
        """
        # Generate execution ID
        self.execution_id = str(uuid4())
        self.workflow_id = workflow_id
        self.current_state = inputs.copy()

        workflow.logger.info(
            f"Starting workflow execution: {self.execution_id}",
            extra={
                "workflow_id": workflow_id,
                "max_cost_usd": max_cost_usd,
            },
        )

        # Create workflow execution record
        await workflow.execute_activity(
            save_workflow_execution,
            args=[
                self.execution_id,
                workflow_id,
                "RUNNING",
                workflow.info().workflow_id,  # Use Temporal workflow ID as trace ID
                workflow.info().run_id,  # Use run ID as correlation ID
                inputs,
            ],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
            ),
        )

        try:
            # Execute workflow steps
            outputs = await self._execute_steps(
                workflow_id=workflow_id,
                inputs=inputs,
                max_cost_usd=max_cost_usd,
            )

            # Update execution status to completed
            await workflow.execute_activity(
                update_workflow_execution_status,
                args=[self.execution_id, "COMPLETED", None, outputs],
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(f"Workflow execution completed: {self.execution_id}")

            return outputs

        except Exception as e:
            workflow.logger.error(
                f"Workflow execution failed: {self.execution_id}",
                exc_info=e,
            )

            # Update execution status to failed
            await workflow.execute_activity(
                update_workflow_execution_status,
                args=[self.execution_id, "FAILED", str(e), None],
                start_to_close_timeout=timedelta(seconds=30),
            )

            raise

    async def _execute_steps(
        self,
        workflow_id: str,
        inputs: dict[str, Any],
        max_cost_usd: float | None,
    ) -> dict[str, Any]:
        """Execute workflow steps.

        Args:
            workflow_id: Workflow definition ID
            inputs: Workflow inputs
            max_cost_usd: Maximum cost budget

        Returns:
            dict: Step outputs
        """
        # TODO: Load workflow definition from database
        # For now, execute a simple example step

        step_id = "example-step-1"
        step_execution_id = str(uuid4())

        # Create snapshot before step
        await workflow.execute_activity(
            create_state_snapshot,
            args=[
                self.execution_id,
                step_id,
                self.current_state,
                self.snapshot_version,
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )
        self.snapshot_version += 1

        # Check budget if specified
        if max_cost_usd is not None:
            within_budget = await workflow.execute_activity(
                check_budget,
                args=[self.execution_id, max_cost_usd],
                start_to_close_timeout=timedelta(seconds=30),
            )

            if not within_budget:
                raise ValueError(f"Budget exceeded: ${max_cost_usd}")

        # Save step execution
        await workflow.execute_activity(
            save_step_execution,
            args=[
                step_execution_id,
                self.execution_id,
                step_id,
                "RUNNING",
                inputs,
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Execute step (placeholder for now)
        try:
            result = await self._execute_single_step(
                step_execution_id=step_execution_id,
                step_id=step_id,
                inputs=inputs,
            )

            # Update step execution with success
            await workflow.execute_activity(
                update_step_execution,
                args=[
                    step_execution_id,
                    "COMPLETED",
                    result,
                    None,
                    None,
                    result.get("stdout"),
                    result.get("stderr"),
                    result.get("exit_code"),
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Update current state
            self.current_state.update(result)

            return result

        except Exception as e:
            # Update step execution with failure
            await workflow.execute_activity(
                update_step_execution,
                args=[
                    step_execution_id,
                    "FAILED",
                    None,
                    str(e),
                    None,
                    None,
                    None,
                    1,
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )
            raise

    async def _execute_single_step(
        self,
        step_execution_id: str,
        step_id: str,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single workflow step.

        Args:
            step_execution_id: Step execution ID
            step_id: Step ID
            inputs: Step inputs

        Returns:
            dict: Step outputs
        """
        workflow.logger.info(
            f"Executing step: {step_id}",
            extra={"step_execution_id": step_execution_id},
        )

        # For now, just return a placeholder result
        # TODO: Implement actual step execution based on step type
        result = {
            "step_id": step_id,
            "status": "completed",
            "output": f"Step {step_id} executed successfully",
        }

        return result


@workflow.defn
class SimpleWorkflow:
    """Simple workflow for testing and examples.

    This is a minimal workflow that demonstrates the basic structure.
    """

    @workflow.run
    async def run(self, name: str) -> str:
        """Execute a simple workflow.

        Args:
            name: Input name

        Returns:
            str: Greeting message
        """
        workflow.logger.info(f"Running simple workflow for: {name}")

        # Simple workflow that just returns a greeting
        result = f"Hello, {name}! Workflow executed successfully."

        workflow.logger.info("Simple workflow completed")

        return result


@workflow.defn
class CodeExecutionWorkflow:
    """Workflow for executing code in a sandbox.

    This workflow demonstrates sandboxed code execution with
    cost tracking and state management.
    """

    def __init__(self) -> None:
        """Initialize workflow."""
        self.execution_id: str = ""

    @workflow.run
    async def run(
        self,
        code: str,
        timeout_seconds: int = 30,
        track_costs: bool = False,
    ) -> dict[str, Any]:
        """Execute code in a sandbox.

        Args:
            code: Python code to execute
            timeout_seconds: Maximum execution time
            track_costs: Whether to track costs

        Returns:
            dict: Execution results
        """
        self.execution_id = str(uuid4())

        workflow.logger.info(
            f"Executing code in sandbox: {self.execution_id}",
            extra={"timeout": timeout_seconds},
        )

        # Execute code in sandbox
        result = await workflow.execute_activity(
            execute_code_in_sandbox,
            args=[code, timeout_seconds],
            start_to_close_timeout=timedelta(seconds=timeout_seconds + 10),
            retry_policy=RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=1),
            ),
        )

        # Track costs if requested
        if track_costs and result.get("exit_code") == 0:
            # Placeholder cost tracking
            await workflow.execute_activity(
                track_cost,
                args=[
                    self.execution_id,
                    None,
                    0.01,  # Placeholder cost
                    100,  # Placeholder prompt tokens
                    50,  # Placeholder completion tokens
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )

        workflow.logger.info("Code execution workflow completed")

        return result
