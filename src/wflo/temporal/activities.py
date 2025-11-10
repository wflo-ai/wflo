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
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    step_execution_id: str | None = None,
) -> float:
    """Track cost for LLM API calls using CostTracker.

    Args:
        execution_id: Workflow execution ID
        model: LLM model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        step_execution_id: Step execution ID (if step-level tracking)

    Returns:
        float: Calculated cost in USD
    """
    from wflo.cost import CostTracker, TokenUsage

    activity.logger.info(
        f"Tracking cost for execution {execution_id}",
        extra={
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    )

    # Use CostTracker for consistent cost calculation and database tracking
    async for session in get_session():
        tracker = CostTracker()
        usage = TokenUsage(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        await tracker.track_cost(session, execution_id, usage, step_execution_id)

        # Return the calculated cost for logging/monitoring
        cost = tracker.calculate_cost(usage)
        activity.logger.info(f"Tracked ${cost:.4f} for execution {execution_id}")
        return cost


@activity.defn
async def execute_code_in_sandbox(
    code: str,
    timeout_seconds: int = 30,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Execute code in a sandboxed environment.

    Args:
        code: Python code to execute
        timeout_seconds: Maximum execution time
        allow_network: Whether to allow network access

    Returns:
        dict: Execution result with stdout, stderr, exit_code, duration, sandbox_id
    """
    from wflo.sandbox import SandboxRuntime

    activity.logger.info(
        f"Executing code in sandbox (timeout: {timeout_seconds}s)",
    )

    try:
        async with SandboxRuntime() as runtime:
            result = await runtime.execute_code(
                code=code,
                timeout_seconds=timeout_seconds,
                allow_network=allow_network,
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "sandbox_id": result.sandbox_id,
                "duration_seconds": result.duration_seconds,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
            }
    except TimeoutError as e:
        activity.logger.error(f"Sandbox execution timed out: {e}")
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds",
            "exit_code": 124,  # Standard timeout exit code
            "sandbox_id": "timeout",
            "duration_seconds": float(timeout_seconds),
        }
    except Exception as e:
        activity.logger.error(f"Sandbox execution failed: {e}", exc_info=e)
        return {
            "stdout": "",
            "stderr": f"Sandbox error: {str(e)}",
            "exit_code": 1,
            "sandbox_id": "error",
            "duration_seconds": 0.0,
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
