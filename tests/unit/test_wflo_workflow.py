"""Unit tests for WfloWorkflow class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from wflo.sdk.workflow import WfloWorkflow, BudgetExceededError


def mock_get_session_generator(mock_session=None):
    """Create a mock async generator for get_session."""
    if mock_session is None:
        mock_session = Mock()
        # Add async methods that are commonly used
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

    async def mock_gen():
        yield mock_session

    return mock_gen()


@pytest.mark.asyncio
class TestWfloWorkflow:
    """Tests for WfloWorkflow class."""

    async def test_workflow_initialization(self):
        """Test workflow initializes with correct parameters."""
        workflow = WfloWorkflow(
            name="test-workflow",
            budget_usd=10.0,
            per_agent_budgets={"agent1": 5.0},
            max_iterations=50,
            enable_checkpointing=True,
            enable_observability=True,
        )

        assert workflow.name == "test-workflow"
        assert workflow.budget_usd == 10.0
        assert workflow.per_agent_budgets == {"agent1": 5.0}
        assert workflow.max_iterations == 50
        assert workflow.enable_checkpointing is True
        assert workflow.enable_observability is True
        assert workflow.execution_id is None

    async def test_check_budget_within_limit(self):
        """Test check_budget passes when under budget."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        mock_session = Mock()
        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=5.0)):
            # Mock async generator
            async def mock_gen():
                yield mock_session
            mock_get_session.return_value = mock_gen()

            # Should not raise
            await workflow.check_budget()

    async def test_check_budget_exceeds_limit(self):
        """Test check_budget raises BudgetExceededError when over budget."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        mock_session = Mock()
        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=15.0)):
            # Mock async generator
            async def mock_gen():
                yield mock_session
            mock_get_session.return_value = mock_gen()

            with pytest.raises(BudgetExceededError) as exc_info:
                await workflow.check_budget()

            assert exc_info.value.spent_usd == 15.0
            assert exc_info.value.budget_usd == 10.0

    async def test_check_budget_no_execution_id(self):
        """Test check_budget returns early if no execution_id."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = None

        # Should not raise even if cost tracker not configured
        await workflow.check_budget()

    async def test_get_cost_breakdown(self):
        """Test get_cost_breakdown returns correct structure."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        mock_session = Mock()
        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=7.5)):
            # Mock async generator
            async def mock_gen():
                yield mock_session
            mock_get_session.return_value = mock_gen()

            breakdown = await workflow.get_cost_breakdown()

            assert breakdown["total_usd"] == 7.5
            assert breakdown["budget_usd"] == 10.0
            assert breakdown["remaining_usd"] == 2.5
            assert breakdown["exceeded"] is False

    async def test_get_cost_breakdown_exceeded(self):
        """Test get_cost_breakdown when budget exceeded."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        mock_session = Mock()
        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=12.0)):
            # Mock async generator
            async def mock_gen():
                yield mock_session
            mock_get_session.return_value = mock_gen()

            breakdown = await workflow.get_cost_breakdown()

            assert breakdown["total_usd"] == 12.0
            assert breakdown["budget_usd"] == 10.0
            assert breakdown["remaining_usd"] == 0
            assert breakdown["exceeded"] is True

    async def test_checkpoint_saves_state(self):
        """Test checkpoint saves state through checkpoint service."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0, enable_checkpointing=True)
        workflow.execution_id = "test-exec-123"

        with patch.object(
            workflow.checkpoint_service, "save", new=AsyncMock()
        ) as mock_save:
            await workflow.checkpoint("my-checkpoint", {"key": "value"})

            mock_save.assert_called_once_with(
                execution_id="test-exec-123",
                checkpoint_name="my-checkpoint",
                state={"key": "value"},
            )

    async def test_checkpoint_disabled(self):
        """Test checkpoint does nothing when checkpointing disabled."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0, enable_checkpointing=False)
        workflow.execution_id = "test-exec-123"

        with patch.object(
            workflow.checkpoint_service, "save", new=AsyncMock()
        ) as mock_save:
            await workflow.checkpoint("my-checkpoint", {"key": "value"})

            # Should not call save
            mock_save.assert_not_called()

    async def test_rollback_to_checkpoint(self):
        """Test rollback_to_checkpoint restores state."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        expected_state = {"restored": "state"}

        with patch.object(
            workflow.checkpoint_service,
            "rollback_to_checkpoint",
            new=AsyncMock(return_value=expected_state),
        ) as mock_rollback:
            state = await workflow.rollback_to_checkpoint("my-checkpoint")

            assert state == expected_state
            mock_rollback.assert_called_once_with(
                execution_id="test-exec-123", checkpoint_name="my-checkpoint"
            )

    async def test_rollback_to_last_checkpoint(self):
        """Test rollback_to_last_checkpoint restores most recent state."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-123"

        expected_state = {"latest": "state"}

        with patch.object(
            workflow.checkpoint_service, "load", new=AsyncMock(return_value=expected_state)
        ) as mock_load:
            state = await workflow.rollback_to_last_checkpoint()

            assert state == expected_state
            mock_load.assert_called_once_with(execution_id="test-exec-123")

    async def test_get_trace_id(self):
        """Test get_trace_id returns execution_id."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = "test-exec-789"

        trace_id = workflow.get_trace_id()

        assert trace_id == "test-exec-789"

    async def test_get_trace_id_no_execution(self):
        """Test get_trace_id returns placeholder when no execution."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)
        workflow.execution_id = None

        trace_id = workflow.get_trace_id()

        assert trace_id == "no-execution"

    async def test_execute_generates_execution_id(self):
        """Test execute generates unique execution ID."""
        workflow = WfloWorkflow(name="test", budget_usd=10.0)

        # Mock workflow execution
        mock_workflow = AsyncMock(return_value="result")

        with patch("wflo.sdk.workflow.get_session"), \
             patch("wflo.sdk.workflow.WorkflowExecutionModel"):
            await workflow.execute(mock_workflow, {"input": "data"})

            # Verify execution ID generated
            assert workflow.execution_id is not None
            assert workflow.execution_id.startswith("exec-")

    async def test_execute_callable_workflow(self):
        """Test execute works with generic callable."""
        workflow = WfloWorkflow(name="test", budget_usd=100.0)

        # Create mock callable workflow
        mock_callable = AsyncMock(return_value={"status": "success"})

        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch("wflo.sdk.workflow.WorkflowExecutionModel"), \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=5.0)):
            mock_get_session.return_value = mock_get_session_generator()
            result = await workflow.execute(mock_callable, {"input": "test"})

            # Verify callable was called with inputs
            mock_callable.assert_called_once_with({"input": "test"})
            assert result == {"status": "success"}

    async def test_execute_langgraph_workflow(self):
        """Test execute detects and handles LangGraph workflow."""
        workflow = WfloWorkflow(name="test", budget_usd=100.0)

        # Create mock LangGraph workflow (has __ainvoke__)
        mock_langgraph = Mock()
        mock_langgraph.__ainvoke__ = AsyncMock(return_value={"final": "state"})

        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch("wflo.sdk.workflow.WorkflowExecutionModel"), \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=5.0)):
            mock_get_session.return_value = mock_get_session_generator()
            result = await workflow.execute(mock_langgraph, {"initial": "state"})

            # Verify ainvoke was called
            mock_langgraph.__ainvoke__.assert_called_once_with({"initial": "state"})
            assert result == {"final": "state"}

    async def test_execute_crewai_crew(self):
        """Test execute detects and handles CrewAI crew."""
        workflow = WfloWorkflow(name="test", budget_usd=100.0)

        # Create mock CrewAI crew (has kickoff)
        mock_crew = Mock()
        mock_crew.kickoff = Mock(return_value="crew result")

        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch("wflo.sdk.workflow.WorkflowExecutionModel"), \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=5.0)):
            mock_get_session.return_value = mock_get_session_generator()
            result = await workflow.execute(mock_crew, {})

            # Verify kickoff was called
            mock_crew.kickoff.assert_called_once()
            assert result == "crew result"

    async def test_execute_raises_budget_exceeded(self):
        """Test execute raises BudgetExceededError when budget exceeded."""
        workflow = WfloWorkflow(name="test", budget_usd=5.0)

        mock_workflow = AsyncMock(return_value="result")

        with patch("wflo.sdk.workflow.get_session") as mock_get_session, \
             patch("wflo.sdk.workflow.WorkflowExecutionModel"), \
             patch.object(workflow.cost_tracker, "get_total_cost", new=AsyncMock(return_value=10.0)):
            mock_get_session.return_value = mock_get_session_generator()
            with pytest.raises(BudgetExceededError):
                await workflow.execute(mock_workflow, {})


class TestBudgetExceededError:
    """Tests for BudgetExceededError exception."""

    def test_budget_exceeded_error_attributes(self):
        """Test BudgetExceededError stores spent and budget amounts."""
        error = BudgetExceededError(
            "Budget exceeded: $12.50 > $10.00", spent_usd=12.50, budget_usd=10.00
        )

        assert error.spent_usd == 12.50
        assert error.budget_usd == 10.00
        assert "Budget exceeded" in str(error)
