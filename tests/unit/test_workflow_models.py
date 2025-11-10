"""Unit tests for workflow data models."""

import pytest
from pydantic import ValidationError

from wflo.models.workflow import (
    ExecutionStatus,
    RetryPolicy,
    StepType,
    WorkflowDefinition,
    WorkflowPolicies,
    WorkflowStep,
)


class TestWorkflowStep:
    """Test WorkflowStep model."""

    def test_create_basic_step(self):
        """Test creating a basic workflow step."""
        step = WorkflowStep(
            id="step1",
            name="Analyze Data",
            type=StepType.AGENT,
            config={"model": "gpt-4"},
        )

        assert step.id == "step1"
        assert step.name == "Analyze Data"
        assert step.type == StepType.AGENT
        assert step.config == {"model": "gpt-4"}
        assert step.depends_on == []
        assert step.approval_required is False
        assert step.rollback_enabled is False

    def test_step_with_dependencies(self):
        """Test step with dependencies."""
        step = WorkflowStep(
            id="step2",
            name="Process Results",
            type=StepType.TOOL,
            depends_on=["step1"],
        )

        assert step.depends_on == ["step1"]

    def test_step_with_approval(self):
        """Test step requiring approval."""
        step = WorkflowStep(
            id="delete_step",
            name="Delete Records",
            type=StepType.AGENT,
            approval_required=True,
            approval_reason="Destructive operation",
            approval_timeout_seconds=1800,
        )

        assert step.approval_required is True
        assert step.approval_reason == "Destructive operation"
        assert step.approval_timeout_seconds == 1800

    def test_step_with_rollback(self):
        """Test step with rollback enabled."""
        step = WorkflowStep(
            id="update_db",
            name="Update Database",
            type=StepType.AGENT,
            rollback_enabled=True,
        )

        assert step.rollback_enabled is True


class TestWorkflowDefinition:
    """Test WorkflowDefinition model."""

    def test_create_simple_workflow(self):
        """Test creating a simple workflow."""
        workflow = WorkflowDefinition(
            name="test-workflow",
            version="1.0.0",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.AGENT,
                ),
            ],
        )

        assert workflow.name == "test-workflow"
        assert workflow.version == "1.0.0"
        assert len(workflow.steps) == 1
        assert workflow.id  # Should have auto-generated ID

    def test_validate_dag_success(self):
        """Test DAG validation with valid workflow."""
        workflow = WorkflowDefinition(
            name="valid-dag",
            steps=[
                WorkflowStep(id="step1", name="Step 1", type=StepType.AGENT),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.AGENT,
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    type=StepType.AGENT,
                    depends_on=["step2"],
                ),
            ],
        )

        # Should not raise
        assert workflow.validate_dag() is True

    def test_validate_dag_circular_dependency(self):
        """Test DAG validation fails with circular dependency."""
        workflow = WorkflowDefinition(
            name="circular-dag",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.AGENT,
                    depends_on=["step2"],
                ),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.AGENT,
                    depends_on=["step1"],
                ),
            ],
        )

        with pytest.raises(ValueError, match="circular dependencies"):
            workflow.validate_dag()

    def test_validate_dag_missing_dependency(self):
        """Test DAG validation fails with missing dependency."""
        workflow = WorkflowDefinition(
            name="missing-dep",
            steps=[
                WorkflowStep(
                    id="step1",
                    name="Step 1",
                    type=StepType.AGENT,
                    depends_on=["nonexistent"],
                ),
            ],
        )

        with pytest.raises(ValueError, match="non-existent step"):
            workflow.validate_dag()

    def test_validate_dag_empty_workflow(self):
        """Test DAG validation fails with no steps."""
        workflow = WorkflowDefinition(name="empty", steps=[])

        with pytest.raises(ValueError, match="at least one step"):
            workflow.validate_dag()

    def test_get_execution_order_linear(self):
        """Test execution order for linear workflow."""
        workflow = WorkflowDefinition(
            name="linear",
            steps=[
                WorkflowStep(id="step1", name="Step 1", type=StepType.AGENT),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.AGENT,
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    type=StepType.AGENT,
                    depends_on=["step2"],
                ),
            ],
        )

        order = workflow.get_execution_order()
        assert order == ["step1", "step2", "step3"]

    def test_get_execution_order_parallel(self):
        """Test execution order with parallel steps."""
        workflow = WorkflowDefinition(
            name="parallel",
            steps=[
                WorkflowStep(id="step1", name="Step 1", type=StepType.AGENT),
                WorkflowStep(
                    id="step2",
                    name="Step 2",
                    type=StepType.AGENT,
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step3",
                    name="Step 3",
                    type=StepType.AGENT,
                    depends_on=["step1"],
                ),
                WorkflowStep(
                    id="step4",
                    name="Step 4",
                    type=StepType.AGENT,
                    depends_on=["step2", "step3"],
                ),
            ],
        )

        order = workflow.get_execution_order()

        # step1 must be first
        assert order[0] == "step1"
        # step2 and step3 can be in any order (parallel)
        assert set(order[1:3]) == {"step2", "step3"}
        # step4 must be last
        assert order[3] == "step4"

    def test_get_execution_order_complex_dag(self):
        """Test execution order for complex DAG."""
        workflow = WorkflowDefinition(
            name="complex",
            steps=[
                WorkflowStep(id="A", name="A", type=StepType.AGENT),
                WorkflowStep(id="B", name="B", type=StepType.AGENT, depends_on=["A"]),
                WorkflowStep(id="C", name="C", type=StepType.AGENT, depends_on=["A"]),
                WorkflowStep(id="D", name="D", type=StepType.AGENT, depends_on=["B"]),
                WorkflowStep(id="E", name="E", type=StepType.AGENT, depends_on=["B", "C"]),
                WorkflowStep(id="F", name="F", type=StepType.AGENT, depends_on=["D", "E"]),
            ],
        )

        order = workflow.get_execution_order()

        # A must be first
        assert order[0] == "A"
        # F must be last
        assert order[-1] == "F"
        # B and C must come before D and E
        b_idx = order.index("B")
        c_idx = order.index("C")
        d_idx = order.index("D")
        e_idx = order.index("E")

        assert b_idx < d_idx
        assert b_idx < e_idx
        assert c_idx < e_idx


