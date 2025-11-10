"""Integration tests for cost tracking.

These tests verify that cost tracking works correctly with the database
and accurately tracks LLM API usage costs.

Run with: pytest tests/integration/test_cost_tracking.py -v
"""

import pytest
from sqlalchemy import select

from wflo.cost.tracker import CostTracker, TokenUsage
from wflo.db.models import WorkflowExecutionModel


@pytest.mark.asyncio
@pytest.mark.integration
class TestCostTracker:
    """Test CostTracker with database integration."""

    async def test_create_cost_tracker(self, db_session):
        """Test creating a CostTracker instance."""
        tracker = CostTracker()
        assert tracker is not None

    async def test_calculate_cost_gpt4(self, db_session):
        """Test calculating cost for GPT-4 API call."""
        tracker = CostTracker()

        usage = TokenUsage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        cost = tracker.calculate_cost(usage)

        # GPT-4 pricing (as of 2024): $0.03/1K prompt, $0.06/1K completion
        expected_cost = (100 * 0.03 / 1000) + (50 * 0.06 / 1000)
        assert abs(cost - expected_cost) < 0.0001  # Allow small floating point error

    async def test_calculate_cost_gpt35_turbo(self, db_session):
        """Test calculating cost for GPT-3.5-turbo API call."""
        tracker = CostTracker()

        usage = TokenUsage(
            model="gpt-3.5-turbo",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        cost = tracker.calculate_cost(usage)

        # GPT-3.5-turbo pricing: $0.0015/1K prompt, $0.002/1K completion
        expected_cost = (1000 * 0.0015 / 1000) + (500 * 0.002 / 1000)
        assert abs(cost - expected_cost) < 0.0001

    async def test_calculate_cost_claude_sonnet(self, db_session):
        """Test calculating cost for Claude Sonnet API call."""
        tracker = CostTracker()

        usage = TokenUsage(
            model="claude-3-5-sonnet-20241022",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        cost = tracker.calculate_cost(usage)

        # Claude Sonnet pricing: $0.003/1K prompt, $0.015/1K completion
        expected_cost = (1000 * 0.003 / 1000) + (500 * 0.015 / 1000)
        assert abs(cost - expected_cost) < 0.0001

    async def test_track_cost_in_database(self, db_session):
        """Test tracking cost in database."""
        from datetime import datetime, timezone

        from wflo.db.models import WorkflowDefinitionModel

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id="test-workflow",
            name="Test Workflow",
            description="Test",
            version=1,
            definition={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create workflow execution
        execution = WorkflowExecutionModel(
            id="test-execution-1",
            workflow_id="test-workflow",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            inputs={},
            trace_id="trace-1",
            correlation_id="corr-1",
        )
        db_session.add(execution)
        await db_session.commit()

        # Track cost
        tracker = CostTracker()
        usage = TokenUsage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        await tracker.track_cost(
            session=db_session,
            execution_id="test-execution-1",
            usage=usage,
        )

        # Verify cost was tracked
        result = await db_session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == "test-execution-1"
            )
        )
        updated_execution = result.scalar_one()

        assert updated_execution.cost_prompt_tokens == 100
        assert updated_execution.cost_completion_tokens == 50
        assert updated_execution.cost_total_usd > 0

    async def test_aggregate_costs_multiple_calls(self, db_session):
        """Test aggregating costs from multiple LLM calls."""
        from datetime import datetime, timezone

        from wflo.db.models import WorkflowDefinitionModel

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id="test-workflow-2",
            name="Test Workflow 2",
            description="Test",
            version=1,
            definition={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create workflow execution
        execution = WorkflowExecutionModel(
            id="test-execution-2",
            workflow_id="test-workflow-2",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            inputs={},
            trace_id="trace-2",
            correlation_id="corr-2",
        )
        db_session.add(execution)
        await db_session.commit()

        # Track multiple costs
        tracker = CostTracker()

        # First call
        usage1 = TokenUsage(
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )
        await tracker.track_cost(
            session=db_session,
            execution_id="test-execution-2",
            usage=usage1,
        )

        # Second call
        usage2 = TokenUsage(
            model="gpt-4",
            prompt_tokens=200,
            completion_tokens=100,
        )
        await tracker.track_cost(
            session=db_session,
            execution_id="test-execution-2",
            usage=usage2,
        )

        # Verify aggregated costs
        result = await db_session.execute(
            select(WorkflowExecutionModel).where(
                WorkflowExecutionModel.id == "test-execution-2"
            )
        )
        updated_execution = result.scalar_one()

        assert updated_execution.cost_prompt_tokens == 300  # 100 + 200
        assert updated_execution.cost_completion_tokens == 150  # 50 + 100

        # Calculate expected total cost
        cost1 = tracker.calculate_cost(usage1)
        cost2 = tracker.calculate_cost(usage2)
        expected_total = cost1 + cost2

        assert abs(updated_execution.cost_total_usd - expected_total) < 0.0001


@pytest.mark.asyncio
@pytest.mark.integration
class TestBudgetCheck:
    """Test budget checking functionality."""

    async def test_check_budget_within_limit(self, db_session):
        """Test budget check when within limit."""
        from datetime import datetime, timezone

        from wflo.cost.tracker import check_budget
        from wflo.db.models import WorkflowDefinitionModel

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id="test-workflow-budget-1",
            name="Test Workflow",
            description="Test",
            version=1,
            definition={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create workflow execution with some cost
        execution = WorkflowExecutionModel(
            id="test-execution-budget-1",
            workflow_id="test-workflow-budget-1",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            inputs={},
            trace_id="trace-1",
            correlation_id="corr-1",
            cost_total_usd=5.0,  # $5 spent
        )
        db_session.add(execution)
        await db_session.commit()

        # Check budget (limit: $10)
        within_budget = await check_budget(
            session=db_session,
            execution_id="test-execution-budget-1",
            max_cost_usd=10.0,
        )

        assert within_budget is True

    async def test_check_budget_exceeds_limit(self, db_session):
        """Test budget check when exceeding limit."""
        from datetime import datetime, timezone

        from wflo.cost.tracker import check_budget
        from wflo.db.models import WorkflowDefinitionModel

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id="test-workflow-budget-2",
            name="Test Workflow",
            description="Test",
            version=1,
            definition={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create workflow execution with high cost
        execution = WorkflowExecutionModel(
            id="test-execution-budget-2",
            workflow_id="test-workflow-budget-2",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            inputs={},
            trace_id="trace-2",
            correlation_id="corr-2",
            cost_total_usd=15.0,  # $15 spent
        )
        db_session.add(execution)
        await db_session.commit()

        # Check budget (limit: $10)
        within_budget = await check_budget(
            session=db_session,
            execution_id="test-execution-budget-2",
            max_cost_usd=10.0,
        )

        assert within_budget is False

    async def test_check_budget_at_exact_limit(self, db_session):
        """Test budget check when at exact limit."""
        from datetime import datetime, timezone

        from wflo.cost.tracker import check_budget
        from wflo.db.models import WorkflowDefinitionModel

        # Create workflow definition
        workflow_def = WorkflowDefinitionModel(
            id="test-workflow-budget-3",
            name="Test Workflow",
            description="Test",
            version=1,
            definition={},
        )
        db_session.add(workflow_def)
        await db_session.commit()

        # Create workflow execution at exact limit
        execution = WorkflowExecutionModel(
            id="test-execution-budget-3",
            workflow_id="test-workflow-budget-3",
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            inputs={},
            trace_id="trace-3",
            correlation_id="corr-3",
            cost_total_usd=10.0,  # Exactly $10 spent
        )
        db_session.add(execution)
        await db_session.commit()

        # Check budget (limit: $10)
        within_budget = await check_budget(
            session=db_session,
            execution_id="test-execution-budget-3",
            max_cost_usd=10.0,
        )

        assert within_budget is True  # At limit is considered within budget


@pytest.mark.asyncio
@pytest.mark.integration
class TestCostEstimation:
    """Test cost estimation functionality."""

    async def test_estimate_cost_for_prompt(self, db_session):
        """Test estimating cost for a given prompt."""
        tracker = CostTracker()

        # Estimate cost for a prompt (roughly 100 tokens)
        prompt = "Write a comprehensive analysis of the following topic: " * 10

        estimated_cost = tracker.estimate_cost(
            model="gpt-4",
            prompt=prompt,
            max_completion_tokens=500,
        )

        # Should return a reasonable estimate
        assert estimated_cost > 0
        assert estimated_cost < 1.0  # Should be less than $1 for this small prompt

    async def test_estimate_cost_different_models(self, db_session):
        """Test cost estimation across different models."""
        tracker = CostTracker()

        prompt = "Hello, world!"

        # GPT-4 should be more expensive than GPT-3.5
        gpt4_cost = tracker.estimate_cost(
            model="gpt-4",
            prompt=prompt,
            max_completion_tokens=100,
        )

        gpt35_cost = tracker.estimate_cost(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_completion_tokens=100,
        )

        assert gpt4_cost > gpt35_cost
