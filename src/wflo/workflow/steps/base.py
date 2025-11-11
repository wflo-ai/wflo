"""Base classes for workflow steps.

This module provides the foundation for the workflow step type system.
Each step type (LLM, HTTP, Sandbox, etc.) inherits from the base Step class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class StepContext:
    """Context passed to step execution.

    Contains all the information a step needs to execute, including
    execution IDs, input data, workflow state, and configuration.

    Attributes:
        execution_id: Workflow execution ID
        step_execution_id: This step's execution ID
        inputs: Input data for the step
        state: Current workflow state
        config: Configuration for the step
    """

    execution_id: str
    step_execution_id: str
    inputs: Dict[str, Any]
    state: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """Result of step execution.

    Contains the outcome of executing a step, including success status,
    output data, error information, cost tracking, and metadata.

    Attributes:
        success: Whether step succeeded
        output: Step output data
        error: Error message if failed
        cost_usd: Cost incurred (if applicable)
        metadata: Additional metadata (tokens, latency, etc.)
        started_at: Execution start time
        completed_at: Execution completion time
    """

    success: bool
    output: Dict[str, Any]
    error: str | None = None
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.completed_at is None:
            self.completed_at = datetime.now()

    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds.

        Returns:
            float: Duration in seconds
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class Step(ABC):
    """Base class for all workflow steps.

    This abstract class defines the interface that all step types must implement.
    Subclasses should override the execute() method to provide their specific
    functionality.

    Example:
        class MyStep(Step):
            async def execute(self, context: StepContext) -> StepResult:
                # Implementation here
                return StepResult(success=True, output={"result": "data"})

    Attributes:
        step_id: Unique identifier for this step
        config: Step-specific configuration
    """

    def __init__(self, step_id: str, **kwargs):
        """Initialize step.

        Args:
            step_id: Unique step identifier
            **kwargs: Step-specific configuration
        """
        self.step_id = step_id
        self.config = kwargs

    @abstractmethod
    async def execute(self, context: StepContext) -> StepResult:
        """Execute the step.

        This method must be implemented by subclasses to provide the
        step's specific functionality.

        Args:
            context: Step execution context with inputs and state

        Returns:
            StepResult: Execution result with output and metadata

        Raises:
            Exception: If step execution fails
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )

    async def validate(self, context: StepContext) -> bool:
        """Validate step can execute with given context.

        Override this method to add validation logic before execution.
        Default implementation always returns True.

        Args:
            context: Step execution context

        Returns:
            bool: True if valid, False otherwise
        """
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step to dictionary.

        Useful for storing step definitions in database or
        transmitting over API.

        Returns:
            dict: Step configuration including type and config
        """
        return {
            "type": self.__class__.__name__,
            "step_id": self.step_id,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Deserialize step from dictionary.

        Args:
            data: Dictionary with step type, ID, and config

        Returns:
            Step: Instantiated step object

        Raises:
            ValueError: If step type is unknown
        """
        # This will be extended when we have multiple step types
        step_id = data.get("step_id")
        config = data.get("config", {})

        if not step_id:
            raise ValueError("step_id is required")

        return cls(step_id=step_id, **config)

    def __repr__(self) -> str:
        """String representation of step.

        Returns:
            str: Step description
        """
        return f"{self.__class__.__name__}(step_id='{self.step_id}')"
