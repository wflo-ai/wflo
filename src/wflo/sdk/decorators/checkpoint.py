"""Checkpoint decorator for automatic state saving and rollback capability."""

import time
from functools import wraps
from typing import Any, Callable, Optional
import structlog

logger = structlog.get_logger()


def checkpoint(name: Optional[str] = None):
    """
    Decorator to automatically checkpoint state after function execution.

    Creates a state snapshot that can be restored later for rollback.

    Usage:
        @checkpoint
        async def process_step(state):
            # ... do work ...
            return new_state  # Auto-saved as checkpoint

        @checkpoint(name="after_research")
        async def research_phase(state):
            # Named checkpoint for easier identification
            return state

    Args:
        name: Optional checkpoint name. If not provided, uses function name.

    Returns:
        Decorated async function that saves checkpoint after execution
    """

    def decorator(func: Callable) -> Callable:
        checkpoint_name = name or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from wflo.sdk.context import get_current_execution_id
            from wflo.services.checkpoint import get_checkpoint_service

            execution_id = get_current_execution_id()
            start_time = time.time()

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Extract state to save
                state_to_save = _extract_state(result, args, kwargs)

                # Save checkpoint
                checkpoint_service = get_checkpoint_service()
                await checkpoint_service.save(
                    execution_id=execution_id,
                    checkpoint_name=checkpoint_name,
                    state=state_to_save,
                )

                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    "checkpoint_saved",
                    execution_id=execution_id,
                    checkpoint_name=checkpoint_name,
                    duration_ms=round(duration_ms, 2),
                )

                return result

            except Exception as e:
                logger.error(
                    "checkpoint_failed",
                    execution_id=execution_id,
                    checkpoint_name=checkpoint_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # Don't fail execution if checkpoint fails
                # Re-raise original exception
                raise

        return wrapper

    # Support both @checkpoint and @checkpoint(name="...")
    if callable(name):
        # Called as @checkpoint without parentheses
        func = name
        checkpoint_name = func.__name__
        return decorator(func)

    return decorator


def _extract_state(result: Any, args: tuple, kwargs: dict) -> dict:
    """
    Extract state to save from function result and arguments.

    Args:
        result: Function return value
        args: Function positional arguments
        kwargs: Function keyword arguments

    Returns:
        Dictionary containing state to checkpoint
    """
    state = {}

    # If result is a dict, use it as state
    if isinstance(result, dict):
        state = result.copy()
    # If result is an object with __dict__, use its attributes
    elif hasattr(result, "__dict__"):
        state = {"result": result.__dict__}
    else:
        # Store result directly
        state = {"result": result}

    # For LangGraph compatibility: first arg is often state dict
    if args and isinstance(args[0], dict):
        state.update(args[0])

    # Include any state from kwargs
    if "state" in kwargs and isinstance(kwargs["state"], dict):
        state.update(kwargs["state"])

    return state


def checkpoint_after_agent(task: Any, agent_name: str) -> Any:
    """
    Wrapper to checkpoint after a CrewAI agent task completes.

    Usage:
        research_task = Task(...)
        research_task = checkpoint_after_agent(research_task, agent_name="researcher")

    Args:
        task: CrewAI Task object
        agent_name: Name of the agent for checkpoint identification

    Returns:
        Modified task with checkpoint callback
    """
    # Store original callback if exists
    original_callback = getattr(task, "callback", None)

    async def checkpoint_callback(output):
        """Callback that saves checkpoint after task completion."""
        from wflo.sdk.context import get_current_execution_id
        from wflo.services.checkpoint import get_checkpoint_service

        execution_id = get_current_execution_id()
        checkpoint_service = get_checkpoint_service()

        # Save checkpoint
        await checkpoint_service.save(
            execution_id=execution_id,
            checkpoint_name=f"agent_{agent_name}",
            state={"agent": agent_name, "output": str(output), "timestamp": time.time()},
        )

        logger.info(
            "agent_checkpoint_saved",
            execution_id=execution_id,
            agent_name=agent_name,
        )

        # Call original callback if exists
        if original_callback:
            if callable(original_callback):
                return await original_callback(output)

    # Set checkpoint callback
    task.callback = checkpoint_callback
    return task
