"""Unit tests for checkpoint decorator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from wflo.sdk.decorators.checkpoint import checkpoint, _extract_state, checkpoint_after_agent
from wflo.sdk.context import set_current_execution_id, clear_context


@pytest.fixture(autouse=True)
def setup_context():
    """Setup execution context for tests."""
    set_current_execution_id("test-exec-456")
    yield
    clear_context()


class TestExtractState:
    """Tests for _extract_state function."""

    def test_extract_state_from_dict_result(self):
        """Test extracting state when result is a dict."""
        result = {"key": "value", "count": 42}
        args = ()
        kwargs = {}

        state = _extract_state(result, args, kwargs)

        assert state == {"key": "value", "count": 42}

    def test_extract_state_from_object(self):
        """Test extracting state from object with __dict__."""
        result = Mock()
        result.value = "test"
        result.count = 42

        state = _extract_state(result, (), {})

        assert "result" in state
        assert isinstance(state["result"], dict)

    def test_extract_state_from_primitive(self):
        """Test extracting state from primitive value."""
        result = "simple string"

        state = _extract_state(result, (), {})

        assert state == {"result": "simple string"}

    def test_extract_state_from_args(self):
        """Test extracting state from function arguments (LangGraph pattern)."""
        result = {"step": "completed"}
        args = ({"query": "test", "plan": "do something"},)
        kwargs = {}

        state = _extract_state(result, args, kwargs)

        # Should merge result with first arg (state dict)
        assert state["step"] == "completed"
        assert state["query"] == "test"
        assert state["plan"] == "do something"

    def test_extract_state_from_kwargs(self):
        """Test extracting state from kwargs."""
        result = {"step": "completed"}
        args = ()
        kwargs = {"state": {"extra": "data"}}

        state = _extract_state(result, args, kwargs)

        assert state["step"] == "completed"
        assert state["extra"] == "data"


@pytest.mark.asyncio
class TestCheckpointDecorator:
    """Tests for @checkpoint decorator."""

    async def test_checkpoint_saves_state_after_execution(self):
        """Test checkpoint decorator saves state after function execution."""
        with patch(
            "wflo.sdk.decorators.checkpoint.get_checkpoint_service"
        ) as mock_get_service:
            # Setup mock checkpoint service
            mock_service = Mock()
            mock_service.save = AsyncMock()
            mock_get_service.return_value = mock_service

            # Create decorated function
            @checkpoint
            async def my_step(state):
                state["processed"] = True
                return state

            # Execute
            input_state = {"value": 42}
            result = await my_step(input_state)

            # Verify result returned correctly
            assert result["value"] == 42
            assert result["processed"] is True

            # Verify checkpoint saved
            mock_service.save.assert_called_once()
            call_args = mock_service.save.call_args[1]
            assert call_args["execution_id"] == "test-exec-456"
            assert call_args["checkpoint_name"] == "my_step"
            assert "processed" in call_args["state"]
            assert call_args["state"]["processed"] is True

    async def test_checkpoint_with_custom_name(self):
        """Test checkpoint decorator with custom name."""
        with patch(
            "wflo.sdk.decorators.checkpoint.get_checkpoint_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.save = AsyncMock()
            mock_get_service.return_value = mock_service

            # Create decorated function with custom name
            @checkpoint(name="custom_checkpoint")
            async def my_function():
                return {"status": "done"}

            # Execute
            await my_function()

            # Verify custom name used
            call_args = mock_service.save.call_args[1]
            assert call_args["checkpoint_name"] == "custom_checkpoint"

    async def test_checkpoint_handles_errors_gracefully(self):
        """Test checkpoint decorator doesn't fail execution on checkpoint error."""
        with patch(
            "wflo.sdk.decorators.checkpoint.get_checkpoint_service"
        ) as mock_get_service, patch(
            "wflo.sdk.decorators.checkpoint.logger"
        ) as mock_logger:
            # Setup mock to raise error on save
            mock_service = Mock()
            mock_service.save = AsyncMock(side_effect=Exception("DB Error"))
            mock_get_service.return_value = mock_service

            # Create decorated function
            @checkpoint
            async def my_function():
                return {"result": "success"}

            # Execute - should raise original exception, not checkpoint error
            with pytest.raises(Exception, match="DB Error"):
                await my_function()

            # Verify error logged
            mock_logger.error.assert_called_once()

    async def test_checkpoint_preserves_function_metadata(self):
        """Test checkpoint decorator preserves function metadata."""

        @checkpoint
        async def my_function():
            """My docstring."""
            return {}

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    async def test_checkpoint_without_parentheses(self):
        """Test checkpoint decorator can be used without parentheses."""
        with patch(
            "wflo.sdk.decorators.checkpoint.get_checkpoint_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.save = AsyncMock()
            mock_get_service.return_value = mock_service

            # Use decorator without parentheses
            @checkpoint
            async def my_function():
                return {"status": "ok"}

            await my_function()

            # Should still work
            assert mock_service.save.called


@pytest.mark.asyncio
class TestCheckpointAfterAgent:
    """Tests for checkpoint_after_agent wrapper."""

    async def test_checkpoint_after_agent_adds_callback(self):
        """Test checkpoint_after_agent adds callback to task."""
        # Mock CrewAI task
        task = Mock()
        task.callback = None

        # Wrap task
        wrapped_task = checkpoint_after_agent(task, agent_name="test_agent")

        # Verify callback added
        assert wrapped_task.callback is not None
        assert callable(wrapped_task.callback)

    async def test_checkpoint_after_agent_preserves_existing_callback(self):
        """Test checkpoint_after_agent preserves existing callback."""
        # Mock existing callback
        original_callback_called = False

        async def original_callback(output):
            nonlocal original_callback_called
            original_callback_called = True

        # Mock task with existing callback
        task = Mock()
        task.callback = original_callback

        # Wrap task
        with patch(
            "wflo.sdk.decorators.checkpoint.get_checkpoint_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.save = AsyncMock()
            mock_get_service.return_value = mock_service

            wrapped_task = checkpoint_after_agent(task, agent_name="test_agent")

            # Execute callback
            await wrapped_task.callback("test output")

            # Verify both checkpoint and original callback executed
            assert mock_service.save.called
            assert original_callback_called
