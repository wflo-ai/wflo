"""Temporal activities for workflow execution.

Activities are the building blocks of Temporal workflows. They perform
the actual work and can be retried independently.
"""

from datetime import datetime, timezone
from typing import Any

from temporalio import activity

from wflo.config.settings import get_settings
from wflo.db.engine import get_session
from wflo.db.models import (
    StateSnapshotModel,
    StepExecutionModel,
    WorkflowExecutionModel,
)


@activity.defn
async def save_workflow_execution(
    execution_id: str,
    workflow_id: str,
    status: str,
    trace_id: str,
    correlation_id: str,
    inputs: dict[str, Any],
) -> str:
    """Save workflow execution to database.

    Args:
        execution_id: Unique execution ID
        workflow_id: Workflow definition ID
        status: Execution status
        trace_id: Distributed trace ID
        correlation_id: Correlation ID for tracking
        inputs: Workflow inputs

    Returns:
        str: Created execution ID
    """
    activity.logger.info(
        f"Saving workflow execution: {execution_id}",
        extra={
            "workflow_id": workflow_id,
            "status": status,
        },
    )

    async for session in get_session():
        execution = WorkflowExecutionModel(
            id=execution_id,
            workflow_id=workflow_id,
            status=status,
            started_at=datetime.now(timezone.utc) if status == "RUNNING" else None,
            trace_id=trace_id,
            correlation_id=correlation_id,
            inputs=inputs,
        )

        session.add(execution)
        await session.commit()

    return execution_id


@activity.defn
async def update_workflow_execution_status(
    execution_id: str,
    status: str,
    error_message: str | None = None,
    outputs: dict[str, Any] | None = None,
) -> None:
    """Update workflow execution status.

    Args:
        execution_id: Execution ID to update
        status: New status
        error_message: Error message if failed
        outputs: Workflow outputs if completed
    """
    activity.logger.info(
        f"Updating execution {execution_id} to status: {status}",
    )

    async for session in get_session():
        from sqlalchemy import select

        result = await session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == execution_id
            )
        )
        execution = result.scalar_one()

        execution.status = status
        if error_message:
            execution.error_message = error_message
        if outputs:
            execution.outputs = outputs
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            execution.completed_at = datetime.now(timezone.utc)

        await session.commit()


@activity.defn
async def save_step_execution(
    step_execution_id: str,
    execution_id: str,
    step_id: str,
    status: str,
    inputs: dict[str, Any],
) -> str:
    """Save step execution to database.

    Args:
        step_execution_id: Unique step execution ID
        execution_id: Parent workflow execution ID
        step_id: Step ID from workflow definition
        status: Execution status
        inputs: Step inputs

    Returns:
        str: Created step execution ID
    """
    activity.logger.info(
        f"Saving step execution: {step_execution_id}",
        extra={
            "execution_id": execution_id,
            "step_id": step_id,
        },
    )

    async for session in get_session():
        step_execution = StepExecutionModel(
            id=step_execution_id,
            execution_id=execution_id,
            step_id=step_id,
            status=status,
            started_at=datetime.now(timezone.utc) if status == "RUNNING" else None,
            inputs=inputs,
        )

        session.add(step_execution)
        await session.commit()

    return step_execution_id


@activity.defn
async def update_step_execution(
    step_execution_id: str,
    status: str,
    outputs: dict[str, Any] | None = None,
    error_message: str | None = None,
    code: str | None = None,
    stdout: str | None = None,
    stderr: str | None = None,
    exit_code: int | None = None,
) -> None:
    """Update step execution with results.

    Args:
        step_execution_id: Step execution ID to update
        status: New status
        outputs: Step outputs
        error_message: Error message if failed
        code: Executed code
        stdout: Standard output
        stderr: Standard error
        exit_code: Exit code
    """
    activity.logger.info(
        f"Updating step execution {step_execution_id} to status: {status}",
    )

    async for session in get_session():
        from sqlalchemy import select

        result = await session.execute(
            select(StepExecutionModel).where(StepExecutionModel.id == step_execution_id)
        )
        step_execution = result.scalar_one()

        step_execution.status = status
        if outputs:
            step_execution.outputs = outputs
        if error_message:
            step_execution.error_message = error_message
        if code:
            step_execution.code = code
        if stdout:
            step_execution.stdout = stdout
        if stderr:
            step_execution.stderr = stderr
        if exit_code is not None:
            step_execution.exit_code = exit_code
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            step_execution.completed_at = datetime.now(timezone.utc)

        await session.commit()


