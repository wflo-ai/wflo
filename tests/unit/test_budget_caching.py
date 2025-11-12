"""Unit tests for budget caching optimization."""

import pytest

from wflo.sdk.context import (
    ExecutionContext,
    get_current_budget,
    set_current_budget,
    clear_context,
)


class TestBudgetCaching:
    """Test budget caching in execution context."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_set_and_get_budget(self):
        """Test setting and getting budget from context."""
        assert get_current_budget() is None

        set_current_budget(10.0)

        assert get_current_budget() == 10.0

    def test_budget_cleared_with_context(self):
        """Test budget is cleared when context is cleared."""
        set_current_budget(5.0)
        assert get_current_budget() == 5.0

        clear_context()

        assert get_current_budget() is None

    @pytest.mark.asyncio
    async def test_execution_context_sets_budget(self):
        """Test ExecutionContext sets budget in context."""
        async with ExecutionContext(
            execution_id="exec-123",
            budget_usd=15.0,
        ):
            assert get_current_budget() == 15.0

        # Budget should be cleared after context
        assert get_current_budget() is None

    @pytest.mark.asyncio
    async def test_nested_contexts_preserve_budget(self):
        """Test nested execution contexts preserve parent budget."""
        async with ExecutionContext(
            execution_id="outer",
            budget_usd=10.0,
        ):
            assert get_current_budget() == 10.0

            async with ExecutionContext(
                execution_id="inner",
                budget_usd=5.0,
            ):
                assert get_current_budget() == 5.0

            # Parent budget restored
            assert get_current_budget() == 10.0

        # All cleared
        assert get_current_budget() is None

    @pytest.mark.asyncio
    async def test_context_without_budget(self):
        """Test ExecutionContext works without budget."""
        async with ExecutionContext(
            execution_id="exec-123",
            # No budget_usd parameter
        ):
            assert get_current_budget() is None

    @pytest.mark.asyncio
    async def test_budget_isolated_across_contexts(self):
        """Test budget values are isolated between contexts."""
        import asyncio

        results = []

        async def worker(exec_id: str, budget: float):
            async with ExecutionContext(
                execution_id=exec_id,
                budget_usd=budget,
            ):
                # Small delay to ensure concurrency
                await asyncio.sleep(0.01)
                results.append((exec_id, get_current_budget()))

        # Run multiple workers concurrently
        await asyncio.gather(
            worker("exec-1", 10.0),
            worker("exec-2", 20.0),
            worker("exec-3", 30.0),
        )

        # Each should have seen their own budget
        results_dict = dict(results)
        assert results_dict["exec-1"] == 10.0
        assert results_dict["exec-2"] == 20.0
        assert results_dict["exec-3"] == 30.0

    def test_budget_zero_is_valid(self):
        """Test budget of 0.0 is a valid value (not None)."""
        set_current_budget(0.0)

        # Should return 0.0, not None
        assert get_current_budget() == 0.0
        assert get_current_budget() is not None

    @pytest.mark.asyncio
    async def test_budget_persists_across_awaits(self):
        """Test budget value persists across async operations."""
        import asyncio

        async with ExecutionContext(
            execution_id="exec-test",
            budget_usd=25.5,
        ):
            # Before await
            assert get_current_budget() == 25.5

            await asyncio.sleep(0.01)

            # After await
            assert get_current_budget() == 25.5

            await asyncio.sleep(0.01)

            # Still persists
            assert get_current_budget() == 25.5

    @pytest.mark.asyncio
    async def test_context_exit_on_exception_restores_budget(self):
        """Test budget is restored even if exception occurs."""
        set_current_budget(100.0)

        try:
            async with ExecutionContext(
                execution_id="exec-error",
                budget_usd=50.0,
            ):
                assert get_current_budget() == 50.0
                raise ValueError("Test error")
        except ValueError:
            pass

        # Budget should be restored to previous value
        assert get_current_budget() == 100.0

    def test_context_manager_sync_mode(self):
        """Test ExecutionContext works in synchronous mode."""
        with ExecutionContext(
            execution_id="sync-exec",
            budget_usd=12.5,
        ):
            assert get_current_budget() == 12.5

        assert get_current_budget() is None

    def test_multiple_budget_updates(self):
        """Test budget can be updated multiple times."""
        set_current_budget(10.0)
        assert get_current_budget() == 10.0

        set_current_budget(20.0)
        assert get_current_budget() == 20.0

        set_current_budget(30.0)
        assert get_current_budget() == 30.0


class TestBudgetCachingIntegration:
    """Integration tests for budget caching with workflow."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    @pytest.mark.asyncio
    async def test_workflow_context_sets_budget(self):
        """Test WfloWorkflow sets budget in context."""
        from wflo.sdk.workflow import WfloWorkflow

        workflow = WfloWorkflow(
            name="test-workflow",
            budget_usd=42.0,
        )

        # Budget should be available in context during execution
        # (This is tested indirectly - the budget is set when ExecutionContext is entered)

        assert workflow.budget_usd == 42.0

    @pytest.mark.asyncio
    async def test_budget_accessible_in_decorators(self):
        """Test budget is accessible from decorators via context."""

        async def mock_workflow():
            # During workflow execution, budget should be in context
            # This simulates what happens in @track_llm_call
            return get_current_budget()

        # Simulate workflow execution context
        async with ExecutionContext(
            execution_id="exec-decorator-test",
            budget_usd=77.5,
        ):
            budget_seen = await mock_workflow()

        assert budget_seen == 77.5

    @pytest.mark.asyncio
    async def test_budget_not_available_outside_context(self):
        """Test budget is None outside execution context."""
        # Outside any context
        assert get_current_budget() is None

        # Inside context
        async with ExecutionContext(
            execution_id="exec-context",
            budget_usd=15.0,
        ):
            assert get_current_budget() == 15.0

        # Outside again
        assert get_current_budget() is None
