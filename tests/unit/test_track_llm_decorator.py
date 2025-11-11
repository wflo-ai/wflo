"""Unit tests for track_llm decorator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from wflo.sdk.decorators.track_llm import track_llm_call, _extract_usage, _get_provider_from_model
from wflo.sdk.context import set_current_execution_id, clear_context


@pytest.fixture(autouse=True)
def setup_context():
    """Setup execution context for tests."""
    set_current_execution_id("test-exec-123")
    yield
    clear_context()


class TestExtractUsage:
    """Tests for _extract_usage function."""

    def test_extract_usage_openai_format(self):
        """Test extracting usage from OpenAI response format."""
        # Mock OpenAI response
        response = Mock()
        response.usage = Mock()
        response.usage.prompt_tokens = 100
        response.usage.completion_tokens = 50
        response.usage.total_tokens = 150

        result = _extract_usage(response, "gpt-4")

        assert result == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

    def test_extract_usage_anthropic_format(self):
        """Test extracting usage from Anthropic Claude response format."""
        # Mock Anthropic response - use spec to limit attributes
        usage_mock = Mock(spec=['input_tokens', 'output_tokens'])
        usage_mock.input_tokens = 100
        usage_mock.output_tokens = 50

        response = Mock(spec=['usage'])
        response.usage = usage_mock

        result = _extract_usage(response, "claude-3-5-sonnet-20241022")

        assert result == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

    def test_extract_usage_dict_openai_format(self):
        """Test extracting usage from dict with OpenAI format."""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }

        result = _extract_usage(response, "gpt-4")

        assert result == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

    def test_extract_usage_dict_anthropic_format(self):
        """Test extracting usage from dict with Anthropic format."""
        response = {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            }
        }

        result = _extract_usage(response, "claude-3-5-sonnet-20241022")

        assert result == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

    def test_extract_usage_no_usage_field(self):
        """Test extracting usage when no usage field exists."""
        response = Mock(spec=[])  # Empty spec - no attributes

        result = _extract_usage(response, "gpt-4")

        assert result is None


class TestGetProviderFromModel:
    """Tests for _get_provider_from_model function."""

    @pytest.mark.parametrize(
        "model,expected_provider",
        [
            ("gpt-4", "openai"),
            ("gpt-3.5-turbo", "openai"),
            ("o1-preview", "openai"),
            ("o3-mini", "openai"),
            ("claude-3-5-sonnet-20241022", "anthropic"),
            ("claude-2", "anthropic"),
            ("gemini-pro", "google"),
            ("gemini-1.5-flash", "google"),
            ("llama-3-70b", "meta"),
            ("mistral-large", "mistral"),
            ("unknown-model-v1", "unknown"),
        ],
    )
    def test_provider_detection(self, model, expected_provider):
        """Test provider detection from model name."""
        result = _get_provider_from_model(model)
        assert result == expected_provider


@pytest.mark.asyncio
class TestTrackLlmCallDecorator:
    """Tests for @track_llm_call decorator."""

    async def test_decorator_tracks_successful_call(self):
        """Test decorator tracks successful LLM call."""
        # Mock dependencies
        with patch("wflo.sdk.decorators.track_llm.CostTracker") as MockCostTracker, \
             patch("wflo.sdk.decorators.track_llm.metrics") as mock_metrics, \
             patch("wflo.sdk.decorators.track_llm.logger") as mock_logger:

            # Setup mock cost tracker
            mock_cost_tracker = MockCostTracker.return_value
            mock_cost_tracker.track_llm_call = AsyncMock(return_value=0.0234)

            # Create decorated function
            @track_llm_call(model="gpt-4")
            async def mock_llm_call():
                response = Mock()
                response.usage = Mock()
                response.usage.prompt_tokens = 100
                response.usage.completion_tokens = 50
                response.usage.total_tokens = 150
                return response

            # Execute
            result = await mock_llm_call()

            # Verify response returned
            assert result is not None
            assert result.usage.total_tokens == 150

            # Verify cost tracking called
            mock_cost_tracker.track_llm_call.assert_called_once()
            call_args = mock_cost_tracker.track_llm_call.call_args[1]
            assert call_args["execution_id"] == "test-exec-123"
            assert call_args["provider"] == "openai"
            assert call_args["model"] == "gpt-4"
            assert call_args["prompt_tokens"] == 100
            assert call_args["completion_tokens"] == 50

            # Verify metrics emitted
            assert mock_metrics.histogram.called
            assert mock_metrics.counter.called

            # Verify logging
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0]
            assert log_call[0] == "llm_call_completed"

    async def test_decorator_handles_error(self):
        """Test decorator handles LLM call errors."""
        with patch("wflo.sdk.decorators.track_llm.metrics") as mock_metrics, \
             patch("wflo.sdk.decorators.track_llm.logger") as mock_logger:

            # Create decorated function that raises error
            @track_llm_call(model="gpt-4")
            async def mock_failing_call():
                raise ValueError("API Error")

            # Execute and expect error
            with pytest.raises(ValueError, match="API Error"):
                await mock_failing_call()

            # Verify error logged
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args[0]
            assert log_call[0] == "llm_call_failed"

            # Verify error metric emitted
            error_metric_calls = [
                call for call in mock_metrics.counter.call_args_list
                if "status" in str(call) and "error" in str(call)
            ]
            assert len(error_metric_calls) > 0

    async def test_decorator_no_usage_warning(self):
        """Test decorator logs warning when no usage data."""
        with patch("wflo.sdk.decorators.track_llm.logger") as mock_logger:

            # Create decorated function returning response without usage
            @track_llm_call(model="gpt-4")
            async def mock_llm_call_no_usage():
                return Mock(spec=[])  # No usage attribute

            # Execute
            await mock_llm_call_no_usage()

            # Verify warning logged
            mock_logger.warning.assert_called_once()
            log_call = mock_logger.warning.call_args[0]
            assert log_call[0] == "llm_call_no_usage"

    async def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves original function metadata."""

        @track_llm_call(model="gpt-4")
        async def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."
