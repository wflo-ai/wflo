"""Unit tests for retry manager with exponential backoff."""

import asyncio
import pytest

from wflo.resilience.retry import (
    RetryManager,
    RetryStrategy,
    RetryExhaustedError,
    retry_with_backoff,
)


class TestRetryManager:
    """Test RetryManager class."""

    def test_calculate_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        retry_manager = RetryManager(
            max_retries=5,
            base_delay=1.0,
            multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,  # Disable jitter for predictable tests
        )

        # Exponential: 1.0 * 2^n
        assert retry_manager.calculate_delay(0) == 1.0  # 2^0 = 1
        assert retry_manager.calculate_delay(1) == 2.0  # 2^1 = 2
        assert retry_manager.calculate_delay(2) == 4.0  # 2^2 = 4
        assert retry_manager.calculate_delay(3) == 8.0  # 2^3 = 8

    def test_calculate_delay_linear(self):
        """Test linear backoff delay calculation."""
        retry_manager = RetryManager(
            base_delay=1.0,
            multiplier=1.0,
            strategy=RetryStrategy.LINEAR,
            jitter=False,
        )

        # Linear: base * (attempt + 1) * multiplier
        assert retry_manager.calculate_delay(0) == 1.0  # 1 * 1 * 1
        assert retry_manager.calculate_delay(1) == 2.0  # 1 * 2 * 1
        assert retry_manager.calculate_delay(2) == 3.0  # 1 * 3 * 1
        assert retry_manager.calculate_delay(3) == 4.0  # 1 * 4 * 1

    def test_calculate_delay_fixed(self):
        """Test fixed delay calculation."""
        retry_manager = RetryManager(
            base_delay=5.0,
            strategy=RetryStrategy.FIXED,
            jitter=False,
        )

        assert retry_manager.calculate_delay(0) == 5.0
        assert retry_manager.calculate_delay(1) == 5.0
        assert retry_manager.calculate_delay(2) == 5.0

    def test_calculate_delay_with_max_cap(self):
        """Test delay is capped at max_delay."""
        retry_manager = RetryManager(
            base_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,
        )

        assert retry_manager.calculate_delay(0) == 1.0
        assert retry_manager.calculate_delay(1) == 2.0
        assert retry_manager.calculate_delay(2) == 4.0
        assert retry_manager.calculate_delay(3) == 8.0
        assert retry_manager.calculate_delay(4) == 10.0  # Capped
        assert retry_manager.calculate_delay(5) == 10.0  # Still capped

    def test_calculate_delay_with_jitter(self):
        """Test jitter adds randomness to delay."""
        retry_manager = RetryManager(
            base_delay=10.0,
            strategy=RetryStrategy.FIXED,
            jitter=True,
            jitter_factor=0.1,  # ±10%
        )

        # With jitter, delay should be in range [9.0, 11.0]
        for _ in range(10):
            delay = retry_manager.calculate_delay(0)
            assert 9.0 <= delay <= 11.0

    @pytest.mark.asyncio
    async def test_execute_success_first_try(self):
        """Test successful execution on first try."""
        retry_manager = RetryManager(max_retries=3)

        async def successful_function():
            return "success"

        result = await retry_manager.execute(successful_function)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_success_after_retries(self):
        """Test successful execution after some failures."""
        retry_manager = RetryManager(
            max_retries=3,
            base_delay=0.01,  # Fast for testing
        )

        attempts = []

        async def flaky_function():
            attempts.append(len(attempts))
            if len(attempts) < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_manager.execute(
            flaky_function,
            retryable_exceptions=(ValueError,),
        )

        assert result == "success"
        assert len(attempts) == 3  # Failed twice, succeeded on third

    @pytest.mark.asyncio
    async def test_execute_retry_exhausted(self):
        """Test RetryExhaustedError when all retries fail."""
        retry_manager = RetryManager(
            max_retries=2,
            base_delay=0.01,
        )

        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_manager.execute(
                always_fails,
                retryable_exceptions=(ValueError,),
            )

        error = exc_info.value
        assert error.attempts == 3  # Initial + 2 retries
        assert isinstance(error.last_exception, ValueError)

    @pytest.mark.asyncio
    async def test_execute_non_retryable_exception(self):
        """Test that non-retryable exceptions aren't retried."""
        retry_manager = RetryManager(max_retries=3)

        attempts = []

        async def raises_non_retryable():
            attempts.append(1)
            raise TypeError("Non-retryable")

        with pytest.raises(TypeError):
            await retry_manager.execute(
                raises_non_retryable,
                retryable_exceptions=(ValueError,),  # Only retry ValueError
            )

        assert len(attempts) == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_on_retry_callback(self):
        """Test on_retry callback is called."""
        retry_manager = RetryManager(
            max_retries=2,
            base_delay=0.01,
        )

        retry_events = []

        def on_retry(attempt, exception):
            retry_events.append((attempt, str(exception)))

        async def flaky_function():
            if len(retry_events) < 2:
                raise ValueError(f"Failure {len(retry_events)}")
            return "success"

        result = await retry_manager.execute(
            flaky_function,
            retryable_exceptions=(ValueError,),
            on_retry=on_retry,
        )

        assert result == "success"
        assert len(retry_events) == 2
        assert retry_events[0] == (0, "Failure 0")
        assert retry_events[1] == (1, "Failure 1")

    def test_execute_sync_success(self):
        """Test synchronous execution."""
        retry_manager = RetryManager(max_retries=2)

        def sync_function():
            return "sync_success"

        result = retry_manager.execute_sync(sync_function)
        assert result == "sync_success"

    def test_execute_sync_with_retries(self):
        """Test synchronous retry logic."""
        retry_manager = RetryManager(
            max_retries=2,
            base_delay=0.01,
        )

        attempts = []

        def flaky_sync():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("Retry me")
            return "success"

        result = retry_manager.execute_sync(
            flaky_sync,
            retryable_exceptions=(ValueError,),
        )

        assert result == "success"
        assert len(attempts) == 2


class TestRetryDecorator:
    """Test @retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_decorator_async_function(self):
        """Test decorator on async function."""
        attempts = []

        @retry_with_backoff(
            max_retries=2,
            base_delay=0.01,
            retryable_exceptions=(ValueError,),
        )
        async def flaky_async():
            attempts.append(1)
            if len(attempts) < 2:
                raise ValueError("Retry")
            return "success"

        result = await flaky_async()
        assert result == "success"
        assert len(attempts) == 2

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @retry_with_backoff(max_retries=1)
        async def documented_function():
            """This is a docstring."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a docstring."

    @pytest.mark.asyncio
    async def test_decorator_with_different_strategies(self):
        """Test decorator with different retry strategies."""

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.01,
            strategy=RetryStrategy.LINEAR,
        )
        async def test_function():
            return "result"

        result = await test_function()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_decorator_retry_exhausted(self):
        """Test decorator raises RetryExhaustedError."""

        @retry_with_backoff(
            max_retries=1,
            base_delay=0.01,
            retryable_exceptions=(ValueError,),
        )
        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(RetryExhaustedError):
            await always_fails()
