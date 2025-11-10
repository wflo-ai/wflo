"""Unit tests for execution and state models."""

from datetime import datetime, timedelta

import pytest

from wflo.models.execution import (
    CostSummary,
    ExecutionResult,
    StepExecution,
    WorkflowExecution,
)
from wflo.models.state import ApprovalRequest, RollbackAction, StateSnapshot, WorkflowState
from wflo.models.workflow import ExecutionStatus


class TestWorkflowExecution:
    """Test WorkflowExecution model."""

    def test_create_execution(self):
        """Test creating a workflow execution."""
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="test-workflow",
            workflow_version="1.0.0",
        )

        assert execution.workflow_id == "wf-123"
        assert execution.workflow_name == "test-workflow"
        assert execution.status == ExecutionStatus.PENDING
        assert execution.id  # Auto-generated
        assert execution.trace_id  # Auto-generated
        assert execution.correlation_id.startswith("req-")
        assert isinstance(execution.cost, CostSummary)
        assert execution.created_at

    def test_execution_with_budget(self):
        """Test execution with budget limit."""
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="test",
            workflow_version="1.0.0",
            budget_limit_usd=50.0,
        )

        assert execution.budget_limit_usd == 50.0

    def test_execution_status_checks(self):
        """Test execution status helper properties."""
        # Running
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="test",
            workflow_version="1.0.0",
            status=ExecutionStatus.RUNNING,
        )
        assert execution.is_running is True
        assert execution.is_terminal is False

        # Waiting approval (also considered running)
        execution.status = ExecutionStatus.WAITING_APPROVAL
        assert execution.is_running is True
        assert execution.is_terminal is False

        # Completed (terminal)
        execution.status = ExecutionStatus.COMPLETED
        assert execution.is_running is False
        assert execution.is_terminal is True

        # Failed (terminal)
        execution.status = ExecutionStatus.FAILED
        assert execution.is_running is False
        assert execution.is_terminal is True

    def test_duration_calculation(self):
        """Test duration calculation."""
        now = datetime.utcnow()
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="test",
            workflow_version="1.0.0",
            started_at=now,
            completed_at=now + timedelta(seconds=45),
        )

        assert execution.duration_seconds == pytest.approx(45.0, rel=1.0)

    def test_duration_none_when_incomplete(self):
        """Test that duration is None when execution incomplete."""
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="test",
            workflow_version="1.0.0",
            started_at=datetime.utcnow(),
        )

        assert execution.duration_seconds is None


class TestStepExecution:
    """Test StepExecution model."""

    def test_create_step_execution(self):
        """Test creating a step execution."""
        step_exec = StepExecution(
            execution_id="exec-123",
            step_id="step1",
            step_name="Analyze Data",
        )

        assert step_exec.execution_id == "exec-123"
        assert step_exec.step_id == "step1"
        assert step_exec.step_name == "Analyze Data"
        assert step_exec.status == ExecutionStatus.PENDING
        assert step_exec.attempt_number == 1

    def test_step_duration_calculation(self):
        """Test step duration calculation."""
        now = datetime.utcnow()
        step_exec = StepExecution(
            execution_id="exec-123",
            step_id="step1",
            step_name="Step 1",
            started_at=now,
            completed_at=now + timedelta(seconds=3.5),
        )

        assert step_exec.duration_seconds == pytest.approx(3.5, rel=1.0)


class TestExecutionResult:
    """Test ExecutionResult model."""

    def test_successful_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            output={"data": "processed"},
            duration_seconds=2.5,
            cost_usd=0.03,
        )

        assert result.success is True
        assert result.output == {"data": "processed"}
        assert result.error is None
        assert result.duration_seconds == 2.5
        assert result.cost_usd == 0.03

    def test_failed_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            error="Division by zero",
            error_type="ZeroDivisionError",
            duration_seconds=0.5,
        )

        assert result.success is False
        assert result.error == "Division by zero"
        assert result.error_type == "ZeroDivisionError"
        assert result.output is None


