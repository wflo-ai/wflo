"""Unit tests for LLM step implementation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from wflo.workflow.steps import LLMStep, StepContext, StepResult


@pytest.mark.unit
class TestLLMStep:
    """Test LLM step implementation."""

    def test_init_defaults(self):
        """Test LLM step initialization with defaults."""
        step = LLMStep(step_id="test-step")

        assert step.step_id == "test-step"
        assert step.model == "gpt-4"
        assert step.prompt_template == "{input}"
        assert step.system_prompt is None
        assert step.max_tokens == 500
        assert step.temperature == 0.7

    def test_init_custom(self):
        """Test LLM step initialization with custom values."""
        step = LLMStep(
            step_id="custom-step",
            model="gpt-3.5-turbo",
            prompt_template="Hello {name}, you are {age}",
            system_prompt="You are a helpful assistant",
            max_tokens=200,
            temperature=0.5,
        )

        assert step.step_id == "custom-step"
        assert step.model == "gpt-3.5-turbo"
        assert step.prompt_template == "Hello {name}, you are {age}"
        assert step.system_prompt == "You are a helpful assistant"
        assert step.max_tokens == 200
        assert step.temperature == 0.5

    def test_render_prompt_simple(self):
        """Test simple prompt template rendering."""
        step = LLMStep(step_id="test", prompt_template="Hello {name}")

        prompt = step._render_prompt({"name": "Alice"})
        assert prompt == "Hello Alice"

    def test_render_prompt_multiple_variables(self):
        """Test prompt rendering with multiple variables."""
        step = LLMStep(
            step_id="test", prompt_template="Hello {name}, you are {age} years old"
        )

        prompt = step._render_prompt({"name": "Alice", "age": 30})
        assert prompt == "Hello Alice, you are 30 years old"

    def test_render_prompt_missing_variable(self):
        """Test prompt rendering with missing variable raises ValueError."""
        step = LLMStep(step_id="test", prompt_template="Hello {name}")

        with pytest.raises(ValueError, match="Missing required input variable"):
            step._render_prompt({"age": 30})

    def test_render_prompt_extra_variables(self):
        """Test prompt rendering ignores extra variables."""
        step = LLMStep(step_id="test", prompt_template="Hello {name}")

        prompt = step._render_prompt({"name": "Alice", "age": 30, "city": "NYC"})
        assert prompt == "Hello Alice"

    @pytest.mark.asyncio
    async def test_validate_no_api_key(self):
        """Test validation fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            step = LLMStep(step_id="test", prompt_template="Hello")
            context = StepContext(
                execution_id="ex-1",
                step_execution_id="step-1",
                inputs={},
                state={},
                config={},
            )

            is_valid = await step.validate(context)
            assert not is_valid

    @pytest.mark.asyncio
    async def test_validate_missing_input(self):
        """Test validation fails with missing template variable."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            step = LLMStep(step_id="test", prompt_template="Hello {name}")
            context = StepContext(
                execution_id="ex-1",
                step_execution_id="step-1",
                inputs={"age": 30},  # Missing 'name'
                state={},
                config={},
            )

            is_valid = await step.validate(context)
            assert not is_valid

    @pytest.mark.asyncio
    async def test_validate_success(self):
        """Test validation succeeds with API key and inputs."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            step = LLMStep(step_id="test", prompt_template="Hello {name}")
            context = StepContext(
                execution_id="ex-1",
                step_execution_id="step-1",
                inputs={"name": "Alice"},
                state={},
                config={},
            )

            is_valid = await step.validate(context)
            assert is_valid

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful LLM execution with mocked API."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello, Alice!"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15

            # Mock CostTracker
            mock_cost = 0.002

            with patch("wflo.workflow.steps.llm.AsyncOpenAI") as mock_openai:
                with patch(
                    "wflo.workflow.steps.llm.CostTracker"
                ) as mock_cost_tracker:
                    # Setup mocks
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        return_value=mock_response
                    )
                    mock_openai.return_value = mock_client

                    mock_tracker_instance = MagicMock()
                    mock_tracker_instance.calculate_cost.return_value = mock_cost
                    mock_cost_tracker.return_value = mock_tracker_instance

                    # Execute step
                    step = LLMStep(
                        step_id="test",
                        model="gpt-4",
                        prompt_template="Say hello to {name}",
                    )

                    context = StepContext(
                        execution_id="ex-1",
                        step_execution_id="step-1",
                        inputs={"name": "Alice"},
                        state={},
                        config={},
                    )

                    result = await step.execute(context)

                    # Verify result
                    assert result.success
                    assert result.output["text"] == "Hello, Alice!"
                    assert result.output["prompt"] == "Say hello to Alice"
                    assert result.output["model"] == "gpt-4"
                    assert result.cost_usd == mock_cost
                    assert result.metadata["prompt_tokens"] == 10
                    assert result.metadata["completion_tokens"] == 5
                    assert result.metadata["total_tokens"] == 15
                    assert result.metadata["finish_reason"] == "stop"
                    assert result.started_at is not None
                    assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_execute_with_system_prompt(self):
        """Test execution with system prompt."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage.prompt_tokens = 20
            mock_response.usage.completion_tokens = 10
            mock_response.usage.total_tokens = 30

            with patch("wflo.workflow.steps.llm.AsyncOpenAI") as mock_openai:
                with patch("wflo.workflow.steps.llm.CostTracker") as mock_cost_tracker:
                    mock_client = AsyncMock()
                    mock_client.chat.completions.create = AsyncMock(
                        return_value=mock_response
                    )
                    mock_openai.return_value = mock_client

                    mock_tracker_instance = MagicMock()
                    mock_tracker_instance.calculate_cost.return_value = 0.005
                    mock_cost_tracker.return_value = mock_tracker_instance

                    step = LLMStep(
                        step_id="test",
                        model="gpt-4",
                        prompt_template="{query}",
                        system_prompt="You are a helpful assistant",
                    )

                    context = StepContext(
                        execution_id="ex-1",
                        step_execution_id="step-1",
                        inputs={"query": "What is 2+2?"},
                        state={},
                        config={},
                    )

                    result = await step.execute(context)

                    # Verify system prompt was included
                    assert result.success
                    call_args = (
                        mock_client.chat.completions.create.call_args[1]["messages"]
                    )
                    assert len(call_args) == 2
                    assert call_args[0]["role"] == "system"
                    assert call_args[0]["content"] == "You are a helpful assistant"
                    assert call_args[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """Test execution fails gracefully without API key."""
        with patch.dict("os.environ", {}, clear=True):
            step = LLMStep(step_id="test", prompt_template="Hello")

            context = StepContext(
                execution_id="ex-1",
                step_execution_id="step-1",
                inputs={},
                state={},
                config={},
            )

            result = await step.execute(context)

            assert not result.success
            assert "OPENAI_API_KEY" in result.error
            assert result.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test execution handles API errors gracefully."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("wflo.workflow.steps.llm.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("API rate limit exceeded")
                )
                mock_openai.return_value = mock_client

                step = LLMStep(step_id="test", prompt_template="Hello")

                context = StepContext(
                    execution_id="ex-1",
                    step_execution_id="step-1",
                    inputs={},
                    state={},
                    config={},
                )

                result = await step.execute(context)

                assert not result.success
                assert "API rate limit exceeded" in result.error
                assert result.cost_usd == 0.0

    def test_to_dict(self):
        """Test step serialization to dictionary."""
        step = LLMStep(
            step_id="test",
            model="gpt-3.5-turbo",
            prompt_template="Hello {name}",
            system_prompt="Be helpful",
            max_tokens=100,
            temperature=0.5,
        )

        data = step.to_dict()

        assert data["type"] == "LLMStep"
        assert data["step_id"] == "test"
        assert data["model"] == "gpt-3.5-turbo"
        assert data["prompt_template"] == "Hello {name}"
        assert data["system_prompt"] == "Be helpful"
        assert data["max_tokens"] == 100
        assert data["temperature"] == 0.5

    def test_repr(self):
        """Test string representation."""
        step = LLMStep(step_id="my-step")

        assert repr(step) == "LLMStep(step_id='my-step')"


@pytest.mark.unit
class TestStepResult:
    """Test StepResult dataclass."""

    def test_duration_seconds(self):
        """Test duration calculation."""
        start = datetime(2025, 1, 1, 12, 0, 0)
        end = datetime(2025, 1, 1, 12, 0, 5)

        result = StepResult(
            success=True,
            output={},
            started_at=start,
            completed_at=end,
        )

        assert result.duration_seconds == 5.0

    def test_auto_timestamps(self):
        """Test automatic timestamp generation."""
        result = StepResult(success=True, output={})

        assert result.started_at is not None
        assert result.completed_at is not None
        assert isinstance(result.started_at, datetime)
        assert isinstance(result.completed_at, datetime)


@pytest.mark.unit
class TestStepContext:
    """Test StepContext dataclass."""

    def test_init_minimal(self):
        """Test context with minimal fields."""
        context = StepContext(
            execution_id="ex-1",
            step_execution_id="step-1",
            inputs={"key": "value"},
            state={},
        )

        assert context.execution_id == "ex-1"
        assert context.step_execution_id == "step-1"
        assert context.inputs == {"key": "value"}
        assert context.state == {}
        assert context.config == {}

    def test_init_with_config(self):
        """Test context with config."""
        context = StepContext(
            execution_id="ex-1",
            step_execution_id="step-1",
            inputs={},
            state={},
            config={"timeout": 30},
        )

        assert context.config == {"timeout": 30}