class TestWorkflowPolicies:
    """Test WorkflowPolicies model."""

    def test_default_policies(self):
        """Test default policy values."""
        policies = WorkflowPolicies()

        assert policies.max_cost_usd is None
        assert policies.timeout_seconds == 3600
        assert policies.require_approval_all is False
        assert isinstance(policies.retry_policy, RetryPolicy)

    def test_custom_policies(self):
        """Test custom policy values."""
        policies = WorkflowPolicies(
            max_cost_usd=50.0,
            timeout_seconds=1800,
            require_approval_all=True,
        )

        assert policies.max_cost_usd == 50.0
        assert policies.timeout_seconds == 1800
        assert policies.require_approval_all is True

    def test_retry_policy(self):
        """Test retry policy configuration."""
        retry = RetryPolicy(
            max_attempts=5,
            initial_interval_seconds=2,
            maximum_interval_seconds=30,
            backoff_coefficient=3.0,
        )

        assert retry.max_attempts == 5
        assert retry.initial_interval_seconds == 2
        assert retry.maximum_interval_seconds == 30
        assert retry.backoff_coefficient == 3.0

    def test_retry_policy_validation(self):
        """Test retry policy validation."""
        # Valid
        retry = RetryPolicy(max_attempts=3)
        assert retry.max_attempts == 3

        # Invalid: max_attempts too low
        with pytest.raises(ValidationError):
            RetryPolicy(max_attempts=0)

        # Invalid: max_attempts too high
        with pytest.raises(ValidationError):
            RetryPolicy(max_attempts=20)


class TestEnums:
    """Test enum types."""

    def test_step_type_enum(self):
        """Test StepType enum values."""
        assert StepType.AGENT == "agent"
        assert StepType.TOOL == "tool"
        assert StepType.APPROVAL == "approval"
        assert StepType.CONDITION == "condition"
        assert StepType.PARALLEL == "parallel"

    def test_execution_status_enum(self):
        """Test ExecutionStatus enum values."""
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.WAITING_APPROVAL == "waiting_approval"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"
        assert ExecutionStatus.CANCELLED == "cancelled"
        assert ExecutionStatus.TIMEOUT == "timeout"
        assert ExecutionStatus.ROLLED_BACK == "rolled_back"