class TestCostSummary:
    """Test CostSummary model."""

    def test_create_cost_summary(self):
        """Test creating a cost summary."""
        cost = CostSummary(
            total_cost_usd=10.50,
            llm_cost_usd=10.00,
            compute_cost_usd=0.50,
            breakdown={
                "openai_gpt4": 8.00,
                "anthropic_claude": 2.00,
                "compute": 0.50,
            },
        )

        assert cost.total_cost_usd == 10.50
        assert cost.llm_cost_usd == 10.00
        assert cost.compute_cost_usd == 0.50
        assert cost.breakdown["openai_gpt4"] == 8.00


class TestWorkflowState:
    """Test WorkflowState model."""

    def test_create_state(self):
        """Test creating workflow state."""
        state = WorkflowState(
            workflow_id="wf-123",
            execution_id="exec-456",
            status=ExecutionStatus.RUNNING,
            current_step="step2",
            variables={"count": 10, "user": "john"},
            step_results={"step1": {"output": "data"}},
        )

        assert state.workflow_id == "wf-123"
        assert state.execution_id == "exec-456"
        assert state.status == ExecutionStatus.RUNNING
        assert state.current_step == "step2"
        assert state.variables["count"] == 10
        assert state.step_results["step1"]["output"] == "data"


class TestStateSnapshot:
    """Test StateSnapshot model."""

    def test_create_snapshot(self):
        """Test creating a state snapshot."""
        snapshot = StateSnapshot(
            execution_id="exec-123",
            step_id="step2",
            state_data={"variables": {"x": 100}, "results": {}},
        )

        assert snapshot.execution_id == "exec-123"
        assert snapshot.step_id == "step2"
        assert snapshot.state_data["variables"]["x"] == 100
        assert snapshot.id  # Auto-generated
        assert snapshot.created_at


class TestRollbackAction:
    """Test RollbackAction model."""

    def test_create_rollback_action(self):
        """Test creating a rollback action."""
        action = RollbackAction(
            execution_id="exec-123",
            step_id="step3",
            action_type="database_update",
            action_data={
                "query": "UPDATE users SET status = ? WHERE id = ?",
                "params": ["inactive", "user-123"],
            },
        )

        assert action.execution_id == "exec-123"
        assert action.step_id == "step3"
        assert action.action_type == "database_update"
        assert action.action_data["query"].startswith("UPDATE")
        assert action.executed_at is None

    def test_executed_rollback(self):
        """Test marking rollback as executed."""
        action = RollbackAction(
            execution_id="exec-123",
            step_id="step3",
            action_type="send_email",
            action_data={"to": "user@example.com"},
            executed_at=datetime.utcnow(),
        )

        assert action.executed_at is not None


class TestApprovalRequest:
    """Test ApprovalRequest model."""

    def test_create_approval_request(self):
        """Test creating an approval request."""
        approval = ApprovalRequest(
            execution_id="exec-123",
            step_id="delete_step",
            reason="Destructive database operation",
            timeout_seconds=3600,
        )

        assert approval.execution_id == "exec-123"
        assert approval.step_id == "delete_step"
        assert approval.reason == "Destructive database operation"
        assert approval.status == "PENDING"
        assert approval.timeout_seconds == 3600
        assert approval.approved_by is None

    def test_approval_status_checks(self):
        """Test approval status helper properties."""
        # Pending
        approval = ApprovalRequest(
            execution_id="exec-123",
            step_id="step1",
            reason="Test",
            timeout_seconds=3600,
        )
        assert approval.is_pending is True
        assert approval.is_approved is False
        assert approval.is_rejected is False

        # Approved
        approval.status = "APPROVED"
        approval.approved_by = "user@example.com"
        approval.decided_at = datetime.utcnow()

        assert approval.is_pending is False
        assert approval.is_approved is True
        assert approval.is_rejected is False
        assert approval.approved_by == "user@example.com"
        assert approval.decided_at is not None

        # Rejected
        approval.status = "REJECTED"
        assert approval.is_pending is False
        assert approval.is_approved is False
        assert approval.is_rejected is True

    def test_approval_with_context(self):
        """Test approval with additional context."""
        approval = ApprovalRequest(
            execution_id="exec-123",
            step_id="refund_step",
            reason="Issue refund",
            context={
                "customer": "john@example.com",
                "amount": 49.99,
                "order_id": "ORD-12345",
            },
            timeout_seconds=1800,
        )

        assert approval.context["customer"] == "john@example.com"
        assert approval.context["amount"] == 49.99
        assert approval.context["order_id"] == "ORD-12345"
