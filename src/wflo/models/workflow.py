"""Core workflow data models."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StepType(str, Enum):
    """Type of workflow step."""

    AGENT = "agent"  # AI agent execution
    TOOL = "tool"  # Tool/function call
    APPROVAL = "approval"  # Human approval gate
    CONDITION = "condition"  # Conditional branching
    PARALLEL = "parallel"  # Parallel execution


class ExecutionStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"  # Not yet started
    RUNNING = "running"  # Currently executing
    WAITING_APPROVAL = "waiting_approval"  # Paused for approval
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Failed with error
    CANCELLED = "cancelled"  # Cancelled by user
    TIMEOUT = "timeout"  # Exceeded timeout
    ROLLED_BACK = "rolled_back"  # Rolled back to previous state


class RetryPolicy(BaseModel):
    """Retry policy for failed steps."""

    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_interval_seconds: int = Field(default=1, ge=1)
    maximum_interval_seconds: int = Field(default=10, ge=1)
    backoff_coefficient: float = Field(default=2.0, ge=1.0)


class WorkflowPolicies(BaseModel):
    """Policies for workflow execution."""

    max_cost_usd: float | None = Field(
        default=None,
        ge=0.0,
        description="Maximum cost in USD",
    )
    timeout_seconds: int = Field(
        default=3600,
        ge=60,
        description="Maximum execution time",
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry policy for failed steps",
    )
    require_approval_all: bool = Field(
        default=False,
        description="Require approval for all steps",
    )


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""

    id: str = Field(
        description="Unique step identifier",
    )
    name: str = Field(
        description="Human-readable step name",
    )
    type: StepType = Field(
        description="Type of step",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific configuration",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of steps this step depends on",
    )
    approval_required: bool = Field(
        default=False,
        description="Require human approval before execution",
    )
    approval_reason: str | None = Field(
        default=None,
        description="Reason for approval requirement",
    )
    approval_timeout_seconds: int = Field(
        default=3600,
        ge=60,
        description="Timeout for approval",
    )
    rollback_enabled: bool = Field(
        default=False,
        description="Enable rollback for this step",
    )
    retry_policy: RetryPolicy | None = Field(
        default=None,
        description="Override retry policy for this step",
    )
    timeout_seconds: int | None = Field(
        default=None,
        ge=10,
        description="Override timeout for this step",
    )


class WorkflowDefinition(BaseModel):
    """Definition of a workflow (DAG)."""

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique workflow ID",
    )
    name: str = Field(
        description="Workflow name",
    )
    version: str = Field(
        default="1.0.0",
        description="Workflow version",
    )
    description: str | None = Field(
        default=None,
        description="Workflow description",
    )
    steps: list[WorkflowStep] = Field(
        description="List of workflow steps",
    )
    policies: WorkflowPolicies = Field(
        default_factory=WorkflowPolicies,
        description="Workflow execution policies",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )

    def validate_dag(self) -> bool:
        """
        Validate that the workflow forms a valid DAG.

        Checks:
        - No circular dependencies
        - All dependencies reference existing steps
        - At least one step exists

        Returns:
            bool: True if valid DAG

        Raises:
            ValueError: If validation fails
        """
        if not self.steps:
            raise ValueError("Workflow must have at least one step")

        # Build step ID set
        step_ids = {step.id for step in self.steps}

        # Check all dependencies exist
        for step in self.steps:
            for dep_id in step.depends_on:
                if dep_id not in step_ids:
                    raise ValueError(
                        f"Step '{step.id}' depends on non-existent step '{dep_id}'"
                    )

        # Check for circular dependencies using DFS
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)

            # Get dependencies
            step = next((s for s in self.steps if s.id == step_id), None)
            if step:
                for dep_id in step.depends_on:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True

            rec_stack.remove(step_id)
            return False

        for step in self.steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    raise ValueError("Workflow contains circular dependencies")

        return True

    def get_execution_order(self) -> list[str]:
        """
        Get topological sort of steps for execution order.

        Returns:
            list[str]: Step IDs in execution order

        Raises:
            ValueError: If DAG is invalid
        """
        self.validate_dag()

        # Build dependency map
        in_degree: dict[str, int] = {step.id: 0 for step in self.steps}
        adj_list: dict[str, list[str]] = {step.id: [] for step in self.steps}

        for step in self.steps:
            for dep_id in step.depends_on:
                adj_list[dep_id].append(step.id)
                in_degree[step.id] += 1

        # Topological sort using Kahn's algorithm
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            step_id = queue.pop(0)
            result.append(step_id)

            for neighbor in adj_list[step_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.steps):
            raise ValueError("Cycle detected in workflow graph")

        return result