@activity.defn
async def create_state_snapshot(
    execution_id: str,
    step_id: str,
    variables: dict[str, Any],
    version: int,
) -> str:
    """Create a state snapshot for rollback capability.

    Args:
        execution_id: Workflow execution ID
        step_id: Current step ID
        variables: State variables to snapshot
        version: Snapshot version number

    Returns:
        str: Created snapshot ID
    """
    from uuid import uuid4

    activity.logger.info(
        f"Creating state snapshot for execution {execution_id}, version {version}",
    )

    snapshot_id = str(uuid4())

    async for session in get_session():
        snapshot = StateSnapshotModel(
            id=snapshot_id,
            execution_id=execution_id,
            step_id=step_id,
            variables=variables,
            version=version,
        )

        session.add(snapshot)
        await session.commit()

    return snapshot_id


@activity.defn
async def track_cost(
    execution_id: str,
    step_execution_id: str | None,
    cost_usd: float,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Track cost for LLM API calls.

    Args:
        execution_id: Workflow execution ID
        step_execution_id: Step execution ID (if step-level tracking)
        cost_usd: Cost in USD
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
    """
    activity.logger.info(
        f"Tracking cost for execution {execution_id}: ${cost_usd:.4f}",
        extra={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    )

    async for session in get_session():
        from sqlalchemy import select

        # Update workflow execution costs
        result = await session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == execution_id
            )
        )
        execution = result.scalar_one()

        execution.cost_total_usd += cost_usd
        execution.cost_prompt_tokens += prompt_tokens
        execution.cost_completion_tokens += completion_tokens

        # Update step execution costs if provided
        if step_execution_id:
            result = await session.execute(
                select(StepExecutionModel).where(
                    StepExecutionModel.id == step_execution_id
                )
            )
            step_execution = result.scalar_one()

            step_execution.cost_usd += cost_usd
            step_execution.prompt_tokens += prompt_tokens
            step_execution.completion_tokens += completion_tokens

        await session.commit()


@activity.defn
async def execute_code_in_sandbox(
    code: str,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Execute code in a sandboxed environment.

    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time

    Returns:
        dict: Execution result with stdout, stderr, exit_code
    """
    activity.logger.info(
        f"Executing code in sandbox (timeout: {timeout_seconds}s)",
    )

    # TODO: Implement actual sandbox execution with aiodocker
    # For now, return a placeholder result
    return {
        "stdout": f"# Code execution placeholder\n# Code:\n{code[:100]}...",
        "stderr": "",
        "exit_code": 0,
        "sandbox_id": "sandbox-placeholder",
    }


@activity.defn
async def check_budget(
    execution_id: str,
    max_cost_usd: float,
) -> bool:
    """Check if workflow is within budget.

    Args:
        execution_id: Workflow execution ID
        max_cost_usd: Maximum allowed cost in USD

    Returns:
        bool: True if within budget, False otherwise
    """
    activity.logger.info(
        f"Checking budget for execution {execution_id}: max ${max_cost_usd:.2f}",
    )

    async for session in get_session():
        from sqlalchemy import select

        result = await session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == execution_id
            )
        )
        execution = result.scalar_one()

        current_cost = execution.cost_total_usd
        within_budget = current_cost <= max_cost_usd

        activity.logger.info(
            f"Current cost: ${current_cost:.4f}, "
            f"Within budget: {within_budget}",
        )

        return within_budget
