"""Execution context management for tracking current workflow execution."""

import contextvars
from typing import Optional
import uuid

# Context variables for tracking current execution
_current_execution_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_execution_id", default=None
)

_current_workflow_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_workflow_name", default=None
)


def set_current_execution_id(execution_id: str) -> None:
    """
    Set the current execution ID in context.

    Args:
        execution_id: Unique execution identifier
    """
    _current_execution_id.set(execution_id)


def get_current_execution_id() -> str:
    """
    Get the current execution ID from context.

    Returns:
        Current execution ID, or generates a new one if not set

    Note:
        If no execution ID is set, generates a temporary one.
        For production use, always set execution ID via WfloWorkflow.
    """
    execution_id = _current_execution_id.get()

    if execution_id is None:
        # Generate temporary execution ID
        # In production, this should always be set by WfloWorkflow
        execution_id = f"temp-{uuid.uuid4().hex[:12]}"
        _current_execution_id.set(execution_id)

    return execution_id


def set_current_workflow_name(workflow_name: str) -> None:
    """
    Set the current workflow name in context.

    Args:
        workflow_name: Workflow identifier
    """
    _current_workflow_name.set(workflow_name)


def get_current_workflow_name() -> Optional[str]:
    """
    Get the current workflow name from context.

    Returns:
        Current workflow name or None if not set
    """
    return _current_workflow_name.get()


def clear_context() -> None:
    """Clear execution context (useful for testing)."""
    _current_execution_id.set(None)
    _current_workflow_name.set(None)


class ExecutionContext:
    """
    Context manager for setting execution context.

    Usage:
        async with ExecutionContext(execution_id="exec-123", workflow_name="my-workflow"):
            # Code here has access to execution_id
            result = await tracked_function()
    """

    def __init__(self, execution_id: str, workflow_name: Optional[str] = None):
        self.execution_id = execution_id
        self.workflow_name = workflow_name
        self.previous_execution_id = None
        self.previous_workflow_name = None

    def __enter__(self):
        """Enter context."""
        self.previous_execution_id = _current_execution_id.get()
        self.previous_workflow_name = _current_workflow_name.get()

        set_current_execution_id(self.execution_id)
        if self.workflow_name:
            set_current_workflow_name(self.workflow_name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if self.previous_execution_id is not None:
            _current_execution_id.set(self.previous_execution_id)
        else:
            _current_execution_id.set(None)

        if self.previous_workflow_name is not None:
            _current_workflow_name.set(self.previous_workflow_name)
        else:
            _current_workflow_name.set(None)

    async def __aenter__(self):
        """Enter async context."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        return self.__exit__(exc_type, exc_val, exc_tb)
